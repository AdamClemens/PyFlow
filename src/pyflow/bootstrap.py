"""Application bootstrap (TASK-010): load configuration, initialise
logging, open the rendering window, run the loop, exit cleanly.

TASK-010's own job was integration only -- prove every
engineering-infrastructure piece (D1-D3) composes into one coherent run,
not simulate anything. **That stopped being the whole of this module in
TASK-030 (Stage 4, 2026-08-28):** `_add_passive_scalar_transport` wires
a real `simulation.step()` into the render loop, one timestep per
rendered frame, whenever `config.simulation.scalar_pattern` is set.
**A second live path arrived in TASK-034 (Stage 5, 2026-08-29):**
`_add_solved_velocity_rendering` wires a real, genuinely pressure-
corrected `simulation.navier_stokes_step()` into the render loop instead,
whenever `config.simulation.velocity_solved` is set with no
`scalar_pattern` -- the Lid-Driven Cavity demo's own shape. Every other
configuration still renders without stepping anything.

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

from pyflow import __version__
from pyflow.configuration import load_config
from pyflow.configuration.schema import FieldDisplayConfig, PyFlowConfig, RenderBackend
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
_LEGEND_GAP_FRACTION = 0.04

# Z-offsets so overlapping same-plane content composites predictably
# (arrows/legend drawn over field fills) rather than depending on draw
# order at equal depth, which this renderer's tie-breaking behaviour was
# never verified for.
_ARROWS_Z = 0.01
_LEGEND_Z = 0.02

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


def _add_passive_scalar_transport(
    window: RenderWindow, mesh: Mesh, config: PyFlowConfig
) -> Callable[[], None]:
    """Wires a real `simulation.step()` into a live `pyflow run`
    (Stage 4 Completion Criterion 1, TASK-030) -- the mechanism the
    Passive Scalar Transport golden demo needs and no demo before it
    does. Builds the initial transported scalar field and prescribed
    velocity field from `config.simulation`, renders the first frame,
    and returns an `on_frame` closure that advances the simulation by one
    `config.numerics.timestep` and re-renders after every frame
    thereafter.

    Rebuilds the rendered `gfx.Mesh` from scratch each frame (removes the
    old one from `window.scene`, `build_scalar_field_mesh`s a new one)
    rather than mutating the geometry's own colour buffer in place --
    `build_scalar_field_mesh`/`scalar_field_colors` are already proven
    correct (TASK-017); an in-place buffer mutation would be new,
    unverified pygfx-API surface for a small win on a small demo mesh
    (TASK-030's own Design decision).

    **`config.simulation.velocity_solved` (TASK-031, added 2026-08-29)**:
    when true, velocity's own two components join `state` (decomposed
    via `VectorField.decompose`) and are advanced by the same `step`
    call as the scalar -- self-advected by the transporting `velocity`
    itself, reassembled (`VectorField.assemble`) from the just-advanced
    components after every frame so the *next* frame transports against
    the current velocity, not the initial one. `simulation.py` itself
    needs no change for this (Stage 5 Completion Criterion 1's own
    structural clause): decompose-before/reassemble-after lives entirely
    here, and `step` just sees more entries in `fields`. **Still requires
    a scalar (`scalar_pattern`)** -- a velocity-only live run has nothing
    this function knows how to render yet (no vector-arrow-per-frame
    path exists), so `velocity_solved` set without `scalar_pattern` is
    validated but has no visible effect through `bootstrap.py` today; the
    mechanism itself is proven directly against `simulation.step()`
    (`tests/features/velocity_field_support.feature`), not only through
    this live path. Revisit when a demo genuinely needs velocity-only
    live rendering (TASK-034's own Lid-Driven Cavity is the likely first).
    """
    assert window.assembled_numerics is not None
    numerics = window.assembled_numerics
    assert config.simulation.scalar_pattern is not None

    bounds = mesh_bounding_box(mesh)
    scalar_initializer = _simulation_scalar_initializer(config.simulation.scalar_pattern, bounds)
    velocity_initializer = _simulation_velocity_initializer(
        config.simulation.velocity_pattern, config.simulation.velocity
    )
    scalar_field = ScalarField(mesh, "tracer", initial_value=scalar_initializer)
    velocity_field = VectorField(
        mesh, "velocity", num_components=2, initial_value=velocity_initializer
    )

    solved = config.simulation.velocity_solved
    state: dict[str, Field] = {"tracer": scalar_field}
    if solved:
        for component in velocity_field.decompose():
            state[component.name] = component
    window.simulation_fields = state

    colors = scalar_field_colors(
        scalar_field,
        config.field_display.low_color,
        config.field_display.high_color,
        config.field_display.value_range,
    )
    rendered_object = build_scalar_field_mesh(scalar_field, colors)
    window.scene.add(rendered_object)

    def _advance() -> None:
        nonlocal state, rendered_object, velocity_field
        state = simulation_step(state, velocity_field, numerics, config.numerics.timestep)
        window.simulation_fields = state
        if solved:
            u_name = VectorField.component_name("velocity", 0)
            v_name = VectorField.component_name("velocity", 1)
            u, v = state[u_name], state[v_name]
            assert isinstance(u, ScalarField)
            assert isinstance(v, ScalarField)
            velocity_field = VectorField.assemble([u, v], "velocity")
        tracer = state["tracer"]
        assert isinstance(tracer, ScalarField)
        colors = scalar_field_colors(
            tracer,
            config.field_display.low_color,
            config.field_display.high_color,
            config.field_display.value_range,
        )
        window.scene.remove(rendered_object)
        rendered_object = build_scalar_field_mesh(tracer, colors)
        window.scene.add(rendered_object)

    return _advance


def _add_solved_velocity_rendering(
    window: RenderWindow, mesh: Mesh, config: PyFlowConfig
) -> Callable[[], None]:
    """Wires a real `simulation.navier_stokes_step()` into a live `pyflow
    run` (TASK-034, Stage 5) -- the mechanism the Lid-Driven Cavity
    golden demo needs and no demo before it does: a *solved* velocity
    field, rendered live, with no scalar alongside it at all.

    `_add_passive_scalar_transport`'s own docstring named this gap in
    advance (TASK-031, 2026-08-29): "a velocity-only live run has
    nothing this function knows how to render yet (no vector-arrow-per-
    frame path exists)... revisit when a demo genuinely needs
    velocity-only live rendering (TASK-034's own Lid-Driven Cavity is the
    likely first)". This is that revisit -- `build_vector_field_arrows`
    (TASK-017) already existed for a *static* vector display; this
    function is what rebuilds it every frame, the same "remove the old
    `gfx.Line`, build a new one" shape `_add_passive_scalar_transport`
    already uses for its own scalar mesh.

    **Uses `navier_stokes_step`, not plain `step`** -- the real
    difference from `_add_passive_scalar_transport`'s own `velocity_
    solved` path, which only ever transports velocity's components like
    an ordinary scalar and never pressure-corrects them (a genuine,
    pre-existing gap in that path, out of this task's own scope to
    close: nothing before TASK-034 had a corrector loop to call). A
    demo using this function is genuinely incompressible, frame by
    frame, not merely self-advected.
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

    return _advance


def _add_field_display(
    window: RenderWindow, mesh: Mesh, field_display: FieldDisplayConfig
) -> _Bounds:
    """Build and add whatever `field_display` asks for -- the scalar
    colour map, its legend, and the vector arrows -- entirely from
    configuration, per the golden-demo public-API rule. Does nothing for
    whichever of scalar/vector isn't configured (`None`, the default for
    both).

    Returns the bounding box the caller should frame the camera on:
    the mesh's own bounds, extended downward to include the legend strip
    if one was drawn.
    """
    bounds = mesh_bounding_box(mesh)
    min_x, min_y, max_x, max_y = bounds
    center = ((min_x + max_x) / 2, (min_y + max_y) / 2)

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

        if field_display.show_legend:
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
            bounds = (min_x, legend_bottom, max_x, max_y)

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

    return bounds


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

    # TASK-021: assemble all six numerics components from `config.numerics`
    # and report the result -- Stage 3 Completion Criterion 8. Every run
    # does this, not only ones that need numerics for anything yet, since
    # `NumericsConfig` always has a full section (defaulted or not) and
    # assembly must not depend on whether a caller happens to care.
    # `config.fluid.diffusion_coefficient` (TASK-041, 2026-08-28) is
    # threaded in explicitly -- it moved out of `NumericsConfig` into its
    # own `fluid:` section, so `assemble_numerics` can no longer read it
    # off `config.numerics` alone. `coefficient_overrides` (TASK-031b,
    # 2026-08-29): when velocity is solved, its own two components
    # (`VectorField.component_name`) are diffused with `fluid.viscosity`
    # instead of the scalar default -- this is the one place in the
    # engine that legitimately knows a run's velocity field is
    # conventionally named "velocity", so it is where that mapping is
    # built, not inside `assemble_numerics`/`CentralDifferenceDiffusion`
    # themselves (both stay field-name-agnostic).
    coefficient_overrides = None
    if config.simulation.velocity_solved:
        coefficient_overrides = {
            VectorField.component_name("velocity", i): config.fluid.viscosity for i in range(2)
        }
    window.assembled_numerics = assemble_numerics(
        config.numerics, config.fluid.diffusion_coefficient, coefficient_overrides
    )
    logger.info("numerics assembled: %s", window.assembled_numerics.names)

    show_fields = (
        config.field_display.scalar_pattern is not None
        or config.field_display.vector_pattern is not None
    )
    run_scalar_simulation = config.simulation.scalar_pattern is not None
    # TASK-034 (Stage 5): a velocity-only live run -- solved, rendered as
    # arrows, no scalar alongside it (`_add_solved_velocity_rendering`'s
    # own docstring). Mutually exclusive with `run_scalar_simulation`,
    # the same "one live-simulation path per run" shape TASK-030 already
    # established -- `_add_passive_scalar_transport`'s own `velocity_
    # solved` still covers a solved velocity carrying a scalar alongside
    # it, unaffected by this addition.
    run_velocity_only_simulation = (
        config.simulation.velocity_solved and config.simulation.scalar_pattern is None
    )
    run_simulation = run_scalar_simulation or run_velocity_only_simulation
    on_frame: Callable[[], None] | None = None
    if config.rendering.show_mesh or show_fields or run_simulation:
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
        bounds = mesh_bounding_box(mesh)
        if config.rendering.show_mesh:
            window.scene.add(build_mesh_grid_line(mesh, config.rendering.grid_color))
        if show_fields:
            bounds = _add_field_display(window, mesh, config.field_display)
        if run_scalar_simulation:
            # TASK-030: the first config that wires a real `simulation.
            # step()` into this run's own render loop, one timestep per
            # rendered frame -- every capability before it only ever
            # rendered one static frame.
            on_frame = _add_passive_scalar_transport(window, mesh, config)
        elif run_velocity_only_simulation:
            on_frame = _add_solved_velocity_rendering(window, mesh, config)
        fit_camera_to_bounds(window.camera, bounds)

    window.apply_camera_config()

    window.run(max_frames=max_frames, on_frame=on_frame)
    logger.info("pyflow exited cleanly")
    return window
