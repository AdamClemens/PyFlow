"""Acceptance tests for the interactive (glfw) window path.

Everything here needs a real OS window system, unlike the rest of the
automated suite (see `tests/unit/CLAUDE.md` and
`src/pyflow/rendering/CLAUDE.md`): the interactive backend was
previously verified only by hand, with the verification command written
down for a maintainer to re-run locally. `_display_available()` below
turns that manual command into a real, automated skip-guard instead --
these tests run for real wherever a display exists (this development
machine included) and skip cleanly wherever one doesn't (headless CI),
rather than being red on every push or silently untested forever.
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

from pyflow.configuration import RenderingConfig
from pyflow.rendering import RenderWindow
from pyflow.rendering.canvas import get_loop


def _display_available() -> bool:
    # A genuinely headless Linux machine (no DISPLAY, no WAYLAND_DISPLAY --
    # ubuntu-latest's real state, confirmed on GitHub Actions 2026-08-19)
    # must be ruled out *before* GlfwRenderCanvas is ever constructed.
    # GLFW's native code doesn't fail there with a catchable Python
    # exception -- it hard-aborts the whole process (`Fatal Python error:
    # Aborted`, a real SIGABRT inside glfwSetFramebufferSizeCallback),
    # which no `except Exception` below can catch. This was never
    # reproducible locally: this dev machine always has a display.
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


def test_display_probe_skips_glfw_when_no_display_env_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test (2026-08-19): the previous `_display_available()`
    called straight into `GlfwRenderCanvas` with no display-server check
    first. On real headless Ubuntu CI that crashed the whole process with
    a native SIGABRT no `except Exception` can catch -- never reproducible
    locally, since this dev machine always has a display. The fix checks
    `DISPLAY`/`WAYLAND_DISPLAY` before touching `rendercanvas.glfw` at
    all. Proven here, on any platform, by making `GlfwRenderCanvas` raise
    something `except Exception` deliberately would *not* catch --
    standing in for the real SIGABRT -- so if the guard is ever removed
    or broken, this fails loudly instead of silently passing. Not
    decorated with `_needs_a_real_display`: this must run precisely where
    there is no display, which is the case it exists to cover.
    """

    class _WouldHaveCrashed(BaseException):
        pass

    def _boom(*args: object, **kwargs: object) -> None:
        raise _WouldHaveCrashed("the DISPLAY/WAYLAND_DISPLAY guard did not short-circuit")

    import rendercanvas.glfw

    monkeypatch.setattr(rendercanvas.glfw, "GlfwRenderCanvas", _boom)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    assert _display_available() is False


def _frame_hash(image: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()


@_needs_a_real_display
def test_pyflow_run_opens_an_interactive_window_and_exits_cleanly(tmp_path: Path) -> None:
    """`pyflow run` through the real CLI, with the default interactive
    (glfw) backend -- the literal command a user types, not the
    `--backend offscreen` override every other integration test uses to
    stay headless. `--max-frames` stands in for a user clicking close,
    since a test has no user to do that.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: glfw\n  width: 64\n  height: 64\n")

    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "run", "--config", str(config_file), "--max-frames", "5"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "render window closed: 5 frame(s)" in result.stderr


@_needs_a_real_display
def test_render_window_presents_distinct_frames() -> None:
    """A real glfw window, redrawn several times, actually presents
    different pixel content frame to frame -- not `frame_count`
    incrementing while the same buffer is redrawn or re-presented.

    Stage 0's own scene has no animated content (no simulation yet --
    see `RenderWindow`'s own docstring), so `pyflow run` as shipped
    can't demonstrate changing frames on its own. This test adds a small
    mesh whose material colour changes every frame, through the public
    `self.scene` extension point RenderWindow's docstring already
    sanctions, and the `on_frame` hook added specifically to let a
    caller observe (and mutate) state each frame.
    """
    config = RenderingConfig(backend="glfw", width=32, height=32)
    window = RenderWindow(config)

    mesh = gfx.Mesh(gfx.box_geometry(1, 1, 1), gfx.MeshBasicMaterial(color="#ff0000"))
    window.scene.add(mesh)

    hashes: list[str] = []

    def on_frame() -> None:
        hashes.append(_frame_hash(np.asarray(window.renderer.snapshot())))
        shade = window.frame_count / 5
        mesh.material.color = (shade, 0.0, 1.0 - shade, 1.0)

    window.run(max_frames=5, on_frame=on_frame)

    assert window.frame_count == 5
    assert window.canvas.get_closed()
    assert len(hashes) == 5
    assert len(set(hashes)) > 1, "all 5 presented frames were pixel-identical"


@_needs_a_real_display
def test_close_key_terminates_the_render_loop_and_process_cleanly() -> None:
    """Pressing Escape closes the window and lets the process exit --
    the only way an interactive PyFlow window closes short of killing
    the process (see `_DEFAULT_CLOSE_KEYS` in
    `src/pyflow/rendering/window.py`).

    Automates the manual verification recipe recorded in
    `src/pyflow/rendering/CLAUDE.md`: a synthetic Escape `key_down` is
    scheduled on the real event loop while `window.run()` is genuinely
    blocking (no `max_frames`), so this only passes if the window keeps
    repainting *and* actually responds to the key -- not if `run()`
    happens to return some other way.
    """
    config = RenderingConfig(backend="glfw", width=32, height=32)
    window = RenderWindow(config)
    loop = get_loop(config)

    loop.call_later(
        0.5, lambda: window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})
    )

    window.run()  # no max_frames: only the injected key should end this

    assert window.canvas.get_closed()
    # A handful of frames at minimum over the 0.5s wait -- proves the
    # window was actually live and repainting, not frozen on frame 1
    # until the key handler fired.
    assert window.frame_count > 2


@_needs_a_real_display
def test_wheel_event_zooms_the_camera_live() -> None:
    """Live zoom (TASK-013): a real scroll-wheel event, injected into a
    genuinely blocking `run()` exactly like the close-key test above,
    changes `camera.zoom` -- not just `RenderWindow._handle_wheel_zoom`
    called directly (already covered by `tests/unit/test_rendering.py`),
    but the actual `canvas.add_event_handler(..., "wheel")` wiring.
    """
    config = RenderingConfig(backend="glfw", width=32, height=32)
    window = RenderWindow(config)
    loop = get_loop(config)
    initial_zoom = window.camera.zoom

    loop.call_later(
        0.3, lambda: window.canvas.submit_event({"event_type": "wheel", "dx": 0.0, "dy": -1.0})
    )
    loop.call_later(
        0.6, lambda: window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})
    )

    window.run()

    assert window.canvas.get_closed()
    assert window.camera.zoom > initial_zoom


@_needs_a_real_display
def test_pointer_drag_pans_the_camera_live() -> None:
    """Live pan (TASK-013): a real pointer_down/move/up sequence,
    injected the same way, moves `camera.local.position` -- the actual
    `add_event_handler` wiring, not just `_begin_pan`/`_update_pan`
    called directly (already covered by `tests/unit/test_rendering.py`).
    """
    config = RenderingConfig(backend="glfw", width=32, height=32)
    window = RenderWindow(config)
    loop = get_loop(config)
    initial_position = tuple(window.camera.local.position)

    def _drag() -> None:
        window.canvas.submit_event(
            {"event_type": "pointer_down", "x": 10.0, "y": 10.0, "button": 1, "buttons": (1,)}
        )
        window.canvas.submit_event(
            {"event_type": "pointer_move", "x": 20.0, "y": 15.0, "button": 0, "buttons": (1,)}
        )
        window.canvas.submit_event(
            {"event_type": "pointer_up", "x": 20.0, "y": 15.0, "button": 1, "buttons": ()}
        )

    loop.call_later(0.3, _drag)
    loop.call_later(
        0.6, lambda: window.canvas.submit_event({"event_type": "key_down", "key": "Escape"})
    )

    window.run()

    assert window.canvas.get_closed()
    assert tuple(window.camera.local.position) != initial_position
