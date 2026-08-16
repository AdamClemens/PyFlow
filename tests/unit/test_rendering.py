"""Unit tests for pyflow.rendering (TASK-007).

Offscreen backend only -- it's the one that works everywhere, including
headless CI (backlog D3/D5); the interactive glfw backend needs a real
display and is exercised manually via `make demo`, not in the automated
suite.
"""

import pytest

from pyflow.configuration import RenderingConfig
from pyflow.rendering import RenderWindow
from pyflow.rendering.canvas import create_canvas, get_loop


def test_create_canvas_offscreen() -> None:
    config = RenderingConfig(backend="offscreen", width=320, height=240)
    canvas = create_canvas(config)
    assert canvas.get_logical_size() == (320, 240)


def test_create_canvas_rejects_unknown_backend() -> None:
    config = RenderingConfig(backend="offscreen")
    config.backend = "not-a-backend"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="unknown rendering backend"):
        create_canvas(config)


def test_get_loop_offscreen_has_none() -> None:
    config = RenderingConfig(backend="offscreen")
    with pytest.raises(ValueError, match="no event loop"):
        get_loop(config)


def test_render_window_opens_updates_and_closes() -> None:
    config = RenderingConfig(backend="offscreen", width=64, height=64)
    window = RenderWindow(config)

    assert window.frame_count == 0
    window.run(max_frames=3)

    assert window.frame_count == 3
    assert window.canvas.get_closed()


def test_render_window_default_single_frame() -> None:
    config = RenderingConfig(backend="offscreen", width=64, height=64)
    window = RenderWindow(config)
    window.run()
    assert window.frame_count == 1


def test_render_window_captures_pixel_data() -> None:
    """A real frame gets presented, not just rendered into an unread texture.

    Guards against the D5 bug: calling `renderer.render()` without ever
    calling `canvas.draw()` renders but never presents, so `last_image`
    would silently stay `None` forever -- caught once by inspecting the
    actual array, not just checking frame_count incremented.
    """
    config = RenderingConfig(backend="offscreen", width=32, height=16)
    window = RenderWindow(config)

    assert window.last_image is None

    window.run(max_frames=1)

    assert window.last_image is not None
    assert window.last_image.shape == (16, 32, 4)
