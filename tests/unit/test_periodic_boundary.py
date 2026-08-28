"""Binds `tests/features/periodic_boundary.feature` (TASK-030) -- Stage
4's ninth and last task. Periodic bypasses `BoundaryCondition` entirely
(`docs/planning/roadmap.md` TASK-030's own Design decision): a real
Advection/Diffusion scheme wired with a `periodic_pairs` mapping must
consult the wrapped-neighbour cell directly, through the same formula it
already uses for a genuine interior neighbour, never a `BoundaryCondition`
-- so unlike `test_dirichlet_boundary.py`/`test_neumann_boundary.py`,
there is no condition class under test here at all, only the mesh's own
`wrapped_neighbour_cell` (`test_structured_cartesian_mesh.py`) and the two
real schemes' own wiring to it.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PressureCoupling
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import step as simulation_step
from pyflow.engine.vector_field import VectorField

scenarios("periodic_boundary.feature")

_GAMMA = 2.0
"""Not `1.0` -- same reasoning as every other diffusion scenario's own
identically-named constant in this repository.
"""


class _FixedGradientCondition(BoundaryCondition):
    """Zero-gradient, for the non-periodic boundary faces the round-trip
    scenario's own mesh still needs *something* configured for (diffusion
    has no inflow/outflow carve-out) -- never the mechanism under test.
    """

    def __init__(self, gradient: float = 0.0) -> None:
        self._gradient = gradient

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._gradient


class _InertLinearSolver(LinearSolver):
    """`AssembledNumerics` requires one to construct at all; `step` never
    calls it -- same precedent as `test_simulation.py`'s own double.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=False, iterations=0)


class _InertPressureCoupling(PressureCoupling):
    """Same reasoning as `_InertLinearSolver` above."""

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        del dt
        return provisional_velocity.copy(), ScalarField(provisional_velocity.mesh, "pressure")


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    scalar: ScalarField
    velocity: VectorField
    boundary_conditions: dict[str, BoundaryCondition]
    periodic_pairs: dict[str, str]
    flux: torch.Tensor | None = None
    target_face: int | None = None
    wrapped_neighbour: int | None = None
    velocity_x: float | None = None
    round_trip_errors: tuple[float, float] | None = None


def _mesh() -> StructuredCartesianMesh:
    # Non-"nice" origin/spacing and a non-square extent, matching every
    # other contract suite's fixture in this repository.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(4, 2))


def _distinct_scalar(mesh: StructuredCartesianMesh) -> ScalarField:
    # Every cell gets a genuinely different value -- a wrong wrapped-cell
    # id (or a mirrored/clamped-to-owner fallback) would read a
    # coincidentally-equal value for at most one cell, never for every
    # face this file exercises.
    return ScalarField(mesh, "tracer", initial_value=lambda x, y: 10 * x + 100 * y)


def _west_face(mesh: StructuredCartesianMesh) -> int:
    return next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "west")


def _face_normal_velocity(ctx: _Context, face: int, neighbour: int | None) -> float:
    """Independently derived, not calling into either scheme under test --
    same reasoning `test_neumann_boundary.py`'s own identically-named
    helper states.
    """
    owner, _ = ctx.mesh.face_neighbours(face)
    normal_x, normal_y = ctx.mesh.face_normal(face)
    owner_x, owner_y = ctx.velocity.value_at(owner)
    if neighbour is None:
        v_x, v_y = owner_x, owner_y
    else:
        neighbour_x, neighbour_y = ctx.velocity.value_at(neighbour)
        v_x, v_y = (owner_x + neighbour_x) / 2, (owner_y + neighbour_y) / 2
    return v_x * normal_x + v_y * normal_y


# -- Given -------------------------------------------------------------


@given(
    "a small, non-square, non-trivially-origined mesh whose cells each hold a distinct value",
    target_fixture="ctx",
)
def _given_default_mesh() -> _Context:
    mesh = _mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    scalar = _distinct_scalar(mesh)
    return _Context(
        mesh=mesh,
        scalar=scalar,
        velocity=velocity,
        boundary_conditions={
            "north": _FixedGradientCondition(),
            "south": _FixedGradientCondition(),
            "east": _FixedGradientCondition(),
        },
        periodic_pairs={},
    )


@given("a west boundary face configured periodic with its east partner")
def _given_periodic_west(ctx: _Context) -> None:
    ctx.target_face = _west_face(ctx.mesh)
    ctx.periodic_pairs = {"west": "east", "east": "west"}
    ctx.wrapped_neighbour = ctx.mesh.wrapped_neighbour_cell(ctx.target_face)


@given("no boundary condition configured for that face at all")
def _given_no_condition_for_that_face(ctx: _Context) -> None:
    ctx.boundary_conditions = {
        name: condition for name, condition in ctx.boundary_conditions.items() if name != "west"
    }


@given("a mesh whose east and west edges are both periodic")
def _given_fully_periodic_mesh(ctx: _Context) -> None:
    ctx.periodic_pairs = {"west": "east", "east": "west"}


@given(
    "a uniform velocity field that carries the domain's own scalar field once fully around it "
    "in a whole number of real timesteps"
)
def _given_uniform_round_trip_velocity(ctx: _Context) -> None:
    ctx.velocity_x = 1.0


# -- When --------------------------------------------------------------


@when("the advective flux is computed with inflow at that face")
def _when_advective_flux(ctx: _Context) -> None:
    scheme = FirstOrderUpwindAdvection(ctx.boundary_conditions, ctx.periodic_pairs)
    # west's canonical normal is (-1, 0); velocity (+1, 0) gives
    # velocity_normal = 1*(-1) = -1 -- inflow, same reasoning as
    # `test_neumann_boundary.py`'s own identically-shaped step.
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.flux = scheme.flux(ctx.scalar, ctx.velocity)


@when("the diffusive flux is computed at that face")
def _when_diffusive_flux(ctx: _Context) -> None:
    scheme = CentralDifferenceDiffusion(ctx.boundary_conditions, ctx.periodic_pairs, _GAMMA)
    ctx.flux = scheme.flux(ctx.scalar)


def _round_trip_error(
    nx: int, num_steps: int, velocity_x: float, periodic_pairs: dict[str, str]
) -> float:
    """One lap around a periodic domain at resolution `nx`, `num_steps`
    real RK4 timesteps (chosen equal to `nx`, i.e. Courant number ~1 --
    verified numerically that refining time alone barely moves this
    error, since it is dominated by first-order upwind's own spatial
    truncation, not time-integration error), returning the max absolute
    difference between the field's final and starting values.

    A fresh sine-in-x pattern (period equal to the domain width, so it is
    genuinely periodic-compatible -- unlike a plain linear ramp, which
    creates an artificial discontinuity at the wrap seam that numerical
    diffusion then smooths, confounding this specific claim, found by
    running exactly that fixture first) plus a `100 * y` term, so every
    row is checked, not only one.
    """
    origin = (0.5, -1.0)
    spacing = (0.8 / nx, 0.3)
    mesh = StructuredCartesianMesh(origin=origin, spacing=spacing, extent=(nx, 2))
    dx, _ = spacing
    domain_width = nx * dx
    x0 = origin[0]

    def pattern(x: float, y: float) -> float:
        return math.sin(2 * math.pi * (x - x0) / domain_width) + 100 * y

    scalar = ScalarField(mesh, "tracer", initial_value=pattern)
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(velocity_x, 0.0))
    solver = _InertLinearSolver()
    numerics = AssembledNumerics(
        advection=FirstOrderUpwindAdvection({}, periodic_pairs),
        diffusion=_ZeroDiffusion(),
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=_InertPressureCoupling(solver),
        boundary_conditions={},
        names={},
    )
    dt = domain_width / (velocity_x * num_steps)
    fields: dict[str, Field] = {"tracer": scalar}
    for _ in range(num_steps):
        fields = simulation_step(fields, velocity, numerics, dt)
    tracer = fields["tracer"]
    assert isinstance(tracer, ScalarField)
    return float((tracer.values - scalar.values).abs().max())


@when(
    "the field is advected for exactly that many real timesteps, at two mesh resolutions "
    "four times apart"
)
def _when_advected_at_two_resolutions(ctx: _Context) -> None:
    assert ctx.velocity_x is not None
    coarse = _round_trip_error(16, 16, ctx.velocity_x, ctx.periodic_pairs)
    fine = _round_trip_error(64, 64, ctx.velocity_x, ctx.periodic_pairs)
    ctx.round_trip_errors = (coarse, fine)


# -- Then ----------------------------------------------------------------


@then(
    "the inflow boundary face's implied value is the wrapped neighbour's own value, not the owner's"
)
def _then_advection_reads_wrapped_neighbour(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.wrapped_neighbour is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    velocity_normal = _face_normal_velocity(ctx, ctx.target_face, ctx.wrapped_neighbour)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert implied == ctx.scalar.value_at(ctx.wrapped_neighbour)
    assert implied != ctx.scalar.value_at(owner)


@then(
    "that boundary face's flux equals the diffusion coefficient times the difference "
    "between the wrapped neighbour's and the owner's own value, divided by one full "
    "grid spacing"
)
def _then_diffusion_uses_wrapped_neighbour_at_full_spacing(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.wrapped_neighbour is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    distance = 2 * ctx.mesh.face_centroid_distance(ctx.target_face)
    expected = (
        _GAMMA
        * (ctx.scalar.value_at(ctx.wrapped_neighbour) - ctx.scalar.value_at(owner))
        / distance
    )
    assert math.isclose(float(ctx.flux[ctx.target_face]), expected, abs_tol=1e-9)


@then(
    "the round-trip error at the finer resolution is well under two thirds of the "
    "error at the coarser one"
)
def _then_error_shrinks_with_refinement(ctx: _Context) -> None:
    assert ctx.round_trip_errors is not None
    coarse, fine = ctx.round_trip_errors
    assert fine < (2 / 3) * coarse, (
        f"fine-resolution round-trip error {fine} did not drop meaningfully below "
        f"two thirds of the coarse-resolution error {coarse} -- a wrapped-neighbour "
        "implementation should converge toward the starting distribution as the mesh "
        "is refined; a mirrored/clamped one measurably does not (see this scenario's "
        "own comment in periodic_boundary.feature)"
    )


# -- Local doubles (defined after use above is fine at import time; kept
# near the bottom since only the round-trip scenario needs it) ----------


class _ZeroDiffusion(CentralDifferenceDiffusion):
    """No diffusion at all -- the round-trip scenario is specifically an
    *advection* claim (`periodic_boundary.feature`'s own comment):
    diffusion's own periodic wiring is already checked directly by the
    scenario above, and diffusion is irreversible, so including a real
    one here would falsify this claim rather than test it.
    """

    def __init__(self) -> None:
        super().__init__({}, {}, 1.0)

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)
