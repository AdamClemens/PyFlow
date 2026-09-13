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
from pyflow.rendering.window import screen_to_world


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


def test_pointer_drag_follows_the_cursor_when_camera_and_canvas_aspects_differ() -> None:
    """Regression test (2026-08-21 audit). `pygfx.OrthographicCamera`
    defaults to `maintain_aspect=True`, so the *visible* world extent is
    not `camera.width`/`camera.height` -- pygfx expands whichever axis is
    narrower than the viewport (`_update_projection_matrix`). Panning
    computed from `camera.width` alone therefore under-tracks the cursor
    by exactly the aspect mismatch.

    The test above uses a 4:3 camera on a 4:3 canvas, which is precisely
    the case where the two agree and the bug is invisible. This one uses
    a square camera on a 16:9 canvas -- the default `pyflow run` shape,
    where `fit_camera_to_mesh` frames a square mesh in a 1280x720 window
    -- and asserts the drag against the extent pygfx actually projects,
    derived from the projection matrix rather than restated here.
    """
    config = RenderingConfig(backend="offscreen", width=1280, height=720)
    window = RenderWindow(config)
    window.camera.width = 12.0
    window.camera.height = 12.0
    window.camera.local.position = (0.0, 0.0, 1.0)

    # What pygfx will actually project, after its own aspect expansion.
    window.camera.set_view_size(1280, 720)
    projection = window.camera.projection_matrix
    visible_width = 2.0 / projection[0, 0]
    visible_height = 2.0 / projection[1, 1]
    assert visible_width > window.camera.width  # the mismatch this test exists for

    window._begin_pan(x=100.0, y=100.0)
    window._update_pan(x=200.0, y=150.0)  # dragged +100px right, +50px down

    x, y, z = window.camera.local.position
    expected_x = -100.0 * visible_width / 1280
    expected_y = +50.0 * visible_height / 720
    assert (x, y, z) == pytest.approx((expected_x, expected_y, 1.0))


def test_screen_to_world_maps_the_four_corners_and_center() -> None:
    """The inverse of what `_update_pan` tracks only as a *delta* -- an
    absolute screen-pixel-to-world mapping, needed by TASK-048's scrub
    bar to place a thumb and hit-test a drag. Verified against a real
    rendered marker at a known world position (`docs/CHANGELOG-DESIGN.md`,
    TASK-048) before being trusted; pinned here against the four corners
    and centre of a simple, camera-centred-on-origin case.
    """
    config = RenderingConfig(backend="offscreen", width=400, height=300)
    window = RenderWindow(config)
    window.camera.width = 4.0
    window.camera.height = 3.0
    window.camera.local.position = (0.0, 0.0, 1.0)
    logical_width, logical_height = window.canvas.get_logical_size()

    top_left = screen_to_world(window.camera, logical_width, logical_height, 0.0, 0.0)
    bottom_right = screen_to_world(window.camera, logical_width, logical_height, 400.0, 300.0)
    center = screen_to_world(window.camera, logical_width, logical_height, 200.0, 150.0)

    assert top_left == pytest.approx((-2.0, 1.5))
    assert bottom_right == pytest.approx((2.0, -1.5))
    assert center == pytest.approx((0.0, 0.0))


def test_screen_to_world_accounts_for_camera_position_and_aspect_expansion() -> None:
    """Off-centre camera, and a canvas aspect wider than the camera's own
    -- the same `maintain_aspect` expansion `visible_world_size`'s own
    docstring explains, applied to an absolute mapping rather than a
    pan delta.
    """
    config = RenderingConfig(backend="offscreen", width=200, height=100)
    window = RenderWindow(config)
    window.camera.width = 10.0
    window.camera.height = 10.0
    window.camera.local.position = (5.0, 3.0, 0.0)
    logical_width, logical_height = window.canvas.get_logical_size()

    # Matches the real-marker empirical check recorded in
    # docs/CHANGELOG-DESIGN.md: a marker rendered at world (1.0, 7.0)
    # landed at pixel (~59.5, ~9.5) in a 200x100 offscreen render.
    world_x, world_y = screen_to_world(window.camera, logical_width, logical_height, 59.5, 9.5)
    assert (world_x, world_y) == pytest.approx((1.0, 7.05), abs=0.1)


# -- A raising frame callback (TASK-053, Stage 9) ----------------------------
#
# `RenderWindow` is the seam both `pyflow run` and `pyflow play` go
# through, so these cover Criterion 4's "both window-opening subcommands"
# structurally rather than by contriving a diverging playback -- `play`
# renders pre-materialized frames, so the engine's own divergence cannot
# arise inside its frame callback at all. What can arise there is any
# error in its own scene rebuilding, and this is the mechanism that would
# carry it. `tests/integration/test_frame_failure.py` is the end-to-end
# half, against a real diverging configuration and a real exit code.


class _DeliberateFrameError(RuntimeError):
    """Distinctive, so the assertions below cannot pass on some other
    exception the rendering stack happened to raise.
    """


def test_run_reraises_whatever_the_frame_callback_raised() -> None:
    window = RenderWindow(RenderingConfig(backend="offscreen"))

    def _raise() -> None:
        raise _DeliberateFrameError("frame callback failed")

    with pytest.raises(_DeliberateFrameError):
        window.run(max_frames=5, on_frame=_raise)


def test_a_failing_frame_does_not_count_as_drawn() -> None:
    window = RenderWindow(RenderingConfig(backend="offscreen"))
    calls = 0

    def _raise_on_third() -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise _DeliberateFrameError("frame callback failed")

    with pytest.raises(_DeliberateFrameError):
        window.run(max_frames=10, on_frame=_raise_on_third)

    # Two frames completed; the third raised. `frame_count` used to be
    # incremented before `on_frame` ran, so a frame that died in the
    # simulation still counted -- which is how a failing run could report
    # a full budget.
    assert window.frame_count == 2, window.frame_count
    # And the budget was abandoned rather than run to completion.
    assert calls == 3, calls


def test_a_frame_callback_that_does_not_raise_is_unaffected() -> None:
    # The guard must not fire on a healthy run -- the other half of the
    # claim, and the one a regression would break silently.
    window = RenderWindow(RenderingConfig(backend="offscreen"))
    calls = 0

    def _count() -> None:
        nonlocal calls
        calls += 1

    window.run(max_frames=4, on_frame=_count)

    assert calls == 4
    assert window.frame_count == 4
