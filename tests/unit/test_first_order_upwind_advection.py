"""Binds `tests/features/first_order_upwind_advection.feature` (TASK-023)
-- Stage 4's first real numerical scheme, and Stage 4 Completion
Criterion 4's own claim for it: bounded, and (two distinct claims)
conservative on a closed domain and on a fully periodic one, with
boundedness explicitly not the same claim as stability. The periodic
conservation scenario was added by the 2026-08-28 Stage 4 exit audit,
which found the closed-domain one passing for any flux array whatsoever
-- see `src/pyflow/engine/CLAUDE.md`'s `FirstOrderUpwindAdvection` entry
for what a conservation scenario can and cannot test.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from dataclasses import field as dataclass_field

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import (
    FirstOrderUpwindAdvection,
    UnconfiguredBoundaryFaceError,
)
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import accumulate_flux_to_cells
from pyflow.engine.vector_field import VectorField

from ._numerics import (
    FixedGradientCondition,
    FixedValueCondition,
    default_mesh,
    face_normal_velocity,
    zero_gradient_everywhere,
)

scenarios("first_order_upwind_advection.feature")


# -- Fixture context -----------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    scalar: ScalarField
    velocity: VectorField
    boundary_conditions: dict[str, BoundaryCondition]
    periodic_pairs: dict[str, str] = dataclass_field(default_factory=dict)
    flux: torch.Tensor | None = None
    error: Exception | None = None
    target_face: int | None = None
    prescribed_value: float | None = None
    history: list[torch.Tensor] | None = None
    dt: float | None = None


def _run_flux(ctx: _Context) -> None:
    scheme = FirstOrderUpwindAdvection(ctx.boundary_conditions, ctx.periodic_pairs)
    try:
        ctx.flux = scheme.flux(ctx.scalar, ctx.velocity)
    except UnconfiguredBoundaryFaceError as exc:
        ctx.error = exc


# -- Given -----------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    mesh = default_mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    scalar = ScalarField(mesh, "temperature", initial_value=0.0)
    return _Context(
        mesh=mesh, scalar=scalar, velocity=velocity, boundary_conditions=zero_gradient_everywhere()
    )


@given("a non-monotonic field and a velocity not aligned with either mesh axis")
def _given_non_monotonic_field(ctx: _Context) -> None:
    values = [5.0, 1.0, 8.0, 2.0, 9.0, 3.0]
    for cell, value in enumerate(values):
        ctx.scalar.set_value_at(cell, value)
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.3, -0.7))


@given("a boundary face where the flow points out of the domain")
def _given_outflow_boundary(ctx: _Context) -> None:
    # west's canonical normal is (-1, 0); velocity (-1, 0) gives
    # velocity_normal = (-1)*(-1) = +1 -- outflow, by this scheme's own
    # convention (velocity_normal >= 0 means the owner is upstream).
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(-1.0, 0.0))
    ctx.scalar = ScalarField(ctx.mesh, "temperature", initial_value=1.0)
    ctx.target_face = next(
        f for f in range(ctx.mesh.num_faces) if ctx.mesh.boundary_face_name(f) == "west"
    )


@given("that boundary's own condition prescribes a value the interior cell does not have")
def _given_outflow_condition(ctx: _Context) -> None:
    ctx.prescribed_value = 99.0
    condition = FixedValueCondition(ctx.prescribed_value)
    ctx.boundary_conditions = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }


@given("a boundary face where the flow points into the domain")
def _given_inflow_boundary(ctx: _Context) -> None:
    # west's canonical normal is (-1, 0); velocity (+1, 0) gives
    # velocity_normal = 1*(-1) = -1 -- inflow.
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.scalar = ScalarField(ctx.mesh, "temperature", initial_value=1.0)
    ctx.target_face = next(
        f for f in range(ctx.mesh.num_faces) if ctx.mesh.boundary_face_name(f) == "west"
    )


@given("that boundary's own condition prescribes a fixed value")
def _given_inflow_value_condition(ctx: _Context) -> None:
    ctx.prescribed_value = 7.5
    ctx.boundary_conditions = {"west": FixedValueCondition(ctx.prescribed_value)}


@given("that boundary's own condition prescribes a gradient instead of a value")
def _given_inflow_gradient_condition(ctx: _Context) -> None:
    ctx.boundary_conditions = {"west": FixedGradientCondition(-3.0)}


@given("that boundary has no configured condition at all")
def _given_no_condition(ctx: _Context) -> None:
    ctx.boundary_conditions = {}


@given("a one-dimensional line of cells with a single non-zero pulse", target_fixture="ctx")
def _given_line_with_pulse() -> _Context:
    dx = 0.5
    mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(dx, 1.0), extent=(10, 1))
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    scalar = ScalarField(mesh, "temperature", initial_value=0.0)
    scalar.set_value_at(mesh.num_cells // 2, 10.0)
    ctx = _Context(
        mesh=mesh, scalar=scalar, velocity=velocity, boundary_conditions=zero_gradient_everywhere()
    )
    ctx.history = [scalar.values.clone()]
    return ctx


@given("zero-gradient conditions at both ends")
def _given_zero_gradient_ends(ctx: _Context) -> None:
    ctx.boundary_conditions = zero_gradient_everywhere()


@given("a domain whose boundary cells all have zero velocity", target_fixture="ctx")
def _given_zero_boundary_velocity() -> _Context:
    mesh = default_mesh(extent=(4, 3))
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    scalar = ScalarField(mesh, "temperature")
    initial_values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0]
    for cell, value in enumerate(initial_values):
        scalar.set_value_at(cell, value)
    ctx = _Context(
        mesh=mesh, scalar=scalar, velocity=velocity, boundary_conditions=zero_gradient_everywhere()
    )
    ctx.history = [scalar.values.clone()]
    return ctx


@given("interior cells with a nonzero velocity")
def _given_interior_velocity(ctx: _Context) -> None:
    assert isinstance(ctx.mesh, StructuredCartesianMesh)
    nx, ny = 4, 3
    for i in range(1, nx - 1):
        for j in range(1, ny - 1):
            ctx.velocity.set_value_at(ctx.mesh.cell_id(i, j), (1.7, -0.9))


@given(
    "a fully periodic domain and a velocity aligned with neither mesh axis",
    target_fixture="ctx",
)
def _given_fully_periodic_domain() -> _Context:
    """Every edge periodic, so every boundary face carries a genuinely
    nonzero flux -- unlike the closed-domain fixture above, whose
    zero-velocity boundary cells make every boundary flux zero whatever
    face value the scheme picks.

    Conservation here is a real property of the wrap accounting:
    `accumulate_flux_to_cells` credits a periodic face's contribution to
    its owner alone (the mesh reports no neighbour), so the two faces of
    a periodic pair cancel globally only if both resolve the same
    upstream cell. A wrapped-neighbour lookup does; a mirrored or
    clamped one does not, and the total then drifts. No boundary
    condition is configured at all -- a periodic face must never consult
    one, so an empty mapping is the fixture that proves it doesn't.
    """
    mesh = default_mesh(extent=(4, 3))
    # Neither component zero and the two unequal, so the wrap is
    # exercised on both axes at once and no coincidence of dx == dy or
    # u == v can make a wrong accounting agree with a right one
    # (`docs/practices.md`, "Verify a conversion where its factors are
    # distinct").
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(1.7, -0.9))
    scalar = ScalarField(mesh, "temperature")
    initial_values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0]
    for cell, value in enumerate(initial_values):
        scalar.set_value_at(cell, value)
    ctx = _Context(
        mesh=mesh,
        scalar=scalar,
        velocity=velocity,
        boundary_conditions={},
        periodic_pairs={"north": "south", "south": "north", "east": "west", "west": "east"},
    )
    ctx.history = [scalar.values.clone()]
    return ctx


# -- When ------------------------------------------------------------------


@when("the advective flux is computed")
def _when_flux_computed(ctx: _Context) -> None:
    _run_flux(ctx)


@when("the field is advanced for several timesteps at half the CFL limit")
def _when_advanced_stable(ctx: _Context) -> None:
    dx = 0.5
    u0 = 1.0
    ctx.dt = 0.5 * dx / u0
    _advance(ctx, steps=8)


@when("the field is advanced for several timesteps at twice the CFL limit")
def _when_advanced_unstable(ctx: _Context) -> None:
    dx = 0.5
    u0 = 1.0
    ctx.dt = 2.0 * dx / u0
    _advance(ctx, steps=8)


@when("the field is advanced for many timesteps")
def _when_advanced_many(ctx: _Context) -> None:
    ctx.dt = 0.01
    _advance(ctx, steps=20)


def _advance(ctx: _Context, steps: int) -> None:
    assert ctx.dt is not None
    assert ctx.history is not None
    scheme = FirstOrderUpwindAdvection(ctx.boundary_conditions, ctx.periodic_pairs)
    scalar = ctx.scalar
    for _ in range(steps):
        flux = scheme.flux(scalar, ctx.velocity)
        derivative = accumulate_flux_to_cells(ctx.mesh, -flux)
        advanced = scalar.copy()
        advanced.values[:] = scalar.values + ctx.dt * derivative
        scalar = advanced
        ctx.history.append(scalar.values.clone())
    ctx.scalar = scalar


# -- Then ------------------------------------------------------------------


@then(
    "every interior face's implied value equals its owner's or its neighbour's own value, "
    "within the range of the two"
)
def _then_bounded(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert isinstance(ctx.scalar, ScalarField)
    for face in range(ctx.mesh.num_faces):
        owner, neighbour = ctx.mesh.face_neighbours(face)
        if neighbour is None:
            continue
        velocity_normal = face_normal_velocity(ctx.mesh, ctx.velocity, face)
        implied = float(ctx.flux[face]) / velocity_normal
        owner_value = ctx.scalar.value_at(owner)
        neighbour_value = ctx.scalar.value_at(neighbour)
        low, high = sorted((owner_value, neighbour_value))
        assert low - 1e-9 <= implied <= high + 1e-9, (
            f"face {face}: implied value {implied} outside [{low}, {high}]"
        )
        # Recovered by dividing back through `velocity_normal` -- not
        # bit-exact, so this is a tolerance comparison, not `==`.
        assert math.isclose(implied, owner_value, abs_tol=1e-9) or math.isclose(
            implied, neighbour_value, abs_tol=1e-9
        )


@then(
    "the outflow boundary face's implied value is the interior cell's own value, "
    "not the boundary condition's"
)
def _then_outflow_uses_owner(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    velocity_normal = face_normal_velocity(ctx.mesh, ctx.velocity, ctx.target_face)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert isinstance(ctx.scalar, ScalarField)
    assert implied == ctx.scalar.value_at(owner)
    assert ctx.prescribed_value is not None
    assert implied != ctx.prescribed_value


@then("the inflow boundary face's implied value is exactly the prescribed value")
def _then_inflow_uses_prescribed_value(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_value is not None
    velocity_normal = face_normal_velocity(ctx.mesh, ctx.velocity, ctx.target_face)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert implied == ctx.prescribed_value


@then("the inflow boundary face's implied value is the interior cell's own value")
def _then_inflow_extrapolates_owner(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    velocity_normal = face_normal_velocity(ctx.mesh, ctx.velocity, ctx.target_face)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert isinstance(ctx.scalar, ScalarField)
    assert implied == ctx.scalar.value_at(owner)


@then("an UnconfiguredBoundaryFaceError is raised")
def _then_unconfigured_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, UnconfiguredBoundaryFaceError)


@then("the field's magnitude never exceeds its initial maximum at any step")
def _then_never_exceeds_initial_max(ctx: _Context) -> None:
    assert ctx.history is not None
    initial_max = float(ctx.history[0].abs().max())
    for step, snapshot in enumerate(ctx.history[1:], start=1):
        current_max = float(snapshot.abs().max())
        assert current_max <= initial_max + 1e-9, (
            f"step {step}: |field| grew to {current_max}, above the initial {initial_max}"
        )


@then("the field's magnitude grows far beyond its initial maximum")
def _then_grows_far_beyond_initial_max(ctx: _Context) -> None:
    assert ctx.history is not None
    initial_max = float(ctx.history[0].abs().max())
    final_max = float(ctx.history[-1].abs().max())
    assert final_max > 100 * initial_max, (
        f"expected clear divergence, got final max {final_max} vs initial {initial_max}"
    )


@then("the field's total summed over every cell is unchanged to floating-point tolerance")
def _then_total_conserved(ctx: _Context) -> None:
    assert ctx.history is not None
    initial_total = float(ctx.history[0].sum())
    final_total = float(ctx.history[-1].sum())
    assert abs(final_total - initial_total) < 1e-9, (
        f"total drifted from {initial_total} to {final_total}"
    )
