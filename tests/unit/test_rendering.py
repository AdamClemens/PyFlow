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


def test_render_window_applies_configured_background_color() -> None:
    config = RenderingConfig(backend="offscreen", width=16, height=16, background_color="#1a1a2e")
    window = RenderWindow(config)

    window.run(max_frames=1)

    assert window.last_image is not None
    expected = [0x1A, 0x1A, 0x2E, 0xFF]
    assert (window.last_image == expected).all()


def test_render_window_with_no_background_color_is_transparent() -> None:
    config = RenderingConfig(backend="offscreen", width=16, height=16)
    window = RenderWindow(config)

    window.run(max_frames=1)

    assert window.last_image is not None
    assert (window.last_image[..., 3] == 0).all()  # fully transparent alpha


def test_apply_camera_config_sets_zoom() -> None:
    config = RenderingConfig(backend="offscreen", zoom=2.5, zoom_min=0.1, zoom_max=10.0)
    window = RenderWindow(config)

    window.apply_camera_config()

    assert window.camera.zoom == 2.5


def test_apply_camera_config_offsets_position_by_configured_pan() -> None:
    config = RenderingConfig(backend="offscreen", pan=(1.5, -0.5))
    window = RenderWindow(config)
    window.camera.local.position = (10.0, 20.0, 1.0)  # simulate prior mesh-fit framing

    window.apply_camera_config()

    x, y, z = window.camera.local.position
    assert (x, y, z) == pytest.approx((11.5, 19.5, 1.0))


def test_wheel_zoom_with_zero_dy_is_a_no_op() -> None:
    config = RenderingConfig(backend="offscreen", zoom=1.0, zoom_min=0.1, zoom_max=10.0)
    window = RenderWindow(config)

    window._handle_wheel_zoom(dy=0.0)

    assert window.camera.zoom == 1.0


def test_wheel_zoom_in_increases_zoom_within_bounds() -> None:
    config = RenderingConfig(backend="offscreen", zoom=1.0, zoom_min=0.1, zoom_max=10.0)
    window = RenderWindow(config)

    window._handle_wheel_zoom(dy=-1.0)  # negative dy: zoom in, by this module's convention

    assert window.camera.zoom > 1.0


def test_wheel_zoom_out_decreases_zoom_within_bounds() -> None:
    config = RenderingConfig(backend="offscreen", zoom=1.0, zoom_min=0.1, zoom_max=10.0)
    window = RenderWindow(config)

    window._handle_wheel_zoom(dy=1.0)

    assert window.camera.zoom < 1.0


def test_wheel_zoom_is_clamped_to_configured_bounds() -> None:
    config = RenderingConfig(backend="offscreen", zoom=9.9, zoom_min=0.1, zoom_max=10.0)
    window = RenderWindow(config)

    for _ in range(50):
        window._handle_wheel_zoom(dy=-1.0)
    assert window.camera.zoom == pytest.approx(10.0)

    for _ in range(200):
        window._handle_wheel_zoom(dy=1.0)
    assert window.camera.zoom == pytest.approx(0.1)


def test_pointer_drag_pans_the_camera_following_the_cursor() -> None:
    config = RenderingConfig(backend="offscreen", width=400, height=300)
    window = RenderWindow(config)
    window.camera.width = 4.0
    window.camera.height = 3.0
    window.camera.local.position = (0.0, 0.0, 1.0)

    window._begin_pan(x=100.0, y=100.0)
    window._update_pan(x=200.0, y=150.0)  # dragged +100px right, +50px down

    x, y, z = window.camera.local.position
    # 100 world-space px-to-unit at zoom=1: 400px/4.0units = 100px/unit (x),
    # 300px/3.0units = 100px/unit (y). Dragging right/down should make the
    # *content* follow the cursor (verified empirically, see
    # rendering/CLAUDE.md): camera x decreases, camera y increases.
    assert (x, y, z) == pytest.approx((-1.0, 0.5, 1.0))


def test_pointer_drag_does_nothing_before_a_drag_begins() -> None:
    config = RenderingConfig(backend="offscreen")
    window = RenderWindow(config)
    original_position = tuple(window.camera.local.position)

    window._update_pan(x=50.0, y=50.0)

    assert tuple(window.camera.local.position) == original_position


def test_pointer_drag_stops_after_end_pan() -> None:
    config = RenderingConfig(backend="offscreen", width=400, height=300)
    window = RenderWindow(config)
    window.camera.width = 4.0
    window.camera.height = 3.0

    window._begin_pan(x=0.0, y=0.0)
    window._end_pan()
    position_after_end = tuple(window.camera.local.position)
    window._update_pan(x=999.0, y=999.0)

    assert tuple(window.camera.local.position) == position_after_end
