"""Binds `tests/features/simulation_orchestrator.feature` (TASK-040) --
the Simulation Orchestrator, Stage 4 Completion Criterion 1's own
mechanism: a mesh-sharing set of fields, a velocity field, and an
`AssembledNumerics` advanced by one timestep.

Not a golden demo -- there is no config file under
`examples/golden-demos/` and no CLI subprocess run, since this is the
mechanism a future demo (TASK-030) is built on top of, not a demo
itself. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).

Every test-only scheme below is boundary-aware by holding its own
`BoundaryCondition` at construction (TASK-040's own Design decision,
`docs/planning/roadmap.md`) -- applied uniformly to every boundary face,
since mapping a face to *which* named boundary (north/south/east/west)
it belongs to is TASK-023's own concern (a real scheme's problem), not
this orchestrator's.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine import simulation
from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.advection import AdvectionScheme
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import DiffusionScheme
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PressureCoupling
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.numerics.time_integrator import TimeIntegrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import accumulate_flux_to_cells
from pyflow.engine.vector_field import VectorField

from ._numerics import (
    FixedValueCondition,
    default_mesh,
)

scenarios("simulation_orchestrator.feature")


# -- Test-only implementations -----------------------------------------


class _EchoAdvection(AdvectionScheme):
    """Boundary-aware, hand-checkable: at an interior face, the flux is
    the owner cell's own value; at a boundary face, it is this scheme's
    own boundary condition, evaluated -- genuinely varies with both the
    field and the boundary condition, without being a real numerical
    scheme.
    """

    def __init__(self, boundary_condition: BoundaryCondition) -> None:
        self._boundary_condition = boundary_condition

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        assert isinstance(field, CollocatedField)
        mesh = field.mesh
        result = torch.zeros(mesh.num_faces, dtype=torch.float64)
        for face in range(mesh.num_faces):
            if mesh.is_boundary_face(face):
                result[face] = self._boundary_condition.evaluate(field, face)
            else:
                owner, _neighbour = mesh.face_neighbours(face)
                result[face] = field.value_at(owner)
        return result


class _ZeroDiffusion(DiffusionScheme):
    """Trivial: no diffusive contribution, so the tests below isolate
    advection's own effect on the accumulated derivative.
    """

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _EulerIntegrator(TimeIntegrator):
    """Explicit Euler: `new = old + dt * derivative` -- known arithmetic,
    the same rule `test_time_integrator_contract.py`'s own test double
    uses.
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
    at all, so `derivative` must add nothing for any of them to still
    hold.
    """

    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


# -- Fixture context -----------------------------------------------------


@dataclass
class _Context:
    """One scenario's accumulated state -- steps mutate this rather than
    module globals, the same pattern `tests/golden/_demo.py`'s `DemoRun`
    establishes, so two scenarios cannot leak into each other.
    """

    mesh: Mesh
    fields: dict[str, Field]
    velocity: VectorField
    assembled: AssembledNumerics
    dt: float = 0.1
    result: dict[str, Field] | None = None
    other_assembled: AssembledNumerics | None = None
    other_result: dict[str, Field] | None = None
    error: Exception | None = None
    original_values: dict[str, torch.Tensor] | None = None
    face_values: torch.Tensor | None = None
    accumulated: torch.Tensor | None = None


def _assembled(boundary_value: float) -> AssembledNumerics:
    solver = _InertLinearSolver()
    return AssembledNumerics(
        advection=_EchoAdvection(FixedValueCondition(boundary_value)),
        diffusion=_ZeroDiffusion(),
        time_integration=_EulerIntegrator(),
        linear_solver=solver,
        pressure_coupling=_InertPressureCoupling(solver),
        source_term=_ZeroSourceTerm(),
        boundary_conditions={},
        names={},
    )


# -- Given -----------------------------------------------------------------


@given("a mesh-sharing set of fields and an AssembledNumerics", target_fixture="ctx")
def _given_default_context() -> _Context:
    mesh = default_mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    field = ScalarField(mesh, "temperature", initial_value=2.0)
    return _Context(
        mesh=mesh,
        fields={"temperature": field},
        velocity=velocity,
        assembled=_assembled(3.0),
    )


@given("every field and boundary condition is zero everywhere")
def _given_zero_everywhere(ctx: _Context) -> None:
    ctx.fields = {"temperature": ScalarField(ctx.mesh, "temperature", initial_value=0.0)}
    ctx.assembled = _assembled(0.0)


@given("a scheme whose flux depends on its own boundary conditions")
def _given_boundary_dependent_scheme(ctx: _Context) -> None:
    # `ctx.assembled` (from the Background) already uses boundary value
    # 3.0; this is the same setup with a different boundary value, so
    # the two can be compared.
    ctx.other_assembled = _assembled(5.0)


@given("a small, non-square, non-trivially-origined mesh")
def _given_small_mesh(ctx: _Context) -> None:
    assert ctx.mesh.num_cells == 6, "the Background fixture is already 3x2"


@given("a hand-chosen face-value array")
def _given_hand_chosen_face_values(ctx: _Context) -> None:
    ctx.face_values = torch.arange(1, ctx.mesh.num_faces + 1, dtype=torch.float64)


@given("a velocity field defined on a different mesh")
def _given_velocity_on_different_mesh(ctx: _Context) -> None:
    other_mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(2, 2))
    ctx.velocity = VectorField(other_mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))


# -- When ------------------------------------------------------------------


@when("the simulation is stepped by one timestep")
def _when_stepped(ctx: _Context) -> None:
    ctx.original_values = {
        name: f.values.clone() for name, f in ctx.fields.items() if isinstance(f, CollocatedField)
    }
    try:
        ctx.result = simulation.step(ctx.fields, ctx.velocity, ctx.assembled, ctx.dt)
    except simulation.MismatchedMeshError as exc:
        ctx.error = exc


@when("the simulation is stepped once with one boundary value and once with a different one")
def _when_stepped_twice(ctx: _Context) -> None:
    assert ctx.other_assembled is not None
    ctx.result = simulation.step(ctx.fields, ctx.velocity, ctx.assembled, ctx.dt)
    ctx.other_result = simulation.step(ctx.fields, ctx.velocity, ctx.other_assembled, ctx.dt)


@when("the face values are accumulated to cells")
def _when_accumulated(ctx: _Context) -> None:
    assert ctx.face_values is not None
    ctx.accumulated = accumulate_flux_to_cells(ctx.mesh, ctx.face_values)


# -- Then ------------------------------------------------------------------


@then("a new field is returned for every key in the input")
def _then_new_field_per_key(ctx: _Context) -> None:
    assert ctx.result is not None
    assert set(ctx.result.keys()) == set(ctx.fields.keys())
    for name, f in ctx.fields.items():
        assert ctx.result[name] is not f


@then("no input field's own values changed")
def _then_input_unchanged(ctx: _Context) -> None:
    assert ctx.original_values is not None
    for name, f in ctx.fields.items():
        assert isinstance(f, CollocatedField)
        assert torch.equal(f.values, ctx.original_values[name])


@then("every returned field is zero everywhere")
def _then_all_zero(ctx: _Context) -> None:
    assert ctx.result is not None
    for f in ctx.result.values():
        assert isinstance(f, CollocatedField)
        assert torch.all(f.values == 0.0)


@then("the two runs disagree at the cell adjacent to that boundary")
def _then_runs_disagree(ctx: _Context) -> None:
    assert ctx.result is not None
    assert ctx.other_result is not None
    field_a = ctx.result["temperature"]
    field_b = ctx.other_result["temperature"]
    assert isinstance(field_a, CollocatedField)
    assert isinstance(field_b, CollocatedField)
    boundary_face = next(f for f in range(ctx.mesh.num_faces) if ctx.mesh.is_boundary_face(f))
    owner, _neighbour = ctx.mesh.face_neighbours(boundary_face)
    assert field_a.value_at(owner) != field_b.value_at(owner)


@then("the accumulation code never asked whether any face was a boundary face")
def _then_no_boundary_branching() -> None:
    source = inspect.getsource(simulation)
    assert "is_boundary_face" not in source


@then("the result matches the hand-derived cell array exactly, for every cell")
def _then_matches_hand_derived(ctx: _Context) -> None:
    assert ctx.accumulated is not None
    # Hand-derived from the mesh's own geometry (StructuredCartesianMesh,
    # origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(3, 2)) and
    # face_values = 1..17 -- see this module's own history/commit message
    # for the full per-face derivation. Every cell's volume is
    # dx * dy = 0.06.
    expected = torch.tensor(
        [4.7 / 0.06, 5.3 / 0.06, 6.5 / 0.06, 3.5 / 0.06, 0.5 / 0.06, 0.5 / 0.06],
        dtype=torch.float64,
    )
    torch.testing.assert_close(ctx.accumulated, expected, rtol=1e-9, atol=1e-9)


@then("a MismatchedMeshError is raised")
def _then_mismatched_mesh_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, simulation.MismatchedMeshError)


# -- Plain (non-BDD) unit tests, not acceptance criteria of their own --
#
# `accumulate_flux_to_cells` vectorised its per-face Python loop (found
# while investigating a narrower Rhie-Chow fix, `adr/ADR-011`'s own
# sparse-solver work having already fixed the Poisson matrix's equivalent
# cost) -- an implementation-detail performance fix, same treatment
# `PISO._poisson_matrix`'s own caching fix got: plain pytest, not a new
# Gherkin scenario, since the function's public behaviour is unchanged
# and the existing hand-derived scenario above already proves it.


def test_flux_geometry_is_cached_across_repeated_calls_on_the_same_mesh() -> None:
    mesh = default_mesh()

    first = simulation._flux_geometry(mesh)
    second = simulation._flux_geometry(mesh)

    assert second is first, "geometry was rebuilt on a second call, not reused"


def test_flux_geometry_recomputes_for_a_genuinely_different_mesh() -> None:
    mesh_a = default_mesh()
    mesh_b = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(4, 3))

    geometry_a = simulation._flux_geometry(mesh_a)
    geometry_b = simulation._flux_geometry(mesh_b)

    assert geometry_a is not geometry_b
    assert geometry_a.owner_ids.shape != geometry_b.owner_ids.shape
