"""Binds `tests/features/pressure_correction_loop.feature` (TASK-033) --
Stage 5's fourth task in build order. `PISO`'s own corrector loop
mechanism (`engine/numerics/pressure_coupling.py`) is what this task
built; these scenarios prove its own three claims -- a non-increasing
recorded sequence reaching tolerance, genuine multi-pass convergence
when a single pass genuinely cannot finish the job, and honest failure
when the iteration limit is exhausted -- against the real class, not a
new mechanism.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.linear_solver import (
    ConjugateGradientSolver,
    LinearSolver,
    LinearSolverResult,
)
from pyflow.engine.numerics.pressure_coupling import PISO, DivergenceDidNotConvergeError
from pyflow.engine.vector_field import VectorField

from ._numerics import default_mesh

scenarios("pressure_correction_loop.feature")

_TOLERANCE = 1e-4


class _ZeroNormalVelocity(BoundaryCondition):
    """Dirichlet, fixed at zero -- a closed box, the same fixture shape
    `test_piso_pressure_coupling.py`'s own identically-named double uses.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


class _HalvingSolver(LinearSolver):
    """Always returns exactly half of the true (least-squares) solution
    -- a deterministic, hand-verifiable way to force the corrector loop
    to take genuinely multiple passes, rather than relying on a real
    iterative solver's own opaque partial-convergence behaviour.

    Because the pressure-correction system is linear, using half of the
    exact correction each pass leaves exactly half of the *previous*
    residual, not some solver-dependent fraction -- verified directly
    with a disposable prototype script before writing this class (the
    same discipline TASK-026/027 both used): the recorded divergence
    sequence halves on every single pass to machine precision. Always
    reports `converged=True` -- a real "solve" happened, it was just
    deliberately incomplete, the same "converged but wrong" shape
    `test_pressure_coupling_contract.py`'s own `_StubLinearSolver` found
    itself accidentally producing before it was fixed to do a real solve.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        # `torch.linalg.lstsq` has no sparse overload (verified directly,
        # `adr/ADR-011-sparse-linear-solver-matrix.md`) -- densify first,
        # same reasoning as `test_pressure_coupling_contract.py`'s own
        # `_StubLinearSolver` guard.
        dense = matrix.to_dense() if matrix.layout != torch.strided else matrix
        exact = torch.linalg.lstsq(dense, rhs.unsqueeze(-1)).solution.squeeze(-1)
        return LinearSolverResult(solution=0.5 * exact, converged=True, iterations=1)


class _NoOpSolver(LinearSolver):
    """Reports success but returns the zero vector always -- never
    reduces divergence, so a corrector loop using it can only ever
    exhaust its own iteration limit. Distinct from
    `test_piso_pressure_coupling.py`'s own `_NeverConvergesSolver`
    (which reports `converged=False`, testing the *inner* solve's own
    honesty): this double's own inner solve always succeeds, so it is
    the *outer* corrector loop's own exhaustion path this exercises,
    not `PressureSolveDidNotConvergeError`.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=True, iterations=0)


def _divergent_provisional_velocity(mesh: StructuredCartesianMesh) -> VectorField:
    # Neither axis-aligned nor uniform -- the same fixture shape
    # `test_piso_pressure_coupling.py`'s own `_provisional_velocity` uses.
    center_x, center_y = 1.0, -0.4

    def value(x: float, y: float) -> tuple[float, float]:
        return (
            0.6 * (x - center_x) - 0.2 * (y - center_y),
            0.3 * (x - center_x) + 0.9 * (y - center_y),
        )

    return VectorField(mesh, "u_star", num_components=2, initial_value=value)


def _boundary_conditions() -> dict[str, BoundaryCondition]:
    condition = _ZeroNormalVelocity()
    return {"north": condition, "south": condition, "east": condition, "west": condition}


# -- Fixture context -------------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    boundary_conditions: dict[str, BoundaryCondition] = field(default_factory=_boundary_conditions)
    provisional_velocity: VectorField | None = None
    linear_solver: LinearSolver | None = None
    max_iterations: int = 50
    history: tuple[float, ...] | None = None
    error: Exception | None = None


# -- Given -------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    return _Context(mesh=default_mesh(extent=(5, 4)))


@given(
    "a provisional velocity field with real interior divergence, not aligned with either mesh axis"
)
def _given_divergent_velocity(ctx: _Context) -> None:
    ctx.provisional_velocity = _divergent_provisional_velocity(ctx.mesh)


@given("a real linear solver")
def _given_real_solver(ctx: _Context) -> None:
    ctx.linear_solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)


@given("a linear solver that only ever removes half of the remaining divergence per pass")
def _given_halving_solver(ctx: _Context) -> None:
    ctx.linear_solver = _HalvingSolver()


@given("a linear solver that reports success but never actually reduces divergence")
def _given_noop_solver(ctx: _Context) -> None:
    ctx.linear_solver = _NoOpSolver()


@given("a corrector iteration limit of 3")
def _given_iteration_limit(ctx: _Context) -> None:
    ctx.max_iterations = 3


# -- When ------------------------------------------------------------------


@when("the field is corrected by PISO's own corrector loop")
def _when_corrected(ctx: _Context) -> None:
    assert ctx.provisional_velocity is not None
    assert ctx.linear_solver is not None
    piso = PISO(
        ctx.linear_solver,
        ctx.boundary_conditions,
        tolerance=_TOLERANCE,
        max_iterations=ctx.max_iterations,
    )
    try:
        piso.correct(ctx.provisional_velocity, dt=1.0)
    except DivergenceDidNotConvergeError as exc:
        ctx.error = exc
    ctx.history = piso.last_divergence_history


# -- Then ------------------------------------------------------------------


_INITIAL_DIVERGENCE_MARGIN = 1_000.0
"""How far above `_TOLERANCE` this fixture's own pre-correction divergence
must sit for the two assertions after it to mean anything -- "orders of
magnitude", made a number (Stage 5 Completion Criterion 3). Measured
directly on this exact fixture before being chosen: the recorded sequence
starts at 1.85 against a tolerance of 1e-4, so roughly four orders of
magnitude, and this bound keeps a full order of margin below that rather
than being set at the measured value.
"""


@then("the recorded divergence sequence starts orders of magnitude above the configured tolerance")
def _then_starts_far_above_tolerance(ctx: _Context) -> None:
    assert ctx.history is not None
    assert ctx.history[0] > _INITIAL_DIVERGENCE_MARGIN * _TOLERANCE, (
        f"fixture's initial divergence {ctx.history[0]} is not orders of magnitude above the "
        f"configured tolerance {_TOLERANCE}; the non-increasing and reaches-tolerance "
        "assertions below it would pass for a corrector that did nothing"
    )


@then("the recorded divergence sequence is non-increasing at every element")
def _then_non_increasing(ctx: _Context) -> None:
    assert ctx.history is not None
    assert all(a >= b for a, b in zip(ctx.history, ctx.history[1:], strict=False))


@then("its last element is at or below the configured tolerance")
def _then_last_below_tolerance(ctx: _Context) -> None:
    assert ctx.history is not None
    assert ctx.history[-1] <= _TOLERANCE


@then("the recorded divergence sequence has more than two elements")
def _then_more_than_two_elements(ctx: _Context) -> None:
    assert ctx.history is not None
    assert len(ctx.history) > 2, ctx.history


@then("each element is smaller than the one before it")
def _then_strictly_decreasing(ctx: _Context) -> None:
    assert ctx.history is not None
    assert all(a > b for a, b in zip(ctx.history, ctx.history[1:], strict=False)), ctx.history


@then("a divergence-did-not-converge error is raised")
def _then_divergence_error_raised(ctx: _Context) -> None:
    assert isinstance(ctx.error, DivergenceDidNotConvergeError)


@then("the recorded divergence sequence has exactly 4 elements")
def _then_exactly_four_elements(ctx: _Context) -> None:
    # max_iterations=3 corrector *passes* are attempted, plus the initial
    # (pre-correction) measurement -- 4 divergence checks total.
    assert ctx.history is not None
    assert len(ctx.history) == 4, ctx.history
