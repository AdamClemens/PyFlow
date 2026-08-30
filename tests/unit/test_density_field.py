"""Binds `tests/features/density_field.feature` (TASK-036, Stage 6's
third task in build order). Not a golden demo -- density is not one of
Stage 6's three demos, so there is no config file under
`examples/golden-demos/` and no CLI subprocess run. Same `tests/unit/`
shape `test_temperature_field.py` already established: every physical
scenario builds `AssembledNumerics` directly and drives
`navier_stokes_step`/`step` itself.

**This task's own "committed configuration declaring a density field
with its own buoyancy coupling" (`docs/planning/roadmap.md` TASK-036's
own Artifacts Produced) is the YAML content below
(`_TWO_COUPLINGS_CONFIG`), written to a real file via `tmp_path` --
"committed" in the sense every other Stage 6 feature file's own inline
configuration already is: reviewable, stable source, not dynamically
generated per run.** Unlike TASK-035's own two artifacts, this task adds
no golden demo (density is not one of Stage 6's three), so there is no
natural home for a standalone `.yaml` file under `examples/` -- the
roadmap's own bullet for this artifact is, deliberately or not, the only
one in this task's list with no exact path named, unlike every golden
demo bullet elsewhere in this stage.

Every numeric threshold below was measured against this real
implementation while writing this file, the same discipline
`test_temperature_field.py`'s own module docstring records.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.configuration import load_config
from pyflow.configuration.schema import NumericsConfig
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
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion, DiffusionScheme
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver
from pyflow.engine.numerics.pressure_coupling import PISO
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import navier_stokes_step, stable_timestep
from pyflow.engine.simulation import step as simulation_step
from pyflow.engine.vector_field import VectorField
from pyflow.physics.buoyancy import BoussinesqBuoyancy

scenarios("density_field.feature")

# -- Shared physical fixtures (mirrors test_temperature_field.py's own,
# for the closed-domain scenarios) -------------------------------------

_ORIGIN = (0.2, -0.3)
_SPACING = (0.1, 0.15)
_EXTENT = (6, 8)
_VISCOSITY = 0.1
_DENSITY_DIFFUSIVITY = 0.05
_REFERENCE_VALUE = 0.0
_BUOYANCY_COEFFICIENT = 0.003
"""Positive, unlike temperature's own `-0.003` -- `c = +1/rho_0` for a
density field (`docs/planning/roadmap.md` TASK-035's own "The sign,
derived here" section), the physically opposite coupling sign sharing
the identical `f = c * (phi - phi_0) * g` expression.
"""
_DENSE_PATCH_AMPLITUDE = 50.0
_DENSE_PATCH_SIGMA = 0.15
_SINK_STEPS = 5


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
    condition = DirichletBoundaryCondition(0.0, {"density": _REFERENCE_VALUE})
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def _numerics_for(
    gravity: tuple[float, float], couplings: dict[str, tuple[float, float]]
) -> AssembledNumerics:
    bcs = _no_slip_boundary_conditions()
    advection = FirstOrderUpwindAdvection(bcs, {})
    diffusion = CentralDifferenceDiffusion(bcs, {}, _VISCOSITY, {"density": _DENSITY_DIFFUSIVITY})
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


def _dense_patch(mesh: StructuredCartesianMesh) -> ScalarField:
    cx, cy = _domain_center(mesh)

    def pattern(x: float, y: float) -> float:
        return _REFERENCE_VALUE + _DENSE_PATCH_AMPLITUDE * math.exp(
            -((x - cx) ** 2 + (y - cy) ** 2) / (2 * _DENSE_PATCH_SIGMA**2)
        )

    return ScalarField(mesh, "density", initial_value=pattern)


def _initial_velocity_state(mesh: StructuredCartesianMesh) -> dict[str, Field]:
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    return {component.name: component for component in velocity.decompose()}


# -- The "committed configuration" this task's own Artifacts Produced
# bullet names -- see this module's own docstring for why this, and not
# a standalone `.yaml` file under `examples/`.

_TWO_COUPLINGS_CONFIG = (
    "rendering:\n  backend: offscreen\n"
    "simulation:\n  velocity_solved: true\n"
    "fields:\n"
    "  - name: temperature\n"
    "    buoyancy_reference_value: 0.0\n"
    "    buoyancy_coefficient: -0.003\n"
    "  - name: density\n"
    "    buoyancy_reference_value: 1.0\n"
    "    buoyancy_coefficient: 0.5\n"
)


_CAPTURING_SOURCE_TERM_NAME = "test_only_capturing_source_term_for_density_field_test"


class _CapturingSourceTerm(SourceTerm):
    """Records the exact `gravity`/`buoyancy_couplings` it was
    constructed with -- Criterion 4's own substitution check, the same
    `_CapturingSourceTerm` shape `tests/unit/numerics/test_assembly.py`
    already uses for the identical claim at the registry level.
    """

    def __init__(
        self, gravity: tuple[float, float], buoyancy_couplings: Mapping[str, tuple[float, float]]
    ) -> None:
        self.received_gravity = gravity
        self.received_buoyancy_couplings = buoyancy_couplings

    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        del state
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


class _ZeroDiffusion(DiffusionScheme):
    """No diffusive contribution -- isolates pure advection, the
    conservation scenario's own claim.
    """

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _ZeroSourceTerm(SourceTerm):
    """Contributes exactly zero -- the conservation scenario's own claim
    is about advection alone, with no source term in the picture.
    """

    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        del state
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


# -- Fixture context ----------------------------------------------------


@dataclass
class _Context:
    config_path: Path | None = None
    sink_velocity: float | None = None
    captured_source_term: _CapturingSourceTerm | None = None
    initial_integral: float | None = None
    final_integral: float | None = None
    without_density_history: tuple[float, ...] | None = None
    with_density_history: tuple[float, ...] | None = None
    without_density_state: dict[str, Field] | None = None


# -- Given -------------------------------------------------------------


@given(
    "a closed, no-slip domain at rest with a denser patch and downward gravity",
    target_fixture="ctx",
)
def _given_dense_patch(tmp_path: Path) -> _Context:
    del tmp_path
    mesh = _mesh()
    numerics = _numerics_for((0.0, -9.81), {"density": (_REFERENCE_VALUE, _BUOYANCY_COEFFICIENT)})
    state = _initial_velocity_state(mesh)
    state["density"] = _dense_patch(mesh)
    dt = stable_timestep(mesh, _VISCOSITY, velocity_scale=1.0)
    for _ in range(_SINK_STEPS):
        state = navier_stokes_step(state, "velocity", numerics, dt).fields
    cell = _nearest_cell(mesh, _domain_center(mesh))
    v = state["velocity.1"]
    assert isinstance(v, ScalarField)
    return _Context(sink_velocity=v.value_at(cell))


@given(
    "a committed configuration declaring a temperature field and a density field, each with "
    "its own buoyancy coupling",
    target_fixture="ctx",
)
def _given_two_couplings_config(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(_TWO_COUPLINGS_CONFIG)
    return _Context(config_path=config_path)


@given("a SourceTerm test double registered under its own name and selected by configuration")
def _given_capturing_source_term_registered(ctx: _Context) -> None:
    register_source_term(_CAPTURING_SOURCE_TERM_NAME, _CapturingSourceTerm)


@given(
    "a periodic domain transporting a density field by pure advection alone, with no "
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

    density = ScalarField(mesh, "density", initial_value=pattern)
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

    ctx = _Context(initial_integral=integral(density))
    fields: dict[str, Field] = {"density": density}
    for _ in range(50):
        fields = simulation_step(fields, velocity, numerics, 0.02)
    final_density = fields["density"]
    assert isinstance(final_density, ScalarField)
    ctx.final_integral = integral(final_density)
    return ctx


@given(
    "a closed, no-slip domain with a divergent initial velocity field and no density field",
    target_fixture="ctx",
)
def _given_divergent_no_density(tmp_path: Path) -> _Context:
    del tmp_path
    mesh = StructuredCartesianMesh(origin=(0.4, -0.3), spacing=(0.25, 0.2), extent=(4, 3))
    cx, cy = 1.5, -0.9

    def divergent(x: float, y: float) -> tuple[float, float]:
        return (0.6 * (x - cx) - 0.2 * (y - cy), 0.3 * (x - cx) + 0.9 * (y - cy))

    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=divergent)
    state: dict[str, Field] = {component.name: component for component in velocity.decompose()}
    return _Context(without_density_state=state)


def _divergence_numerics(
    couplings: Mapping[str, tuple[float, float]],
) -> tuple[AssembledNumerics, PISO]:
    bcs = _no_slip_boundary_conditions()
    advection = FirstOrderUpwindAdvection(bcs, {})
    diffusion = CentralDifferenceDiffusion(bcs, {}, 1.0, {"density": _DENSITY_DIFFUSIVITY})
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=1000)
    pressure_coupling = PISO(solver, bcs, tolerance=1e-6, max_iterations=200)
    buoyancy = BoussinesqBuoyancy(gravity=(0.0, -9.81), couplings=couplings)
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
    return numerics, pressure_coupling


@given("the same domain carrying a density field with a buoyancy coupling instead")
def _given_same_domain_with_density(ctx: _Context) -> None:
    assert ctx.without_density_state is not None
    mesh = next(iter(ctx.without_density_state.values())).mesh
    numerics_without, piso_without = _divergence_numerics({})
    navier_stokes_step(ctx.without_density_state, "velocity", numerics_without, 0.02)
    ctx.without_density_history = piso_without.last_divergence_history

    state_with: dict[str, Field] = dict(ctx.without_density_state)
    state_with["density"] = ScalarField(mesh, "density", initial_value=5.0)
    numerics_with, piso_with = _divergence_numerics({"density": (0.0, _BUOYANCY_COEFFICIENT)})
    navier_stokes_step(state_with, "velocity", numerics_with, 0.02)
    ctx.with_density_history = piso_with.last_divergence_history


# -- When ------------------------------------------------------------------


@when("several Navier-Stokes timesteps are taken")
def _when_several_timesteps_taken() -> None:
    pass


@when("numerics are assembled from that configuration", target_fixture="ctx")
def _when_numerics_assembled(ctx: _Context) -> _Context:
    assert ctx.config_path is not None
    config = load_config(ctx.config_path)
    numerics_config = NumericsConfig(source_term=_CAPTURING_SOURCE_TERM_NAME)  # type: ignore[arg-type]
    buoyancy_couplings: dict[str, tuple[float, float]] = {}
    for declared in config.fields:
        if declared.has_buoyancy_coupling():
            assert declared.buoyancy_reference_value is not None
            assert declared.buoyancy_coefficient is not None
            buoyancy_couplings[declared.name] = (
                declared.buoyancy_reference_value,
                declared.buoyancy_coefficient,
            )
    assembled = assemble_numerics(
        numerics_config, gravity=config.fluid.gravity, buoyancy_couplings=buoyancy_couplings
    )
    assert isinstance(assembled.source_term, _CapturingSourceTerm)
    ctx.captured_source_term = assembled.source_term
    return ctx


@when("many timesteps are taken")
def _when_many_timesteps_taken() -> None:
    pass


@when("one Navier-Stokes timestep is taken on both")
def _when_one_timestep_taken_on_both() -> None:
    pass


# -- Then --------------------------------------------------------------


@then("the denser patch's own vertical velocity is measurably downward")
def _then_dense_patch_sinks(ctx: _Context) -> None:
    assert ctx.sink_velocity is not None
    assert ctx.sink_velocity < -0.01, (
        f"expected a clearly negative (downward) vertical velocity, got {ctx.sink_velocity}"
    )


@then("the test double was constructed with both couplings, keyed by field name")
def _then_both_couplings_captured(ctx: _Context) -> None:
    assert ctx.captured_source_term is not None
    couplings = ctx.captured_source_term.received_buoyancy_couplings
    assert couplings == {"temperature": (0.0, -0.003), "density": (1.0, 0.5)}, couplings


@then("the density field's own domain integral is unchanged to floating-point precision")
def _then_integral_unchanged(ctx: _Context) -> None:
    assert ctx.initial_integral is not None
    assert ctx.final_integral is not None
    assert ctx.final_integral == pytest.approx(ctx.initial_integral, abs=1e-9), (
        f"expected the domain integral to stay at {ctx.initial_integral}, got {ctx.final_integral}"
    )


@then("both runs converge their own recorded divergence below the configured tolerance")
def _then_both_converge(ctx: _Context) -> None:
    assert ctx.without_density_history is not None
    assert ctx.with_density_history is not None
    tolerance = 1e-6
    assert ctx.without_density_history[-1] <= tolerance, ctx.without_density_history
    assert ctx.with_density_history[-1] <= tolerance, ctx.with_density_history
