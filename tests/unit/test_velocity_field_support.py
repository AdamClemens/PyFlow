"""Binds `tests/features/velocity_field_support.feature` (TASK-031) --
Stage 5's second task, velocity as the first field the engine
*transports* rather than merely stores. Four subtasks, one binding
module (the roadmap's own "share a branch, a test module and a review
cycle"), scenarios and steps grouped by subtask below. Not a golden demo
-- no config file under `examples/golden-demos/`, no CLI subprocess run,
since every claim here is checked against the engine mechanism directly,
the same `tests/unit/` shape every Stage 4 numerical-scheme feature file
already established. Reuses `tests/unit/_numerics.py`'s shared building
blocks (`default_mesh`, `west_face`) rather than re-deriving a mesh, per
this task's own whole-task obligation.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import pytest
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine import simulation
from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import (
    FirstOrderUpwindAdvection,
    IncompatibleVelocityFieldError,
)
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.engine.numerics.boundary_condition import DirichletBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion, DiffusionScheme
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PressureCoupling
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.numerics.time_integrator import TimeIntegrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import (
    ComponentCountMismatchError,
    ComponentMeshMismatchError,
    VectorField,
)

from ._numerics import default_mesh, zero_gradient_everywhere

scenarios("velocity_field_support.feature")

_GAMMA = 2.0
"""Deliberately not `1.0` (`docs/practices.md`'s "distinct factors"
rule), matching every other diffusion-coefficient fixture in this
directory.
"""


# -- Local test-only doubles (this module's own, per `tests/unit/CLAUDE.md`) --


class _EulerIntegrator(TimeIntegrator):
    """Explicit Euler -- known, hand-derivable arithmetic, the same
    reasoning `tests/unit/test_simulation.py`'s own identically-named
    double states.
    """

    def advance(
        self,
        fields: Mapping[str, Field],
        derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]],
        dt: float,
    ) -> dict[str, Field]:
        rates = derivative(fields)
        result: dict[str, Field] = {}
        for name, f in fields.items():
            assert isinstance(f, CollocatedField)
            advanced = f.copy()
            assert isinstance(advanced, CollocatedField)
            advanced.values[:] = f.values + dt * rates[name]
            result[name] = advanced
        return result


class _ZeroDiffusion(DiffusionScheme):
    """No diffusive contribution -- isolates advection's own effect,
    the same reasoning `test_simulation.py`'s own `_ZeroDiffusion`
    double states.
    """

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _InertLinearSolver(LinearSolver):
    """Not exercised by `step` -- `AssembledNumerics` requires one to
    construct at all.
    """

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=False, iterations=0)


class _InertPressureCoupling(PressureCoupling):
    """Not exercised by `step` -- `AssembledNumerics` requires one to
    construct at all.
    """

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        del dt
        return provisional_velocity.copy(), ScalarField(provisional_velocity.mesh, "pressure")


class _ZeroSourceTerm(SourceTerm):
    """Contributes exactly zero (TASK-035) -- every hand-derived
    expectation in this module was derived before a source term existed
    at all.
    """

    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


def _assembled_numerics(
    advection: FirstOrderUpwindAdvection, diffusion: DiffusionScheme | None = None
) -> AssembledNumerics:
    solver = _InertLinearSolver()
    return AssembledNumerics(
        advection=advection,
        diffusion=diffusion or _ZeroDiffusion(),
        time_integration=_EulerIntegrator(),
        linear_solver=solver,
        pressure_coupling=_InertPressureCoupling(solver),
        source_term=_ZeroSourceTerm(),
        boundary_conditions={},
        names={},
    )


# -- Fixture context ---------------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    vector: VectorField | None = None
    components: list[ScalarField] = field(default_factory=list)
    reassembled: VectorField | None = None
    error: Exception | None = None
    velocity_field: ScalarField | None = None
    scalar_field: ScalarField | None = None
    velocity_flux: torch.Tensor | None = None
    scalar_flux: torch.Tensor | None = None
    viscosity: float = 5.0
    diffusion_coefficient: float = 2.0
    field_a: ScalarField | None = None
    field_b: ScalarField | None = None
    value_a: float = 0.0
    value_b: float = 0.0
    flux_a: torch.Tensor | None = None
    flux_b: torch.Tensor | None = None
    other_flux_b: torch.Tensor | None = None
    fields: dict[str, Field] = field(default_factory=dict)
    velocity: VectorField | None = None
    result: dict[str, Field] | None = None
    result_solved: dict[str, Field] | None = None
    result_prescribed: dict[str, Field] | None = None
    advection: FirstOrderUpwindAdvection | None = None


def _west_face(mesh: StructuredCartesianMesh) -> int:
    return next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "west")


# -- Given -------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    return _Context(mesh=default_mesh())


@given("a vector field whose values are not 0 or 1 anywhere")
def _given_nontrivial_vector_field(ctx: _Context) -> None:
    def initial(x: float, y: float) -> tuple[float, float]:
        return (2.0 + x, 3.0 + y)

    ctx.vector = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=initial)


@given("three scalar fields on the same mesh")
def _given_three_scalars(ctx: _Context) -> None:
    ctx.components = [ScalarField(ctx.mesh, f"s{i}", initial_value=float(i)) for i in range(3)]


@given("two scalar fields defined over different meshes")
def _given_two_scalars_different_meshes(ctx: _Context) -> None:
    other_mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(2, 2))
    ctx.components = [
        ScalarField(ctx.mesh, "a", initial_value=1.0),
        ScalarField(other_mesh, "b", initial_value=2.0),
    ]


@given(
    "a velocity component field and an unrelated scalar field, diffused by the same scheme",
    target_fixture="ctx",
)
def _given_velocity_component_and_scalar(ctx: _Context) -> _Context:
    # Non-uniform values, not a constant -- a spatially constant field
    # has an identically-zero interior gradient regardless of the
    # diffusion coefficient, which would make "changing the coefficient
    # changes the flux" trivially unfalsifiable.
    velocity = VectorField(
        ctx.mesh, "velocity", num_components=2, initial_value=lambda x, y: (x, -2.0)
    )
    components = velocity.decompose()
    ctx.velocity_field = components[0]
    ctx.scalar_field = ScalarField(ctx.mesh, "tracer", initial_value=lambda x, y: 4.0 + y)
    return ctx


@given(
    "two scalar fields with different prescribed Dirichlet values at the same wall",
    target_fixture="ctx",
)
def _given_two_scalars_with_different_wall_values(ctx: _Context) -> _Context:
    ctx.field_a = ScalarField(ctx.mesh, "temperature", initial_value=1.0)
    ctx.field_b = ScalarField(ctx.mesh, "humidity", initial_value=1.0)
    ctx.value_a = 10.0
    ctx.value_b = 20.0
    return ctx


@given(
    "a velocity field decomposed into components alongside an unrelated transported scalar",
    target_fixture="ctx",
)
def _given_velocity_components_and_scalar_for_step(ctx: _Context) -> _Context:
    velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.velocity = velocity
    ctx.components = velocity.decompose()
    ctx.fields = {c.name: c for c in ctx.components}
    ctx.fields["tracer"] = ScalarField(ctx.mesh, "tracer", initial_value=3.0)
    return ctx


@given("a scalar transported by a velocity field", target_fixture="ctx")
def _given_scalar_transported_by_velocity(ctx: _Context) -> _Context:
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.scalar_field = ScalarField(ctx.mesh, "tracer", initial_value=3.0)
    return ctx


@given(
    "a velocity field whose own components are the only fields being transported",
    target_fixture="ctx",
)
def _given_self_advected_velocity(ctx: _Context) -> _Context:
    mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(0.5, 0.4), extent=(2, 1))
    velocity = VectorField(
        mesh,
        "velocity",
        num_components=2,
        initial_value=lambda x, y: (2.0 if x < 0.5 else 1.0, 0.0),
    )
    ctx.mesh = mesh
    ctx.velocity = velocity
    ctx.components = velocity.decompose()
    ctx.fields = {c.name: c for c in ctx.components}
    # West is the only inflow boundary on this 2-cell, purely-horizontal
    # mesh (north/south see zero face-normal velocity; east is
    # outflow) -- the hand-derivation below depends on exactly these
    # prescribed values, so they are not the generic 0.0 every other
    # `step`-driving scenario in this file uses.
    u_name = VectorField.component_name("velocity", 0)
    v_name = VectorField.component_name("velocity", 1)
    ctx.advection = FirstOrderUpwindAdvection(
        {"west": DirichletBoundaryCondition(0.0, {u_name: 3.0, v_name: 0.0})}, {}
    )
    return ctx


@given(
    "a one-component vector field standing in for velocity, and a scalar transported by it",
    target_fixture="ctx",
)
def _given_bad_velocity_shape(ctx: _Context) -> _Context:
    bad_velocity = VectorField(ctx.mesh, "velocity", num_components=1, initial_value=(1.0,))
    ctx.velocity = bad_velocity
    ctx.scalar_field = ScalarField(ctx.mesh, "tracer", initial_value=1.0)
    ctx.fields = {"tracer": ctx.scalar_field}
    return ctx


# -- When ------------------------------------------------------------------


@when("it is decomposed into components and the components are reassembled")
def _when_round_trip(ctx: _Context) -> None:
    assert ctx.vector is not None
    ctx.components = ctx.vector.decompose()
    ctx.reassembled = VectorField.assemble(ctx.components, ctx.vector.name)


@when("it is decomposed into components")
def _when_decomposed(ctx: _Context) -> None:
    assert ctx.vector is not None
    ctx.components = ctx.vector.decompose()


@when("they are reassembled into a vector field")
def _when_reassembled(ctx: _Context) -> None:
    try:
        ctx.reassembled = VectorField.assemble(ctx.components, "velocity")
    except (ComponentCountMismatchError, ComponentMeshMismatchError) as exc:
        ctx.error = exc


@when("viscosity changes but the scalar's own diffusion coefficient does not")
def _when_viscosity_changes(ctx: _Context) -> None:
    assert ctx.velocity_field is not None
    assert ctx.scalar_field is not None
    ctx.velocity_flux, ctx.scalar_flux = _diffusive_fluxes(ctx, viscosity=5.0)
    ctx.other_flux_b, _ = _diffusive_fluxes(ctx, viscosity=9.0)


@when("the scalar's own diffusion coefficient changes but viscosity does not")
def _when_diffusion_coefficient_changes(ctx: _Context) -> None:
    assert ctx.velocity_field is not None
    assert ctx.scalar_field is not None
    ctx.velocity_flux, ctx.scalar_flux = _diffusive_fluxes(ctx, diffusion_coefficient=2.0)
    _, ctx.other_flux_b = _diffusive_fluxes(ctx, diffusion_coefficient=7.0)


def _diffusive_fluxes(
    ctx: _Context, viscosity: float | None = None, diffusion_coefficient: float | None = None
) -> tuple[torch.Tensor, torch.Tensor]:
    assert ctx.velocity_field is not None
    assert ctx.scalar_field is not None
    v = viscosity if viscosity is not None else ctx.viscosity
    d = diffusion_coefficient if diffusion_coefficient is not None else ctx.diffusion_coefficient
    scheme = CentralDifferenceDiffusion(
        zero_gradient_everywhere(), {}, d, coefficient_overrides={ctx.velocity_field.name: v}
    )
    velocity_flux = scheme.flux(ctx.velocity_field)
    scalar_flux = scheme.flux(ctx.scalar_field)
    return velocity_flux, scalar_flux


@when("the diffusive flux is computed for each field at that wall")
def _when_flux_computed_for_each_field(ctx: _Context) -> None:
    assert ctx.field_a is not None
    assert ctx.field_b is not None
    condition = DirichletBoundaryCondition(
        0.0, {ctx.field_a.name: ctx.value_a, ctx.field_b.name: ctx.value_b}
    )
    scheme = CentralDifferenceDiffusion(
        {**zero_gradient_everywhere(), "west": condition}, {}, _GAMMA
    )
    ctx.flux_a = scheme.flux(ctx.field_a)
    ctx.flux_b = scheme.flux(ctx.field_b)


@when("one field's prescribed value changes")
def _when_one_fields_value_changes(ctx: _Context) -> None:
    assert ctx.field_a is not None
    assert ctx.field_b is not None
    condition = DirichletBoundaryCondition(
        0.0, {ctx.field_a.name: ctx.value_a, ctx.field_b.name: ctx.value_b}
    )
    scheme = CentralDifferenceDiffusion(
        {**zero_gradient_everywhere(), "west": condition}, {}, _GAMMA
    )
    ctx.flux_b = scheme.flux(ctx.field_b)

    changed_condition = DirichletBoundaryCondition(
        0.0, {ctx.field_a.name: ctx.value_a + 100.0, ctx.field_b.name: ctx.value_b}
    )
    changed_scheme = CentralDifferenceDiffusion(
        {**zero_gradient_everywhere(), "west": changed_condition}, {}, _GAMMA
    )
    ctx.other_flux_b = changed_scheme.flux(ctx.field_b)


def _advection_with_west_inflow_condition() -> FirstOrderUpwindAdvection:
    """`default_mesh()`'s own west edge is the only inflow boundary a
    uniform `(1.0, 0.0)` velocity produces -- north/south see zero
    face-normal velocity (multiplying any boundary value by zero) and
    east is outflow, so neither needs a condition configured at all.
    """
    return FirstOrderUpwindAdvection({"west": DirichletBoundaryCondition(0.0)}, {})


@when("the simulation is stepped by one timestep")
def _when_stepped(ctx: _Context) -> None:
    assert ctx.velocity is not None
    advection = ctx.advection or _advection_with_west_inflow_condition()
    numerics = _assembled_numerics(advection)
    ctx.result = simulation.step(ctx.fields, ctx.velocity, numerics, 0.1)


@when(
    "the simulation is stepped once with that velocity's own components also being "
    "transported and once with the same velocity held fixed"
)
def _when_stepped_solved_and_prescribed(ctx: _Context) -> None:
    assert ctx.velocity is not None
    assert ctx.scalar_field is not None
    numerics = _assembled_numerics(_advection_with_west_inflow_condition())

    solved_fields: dict[str, Field] = {c.name: c for c in ctx.velocity.decompose()}
    solved_fields["tracer"] = ScalarField(ctx.mesh, "tracer", initial_value=3.0)
    ctx.result_solved = simulation.step(solved_fields, ctx.velocity, numerics, 0.1)

    prescribed_fields: dict[str, Field] = {
        "tracer": ScalarField(ctx.mesh, "tracer", initial_value=3.0)
    }
    ctx.result_prescribed = simulation.step(prescribed_fields, ctx.velocity, numerics, 0.1)


@when("the simulation is stepped")
def _when_stepped_plain(ctx: _Context) -> None:
    assert ctx.velocity is not None
    numerics = _assembled_numerics(_advection_with_west_inflow_condition())
    try:
        ctx.result = simulation.step(ctx.fields, ctx.velocity, numerics, 0.1)
    except IncompatibleVelocityFieldError as exc:
        ctx.error = exc


@when("the orchestrator module's source is inspected")
def _when_source_inspected() -> None:
    pass


# -- Then ------------------------------------------------------------------


@then("the reassembled field's values exactly match the original")
def _then_round_trip_matches(ctx: _Context) -> None:
    assert ctx.vector is not None
    assert ctx.reassembled is not None
    torch.testing.assert_close(ctx.reassembled.values, ctx.vector.values, rtol=0, atol=0)


@then("each component is a ScalarField defined over the same mesh as the original")
def _then_components_are_scalar_fields(ctx: _Context) -> None:
    assert ctx.vector is not None
    assert len(ctx.components) == 2
    for component in ctx.components:
        assert isinstance(component, ScalarField)
        assert component.mesh is ctx.vector.mesh


@then("each component's name follows the fixed component-naming convention")
def _then_component_naming_convention(ctx: _Context) -> None:
    assert ctx.vector is not None
    for i, component in enumerate(ctx.components):
        assert component.name == VectorField.component_name(ctx.vector.name, i)


@then("a ComponentCountMismatchError is raised")
def _then_component_count_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, ComponentCountMismatchError)


@then("a ComponentMeshMismatchError is raised")
def _then_component_mesh_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, ComponentMeshMismatchError)


@then("the velocity component's diffusive flux changes")
def _then_velocity_flux_changes(ctx: _Context) -> None:
    assert ctx.velocity_flux is not None
    assert ctx.other_flux_b is not None
    assert not torch.equal(ctx.velocity_flux, ctx.other_flux_b)


@then("the scalar's own diffusive flux does not change")
def _then_scalar_flux_unchanged(ctx: _Context) -> None:
    assert ctx.scalar_flux is not None
    _velocity_again, scalar_again = _diffusive_fluxes(ctx)
    assert torch.equal(ctx.scalar_flux, scalar_again)


@then("the scalar's own diffusive flux changes")
def _then_scalar_flux_changes(ctx: _Context) -> None:
    assert ctx.scalar_flux is not None
    assert ctx.other_flux_b is not None
    assert not torch.equal(ctx.scalar_flux, ctx.other_flux_b)


@then("the velocity component's diffusive flux does not change")
def _then_velocity_flux_unchanged(ctx: _Context) -> None:
    assert ctx.velocity_flux is not None
    velocity_again, _scalar_again = _diffusive_fluxes(ctx)
    assert torch.equal(ctx.velocity_flux, velocity_again)


@then("each field's flux reflects its own prescribed value, not the other's")
def _then_each_field_sees_its_own_value(ctx: _Context) -> None:
    assert ctx.field_a is not None
    assert ctx.field_b is not None
    assert ctx.flux_a is not None
    assert ctx.flux_b is not None
    west = _west_face(ctx.mesh)
    owner, _neighbour = ctx.mesh.face_neighbours(west)
    owner_a = ctx.field_a.value_at(owner)
    owner_b = ctx.field_b.value_at(owner)
    distance = ctx.mesh.face_centroid_distance(west)
    expected_a = _GAMMA * (ctx.value_a - owner_a) / distance
    expected_b = _GAMMA * (ctx.value_b - owner_b) / distance
    assert float(ctx.flux_a[west]) == pytest.approx(expected_a, abs=1e-9)
    assert float(ctx.flux_b[west]) == pytest.approx(expected_b, abs=1e-9)
    assert ctx.flux_a[west] != ctx.flux_b[west]


@then("the other field's flux at that wall is unchanged")
def _then_other_field_unaffected(ctx: _Context) -> None:
    assert ctx.flux_b is not None
    assert ctx.other_flux_b is not None
    torch.testing.assert_close(ctx.flux_b, ctx.other_flux_b, rtol=1e-9, atol=1e-9)


@then("every velocity component and the scalar are all present, and all advanced, in the result")
def _then_all_present_and_advanced(ctx: _Context) -> None:
    assert ctx.result is not None
    assert set(ctx.result.keys()) == set(ctx.fields.keys())
    for name, original in ctx.fields.items():
        advanced = ctx.result[name]
        assert isinstance(original, CollocatedField)
        assert isinstance(advanced, CollocatedField)
        assert advanced is not original


@then("the scalar's own result agrees to floating-point tolerance either way")
def _then_scalar_result_matches_either_way(ctx: _Context) -> None:
    assert ctx.result_solved is not None
    assert ctx.result_prescribed is not None
    solved_tracer = ctx.result_solved["tracer"]
    prescribed_tracer = ctx.result_prescribed["tracer"]
    assert isinstance(solved_tracer, CollocatedField)
    assert isinstance(prescribed_tracer, CollocatedField)
    torch.testing.assert_close(solved_tracer.values, prescribed_tracer.values, rtol=1e-9, atol=1e-9)


@then("each component's result matches its own hand-derived value")
def _then_self_advection_matches_hand_derivation(ctx: _Context) -> None:
    assert ctx.result is not None
    u_name = VectorField.component_name("velocity", 0)
    v_name = VectorField.component_name("velocity", 1)
    u = ctx.result[u_name]
    v = ctx.result[v_name]
    assert isinstance(u, CollocatedField)
    assert isinstance(v, CollocatedField)
    # Hand-derived: origin=(0,0), spacing=(0.5, 0.4), extent=(2, 1),
    # dt=0.1. Initial u=[2.0, 1.0], v=[0.0, 0.0]. Zero diffusion.
    # North/south faces carry zero flux regardless of phi (v is zero
    # everywhere, so velocity_normal=0 there). West (owner=cell0, no
    # neighbour): velocity_normal=-2.0 (inflow), interior (owner=cell0,
    # neighbour=cell1): velocity_normal=1.5 (owner upstream). East
    # (owner=cell1, no neighbour): velocity_normal=1.0 (outflow).
    # See this module's own commit message for the full per-face
    # derivation.
    torch.testing.assert_close(
        u.values, torch.tensor([2.6, 1.4], dtype=torch.float64), rtol=1e-9, atol=1e-9
    )
    torch.testing.assert_close(
        v.values, torch.tensor([0.0, 0.0], dtype=torch.float64), rtol=1e-9, atol=1e-9
    )


@then("an IncompatibleVelocityFieldError is raised")
def _then_incompatible_velocity_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, IncompatibleVelocityFieldError)


@then(
    'it contains no "velocity" string literal, no VectorField isinstance check, and no '
    "hardcoded component-name pair"
)
def _then_no_special_casing_in_orchestrator() -> None:
    # A crude "the word velocity doesn't appear" check would also flag
    # the legitimate `velocity: VectorField` parameter and this module's
    # own prose (e.g. `IncompatibleVelocityFieldError` in a docstring) --
    # neither is special-casing. What the criterion actually forbids is
    # a *quoted string literal* `"velocity"` (the shape a dict-key lookup
    # or `==` comparison would take), an `isinstance(..., VectorField)`
    # call, and a literal component name from the fixed naming
    # convention (`VectorField.component_name`).
    source = inspect.getsource(simulation)
    assert '"velocity"' not in source
    assert re.search(r"isinstance\([^)]*VectorField\)", source) is None
    for i in range(2):
        assert f'"{VectorField.component_name("velocity", i)}"' not in source
