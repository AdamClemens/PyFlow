"""The pure simulation-state construction/advance logic shared by
`bootstrap.py`'s two live-rendering paths and, since TASK-045 (Stage 8,
Recording & Playback), `recording.py`'s headless one.

Extracted from `bootstrap.py`'s `_add_declared_field_transport`/
`_add_solved_velocity_rendering`, which used to build a field's initial
condition, call `navier_stokes_step`/`simulation.step`, and mutate a
`pygfx` scene all inside the same closure -- `recording.py` needs the
first two without the third at all (`RenderWindow.__init__` unconditionally
builds a real `wgpu` renderer, so a genuinely headless recording path
cannot reuse `bootstrap()`/`RenderWindow` even with rendering "turned
off"; see `docs/architecture/sequences.md` Section 3). This module is
what makes that possible without duplicating the stepping logic: it
orchestrates `configuration` + `engine` only, and imports nothing from
`rendering` -- the same "module that composes two or more subpackages
lives at the package root" rule `bootstrap.py` itself follows
(`src/pyflow/CLAUDE.md`), applied to a narrower composition.

**Deliberately does not import `pyflow.rendering.mesh_visualization.
mesh_bounding_box`, even though it computes the identical value for a
`StructuredCartesianMesh`.** That module imports `pygfx` at its own top
level (for `fit_camera_to_bounds`'s own type hint), so importing
anything from it -- even a function with no `pygfx` dependency in its
own body -- would transitively pull `pygfx` into `recording.py`'s own
import chain, defeating the point of a headless path. `_domain_bounds`
below computes the same bounding box directly from `MeshConfig.origin`/
`spacing`/`extent`, which is exact for the one concrete `Mesh` this
project has (`StructuredCartesianMesh`'s own uniform, axis-aligned
vertex grid) and needs no `Mesh` instance or `numpy` at all. A genuine,
acknowledged duplication of what `mesh_bounding_box` computes -- not
its own implementation -- recorded here rather than smoothed over.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

# Side-effect import: `physics.buoyancy` self-registers "boussinesq_
# buoyancy" (`register_source_term`) at its own module scope -- needed
# here for the identical reason `bootstrap.py`'s own top-level import of
# it is needed there (see that module's own docstring): a headless
# `recording.py` run using `source_term: boussinesq_buoyancy` must be
# able to resolve the name too, and this is the only other place that
# calls `assemble_numerics`.
import pyflow.physics.buoyancy  # noqa: F401
from pyflow.configuration.schema import MeshConfig, PyFlowConfig
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh
from pyflow.engine.numerics.assembly import AssembledNumerics, assemble_numerics
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import navier_stokes_step
from pyflow.engine.simulation import step as simulation_step
from pyflow.engine.vector_field import VectorField

_Bounds = tuple[float, float, float, float]

StepMode = Literal["passive", "solved"]


def _domain_bounds(mesh_config: MeshConfig) -> _Bounds:
    """`(min_x, min_y, max_x, max_y)` for a `StructuredCartesianMesh`
    built from `mesh_config` -- see this module's own docstring for why
    this doesn't import `rendering.mesh_visualization.mesh_bounding_box`
    instead, even though the two are exact for this mesh type.
    """
    origin_x, origin_y = mesh_config.origin
    dx, dy = mesh_config.spacing
    nx, ny = mesh_config.extent
    return (origin_x, origin_y, origin_x + dx * nx, origin_y + dy * ny)


def _simulation_scalar_initializer(
    pattern: str, bounds: _Bounds
) -> Callable[[float, float], float]:
    """A `Field`-style `(x, y) -> value` callable for `SimulationConfig.
    scalar_pattern` -- moved from `bootstrap.py` unchanged (TASK-045):
    building a field's initial condition from configuration has no
    rendering dependency, so it belongs wherever the state that
    initial condition seeds gets built, not only where it gets rendered.

    **`"sinusoidal_mode"` (TASK-034, Stage 5) is the Heat Diffusion
    golden demo's own initial condition** -- a single spatial Fourier
    mode, one full wavelength across the mesh's own x-extent
    (`wavenumber = 2*pi / domain_width`, the same "derived from mesh
    bounds" precedent `"gaussian_blob"`'s own `sigma` already sets), with
    no y-dependence. This is the one initial condition PyFlow's diffusion
    equation has a closed-form solution for at all: a single mode decays
    exponentially at a rate `Gamma * wavenumber**2`, set by the diffusion
    coefficient and the mode's own wavenumber alone -- `tests/features/
    heat_diffusion.feature`'s own criterion measures exactly that rate
    against this closed form.
    """
    if pattern == "gaussian_blob":
        min_x, min_y, max_x, max_y = bounds
        domain_width = max_x - min_x
        center_x = min_x + 0.2 * domain_width
        center_y = (min_y + max_y) / 2
        sigma = 0.08 * domain_width
        return lambda x, y: math.exp(-((x - center_x) ** 2 + (y - center_y) ** 2) / (2 * sigma**2))
    if pattern == "sinusoidal_mode":
        min_x, _min_y, max_x, _max_y = bounds
        domain_width = max_x - min_x
        wavenumber = 2 * math.pi / domain_width
        return lambda x, y: math.sin(wavenumber * (x - min_x))
    raise ValueError(f"unknown simulation scalar pattern: {pattern!r}")  # pragma: no cover


def _simulation_velocity_initializer(
    pattern: str | None, velocity: tuple[float, float]
) -> Callable[[float, float], tuple[float, float]]:
    """A `Field`-style `(x, y) -> (vx, vy)` callable for `SimulationConfig.
    velocity_pattern` -- moved from `bootstrap.py` unchanged (TASK-045),
    same reasoning as `_simulation_scalar_initializer` above. `None` (no
    pattern configured) prescribes zero velocity, independent of whether
    a scalar pattern is configured, the same "each of the two names its
    own thing, `None` its own absence" shape `FieldDisplayConfig.
    scalar_pattern`/`vector_pattern` already use.
    """
    if pattern is None:
        return lambda x, y: (0.0, 0.0)
    if pattern == "uniform":
        return lambda x, y: velocity
    raise ValueError(f"unknown simulation velocity pattern: {pattern!r}")  # pragma: no cover


@dataclass
class SimulationState:
    """The state one `record()`/live-render call advances -- `fields` is
    exactly the `dict[str, Field]` `window.simulation_fields` already
    carried before TASK-045 (every entry a single-component `ScalarField`,
    including velocity's own two decomposed components when solved;
    `PressureField` never appears here -- `navier_stokes_step`'s own
    pressure output is a separate return value, never fed back in).

    `mode` decides `advance_simulation_state`'s own dispatch: `"solved"`
    calls `navier_stokes_step` (velocity lives inside `fields` itself,
    corrected every step); `"passive"` calls plain `simulation.step`
    against a separately-tracked, never-updated `velocity_field` (the
    prescribed case -- declared fields self-advect, nothing corrects
    them). `velocity_field` is therefore only ever set for `"passive"`
    mode; `"solved"` mode has nothing else to track between steps, since
    `fields` alone is sufficient to resume from.
    """

    mode: StepMode
    fields: dict[str, Field]
    velocity_field: VectorField | None = None


def build_simulation_state(mesh: Mesh, config: PyFlowConfig) -> SimulationState | None:
    """The initial `SimulationState` for `config`, or `None` if it
    declares nothing that changes frame to frame (`config.fields` empty
    and `config.simulation.velocity_solved` false) -- the exact
    "nothing to run" condition `bootstrap.py`'s own `run_simulation`
    boolean already computed before TASK-045, now a single check any
    caller (live-rendering or headless recording) can share.

    Mirrors `bootstrap.py`'s pre-TASK-045 `_add_declared_field_transport`/
    `_add_solved_velocity_rendering` construction exactly: a declared
    field per `config.fields` entry, plus velocity's own two decomposed
    components joined in when `config.simulation.velocity_solved` --
    `"solved"` mode if declared fields exist (an empty `config.fields`
    plus solved velocity is the velocity-only case, `"solved"` mode with
    no other fields).
    """
    bounds = _domain_bounds(config.mesh)
    velocity_initializer = _simulation_velocity_initializer(
        config.simulation.velocity_pattern, config.simulation.velocity
    )
    velocity_field = VectorField(
        mesh, "velocity", num_components=2, initial_value=velocity_initializer
    )

    declared_fields: dict[str, ScalarField] = {
        declared.name: ScalarField(
            mesh,
            declared.name,
            initial_value=_simulation_scalar_initializer(declared.initial_condition, bounds),
        )
        for declared in config.fields
    }

    solved = config.simulation.velocity_solved
    run_scalar_simulation = bool(config.fields)
    run_velocity_only_simulation = solved and not config.fields
    if not (run_scalar_simulation or run_velocity_only_simulation):
        return None

    if run_scalar_simulation:
        fields: dict[str, Field] = dict(declared_fields)
        if solved:
            for component in velocity_field.decompose():
                fields[component.name] = component
            return SimulationState(mode="solved", fields=fields)
        return SimulationState(mode="passive", fields=fields, velocity_field=velocity_field)

    # Velocity-only, solved (`_add_solved_velocity_rendering`'s own shape).
    fields = {component.name: component for component in velocity_field.decompose()}
    return SimulationState(mode="solved", fields=fields)


def advance_simulation_state(
    state: SimulationState, numerics: AssembledNumerics, dt: float
) -> SimulationState:
    """One timestep, dispatched on `state.mode` -- exactly the
    `if solved: navier_stokes_step(...) else: simulation_step(...)`
    branch `_add_declared_field_transport`'s own `_advance` closure had
    inline before TASK-045, and exactly what `_add_solved_velocity_
    rendering`'s own `_advance` always did (it was always `"solved"`
    mode). Returns a new `SimulationState`; does not mutate `state`.
    """
    if state.mode == "solved":
        fields = navier_stokes_step(state.fields, "velocity", numerics, dt).fields
        return SimulationState(mode="solved", fields=fields)
    assert state.velocity_field is not None
    fields = simulation_step(state.fields, state.velocity_field, numerics, dt)
    return SimulationState(mode="passive", fields=fields, velocity_field=state.velocity_field)


def velocity_field_from_state(state: SimulationState, name: str = "velocity") -> VectorField:
    """Reassembles the `VectorField` named `name` from `state.fields`'
    own decomposed components -- the inverse of how `build_simulation_
    state` put them in. `SimulationState.fields` only ever stores
    decomposed scalar components, never a live `VectorField` object (the
    same shape `window.simulation_fields` already had), so a caller that
    needs one back -- `bootstrap.py`'s own `_add_solved_velocity_
    rendering`, to draw arrows, and TASK-046's eventual playback path,
    for the same reason -- has to reassemble it.
    """
    components = []
    for i in range(2):
        component = state.fields[VectorField.component_name(name, i)]
        assert isinstance(component, ScalarField)
        components.append(component)
    return VectorField.assemble(components, name)


def assembled_numerics_for(config: PyFlowConfig) -> AssembledNumerics:
    """`assemble_numerics` fed from `config` -- the `coefficient_
    overrides`/`buoyancy_couplings` construction moved here unchanged
    from `bootstrap()` (TASK-045), so `recording.py` doesn't duplicate
    it. See `bootstrap.py`'s own inline comments (now here) for why each
    piece is built the way it is.
    """
    coefficient_overrides = {
        declared.name: declared.diffusion_coefficient for declared in config.fields
    }
    if config.simulation.velocity_solved:
        for i in range(2):
            coefficient_overrides[VectorField.component_name("velocity", i)] = (
                config.fluid.viscosity
            )

    buoyancy_couplings: dict[str, tuple[float, float]] = {}
    for declared in config.fields:
        if declared.has_buoyancy_coupling():
            assert declared.buoyancy_reference_value is not None
            assert declared.buoyancy_coefficient is not None
            buoyancy_couplings[declared.name] = (
                declared.buoyancy_reference_value,
                declared.buoyancy_coefficient,
            )

    return assemble_numerics(
        config.numerics,
        config.fluid.diffusion_coefficient,
        coefficient_overrides,
        config.fluid.gravity,
        buoyancy_couplings,
    )
