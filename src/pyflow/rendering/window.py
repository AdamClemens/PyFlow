"""Render window bootstrap: creation, render loop, clean shutdown (TASK-007).

`RenderWindow` owns the canvas, renderer, scene and camera for one
PyFlow window. It doesn't know or care which canvas backend it was given
-- `canvas.py` resolves that from configuration -- so the render loop
below is identical for an interactive glfw window and a headless
offscreen canvas.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

import pygfx as gfx

from pyflow.configuration.schema import RenderingConfig
from pyflow.engine import get_logger
from pyflow.engine.field import Field
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.rendering.canvas import create_canvas, get_loop

if TYPE_CHECKING:
    # `playback.py` imports `rendering` (this package), so a real,
    # runtime import here would be circular -- `TYPE_CHECKING` gives
    # `playback_state` below a real type for mypy without one. The same
    # narrow "a specific feature reports back through RenderWindow"
    # shape `assembled_numerics`/`simulation_fields` already establish,
    # not a new pattern.
    from pyflow.playback import PlaybackState

    pass

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


def visible_world_size(
    camera: gfx.OrthographicCamera, logical_width: float, logical_height: float
) -> tuple[float, float]:
    """The world-space extent `camera` actually projects onto a
    `logical_width` x `logical_height` viewport.

    Deliberately *not* `camera.width`/`camera.height`: with
    `maintain_aspect` (pygfx's default, and what stops a mesh being
    stretched to fill a differently-shaped window), pygfx expands
    whichever axis is narrower than the viewport rather than distorting
    the scene. `camera.width`/`camera.height` is therefore only the
    reference view -- a lower bound on what is on screen -- and using it
    directly as a screen-to-world scale under-tracks by exactly the
    aspect mismatch. Found 2026-08-21: `fit_camera_to_mesh` frames the
    default square mesh at 12x12 while the default window is 1280x720,
    so drag-panning moved the camera 1.78x too little in x. The one unit
    test covering pan used a 4:3 camera on a 4:3 canvas -- the single
    case where the two agree and the bug is invisible.

    Mirrors the orthographic branch of pygfx's own
    `PerspectiveCamera._update_projection_matrix` rather than reading
    `camera.projection_matrix` back, because that matrix is only correct
    once the renderer has pushed the viewport size into the camera
    (`Camera.set_view_size`, whose own docstring says it is "set by the
    renderer; you should typically not use this"). Reading it would make
    this function silently wrong before the first frame is drawn.
    """
    width = camera.width / camera.zoom
    height = camera.height / camera.zoom
    if camera.maintain_aspect:
        aspect = width / height
        view_aspect = logical_width / logical_height
        if aspect < view_aspect:
            width *= view_aspect / aspect
        else:
            height *= aspect / view_aspect
    return (width, height)


def screen_to_world(
    camera: gfx.OrthographicCamera,
    logical_width: float,
    logical_height: float,
    screen_x: float,
    screen_y: float,
) -> tuple[float, float]:
    """The world-space point a screen pixel `(screen_x, screen_y)`
    (logical coordinates, top-left origin, y increasing downward --
    `rendercanvas`'s own pointer-event convention) currently projects to
    under `camera`'s own position/zoom.

    The inverse of what `_update_pan` tracks only as a *delta*: this is
    an absolute mapping, built for TASK-048's scrub bar, which needs to
    place a thumb at an absolute world x and hit-test an absolute
    pointer position, not track a drag relative to where it started.
    Built on `visible_world_size` for the same aspect-ratio-expansion
    reason `_update_pan` already depends on it -- `camera.width`/
    `camera.height` alone would under-track by exactly the mismatch
    between the camera's own aspect and the canvas's.

    Verified empirically before being relied on (not assumed): a marker
    rendered at a known world position was located in a real offscreen
    render, and this formula's prediction from that marker's own pixel
    position matched the marker's actual world position to within
    sub-pixel rounding -- see `docs/CHANGELOG-DESIGN.md`, TASK-048.
    """
    visible_width, visible_height = visible_world_size(camera, logical_width, logical_height)
    center_x, center_y, _center_z = camera.local.position
    world_x = center_x - visible_width / 2 + (screen_x / logical_width) * visible_width
    world_y = center_y + visible_height / 2 - (screen_y / logical_height) * visible_height
    return (world_x, world_y)


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
        self.assembled_numerics: AssembledNumerics | None = None
        """The six numerics components `bootstrap()` assembled for this
        run (TASK-021), or `None` if the caller built a `RenderWindow`
        directly without going through `bootstrap()`. `RenderWindow`
        itself never assembles anything -- true to its own "no simulation
        content" scope above -- `bootstrap()` sets this after calling
        `assemble_numerics()`, purely so a caller has one place to read
        back what got assembled, per Stage 3 Completion Criterion 8."""
        self.simulation_fields: Mapping[str, Field] | None = None
        """The live simulation's own transported fields, updated every
        frame (TASK-030), or `None` if this run has no live simulation
        (every demo before Passive Scalar Transport) or the caller built
        a `RenderWindow` directly. Same shape as `assembled_numerics`
        above: `RenderWindow` never advances a simulation itself, true to
        its own "no simulation content" scope; `bootstrap()`'s own
        `on_frame` closure sets this each step, purely so a caller (a
        golden-demo regression test, most directly) has one place to read
        back the real field state a rendered frame came from, not only
        its rendered pixels."""
        self.playback_state: PlaybackState | None = None
        """`playback.py`'s own `PlaybackState` (position/paused/speed),
        or `None` outside a `playback.play()` run. Same shape as
        `assembled_numerics`/`simulation_fields` above: `RenderWindow`
        never drives playback itself, true to its own "no simulation
        content" scope; `play()`'s own `on_frame` closure sets this once,
        purely so a caller (`tests/integration/test_playback_cli.py`,
        most directly) has one place to read back pause/speed state that
        would otherwise be a local closure variable nothing outside
        `play()` could see."""
        self._on_frame: Callable[[], None] | None = None
        self._frame_error: Exception | None = None
        """Whatever `on_frame` last raised, if anything (TASK-053).
        `run` re-raises it; `_draw` cannot, because the caller above it
        is `rendercanvas`, which swallows.
        """
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

        Screen-to-world conversion uses the camera's *current* visible
        extent (`visible_world_size`, which accounts for pygfx's
        aspect-ratio expansion -- not `camera.width` directly), so
        neither `zoom` changing mid-drag nor a window whose shape differs
        from the framed content produces a mistracked drag. Signs
        verified empirically (not assumed):
        dragging right/down moves the camera in *negative* x / *positive*
        y respectively -- see `docs/CHANGELOG-DESIGN.md`, TASK-013.
        """
        if self._pan_drag_start_screen is None or self._pan_drag_start_position is None:
            return
        dx_screen = x - self._pan_drag_start_screen[0]
        dy_screen = y - self._pan_drag_start_screen[1]

        logical_width, logical_height = self.canvas.get_logical_size()
        visible_width, visible_height = visible_world_size(
            self.camera, logical_width, logical_height
        )
        world_per_px_x = visible_width / logical_width
        world_per_px_y = visible_height / logical_height

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
        """One frame: render, then advance whatever `run`'s own `on_frame`
        callback advances.

        **Anything `on_frame` raises is caught here, recorded, and the
        window closed (TASK-053, Stage 9, 2026-09-12) -- not allowed to escape
        `rendercanvas`.** This method is installed as that library's own
        `_draw_frame`, and it calls it inside `with
        log_exception("Draw error")`, which logs and continues by design
        ("otherwise we crash", in its own comment). So an exception that
        escapes here is not propagated to anybody: before this task,
        `DivergenceDidNotConvergeError` from a diverging simulation was
        swallowed exactly that way, and `pyflow run` printed `pyflow
        exited cleanly` and returned 0 after 22 of 40 frames had failed.

        `rendercanvas` exposes no error-handler API to opt out of that --
        checked directly, not assumed: there is no `set_*error*`,
        `error_handler`, `excepthook` or `on_error` anywhere in the
        package, and `log_exception` de-duplicates by message hash, so a
        repeating failure degrades to one-liners. The seam that works is
        PyFlow's own: catch before the boundary, stash, and let `run`
        re-raise once the loop is over.

        **`frame_count` is incremented before `on_frame` and rolled back
        if it raises**, rather than simply incremented afterward. The
        distinction is not cosmetic: the HUD's own per-frame update is
        composed into `on_frame` (`bootstrap.py`), and it reads
        `frame_count` to render "step N / elapsed t" -- so incrementing
        afterward makes the frame that is *currently being drawn* report
        the previous frame's number, and every run's step readout comes
        out one low. Found by `test_bootstrap_stats_use_configured_time_
        units_for_elapsed_time` failing on a three-frame run that
        displayed `step 2  t = 20 ms`, not by reasoning about it.

        The rollback keeps the property that motivated the change: a
        frame whose simulation step died does not count as drawn, so a
        failing run cannot report a full frame budget.
        """
        self.renderer.render(self.scene, self.camera)
        self.frame_count += 1
        if self._on_frame is not None:
            try:
                self._on_frame()
            except Exception as error:  # noqa: BLE001 -- re-raised by `run`
                self._frame_error = error
                self.frame_count -= 1
                self.canvas.close()

    def _raise_any_frame_error(self) -> None:
        """Re-raise whatever `_draw` caught, now that the event loop has
        let go (TASK-053, Stage 9, 2026-09-12).

        Called on both of `run`'s branches, because both need it for
        different reasons: the offscreen loop is PyFlow's own `for` and
        would otherwise return a full frame budget of failures, and the
        interactive one hands control to `get_loop(...).run()`, which
        returns only once the canvas closes -- which `_draw` does on the
        failing frame.
        """
        error = self._frame_error
        if error is not None:
            self._frame_error = None
            raise error

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
                # `canvas.draw()` returns normally even when `_draw`
                # failed, so the budget has to be abandoned explicitly --
                # unlike the interactive branch below, where closing the
                # canvas ends the loop on its own.
                if self._frame_error is not None:
                    break
            self.canvas.close()
            self._raise_any_frame_error()
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
        self._raise_any_frame_error()
        logger.info("render window closed: %d frame(s)", self.frame_count)
