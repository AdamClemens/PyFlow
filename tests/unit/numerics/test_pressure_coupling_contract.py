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
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
import torch

from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PressureCoupling
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


class _StubLinearSolver(LinearSolver):
    """A minimal `LinearSolver` test double -- exists only so a
    `PressureCoupling` strategy has something real to be constructed
    with; this suite makes no claim about solving.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=True, iterations=0)


class _PassthroughCoupling(PressureCoupling):
    """Returns the provisional velocity unchanged and a zero pressure
    field -- the trivial case.
    """

    def correct(self, provisional_velocity: VectorField) -> tuple[VectorField, ScalarField]:
        pressure = ScalarField(provisional_velocity.mesh, "pressure")
        return provisional_velocity.copy(), pressure


class _ScaledCoupling(PressureCoupling):
    """Genuinely different arithmetic: halves the provisional velocity
    and reports a nonzero constant pressure -- not a real correction,
    only structurally distinct from `_PassthroughCoupling`'s output.
    """

    def correct(self, provisional_velocity: VectorField) -> tuple[VectorField, ScalarField]:
        corrected = provisional_velocity.copy()
        corrected.values[:] = provisional_velocity.values * 0.5
        pressure = ScalarField(provisional_velocity.mesh, "pressure", initial_value=1.0)
        return corrected, pressure


_FACTORIES: list[tuple[str, Callable[[LinearSolver], PressureCoupling]]] = [
    ("passthrough", _PassthroughCoupling),
    ("scaled", _ScaledCoupling),
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

    corrected_velocity, pressure = make_coupling.correct(provisional)

    assert isinstance(corrected_velocity, VectorField)
    assert isinstance(pressure, ScalarField)
    assert corrected_velocity.mesh is mesh
    assert pressure.mesh is mesh


def test_correct_does_not_mutate_the_provisional_field(make_coupling: PressureCoupling) -> None:
    mesh = _mesh()
    provisional = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, -1.0))
    before = provisional.values.clone()

    make_coupling.correct(provisional)

    assert torch.equal(provisional.values, before)
