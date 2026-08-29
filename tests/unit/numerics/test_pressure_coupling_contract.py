"""Contract test suite for `PressureCoupling` (TASK-021) -- the
interface that enforces incompressibility: given a provisional velocity
field, produce a corrected, divergence-free one and the pressure field
consistent with it (`docs/architecture/engine.md`'s Pressure-Velocity
Coupling contract).

Two test-only implementations, per Stage 3 Completion Criterion 2, each
constructed with a test-only `LinearSolver` -- Criterion 6's "the one
real cross-layer dependency among the six" made structural: a coupling
strategy cannot be built without one. No third, deliberately inert
implementation: unlike the five TASK-018 suites, this task's own
Acceptance Criteria name no "varies with input" case to give one teeth
against.

**`correct` gained a second parameter, `dt: float` (TASK-027,
`adr/ADR-009-pressure-coupling-dt.md`)** -- both test-only
implementations below have their call sites adapted, the same shape
`test_time_integrator_contract.py` needed for `TimeIntegrator.advance`'s
own widening (TASK-025). `PISO` (TASK-027, Stage 4) is the real third
fixture this suite joins.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Literal

import pytest
import torch

from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PISO, PressureCoupling
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


class _StubLinearSolver(LinearSolver):
    """A minimal `LinearSolver` test double -- exists only so a
    `PressureCoupling` strategy has something real to be constructed
    with; this suite makes no claim about solving *strategy* (iterative
    vs. direct, tolerance, etc.).

    **Performs a real direct solve (`torch.linalg.lstsq`, not
    `torch.linalg.solve` -- `PISO`'s own Poisson matrix is singular by
    construction, a pure-Neumann pressure problem, so a real solve has to
    tolerate that the same way `ConjugateGradientSolver`'s own gated
    null-space projection does), not a convenient zero -- found
    necessary, not assumed, once `PISO` (TASK-033, Stage 5) became a
    genuine corrector *loop*.** Returning the zero vector while claiming
    `converged=True` was already dishonest in the shape
    `docs/practices.md` warns about, but the old single-pass `PISO` never
    checked whether a correction actually reduced divergence, so it went
    unnoticed; the new loop does check, correctly refuses to accept a
    "solve" that never improves anything, and exhausts its own iteration
    limit -- exposing the stub for what it was rather than a bug in the
    loop itself.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        solution = torch.linalg.lstsq(matrix, rhs.unsqueeze(-1)).solution.squeeze(-1)
        return LinearSolverResult(solution=solution, converged=True, iterations=1)


class _ZeroNormalVelocity(BoundaryCondition):
    """A minimal Dirichlet `BoundaryCondition` test double -- exists only
    so `PISO`'s own `GreenGaussDivergence` has something real to be
    constructed with; this suite makes no claim about `PISO`'s own
    numerical behaviour (`test_piso_pressure_coupling.py` does).
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        return 0.0


class _PassthroughCoupling(PressureCoupling):
    """Returns the provisional velocity unchanged and a zero pressure
    field -- the trivial case.
    """

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        del dt
        pressure = ScalarField(provisional_velocity.mesh, "pressure")
        return provisional_velocity.copy(), pressure


class _ScaledCoupling(PressureCoupling):
    """Genuinely different arithmetic: halves the provisional velocity
    and reports a nonzero constant pressure -- not a real correction,
    only structurally distinct from `_PassthroughCoupling`'s output.
    """

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        del dt
        corrected = provisional_velocity.copy()
        corrected.values[:] = provisional_velocity.values * 0.5
        pressure = ScalarField(provisional_velocity.mesh, "pressure", initial_value=1.0)
        return corrected, pressure


def _piso(linear_solver: LinearSolver) -> PressureCoupling:
    boundary_conditions: Mapping[str, BoundaryCondition] = {
        name: _ZeroNormalVelocity() for name in ("north", "south", "east", "west")
    }
    return PISO(linear_solver, boundary_conditions)


_FACTORIES: list[tuple[str, Callable[[LinearSolver], PressureCoupling]]] = [
    ("passthrough", _PassthroughCoupling),
    ("scaled", _ScaledCoupling),
    ("piso", _piso),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_coupling(request: pytest.FixtureRequest) -> PressureCoupling:
    factory: Callable[[LinearSolver], PressureCoupling] = request.param[1]
    return factory(_StubLinearSolver())


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        PressureCoupling(_StubLinearSolver())  # type: ignore[abstract]


def test_subclass_missing_correct_cannot_be_instantiated() -> None:
    class _Incomplete(PressureCoupling):
        pass

    with pytest.raises(TypeError):
        _Incomplete(_StubLinearSolver())  # type: ignore[abstract]


def test_correct_is_the_only_abstract_method() -> None:
    assert PressureCoupling.__abstractmethods__ == frozenset({"correct"})


def test_constructing_without_a_linear_solver_raises() -> None:
    with pytest.raises(TypeError):
        _PassthroughCoupling(None)  # type: ignore[arg-type]


def test_constructing_with_a_non_solver_object_raises() -> None:
    with pytest.raises(TypeError):
        _PassthroughCoupling("not a solver")  # type: ignore[arg-type]


def test_linear_solver_is_accessible_after_construction() -> None:
    solver = _StubLinearSolver()
    coupling = _PassthroughCoupling(solver)
    assert coupling.linear_solver is solver


def test_correct_returns_a_velocity_and_pressure_field_over_the_same_mesh(
    make_coupling: PressureCoupling,
) -> None:
    mesh = _mesh()
    provisional = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, -1.0))

    corrected_velocity, pressure = make_coupling.correct(provisional, dt=0.01)

    assert isinstance(corrected_velocity, VectorField)
    assert isinstance(pressure, ScalarField)
    assert corrected_velocity.mesh is mesh
    assert pressure.mesh is mesh


def test_correct_does_not_mutate_the_provisional_field(make_coupling: PressureCoupling) -> None:
    mesh = _mesh()
    provisional = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, -1.0))
    before = provisional.values.clone()

    make_coupling.correct(provisional, dt=0.01)

    assert torch.equal(provisional.values, before)
