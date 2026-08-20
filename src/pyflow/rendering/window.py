"""Render window bootstrap: creation, render loop, clean shutdown (TASK-007).

`RenderWindow` owns the canvas, renderer, scene and camera for one
PyFlow window. It doesn't know or care which canvas backend it was given
-- `canvas.py` resolves that from configuration -- so the render loop
below is identical for an interactive glfw window and a headless
offscreen canvas.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygfx as gfx

from pyflow.configuration.schema import RenderingConfig
from pyflow.engine import get_logger
from pyflow.rendering.canvas import create_canvas, get_loop

logger = get_logger(__name__)

# The only way an interactive window closes without killing the process,
# short of hunting for the OS window's own close button -- default,
# always-on, not something each caller has to opt into. Found missing
# 2026-08-16: it had only been wired into the Empty Window golden demo,
# not here, so `pyflow run` itself -- the actual product, not just a
# demo -- opened a window with no responsive way to close it. See
# docs/planning/backlog.md D4.
_DEFAULT_CLOSE_KEYS = ("Escape", "Enter")

# Multiplicative zoom step per wheel "tick" (TASK-013). Direction
# convention (verified empirically, not assumed): negative `dy` zooms
# in. Fixed rather than derived from `dy`'s magnitude, since that varies
# by device/platform -- only its sign is used.
_WHEEL_ZOOM_FACTOR = 1.1


class RenderWindow:
    """A window (or headless canvas) with a renderer, scene and camera.

    No simulation content: TASK-007 is the rendering bootstrap only. An
    empty `pygfx.Scene()`, optionally with a configured background
    colour, is enough to exercise window creation, the render loop and
    clean shutdown, which is everything this task's acceptance criteria
    ask for. Callers can still add further content to `self.scene`
    directly before calling `run()`, but a golden demo's own visual
    identity should come from configuration (`RenderingConfig.
    background_color`), not code here -- see
    `docs/implementation/golden-demos.md`'s public-API rule.
    """

    def __init__(self, config: RenderingConfig) -> None:
        self._config = config
        self.canvas = create_canvas(config)
        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.scene = gfx.Scene()
        if config.background_color is not None:
            self.scene.add(gfx.Background(None, gfx.BackgroundMaterial(config.background_color)))
        self.camera = gfx.OrthographicCamera()
        self.frame_count = 0
        self.last_image: Any | None = None
        """The most recently rendered frame as an NxMx4 uint8 array --
        only populated for the offscreen backend, which is the only one
        `rendercanvas` gives pixel data back for (see
        `rendercanvas.offscreen.OffscreenRenderCanvas.draw`). `None` for
        interactive backends and before the first frame."""
        self._on_frame: Callable[[], None] | None = None
        self._pan_drag_start_screen: tuple[float, float] | None = None
        self._pan_drag_start_position: tuple[float, float, float] | None = None

    def apply_camera_config(self) -> None:
        """Apply `config.zoom`/`config.pan` (TASK-013) to the camera, on
        top of whatever base view is already set (e.g.
        `mesh_visualization.fit_camera_to_mesh`). `pan` is an offset
        added to the camera's *current* position, not an absolute one --
        so callers should set up any base framing first, then call this.
        """
        self.camera.zoom = self._config.zoom
        pan_x, pan_y = self._config.pan
        x, y, z = self.camera.local.position
        self.camera.local.position = (x + pan_x, y + pan_y, z)

    def _handle_wheel_zoom(self, dy: float) -> None:
        """Multiply the camera's zoom by one step per call, clamped to
        `config.zoom_min`/`config.zoom_max`. `dy < 0` zooms in, `dy > 0`
        zooms out, `dy == 0` is a no-op -- only the sign is used.
        """
        if dy == 0:
            return
        factor = _WHEEL_ZOOM_FACTOR if dy < 0 else 1 / _WHEEL_ZOOM_FACTOR
        zoom = self.camera.zoom * factor
        self.camera.zoom = min(max(zoom, self._config.zoom_min), self._config.zoom_max)

    def _begin_pan(self, x: float, y: float) -> None:
        """Start tracking a pointer-drag pan from screen position `(x, y)`."""
        self._pan_drag_start_screen = (x, y)
        self._pan_drag_start_position = tuple(self.camera.local.position)

    def _update_pan(self, x: float, y: float) -> None:
        """Move the camera so the content under the cursor follows the
        drag -- a no-op if no drag is in progress (`_begin_pan` wasn't
        called, or `_end_pan` already ended it).

        Screen-to-world conversion uses the camera's *current* view
        size, so `zoom` changing mid-drag doesn't produce a
        discontinuous jump. Signs verified empirically (not assumed):
        dragging right/down moves the camera in *negative* x / *positive*
        y respectively -- see `docs/CHANGELOG-DESIGN.md`, TASK-013.
        """
        if self._pan_drag_start_screen is None or self._pan_drag_start_position is None:
            return
        dx_screen = x - self._pan_drag_start_screen[0]
        dy_screen = y - self._pan_drag_start_screen[1]

        logical_width, logical_height = self.canvas.get_logical_size()
        world_per_px_x = self.camera.width / self.camera.zoom / logical_width
        world_per_px_y = self.camera.height / self.camera.zoom / logical_height

        start_x, start_y, z = self._pan_drag_start_position
        self.camera.local.position = (
            start_x - dx_screen * world_per_px_x,
            start_y + dy_screen * world_per_px_y,
            z,
        )

    def _end_pan(self) -> None:
        """Stop tracking the current pointer-drag pan, if any."""
        self._pan_drag_start_screen = None
        self._pan_drag_start_position = None

    def _draw(self) -> None:
        self.renderer.render(self.scene, self.camera)
        self.frame_count += 1
        if self._on_frame is not None:
            self._on_frame()

    def run(
        self,
        *,
        max_frames: int | None = None,
        close_keys: tuple[str, ...] | None = _DEFAULT_CLOSE_KEYS,
        on_frame: Callable[[], None] | None = None,
    ) -> None:
        """Run the render loop until the window closes.

        `max_frames`, if given, closes the window after that many frames
        instead of waiting for the user (or running forever) -- what
        `make demo`'s smoke check and the golden-demo regression test
        (backlog D5) both need, since neither has a user to click close.
        Interactive backends self-reschedule each draw via `request_draw`
        so the window keeps repainting until closed, which is also the
        behaviour future real-time simulation frames will need.

        `close_keys`: for interactive backends, pressing any of these
        keys closes the window -- on by default (Escape/Enter), since a
        window a user can't close without killing the process isn't
        acceptable behaviour for anything real, not just for demos. Pass
        `None` to disable (e.g. a future caller wants its own key
        handling instead). Ignored for the offscreen backend, which has
        no keyboard events to listen for.

        `on_frame`, if given, is called once per frame, immediately after
        it's rendered (so `self.frame_count` and `self.renderer.snapshot()`
        already reflect that frame). The one caller today is the
        acceptance suite (`tests/integration/test_interactive_window.py`),
        which uses it to mutate `self.scene` between frames and capture
        per-frame pixel data -- proving the render loop actually presents
        distinct frames rather than redrawing a frozen buffer. Left as a
        general hook, not a test-only seam, since it's exactly what a
        future real-time simulation loop will need too (advance
        state each frame, same as `request_draw` already advances drawing
        each frame).
        """
        self._on_frame = on_frame
        if self._config.backend == "offscreen":
            # canvas.draw() -- not `self._draw()` directly -- is what
            # actually triggers presentation and captures the frame:
            # rendercanvas's offscreen canvas only records `_last_image`
            # inside its own force_draw()/draw() machinery, which invokes
            # whatever was registered via request_draw(). Calling
            # renderer.render() directly (as an earlier version of this
            # method did) renders into the texture but is never
            # presented, so `canvas.draw()` returns nothing new -- caught
            # by actually inspecting the returned array while building
            # the Empty Window golden demo (D5), not by inspection.
            self.canvas.request_draw(self._draw)
            for _ in range(max_frames or 1):
                self.last_image = self.canvas.draw()
            self.canvas.close()
            logger.info("offscreen render complete: %d frame(s)", self.frame_count)
            return

        if close_keys:

            def _on_key(event: dict[str, Any]) -> None:
                if event.get("key") in close_keys:
                    self.canvas.close()

            self.canvas.add_event_handler(_on_key, "key_down")

        # Live camera controls (TASK-013): same `add_event_handler`
        # mechanism as `close_keys` above, not a different one. Only
        # meaningful on an interactive backend with a real event loop --
        # offscreen already returned above -- so these are exercised by
        # `tests/integration/test_interactive_window.py`'s
        # synthetic-event-injection technique, not the unit suite.
        def _on_wheel(event: dict[str, Any]) -> None:
            self._handle_wheel_zoom(event.get("dy", 0.0))

        def _on_pointer_down(event: dict[str, Any]) -> None:
            self._begin_pan(event["x"], event["y"])

        def _on_pointer_move(event: dict[str, Any]) -> None:
            self._update_pan(event["x"], event["y"])

        def _on_pointer_up(event: dict[str, Any]) -> None:
            self._end_pan()

        self.canvas.add_event_handler(_on_wheel, "wheel")
        self.canvas.add_event_handler(_on_pointer_down, "pointer_down")
        self.canvas.add_event_handler(_on_pointer_move, "pointer_move")
        self.canvas.add_event_handler(_on_pointer_up, "pointer_up")

        def on_draw() -> None:
            self._draw()
            if max_frames is not None and self.frame_count >= max_frames:
                self.canvas.close()
            else:
                self.canvas.request_draw(on_draw)

        logger.info(
            "opening render window: %dx%d %r (backend=%s)%s",
            self._config.width,
            self._config.height,
            self._config.title,
            self._config.backend,
            f" -- press {' or '.join(close_keys)} to close" if close_keys else "",
        )
        self.canvas.request_draw(on_draw)
        get_loop(self._config).run()
        logger.info("render window closed: %d frame(s)", self.frame_count)
