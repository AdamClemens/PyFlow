"""Interactive playback rendering (TASK-047, Stage 8, Recording &
Playback): `pyflow play`'s own rendering half -- opens a real window and
renders a `MaterializedWindow` (TASK-046, `replay.py`) with live
keyboard/mouse pause, speed, and seek control, reusing this project's
existing mesh/field-visualization/HUD machinery the same way
`bootstrap.py`'s own live-stepping paths do, just indexing into
pre-computed frames instead of calling `advance_simulation_state`.

**Imports `rendering`, unlike `recording.py`/`replay.py`** -- this is
the one module in Stage 8 whose whole job is putting pixels on screen,
so there is nothing to keep headless here.

**Requires a solved velocity field; declared fields are optional
(TASK-051, Stage 8 reopening, widened 2026-09-09 from the original
"arrows-only, no declared fields" first cut).**
`config.simulation.velocity_solved` must be true --
`UnsupportedPlaybackConfigError` names the gap loudly rather than
silently rendering nothing for a config with no solved velocity at all
(Heat Diffusion's own shape). `config.fields`, if declared, each get a
colour-mapped panel via `config.field_display.panels`, reusing
`field_visualization.panel_colors`/`panel_caption`/`build_panel_legend`/
`PanelRenderState` -- extracted from `bootstrap.py`'s own private
helpers for exactly this reuse, verified behaviour-preserving by the
full existing test suite passing unmodified before this module's own
combined path was added. Grounded in Smoke Transport
(`examples/golden-demos/smoke_transport.yaml`): solved velocity plus a
declared `smoke` field, two configured panels.

**Live scrub (TASK-048, Stage 8 reopening, added 2026-09-09): Left/
Right step one frame, Home/End jump to the loaded window's own edges,
and a draggable scrub bar reaches any frame in between directly.**
Scoped to the window already materialized at launch
(`[from_frame, to_frame]`) -- seeking past either edge still needs a
different `pyflow play` invocation. The scrub bar's own pointer handlers
register at `order=-1` (`RenderWindow.run`'s own camera-pan handlers
register at the default `order=0`) and set `event["stop_propagation"]`
when a drag starts on the bar, so a scrub drag never also pans the
camera underneath it -- verified empirically before being relied on
(`rendercanvas.core.events.EventEmitter.emit` checks
`stop_propagation` before each handler, in `order` then registration
order) rather than assumed from reading the library's own docs, the
same "verify before relying on it" discipline `rendering/CLAUDE.md`'s
pan/zoom entries already establish.

**Pure playback-state logic (`PlaybackState`, `advance_playback_
position`, `toggle_pause`, `increase_speed`, `decrease_speed`,
`seek_relative`, `seek_to`, `frame_index_from_fraction`) is kept
separate from the rendering it drives**, testable with plain pytest and
no window at all -- `tests/unit/test_playback.py`. Only `play()` itself
needs a real display, covered by `tests/integration/
test_playback_cli.py` the same way `tests/integration/
test_interactive_window.py` already covers `RenderWindow`'s own
keyboard/wheel/pointer wiring.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygfx as gfx
import torch

from pyflow.configuration.schema import PyFlowConfig, RenderBackend
from pyflow.engine.logging_setup import configure_logging
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField
from pyflow.rendering import RenderWindow
from pyflow.rendering.field_visualization import (
    PanelRenderState,
    build_panel_legend,
    build_scalar_field_mesh,
    build_vector_field_arrows,
    panel_caption,
    panel_colors,
)
from pyflow.rendering.hud import build_stats_text, build_title_text
from pyflow.rendering.mesh_visualization import (
    build_mesh_grid_line,
    fit_camera_to_bounds,
    mesh_bounding_box,
)
from pyflow.rendering.window import screen_to_world
from pyflow.replay import MaterializedWindow, materialize_or_load_window

_Bounds = tuple[float, float, float, float]

MIN_SPEED = 0.125
MAX_SPEED = 8.0

# Layout/depth constants mirroring `bootstrap.py`'s own established
# values for the same purpose (`_ARROWS_Z`, `_HUD_Z`, `_TITLE_MARGIN_
# FRACTION`, `_STATS_MARGIN_FRACTION`) -- pygfx still gives no cheap way
# to measure a `Text` object's rendered size before adding it to a
# scene, so these are the same "fixed, generous guess, not measured"
# shape those constants already establish, not re-derived independently.
_ARROWS_Z = 0.01
_LEGEND_Z = 0.02
_HUD_Z = 0.03
_TITLE_MARGIN_FRACTION = 0.12
_STATS_MARGIN_FRACTION = 0.20

# Declared-field panels (TASK-051, Stage 8 reopening): same values as
# `bootstrap.py`'s own `_PANEL_GAP_FRACTION`/`_LEGEND_LABEL_MARGIN_
# FRACTION`, duplicated here rather than imported -- this file already
# keeps its own private copies of every other layout/depth constant
# `bootstrap.py` also has (`_ARROWS_Z`, `_HUD_Z`, `_TITLE_MARGIN_
# FRACTION`, `_STATS_MARGIN_FRACTION`), the same precedent.
_PANEL_GAP_FRACTION = 0.15
_LEGEND_LABEL_MARGIN_FRACTION = 0.10

# The scrub bar's own layout (TASK-048, Stage 8 reopening) -- same
# fixed-fraction-of-mesh-height shape as the constants above, for the
# same reason (nothing here can be measured before it's drawn).
_SCRUB_BAR_GAP_FRACTION = 0.08
"""Gap between the scrub bar and whatever HUD element sits above it."""
_SCRUB_BAR_MARGIN_FRACTION = 0.12
"""How far the scrub bar's own margin extends the framed view downward."""
_SCRUB_BAR_HIT_HALF_HEIGHT_FRACTION = 0.04
"""Vertical click tolerance around the bar's own y, as a fraction of
mesh height -- a `pointer_down` within this band of the bar starts a
drag; once dragging, `pointer_move` tracks x regardless of y, the same
"a drag need not stay exactly on the widget" tolerance most UI scrub
bars give."""
_SCRUB_TRACK_COLOR = "#888888"
_SCRUB_THUMB_COLOR = "#ffcc00"


class UnsupportedPlaybackConfigError(ValueError):
    """Raised by `play` when the materialized window's own config has no
    solved velocity field at all (`config.simulation.velocity_solved`
    false) -- Heat Diffusion's own shape, and the one case this module
    cannot render, since there is nothing to draw arrows for. A config
    with `velocity_solved` true and declared `fields` (Smoke Transport's
    own shape) is supported, not rejected -- see this module's own
    docstring. Named loudly rather than silently rendering an empty
    scene.
    """


@dataclass
class PlaybackState:
    """Mutable playback state a `play()` run's keyboard handler and
    per-frame callback both act on. `position` is a *fractional* frame
    index into `MaterializedWindow.frames` -- advanced by `speed` each
    real draw, not each materialized frame, since the two are decoupled
    (`docs/planning/roadmap.md` TASK-047's own Design decisions: at
    mesh sizes above roughly 4096 cells, real draw rate stays capped
    near ~30fps by scene-rebuild cost alone, so "faster" has to mean
    "advance further per draw", not "draw more often").
    """

    position: float = 0.0
    paused: bool = False
    speed: float = 1.0
    dragging: bool = False
    """Set while a mouse drag on the scrub bar is in progress (TASK-048,
    Stage 8 reopening) -- lets `play()`'s pointer handlers distinguish
    "this drag is ours" across `pointer_down`/`pointer_move`/
    `pointer_up`, the same way `RenderWindow._pan_drag_start_screen`
    tracks whether a camera-pan drag is in progress."""


def advance_playback_position(state: PlaybackState, *, max_index: int) -> int:
    """Advance `state.position` by `state.speed` (unless paused), clamp
    to `[0, max_index]` -- freezing on the last frame rather than
    looping back to the start, a deliberate default (a replay that
    suddenly rewinds without being asked is a worse surprise than one
    that just stops) -- and return the resulting frame index
    (`floor(position)`). Mutates `state` in place.
    """
    if not state.paused:
        state.position += state.speed
    state.position = max(0.0, min(state.position, float(max_index)))
    return int(state.position)


def toggle_pause(state: PlaybackState) -> None:
    """Flip `state.paused` -- the Space key's own effect."""
    state.paused = not state.paused


def increase_speed(state: PlaybackState) -> None:
    """Double `state.speed`, clamped at `MAX_SPEED` -- the `+`/`=` key's
    own effect.
    """
    state.speed = min(state.speed * 2.0, MAX_SPEED)


def decrease_speed(state: PlaybackState) -> None:
    """Halve `state.speed`, clamped at `MIN_SPEED` -- the `-` key's own
    effect.
    """
    state.speed = max(state.speed / 2.0, MIN_SPEED)


def seek_relative(state: PlaybackState, delta: int, *, max_index: int) -> int:
    """Move `state.position` by exactly `delta` frames, clamped to
    `[0, max_index]`, regardless of `state.speed` or `state.paused` --
    the Left/Right keys' own effect (TASK-048). Unlike
    `advance_playback_position`, this never depends on speed: a keyboard
    seek always means "one frame", not "however fast playback happens to
    be going". Returns the resulting frame index; mutates `state` in
    place.
    """
    state.position = max(0.0, min(state.position + delta, float(max_index)))
    return int(state.position)


def seek_to(state: PlaybackState, index: int, *, max_index: int) -> int:
    """Jump `state.position` directly to `index`, clamped to
    `[0, max_index]` -- the Home/End keys' own effect (jumping to `0`/
    `max_index`), and the mechanism a scrub-bar drag uses to set an
    absolute position rather than a relative step. Returns the
    resulting frame index; mutates `state` in place.
    """
    state.position = max(0.0, min(float(index), float(max_index)))
    return int(state.position)


def frame_index_from_fraction(fraction: float, *, max_index: int) -> int:
    """The frame index `round(fraction * max_index)` maps to, clamped to
    `[0, max_index]` -- how a scrub-bar drag's own world-space position
    (already reduced to a `0..1` fraction along the bar) becomes a
    frame index. Clamped rather than left to overshoot, since a drag
    that continues past either end of the bar while still held is a
    real, expected gesture, not an error.
    """
    index = round(fraction * max_index)
    return max(0, min(index, max_index))


def _velocity_field_from_frame(
    mesh: StructuredCartesianMesh, frame: dict[str, torch.Tensor]
) -> VectorField:
    """The inverse of `checkpoint.field_tensors`, for one materialized
    frame -- reassembles a `VectorField` from its two raw, decomposed
    tensors, the same `ScalarField`-wrap-then-`VectorField.assemble`
    shape `checkpoint.restore_simulation_state` already uses for a single
    checkpoint's own fields.
    """
    components = [
        ScalarField(
            mesh,
            VectorField.component_name("velocity", i),
            initial_value=frame[VectorField.component_name("velocity", i)],
        )
        for i in range(2)
    ]
    return VectorField.assemble(components, "velocity")


def _declared_field_from_frame(
    mesh: StructuredCartesianMesh, frame: dict[str, torch.Tensor], name: str
) -> ScalarField:
    """One declared field's own raw tensor, wrapped back into a
    `ScalarField` -- the scalar-field counterpart to
    `_velocity_field_from_frame` above, for TASK-051's own panel
    rendering (Stage 8 reopening, added 2026-09-09).
    """
    return ScalarField(mesh, name, initial_value=frame[name])


def _playback_stats_lines(state: PlaybackState, frame_number: int) -> list[str]:
    """The one stats line this first cut shows -- frame number (the real
    materialized simulation frame, not a local playback-loop count) plus
    play/pause and speed. Deliberately simpler than `bootstrap.py`'s own
    `_stats_lines` (no cell/domain size, no `config.units` formatting) --
    a real, stated scope decision for this first cut, not an oversight;
    revisit if a shipped playback demo needs more.
    """
    status = "Paused" if state.paused else "Playing"
    return [f"Frame {frame_number}", f"{status} at {state.speed:g}x"]


def play(
    checkpoints_dir: str | Path,
    *,
    from_frame: int,
    to_frame: int,
    cache_dir: str | Path | None = None,
    backend: RenderBackend | None = None,
    max_frames: int | None = None,
    on_frame: Callable[[RenderWindow], None] | None = None,
) -> RenderWindow:
    """Materialize (or load a cached) window from `checkpoints_dir` over
    `[from_frame, to_frame]` and render it in a real window, with Space
    pausing/resuming and `+`/`-` changing playback speed live.

    `backend`/`max_frames` mirror `bootstrap()`'s own parameters of the
    same name -- an automated/headless run (`--backend offscreen
    --max-frames N`) needs both, the same golden-demo regression-testing
    reason `bootstrap()` already has them.

    `on_frame`, if given, is called once per rendered frame with the
    `RenderWindow` itself, after this function's own per-frame update
    (arrow rebuild, stats text) -- the same "general hook, not a
    test-only seam" shape `RenderWindow.run`'s own `on_frame` parameter
    already establishes, composed the way `bootstrap.py` composes its
    own simulation-advance and HUD-update closures. Takes `window`
    (unlike `RenderWindow.run`'s own no-argument `on_frame`) because a
    caller cannot otherwise reach it before `run()` starts blocking --
    `play()` constructs the window internally. `window.playback_state`
    (`PlaybackState`) is set for exactly this purpose: `pyflow play`
    itself never passes an `on_frame`, but `tests/integration/
    test_playback_cli.py` uses it to observe `playback_state.paused`/
    `.speed` and `window.renderer.snapshot()` frame to frame, which
    nothing outside this function could otherwise see.

    Raises `UnsupportedPlaybackConfigError` if the window's own config has
    no solved velocity field at all (see this module's own docstring for
    why declared fields alongside it are fine).
    """
    window_data: MaterializedWindow = materialize_or_load_window(
        checkpoints_dir, from_frame=from_frame, to_frame=to_frame, cache_dir=cache_dir
    )
    config: PyFlowConfig = window_data.config
    if not config.simulation.velocity_solved:
        raise UnsupportedPlaybackConfigError(
            "pyflow play requires a solved velocity field "
            "(simulation.velocity_solved: true) -- "
            f"got velocity_solved={config.simulation.velocity_solved!r}"
        )

    if backend is not None:
        config.rendering.backend = backend
        config.rendering.validate()
    configure_logging(config.logging)

    window = RenderWindow(config.rendering)
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    mesh_bounds = mesh_bounding_box(mesh)
    bounds = mesh_bounds
    mesh_min_x, mesh_min_y, mesh_max_x, mesh_max_y = mesh_bounds
    mesh_height = mesh_max_y - mesh_min_y
    mesh_width = mesh_max_x - mesh_min_x
    font_size = mesh_height * 0.05

    if config.rendering.show_mesh:
        window.scene.add(build_mesh_grid_line(mesh, config.rendering.grid_color))

    playback_state = PlaybackState()
    window.playback_state = playback_state
    max_index = len(window_data.frames) - 1
    rendered_object = None

    def _rebuild_arrows(index: int) -> None:
        nonlocal rendered_object
        if rendered_object is not None:
            window.scene.remove(rendered_object)
        velocity_field = _velocity_field_from_frame(mesh, window_data.frames[index])
        rendered_object = build_vector_field_arrows(
            velocity_field, config.field_display.arrow_color, config.field_display.arrow_scale
        )
        if rendered_object is not None:
            rendered_object.local.position = (0.0, 0.0, _ARROWS_Z)
            window.scene.add(rendered_object)

    _rebuild_arrows(0)

    # Declared-field panels (TASK-051, Stage 8 reopening, added
    # 2026-09-09) -- built once here (mesh + legend, frame 0), rebuilt
    # per frame by `_rebuild_panels` below (mesh + equalized labels
    # only, never the legend itself, the same "the ramp's own rendered
    # pixels never change" reasoning `build_panel_legend`'s own
    # docstring gives). Empty `config.field_display.panels` (Lid-Driven
    # Cavity's own shape) means this loop does nothing at all.
    panel_states = [
        PanelRenderState(panel, index * mesh_width * (1.0 + _PANEL_GAP_FRACTION))
        for index, panel in enumerate(config.field_display.panels)
    ]
    for panel_state in panel_states:
        panel = panel_state.panel
        rendered_field = _declared_field_from_frame(mesh, window_data.frames[0], panel.field)
        colors = panel_colors(
            rendered_field, panel, config.field_display.low_color, config.field_display.high_color
        )
        panel_state.mesh_object = build_scalar_field_mesh(rendered_field, colors)
        panel_state.mesh_object.local.position = (panel_state.offset_x, 0.0, 0.0)
        window.scene.add(panel_state.mesh_object)
        if panel.mode == "equalized":
            initial_min = float(rendered_field.values.min())
            initial_max = float(rendered_field.values.max())
        else:
            initial_min, initial_max = panel.value_range
        legend_mesh, legend_labels, panel_legend_bounds, panel_state.update_labels = (
            build_panel_legend(
                config.field_display.low_color,
                config.field_display.high_color,
                config.field_display.show_legend,
                mesh_bounds,
                panel_state.offset_x,
                panel_caption(panel),
                initial_min,
                initial_max,
            )
        )
        if legend_mesh is not None:
            legend_mesh.local.position = (0.0, 0.0, _LEGEND_Z)
            window.scene.add(legend_mesh)
        for label in legend_labels:
            label.local.position = (label.local.position[0], label.local.position[1], _HUD_Z)
            window.scene.add(label)
        bounds = (
            bounds[0],
            bounds[1],
            max(bounds[2], mesh_bounds[2] + panel_state.offset_x),
            bounds[3],
        )
        if panel_legend_bounds is not None:
            # Mirrors `bootstrap.py`'s own identical widening
            # (`_add_declared_field_transport`) -- every panel's own
            # legend sits at the same height, so this converges to one
            # value across the loop, and without it a stats block placed
            # below would draw straight over the legend/caption.
            bounds = (
                bounds[0],
                min(
                    bounds[1], panel_legend_bounds[1] - mesh_height * _LEGEND_LABEL_MARGIN_FRACTION
                ),
                bounds[2],
                bounds[3],
            )

    def _rebuild_panels(index: int) -> None:
        for panel_state in panel_states:
            panel = panel_state.panel
            rendered_field = _declared_field_from_frame(
                mesh, window_data.frames[index], panel.field
            )
            colors = panel_colors(
                rendered_field,
                panel,
                config.field_display.low_color,
                config.field_display.high_color,
            )
            assert panel_state.mesh_object is not None
            window.scene.remove(panel_state.mesh_object)
            panel_state.mesh_object = build_scalar_field_mesh(rendered_field, colors)
            panel_state.mesh_object.local.position = (panel_state.offset_x, 0.0, 0.0)
            window.scene.add(panel_state.mesh_object)
            if panel.mode == "equalized" and panel_state.update_labels is not None:
                panel_state.update_labels(
                    float(rendered_field.values.min()), float(rendered_field.values.max())
                )

    min_y = bounds[1]

    if config.rendering.show_title and config.rendering.title:
        title = build_title_text(
            config.rendering.title,
            ((mesh_min_x + mesh_max_x) / 2, mesh_max_y + mesh_height * 0.02),
            font_size=font_size,
            max_width=mesh_width,
        )
        title.local.position = (title.local.position[0], title.local.position[1], _HUD_Z)
        window.scene.add(title)
        bounds = (
            bounds[0],
            bounds[1],
            bounds[2],
            mesh_max_y + mesh_height * _TITLE_MARGIN_FRACTION,
        )

    stats_text = None
    if config.rendering.show_stats:
        stats_text = build_stats_text(
            _playback_stats_lines(playback_state, from_frame),
            (mesh_min_x, min_y - mesh_height * 0.02),
            font_size=font_size,
            max_width=mesh_width,
        )
        stats_text.local.position = (
            stats_text.local.position[0],
            stats_text.local.position[1],
            _HUD_Z,
        )
        window.scene.add(stats_text)
        bounds = (
            bounds[0],
            min_y - mesh_height * _STATS_MARGIN_FRACTION,
            bounds[2],
            bounds[3],
        )

    # The scrub bar (TASK-048): a static track plus a thumb rebuilt the
    # same "remove old, build new" way `_rebuild_arrows` already is --
    # this project's own established convention over mutating a
    # geometry's buffer in place (`_add_declared_field_transport`'s own
    # docstring in `bootstrap.py`).
    bar_y = bounds[1] - mesh_height * _SCRUB_BAR_GAP_FRACTION
    track = gfx.Line(
        gfx.Geometry(positions=[[mesh_min_x, bar_y, _HUD_Z], [mesh_max_x, bar_y, _HUD_Z]]),
        gfx.LineSegmentMaterial(thickness=2.0, color=_SCRUB_TRACK_COLOR),
    )
    window.scene.add(track)
    bounds = (
        bounds[0],
        bar_y - mesh_height * _SCRUB_BAR_MARGIN_FRACTION,
        bounds[2],
        bounds[3],
    )

    thumb_object: gfx.Points | None = None

    def _thumb_x(index: int) -> float:
        fraction = index / max_index if max_index else 0.0
        return mesh_min_x + fraction * mesh_width

    def _rebuild_thumb(index: int) -> None:
        nonlocal thumb_object
        if thumb_object is not None:
            window.scene.remove(thumb_object)
        thumb_object = gfx.Points(
            gfx.Geometry(positions=[[_thumb_x(index), bar_y, _HUD_Z]]),
            gfx.PointsMaterial(color=_SCRUB_THUMB_COLOR, size=12.0),
        )
        window.scene.add(thumb_object)

    _rebuild_thumb(0)

    last_index = 0

    def _on_frame() -> None:
        nonlocal last_index
        index = advance_playback_position(playback_state, max_index=max_index)
        if index != last_index:
            _rebuild_arrows(index)
            _rebuild_panels(index)
            _rebuild_thumb(index)
            last_index = index
        if stats_text is not None:
            stats_text.set_text(
                "\n".join(_playback_stats_lines(playback_state, from_frame + index))
            )
        if on_frame is not None:
            on_frame(window)

    def _on_key(event: dict[str, Any]) -> None:
        key = event.get("key")
        if key == " ":
            toggle_pause(playback_state)
        elif key in ("+", "="):
            increase_speed(playback_state)
        elif key == "-":
            decrease_speed(playback_state)
        elif key == "ArrowRight":
            seek_relative(playback_state, 1, max_index=max_index)
        elif key == "ArrowLeft":
            seek_relative(playback_state, -1, max_index=max_index)
        elif key == "Home":
            seek_to(playback_state, 0, max_index=max_index)
        elif key == "End":
            seek_to(playback_state, max_index, max_index=max_index)

    def _seek_from_pointer_x(screen_x: float, screen_y: float) -> None:
        logical_width, logical_height = window.canvas.get_logical_size()
        world_x, _world_y = screen_to_world(
            window.camera, logical_width, logical_height, screen_x, screen_y
        )
        fraction = (world_x - mesh_min_x) / mesh_width if mesh_width else 0.0
        seek_to(
            playback_state,
            frame_index_from_fraction(fraction, max_index=max_index),
            max_index=max_index,
        )

    def _on_pointer_down(event: dict[str, Any]) -> None:
        logical_width, logical_height = window.canvas.get_logical_size()
        _world_x, world_y = screen_to_world(
            window.camera, logical_width, logical_height, event["x"], event["y"]
        )
        hit_half_height = mesh_height * _SCRUB_BAR_HIT_HALF_HEIGHT_FRACTION
        if abs(world_y - bar_y) > hit_half_height:
            return
        playback_state.dragging = True
        _seek_from_pointer_x(event["x"], event["y"])
        event["stop_propagation"] = True

    def _on_pointer_move(event: dict[str, Any]) -> None:
        if not playback_state.dragging:
            return
        _seek_from_pointer_x(event["x"], event["y"])
        event["stop_propagation"] = True

    def _on_pointer_up(event: dict[str, Any]) -> None:
        if not playback_state.dragging:
            return
        playback_state.dragging = False
        event["stop_propagation"] = True

    window.canvas.add_event_handler(_on_key, "key_down")
    # `order=-1`, run before `RenderWindow.run`'s own camera-pan handlers
    # (registered at the default `order=0`) -- a drag that starts on the
    # scrub bar sets `stop_propagation` so it never also pans the camera
    # underneath it (verified empirically, see this module's own
    # docstring).
    window.canvas.add_event_handler(_on_pointer_down, "pointer_down", order=-1)
    window.canvas.add_event_handler(_on_pointer_move, "pointer_move", order=-1)
    window.canvas.add_event_handler(_on_pointer_up, "pointer_up", order=-1)

    fit_camera_to_bounds(window.camera, bounds)
    window.apply_camera_config()
    window.run(max_frames=max_frames, on_frame=_on_frame)
    return window
