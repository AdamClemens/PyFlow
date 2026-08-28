"""Binds `tests/features/conjugate_gradient_solver.feature` (TASK-026)
-- Stage 4's fifth real numerical scheme, and Stage 4 Completion
Criterion 4's own claim for it: converges on a system with the same
character as the one PISO actually produces for the lid-driven cavity's
boundary configuration (positive semi-definite, pressure fixed only up
to an additive constant), not only on a made-up well-conditioned system.
Separately: non-convergence stays distinguishable from a converged
answer.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).

**The semi-definite fixture is built from the real diffusion operator,
not a hand-typed matrix** -- `CentralDifferenceDiffusion`/
`accumulate_flux_to_cells` (TASK-024/040) on a `StructuredCartesianMesh`
with a zero-gradient condition on every edge, assembled column by column
from unit basis fields. This is the closest available approximation to
"the system PISO actually produces" since PISO itself doesn't exist yet
(TASK-027) -- verified directly (`docs/planning/roadmap.md` TASK-026's
own Context) to actually be symmetric, positive semi-definite, with
exactly one near-zero eigenvalue, before this file was written.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver, LinearSolverResult
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import accumulate_flux_to_cells

scenarios("conjugate_gradient_solver.feature")


class _ZeroGradientCondition(BoundaryCondition):
    """The Neumann shape, fixed at zero -- "every boundary prescribes
    velocity, none prescribes pressure", the configuration that leaves
    the constant mode in the pressure-correction matrix's own null space
    (`docs/architecture/icds.md`'s Linear Solver ICD).
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


def _mesh() -> StructuredCartesianMesh:
    # Non-"nice" origin/spacing and a non-square extent, matching every
    # other contract suite's fixture in this repository.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(3, 2))


def _build_semidefinite_matrix(mesh: StructuredCartesianMesh) -> torch.Tensor:
    """`matrix[:, j] = -accumulate_flux_to_cells(mesh, diffusion.flux(e_j))`
    for each unit basis field `e_j` -- the real discrete Laplacian this
    scheme produces, negated (the raw operator is negative semi-definite;
    a pressure-correction system is posed as the positive semi-definite
    version of the same operator).
    """
    condition = _ZeroGradientCondition()
    boundary_conditions = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    diffusion = CentralDifferenceDiffusion(boundary_conditions, {}, diffusion_coefficient=1.0)

    n = mesh.num_cells
    matrix = torch.zeros((n, n), dtype=torch.float64)
    for column in range(n):
        unit_field = ScalarField(mesh, "unit")
        unit_field.values[column] = 1.0
        flux = diffusion.flux(unit_field)
        matrix[:, column] = -accumulate_flux_to_cells(mesh, flux)
    return matrix


# -- Fixture context -----------------------------------------------------


@dataclass
class _Context:
    matrix: torch.Tensor
    rhs: torch.Tensor
    tolerance: float = 1e-10
    max_iterations: int = 500
    result: LinearSolverResult | None = None


# -- Given -----------------------------------------------------------------


@given(
    "a positive semi-definite system built from CentralDifferenceDiffusion on an "
    "all-zero-gradient-boundary mesh",
    target_fixture="ctx",
)
def _given_semidefinite_system() -> _Context:
    mesh = _mesh()
    matrix = _build_semidefinite_matrix(mesh)
    return _Context(matrix=matrix, rhs=torch.zeros(mesh.num_cells, dtype=torch.float64))


@given("a right-hand side satisfying the zero-mean compatibility condition")
def _given_zero_mean_rhs(ctx: _Context) -> None:
    n = ctx.matrix.shape[0]
    values = [1.0, -2.0, 0.5, 0.5, 1.0, -1.0][:n]
    rhs = torch.tensor(values, dtype=torch.float64)
    rhs = rhs - rhs.mean()
    ctx.rhs = rhs


@given("a well-conditioned system with a known solution", target_fixture="ctx")
def _given_well_conditioned_system() -> _Context:
    matrix = torch.tensor([[4.0, 1.0], [1.0, 3.0]], dtype=torch.float64)
    x_true = torch.tensor([1.5, -2.25], dtype=torch.float64)
    rhs = matrix @ x_true
    return _Context(matrix=matrix, rhs=rhs)


@given("an iteration limit too low to reach the configured tolerance")
def _given_low_iteration_limit(ctx: _Context) -> None:
    ctx.tolerance = 1e-12
    ctx.max_iterations = 1


# -- When ------------------------------------------------------------------


@when("the system is solved")
def _when_solved(ctx: _Context) -> None:
    solver = ConjugateGradientSolver(tolerance=ctx.tolerance, max_iterations=ctx.max_iterations)
    ctx.result = solver.solve(ctx.matrix, ctx.rhs)


# -- Then ------------------------------------------------------------------


@then("the solver reports convergence")
def _then_converged(ctx: _Context) -> None:
    assert ctx.result is not None
    assert ctx.result.converged is True


@then("the residual of the reported solution is close to zero")
def _then_residual_close_to_zero(ctx: _Context) -> None:
    assert ctx.result is not None
    residual = ctx.rhs - ctx.matrix @ ctx.result.solution
    assert float(torch.linalg.vector_norm(residual)) < 1e-6


@then("the reported solution stays bounded")
def _then_solution_bounded(ctx: _Context) -> None:
    assert ctx.result is not None
    assert torch.all(torch.isfinite(ctx.result.solution))
    assert float(torch.max(torch.abs(ctx.result.solution))) < 100.0


@then("the solver reports non-convergence")
def _then_not_converged(ctx: _Context) -> None:
    assert ctx.result is not None
    assert ctx.result.converged is False


@then("the iteration count equals the configured limit")
def _then_iterations_equal_limit(ctx: _Context) -> None:
    assert ctx.result is not None
    assert ctx.result.iterations == ctx.max_iterations
