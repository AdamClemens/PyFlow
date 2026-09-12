"""Binds `tests/features/boundary_velocity.feature` (TASK-052, Stage 9's
first task) -- Stage 9 Completion Criteria 1 and 2: a boundary face's
transporting velocity comes from what the configuration prescribes
there, and every operator that needs that number resolves it through one
shared function.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`). The
stage's visible demonstration is Sealed Box
(`tests/golden/test_sealed_box.py`), which makes the same claim through
the public CLI.

**The sealed-cavity fixture goes through `assemble_numerics` rather than
constructing the six schemes directly**, unlike most modules here. That
is deliberate: the defect this task fixes was a disagreement between two
operators that a real run assembles together, so a fixture that builds
them separately could wire them consistently by hand and prove nothing
about what a configuration actually produces.
"""

from __future__ import annotations

import inspect
import math
from dataclasses import dataclass

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    NumericsConfig,
)
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics import advection as advection_module
from pyflow.engine.numerics import divergence as divergence_module
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import AssembledNumerics, assemble_numerics
from pyflow.engine.numerics.boundary_condition import (
    BoundaryCondition,
    DirichletBoundaryCondition,
    NeumannBoundaryCondition,
)
from pyflow.engine.numerics.divergence import GreenGaussDivergence
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import navier_stokes_step, stable_timestep
from pyflow.engine.vector_field import VectorField

from ._numerics import default_mesh, west_face

scenarios("boundary_velocity.feature")


# -- The sealed cavity -------------------------------------------------------

_CAVITY_EXTENT = (10, 10)
_CAVITY_SPACING = 0.1
_CAVITY_ORIGIN = (0.35, -0.2)
"""Non-trivial, per Stage 5 Completion Criterion 7's degenerate-fixture
rule -- nothing here compares against a reference that fixes the frame,
so there is no reason to sit at the origin.
"""

_CAVITY_VISCOSITY = 0.01
_CAVITY_STEPS = 150
"""Measured, not guessed: at this size and step count the tracer's own
peak-to-peak change is 0.75 (so it genuinely moves) and the pre-fix
engine loses **4.54%** of it through the walls, against the exact
conservation below. A shorter run leaks less and proves less.
"""

_CONSERVATION_TOLERANCE = 1e-12
"""Relative. "Exactly" is the claim -- with zero normal velocity on every
wall each boundary face's flux is exactly `0.0 * phi`, and interior faces
cancel pairwise inside `accumulate_flux_to_cells`, so the only drift
available is floating-point summation order. Measured drift is `0.0` to
every digit printed; this bound is a floor, not a fitted tolerance.
"""


def _cavity_numerics() -> AssembledNumerics:
    """A lid-driven cavity's own numerics, assembled the way a real run
    assembles them -- the tracer's diffusion coefficient is `0.0` so that
    advection is the only transport left, which is what makes exact
    conservation the right claim rather than an approximate one.
    """
    lid = BoundaryFaceConfig(type="dirichlet", field_values={"velocity.0": 1.0, "velocity.1": 0.0})
    wall = BoundaryFaceConfig(type="dirichlet")
    return assemble_numerics(
        NumericsConfig(
            boundary_conditions=BoundaryConditionsConfig(
                north=lid, south=wall, east=wall, west=wall
            ),
            pressure_correction_tolerance=1e-8,
            pressure_correction_max_iterations=200,
        ),
        0.0,
        {"velocity.0": _CAVITY_VISCOSITY, "velocity.1": _CAVITY_VISCOSITY},
    )


def _cavity_mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(
        origin=_CAVITY_ORIGIN,
        spacing=(_CAVITY_SPACING, _CAVITY_SPACING),
        extent=_CAVITY_EXTENT,
    )


def _tracer(mesh: StructuredCartesianMesh) -> ScalarField:
    """A blob offset below the lid, so the cavity's own circulation
    carries it against three of the four walls over the run rather than
    sitting still in the middle.
    """
    width = _CAVITY_EXTENT[0] * _CAVITY_SPACING
    center_x = _CAVITY_ORIGIN[0] + 0.5 * width
    center_y = _CAVITY_ORIGIN[1] + 0.35 * width
    sigma = 0.18 * width
    return ScalarField(
        mesh,
        "tracer",
        initial_value=lambda x, y: math.exp(
            -((x - center_x) ** 2 + (y - center_y) ** 2) / (2 * sigma**2)
        ),
    )


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    numerics: AssembledNumerics | None = None
    fields: dict[str, Field] | None = None
    initial_tracer: torch.Tensor | None = None
    flux: torch.Tensor | None = None
    divergence: torch.Tensor | None = None
    boundary_conditions: dict[str, BoundaryCondition] | None = None
    velocity: VectorField | None = None
    scalar: ScalarField | None = None
    target_face: int | None = None
    prescribed_velocity: float | None = None
    prescribed_value: float | None = None


# -- Given -------------------------------------------------------------------


@given("the advection scheme's source and the divergence scheme's source", target_fixture="ctx")
def _given_both_sources() -> _Context:
    return _Context(mesh=default_mesh())


@given(
    "a closed no-slip cavity carrying a tracer, with the tracer's diffusion switched off",
    target_fixture="ctx",
)
def _given_sealed_cavity() -> _Context:
    mesh = _cavity_mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    fields: dict[str, Field] = {c.name: c for c in velocity.decompose()}
    fields["tracer"] = _tracer(mesh)
    return _Context(mesh=mesh, numerics=_cavity_numerics(), fields=fields)


def _boundary_fixture(prescribed_velocity: float | None, gradient: bool = False) -> _Context:
    """One west-boundary fixture for every Criterion 2 scenario.

    `prescribed_value` (`3.0`) is the *scalar's* boundary value and
    `prescribed_velocity` the boundary's own normal component -- two
    numbers, deliberately different from each other and from every
    interior value, so no scenario below can pass by confusing one for
    another (`docs/practices.md`, "Verify a conversion where its factors
    are distinct"). West's canonical normal is `(-1, 0)` and the
    convention is positive outward, so a negative prescribed velocity is
    inflow.
    """
    mesh = default_mesh(extent=(3, 2))
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.5, 0.0))
    scalar = ScalarField(mesh, "tracer", initial_value=1.0)
    condition: BoundaryCondition
    if gradient:
        condition = NeumannBoundaryCondition(0.0)
    else:
        overrides = {} if prescribed_velocity is None else {"velocity": prescribed_velocity}
        condition = DirichletBoundaryCondition(3.0, overrides)
    # Only west carries the scenario's own condition; the other three
    # extrapolate, so the west face is the only thing that can move any
    # assertion below. With a uniform horizontal velocity the north and
    # south faces then contribute exactly zero, which is what makes the
    # divergence scenario's hand-derivation a two-term sum.
    conditions: dict[str, BoundaryCondition] = {
        name: NeumannBoundaryCondition(0.0) for name in ("north", "south", "east")
    }
    conditions["west"] = condition
    return _Context(
        mesh=mesh,
        velocity=velocity,
        scalar=scalar,
        boundary_conditions=conditions,
        target_face=west_face(mesh),
        prescribed_velocity=prescribed_velocity,
        prescribed_value=3.0,
    )


@given(
    "a boundary prescribing an inward normal velocity, and a different boundary value for the "
    "transported field",
    target_fixture="ctx",
)
def _given_inflow_boundary() -> _Context:
    return _boundary_fixture(prescribed_velocity=-2.0)


@given(
    "a boundary prescribing an outward normal velocity, and a different boundary value for the "
    "transported field",
    target_fixture="ctx",
)
def _given_outflow_boundary() -> _Context:
    return _boundary_fixture(prescribed_velocity=2.0)


@given(
    "a boundary prescribing no normal velocity, and a boundary value for the transported field",
    target_fixture="ctx",
)
def _given_no_prescribed_velocity() -> _Context:
    # No `"velocity"` override at all, so the condition falls through to
    # its own prescribed value's default of `0.0` -- the no-penetration
    # wall every configuration in this repository ships.
    return _boundary_fixture(prescribed_velocity=None)


@given("a boundary prescribing a velocity gradient rather than a value", target_fixture="ctx")
def _given_gradient_boundary() -> _Context:
    return _boundary_fixture(prescribed_velocity=None, gradient=True)


# -- When --------------------------------------------------------------------


@when("the simulation is advanced for many timesteps")
def _when_advanced(ctx: _Context) -> None:
    assert ctx.numerics is not None
    assert ctx.fields is not None
    tracer = ctx.fields["tracer"]
    assert isinstance(tracer, ScalarField)
    ctx.initial_tracer = tracer.values.clone()
    dt = stable_timestep(ctx.mesh, _CAVITY_VISCOSITY, velocity_scale=1.0)
    fields = ctx.fields
    for _ in range(_CAVITY_STEPS):
        fields = navier_stokes_step(fields, "velocity", ctx.numerics, dt).fields
    ctx.fields = fields


@when("the advective flux is computed")
def _when_flux_computed(ctx: _Context) -> None:
    assert ctx.boundary_conditions is not None
    assert ctx.velocity is not None
    assert ctx.scalar is not None
    scheme = FirstOrderUpwindAdvection(ctx.boundary_conditions, {})
    ctx.flux = scheme.flux(ctx.scalar, ctx.velocity)


@when("the velocity field's divergence is computed")
def _when_divergence_computed(ctx: _Context) -> None:
    assert ctx.boundary_conditions is not None
    assert ctx.velocity is not None
    scheme = GreenGaussDivergence(ctx.boundary_conditions, {})
    ctx.divergence = scheme.divergence(ctx.velocity)


# -- Then --------------------------------------------------------------------


@then(
    "both call boundary_normal_velocity, and neither decides a boundary's normal velocity for "
    "itself"
)
def _then_one_shared_resolver(ctx: _Context) -> None:
    del ctx
    advection_source = inspect.getsource(advection_module)
    divergence_source = inspect.getsource(divergence_module)
    for name, source in (
        ("advection", advection_source),
        ("divergence", divergence_source),
    ):
        assert "boundary_normal_velocity(" in source, (
            f"{name}.py no longer calls the shared resolver; two operators deciding a wall's "
            "normal velocity separately is the defect Stage 9 Criterion 1 exists to prevent"
        )
        assert "def boundary_normal_velocity" not in source, (
            f"{name}.py defines its own boundary-normal-velocity resolver; there must be exactly "
            "one, in boundary_condition.py"
        )


@then("the tracer's domain integral is unchanged to floating-point tolerance")
def _then_tracer_conserved(ctx: _Context) -> None:
    assert ctx.fields is not None
    assert ctx.initial_tracer is not None
    tracer = ctx.fields["tracer"]
    assert isinstance(tracer, ScalarField)
    before = float(ctx.initial_tracer.sum())
    after = float(tracer.values.sum())
    assert abs(after - before) <= _CONSERVATION_TOLERANCE * abs(before), (
        f"a sealed domain must conserve a purely advected tracer exactly; its integral went "
        f"{before} -> {after}, a relative change of {(after - before) / before}"
    )


@then("the tracer's own spatial distribution has measurably changed")
def _then_tracer_moved(ctx: _Context) -> None:
    assert ctx.fields is not None
    assert ctx.initial_tracer is not None
    tracer = ctx.fields["tracer"]
    assert isinstance(tracer, ScalarField)
    moved = float((tracer.values - ctx.initial_tracer).abs().max())
    # Measured 0.75 on this fixture. A tracer that never moved would
    # conserve its integral trivially, which is the vacuous pass the
    # scenario above needs this one to rule out.
    assert moved > 0.1, (
        f"the tracer must actually be transported for its conservation to mean anything; its "
        f"largest per-cell change over the run was {moved}"
    )


@then("every wall face's advective flux is exactly zero")
def _then_no_wall_flux(ctx: _Context) -> None:
    assert ctx.fields is not None
    assert ctx.numerics is not None
    tracer = ctx.fields["tracer"]
    assert isinstance(tracer, ScalarField)
    components = [ctx.fields[VectorField.component_name("velocity", i)] for i in range(2)]
    velocity = VectorField.assemble(components, "velocity")  # type: ignore[arg-type]
    flux = ctx.numerics.advection.flux(tracer, velocity)
    for face in range(ctx.mesh.num_faces):
        if ctx.mesh.face_neighbours(face)[1] is None:
            assert float(flux[face]) == 0.0, (
                f"wall face {face} ({ctx.mesh.boundary_face_name(face)}) carries advective flux "
                f"{float(flux[face])}; a wall prescribing zero normal velocity must carry none"
            )


@then("the cells behind those walls still carry real motion")
def _then_wall_cells_move(ctx: _Context) -> None:
    assert ctx.fields is not None
    components = [ctx.fields[VectorField.component_name("velocity", i)] for i in range(2)]
    velocity = VectorField.assemble(components, "velocity")  # type: ignore[arg-type]
    boundary_owners = {
        ctx.mesh.face_neighbours(face)[0]
        for face in range(ctx.mesh.num_faces)
        if ctx.mesh.face_neighbours(face)[1] is None
    }
    fastest = max(math.hypot(*velocity.value_at(cell)) for cell in boundary_owners)
    # Without this, "no flux crosses the wall" is also satisfied by a
    # flow that stopped everywhere. Measured ~0.3 on this fixture.
    assert fastest > 0.05, (
        f"the cells against the walls must still be moving for a zero wall flux to mean the wall "
        f"is impermeable rather than the flow dead; fastest was {fastest}"
    )


def _boundary_flux(ctx: _Context) -> float:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    return float(ctx.flux[ctx.target_face])


@then("that boundary's advective flux is the prescribed velocity times the prescribed field value")
def _then_inflow_carries_prescribed_value(ctx: _Context) -> None:
    assert ctx.prescribed_velocity is not None
    assert ctx.prescribed_value is not None
    expected = ctx.prescribed_velocity * ctx.prescribed_value
    assert _boundary_flux(ctx) == expected, (
        f"expected the prescribed inflow to carry the prescribed boundary value in: "
        f"{ctx.prescribed_velocity} * {ctx.prescribed_value} = {expected}, "
        f"got {_boundary_flux(ctx)}"
    )


@then("that boundary's advective flux is exactly zero")
def _then_no_transport(ctx: _Context) -> None:
    assert _boundary_flux(ctx) == 0.0, (
        f"a boundary prescribing no normal velocity must transport nothing through itself; got "
        f"{_boundary_flux(ctx)}"
    )


@then("that boundary's advective flux uses the interior cell's own value, not the boundary's")
def _then_outflow_carries_owner_value(ctx: _Context) -> None:
    assert ctx.prescribed_velocity is not None
    assert ctx.prescribed_value is not None
    assert ctx.scalar is not None
    assert ctx.target_face is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    expected = ctx.prescribed_velocity * ctx.scalar.value_at(owner)
    assert _boundary_flux(ctx) == expected, (
        f"expected outflow to carry the interior cell's own value out: got "
        f"{_boundary_flux(ctx)}, expected {expected}"
    )
    assert _boundary_flux(ctx) != ctx.prescribed_velocity * ctx.prescribed_value


@then("the cell behind that boundary reports the prescribed inflow, not its own interior velocity")
def _then_divergence_sees_inflow(ctx: _Context) -> None:
    assert ctx.divergence is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_velocity is not None
    assert ctx.velocity is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)

    # Hand-derived on this fixture's own mesh (origin (0.5, -1.0),
    # spacing (0.2, 0.3), extent (3, 2), uniform velocity (0.5, 0)).
    # The west owner cell has four faces, and only two contribute:
    #   west boundary, normal (-1, 0), area dy: prescribed * dy
    #   interior east face, normal (+1, 0), area dy: 0.5 * dy
    # Its north and south faces see a normal velocity of exactly zero,
    # because the flow is purely horizontal and both extrapolate.
    # Divergence is that sum over the cell volume.
    area = ctx.mesh.face_area(ctx.target_face)
    volume = ctx.mesh.cell_volume(owner)
    interior_face_velocity = 0.5
    expected = (ctx.prescribed_velocity * area + interior_face_velocity * area) / volume

    # What the same cell would report if the west face used the owner's
    # own velocity instead -- the pre-TASK-052 answer, and exactly zero
    # here, since a uniform flow entering and leaving one cell is
    # divergence-free. The two differ by a factor of infinity, which is
    # the strongest form this comparison can take.
    owner_x, owner_y = ctx.velocity.value_at(owner)
    normal_x, normal_y = ctx.mesh.face_normal(ctx.target_face)
    interior_answer = (
        (owner_x * normal_x + owner_y * normal_y) * area + interior_face_velocity * area
    ) / volume
    assert interior_answer == 0.0, "fixture error: the interior-velocity answer should be zero"

    assert math.isclose(float(ctx.divergence[owner]), expected, rel_tol=1e-12, abs_tol=1e-15), (
        f"expected the cell behind a prescribed inflow to report it: {expected}, got "
        f"{float(ctx.divergence[owner])}"
    )
    assert float(ctx.divergence[owner]) != interior_answer


@then("that boundary's normal velocity is the interior cell's own")
def _then_gradient_extrapolates(ctx: _Context) -> None:
    assert ctx.scalar is not None
    assert ctx.velocity is not None
    assert ctx.target_face is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    owner_x, owner_y = ctx.velocity.value_at(owner)
    normal_x, normal_y = ctx.mesh.face_normal(ctx.target_face)
    expected_normal = owner_x * normal_x + owner_y * normal_y
    # A gradient face extrapolates zero-order for the transported field
    # too, so the face value is the owner's own and the flux is the
    # product of the two.
    expected = expected_normal * ctx.scalar.value_at(owner)
    assert math.isclose(_boundary_flux(ctx), expected, rel_tol=1e-12, abs_tol=1e-15), (
        f"a gradient boundary must extrapolate the interior's own normal velocity "
        f"({expected_normal}); got a flux of {_boundary_flux(ctx)} against {expected}"
    )
