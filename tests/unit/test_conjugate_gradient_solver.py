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

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver, LinearSolverResult
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import accumulate_flux_to_cells

from ._numerics import (
    FixedGradientCondition,
    default_mesh,
)

scenarios("conjugate_gradient_solver.feature")


def _build_semidefinite_matrix(mesh: StructuredCartesianMesh) -> torch.Tensor:
    """`matrix[:, j] = -accumulate_flux_to_cells(mesh, diffusion.flux(e_j))`
    for each unit basis field `e_j` -- the real discrete Laplacian this
    scheme produces, negated (the raw operator is negative semi-definite;
    a pressure-correction system is posed as the positive semi-definite
    version of the same operator).

    **Zero gradient on every edge is the load-bearing choice, not a
    convenient default**: it is "every boundary prescribes velocity, none
    prescribes pressure" (`docs/architecture/icds.md`'s Linear Solver
    ICD), the configuration that leaves the constant mode in the
    pressure-correction matrix's own null space -- which is the whole
    character this fixture exists to reproduce. Change it and the system
    stops being semi-definite, and this task's own criterion stops being
    checked.
    """
    condition = FixedGradientCondition()
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
    mesh = default_mesh()
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


# -- A plain (non-BDD) unit test, not an acceptance criterion of its own --
#
# `adr/ADR-011-sparse-linear-solver-matrix.md`: `ConjugateGradientSolver`
# now accepts a sparse `matrix`, on the same semi-definite (null-space)
# system this file's own feature scenarios already exercise -- an
# implementation-detail claim (same solver, same math, different tensor
# layout), not a new physical-correctness claim, so a plain pytest test
# rather than a new Gherkin scenario (the same treatment TASK-034's
# `_poisson_matrix` caching fix got, `tests/unit/test_piso_pressure_
# coupling.py`).


def test_solve_gives_the_same_result_for_a_sparse_matrix_as_a_dense_one() -> None:
    mesh = default_mesh()
    dense = _build_semidefinite_matrix(mesh)
    rows, cols = dense.nonzero(as_tuple=True)
    indices = torch.stack([rows, cols])
    values = dense[rows, cols]
    sparse = torch.sparse_coo_tensor(indices, values, dense.shape).coalesce().to_sparse_csr()
    assert torch.equal(sparse.to_dense(), dense)

    rhs_values = [1.0, -2.0, 0.5, 0.5, 1.0, -1.0][: mesh.num_cells]
    rhs = torch.tensor(rhs_values, dtype=torch.float64)
    rhs = rhs - rhs.mean()

    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    dense_result = solver.solve(dense, rhs)
    sparse_result = solver.solve(sparse, rhs)

    assert dense_result.converged
    assert sparse_result.converged
    assert dense_result.iterations == sparse_result.iterations
    assert torch.allclose(dense_result.solution, sparse_result.solution, atol=1e-8)
