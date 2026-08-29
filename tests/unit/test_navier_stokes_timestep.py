"""Binds `tests/features/navier_stokes_timestep.feature` (TASK-034,
Stage 5's fifth and last task in build order) -- assembles TASK-031/032/
033 into one incompressible Navier-Stokes timestep
(`pyflow.engine.simulation.navier_stokes_step`), then validates it. Not
a golden demo -- no config file under `examples/golden-demos/`, no CLI
subprocess run, the same `tests/unit/` shape every prior Stage 4/5
numerical-scheme feature file already established. Reuses
`tests/unit/_numerics.py`'s shared building blocks where they fit;
supplies its own local doubles and `_Context` otherwise, per this
directory's own "local by default, shared where genuinely identical"
convention.

**Per-component wall velocities use `BoundaryFaceConfig.field_values`
directly (`velocity.0`/`velocity.1`, `VectorField.component_name`), not
a dedicated `velocity_tangential` field -- a design finding, not an
oversight.** Stage 5's own design question two (resolved 2026-08-28,
`docs/planning/roadmap.md`) named `velocity_tangential` as its answer,
but `field_values`/`field_gradients` (TASK-031c) landed the very next
day and already supply the exact general mechanism that question needed
-- a per-field-name override at one wall -- with no new config field, no
new per-wall tangential-axis wiring inside `assembly.py` (which stays
field-name-agnostic, per its own established discipline), and no new
concept to document. A no-slip *stationary* wall needs no override at
all (`scalar_value=0.0` already zeroes both components identically,
since normal and tangential are both zero); a *moving* wall (Couette's
plate, the cavity's lid) sets `field_values` for both component names
directly. See this module's own commit message and
`docs/planning/roadmap.md` TASK-034's own Design decision for the full
reasoning -- recorded explicitly, per root `CLAUDE.md`'s Validation
section, rather than silently building something different from what
was decided without saying so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pytest
import torch
from fixtures.ghia_1982_re100 import (
    PRIMARY_VORTEX_CENTER,
    U_VELOCITY_ALONG_VERTICAL_CENTERLINE,
    V_VELOCITY_ALONG_HORIZONTAL_CENTERLINE,
)
from pytest_bdd import given, scenarios, then, when

from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    NumericsConfig,
)
from pyflow.engine import simulation
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import (
    AssembledNumerics,
    assemble_numerics,
    register_linear_solver,
    register_pressure_coupling,
)
from pyflow.engine.numerics.boundary_condition import BoundaryCondition, DirichletBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.divergence import GreenGaussDivergence
from pyflow.engine.numerics.linear_solver import (
    ConjugateGradientSolver,
    LinearSolver,
    LinearSolverResult,
)
from pyflow.engine.numerics.pressure_coupling import PISO, PressureCoupling
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import PressureField, ScalarField
from pyflow.engine.simulation import NavierStokesStepResult
from pyflow.engine.vector_field import VectorField

scenarios("navier_stokes_timestep.feature")

_VELOCITY_NAME = "velocity"
_U_NAME = VectorField.component_name(_VELOCITY_NAME, 0)
_V_NAME = VectorField.component_name(_VELOCITY_NAME, 1)
_DT = 0.02
_TOLERANCE = 1e-6


def _no_slip_mesh(extent: tuple[int, int] = (4, 3)) -> StructuredCartesianMesh:
    # Non-square, non-trivially-origined, non-unit spacing -- the same
    # "distinct factors" discipline every other Stage 4/5 fixture in
    # this repository follows.
    return StructuredCartesianMesh(origin=(0.4, -0.3), spacing=(0.25, 0.2), extent=extent)


def _no_slip_boundary_conditions() -> dict[str, BoundaryCondition]:
    condition = DirichletBoundaryCondition(0.0)
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def _divergent_velocity(mesh: StructuredCartesianMesh) -> VectorField:
    # Non-axis-aligned, non-uniform -- the same fixture shape
    # `test_piso_pressure_coupling.py`/`test_pressure_correction_loop.py`
    # already use, so a real divergent flow needs genuine correction.
    cx, cy = 1.5, -0.9

    def value(x: float, y: float) -> tuple[float, float]:
        return (0.6 * (x - cx) - 0.2 * (y - cy), 0.3 * (x - cx) + 0.9 * (y - cy))

    return VectorField(mesh, _VELOCITY_NAME, num_components=2, initial_value=value)


def _real_numerics(
    boundary_conditions: dict[str, BoundaryCondition],
    periodic_pairs: dict[str, str] | None = None,
    viscosity: float = 1.0,
    pressure_coupling: PressureCoupling | None = None,
) -> AssembledNumerics:
    pairs = periodic_pairs or {}
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=1000)
    return AssembledNumerics(
        advection=FirstOrderUpwindAdvection(boundary_conditions, pairs),
        diffusion=CentralDifferenceDiffusion(boundary_conditions, pairs, viscosity),
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=pressure_coupling
        or PISO(solver, boundary_conditions, tolerance=_TOLERANCE, periodic_pairs=pairs),
        boundary_conditions=boundary_conditions,
        names={},
    )


class _RecordingLinearSolver(LinearSolver):
    """A real Conjugate Gradient solve that records having been asked --
    exists only to prove the timestep's own pressure solve runs through
    whichever `LinearSolver` `assemble_numerics` resolved, not one the
    `PressureCoupling` constructed for itself (Stage 5 Completion
    Criterion 13's *second* substitution check, added by that stage's
    exit audit on 2026-08-29).

    Delegates rather than returning a marker value, deliberately: the
    claim under test is "the configured object is the one that runs", not
    "a wrong answer propagates", so the physics stays real and the
    scenario cannot pass or fail for any reason other than the call
    itself. `_MarkerPressureCoupling` above takes the opposite approach
    for the opposite reason -- a `PressureCoupling`'s own return value
    *is* observable in `NavierStokesStepResult`, so a marker is the
    directer evidence there; a `LinearSolver`'s is not, since it reaches
    the result only through a pressure field a real solve would produce
    too.
    """

    def __init__(self, tolerance: float, max_iterations: int) -> None:
        self._inner = ConjugateGradientSolver(tolerance, max_iterations)
        self.solve_calls = 0

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        self.solve_calls += 1
        return self._inner.solve(matrix, rhs)


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    numerics: AssembledNumerics | None = None
    fields: dict[str, Field] = field(default_factory=dict)
    result: NavierStokesStepResult | None = None
    other_result: NavierStokesStepResult | None = None
    history: list[torch.Tensor] = field(default_factory=list)
    divergence_history: list[float] = field(default_factory=list)
    lid_speed: float = 0.0
    viscosity: float = 0.0
    channel_height: float = 0.0
    channel_bottom: float = 0.0
    steady: bool = False
    ke_history: list[float] = field(default_factory=list)
    cavity_errors: list[float] = field(default_factory=list)
    cavity_finest_fields: dict[str, Field] = field(default_factory=dict)
    cavity_finest_mesh: StructuredCartesianMesh | None = None
    cavity_finest_extent: tuple[int, int] = (0, 0)
    recording_solver: _RecordingLinearSolver | None = None


# -- Given -------------------------------------------------------------


@given("a closed, no-slip domain with a divergent initial velocity field", target_fixture="ctx")
def _given_closed_divergent() -> _Context:
    mesh = _no_slip_mesh()
    bcs = _no_slip_boundary_conditions()
    ctx = _Context(mesh=mesh, numerics=_real_numerics(bcs))
    velocity = _divergent_velocity(mesh)
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


@given(
    "a fully periodic domain with a uniform, non-axis-aligned velocity field and zero viscosity",
    target_fixture="ctx",
)
def _given_periodic_uniform() -> _Context:
    mesh = _no_slip_mesh()
    pairs = {"north": "south", "south": "north", "east": "west", "west": "east"}
    ctx = _Context(mesh=mesh, numerics=_real_numerics({}, pairs, viscosity=0.0))
    # `CentralDifferenceDiffusion` still needs a positive coefficient to
    # be constructed meaningfully; zero viscosity is expressed by scaling
    # the coefficient itself to exactly 0.0, so the diffusive flux is
    # identically zero at every face regardless of the field.
    velocity = VectorField(mesh, _VELOCITY_NAME, num_components=2, initial_value=(1.3, -0.7))
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


@given("a closed, no-slip domain with the fluid initially at rest", target_fixture="ctx")
def _given_closed_at_rest() -> _Context:
    mesh = _no_slip_mesh()
    bcs = _no_slip_boundary_conditions()
    ctx = _Context(mesh=mesh, numerics=_real_numerics(bcs))
    velocity = VectorField(mesh, _VELOCITY_NAME, num_components=2, initial_value=(0.0, 0.0))
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


class _MarkerPressureCoupling(PressureCoupling):
    """Returns a distinctive, obviously-not-real-physics pressure field
    (a large constant no real solve would produce for this fixture) --
    exists only to prove `navier_stokes_step` calls whichever
    `PressureCoupling` `assemble_numerics` resolved, not a hardcoded
    `PISO` (Stage 5 Completion Criterion 13's own substitution check).
    """

    _MARKER = 12345.0

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        del dt
        pressure = PressureField(provisional_velocity.mesh, "pressure")
        pressure.values[:] = self._MARKER
        return provisional_velocity.copy(), pressure


@given(
    "a PressureCoupling test double registered under its own name and selected by configuration",
    target_fixture="ctx",
)
def _given_marker_pressure_coupling() -> _Context:
    mesh = _no_slip_mesh()
    name = "test_only_marker_pressure_coupling"
    register_pressure_coupling(
        name,
        lambda linear_solver, boundary_conditions, tolerance, max_iterations, periodic_pairs: (
            _MarkerPressureCoupling(linear_solver)
        ),
    )
    config = NumericsConfig(
        pressure_coupling=name,  # type: ignore[arg-type]
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
            south=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
            east=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
            west=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
        ),
    )
    numerics = assemble_numerics(config)
    ctx = _Context(mesh=mesh, numerics=numerics)
    velocity = _divergent_velocity(mesh)
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


@given(
    "a LinearSolver test double registered under its own name and selected by configuration",
    target_fixture="ctx",
)
def _given_recording_linear_solver() -> _Context:
    mesh = _no_slip_mesh()
    name = "test_only_recording_linear_solver"
    recorded: list[_RecordingLinearSolver] = []

    def factory(tolerance: float, max_iterations: int) -> LinearSolver:
        solver = _RecordingLinearSolver(tolerance, max_iterations)
        recorded.append(solver)
        return solver

    register_linear_solver(name, factory)
    config = NumericsConfig(
        linear_solver=name,  # type: ignore[arg-type]
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
            south=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
            east=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
            west=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=0.0),
        ),
    )
    numerics = assemble_numerics(config)
    assert len(recorded) == 1, "assemble_numerics did not construct the registered solver"
    ctx = _Context(mesh=mesh, numerics=numerics, recording_solver=recorded[0])
    velocity = _divergent_velocity(mesh)
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


_COUETTE_LID_SPEED = 1.7
_COUETTE_VISCOSITY = 0.8
_COUETTE_EXTENT = (3, 8)
_COUETTE_SPACING = (0.2, 0.2)
_COUETTE_ORIGIN = (0.4, -0.3)


@given(
    "a channel periodic in the flow direction, no-slip walls, one stationary and one moving "
    "tangentially",
    target_fixture="ctx",
)
def _given_couette_channel() -> _Context:
    mesh = StructuredCartesianMesh(
        origin=_COUETTE_ORIGIN, spacing=_COUETTE_SPACING, extent=_COUETTE_EXTENT
    )
    south = DirichletBoundaryCondition(0.0)
    north = DirichletBoundaryCondition(0.0, {_U_NAME: _COUETTE_LID_SPEED, _V_NAME: 0.0})
    bcs: dict[str, BoundaryCondition] = {"south": south, "north": north}
    periodic = {"east": "west", "west": "east"}
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=1000)
    numerics = AssembledNumerics(
        advection=FirstOrderUpwindAdvection(bcs, periodic),
        diffusion=CentralDifferenceDiffusion(bcs, periodic, _COUETTE_VISCOSITY),
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=PISO(solver, bcs, tolerance=1e-8, periodic_pairs=periodic),
        boundary_conditions=bcs,
        names={},
    )
    ctx = _Context(
        mesh=mesh,
        numerics=numerics,
        lid_speed=_COUETTE_LID_SPEED,
        viscosity=_COUETTE_VISCOSITY,
        channel_height=_COUETTE_EXTENT[1] * _COUETTE_SPACING[1],
        channel_bottom=_COUETTE_ORIGIN[1],
    )
    velocity = VectorField(mesh, _VELOCITY_NAME, num_components=2, initial_value=(0.0, 0.0))
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


_NEGLIGIBLE_VISCOSITY = 1e-6


@given(
    "a closed, no-slip domain with a divergent initial velocity field and negligible viscosity",
    target_fixture="ctx",
)
def _given_closed_divergent_inviscid() -> _Context:
    mesh = _no_slip_mesh()
    bcs = _no_slip_boundary_conditions()
    ctx = _Context(mesh=mesh, numerics=_real_numerics(bcs, viscosity=_NEGLIGIBLE_VISCOSITY))
    velocity = _divergent_velocity(mesh)
    ctx.fields = {c.name: c for c in velocity.decompose()}
    return ctx


# -- When ----------------------------------------------------------------


@when("one Navier-Stokes timestep is taken")
def _when_one_step(ctx: _Context) -> None:
    assert ctx.numerics is not None
    ctx.result = simulation.navier_stokes_step(ctx.fields, _VELOCITY_NAME, ctx.numerics, _DT)


@when("one Navier-Stokes timestep is taken twice from the same initial state")
def _when_stepped_twice(ctx: _Context) -> None:
    bcs = _no_slip_boundary_conditions()
    numerics_a = _real_numerics(bcs)
    numerics_b = _real_numerics(bcs)
    velocity_a = _divergent_velocity(ctx.mesh)
    velocity_b = _divergent_velocity(ctx.mesh)
    fields_a = {c.name: c for c in velocity_a.decompose()}
    fields_b = {c.name: c for c in velocity_b.decompose()}
    ctx.result = simulation.navier_stokes_step(fields_a, _VELOCITY_NAME, numerics_a, _DT)
    ctx.other_result = simulation.navier_stokes_step(fields_b, _VELOCITY_NAME, numerics_b, _DT)


def _velocity_divergence(mesh: StructuredCartesianMesh, velocity: VectorField) -> torch.Tensor:
    pairs = {"north": "south", "south": "north", "east": "west", "west": "east"}
    return GreenGaussDivergence({}, pairs).divergence(velocity)


def _kinetic_energy(mesh: StructuredCartesianMesh, velocity: VectorField) -> float:
    total = 0.0
    for cell in range(mesh.num_cells):
        vx, vy = velocity.value_at(cell)
        total += 0.5 * (vx * vx + vy * vy) * mesh.cell_volume(cell)
    return total


@when("many Navier-Stokes timesteps are taken")
def _when_many_steps(ctx: _Context) -> None:
    assert ctx.numerics is not None
    fields = ctx.fields
    for _ in range(20):
        result = simulation.navier_stokes_step(fields, _VELOCITY_NAME, ctx.numerics, _DT)
        fields = result.fields
        ctx.history.append(result.corrected_velocity.values.clone())
        max_divergence = float(
            _velocity_divergence(ctx.mesh, result.corrected_velocity).abs().max()
        )
        ctx.divergence_history.append(max_divergence)
        ctx.ke_history.append(_kinetic_energy(ctx.mesh, result.corrected_velocity))
    ctx.result = result


_STEADY_RESIDUAL_TOLERANCE = 1e-9
_STEADY_MAX_STEPS = 5000


@when("Navier-Stokes timesteps are taken until the flow reaches steady state")
def _when_run_to_steady_state(ctx: _Context) -> None:
    assert ctx.numerics is not None
    dt = simulation.stable_timestep(ctx.mesh, ctx.viscosity, ctx.lid_speed)
    fields = ctx.fields
    previous_u: torch.Tensor | None = None
    # Steadiness is a measured residual, not a step count -- Stage 5
    # Completion Criterion 5's own "fails on not reaching it rather than
    # silently comparing an unconverged field". `ctx.steady` stays False
    # (its own default) if the cap is exhausted, and the Then step below
    # asserts it explicitly rather than only checking the profile.
    for _ in range(_STEADY_MAX_STEPS):
        result = simulation.navier_stokes_step(fields, _VELOCITY_NAME, ctx.numerics, dt)
        fields = result.fields
        u_field = fields[_U_NAME]
        assert isinstance(u_field, ScalarField)
        u_values = u_field.values
        if previous_u is not None:
            residual = float((u_values - previous_u).abs().max())
            if residual < _STEADY_RESIDUAL_TOLERANCE:
                ctx.steady = True
                ctx.result = result
                return
        previous_u = u_values.clone()
    ctx.result = result


# -- Then ------------------------------------------------------------------


@then("the provisional velocity, the corrected velocity, and the pressure field are all present")
def _then_all_present(ctx: _Context) -> None:
    assert ctx.result is not None
    assert isinstance(ctx.result.provisional_velocity, VectorField)
    assert isinstance(ctx.result.corrected_velocity, VectorField)
    assert isinstance(ctx.result.pressure, ScalarField)


@then("the corrected velocity differs from the provisional velocity")
def _then_corrected_differs(ctx: _Context) -> None:
    assert ctx.result is not None
    assert not torch.equal(
        ctx.result.corrected_velocity.values, ctx.result.provisional_velocity.values
    )


@then("the corrected velocity's own divergence is smaller than the provisional velocity's")
def _then_divergence_reduced(ctx: _Context) -> None:
    assert ctx.result is not None
    mesh = ctx.mesh
    divergence_fn = GreenGaussDivergence(_no_slip_boundary_conditions(), {})
    provisional_divergence = float(
        divergence_fn.divergence(ctx.result.provisional_velocity).abs().max()
    )
    corrected_divergence = float(
        divergence_fn.divergence(ctx.result.corrected_velocity).abs().max()
    )
    assert corrected_divergence < provisional_divergence
    assert mesh is ctx.result.corrected_velocity.mesh


@then("the velocity field is exactly the same uniform value at every step")
def _then_uniform_unchanged(ctx: _Context) -> None:
    initial = torch.tensor([1.3, -0.7], dtype=torch.float64)
    for values in ctx.history:
        assert torch.allclose(values, initial.expand_as(values), atol=1e-9)


@then("the velocity field's own divergence never leaves solver tolerance at any step")
def _then_divergence_in_tolerance(ctx: _Context) -> None:
    assert ctx.divergence_history
    for max_divergence in ctx.divergence_history:
        assert max_divergence <= _TOLERANCE


@then("the velocity field stays at rest to floating-point tolerance at every step")
def _then_stays_at_rest(ctx: _Context) -> None:
    assert ctx.history
    for values in ctx.history:
        assert torch.allclose(values, torch.zeros_like(values), atol=1e-9)


@then("both runs produce identical corrected velocity and pressure fields")
def _then_identical_runs(ctx: _Context) -> None:
    assert ctx.result is not None
    assert ctx.other_result is not None
    torch.testing.assert_close(
        ctx.result.corrected_velocity.values,
        ctx.other_result.corrected_velocity.values,
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(
        ctx.result.pressure.values, ctx.other_result.pressure.values, rtol=0, atol=0
    )


@then("the test double's own distinctive pressure value appears in the result, not a real solve's")
def _then_marker_pressure_present(ctx: _Context) -> None:
    assert ctx.result is not None
    assert torch.allclose(
        ctx.result.pressure.values,
        torch.full_like(ctx.result.pressure.values, _MarkerPressureCoupling._MARKER),
    )


@then("the test double records that the timestep's own pressure solve asked it to solve")
def _then_recording_solver_was_called(ctx: _Context) -> None:
    assert ctx.recording_solver is not None
    assert ctx.recording_solver.solve_calls > 0, (
        "the configured LinearSolver was never asked to solve; the timestep's pressure "
        "coupling must be using a solver it constructed for itself"
    )


@then(
    "the steady streamwise velocity profile matches the exact linear Couette solution at "
    "solver tolerance"
)
def _then_couette_profile_matches(ctx: _Context) -> None:
    assert ctx.steady, (
        f"flow did not reach steady state within {_STEADY_MAX_STEPS} steps "
        f"(residual tolerance {_STEADY_RESIDUAL_TOLERANCE})"
    )
    assert ctx.result is not None
    u_field = ctx.result.fields[_U_NAME]
    assert isinstance(u_field, ScalarField)
    for cell in range(ctx.mesh.num_cells):
        _x, y = ctx.mesh.cell_centroid(cell)
        exact = ctx.lid_speed * (y - ctx.channel_bottom) / ctx.channel_height
        actual = float(u_field.value_at(cell))
        assert actual == pytest.approx(exact, abs=1e-6), (
            f"cell {cell} at y={y}: expected {exact}, got {actual}"
        )


@then("the wall-normal velocity component stays zero everywhere")
def _then_wall_normal_velocity_zero(ctx: _Context) -> None:
    assert ctx.result is not None
    v_field = ctx.result.fields[_V_NAME]
    assert isinstance(v_field, ScalarField)
    assert torch.allclose(v_field.values, torch.zeros_like(v_field.values), atol=1e-9)


@then("total kinetic energy never increases from one step to the next")
def _then_ke_never_increases(ctx: _Context) -> None:
    assert len(ctx.ke_history) >= 2
    for previous, current in zip(ctx.ke_history, ctx.ke_history[1:], strict=False):
        assert current <= previous + 1e-12, f"kinetic energy increased: {previous} -> {current}"


# -- Taylor-Green vortex decay: the emergent-phenomenon pair ---------------


_TG_AMPLITUDE = 0.3
_TG_EXTENT = (12, 12)
_TG_DOMAIN_LENGTH = 1.0
_TG_MEASURE_STEPS = (5, 40)
# Measured directly before being trusted (this module's own commit
# message / `docs/planning/roadmap.md` TASK-034's own Design decision):
# at `_TG_VISCOSITY_MATCHED`, the measured decay rate agreed with the
# exact closed form to within ~0.3%; at `_TG_VISCOSITY_MISMATCHED` (100x
# smaller -- the mesh's own advective numerical diffusion stays fixed
# while the physical one shrinks) the measured rate was off by a factor
# of roughly 3.8. Neither bound below was chosen to make a marginal
# result pass -- both keep real margin around the two measured ratios.
_TG_VISCOSITY_MATCHED = 0.05
_TG_VISCOSITY_MISMATCHED = 0.0005


def _taylor_green_wavenumber() -> float:

    return 2 * math.pi / _TG_DOMAIN_LENGTH


@dataclass
class _TaylorGreenContext:
    viscosity: float
    measured_rate: float = 0.0
    exact_rate: float = 0.0


def _run_taylor_green(viscosity: float) -> _TaylorGreenContext:

    k = _taylor_green_wavenumber()
    mesh = StructuredCartesianMesh(
        origin=(0.0, 0.0),
        spacing=(_TG_DOMAIN_LENGTH / _TG_EXTENT[0], _TG_DOMAIN_LENGTH / _TG_EXTENT[1]),
        extent=_TG_EXTENT,
    )
    periodic = {"north": "south", "south": "north", "east": "west", "west": "east"}

    def value(x: float, y: float) -> tuple[float, float]:
        return (
            _TG_AMPLITUDE * math.cos(k * x) * math.sin(k * y),
            -_TG_AMPLITUDE * math.sin(k * x) * math.cos(k * y),
        )

    numerics = _real_numerics({}, periodic, viscosity=viscosity)
    dt = simulation.stable_timestep(mesh, viscosity, _TG_AMPLITUDE, safety_factor=0.25)
    velocity = VectorField(mesh, _VELOCITY_NAME, num_components=2, initial_value=value)
    fields: dict[str, Field] = {c.name: c for c in velocity.decompose()}
    probe_cell = mesh.cell_id(_TG_EXTENT[0] // 4, _TG_EXTENT[1] // 4)

    amplitudes: list[float] = []
    times: list[float] = []
    elapsed = 0.0
    max_step = max(_TG_MEASURE_STEPS)
    u_field = fields[_U_NAME]
    assert isinstance(u_field, ScalarField)
    for step in range(max_step + 1):
        if step in _TG_MEASURE_STEPS:
            amplitudes.append(abs(float(u_field.value_at(probe_cell))))
            times.append(elapsed)
        result = simulation.navier_stokes_step(fields, _VELOCITY_NAME, numerics, dt)
        fields = result.fields
        u_field = fields[_U_NAME]
        assert isinstance(u_field, ScalarField)
        elapsed += dt

    first_amplitude, last_amplitude = amplitudes[0], amplitudes[-1]
    first_time, last_time = times[0], times[-1]
    measured_rate = -math.log(last_amplitude / first_amplitude) / (last_time - first_time)
    exact_rate = 2 * k * k * viscosity
    return _TaylorGreenContext(
        viscosity=viscosity, measured_rate=measured_rate, exact_rate=exact_rate
    )


@given(
    "a Taylor-Green vortex on a periodic domain at a viscosity where physical diffusion dominates",
    target_fixture="tg_ctx",
)
def _given_taylor_green_matched() -> float:
    return _TG_VISCOSITY_MATCHED


@given(
    "a Taylor-Green vortex on a periodic domain at a viscosity where numerical diffusion dominates",
    target_fixture="tg_ctx",
)
def _given_taylor_green_mismatched() -> float:
    return _TG_VISCOSITY_MISMATCHED


@when("the vortex is advanced and its own decay rate is measured", target_fixture="tg_result")
def _when_taylor_green_measured(tg_ctx: float) -> _TaylorGreenContext:
    return _run_taylor_green(tg_ctx)


@then("the measured decay rate matches the exact closed-form rate closely")
def _then_taylor_green_matches(tg_result: _TaylorGreenContext) -> None:
    ratio = tg_result.measured_rate / tg_result.exact_rate
    assert 0.9 <= ratio <= 1.1, (
        f"measured/exact ratio {ratio} outside the expected close-match band"
    )


@then("the measured decay rate does not match the exact closed-form rate")
def _then_taylor_green_mismatches(tg_result: _TaylorGreenContext) -> None:
    ratio = tg_result.measured_rate / tg_result.exact_rate
    assert ratio > 2.0 or ratio < 0.5, (
        f"measured/exact ratio {ratio} was unexpectedly close to a match"
    )


# -- Lid-driven cavity against Ghia, Ghia & Shin (1982) --------------------
#
# This project's most computationally expensive scenario, deliberately
# (`docs/planning/roadmap.md` TASK-034's own Design decision): three real
# runs to a measured steady state. Resolutions chosen odd (9, 13, 17) so
# the vertical/horizontal centreline (x=0.5, y=0.5 in unit-cavity
# coordinates) always lands exactly on a column/row of cell centres, no
# interpolation needed for the two Ghia comparisons themselves.

_CAVITY_RESOLUTIONS = (9, 13, 17)
_CAVITY_REYNOLDS_NUMBER = 100
_CAVITY_LID_SPEED = 1.0
_CAVITY_VISCOSITY = _CAVITY_LID_SPEED / _CAVITY_REYNOLDS_NUMBER  # Re = U*L/nu, L = 1
_CAVITY_STEADY_RESIDUAL_TOLERANCE = 1e-6
_CAVITY_MAX_STEPS = 6000
_CAVITY_ORIGIN = (0.35, -0.2)
"""A deliberately non-trivial mesh origin, added 2026-08-29 by the Stage
5 exit audit (Completion Criterion 7's degenerate-fixture rule).

**Two of that rule's three cavity-relevant clauses cannot be honoured
here, and one can.** Ghia, Ghia & Shin (1982)'s Re = 100 profiles are
nondimensionalised on a *unit square* driven at a *unit* lid speed, so a
non-square cavity or a lid velocity other than 1.0 would not be
comparable to the reference at all -- those two exceptions are forced by
the reference frame, not chosen, and are recorded in this scenario's own
feature file where a reader meets them. The origin was never forced: it
only ever has to be subtracted back out where a comparison is made in
unit-cavity coordinates, which is exactly one place
(`_then_primary_vortex_near_ghia`). Shifting it makes that conversion a
real step rather than an identity, so a vortex detector that quietly
assumed the mesh starts at the origin now fails.

The Ghia *profile* comparison is untouched by this: it indexes cells
(`mesh.cell_id`), never coordinates, so its errors are identical at any
origin -- verified directly by a full three-resolution run at this
origin (0.14328, 0.08741, 0.05775) before the change was committed.
"""
_CAVITY_FINEST_ERROR_TOLERANCE = 0.08
"""Stage 5 Completion Criterion 5's own "the absolute tolerance is stated
and defended in the feature file against the mesh actually used" --
undischarged until the Stage 5 exit audit (2026-08-29) added it, which
left monotonic decrease as the only accuracy claim this scenario made,
and errors of 10, 5 and 2 would satisfy that exactly as well as the real
ones do.

**Defended against three measured numbers, not chosen for comfort.** On
the finest mesh here (17x17) the real run scores 0.0578, so this bound
keeps roughly 38% margin. The coarsest (9x9) scores 0.1433, so this is
genuinely a claim about the finest mesh rather than one any resolution
would pass. And a velocity field of zeros everywhere -- the cheapest
possible "solved nothing" failure -- scores 0.3366 against these same
34 tabulated points, so the bound sits nearly six times tighter than
doing nothing at all. It is not tight enough to call first-order upwind
accurate at this resolution, and is not meant to be: Criterion 5's
gating claim is the convergence one, and `docs/implementation/
upgrade-paths.md` is where a less diffusive scheme lands.
"""
# Ghia's own primary-vortex distance bound: measured directly on a real
# (coarser, n=14) run before being trusted -- the detected centre landed
# 0.019 away from Ghia's own (0.6172, 0.7344) in unit-cavity coordinates.
# 0.1 keeps an order of magnitude of margin around that measured distance
# without being so loose a genuinely wrong vortex location could still
# pass.
_CAVITY_VORTEX_DISTANCE_TOLERANCE = 0.1
# The same measured run found clear opposite-sign vorticity (magnitude
# 0.13-0.43) throughout each bottom corner's own sub-region; this
# threshold sits an order of magnitude below that measured range.
_CAVITY_VORTICITY_NOISE_THRESHOLD = 0.02


@dataclass
class _CavityRun:
    resolution: int
    error: float
    u_field: ScalarField | None = None
    v_field: ScalarField | None = None
    mesh: StructuredCartesianMesh | None = None
    steady: bool = False


def _run_cavity(n: int) -> _CavityRun:
    mesh = StructuredCartesianMesh(origin=_CAVITY_ORIGIN, spacing=(1.0 / n, 1.0 / n), extent=(n, n))
    lid = DirichletBoundaryCondition(0.0, {_U_NAME: _CAVITY_LID_SPEED, _V_NAME: 0.0})
    wall = DirichletBoundaryCondition(0.0)
    bcs: dict[str, BoundaryCondition] = {"north": lid, "south": wall, "east": wall, "west": wall}
    numerics = _real_numerics(bcs, viscosity=_CAVITY_VISCOSITY)
    dt = simulation.stable_timestep(mesh, _CAVITY_VISCOSITY, _CAVITY_LID_SPEED, safety_factor=0.25)

    velocity = VectorField(mesh, _VELOCITY_NAME, num_components=2, initial_value=(0.0, 0.0))
    fields: dict[str, Field] = {c.name: c for c in velocity.decompose()}
    previous_u: torch.Tensor | None = None
    steady = False
    for _ in range(_CAVITY_MAX_STEPS):
        result = simulation.navier_stokes_step(fields, _VELOCITY_NAME, numerics, dt)
        fields = result.fields
        u_field = fields[_U_NAME]
        assert isinstance(u_field, ScalarField)
        u_values = u_field.values
        if previous_u is not None:
            residual = float((u_values - previous_u).abs().max()) / dt
            if residual < _CAVITY_STEADY_RESIDUAL_TOLERANCE:
                steady = True
                break
        previous_u = u_values.clone()

    u_field = fields[_U_NAME]
    v_field = fields[_V_NAME]
    assert isinstance(u_field, ScalarField)
    assert isinstance(v_field, ScalarField)

    center = n // 2
    u_errors = []
    for y_ghia, u_ghia in U_VELOCITY_ALONG_VERTICAL_CENTERLINE:
        row = min(int(y_ghia * n), n - 1)
        cell = mesh.cell_id(center, row)
        u_errors.append((float(u_field.value_at(cell)) - u_ghia) ** 2)
    v_errors = []
    for x_ghia, v_ghia in V_VELOCITY_ALONG_HORIZONTAL_CENTERLINE:
        column = min(int(x_ghia * n), n - 1)
        cell = mesh.cell_id(column, center)
        v_errors.append((float(v_field.value_at(cell)) - v_ghia) ** 2)
    error = math.sqrt((sum(u_errors) + sum(v_errors)) / (len(u_errors) + len(v_errors)))

    return _CavityRun(
        resolution=n, error=error, u_field=u_field, v_field=v_field, mesh=mesh, steady=steady
    )


@given(
    "three lid-driven cavity meshes at increasing resolution, at Reynolds number 100",
    target_fixture="cavity_resolutions",
)
def _given_cavity_resolutions() -> tuple[int, ...]:
    return _CAVITY_RESOLUTIONS


@when("each is run to a measured steady state", target_fixture="cavity_runs")
def _when_cavity_runs(cavity_resolutions: tuple[int, ...]) -> list[_CavityRun]:
    return [_run_cavity(n) for n in cavity_resolutions]


@then(
    "the error against Ghia's centreline profiles decreases monotonically across the three "
    "resolutions"
)
def _then_cavity_error_decreases(cavity_runs: list[_CavityRun]) -> None:
    for run in cavity_runs:
        assert run.steady, (
            f"resolution {run.resolution} did not reach steady state within "
            f"{_CAVITY_MAX_STEPS} steps"
        )
    errors = [run.error for run in cavity_runs]
    for previous, current in zip(errors, errors[1:], strict=False):
        assert current < previous, f"error did not decrease monotonically: {errors}"


@then("the finest resolution's own error is below the stated absolute bound for that mesh")
def _then_finest_error_within_absolute_bound(cavity_runs: list[_CavityRun]) -> None:
    run = _finest_run(cavity_runs)
    assert run.error < _CAVITY_FINEST_ERROR_TOLERANCE, (
        f"resolution {run.resolution} scored {run.error} against Ghia's centreline profiles, "
        f"above this mesh's own stated bound of {_CAVITY_FINEST_ERROR_TOLERANCE}"
    )


def _finest_run(cavity_runs: list[_CavityRun]) -> _CavityRun:
    return max(cavity_runs, key=lambda run: run.resolution)


def _vorticity_at(run: _CavityRun, i: int, j: int) -> float:
    assert run.mesh is not None
    assert run.u_field is not None
    assert run.v_field is not None
    dx = 1.0 / run.resolution
    dv_dx = (
        float(run.v_field.value_at(run.mesh.cell_id(i + 1, j)))
        - float(run.v_field.value_at(run.mesh.cell_id(i - 1, j)))
    ) / (2 * dx)
    du_dy = (
        float(run.u_field.value_at(run.mesh.cell_id(i, j + 1)))
        - float(run.u_field.value_at(run.mesh.cell_id(i, j - 1)))
    ) / (2 * dx)
    return dv_dx - du_dy


@then("the finest resolution's primary vortex centre is within a stated distance of Ghia's own")
def _then_primary_vortex_near_ghia(cavity_runs: list[_CavityRun]) -> None:
    run = _finest_run(cavity_runs)
    assert run.mesh is not None
    assert run.u_field is not None
    assert run.v_field is not None
    n = run.resolution
    margin = n // 4
    best: tuple[float, int, int] | None = None
    for i in range(margin, n - margin):
        for j in range(margin, n - margin):
            cell = run.mesh.cell_id(i, j)
            u_val = float(run.u_field.value_at(cell))
            v_val = float(run.v_field.value_at(cell))
            magnitude = math.hypot(u_val, v_val)
            if best is None or magnitude < best[0]:
                best = (magnitude, i, j)
    assert best is not None
    _magnitude, i, j = best
    mesh_x, mesh_y = run.mesh.cell_centroid(run.mesh.cell_id(i, j))
    # Ghia's coordinates are unit-cavity ones, measured from the cavity's
    # own bottom-left corner; this mesh does not start there
    # (`_CAVITY_ORIGIN`), so the conversion is a real step, not an
    # identity. The cavity is one unit across by construction (spacing
    # 1/n, extent n), so subtracting the origin is the whole conversion.
    x, y = mesh_x - _CAVITY_ORIGIN[0], mesh_y - _CAVITY_ORIGIN[1]
    ghia_x, ghia_y = PRIMARY_VORTEX_CENTER
    distance = math.hypot(x - ghia_x, y - ghia_y)
    assert distance < _CAVITY_VORTEX_DISTANCE_TOLERANCE, (
        f"detected primary vortex at ({x}, {y}) in unit-cavity coordinates, {distance} "
        f"from Ghia's own {PRIMARY_VORTEX_CENTER}"
    )


@then(
    "the finest resolution shows both downstream secondary corner vortices, rotating opposite "
    "the primary"
)
def _then_secondary_vortices_present(cavity_runs: list[_CavityRun]) -> None:
    run = _finest_run(cavity_runs)
    assert run.mesh is not None
    n = run.resolution
    margin = n // 4
    best: tuple[float, int, int] | None = None
    for i in range(margin, n - margin):
        for j in range(margin, n - margin):
            assert run.u_field is not None
            assert run.v_field is not None
            cell = run.mesh.cell_id(i, j)
            magnitude = math.hypot(
                float(run.u_field.value_at(cell)), float(run.v_field.value_at(cell))
            )
            if best is None or magnitude < best[0]:
                best = (magnitude, i, j)
    assert best is not None
    _magnitude, pi, pj = best
    primary_vorticity = _vorticity_at(run, pi, pj)
    primary_positive = primary_vorticity > 0

    def _has_opposite_sign_vorticity(i_range: range, j_range: range) -> bool:
        for i in i_range:
            for j in j_range:
                vorticity = _vorticity_at(run, i, j)
                if (vorticity > 0) != primary_positive and abs(
                    vorticity
                ) > _CAVITY_VORTICITY_NOISE_THRESHOLD:
                    return True
        return False

    bottom_left = _has_opposite_sign_vorticity(range(1, n // 3), range(1, n // 3))
    bottom_right = _has_opposite_sign_vorticity(range(2 * n // 3, n - 1), range(1, n // 3))
    assert bottom_left, "no opposite-sign (secondary) vorticity found near the bottom-left corner"
    assert bottom_right, "no opposite-sign (secondary) vorticity found near the bottom-right corner"
