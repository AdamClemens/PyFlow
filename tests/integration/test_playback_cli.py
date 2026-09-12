"""`pyflow play` (TASK-046/047, Stage 8, Recording & Playback): real
subprocesses for the headless path, and a real glfw window with genuine
injected keyboard events for the interactive pause path -- the same
two-tier split `tests/integration/test_interactive_window.py` already
establishes for `RenderWindow`'s own keyboard/wheel/pointer wiring,
applied here to `playback.py`'s own Space/`+`/`-` handling.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pygfx as gfx
import pytest

from pyflow.checkpoint import read_checkpoint
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.playback import play
from pyflow.rendering.mesh_visualization import mesh_bounding_box
from pyflow.rendering.window import RenderWindow, visible_world_size


def _display_available() -> bool:
    # Copied from `tests/integration/test_interactive_window.py` rather
    # than imported -- `tests/` is not an importable package here, and
    # `tests/unit/CLAUDE.md`'s own "local by default" convention already
    # prefers a short duplicate over a new shared-import mechanism for
    # exactly this kind of small, self-contained helper. See that
    # module's own copy for the full reasoning (the Linux DISPLAY/
    # WAYLAND_DISPLAY guard in particular).
    if sys.platform.startswith("linux") and not (
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    ):
        return False

    try:
        from rendercanvas.glfw import GlfwRenderCanvas

        canvas = GlfwRenderCanvas(size=(2, 2))
        canvas.close()
        return True
    except Exception:
        return False


_needs_a_real_display = pytest.mark.skipif(
    not _display_available(), reason="no display available for a real glfw window"
)


def _record_cavity(output_dir: Path, *, max_frames: int, checkpoint_interval: int) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "record",
            "--config",
            "examples/golden-demos/lid_driven_cavity.yaml",
            "--max-frames",
            str(max_frames),
            "--output-dir",
            str(output_dir),
            "--checkpoint-interval",
            str(checkpoint_interval),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _record_cavity_without_stats(
    tmp_path: Path, output_dir: Path, *, max_frames: int, checkpoint_interval: int
) -> None:
    """Record the same cavity, but with `rendering.show_stats: false`.

    **Added 2026-09-11 by the Stage 8 exit audit**, for the pixel-level
    scrub check below. The stats HUD rewrites the frame number into the
    rendered image every single frame, so with it on, *any* two frames
    at different positions hash differently whether or not the field
    itself was ever rebuilt -- a full-frame hash would pass vacuously.
    Turning it off leaves the field, the arrows and the scrub thumb as
    the only things in the image, which is what the criterion is
    actually about.
    """
    config_text = Path("examples/golden-demos/lid_driven_cavity.yaml").read_text(encoding="utf-8")
    config_file = tmp_path / "cavity_no_stats.yaml"
    # `rendering:` is the last section in the golden demo, so appending
    # one more key to it needs no YAML round trip.
    config_file.write_text(config_text + "  show_stats: false\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "record",
            "--config",
            str(config_file),
            "--max-frames",
            str(max_frames),
            "--output-dir",
            str(output_dir),
            "--checkpoint-interval",
            str(checkpoint_interval),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_play_renders_a_real_recorded_run_headlessly(tmp_path: Path) -> None:
    checkpoints_dir = tmp_path / "checkpoints"
    _record_cavity(checkpoints_dir, max_frames=20, checkpoint_interval=20)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "play",
            "--checkpoints-dir",
            str(checkpoints_dir),
            "--to-frame",
            "20",
            "--backend",
            "offscreen",
            "--max-frames",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def _record_smoke_transport(output_dir: Path, *, max_frames: int, checkpoint_interval: int) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "record",
            "--config",
            "examples/golden-demos/smoke_transport.yaml",
            "--max-frames",
            str(max_frames),
            "--output-dir",
            str(output_dir),
            "--checkpoint-interval",
            str(checkpoint_interval),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_play_renders_smoke_transport_through_the_real_cli(tmp_path: Path) -> None:
    """TASK-051's own Golden Demo grounding: Smoke Transport combines a
    solved velocity field with a declared `smoke` field, the config
    shape `play()` used to reject outright before this task.
    """
    checkpoints_dir = tmp_path / "checkpoints"
    _record_smoke_transport(checkpoints_dir, max_frames=10, checkpoint_interval=10)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "play",
            "--checkpoints-dir",
            str(checkpoints_dir),
            "--to-frame",
            "10",
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_play_renders_both_arrows_and_a_panel_for_smoke_transport(tmp_path: Path) -> None:
    """The literal claim this task exists to prove -- through the public
    Python API (`play()` directly) rather than the CLI, since that is
    the only way to inspect what actually landed in `window.scene`.
    Distinguishes real content from coincidence by shape, not merely by
    type: the scrub bar's own track is always exactly a 2-point line
    segment (`playback.py`'s own track geometry), so any longer `gfx.
    Line` must be the velocity arrows; a panel's own field mesh has one
    quad (4 vertices) per mesh cell, far more than a legend's fixed
    32-quad gradient strip (also a `gfx.Mesh`), so a mesh with more than
    128 vertices must be a real field panel, not just a legend.
    """
    checkpoints_dir = tmp_path / "checkpoints"
    _record_smoke_transport(checkpoints_dir, max_frames=10, checkpoint_interval=10)

    window = play(checkpoints_dir, from_frame=0, to_frame=10, backend="offscreen", max_frames=1)

    lines = [child for child in window.scene.children if isinstance(child, gfx.Line)]
    meshes = [child for child in window.scene.children if isinstance(child, gfx.Mesh)]

    assert any(len(line.geometry.positions.data) > 2 for line in lines), "no arrows found"
    assert any(len(mesh.geometry.positions.data) > 128 for mesh in meshes), "no field panel found"


def test_play_rejects_a_config_with_no_solved_velocity(tmp_path: Path) -> None:
    """The scope boundary `playback.py`'s own docstring names -- a
    solved velocity field is required -- checked against a real
    declared-field-only recording (Heat Diffusion, no
    `simulation.velocity_solved`), not a config combining a solved
    velocity field with declared fields (Smoke Transport's own shape,
    which TASK-051 made supported rather than rejected).
    """
    checkpoints_dir = tmp_path / "checkpoints"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "record",
            "--config",
            "examples/golden-demos/heat_diffusion.yaml",
            "--max-frames",
            "5",
            "--output-dir",
            str(checkpoints_dir),
            "--checkpoint-interval",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    play_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "play",
            "--checkpoints-dir",
            str(checkpoints_dir),
            "--to-frame",
            "5",
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert play_result.returncode != 0
    assert "requires a solved velocity field" in play_result.stderr


def test_play_requires_checkpoints_dir_and_to_frame() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "play"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--checkpoints-dir" in result.stderr


def _frame_hash(image: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()


# A safety backstop, not the intended way this test ends -- if pausing or
# the Escape injection below never fires (a genuine bug), the window
# still closes on its own after this many frames rather than hanging the
# suite forever. Comfortably past the frame (12) the test expects to
# reach under normal operation.
_SAFETY_MAX_FRAMES = 50


@_needs_a_real_display
def test_space_pauses_playback_live(tmp_path: Path) -> None:
    """A real glfw window: inject Space early, and prove the rendered
    frame stops changing while paused -- not just that `PlaybackState.
    paused` flips (`tests/unit/test_playback.py` already proves that in
    isolation), but that pausing actually freezes what's on screen,
    through the real keyboard-event wiring `play()`'s own `_on_key`
    registers via `canvas.add_event_handler`.
    """
    checkpoints_dir = tmp_path / "checkpoints"
    _record_cavity(checkpoints_dir, max_frames=30, checkpoint_interval=30)

    hashes: list[str] = []
    paused_at: int | None = None

    def _on_frame(window: RenderWindow) -> None:
        nonlocal paused_at
        assert window.playback_state is not None
        hashes.append(_frame_hash(np.asarray(window.renderer.snapshot())))
        if window.frame_count == 4 and paused_at is None:
            paused_at = len(hashes)
            window.canvas.submit_event({"event_type": "key_down", "key": " "})
        if window.frame_count == 12:
            window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})

    window = play(
        checkpoints_dir,
        from_frame=0,
        to_frame=30,
        backend="glfw",
        max_frames=_SAFETY_MAX_FRAMES,
        on_frame=_on_frame,
    )

    assert window.canvas.get_closed()
    assert paused_at is not None, "never reached frame 4 to inject the pause key"
    assert window.frame_count < _SAFETY_MAX_FRAMES, "Escape injection never closed the window"
    # Every frame hash from the one right after pausing onward must be
    # identical -- the materialized frame index stopped advancing.
    # `paused_at` itself (and it alone, confirmed empirically) still
    # differs from what follows: the key event submitted during frame
    # 4's own callback is queued, not processed synchronously, so it
    # takes effect starting from the *next* frame's advance rather than
    # retroactively on the frame already in flight -- one real frame of
    # event-queue latency, not a bug in `playback.py`'s own pause logic.
    post_pause = hashes[paused_at + 1 :]
    assert len(post_pause) >= 3, "not enough frames rendered after pausing to prove anything"
    assert len(set(post_pause)) == 1, "frames kept changing after Space was pressed"


# A generous per-step margin for the two scrub tests below -- wider than
# the single-frame latency `test_space_pauses_playback_live` established,
# since each step here reads the *settled* value right before the next
# key lands rather than the very next frame. Comfortably inside
# `_SCRUB_SAFETY_MAX_FRAMES`.
_SCRUB_STEP_FRAMES = 8
_SCRUB_SAFETY_MAX_FRAMES = 100


@_needs_a_real_display
def test_arrow_and_home_end_keys_seek_playback_live(tmp_path: Path) -> None:
    """Real glfw window, genuine injected key events -- proves Left/
    Right/Home/End actually move `PlaybackState.position` through the
    real keyboard wiring `play()`'s own `_on_key` registers, not just in
    isolation (`tests/unit/test_playback.py` already proves the pure
    `seek_relative`/`seek_to` functions). Paused first so the ordinary
    per-frame `speed` advance can't mix into the numbers being checked;
    each assertion reads the settled value one full step *before* the
    next key is submitted, not the frame right after the previous one.
    """
    checkpoints_dir = tmp_path / "checkpoints"
    _record_cavity(checkpoints_dir, max_frames=30, checkpoint_interval=30)

    step = _SCRUB_STEP_FRAMES
    settled: dict[str, float] = {}
    injected: set[str] = set()

    def _on_frame(window: RenderWindow) -> None:
        assert window.playback_state is not None
        position = window.playback_state.position
        frame = window.frame_count

        if frame == step and "pause" not in injected:
            injected.add("pause")
            window.canvas.submit_event({"event_type": "key_down", "key": " "})
        elif frame == 2 * step:
            settled["after_pause"] = position
            injected.add("right")
            window.canvas.submit_event({"event_type": "key_down", "key": "ArrowRight"})
        elif frame == 3 * step:
            settled["after_right"] = position
            injected.add("right2")
            window.canvas.submit_event({"event_type": "key_down", "key": "ArrowRight"})
        elif frame == 4 * step:
            settled["after_right2"] = position
            injected.add("end")
            window.canvas.submit_event({"event_type": "key_down", "key": "End"})
        elif frame == 5 * step:
            settled["after_end"] = position
            injected.add("home")
            window.canvas.submit_event({"event_type": "key_down", "key": "Home"})
        elif frame == 6 * step:
            settled["after_home"] = position
            window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})

    window = play(
        checkpoints_dir,
        from_frame=0,
        to_frame=30,
        backend="glfw",
        max_frames=_SCRUB_SAFETY_MAX_FRAMES,
        on_frame=_on_frame,
    )

    assert window.canvas.get_closed()
    assert injected == {"pause", "right", "right2", "end", "home"}, injected
    assert window.frame_count < _SCRUB_SAFETY_MAX_FRAMES, "Escape injection never closed the window"
    # Pause freezes wherever autoplay (`speed=1.0`/frame, unpaused for
    # the first `step` frames) already reached, rather than resetting to
    # 0 -- confirmed directly (not assumed) by logging every frame's own
    # position/paused pair before writing these numbers down: position
    # tracks frame count exactly (1.0/frame) through frame `step`, then
    # freezes at exactly `step` starting the frame right after pause is
    # submitted, the same one-frame latency `test_space_pauses_
    # playback_live` above already established.
    assert settled["after_pause"] == float(step)
    assert settled["after_right"] == step + 1.0
    assert settled["after_right2"] == step + 2.0
    assert settled["after_end"] == 30.0
    assert settled["after_home"] == 0.0


def _world_to_screen(
    camera: gfx.OrthographicCamera,
    logical_width: float,
    logical_height: float,
    world_x: float,
    world_y: float,
) -> tuple[float, float]:
    """The inverse of `pyflow.rendering.window.screen_to_world`, built
    here rather than imported -- inverting the transform under test
    would hide a bug in the transform itself rather than exercise it.
    """
    visible_width, visible_height = visible_world_size(camera, logical_width, logical_height)
    center_x, center_y, _center_z = camera.local.position
    screen_x = (world_x - center_x + visible_width / 2) / visible_width * logical_width
    screen_y = (center_y + visible_height / 2 - world_y) / visible_height * logical_height
    return (screen_x, screen_y)


@_needs_a_real_display
def test_dragging_the_scrub_bar_seeks_without_panning_the_camera(tmp_path: Path) -> None:
    """The core risk this task started from: `RenderWindow.run`'s own
    camera-pan pointer handlers are registered on the very same canvas.
    A drag that starts on the scrub bar must move `PlaybackState.
    position` and must **not** also pan the camera -- proven directly on
    both counts, through the real pointer-event wiring, not assumed from
    reading `stop_propagation`'s own documentation.

    The bar's own world y is read back from the live `gfx.Points` thumb
    `play()` actually builds (scene contents, the same "reach into the
    real object" technique `tests/unit/test_hud.py` already uses) rather
    than recomputed from `playback.py`'s own private layout constants --
    recomputing the layout would risk the test and the code sharing the
    same mistake instead of checking one against the other.
    """
    checkpoints_dir = tmp_path / "checkpoints"
    _record_cavity(checkpoints_dir, max_frames=30, checkpoint_interval=30)
    checkpoint = read_checkpoint(checkpoints_dir / "checkpoint_00000000.pt")
    mesh = StructuredCartesianMesh.from_config(checkpoint.config.mesh)
    mesh_min_x, _mesh_min_y, mesh_max_x, _mesh_max_y = mesh_bounding_box(mesh)
    mesh_width = mesh_max_x - mesh_min_x

    step = _SCRUB_STEP_FRAMES
    found: dict[str, object] = {}
    injected: set[str] = set()

    def _on_frame(window: RenderWindow) -> None:
        assert window.playback_state is not None
        logical_width, logical_height = window.canvas.get_logical_size()
        frame = window.frame_count

        if "bar_y" not in found:
            thumb = next(child for child in window.scene.children if isinstance(child, gfx.Points))
            _thumb_x, bar_y, _z = thumb.geometry.positions.data[0]
            found["bar_y"] = float(bar_y)
            found["camera_before"] = tuple(window.camera.local.position)

        bar_y = found["bar_y"]
        assert isinstance(bar_y, float)

        # Paused first (as the keyboard test above does) so the ordinary
        # per-frame `speed` advance can't drift the position the drag
        # itself sets while later steps are still settling.
        if frame == step and "pause" not in injected:
            injected.add("pause")
            window.canvas.submit_event({"event_type": "key_down", "key": " "})
        elif frame == 2 * step and "down" not in injected:
            injected.add("down")
            screen_x, screen_y = _world_to_screen(
                window.camera, logical_width, logical_height, mesh_min_x + 0.2 * mesh_width, bar_y
            )
            found["last_screen_pos"] = (screen_x, screen_y)
            window.canvas.submit_event(
                {"event_type": "pointer_down", "x": screen_x, "y": screen_y, "button": 1}
            )
        elif frame == 3 * step and "move" not in injected:
            injected.add("move")
            screen_x, screen_y = _world_to_screen(
                window.camera, logical_width, logical_height, mesh_min_x + 0.8 * mesh_width, bar_y
            )
            found["last_screen_pos"] = (screen_x, screen_y)
            window.canvas.submit_event(
                {"event_type": "pointer_move", "x": screen_x, "y": screen_y, "buttons": (1,)}
            )
        elif frame == 4 * step and "up" not in injected:
            injected.add("up")
            last_screen_pos = found["last_screen_pos"]
            assert isinstance(last_screen_pos, tuple)
            screen_x, screen_y = last_screen_pos
            window.canvas.submit_event(
                {"event_type": "pointer_up", "x": screen_x, "y": screen_y, "button": 1}
            )
        elif frame == 5 * step:
            found["position_after"] = window.playback_state.position
            found["camera_after"] = tuple(window.camera.local.position)
            window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})

    window = play(
        checkpoints_dir,
        from_frame=0,
        to_frame=30,
        backend="glfw",
        max_frames=_SCRUB_SAFETY_MAX_FRAMES,
        on_frame=_on_frame,
    )

    assert window.canvas.get_closed()
    assert injected == {"pause", "down", "move", "up"}, injected
    # The drag moved to 80% of the bar's own extent -> frame 24 (30 * 0.8),
    # exact now that autoplay can't drift it between steps.
    assert found["position_after"] == pytest.approx(24.0, abs=1.0)
    # The camera must not have moved at all -- the scrub drag's own
    # `stop_propagation` kept `RenderWindow.run`'s pan handlers from ever
    # starting a pan for this gesture.
    assert found["camera_after"] == found["camera_before"]


# Stage 8 Completion Criterion 6's second bullet asks for the two scrub
# paths checked "against real rendered pixels, the same way Space's own
# pause already is". **The three helpers and two tests below were added
# 2026-09-11 by the Stage 8 exit audit**, which found that bullet marked
# Met against two tests (above) that assert only on `PlaybackState.
# position` and never call `snapshot()` at all.
#
# **Two false starts are recorded here because each one passed against a
# deliberately broken renderer, and the shape of the mistake is the
# useful part.**
#
# 1. *"The pixels changed after seeking"* proves nothing: the scrub
#    thumb moves with the index, so any index change repaints something
#    whether or not the field was rebuilt underneath it.
# 2. *"A seek-reached frame matches an autoplay-reached frame at the
#    same index"* -- the obvious repair -- proves almost nothing either,
#    and this one actually had to be mutation-tested to see it. Freezing
#    the field (`_rebuild_arrows(0)`/`_rebuild_panels(0)`, thumb left
#    working) leaves *both* sides of that comparison equally frozen, so
#    they still match. A reference computed by the same run cannot
#    detect a fault common to the whole run.
#
# So the reference comes from **a separate `play()` window launched at
# the target frame** (`_reference_field_hash`), where that frame is
# index 0 and therefore rendered by the initial scene build rather than
# by the seek path at all -- and the comparison is over the **field
# region only** (`_field_region_hash`), cropping away the scrub bar,
# which `playback.py` draws below `mesh_min_y` and which would otherwise
# reintroduce exactly the thumb-moved-so-pixels-changed confound from
# (1). Both tests were re-run against the same frozen-field mutation and
# confirmed to fail before being trusted green.
#
# One timing fact the helpers depend on: **`snapshot()` is one frame
# behind `position`.** `play()`'s own `_on_frame` advances the position,
# rebuilds the scene, and only then invokes this callback -- all before
# the canvas presents anything -- so the image read back while
# `position` reads N is the rendering of frame N-1. Established
# empirically by logging `(frame_count, position, hash)` against a plain
# autoplay run, not inferred from reading `playback.py`.
def _field_region_hash(window: RenderWindow, mesh_bounds: tuple[float, float, float, float]) -> str:
    """Hash only the rows of `snapshot()` above the mesh's own bottom
    edge -- the field and its arrows, never the scrub bar.

    `playback.py` puts the bar at `mesh_min_y - mesh_height * 0.08`, so
    cropping at `mesh_min_y` excludes the bar and its thumb entirely
    while keeping every pixel the field itself can touch.
    """
    logical_width, logical_height = window.canvas.get_logical_size()
    mesh_min_x, mesh_min_y, _mesh_max_x, _mesh_max_y = mesh_bounds
    _screen_x, screen_y = _world_to_screen(
        window.camera, logical_width, logical_height, mesh_min_x, mesh_min_y
    )

    image = np.asarray(window.renderer.snapshot())
    # `snapshot()` is in physical pixels and `_world_to_screen` returns
    # logical ones, so convert through a fraction of the height rather
    # than assuming the two are the same scale.
    cut = int(round((screen_y / logical_height) * image.shape[0]))
    cut = max(1, min(cut, image.shape[0]))
    return _frame_hash(image[:cut])


def _reference_field_hash(
    checkpoints_dir: Path, frame: int, mesh_bounds: tuple[float, float, float, float]
) -> str:
    """The field region of absolute `frame`, rendered by a *separate*
    `play()` window that starts there.

    In that window `frame` is index 0, so it is drawn by the initial
    scene build and never by a seek or an advance -- which is what makes
    it an independent reference rather than a second reading of the same
    possibly-broken path.
    """
    captured: dict[str, str] = {}

    def _on_frame(window: RenderWindow) -> None:
        if "hash" not in captured:
            captured["hash"] = _field_region_hash(window, mesh_bounds)
            window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})

    play(
        checkpoints_dir,
        from_frame=frame,
        to_frame=frame + 1,
        backend="glfw",
        max_frames=_SCRUB_SAFETY_MAX_FRAMES,
        on_frame=_on_frame,
    )
    assert "hash" in captured, "reference window never rendered a frame"
    return captured["hash"]


@_needs_a_real_display
def test_keyboard_seeking_rerenders_the_field_in_real_pixels(tmp_path: Path) -> None:
    """ArrowLeft, through the real key wiring, against a real window."""
    checkpoints_dir = tmp_path / "checkpoints"
    _record_cavity_without_stats(tmp_path, checkpoints_dir, max_frames=30, checkpoint_interval=30)
    checkpoint = read_checkpoint(checkpoints_dir / "checkpoint_00000000.pt")
    mesh_bounds = mesh_bounding_box(StructuredCartesianMesh.from_config(checkpoint.config.mesh))

    step = _SCRUB_STEP_FRAMES
    seen: dict[str, object] = {}
    injected: set[str] = set()

    def _on_frame(window: RenderWindow) -> None:
        assert window.playback_state is not None
        index = int(window.playback_state.position)
        frame = window.frame_count

        if frame == step and "pause" not in injected:
            injected.add("pause")
            window.canvas.submit_event({"event_type": "key_down", "key": " "})
        elif frame == 2 * step and "left" not in injected:
            seen["paused_index"] = index
            seen["paused_hash"] = _field_region_hash(window, mesh_bounds)
            injected.add("left")
            window.canvas.submit_event({"event_type": "key_down", "key": "ArrowLeft"})
        elif frame == 3 * step:
            # One frame behind `position`, so the settled image here
            # depicts `index`, which has not moved for a whole step.
            seen["sought_index"] = index
            seen["sought_hash"] = _field_region_hash(window, mesh_bounds)
            window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})

    window = play(
        checkpoints_dir,
        from_frame=0,
        to_frame=30,
        backend="glfw",
        max_frames=_SCRUB_SAFETY_MAX_FRAMES,
        on_frame=_on_frame,
    )

    assert window.canvas.get_closed()
    assert injected == {"pause", "left"}, injected

    paused_index = seen["paused_index"]
    sought_index = seen["sought_index"]
    assert isinstance(paused_index, int) and isinstance(sought_index, int)
    assert sought_index == paused_index - 1, (paused_index, sought_index)

    # The weak half: the rendered field moved at all. Already stronger
    # than a whole-frame hash, since the thumb is cropped out.
    assert seen["sought_hash"] != seen["paused_hash"], (
        "ArrowLeft left the rendered field byte-identical"
    )
    # The strong half: it is the genuine rendering of that frame,
    # according to a window that never seeked.
    assert seen["sought_hash"] == _reference_field_hash(
        checkpoints_dir, sought_index, mesh_bounds
    ), (
        f"ArrowLeft moved position to {sought_index} but rendered a different field "
        "than a fresh window started at that frame"
    )


@_needs_a_real_display
def test_dragging_the_scrub_bar_rerenders_the_field_in_real_pixels(tmp_path: Path) -> None:
    """The same check for the mouse path, through real pointer events."""
    checkpoints_dir = tmp_path / "checkpoints"
    _record_cavity_without_stats(tmp_path, checkpoints_dir, max_frames=30, checkpoint_interval=30)
    checkpoint = read_checkpoint(checkpoints_dir / "checkpoint_00000000.pt")
    mesh_bounds = mesh_bounding_box(StructuredCartesianMesh.from_config(checkpoint.config.mesh))
    mesh_min_x, _mesh_min_y, mesh_max_x, _mesh_max_y = mesh_bounds
    mesh_width = mesh_max_x - mesh_min_x

    step = _SCRUB_STEP_FRAMES
    max_index = 30
    target_index = 21

    seen: dict[str, object] = {}
    injected: set[str] = set()

    def _on_frame(window: RenderWindow) -> None:
        assert window.playback_state is not None
        index = int(window.playback_state.position)
        frame = window.frame_count
        logical_width, logical_height = window.canvas.get_logical_size()

        if "bar_y" not in seen:
            thumb = next(child for child in window.scene.children if isinstance(child, gfx.Points))
            _thumb_x, bar_y, _z = thumb.geometry.positions.data[0]
            seen["bar_y"] = float(bar_y)

        bar_y = seen["bar_y"]
        assert isinstance(bar_y, float)
        target_x = mesh_min_x + (target_index / max_index) * mesh_width

        if frame == step and "pause" not in injected:
            injected.add("pause")
            window.canvas.submit_event({"event_type": "key_down", "key": " "})
        elif frame == 2 * step and "down" not in injected:
            seen["paused_hash"] = _field_region_hash(window, mesh_bounds)
            injected.add("down")
            screen_x, screen_y = _world_to_screen(
                window.camera, logical_width, logical_height, target_x, bar_y
            )
            seen["screen_pos"] = (screen_x, screen_y)
            window.canvas.submit_event(
                {"event_type": "pointer_down", "x": screen_x, "y": screen_y, "button": 1}
            )
        elif frame == 3 * step and "up" not in injected:
            injected.add("up")
            screen_pos = seen["screen_pos"]
            assert isinstance(screen_pos, tuple)
            screen_x, screen_y = screen_pos
            window.canvas.submit_event(
                {"event_type": "pointer_up", "x": screen_x, "y": screen_y, "button": 1}
            )
        elif frame == 4 * step:
            seen["dragged_index"] = index
            seen["dragged_hash"] = _field_region_hash(window, mesh_bounds)
            window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})

    window = play(
        checkpoints_dir,
        from_frame=0,
        to_frame=max_index,
        backend="glfw",
        max_frames=_SCRUB_SAFETY_MAX_FRAMES,
        on_frame=_on_frame,
    )

    assert window.canvas.get_closed()
    assert injected == {"pause", "down", "up"}, injected
    assert seen["dragged_index"] == target_index, seen["dragged_index"]

    assert seen["dragged_hash"] != seen["paused_hash"], (
        "the scrub drag left the rendered field byte-identical"
    )
    assert seen["dragged_hash"] == _reference_field_hash(
        checkpoints_dir, target_index, mesh_bounds
    ), (
        f"the drag moved position to {target_index} but rendered a different field "
        "than a fresh window started at that frame"
    )


def test_play_help_documents_every_window_control() -> None:
    """`pyflow play --help` must name the controls the subcommand exists
    for, and say where seeking stops.

    **Added 2026-09-11 by the Stage 8 exit audit**, which found pause,
    speed and scrub -- everything TASK-047 and TASK-048 built -- absent
    from `--help` entirely, discoverable only by reading `README.md`.
    Root `CLAUDE.md`'s Feature Verification rule asks for exactly this
    check ("confirm every new CLI flag actually appears in `--help`");
    the controls are not flags, but they are the same promise.

    The bounded-seek line is asserted too, because it is the one place a
    user is told that Home/End stop at the loaded window rather than at
    the recording's own ends -- Stage 8's own stated scope boundary, and
    the thing most likely to read as a bug without it.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "play", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    for control in ("Space", "+ / -", "Left / Right", "Home / End", "drag scrub bar"):
        assert control in result.stdout, f"{control!r} missing from pyflow play --help"
    assert "loaded window only" in result.stdout
