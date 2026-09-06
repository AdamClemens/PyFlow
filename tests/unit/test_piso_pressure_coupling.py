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

import pytest
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PISO, PressureSolveDidNotConvergeError
from pyflow.engine.vector_field import VectorField

from ._numerics import (
    DEFAULT_ORIGIN,
    DEFAULT_SPACING,
    FixedGradientCondition,
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

    return GreenGaussDivergence(ctx.boundary_conditions, {}).divergence(velocity)


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


# -- A plain (non-BDD) unit test, not an acceptance criterion of its own --
#
# TASK-034 (Stage 5): `_poisson_matrix` is now cached per `PISO` instance
# rather than rebuilt every `correct` call -- an implementation-detail
# performance fix (found while measuring the Lid-Driven Cavity
# validation's own real runtime, `pressure_coupling.py`'s own entry for
# the full reasoning), not a new physical-correctness claim, so a plain
# pytest test rather than a new Gherkin scenario.


def test_poisson_matrix_is_cached_across_repeated_correct_calls_on_the_same_mesh() -> None:
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    mesh = default_mesh()
    condition = _ZeroNormalVelocity()
    boundary_conditions: dict[str, BoundaryCondition] = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    piso = PISO(solver, boundary_conditions, tolerance=1e-8)

    velocity = VectorField(
        mesh, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity, dt=0.1)
    first_matrix = piso._cached_poisson_matrix
    assert first_matrix is not None

    piso.correct(velocity, dt=0.1)
    second_matrix = piso._cached_poisson_matrix
    assert second_matrix is first_matrix, "the matrix was rebuilt on a second call, not reused"


def test_poisson_matrix_recomputes_for_a_genuinely_different_mesh() -> None:
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    condition = _ZeroNormalVelocity()
    boundary_conditions: dict[str, BoundaryCondition] = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    piso = PISO(solver, boundary_conditions, tolerance=1e-8)

    mesh_a = default_mesh(extent=(3, 2))
    velocity_a = VectorField(
        mesh_a, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity_a, dt=0.1)
    matrix_a = piso._cached_poisson_matrix

    mesh_b = default_mesh(extent=(4, 3))
    velocity_b = VectorField(
        mesh_b, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity_b, dt=0.1)
    matrix_b = piso._cached_poisson_matrix

    assert matrix_a is not None
    assert matrix_b is not None
    assert matrix_a.shape != matrix_b.shape


def test_poisson_matrix_is_stored_sparse() -> None:
    # `adr/ADR-011-sparse-linear-solver-matrix.md`: the dense `(N,N)`
    # tensor TASK-026's own reversible decision left in place is now a
    # sparse CSR tensor -- an implementation detail, same shape as the
    # caching tests above, not a new physical-correctness claim.
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    mesh = default_mesh()
    condition = _ZeroNormalVelocity()
    boundary_conditions: dict[str, BoundaryCondition] = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    piso = PISO(solver, boundary_conditions, tolerance=1e-8)

    velocity = VectorField(
        mesh, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity, dt=0.1)

    matrix = piso._cached_poisson_matrix
    assert matrix is not None
    assert matrix.layout == torch.sparse_csr


def test_rhie_chow_geometry_is_cached_across_repeated_correct_calls_on_the_same_mesh() -> None:
    # `_rhie_chow_divergence`'s own per-face Python loop was split and
    # vectorised the same way `CentralDifferenceDiffusion.flux`'s own fix
    # did: a per-instance geometry cache, distinct from
    # `_cached_poisson_matrix` above, built once per mesh identity.
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    mesh = default_mesh()
    condition = _ZeroNormalVelocity()
    boundary_conditions: dict[str, BoundaryCondition] = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    piso = PISO(solver, boundary_conditions, tolerance=1e-8)

    velocity = VectorField(
        mesh, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity, dt=0.1)
    first = piso._cached_rhie_chow_geometry
    assert first is not None

    piso.correct(velocity, dt=0.1)
    second = piso._cached_rhie_chow_geometry
    assert second is first, "geometry was rebuilt on a second call, not reused"


def test_rhie_chow_geometry_recomputes_for_a_genuinely_different_mesh() -> None:
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    condition = _ZeroNormalVelocity()
    boundary_conditions: dict[str, BoundaryCondition] = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    piso = PISO(solver, boundary_conditions, tolerance=1e-8)

    mesh_a = default_mesh(extent=(3, 2))
    velocity_a = VectorField(
        mesh_a, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity_a, dt=0.1)
    geometry_a = piso._cached_rhie_chow_geometry

    mesh_b = default_mesh(extent=(4, 3))
    velocity_b = VectorField(
        mesh_b, "velocity", num_components=2, initial_value=lambda x, y: (0.6 * x, 0.3 * y)
    )
    piso.correct(velocity_b, dt=0.1)
    geometry_b = piso._cached_rhie_chow_geometry

    assert geometry_a is not None
    assert geometry_b is not None
    assert geometry_a is not geometry_b
    assert geometry_a.owner_ids.shape != geometry_b.owner_ids.shape


# -- `_poisson_matrix`'s direct per-face construction, replacing the
# O(num_cells * num_faces) probe loop (`adr/ADR-012-direct-poisson-
# matrix-construction.md`) -- an implementation-detail performance fix,
# same shape as the caching tests above, not a new physical-correctness
# claim: `PressureCoupling.correct`'s own public contract is unchanged.
#
# Highest priority here: the matrix must be proven identical to the
# probe-based one it replaces, not merely "looks right on paper" -- a
# first hand derivation of the periodic-face contribution, made while
# planning this change, was wrong until checked numerically against the
# real, unmodified code.


def _reference_poisson_matrix(
    mesh: StructuredCartesianMesh, periodic_pairs: dict[str, str], gamma: float = 1.0
) -> torch.Tensor:
    """An independently-derived O(num_faces) construction -- ported from
    a disposable prototype verified numerically against the real,
    unmodified probe-based `_poisson_matrix` across four mesh
    configurations before `_poisson_matrix` itself was rewritten to
    match it. Deliberately does not call anything in
    `pressure_coupling.py`, so a bug shared between this function and
    the real implementation cannot hide from the comparison below.
    """
    volumes = {mesh.cell_volume(cell) for cell in range(mesh.num_cells)}
    assert len(volumes) == 1, "test fixture itself must be uniform-volume"
    volume = next(iter(volumes))

    rows: list[int] = []
    cols: list[int] = []
    values: list[float] = []
    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        area = mesh.face_area(face)
        if neighbour is not None:
            distance = mesh.face_centroid_distance(face)
            coefficient = gamma * area / (distance * volume)
            rows += [owner, neighbour, owner, neighbour]
            cols += [owner, neighbour, neighbour, owner]
            values += [coefficient, coefficient, -coefficient, -coefficient]
            continue
        boundary_name = mesh.boundary_face_name(face)
        assert boundary_name is not None
        if boundary_name in periodic_pairs:
            wrapped = mesh.wrapped_neighbour_cell(face)
            distance = 2 * mesh.face_centroid_distance(face)
            coefficient = gamma * area / (distance * volume)
            rows += [owner, owner]
            cols += [owner, wrapped]
            values += [coefficient, -coefficient]
        # else: a genuine boundary face is zero-gradient by PISO's own
        # construction and contributes nothing -- skip.

    indices = torch.tensor([rows, cols], dtype=torch.long)
    return torch.sparse_coo_tensor(
        indices, torch.tensor(values, dtype=torch.float64), (mesh.num_cells, mesh.num_cells)
    ).to_dense()


def _piso_for_matrix_tests(periodic_pairs: dict[str, str] | None = None) -> PISO:
    from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver

    condition = _ZeroNormalVelocity()
    boundary_conditions: dict[str, BoundaryCondition] = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=500)
    return PISO(solver, boundary_conditions, periodic_pairs=periodic_pairs or {})


def test_poisson_matrix_matches_hand_derived_values_on_a_small_interior_only_mesh() -> None:
    # `default_mesh(extent=(2, 1))`: two cells, exactly one interior face
    # between them (a single row, so every horizontal face is a
    # boundary), no periodicity. `DEFAULT_SPACING = (0.2, 0.3)`: the one
    # interior face is vertical (area = dy = 0.3), centroid distance
    # dx = 0.2, cell volume dx*dy = 0.06 -- coefficient = 1.0 * 0.3 /
    # (0.2 * 0.06) = 25.0, by hand.
    mesh = default_mesh(extent=(2, 1))
    piso = _piso_for_matrix_tests()

    matrix = piso._poisson_matrix(mesh).to_dense()
    expected = torch.tensor([[25.0, -25.0], [-25.0, 25.0]], dtype=torch.float64)
    assert torch.allclose(matrix, expected, atol=1e-9)


@pytest.mark.parametrize(
    ("extent", "periodic_pairs"),
    [
        pytest.param((3, 2), {}, id="no-periodicity"),
        pytest.param(
            (4, 3),
            {"east": "west", "west": "east"},
            id="one-axis-periodic-no-coincidence",
        ),
        pytest.param(
            (3, 2),
            {"north": "south", "south": "north", "east": "west", "west": "east"},
            id="fully-periodic-coincides-with-interior-connection",
        ),
        pytest.param(
            (2, 3),
            {"east": "west", "west": "east"},
            id="one-axis-periodic-coincides-with-interior-connection",
        ),
    ],
)
def test_poisson_matrix_matches_independent_reference_construction(
    extent: tuple[int, int], periodic_pairs: dict[str, str]
) -> None:
    mesh = default_mesh(extent=extent)
    piso = _piso_for_matrix_tests(periodic_pairs)

    actual = piso._poisson_matrix(mesh).to_dense()
    expected = _reference_poisson_matrix(mesh, periodic_pairs)
    assert torch.allclose(actual, expected, atol=1e-9), f"actual:\n{actual}\nexpected:\n{expected}"


def test_poisson_matrix_raises_for_non_uniform_cell_volume() -> None:
    from pyflow.engine.numerics.pressure_coupling import NonUniformCellVolumeError

    class _NonUniformVolumeMesh(StructuredCartesianMesh):
        def cell_volume(self, cell: int) -> float:
            base = super().cell_volume(cell)
            return base * 2.0 if cell == 0 else base

    mesh = _NonUniformVolumeMesh(origin=DEFAULT_ORIGIN, spacing=DEFAULT_SPACING, extent=(2, 1))
    piso = _piso_for_matrix_tests()

    with pytest.raises(NonUniformCellVolumeError):
        piso._poisson_matrix(mesh)


def test_poisson_matrix_raises_for_non_zero_gradient_pressure_boundary() -> None:
    from pyflow.engine.numerics.pressure_coupling import (
        UnsupportedPressureBoundaryConditionError,
    )

    mesh = default_mesh(extent=(2, 1))
    piso = _piso_for_matrix_tests()
    # Reach into PISO's own internal state deliberately, the same
    # "private, on purpose" precedent `piso._cached_poisson_matrix`
    # already sets above -- corrupting the one invariant this test
    # exists to guard.
    piso._pressure_boundary_conditions = {
        name: FixedGradientCondition(gradient=1.0) for name in ("north", "south", "east", "west")
    }

    with pytest.raises(UnsupportedPressureBoundaryConditionError):
        piso._poisson_matrix(mesh)
