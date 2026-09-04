"""Application bootstrap (TASK-010): load configuration, initialise
logging, open the rendering window, run the loop, exit cleanly.

TASK-010's own job was integration only -- prove every
engineering-infrastructure piece (D1-D3) composes into one coherent run,
not simulate anything. **That stopped being the whole of this module in
TASK-030 (Stage 4, 2026-08-28):** `_add_declared_field_transport` wires
a real `simulation.step()` into the render loop, one timestep per
rendered frame, whenever `config.fields` declares at least one field.
**A second live path arrived in TASK-034 (Stage 5, 2026-08-29):**
`_add_solved_velocity_rendering` wires a real, genuinely pressure-
corrected `simulation.navier_stokes_step()` into the render loop instead,
whenever `config.simulation.velocity_solved` is set with no declared
fields -- the Lid-Driven Cavity demo's own shape. Every other
configuration still renders without stepping anything.

**`config.simulation.velocity_solved` now means the same thing on both
live paths** (Stage 5 exit audit, 2026-08-29): with a declared field
alongside it, `_add_declared_field_transport` calls `navier_stokes_step`
too. It did not until then -- it transported velocity's components like
any other scalar and never pressure-corrected them -- so which of the
two behaviours a configuration got was decided by whether a scalar
happened to be configured. See that function's own docstring for the
measured before/after.

**`_add_declared_field_transport` is TASK-042's generalisation of
TASK-030's own `_add_passive_scalar_transport` (Stage 6, 2026-08-30)**:
one hardcoded field named `"tracer"` became one `ScalarField` per
`config.fields` declaration, and which one (if any) gets a live colour
map is `field_display.render_field`, named explicitly rather than
inferred (`src/pyflow/configuration/CLAUDE.md`'s own `FieldConfig`
entry) -- the same rename this docstring's own two paragraphs above
apply throughout. It needed no further change for TASK-035's own
solved-velocity-plus-declared-field combination (Thermal Buoyancy): it
already assembled that combination generically, for TASK-042.

**This module composes a fourth package as of TASK-035 (Stage 6,
2026-08-30): `physics`.** It imports `pyflow.physics.buoyancy` for its
import side effect alone --
`engine/numerics/assembly.py` cannot (`engine` must stay "independent of
any specific physics", `src/pyflow/engine/CLAUDE.md`'s own opening
line), so this is the one place allowed to know about both the registry
and a concrete phenomenon, the same reason this module already composes
`configuration`/`engine`/`rendering`. **The registration itself lives in
`physics/buoyancy.py`, at that module's own import time, not here** --
a first version called `register_source_term("boussinesq_buoyancy", ...)`
from inside this module's own `bootstrap()` function, which made the
name resolvable only after `bootstrap()` had actually run once, unlike
every one of `adr/ADR-003`'s six components (self-registered the moment
`assembly.py` is imported). Fixed the same way those six avoid the
problem: `physics/buoyancy.py` self-registers at its own module scope,
and this module's own existing import of it is what triggers that.

This docstring read "No simulation functionality -- Stage 0's job..."
until the 2026-08-28 Stage 4 exit audit, in a module that by then
imported `simulation_step` twenty lines below -- the same stale
self-description `__main__.py`'s own help text carried, found the same
day but swept only as far as that file (see `src/pyflow/CLAUDE.md`'s
own rule on keeping the CLI's self-description current, which this
module is now covered by too).

Lives at the `pyflow` package root, not inside `engine/`, deliberately:
it composes `configuration`, `engine` (for logging) and `rendering`
together, so it sits above all three in the dependency graph rather than
inside one of them. Putting it in `engine/` first (as TASK-010's own name
suggests) created a real circular import -- `engine` needing `rendering`
while `rendering.window` needs `engine.logging_setup` -- caught by
actually running the import, not just by inspection. See
`docs/CHANGELOG-DESIGN.md`, 2026-08-16 (D4).

This is PyFlow's public Python API for running anything, golden demos
included: a golden demo must be reproducible by a user as "the relevant
command with the relevant configuration," not bespoke code, so this
function -- and the `pyflow run` CLI built on it -- is the only sanctioned
way a demo gets run. See `docs/implementation/golden-demos.md`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import pygfx as gfx

# Side-effect import: `physics.buoyancy` self-registers "boussinesq_
# buoyancy" (`register_source_term`) at its own module scope -- this
# import is what makes that name resolvable to `assemble_numerics`
# below, not a reference to anything this module calls directly. See
# this module's own docstring above for why the registration itself
# does not live here.
import pyflow.physics.buoyancy  # noqa: F401
from pyflow import __version__
from pyflow.configuration import load_config
from pyflow.configuration.schema import (
    FieldDisplayConfig,
    PyFlowConfig,
    RenderBackend,
    UnitsConfig,
)
from pyflow.engine.field import Field
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.assembly import assemble_numerics
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import navier_stokes_step
from pyflow.engine.simulation import step as simulation_step
from pyflow.engine.vector_field import VectorField
from pyflow.rendering import RenderWindow
from pyflow.rendering.field_visualization import (
    build_field_legend,
    build_scalar_field_mesh,
    build_vector_field_arrows,
    scalar_field_colors,
)
from pyflow.rendering.hud import (
    build_axis_labels,
    build_legend_labels,
    build_stats_text,
    build_title_text,
)
from pyflow.rendering.mesh_visualization import (
    build_mesh_grid_line,
    fit_camera_to_bounds,
    mesh_bounding_box,
)

logger = get_logger(__name__)

# Fraction of the mesh's own height reserved for the legend strip drawn
# beneath it, and the gap left between the two. The legend extends past
# the mesh's own bounding box, so the camera must be framed on the
# combined box `_add_field_display` returns, not the mesh's bounds alone
# (`fit_camera_to_bounds`, not TASK-013's mesh-only `fit_camera_to_mesh`).
_LEGEND_HEIGHT_FRACTION = 0.12
_LEGEND_GAP_FRACTION = 0.08
# 0.04 until 2026-09-03, when the Stage 7 (Rendering Annotations) exit
# audit rendered the demos and looked at them. The legend caption
# (`field_label`) is anchored `bottom-center` on the strip's *top* edge
# and grows upward into this gap, and the HUD font is
# `mesh_height * 0.05` -- so at 0.04 the caption was taller than the
# space it had and was drawn *over* the mesh's own bottom row. Visible
# in `thermal_buoyancy` (a colour map with "Temperature (model units)"
# printed across the data) and `field_display` alike, i.e. in every one
# of the nine demos that sets `field_label`. 0.08 leaves 0.03 of mesh
# height clear below the mesh, generous rather than tight, the same
# convention every other margin here follows.
#
# `bootstrap.py`'s own comment at the caption predicted this exactly --
# "tight enough to visually crowd the mesh's own bottom row on a small
# mesh... revisit if a real config using `field_label` shows it in
# practice" -- and every demo has set `field_label` since 2026-08-31.
# The condition had fired; nothing was watching it
# (`docs/practices.md`, "A checkable trigger still needs somebody to
# check it"). Nothing but a rendered frame could have caught it: the
# text was inside the camera's bounds, so the pixel-band scenarios pass
# either way, and every object-presence assertion passes too.

# HUD layout fractions (Stage 7, Rendering Annotations) -- fixed guesses
# in the same spirit as `_LEGEND_HEIGHT_FRACTION` above, not a measured
# text height (pygfx gives no cheap way to measure a `Text` object's
# rendered extent before adding it to a scene). Generous rather than
# tight, since the world-space HUD text grows/shrinks with zoom and a
# too-tight margin would clip at typical zoom levels sooner than a too-
# generous one wastes empty space.
_TITLE_MARGIN_FRACTION = 0.12
_LEGEND_LABEL_MARGIN_FRACTION = 0.10
_STATS_MARGIN_FRACTION = 0.20
_AXIS_LABEL_GAP_FRACTION = 0.02
_X_AXIS_LABEL_MARGIN_FRACTION = 0.08
_Y_AXIS_LABEL_MARGIN_FRACTION = 0.12

# Z-offsets so overlapping same-plane content composites predictably
# (arrows/legend drawn over field fills) rather than depending on draw
# order at equal depth, which this renderer's tie-breaking behaviour was
# never verified for.
_ARROWS_Z = 0.01
_LEGEND_Z = 0.02
_HUD_Z = 0.03

_Bounds = tuple[float, float, float, float]


def _scalar_display_initializer(
    pattern: str, center: tuple[float, float]
) -> Callable[[float, float], float]:
    """A `Field`-style `(x, y) -> value` callable for `pattern`."""
    cx, cy = center
    if pattern == "radial_gradient":
        return lambda x, y: math.hypot(x - cx, y - cy)
    raise ValueError(f"unknown scalar display pattern: {pattern!r}")  # pragma: no cover


def _vector_display_initializer(
    pattern: str, center: tuple[float, float]
) -> Callable[[float, float], tuple[float, float]]:
    """A `Field`-style `(x, y) -> (vx, vy)` callable for `pattern`."""
    cx, cy = center
    if pattern == "rotational":
        return lambda x, y: (-(y - cy), x - cx)
    raise ValueError(f"unknown vector display pattern: {pattern!r}")  # pragma: no cover


def _simulation_scalar_initializer(
    pattern: str, bounds: _Bounds
) -> Callable[[float, float], float]:
    """A `Field`-style `(x, y) -> value` callable for `SimulationConfig.
    scalar_pattern` (TASK-030) -- the live-simulation counterpart to
    `_scalar_display_initializer` above, sharing its "derive shape from
    mesh bounds, don't add a config field for it" reasoning.

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
    velocity_pattern` -- `None` (no pattern configured) prescribes zero
    velocity, independent of whether a scalar pattern is configured, the
    same "each of the two names its own thing, `None` its own absence"
    shape `FieldDisplayConfig.scalar_pattern`/`vector_pattern` already use.
    """
    if pattern is None:
        return lambda x, y: (0.0, 0.0)
    if pattern == "uniform":
        return lambda x, y: velocity
    raise ValueError(f"unknown simulation velocity pattern: {pattern!r}")  # pragma: no cover


def _add_legend(
    window: RenderWindow, field_display: FieldDisplayConfig, mesh_bounds: _Bounds
) -> _Bounds | None:
    """The colour-ramp legend strip, below `mesh_bounds` -- shared by
    every path that colour-maps a scalar field, static
    (`_add_field_display`) or live (`_add_declared_field_transport`).
    Returns the strip's own bounds (for `_add_hud`'s numeric labels), or
    `None` if `field_display.show_legend` is false.

    Factored out (Stage 7, Rendering Annotations) from what used to be
    `_add_field_display`'s own inline block: the live-stepping path drew
    a colour-mapped field with no legend at all before this, which is
    exactly the gap this stage exists to close -- watching a live run is
    the case a legend matters most for, not only a static demo frame.
    """
    if not field_display.show_legend:
        return None
    min_x, min_y, max_x, max_y = mesh_bounds
    mesh_height = max_y - min_y
    legend_height = mesh_height * _LEGEND_HEIGHT_FRACTION
    gap = mesh_height * _LEGEND_GAP_FRACTION
    legend_bottom = min_y - gap - legend_height
    legend_bounds = (min_x, legend_bottom, max_x, min_y - gap)
    legend = build_field_legend(
        field_display.low_color,
        field_display.high_color,
        field_display.value_range,
        legend_bounds,
    )
    legend.local.position = (0.0, 0.0, _LEGEND_Z)
    window.scene.add(legend)
    return legend_bounds


def _add_declared_field_transport(
    window: RenderWindow, mesh: Mesh, config: PyFlowConfig
) -> tuple[Callable[[], None], _Bounds | None]:
    """Wires a real `simulation.step()` into a live `pyflow run`
    (Stage 4 Completion Criterion 1, TASK-030) -- the mechanism the
    Passive Scalar Transport golden demo needs and no demo before it
    does. Builds one `ScalarField` per `config.fields` declaration and a
    prescribed velocity field from `config.simulation`, renders the
    first frame, and returns an `on_frame` closure that advances every
    declared field by one `config.numerics.timestep` and re-renders
    after every frame thereafter.

    **Generalised from one hardcoded field named `"tracer"` to
    `config.fields`' own declarations (TASK-042, Stage 6, 2026-08-30).**
    Every declared field is transported together, in the same `step`/
    `navier_stokes_step` call -- Criterion 1's own claim that a
    transported field is added by configuration, not by code. Which one
    (if any) gets a live colour map is `config.field_display.
    render_field`, named explicitly rather than inferred
    (`src/pyflow/configuration/CLAUDE.md`'s own `FieldConfig` entry) --
    `None` renders nothing for the live simulation, the same "no display
    configured, nothing drawn" shape `_add_field_display` already uses
    for the static case.

    Rebuilds the rendered `gfx.Mesh` from scratch each frame (removes the
    old one from `window.scene`, `build_scalar_field_mesh`s a new one)
    rather than mutating the geometry's own colour buffer in place --
    `build_scalar_field_mesh`/`scalar_field_colors` are already proven
    correct (TASK-017); an in-place buffer mutation would be new,
    unverified pygfx-API surface for a small win on a small demo mesh
    (TASK-030's own Design decision).

    **`config.simulation.velocity_solved` (TASK-031, added 2026-08-29)**:
    when true, velocity's own two components join `state` (decomposed via
    `VectorField.decompose`) alongside every declared field, and the
    whole state is advanced by `navier_stokes_step` rather than plain
    `step` -- so the velocity carrying them is genuinely pressure-
    corrected, frame by frame, and the *next* frame transports against a
    corrected velocity rather than the initial one. `simulation.py`
    needs no change for this (Stage 5 Completion Criterion 1's own
    structural clause): decompose-before/reassemble-after lives entirely
    here.

    **This path used plain `step` until the Stage 5 exit audit
    (2026-08-29), and that was a real defect, not a scoping choice.**
    TASK-031 built it before any corrector loop existed to call, and
    TASK-034 -- which built one, and used it in
    `_add_solved_velocity_rendering` -- left this path alone and recorded
    the gap in two `CLAUDE.md` files. The result was a configuration
    field named `velocity_solved` that solved on one live path and merely
    self-advected on the other, chosen by whether a scalar field happened
    to be configured, with no error and nothing rendered differently: a
    plausible-looking wrong answer reachable from configuration alone.
    Measured before and after, on the fixture
    `tests/unit/test_bootstrap.py` now uses: maximum divergence sat at
    9.16 -> 8.24 -> 6.95 over 1, 10 and 40 frames uncorrected, and falls
    2.30 -> 0.47 -> 0.057 corrected.

    **Velocity's own initial condition still comes from
    `velocity_pattern`/`velocity` either way** -- "solved" decides what
    happens to it after frame zero, not what it starts as
    (`src/pyflow/configuration/CLAUDE.md`).
    """
    assert window.assembled_numerics is not None
    numerics = window.assembled_numerics
    assert config.fields

    bounds = mesh_bounding_box(mesh)
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
    state: dict[str, Field] = dict(declared_fields)
    if solved:
        for component in velocity_field.decompose():
            state[component.name] = component
    window.simulation_fields = state

    render_field_name = config.field_display.render_field
    rendered_object: gfx.Mesh | None = None
    legend_bounds: _Bounds | None = None
    if render_field_name is not None:
        colors = scalar_field_colors(
            declared_fields[render_field_name],
            config.field_display.low_color,
            config.field_display.high_color,
            config.field_display.value_range,
        )
        rendered_object = build_scalar_field_mesh(declared_fields[render_field_name], colors)
        window.scene.add(rendered_object)
        legend_bounds = _add_legend(window, config.field_display, bounds)

    def _advance() -> None:
        nonlocal state, rendered_object
        if solved:
            # `velocity_field` is read only to seed `state` above -- from
            # here on, velocity lives in `state` as its own two
            # components and `navier_stokes_step` reassembles and
            # corrects them itself, so there is nothing left to keep in
            # sync. The prescribed branch below is the opposite case: its
            # velocity never changes at all.
            state = navier_stokes_step(state, "velocity", numerics, config.numerics.timestep).fields
        else:
            state = simulation_step(state, velocity_field, numerics, config.numerics.timestep)
        window.simulation_fields = state
        if render_field_name is not None:
            rendered_field = state[render_field_name]
            assert isinstance(rendered_field, ScalarField)
            colors = scalar_field_colors(
                rendered_field,
                config.field_display.low_color,
                config.field_display.high_color,
                config.field_display.value_range,
            )
            assert rendered_object is not None
            window.scene.remove(rendered_object)
            rendered_object = build_scalar_field_mesh(rendered_field, colors)
            window.scene.add(rendered_object)
            # Note for anyone inspecting `window.scene.children` order
            # (found while fixing `tests/unit/
            # test_field_declaration_configuration.py` for Stage 7's own
            # legend addition): after this remove-then-add, the field mesh
            # sits *after* the legend added once, above, in scene-child
            # order -- not before it, as a first render's own insertion
            # order would suggest. Identify the field mesh by its own
            # geometry shape (`mesh.num_cells * 2` colour rows), not by
            # scene position, if a future reader needs to find it again.

    return _advance, legend_bounds


def _add_solved_velocity_rendering(
    window: RenderWindow, mesh: Mesh, config: PyFlowConfig
) -> tuple[Callable[[], None], _Bounds | None, Callable[[], bool]]:
    """Wires a real `simulation.navier_stokes_step()` into a live `pyflow
    run` (TASK-034, Stage 5) -- the mechanism the Lid-Driven Cavity
    golden demo needs and no demo before it does: a *solved* velocity
    field, rendered live, with no scalar alongside it at all.

    `_add_declared_field_transport`'s own docstring named this gap in
    advance (TASK-031, 2026-08-29, as `_add_passive_scalar_transport`
    before its TASK-042 rename): "a velocity-only live run has
    nothing this function knows how to render yet (no vector-arrow-per-
    frame path exists)... revisit when a demo genuinely needs
    velocity-only live rendering (TASK-034's own Lid-Driven Cavity is the
    likely first)". This is that revisit -- `build_vector_field_arrows`
    (TASK-017) already existed for a *static* vector display; this
    function is what rebuilds it every frame, the same "remove the old
    `gfx.Line`, build a new one" shape `_add_declared_field_transport`
    already uses for its own scalar mesh.

    **Uses `navier_stokes_step`, not plain `step`**, so a demo using this
    function is genuinely incompressible frame by frame, not merely
    self-advected.

    This paragraph used to go on to name that as "the real difference
    from `_add_passive_scalar_transport`'s own `velocity_solved` path,
    which only ever transports velocity's components like an ordinary
    scalar and never pressure-corrects them (a genuine, pre-existing gap
    in that path, out of this task's own scope to close)". **The Stage 5
    exit audit closed that gap on 2026-08-29** rather than leaving a
    configuration field that solved on one path and did not on the other:
    both live paths now call `navier_stokes_step`, and the only real
    difference between these two functions is what they render -- arrows
    for a velocity alone here, a colour map for the scalar there.
    """
    assert window.assembled_numerics is not None
    numerics = window.assembled_numerics

    velocity_initializer = _simulation_velocity_initializer(
        config.simulation.velocity_pattern, config.simulation.velocity
    )
    velocity_field = VectorField(
        mesh, "velocity", num_components=2, initial_value=velocity_initializer
    )
    state: dict[str, Field] = {c.name: c for c in velocity_field.decompose()}
    window.simulation_fields = state

    rendered_object = build_vector_field_arrows(
        velocity_field, config.field_display.arrow_color, config.field_display.arrow_scale
    )
    if rendered_object is not None:
        rendered_object.local.position = (0.0, 0.0, _ARROWS_Z)
        window.scene.add(rendered_object)

    def _advance() -> None:
        nonlocal state, rendered_object, velocity_field
        result = navier_stokes_step(state, "velocity", numerics, config.numerics.timestep)
        state = result.fields
        window.simulation_fields = state
        velocity_field = result.corrected_velocity
        if rendered_object is not None:
            window.scene.remove(rendered_object)
        rendered_object = build_vector_field_arrows(
            velocity_field, config.field_display.arrow_color, config.field_display.arrow_scale
        )
        if rendered_object is not None:
            rendered_object.local.position = (0.0, 0.0, _ARROWS_Z)
            window.scene.add(rendered_object)

    def _arrows_drawn() -> bool:
        """Queried per frame, not captured once (Stage 7 exit audit,
        2026-09-03). A solved velocity starting from rest --
        `lid_driven_cavity.yaml`'s own initial condition -- is exactly
        zero everywhere on the first frame, so `build_vector_field_
        arrows` draws nothing and there is no length-per-magnitude
        conversion for `_add_hud`'s vector-scale line to state. Arrows
        appear as soon as the lid drives the flow, and the line must
        appear with them: a boolean captured at build time would be
        wrong in one direction or the other for the whole run.
        """
        return rendered_object is not None

    # `None` legend bounds -- this path renders velocity as arrows,
    # never a colour-mapped scalar, so there is no legend to report
    # (Stage 7's `_add_legend`, shared with the two paths that do
    # colour-map one).
    return _advance, None, _arrows_drawn


def _add_field_display(
    window: RenderWindow, mesh: Mesh, field_display: FieldDisplayConfig
) -> tuple[_Bounds, _Bounds | None, bool]:
    """Build and add whatever `field_display` asks for -- the scalar
    colour map, its legend, and the vector arrows -- entirely from
    configuration, per the golden-demo public-API rule. Does nothing for
    whichever of scalar/vector isn't configured (`None`, the default for
    both).

    Returns the bounding box the caller should frame the camera on (the
    mesh's own bounds, extended downward to include the legend strip if
    one was drawn); the legend strip's own bounds (for `_add_hud`'s
    numeric labels) -- `None` if no legend was drawn; and whether any
    arrow was actually added to the scene.

    **That third value is what it is because `vector_pattern is not
    None` is not the same question** (Stage 7 exit audit, 2026-09-03):
    `build_vector_field_arrows` returns `None` for a field whose every
    cell vector is exactly zero, so a configured `vector_pattern` can
    legitimately draw nothing -- and `_add_hud`'s vector-scale line must
    describe the arrows on screen, not the ones the configuration asked
    for.
    """
    bounds = mesh_bounding_box(mesh)
    min_x, min_y, max_x, max_y = bounds
    center = ((min_x + max_x) / 2, (min_y + max_y) / 2)
    legend_bounds: _Bounds | None = None
    arrows_drawn = False

    if field_display.scalar_pattern is not None:
        scalar_initializer = _scalar_display_initializer(field_display.scalar_pattern, center)
        scalar_field = ScalarField(mesh, "scalar_display", initial_value=scalar_initializer)
        colors = scalar_field_colors(
            scalar_field,
            field_display.low_color,
            field_display.high_color,
            field_display.value_range,
        )
        window.scene.add(build_scalar_field_mesh(scalar_field, colors))

        legend_bounds = _add_legend(window, field_display, bounds)
        if legend_bounds is not None:
            bounds = (min_x, legend_bounds[1], max_x, max_y)

    if field_display.vector_pattern is not None:
        vector_initializer = _vector_display_initializer(field_display.vector_pattern, center)
        vector_field = VectorField(
            mesh, "vector_display", num_components=2, initial_value=vector_initializer
        )
        arrows = build_vector_field_arrows(
            vector_field, field_display.arrow_color, field_display.arrow_scale
        )
        if arrows is not None:
            arrows.local.position = (0.0, 0.0, _ARROWS_Z)
            window.scene.add(arrows)
            arrows_drawn = True

    return bounds, legend_bounds, arrows_drawn


def _format_length(value: float, units: UnitsConfig) -> str:
    """A single number, always labelled with `units.length_unit` --
    deliberately not a dual "raw (converted)" display. At the default
    scale (`1.0`) and unit (`"m"`), this shows the bare simulation
    number labelled `m`; a configured `length_scale`/`length_unit`
    changes what is shown, not whether something is shown, which avoids
    the "when do I show the parenthetical" question a dual display would
    raise entirely.
    """
    return f"{value * units.length_scale:.4g} {units.length_unit}"


def _format_time(value: float, units: UnitsConfig) -> str:
    """`_format_length`'s exact time counterpart."""
    return f"{value * units.time_scale:.4g} {units.time_unit}"


def _stats_lines(
    mesh_bounds: _Bounds,
    config: PyFlowConfig,
    frame_count: int | None,
    show_vector_scale: bool,
) -> list[str]:
    """Cell size and domain size always; a leading "step N  t = ..." line
    only when `frame_count` is given -- a static (non-live-stepping) run
    has no timestep concept to report. A trailing vector-scale line
    (Stage 7, added after real user feedback that arrows alone give no
    way to read magnitude: "neither the direction nor magnitude is
    clear") only when `show_vector_scale` is true *and*
    `field_display.vector_label` is set -- arrows being drawn is not, on
    its own, reason enough to claim a label the config never gave them.
    **The converse holds too, and did not until the Stage 7 exit audit
    (2026-09-03):** `show_vector_scale` reports whether an arrow is
    actually on screen, not whether one was configured, so a configured
    `vector_label` no longer states a length-per-magnitude conversion
    over a frame with no arrow in it to read it against.

    `frame_count`, when given, is `window.frame_count` at the moment
    `bootstrap()`'s composed `on_frame` calls this (after the
    simulation-advance closure has already run for this frame): `_draw()`
    increments `frame_count` *before* firing `on_frame`, so by the time
    this runs, the state that will be shown starting the *next* rendered
    frame has been advanced exactly `frame_count` times in total --
    `elapsed = frame_count * timestep` describes that state, which is
    what makes the label agree with what is actually on screen once the
    mutated text becomes visible next frame. Traced through `RenderWindow
    ._draw`'s own increment-then-callback order (`rendering/window.py`),
    not assumed.
    """
    dx, dy = config.mesh.spacing
    min_x, min_y, max_x, max_y = mesh_bounds
    lines = [
        f"cell: {_format_length(dx, config.units)} x {_format_length(dy, config.units)}",
        f"domain: {_format_length(max_x - min_x, config.units)} x "
        f"{_format_length(max_y - min_y, config.units)}",
    ]
    if frame_count is not None:
        elapsed = frame_count * config.numerics.timestep
        lines.insert(0, f"step {frame_count}  t = {_format_time(elapsed, config.units)}")
    if show_vector_scale and config.field_display.vector_label is not None:
        lines.append(
            f"{config.field_display.vector_label}: length = "
            f"{config.field_display.arrow_scale:.4g} x magnitude"
        )
    return lines


def _arrows_drawn_constantly(drawn: bool) -> Callable[[], bool]:
    """`_add_hud`'s `show_vector_scale` for a path whose answer cannot
    change during the run: a static `vector_pattern` either drew arrows
    when the scene was built or it never will, and a run drawing no
    arrows at all stays that way. Only the live velocity path
    (`_add_solved_velocity_rendering`) needs a genuine per-frame query,
    and it supplies its own.
    """
    return lambda: drawn


def _either_path_drew_arrows(
    first: Callable[[], bool], second: Callable[[], bool]
) -> Callable[[], bool]:
    """`show_vector_scale` for a run where both arrow-drawing paths are
    active -- a static `vector_pattern` *and* a velocity-only solved run,
    which are independent switches a configuration may set together.

    **Joined, not replaced** (2026-09-03, found by re-auditing the Stage
    7 exit audit's own first fix for the vector-scale line). That fix had
    the live path's per-frame query overwrite the static path's answer,
    so a configuration setting both went silent whenever the solved
    velocity was at rest -- while the static pattern's arrows sat plainly
    on screen. The line describes arrows a viewer can see; either path
    having drawn one is enough. Still evaluated per frame, since the
    live path's own answer changes as the flow develops.
    """
    return lambda: first() or second()


def _add_hud(
    window: RenderWindow,
    mesh_bounds: _Bounds,
    bounds: _Bounds,
    legend_bounds: _Bounds | None,
    config: PyFlowConfig,
    live_stepping: bool,
    show_vector_scale: Callable[[], bool],
) -> tuple[_Bounds, Callable[[], None] | None]:
    """The title, legend numeric labels, and timestep/cell/domain-size
    stats block -- entirely from `config.rendering`/`config.field_display`
    /`config.units`, per the golden-demo public-API rule every other
    piece of this module follows.

    World-space, camera-following (the maintainer's own choice for this
    iteration, over a fixed screen-space overlay -- `rendering/hud.py`'s
    own module docstring has the fuller reasoning): every element is
    placed relative to `mesh_bounds`/`legend_bounds` and `bounds` is
    extended to include it, the same pattern `_add_field_display` already
    uses for the legend strip itself. Layout is fixed-fraction margins,
    not measured text extents (pygfx gives no cheap way to measure a
    `Text` object before adding it to a scene) -- generous rather than
    tight, since a too-tight margin clips sooner at typical zoom levels
    than a too-generous one wastes space.

    Returns the further-extended bounds and, only when `live_stepping`
    and `show_stats` are both true, an update closure the caller composes
    into `on_frame` -- a static run's stats never change, so there is
    nothing to re-set frame to frame.

    **`show_vector_scale` is a callable, not a bool** (Stage 7 exit
    audit, 2026-09-03): whether an arrow is on screen is a per-frame
    fact on the live velocity path, where a velocity starting from rest
    draws none until the flow develops. The static path passes a
    constant.
    """
    rendering = config.rendering
    min_x, min_y, max_x, max_y = bounds
    mesh_min_x, mesh_min_y, mesh_max_x, mesh_max_y = mesh_bounds
    mesh_height = mesh_max_y - mesh_min_y
    mesh_width = mesh_max_x - mesh_min_x
    mesh_center_x = (mesh_min_x + mesh_max_x) / 2
    mesh_center_y = (mesh_min_y + mesh_max_y) / 2
    font_size = mesh_height * 0.05

    if rendering.show_title:
        title = build_title_text(
            rendering.title,
            (mesh_center_x, mesh_max_y + mesh_height * 0.02),
            font_size=font_size,
            max_width=mesh_width,
        )
        title.local.position = (title.local.position[0], title.local.position[1], _HUD_Z)
        window.scene.add(title)
        max_y = max(max_y, mesh_max_y + mesh_height * _TITLE_MARGIN_FRACTION)

    # Standing rule (Stage 7, Rendering Annotations, added after real user
    # feedback: "the spatial axes should be labelled... make that a
    # standing rule for rendering that all graphs and axes must be
    # labelled"): every mesh view labels its own physical extent, not
    # only a domain-size number once in the stats block below. Reuses
    # `show_stats` as the gate rather than a new toggle -- both describe
    # the mesh's own geometry, and this keeps the same opt-out mechanism
    # (`empty_window.yaml`'s own `show_stats: false`) rather than adding
    # a second one. Min/mid/max ticks per axis; placed above whatever the
    # top of the framed view already is (mesh or title) and left of the
    # mesh -- new bounds directions neither the legend nor the stats
    # block ever needed to extend.
    if rendering.show_stats:
        x_ticks = [
            (x, _format_length(x, config.units)) for x in (mesh_min_x, mesh_center_x, mesh_max_x)
        ]
        y_ticks = [
            (y, _format_length(y, config.units)) for y in (mesh_min_y, mesh_center_y, mesh_max_y)
        ]
        axis_y = max_y + mesh_height * _AXIS_LABEL_GAP_FRACTION
        axis_x = mesh_min_x - mesh_width * _AXIS_LABEL_GAP_FRACTION
        axis_labels = build_axis_labels(
            x_ticks, y_ticks, axis_y, axis_x, font_size=font_size, max_width=mesh_width
        )
        for label in axis_labels:
            label.local.position = (label.local.position[0], label.local.position[1], _HUD_Z)
            window.scene.add(label)
        max_y = axis_y + mesh_height * _X_AXIS_LABEL_MARGIN_FRACTION
        min_x = min(min_x, axis_x - mesh_width * _Y_AXIS_LABEL_MARGIN_FRACTION)

    if legend_bounds is not None and config.field_display.show_legend:
        # `field_label`, if any, is placed just above `legend_bounds`
        # (inside the mesh-to-legend gap, `_LEGEND_GAP_FRACTION`) -- not
        # clipped by the camera framing below, since that gap is already
        # within `bounds`. **That gap is sized for this text**: it was
        # 0.04 against a 0.05 font until 2026-09-03, which drew the
        # caption over the mesh's own bottom row in every demo setting
        # `field_label`. See `_LEGEND_GAP_FRACTION`'s own comment for
        # what that cost and how it was found.
        field_label = config.field_display.field_label or config.field_display.render_field
        low_value, high_value = config.field_display.value_range
        labels = build_legend_labels(
            f"{low_value:.4g}",
            f"{high_value:.4g}",
            field_label,
            legend_bounds,
            font_size=font_size,
            max_width=mesh_width,
        )
        for label in labels:
            label.local.position = (label.local.position[0], label.local.position[1], _HUD_Z)
            window.scene.add(label)
        min_y = min(min_y, legend_bounds[1] - mesh_height * _LEGEND_LABEL_MARGIN_FRACTION)

    stats_object: gfx.Text | None = None
    if rendering.show_stats:
        frame_count = window.frame_count if live_stepping else None
        stats_object = build_stats_text(
            _stats_lines(mesh_bounds, config, frame_count, show_vector_scale()),
            (mesh_min_x, min_y - mesh_height * 0.02),
            font_size=font_size,
            max_width=mesh_width,
        )
        stats_object.local.position = (
            stats_object.local.position[0],
            stats_object.local.position[1],
            _HUD_Z,
        )
        window.scene.add(stats_object)
        min_y -= mesh_height * _STATS_MARGIN_FRACTION

    new_bounds = (min(min_x, mesh_min_x), min_y, max(max_x, mesh_max_x), max_y)

    if not (live_stepping and rendering.show_stats):
        return new_bounds, None

    assert stats_object is not None

    def _update_stats() -> None:
        stats_object.set_text(
            "\n".join(_stats_lines(mesh_bounds, config, window.frame_count, show_vector_scale()))
        )

    return new_bounds, _update_stats


def bootstrap(
    config_path: str | Path | None = None,
    *,
    max_frames: int | None = None,
    backend: RenderBackend | None = None,
) -> RenderWindow:
    """Load configuration, initialise logging, open the render window, run.

    `max_frames` bounds the run for automated contexts (CI, the
    golden-demo regression test, backlog D5) that have no user to close a
    window. Left as `None` for a real interactive run, which blocks until
    the window is closed -- what `make demo` gives a developer.

    `backend`, if given, overrides whatever `config_path` specifies for
    `rendering.backend`. Exists so the same config file a user runs
    interactively can also be run headlessly for automated verification
    (`--backend offscreen`) without needing a second, duplicate config
    file just to change one field.

    Returns the `RenderWindow` so callers -- notably golden-demo
    regression tests -- can inspect what was actually rendered
    (`window.last_image`) rather than only that nothing raised, and
    (TASK-021) what got assembled from `config.numerics`
    (`window.assembled_numerics`).
    """
    config = load_config(config_path)
    if backend is not None:
        config.rendering.backend = backend
        config.rendering.validate()
    configure_logging(config.logging)

    logger.info("pyflow %s bootstrapping", __version__)
    window = RenderWindow(config.rendering)

    # TASK-021: assemble every numerics component from `config.numerics`
    # and report the result -- Stage 3 Completion Criterion 8. Every run
    # does this, not only ones that need numerics for anything yet, since
    # `NumericsConfig` always has a full section (defaulted or not) and
    # assembly must not depend on whether a caller happens to care.
    # `config.fluid.diffusion_coefficient` (TASK-041, 2026-08-28) is
    # threaded in explicitly -- it moved out of `NumericsConfig` into its
    # own `fluid:` section, so `assemble_numerics` can no longer read it
    # off `config.numerics` alone. `coefficient_overrides` is now built
    # from `config.fields`' own declarations (TASK-042, Stage 6,
    # 2026-08-30) rather than only from `velocity_solved`: every declared
    # field contributes its own `diffusion_coefficient`, keyed by the
    # field's own `name` -- the mechanism (`CentralDifferenceDiffusion`'s
    # own per-field override map, TASK-031b) is unchanged, only its
    # source is new. When velocity is solved, its own two components
    # (`VectorField.component_name`) are *additionally* diffused with
    # `fluid.viscosity` instead of the scalar default -- this is the one
    # place in the engine that legitimately knows a run's velocity field
    # is conventionally named "velocity", so it is where that mapping is
    # built, not inside `assemble_numerics`/`CentralDifferenceDiffusion`
    # themselves (both stay field-name-agnostic).
    coefficient_overrides = {
        declared.name: declared.diffusion_coefficient for declared in config.fields
    }
    if config.simulation.velocity_solved:
        for i in range(2):
            coefficient_overrides[VectorField.component_name("velocity", i)] = (
                config.fluid.viscosity
            )

    # `buoyancy_couplings` (TASK-035, Stage 6, 2026-08-30) is
    # `source_term`'s own per-field mapping, the identical
    # "assemble_numerics stays field-name-agnostic, bootstrap.py builds
    # the map" split `coefficient_overrides` above already establishes.
    # `"boussinesq_buoyancy"` is already registered by the time this runs
    # -- `physics/buoyancy.py` self-registers at its own import time
    # (this module's own top-level `import pyflow.physics.buoyancy`
    # triggers it), not here, so that the name resolves even if
    # `assemble_numerics` is ever called without `bootstrap()` having
    # run first (this module's own docstring has the full history).
    buoyancy_couplings: dict[str, tuple[float, float]] = {}
    for declared in config.fields:
        if declared.has_buoyancy_coupling():
            assert declared.buoyancy_reference_value is not None
            assert declared.buoyancy_coefficient is not None
            buoyancy_couplings[declared.name] = (
                declared.buoyancy_reference_value,
                declared.buoyancy_coefficient,
            )
    window.assembled_numerics = assemble_numerics(
        config.numerics,
        config.fluid.diffusion_coefficient,
        coefficient_overrides,
        config.fluid.gravity,
        buoyancy_couplings,
    )
    logger.info("numerics assembled: %s", window.assembled_numerics.names)
    if config.fields:
        # The same reporting shape the line above uses, for the other
        # thing a run is assembled from. Added 2026-09-04 with the
        # Multi-Field Plume demo, whose whole demonstration is that four
        # differently-named fields ride one engine: a rendered frame
        # colour-maps exactly one of them, so without this the demo
        # looks like Thermal Buoyancy and exit-code-zero covers nothing
        # it claims (`tests/golden/CLAUDE.md`, "a demo whose output is
        # its point needs a second scenario"). Read back through the
        # real CLI by `tests/features/multi_field_plume.feature`, so
        # deleting this line fails a test rather than quietly removing
        # a demonstration -- which is the defect the Stage 3 exit audit
        # found in the numerics report above.
        logger.info(
            "transporting declared fields: %s",
            ", ".join(declared.name for declared in config.fields),
        )

    show_fields = (
        config.field_display.scalar_pattern is not None
        or config.field_display.vector_pattern is not None
    )
    run_scalar_simulation = bool(config.fields)
    # TASK-034 (Stage 5): a velocity-only live run -- solved, rendered as
    # arrows, no declared field alongside it
    # (`_add_solved_velocity_rendering`'s own docstring). Mutually
    # exclusive with `run_scalar_simulation`, the same "one live-
    # simulation path per run" shape TASK-030 already established --
    # `_add_declared_field_transport`'s own `velocity_solved` still
    # covers a solved velocity carrying declared fields alongside it,
    # unaffected by this addition.
    run_velocity_only_simulation = config.simulation.velocity_solved and not config.fields
    run_simulation = run_scalar_simulation or run_velocity_only_simulation
    # Vectors are drawn as arrows by two different paths (a static
    # `vector_pattern`, or a live, velocity-only solved run) -- neither
    # implies the other, so both report separately below, and `False`
    # here is the answer for a run that takes neither path.
    #
    # **Answered by the drawing paths themselves since the Stage 7 exit
    # audit (2026-09-03), not computed from configuration here.** This
    # used to read `(show_fields and vector_pattern is not None) or
    # run_velocity_only_simulation`, which is a different question:
    # `build_vector_field_arrows` returns `None` for a field whose every
    # cell vector is exactly zero, so both of those conditions can be
    # true over a frame containing no arrow at all -- and the stats
    # block then stated a length-per-magnitude conversion for something
    # the viewer could not see. Reachable from a shipped demo:
    # `lid_driven_cavity.yaml` sets `vector_label` and starts from rest.
    show_vector_scale: Callable[[], bool] = _arrows_drawn_constantly(False)
    on_frame: Callable[[], None] | None = None
    # Reversed 2026-08-31 after real user feedback: this used to also
    # require `show_mesh`/`show_fields`/`run_simulation`, specifically to
    # protect Empty Window's own contract (`tests/features/
    # empty_window.feature`, "every pixel is the configured background
    # colour") from an HUD that activated on its own. That made every
    # demo with nothing else configured to show (Numerics Assembly,
    # Stage 3's own "no CFD yet" demo) render a genuinely blank window
    # with zero information -- worse than the gap this stage exists to
    # close. `show_title`/`show_stats` are now the actual gate; Empty
    # Window opts out of both explicitly instead of relying on this
    # condition to do it implicitly.
    if (
        config.rendering.show_mesh
        or show_fields
        or run_simulation
        or config.rendering.show_title
        or config.rendering.show_stats
    ):
        # TASK-013/017: visualise the configured mesh's grid and/or its
        # fields -- no bespoke code, per the golden-demo public-API rule.
        # `show_mesh` is gated separately from `grid_color` being set
        # (changed 2026-08-21): a colour is a colour, not a feature
        # switch. `fit_camera_to_bounds` must run before
        # `apply_camera_config` below: it sets the "zoom == 1" base view
        # (and centres the camera), which configured zoom/pan then apply
        # on top of. `bounds` starts as the mesh's own bounding box and
        # `_add_field_display` widens it if a legend was drawn below the
        # mesh -- when only `show_mesh` is set, this is exactly what
        # `fit_camera_to_mesh` used to compute directly, unchanged.
        mesh = StructuredCartesianMesh.from_config(config.mesh)
        mesh_bounds = mesh_bounding_box(mesh)
        bounds = mesh_bounds
        legend_bounds: _Bounds | None = None
        if config.rendering.show_mesh:
            window.scene.add(build_mesh_grid_line(mesh, config.rendering.grid_color))
        if show_fields:
            bounds, legend_bounds, static_arrows = _add_field_display(
                window, mesh, config.field_display
            )
            show_vector_scale = _arrows_drawn_constantly(static_arrows)
        if run_scalar_simulation:
            # TASK-030: the first config that wires a real `simulation.
            # step()` into this run's own render loop, one timestep per
            # rendered frame -- every capability before it only ever
            # rendered one static frame.
            # Draws a colour map, never arrows, so it leaves
            # `show_vector_scale` alone (`_add_field_display`'s static
            # `vector_pattern` above may still have drawn some).
            on_frame, legend_bounds = _add_declared_field_transport(window, mesh, config)
        elif run_velocity_only_simulation:
            # Joined with whatever `_add_field_display` reported above,
            # never replacing it: a static `vector_pattern` and a
            # velocity-only solve are independent switches, and a
            # configuration setting both has arrows from two sources.
            on_frame, legend_bounds, solved_arrows = _add_solved_velocity_rendering(
                window, mesh, config
            )
            show_vector_scale = _either_path_drew_arrows(show_vector_scale, solved_arrows)

        bounds, hud_update = _add_hud(
            window,
            mesh_bounds,
            bounds,
            legend_bounds,
            config,
            on_frame is not None,
            show_vector_scale,
        )
        if hud_update is not None:
            simulation_advance = on_frame
            assert simulation_advance is not None

            def _on_frame() -> None:
                simulation_advance()
                hud_update()

            on_frame = _on_frame

        fit_camera_to_bounds(window.camera, bounds)

    window.apply_camera_config()

    window.run(max_frames=max_frames, on_frame=on_frame)
    logger.info("pyflow exited cleanly")
    return window
