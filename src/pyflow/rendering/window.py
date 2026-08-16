"""Render window bootstrap: creation, render loop, clean shutdown (TASK-007).

`RenderWindow` owns the canvas, renderer, scene and camera for one
PyFlow window. It doesn't know or care which canvas backend it was given
-- `canvas.py` resolves that from configuration -- so the render loop
below is identical for an interactive glfw window and a headless
offscreen canvas.
"""

from __future__ import annotations

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


class RenderWindow:
    """A window (or headless canvas) with a renderer, scene and camera.

    No simulation content: TASK-007 is the rendering bootstrap only. An
    empty `pygfx.Scene()` is enough to exercise window creation, the
    render loop and clean shutdown, which is everything this task's
    acceptance criteria ask for. Callers (e.g. a golden demo) can add
    content to `self.scene` before calling `run()`.
    """

    def __init__(self, config: RenderingConfig) -> None:
        self._config = config
        self.canvas = create_canvas(config)
        self.renderer = gfx.WgpuRenderer(self.canvas)
        self.scene = gfx.Scene()
        self.camera = gfx.OrthographicCamera()
        self.frame_count = 0
        self.last_image: Any | None = None
        """The most recently rendered frame as an NxMx4 uint8 array --
        only populated for the offscreen backend, which is the only one
        `rendercanvas` gives pixel data back for (see
        `rendercanvas.offscreen.OffscreenRenderCanvas.draw`). `None` for
        interactive backends and before the first frame."""

    def _draw(self) -> None:
        self.renderer.render(self.scene, self.camera)
        self.frame_count += 1

    def run(
        self,
        *,
        max_frames: int | None = None,
        close_keys: tuple[str, ...] | None = _DEFAULT_CLOSE_KEYS,
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
        """
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
