"""Interactive playback rendering (TASK-047, Stage 8, Recording &
Playback): `pyflow play`'s own rendering half -- opens a real window and
renders a `MaterializedWindow` (TASK-046, `replay.py`) with live
keyboard pause/speed control, reusing this project's existing mesh/
field-visualization/HUD machinery the same way `bootstrap.py`'s own
live-stepping paths do, just indexing into pre-computed frames instead
of calling `advance_simulation_state`.

**Imports `rendering`, unlike `recording.py`/`replay.py`** -- this is
the one module in Stage 8 whose whole job is putting pixels on screen,
so there is nothing to keep headless here.

**Scoped to solved-velocity (arrows-only) rendering for this first
cut** -- exactly what the chosen Golden Demo (Lid-Driven Cavity) needs
(`config.simulation.velocity_solved` true, no declared `fields`).
Declared-field/scalar-colormap playback is a real, stated future
extension, not built now -- the same "scope to what a demo genuinely
needs first, revisit when one needs more" precedent
`_add_solved_velocity_rendering`'s own history in `bootstrap.py` already
set for TASK-031/034. `UnsupportedPlaybackConfigError` names the gap
loudly rather than silently rendering nothing.

**Pure playback-state logic (`PlaybackState`, `advance_playback_
position`, `toggle_pause`, `increase_speed`, `decrease_speed`) is kept
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

import torch

from pyflow.configuration.schema import PyFlowConfig, RenderBackend
from pyflow.engine.logging_setup import configure_logging
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField
from pyflow.rendering import RenderWindow
from pyflow.rendering.field_visualization import build_vector_field_arrows
from pyflow.rendering.hud import build_stats_text, build_title_text
from pyflow.rendering.mesh_visualization import (
    build_mesh_grid_line,
    fit_camera_to_bounds,
    mesh_bounding_box,
)
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
_HUD_Z = 0.03
_TITLE_MARGIN_FRACTION = 0.12
_STATS_MARGIN_FRACTION = 0.20


class UnsupportedPlaybackConfigError(ValueError):
    """Raised by `play` when the materialized window's own config is not
    the one shape this first cut of playback supports: solved velocity,
    no declared fields (`config.simulation.velocity_solved` true,
    `config.fields` empty) -- the Lid-Driven Cavity golden demo's own
    shape. Named loudly rather than silently rendering an empty scene.
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

    Raises `UnsupportedPlaybackConfigError` if the window's own config is
    not solved-velocity-only (see this module's own docstring for why).
    """
    window_data: MaterializedWindow = materialize_or_load_window(
        checkpoints_dir, from_frame=from_frame, to_frame=to_frame, cache_dir=cache_dir
    )
    config: PyFlowConfig = window_data.config
    if not (config.simulation.velocity_solved and not config.fields):
        raise UnsupportedPlaybackConfigError(
            "pyflow play only supports a solved-velocity-only config for now "
            "(simulation.velocity_solved: true, no declared fields) -- "
            f"got velocity_solved={config.simulation.velocity_solved!r}, "
            f"fields={[f.name for f in config.fields]!r}"
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
    min_y = mesh_min_y

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

    last_index = 0

    def _on_frame() -> None:
        nonlocal last_index
        index = advance_playback_position(playback_state, max_index=max_index)
        if index != last_index:
            _rebuild_arrows(index)
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

    window.canvas.add_event_handler(_on_key, "key_down")

    fit_camera_to_bounds(window.camera, bounds)
    window.apply_camera_config()
    window.run(max_frames=max_frames, on_frame=_on_frame)
    return window
