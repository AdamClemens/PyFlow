"""Binds `tests/features/humidity_field.feature` (TASK-037, Stage 6's
fourth task in build order). Not a golden demo -- no config file under
`examples/golden-demos/`, no CLI subprocess run, the same `tests/unit/`
shape `test_density_field.py` (TASK-036) already established for a
Stage 6 task with no golden demo of its own.

**This task's own real subject, per its own Intent, is whether Stage
5's per-field coefficient (`coefficient_overrides`) and boundary-value
(`field_values`/`field_gradients`) mechanisms -- both built and only
ever exercised for velocity's own two components (TASK-031b/c) -- work
for two independently-named, independently-configured scalar fields
sharing one run.** Its first two scenarios go through real configuration
(`load_config`, `bootstrap()`) rather than hand-built `AssembledNumerics`
objects, deliberately: the claim is about the *configuration surface*
generalising, which a hand-constructed scheme would not exercise at all.

Every numeric threshold below was measured against this real
implementation while writing this file, the same discipline
`test_temperature_field.py`'s/`test_density_field.py`'s own module
docstrings record.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.configuration import load_config
from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import AssembledNumerics, assemble_numerics
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import DiffusionScheme
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver
from pyflow.engine.numerics.pressure_coupling import PISO
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import step as simulation_step
from pyflow.engine.vector_field import VectorField

from ._numerics import west_face

scenarios("humidity_field.feature")

# -- Shared physical fixtures --------------------------------------------
#
# Non-square, non-trivially-origined -- `docs/practices.md`'s "distinct
# factors" rule, the same discipline every Stage 4/5/6 fixture in this
# repository follows.

_PERIODIC_CONFIG = (
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
    "    diffusion_coefficient: {temperature_diffusivity}\n"
)

_TEMPERATURE_DIFFUSIVITY = 0.05
_HUMIDITY_DIFFUSIVITY = 0.02
_DOMAIN_WIDTH = 24 * 0.05


def _two_field_config() -> str:
    return _PERIODIC_CONFIG.format(temperature_diffusivity=_TEMPERATURE_DIFFUSIVITY) + (
        "  - name: humidity\n"
        "    initial_condition: sinusoidal_mode\n"
        f"    diffusion_coefficient: {_HUMIDITY_DIFFUSIVITY}\n"
    )


def _rms_amplitude(field: ScalarField) -> float:
    mesh = field.mesh
    total = sum(float(field.value_at(cell)) ** 2 for cell in range(mesh.num_cells))
    return math.sqrt(total / mesh.num_cells)


class _ZeroDiffusion(DiffusionScheme):
    """No diffusive contribution -- isolates pure advection, the
    conservation scenario's own claim, the same double
    `test_density_field.py` already establishes for the identical
    purpose.
    """

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _ZeroSourceTerm(SourceTerm):
    """Contributes exactly zero -- the conservation scenario's own claim
    is about advection alone, with no source term in the picture.
    """

    def source(self, field: Field, state: object) -> torch.Tensor:
        del state
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


# -- Fixture context ------------------------------------------------------


@dataclass
class _Context:
    config_path: Path | None = None
    config_path_without_humidity: Path | None = None
    config_path_with_humidity: Path | None = None
    dt: float | None = None
    early_amplitudes: dict[str, float] | None = None
    late_amplitudes: dict[str, float] | None = None
    assembled_boundary: BoundaryCondition | None = None
    initial_integral: float | None = None
    final_integral: float | None = None
    temperature_without_humidity: torch.Tensor | None = None
    temperature_with_humidity: torch.Tensor | None = None


# -- Given -----------------------------------------------------------------


@given(
    "a periodic domain transporting a temperature field and a humidity field together, each "
    "with its own diffusivity",
    target_fixture="ctx",
)
def _given_two_field_periodic_domain(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(_two_field_config())
    return _Context(config_path=config_path)


@given(
    "a committed configuration declaring field_values for a temperature field and a humidity "
    "field at the same wall",
    target_fixture="ctx",
)
def _given_field_values_config(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "numerics:\n"
        "  boundary_conditions:\n"
        "    west:\n"
        "      type: dirichlet\n"
        "      scalar_value: 0.0\n"
        "      field_values:\n"
        "        temperature: 5.0\n"
        "        humidity: 2.0\n"
        "fields:\n"
        "  - name: temperature\n"
        "  - name: humidity\n"
    )
    return _Context(config_path=config_path)


@given(
    "a periodic domain transporting a humidity field by pure advection alone, with no "
    "diffusion and no source",
    target_fixture="ctx",
)
def _given_pure_advection(tmp_path: Path) -> _Context:
    del tmp_path
    extent = (12, 4)
    spacing = (2.0 / 12, 1.0 / 4)
    mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=spacing, extent=extent)

    def pattern(x: float, y: float) -> float:
        return 1.0 + 0.3 * math.sin(2 * math.pi * x / 2.0)

    humidity = ScalarField(mesh, "humidity", initial_value=pattern)
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.3, 0.1))
    periodic = {"north": "south", "south": "north", "east": "west", "west": "east"}
    advection = FirstOrderUpwindAdvection({}, periodic)
    diffusion = _ZeroDiffusion()
    solver = ConjugateGradientSolver(tolerance=1e-8, max_iterations=1000)
    pressure_coupling = PISO(solver, {}, tolerance=1e-6)
    numerics = AssembledNumerics(
        advection=advection,
        diffusion=diffusion,
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=pressure_coupling,
        source_term=_ZeroSourceTerm(),
        boundary_conditions={},
        names={},
    )

    dx, dy = spacing

    def integral(field: ScalarField) -> float:
        return sum(field.value_at(c) for c in range(mesh.num_cells)) * dx * dy

    ctx = _Context(initial_integral=integral(humidity))
    fields: dict[str, Field] = {"humidity": humidity}
    for _ in range(50):
        fields = simulation_step(fields, velocity, numerics, 0.02)
    final_humidity = fields["humidity"]
    assert isinstance(final_humidity, ScalarField)
    ctx.final_integral = integral(final_humidity)
    return ctx


@given("a configuration transporting a temperature field alone", target_fixture="ctx")
def _given_temperature_alone(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        _PERIODIC_CONFIG.format(temperature_diffusivity=_TEMPERATURE_DIFFUSIVITY)
    )
    return _Context(config_path_without_humidity=config_path)


@given("the same configuration with a humidity field also declared")
def _given_temperature_with_humidity(ctx: _Context) -> None:
    assert ctx.config_path_without_humidity is not None
    config_path = ctx.config_path_without_humidity.parent / "config_with_humidity.yaml"
    config_path.write_text(_two_field_config())
    ctx.config_path_with_humidity = config_path


# -- When ------------------------------------------------------------------


@when("it is run for a few real timesteps and again for many more")
def _when_run_twice(ctx: _Context) -> None:
    assert ctx.config_path is not None
    early_window = bootstrap(ctx.config_path, backend="offscreen", max_frames=1)
    assert early_window.simulation_fields is not None
    late_window = bootstrap(ctx.config_path, backend="offscreen", max_frames=201)
    assert late_window.simulation_fields is not None

    early: dict[str, float] = {}
    late: dict[str, float] = {}
    for name in ("temperature", "humidity"):
        early_field = early_window.simulation_fields[name]
        late_field = late_window.simulation_fields[name]
        assert isinstance(early_field, ScalarField)
        assert isinstance(late_field, ScalarField)
        early[name] = _rms_amplitude(early_field)
        late[name] = _rms_amplitude(late_field)

    ctx.dt = load_config(ctx.config_path).numerics.timestep
    ctx.early_amplitudes = early
    ctx.late_amplitudes = late


@when("numerics are assembled from that configuration", target_fixture="ctx")
def _when_numerics_assembled(ctx: _Context) -> _Context:
    assert ctx.config_path is not None
    config = load_config(ctx.config_path)
    numerics = assemble_numerics(config.numerics)
    ctx.assembled_boundary = numerics.boundary_conditions["west"]
    return ctx


@when("many timesteps are taken")
def _when_many_timesteps_taken() -> None:
    pass


@when("both are run for the same number of real timesteps")
def _when_both_run(ctx: _Context) -> None:
    assert ctx.config_path_without_humidity is not None
    assert ctx.config_path_with_humidity is not None
    without = bootstrap(ctx.config_path_without_humidity, backend="offscreen", max_frames=6)
    with_humidity = bootstrap(ctx.config_path_with_humidity, backend="offscreen", max_frames=6)
    assert without.simulation_fields is not None
    assert with_humidity.simulation_fields is not None
    without_temperature = without.simulation_fields["temperature"]
    with_temperature = with_humidity.simulation_fields["temperature"]
    assert isinstance(without_temperature, ScalarField)
    assert isinstance(with_temperature, ScalarField)
    ctx.temperature_without_humidity = without_temperature.values
    ctx.temperature_with_humidity = with_temperature.values


# -- Then --------------------------------------------------------------


@then(
    "each field's own measured decay rate matches the analytic rate set by its own diffusion "
    "coefficient and wavenumber"
)
def _then_each_decay_rate_matches_analytic(ctx: _Context) -> None:
    assert ctx.early_amplitudes is not None
    assert ctx.late_amplitudes is not None
    assert ctx.dt is not None
    elapsed_time = ctx.dt * 200
    wavenumber = 2 * math.pi / _DOMAIN_WIDTH

    diffusivities = {"temperature": _TEMPERATURE_DIFFUSIVITY, "humidity": _HUMIDITY_DIFFUSIVITY}
    for name, diffusivity in diffusivities.items():
        measured_rate = (
            -math.log(ctx.late_amplitudes[name] / ctx.early_amplitudes[name]) / elapsed_time
        )
        analytic_rate = diffusivity * wavenumber**2
        assert measured_rate == pytest.approx(analytic_rate, rel=0.1), (
            f"{name}: expected decay at roughly {analytic_rate} per unit time, measured "
            f"{measured_rate}"
        )


@then(
    "the resolved boundary condition returns each field's own configured value at that wall, "
    "not the other's or the wall's own default"
)
def _then_each_field_own_boundary_value(ctx: _Context) -> None:
    assert ctx.assembled_boundary is not None
    mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(0.1, 0.1), extent=(4, 4))
    face = west_face(mesh)
    temperature = ScalarField(mesh, "temperature", initial_value=0.0)
    humidity = ScalarField(mesh, "humidity", initial_value=0.0)
    other = ScalarField(mesh, "unconfigured_field", initial_value=0.0)
    assert ctx.assembled_boundary.evaluate(temperature, face) == 5.0
    assert ctx.assembled_boundary.evaluate(humidity, face) == 2.0
    assert ctx.assembled_boundary.evaluate(other, face) == 0.0


@then("the humidity field's own domain integral is unchanged to floating-point precision")
def _then_integral_unchanged(ctx: _Context) -> None:
    assert ctx.initial_integral is not None
    assert ctx.final_integral is not None
    assert ctx.final_integral == pytest.approx(ctx.initial_integral, abs=1e-9), (
        f"expected the domain integral to stay at {ctx.initial_integral}, got {ctx.final_integral}"
    )


@then("the temperature field is identical, element by element, whether or not humidity is present")
def _then_temperature_identical(ctx: _Context) -> None:
    assert ctx.temperature_without_humidity is not None
    assert ctx.temperature_with_humidity is not None
    assert torch.equal(ctx.temperature_without_humidity, ctx.temperature_with_humidity), (
        "expected temperature to be bit-identical with and without a declared humidity field"
    )
