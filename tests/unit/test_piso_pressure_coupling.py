"""Binds `tests/features/piso_pressure_coupling.feature` (TASK-027) --
Stage 4's sixth real numerical scheme, and Stage 4 Completion
Criterion 4's own claim for it, corrected 2026-08-27 before
implementation started (`docs/planning/roadmap.md`, Stage 4 Completion
Criteria, Pressure-Velocity Coupling bullet): a single correction pass
measurably and boundedly reduces the divergence of a manufactured
provisional velocity field, checked in isolation against a stated
tolerance. The full "reaches a configured tolerance via monotonic
multi-pass correction" claim belongs to Stage 5 TASK-033, not this file.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).

**The provisional velocity fixture is not axis-aligned and its
divergence is not the same at every cell** (`docs/practices.md`,
"Verify a conversion where its factors are distinct"), so a wrong
implementation (e.g. one that leaves the field unchanged, or corrects
uniformly regardless of local divergence) cannot pass by coincidence.
The 70% bound in the feature file's own first scenario is the actual,
measured reduction on this fixture (roughly 46-54% depending on the
cell, `docs/planning/roadmap.md` TASK-027's own Design decision Two),
with real margin, not a value picked to make a marginal result pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PISO, PressureSolveDidNotConvergeError
from pyflow.engine.vector_field import VectorField

from ._numerics import (
    default_mesh,
)

scenarios("piso_pressure_coupling.feature")


class _ZeroNormalVelocity(BoundaryCondition):
    """Dirichlet, fixed at zero -- a closed box: every boundary
    prescribes zero normal velocity, so the manufactured provisional
    field's own interior divergence is the only source of imbalance the
    correction has to remove.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


class _NeverConvergesSolver(LinearSolver):
    """Reports `converged=False` unconditionally -- exists only to prove
    `PISO.correct` raises rather than returning an unconverged pressure
    solve's velocity correction as if it were trustworthy.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=False, iterations=1000)


def _boundary_conditions() -> dict[str, BoundaryCondition]:
    condition = _ZeroNormalVelocity()
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def _provisional_velocity(mesh: StructuredCartesianMesh) -> VectorField:
    # Neither axis-aligned nor uniform -- a real divergence field, not a
    # degenerate one a wrong implementation could satisfy by luck.
    center_x, center_y = 1.0, -0.4

    def value(x: float, y: float) -> tuple[float, float]:
        return (
            0.6 * (x - center_x) - 0.2 * (y - center_y),
            0.3 * (x - center_x) + 0.9 * (y - center_y),
        )

    return VectorField(mesh, "u_star", num_components=2, initial_value=value)


# -- Fixture context -------------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    boundary_conditions: dict[str, BoundaryCondition]
    provisional_velocity: VectorField
    linear_solver: LinearSolver | None = None
    corrected_velocity: VectorField | None = None
    raised: Exception | None = field(default=None)


# -- Given -------------------------------------------------------------------


@given(
    "a closed-box mesh with zero normal velocity prescribed on every boundary",
    target_fixture="ctx",
)
def _given_closed_box_mesh() -> _Context:
    mesh = default_mesh(extent=(5, 4))
    return _Context(
        mesh=mesh,
        boundary_conditions=_boundary_conditions(),
        provisional_velocity=_provisional_velocity(mesh),
    )


@given(
    "a provisional velocity field with real interior divergence, not aligned with either mesh axis"
)
def _given_provisional_velocity(ctx: _Context) -> None:
    # Already built by the mesh step above -- this step exists so the
    # scenario reads as two independent Givens, matching the feature
    # file's own phrasing, without rebuilding the field a second time.
    assert ctx.provisional_velocity is not None


@given("a linear solver that never reports convergence")
def _given_never_converges_solver(ctx: _Context) -> None:
    ctx.linear_solver = _NeverConvergesSolver()


# -- When --------------------------------------------------------------------


@when("the field is corrected by one PISO pass")
def _when_corrected(ctx: _Context) -> None:
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    linear_solver = ctx.linear_solver or ConjugateGradientSolver(
        tolerance=1e-10, max_iterations=500
    )
    piso = PISO(linear_solver, ctx.boundary_conditions)
    try:
        ctx.corrected_velocity, _ = piso.correct(ctx.provisional_velocity, dt=1.0)
    except PressureSolveDidNotConvergeError as error:
        ctx.raised = error


# -- Then ----------------------------------------------------------------------


def _divergence(ctx: _Context, velocity: VectorField) -> torch.Tensor:
    from pyflow.engine.numerics.divergence import GreenGaussDivergence

    return GreenGaussDivergence(ctx.boundary_conditions).divergence(velocity)


@then(
    "every cell's corrected divergence magnitude is less than 70% of the provisional "
    "field's own maximum divergence magnitude"
)
def _then_every_cell_bounded(ctx: _Context) -> None:
    assert ctx.corrected_velocity is not None
    original = _divergence(ctx, ctx.provisional_velocity).abs()
    corrected = _divergence(ctx, ctx.corrected_velocity).abs()
    bound = 0.7 * float(original.max())
    assert bool((corrected < bound).all()), (
        f"corrected divergence exceeded {bound} somewhere: {corrected}"
    )


@then(
    "the corrected field's own maximum divergence magnitude is smaller than the provisional field's"
)
def _then_max_smaller(ctx: _Context) -> None:
    assert ctx.corrected_velocity is not None
    original_max = float(_divergence(ctx, ctx.provisional_velocity).abs().max())
    corrected_max = float(_divergence(ctx, ctx.corrected_velocity).abs().max())
    assert corrected_max < original_max


@then("a pressure solve non-convergence error is raised")
def _then_non_convergence_raised(ctx: _Context) -> None:
    assert isinstance(ctx.raised, PressureSolveDidNotConvergeError)
