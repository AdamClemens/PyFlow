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
import pytest

from pyflow.playback import play
from pyflow.rendering.window import RenderWindow


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


def test_play_rejects_a_config_it_does_not_support(tmp_path: Path) -> None:
    """The scope boundary `playback.py`'s own docstring names --
    solved-velocity only -- checked against a real declared-field
    recording (Heat Diffusion), not a velocity-only one.
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
    assert "solved-velocity-only" in play_result.stderr


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
