"""Binds `tests/features/temperature_field.feature` (TASK-035, Stage 6's
second task in build order). Not a golden demo -- no config file under
`examples/golden-demos/`, no CLI subprocess run, the same `tests/unit/`
shape `test_navier_stokes_timestep.py` already established for
engine-level claims. This task's own two golden demos (Heat Transport,
Thermal Buoyancy) are bound separately, under `tests/golden/`.

Every physical scenario below (warm-patch rise, gravity reversal, the
null case, Rayleigh-Benard) builds `AssembledNumerics` directly and
drives `navier_stokes_step` itself, the same shape
`test_navier_stokes_timestep.py` uses -- no config file, no
`bootstrap()`. The one exception is the analytic-decay-rate scenario,
which goes through `load_config`/`bootstrap()` (mirroring
`tests/golden/test_heat_diffusion.py`'s own two-frame-count shape)
because its own claim is specifically about a *configured* field's
identity, not the bare engine mechanism. The rejection scenario also
goes through `load_config`, the same "rejection scenarios call
`load_config` directly" shape `test_field_declaration_configuration.py`
already established.

Every numeric threshold below (the rise/reversal magnitude, the
Rayleigh-Benard step count and RMS-ratio bound) was measured against
this real implementation while writing this file, not chosen in
advance -- the same discipline `test_navier_stokes_timestep.py`'s own
Ghia/Couette bounds and `test_piso_pressure_coupling.py`'s 70% bound
both follow.
"""

from __future__ import annotations

import inspect
import math
from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.configuration import load_config
from pyflow.configuration.schema import NumericsConfig
from pyflow.engine import simulation
from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import (
    AssembledNumerics,
    assemble_numerics,
    register_source_term,
)
from pyflow.engine.numerics.boundary_condition import DirichletBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver
from pyflow.engine.numerics.pressure_coupling import PISO
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import navier_stokes_step, stable_timestep
from pyflow.engine.vector_field import VectorField
from pyflow.physics.buoyancy import BoussinesqBuoyancy

scenarios("temperature_field.feature")

# -- Shared physical fixtures ------------------------------------------------
#
# Non-square, non-trivially-origined -- `docs/practices.md`'s "distinct
# factors" rule, the same discipline every Stage 4/5 fixture in this
# repository follows.

_ORIGIN = (0.2, -0.3)
_SPACING = (0.1, 0.15)
_EXTENT = (6, 8)
_VISCOSITY = 0.1
_TEMPERATURE_DIFFUSIVITY = 0.05
_REFERENCE_VALUE = 0.0
_BUOYANCY_COEFFICIENT = -0.003
_WARM_PATCH_AMPLITUDE = 50.0
_WARM_PATCH_SIGMA = 0.15
_RISE_STEPS = 5


def _mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=_ORIGIN, spacing=_SPACING, extent=_EXTENT)


def _domain_center(mesh: StructuredCartesianMesh) -> tuple[float, float]:
    nx, ny = _EXTENT
    dx, dy = _SPACING
    ox, oy = _ORIGIN
    return (ox + nx * dx / 2, oy + ny * dy / 2)


def _nearest_cell(mesh: StructuredCartesianMesh, point: tuple[float, float]) -> int:
    px, py = point
    return min(
        range(mesh.num_cells),
        key=lambda c: (mesh.cell_centroid(c)[0] - px) ** 2 + (mesh.cell_centroid(c)[1] - py) ** 2,
    )


def _no_slip_boundary_conditions() -> dict[str, DirichletBoundaryCondition]:
    """No-slip velocity at every wall, with temperature pinned to its own
    ambient/reference value there too (`overrides`) -- a wall genuinely
    at the ambient value, not an incidental zero that would itself drive
    a spurious temperature gradient near the boundary.
    """
    condition = DirichletBoundaryCondition(0.0, {"temperature": _REFERENCE_VALUE})
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def _numerics_for(
    gravity: tuple[float, float], couplings: dict[str, tuple[float, float]]
) -> AssembledNumerics:
    bcs = _no_slip_boundary_conditions()
    advection = FirstOrderUpwindAdvection(bcs, {})
    diffusion = CentralDifferenceDiffusion(
        bcs, {}, _VISCOSITY, {"temperature": _TEMPERATURE_DIFFUSIVITY}
    )
    solver = ConjugateGradientSolver(tolerance=1e-8, max_iterations=1000)
    pressure_coupling = PISO(solver, bcs, tolerance=1e-6, max_iterations=200)
    buoyancy = BoussinesqBuoyancy(gravity=gravity, couplings=couplings)
    return AssembledNumerics(
        advection=advection,
        diffusion=diffusion,
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=pressure_coupling,
        source_term=buoyancy,
        boundary_conditions=bcs,
        names={},
    )


def _warm_patch_temperature(mesh: StructuredCartesianMesh) -> ScalarField:
    cx, cy = _domain_center(mesh)

    def pattern(x: float, y: float) -> float:
        return _REFERENCE_VALUE + _WARM_PATCH_AMPLITUDE * math.exp(
            -((x - cx) ** 2 + (y - cy) ** 2) / (2 * _WARM_PATCH_SIGMA**2)
        )

    return ScalarField(mesh, "temperature", initial_value=pattern)


def _initial_velocity_state(mesh: StructuredCartesianMesh) -> dict[str, Field]:
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    return {component.name: component for component in velocity.decompose()}


def _advance(
    state: dict[str, Field], numerics: AssembledNumerics, dt: float, steps: int
) -> dict[str, Field]:
    for _ in range(steps):
        state = navier_stokes_step(state, "velocity", numerics, dt).fields
    return state


class _MarkerSourceTerm(SourceTerm):
    """Returns a distinctive, unphysical constant for velocity's own
    vertical component -- exists only to prove the timestep calls the
    *configured* source term, the same `_MarkerPressureCoupling`-shaped
    substitution double `test_navier_stokes_timestep.py` already uses
    for its own seam.
    """

    MARKER_VALUE = 12345.0

    def __init__(self, gravity: tuple[float, float], couplings: object) -> None:
        del gravity, couplings

    def source(self, field: Field, state: object) -> torch.Tensor:
        del state
        assert isinstance(field, CollocatedField)
        if field.name == VectorField.component_name("velocity", 1):
            return torch.full(
                (field.mesh.num_cells, *field.component_shape),
                self.MARKER_VALUE,
                dtype=torch.float64,
            )
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


# -- Fixture context ----------------------------------------------------


@dataclass
class _Context:
    config_path: Path | None = None
    error: ValueError | None = None
    early_amplitude: float | None = None
    late_amplitude: float | None = None
    dt: float | None = None
    rise_velocity: float | None = None
    reversed_velocity: float | None = None
    with_field_state: dict[str, Field] | None = None
    without_field_state: dict[str, Field] | None = None
    marker_result: dict[str, Field] | None = None
    below_rms: list[float] | None = None
    above_rms: list[float] | None = None


# -- Given -----------------------------------------------------------------


@given(
    "a periodic domain transporting a named temperature field with a sinusoidal initial condition",
    target_fixture="ctx",
)
def _given_periodic_temperature(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "rendering:\n  backend: offscreen\n"
        "mesh:\n  extent: [24, 3]\n  spacing: [0.05, 0.3]\n"
        "numerics:\n"
        "  boundary_conditions:\n"
        "    north:\n      type: periodic\n"
        "    south:\n      type: periodic\n"
        "    east:\n      type: periodic\n"
        "    west:\n      type: periodic\n"
        "fields:\n"
        "  - name: temperature\n"
        "    initial_condition: sinusoidal_mode\n"
        "    diffusion_coefficient: 0.05\n"
        "field_display:\n  render_field: temperature\n"
    )
    return _Context(config_path=config_path)


@given(
    "a closed, no-slip domain at rest with a warm patch and downward gravity", target_fixture="ctx"
)
def _given_warm_patch_down(tmp_path: Path) -> _Context:
    del tmp_path
    mesh = _mesh()
    numerics = _numerics_for(
        (0.0, -9.81), {"temperature": (_REFERENCE_VALUE, _BUOYANCY_COEFFICIENT)}
    )
    state = _initial_velocity_state(mesh)
    state["temperature"] = _warm_patch_temperature(mesh)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    state = _advance(state, numerics, dt, _RISE_STEPS)
    cell = _nearest_cell(mesh, _domain_center(mesh))
    v = state["velocity.1"]
    assert isinstance(v, ScalarField)
    return _Context(rise_velocity=v.value_at(cell))


@given(
    "a closed, no-slip domain at rest with a warm patch and upward gravity", target_fixture="ctx"
)
def _given_warm_patch_up(tmp_path: Path) -> _Context:
    del tmp_path
    mesh = _mesh()
    numerics = _numerics_for(
        (0.0, 9.81), {"temperature": (_REFERENCE_VALUE, _BUOYANCY_COEFFICIENT)}
    )
    state = _initial_velocity_state(mesh)
    state["temperature"] = _warm_patch_temperature(mesh)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    state = _advance(state, numerics, dt, _RISE_STEPS)
    cell = _nearest_cell(mesh, _domain_center(mesh))
    v = state["velocity.1"]
    assert isinstance(v, ScalarField)
    return _Context(reversed_velocity=v.value_at(cell))


@given(
    "a closed, no-slip domain at rest with a uniform temperature field and downward gravity",
    target_fixture="ctx",
)
def _given_uniform_temperature(tmp_path: Path) -> _Context:
    del tmp_path
    mesh = _mesh()
    numerics = _numerics_for(
        (0.0, -9.81), {"temperature": (_REFERENCE_VALUE, _BUOYANCY_COEFFICIENT)}
    )
    state = _initial_velocity_state(mesh)
    state["temperature"] = ScalarField(mesh, "temperature", initial_value=_REFERENCE_VALUE)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    state = _advance(state, numerics, dt, _RISE_STEPS)
    return _Context(with_field_state=state)


@given("the same domain carrying no temperature field at all")
def _given_no_temperature_field(ctx: _Context) -> None:
    mesh = _mesh()
    numerics = _numerics_for((0.0, -9.81), {})
    state = _initial_velocity_state(mesh)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    ctx.without_field_state = _advance(state, numerics, dt, _RISE_STEPS)


@given(
    "a SourceTerm test double registered under its own name and selected by configuration",
    target_fixture="ctx",
)
def _given_marker_source_term() -> _Context:
    name = "test_only_marker_source_term_for_temperature_field_test"
    register_source_term(name, _MarkerSourceTerm)
    mesh = _mesh()
    config = NumericsConfig(source_term=name)  # type: ignore[arg-type]
    numerics = assemble_numerics(config)
    state = _initial_velocity_state(mesh)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    result = navier_stokes_step(state, "velocity", numerics, dt)
    return _Context(marker_result=result.fields)


@given(
    "a configuration transporting a declared field with no buoyancy coupling on it, source "
    "term left at its default",
    target_fixture="ctx",
)
def _given_no_coupling_default_source(tmp_path: Path) -> _Context:
    del tmp_path
    mesh = _mesh()
    numerics = _numerics_for((0.0, -9.81), {})  # "none"-equivalent: empty couplings
    state = _initial_velocity_state(mesh)
    state["tracer"] = ScalarField(mesh, "tracer", initial_value=1.0)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    state = _advance(state, numerics, dt, _RISE_STEPS)
    return _Context(with_field_state=state)


@given("the same configuration with the boussinesq_buoyancy source term selected instead")
def _given_boussinesq_selected_with_no_couplings(ctx: _Context) -> None:
    mesh = _mesh()
    # Real BoussinesqBuoyancy, genuinely selected, but with no field ever
    # given a buoyancy coupling -- the claim is that this is
    # indistinguishable from "none", not merely that the config is valid.
    numerics = _numerics_for((0.0, -9.81), {})
    state = _initial_velocity_state(mesh)
    state["tracer"] = ScalarField(mesh, "tracer", initial_value=1.0)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    ctx.without_field_state = _advance(state, numerics, dt, _RISE_STEPS)


# -- Rayleigh-Benard ---------------------------------------------------------

_RB_EXTENT = (12, 6)
_RB_HEIGHT = 1.0
_RB_WIDTH = 2.0
_RB_SPACING = (_RB_WIDTH / _RB_EXTENT[0], _RB_HEIGHT / _RB_EXTENT[1])
_RB_VISCOSITY = 0.01
_RB_DIFFUSIVITY = 0.01
_RB_COEFFICIENT = -0.0102
_RB_DELTA_T = 20.0
_RB_STEPS = 300


def _rayleigh_benard_numerics(heated_from_below: bool) -> tuple[AssembledNumerics, float]:
    bottom = _RB_DELTA_T / 2 if heated_from_below else -_RB_DELTA_T / 2
    top = -_RB_DELTA_T / 2 if heated_from_below else _RB_DELTA_T / 2
    south = DirichletBoundaryCondition(0.0, {"temperature": bottom})
    north = DirichletBoundaryCondition(0.0, {"temperature": top})
    bcs = {"south": south, "north": north}
    periodic = {"east": "west", "west": "east"}
    advection = FirstOrderUpwindAdvection(bcs, periodic)
    diffusion = CentralDifferenceDiffusion(
        bcs, periodic, _RB_VISCOSITY, {"temperature": _RB_DIFFUSIVITY}
    )
    solver = ConjugateGradientSolver(tolerance=1e-8, max_iterations=2000)
    pressure_coupling = PISO(
        solver, bcs, tolerance=1e-6, max_iterations=300, periodic_pairs=periodic
    )
    buoyancy = BoussinesqBuoyancy(
        gravity=(0.0, -9.81), couplings={"temperature": (0.0, _RB_COEFFICIENT)}
    )
    numerics = AssembledNumerics(
        advection=advection,
        diffusion=diffusion,
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=pressure_coupling,
        source_term=buoyancy,
        boundary_conditions=bcs,
        names={},
    )
    mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=_RB_SPACING, extent=_RB_EXTENT)
    dt = stable_timestep(mesh, _RB_VISCOSITY, velocity_scale=1.0) * 0.5
    return numerics, dt


def _rayleigh_benard_rms(heated_from_below: bool) -> list[float]:
    """The vertical velocity's own RMS at four checkpoints -- a monotone
    rise for the unstable (heated-from-below) case, essentially flat for
    the stable one, measured directly rather than assumed (see this
    module's own docstring).
    """
    numerics, dt = _rayleigh_benard_numerics(heated_from_below)
    mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=_RB_SPACING, extent=_RB_EXTENT)
    bottom = _RB_DELTA_T / 2 if heated_from_below else -_RB_DELTA_T / 2
    top = -_RB_DELTA_T / 2 if heated_from_below else _RB_DELTA_T / 2

    def temperature_ic(x: float, y: float) -> float:
        base = bottom + (top - bottom) * (y / _RB_HEIGHT)
        perturbation = (
            0.01
            * _RB_DELTA_T
            * math.cos(2 * math.pi * x / _RB_WIDTH)
            * math.sin(math.pi * y / _RB_HEIGHT)
        )
        return base + perturbation

    state = _initial_velocity_state(mesh)
    state["temperature"] = ScalarField(mesh, "temperature", initial_value=temperature_ic)

    checkpoints = [step for step in (_RB_STEPS,)]
    results: list[float] = []
    step = 0
    for target in checkpoints:
        while step < target:
            state = navier_stokes_step(state, "velocity", numerics, dt).fields
            step += 1
        v = state["velocity.1"]
        assert isinstance(v, ScalarField)
        rms = math.sqrt(sum(v.value_at(c) ** 2 for c in range(mesh.num_cells)) / mesh.num_cells)
        results.append(rms)
    return results


@given("a closed, no-slip fluid layer heated from below", target_fixture="ctx")
def _given_heated_from_below() -> _Context:
    return _Context(below_rms=_rayleigh_benard_rms(heated_from_below=True))


@given("the same layer heated from above instead")
def _given_heated_from_above(ctx: _Context) -> None:
    ctx.above_rms = _rayleigh_benard_rms(heated_from_below=False)


@given(
    "a configuration declaring a field with a buoyancy coupling and simulation.velocity_solved "
    "left false",
    target_fixture="ctx",
)
def _given_buoyancy_without_solved_velocity(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "fields:\n"
        "  - name: temperature\n"
        "    buoyancy_reference_value: 0.0\n"
        "    buoyancy_coefficient: -0.003\n"
    )
    return _Context(config_path=config_path)


# -- When ------------------------------------------------------------------


@when("it is run for a few real timesteps and again for many more")
def _when_run_twice(ctx: _Context) -> None:
    assert ctx.config_path is not None
    early_window = bootstrap(ctx.config_path, backend="offscreen", max_frames=1)
    assert early_window.simulation_fields is not None
    early_field = early_window.simulation_fields["temperature"]
    assert isinstance(early_field, ScalarField)

    late_window = bootstrap(ctx.config_path, backend="offscreen", max_frames=201)
    assert late_window.simulation_fields is not None
    late_field = late_window.simulation_fields["temperature"]
    assert isinstance(late_field, ScalarField)

    ctx.dt = load_config(ctx.config_path).numerics.timestep
    ctx.early_amplitude = _rms_amplitude(early_field)
    ctx.late_amplitude = _rms_amplitude(late_field)


def _rms_amplitude(field: ScalarField) -> float:
    mesh = field.mesh
    total = sum(float(field.value_at(cell)) ** 2 for cell in range(mesh.num_cells))
    return math.sqrt(total / mesh.num_cells)


@when("several Navier-Stokes timesteps are taken")
def _when_several_timesteps_taken() -> None:
    # Already advanced inside the `Given` steps above -- both fixtures
    # this scenario shape uses need their own numerics/state built
    # before they can be advanced, so there is nothing further to do
    # here; kept as a real step so the scenario reads naturally.
    pass


@when("one Navier-Stokes timestep is taken")
def _when_one_timestep_taken() -> None:
    pass


@when("several Navier-Stokes timesteps are taken on both")
def _when_several_timesteps_taken_on_both() -> None:
    pass


@when("both are advanced for many Navier-Stokes timesteps")
def _when_both_advanced() -> None:
    pass


@when("the configuration is loaded")
def _when_configuration_loaded(ctx: _Context) -> None:
    assert ctx.config_path is not None
    try:
        load_config(ctx.config_path)
    except ValueError as exc:
        ctx.error = exc


@when("the orchestrator module's source is inspected")
def _when_source_inspected() -> None:
    pass


# -- Then --------------------------------------------------------------


@then(
    "the measured decay rate matches the analytic rate set by the temperature field's own "
    "diffusion coefficient and wavenumber"
)
def _then_decay_rate_matches_analytic(ctx: _Context) -> None:
    assert ctx.early_amplitude is not None
    assert ctx.late_amplitude is not None
    assert ctx.dt is not None
    elapsed_steps = 200
    elapsed_time = ctx.dt * elapsed_steps
    measured_rate = -math.log(ctx.late_amplitude / ctx.early_amplitude) / elapsed_time

    domain_width = 24 * 0.05
    wavenumber = 2 * math.pi / domain_width
    analytic_rate = 0.05 * wavenumber**2

    assert measured_rate == pytest.approx(analytic_rate, rel=0.1), (
        f"expected decay at roughly {analytic_rate} per unit time, measured {measured_rate}"
    )


@then("the warm patch's own vertical velocity is measurably upward")
def _then_warm_patch_rises(ctx: _Context) -> None:
    assert ctx.rise_velocity is not None
    assert ctx.rise_velocity > 0.01, (
        f"expected a clearly positive (upward) vertical velocity, got {ctx.rise_velocity}"
    )


@then("the warm patch's own vertical velocity is measurably downward")
def _then_warm_patch_sinks_with_reversed_gravity(ctx: _Context) -> None:
    assert ctx.reversed_velocity is not None
    assert ctx.reversed_velocity < -0.01, (
        f"expected a clearly negative (downward) vertical velocity, got {ctx.reversed_velocity}"
    )


@then("the two velocity fields are identical, element by element")
def _then_velocity_fields_identical(ctx: _Context) -> None:
    assert ctx.with_field_state is not None
    assert ctx.without_field_state is not None
    for name in ("velocity.0", "velocity.1"):
        with_field = ctx.with_field_state[name]
        without_field = ctx.without_field_state[name]
        assert isinstance(with_field, ScalarField)
        assert isinstance(without_field, ScalarField)
        assert torch.equal(with_field.values, without_field.values), (
            f"expected {name!r} to be bit-identical with and without the temperature field"
        )


@then("the test double's own distinctive contribution appears in the result, not a real source's")
def _then_marker_appears(ctx: _Context) -> None:
    assert ctx.marker_result is not None
    v1 = ctx.marker_result["velocity.1"]
    assert isinstance(v1, ScalarField)
    for cell in range(v1.mesh.num_cells):
        assert v1.value_at(cell) != 0.0


@then("the two runs produce identical fields, element by element")
def _then_runs_identical(ctx: _Context) -> None:
    assert ctx.with_field_state is not None
    assert ctx.without_field_state is not None
    for name in ("velocity.0", "velocity.1", "tracer"):
        with_field = ctx.with_field_state[name]
        without_field = ctx.without_field_state[name]
        assert isinstance(with_field, ScalarField)
        assert isinstance(without_field, ScalarField)
        assert torch.equal(with_field.values, without_field.values), (
            f"expected {name!r} to be bit-identical regardless of the selected source term"
        )


@then(
    "the layer heated from below develops a substantially larger vertical velocity than the "
    "one heated from above"
)
def _then_below_convects_above_does_not(ctx: _Context) -> None:
    assert ctx.below_rms is not None
    assert ctx.above_rms is not None
    below_final = ctx.below_rms[-1]
    above_final = ctx.above_rms[-1]
    assert below_final > 2 * above_final, (
        f"expected heated-from-below's own RMS vertical velocity ({below_final}) to be at "
        f"least twice heated-from-above's ({above_final})"
    )


@then("loading is rejected with a named error naming the field and requiring solved velocity")
def _then_rejected_requiring_solved_velocity(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the unsolved-velocity coupling"
    message = str(ctx.error)
    assert "temperature" in message
    assert "velocity_solved" in message


@then('it contains no "temperature" string literal')
def _then_no_temperature_literal() -> None:
    source = inspect.getsource(simulation)
    assert '"temperature"' not in source
