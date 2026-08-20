# CLAUDE

Rendering subsystem: window/render-loop bootstrap (`docs/planning/roadmap.md`
TASK-007) and visualisation of scalar/vector fields.

As of 2026-08-15, this package's scope also covers what was briefly a
separate, undocumented `interaction/` package (user input, camera/view
control) -- interactive visualisation and the input handling that drives
it belong together. See `docs/planning/backlog.md` §1 "TASK-000 package
structure mismatch" and `docs/CHANGELOG-DESIGN.md` for why. Split input
handling back out only once it's grown large enough to justify its own
package.

**Implemented 2026-08-16 (D3, TASK-007).** `canvas.py` is the seam
between configuration and windowing: `create_canvas(config)` builds
either a `rendercanvas.glfw.GlfwRenderCanvas` (interactive) or a
`rendercanvas.offscreen.OffscreenRenderCanvas` (headless -- what CI and
the golden-demo regression tests, D5, need), selected by
`RenderingConfig.backend`. `window.py`'s `RenderWindow` doesn't know or
care which one it got: both implement `rendercanvas.base.
BaseRenderCanvas`, and `pygfx.WgpuRenderer` only depends on that
protocol -- the same "swap the implementation behind a stable interface"
pattern `adr/ADR-003-modular-numerical-strategies.md` already commits
PyFlow to for numerics, applied here to the windowing layer.

**Adding a third backend (Qt/PySide6, the maintainer's stated long-term
ambition) means adding one branch to `create_canvas`/`get_loop`, not
touching `window.py` or the render loop.** Deliberately not implemented
yet -- Stage 0 doesn't need it, and building it unused would be exactly
the kind of speculative abstraction the root `CLAUDE.md` warns against.

`RenderWindow.run(max_frames=...)`: interactive backends self-reschedule
each draw via `request_draw` until closed (by the user, or automatically
once `max_frames` is reached); offscreen draws `max_frames` (default 1)
frames directly, since it has no event loop to run
(`rendercanvas.offscreen`'s own docstring: "No scheduling"). The
`max_frames` bound exists because `make demo` and D5's regression test
both need to exit on their own, not wait for a user to close a window
that doesn't have one.

**Only the offscreen backend is exercised by `tests/unit/test_rendering.py`**
-- it's the one that works headless, in CI, and `tests/unit/CLAUDE.md`
documents why unit tests stay offscreen-only.

**Updated 2026-08-17: the interactive glfw path is now exercised
automatically too, just not from `tests/unit/`.**
`tests/integration/test_interactive_window.py` opens a real
`GlfwRenderCanvas` -- window creation, the render loop, distinct
per-frame presentation, and the close-key handler below, all through
`RenderWindow`/`pyflow run` itself -- and skips itself cleanly
(`pytest.mark.skipif`, probing a throwaway canvas at import time) on a
machine with no display, rather than being red on every push. It's an
`integration/` test, not `unit/`, because it needs a real OS window
resource -- a boundary crossing, per `tests/integration/CLAUDE.md`. This
was smoke-tested manually only, previously (D3, D4); do not assume
"needs a real display" still means "not automated" for anything in this
package going forward -- check `tests/integration/test_interactive_window.py`
first.

**`RenderWindow.run(close_keys=...)`, on by default, added 2026-08-16.**
Found by the maintainer actually running `pyflow run`: the window opened
and rendered, but nothing closed it short of killing the process -- every
earlier verification of this file (D3, D4) had used `max_frames` to
bound the run, so the actual "a real person, with no bound, needs to
close this" scenario was never exercised. `close_keys` defaults to
`("Escape", "Enter")` for every interactive backend; pass `None` to
disable. **This is the only way an interactive PyFlow window closes
without killing the process**, short of the OS window's own chrome --
treat that as a hard requirement for anything built on `RenderWindow`
going forward, not an optional nicety.
Verified with the same real-delay technique the maintainer suggested:
`window.canvas.submit_event({"event_type": "key_down", "key": "Escape",
...})` injected via `loop.call_later(6.0, ...)` while `window.run()` was
genuinely blocking -- confirmed the window was still live and repainting
the whole time (164 frames over 6s, not frozen) and closed cleanly the
moment the key event arrived.

**Automated 2026-08-17.** That exact technique -- `submit_event` via
`loop.call_later` while `run()` genuinely blocks, no `max_frames` --
is now
`tests/integration/test_interactive_window.py::test_close_key_terminates_the_render_loop_and_process_cleanly`,
with a shorter (0.5s) delay and an assertion on `frame_count` in place
of the manual frame-count read. Runs for real wherever a display exists
and skips itself where one doesn't (see the note above); re-run the
command above by hand only if you want to *watch* the window rather
than just confirm it closes.

**`RenderWindow.run(on_frame=...)`, added 2026-08-17.** Called once per
frame, immediately after it's rendered -- `self.frame_count` and
`self.renderer.snapshot()` already reflect that frame inside the
callback. Built for
`tests/integration/test_interactive_window.py::test_render_window_presents_distinct_frames`,
which needed a way to (a) prove the render loop presents genuinely
different pixels frame to frame, not a frozen buffer redrawn
repeatedly, and (b) mutate `self.scene` between frames to make that
true in the first place -- Stage 0's own scene has no animated content
(no simulation yet), so a static scene renders bit-identical frames
every time (verified empirically before adding this: five successive
`renderer.snapshot()` calls against an unchanged scene were pixel-equal
every time). Left as a general hook rather than a test-only seam,
since a future real-time simulation loop needs exactly this shape:
advance state once per frame, same as `request_draw` already advances
drawing once per frame. `None` (the default) changes nothing for every
existing caller.

**`RenderingConfig.background_color`, wired in `RenderWindow.__init__`,
added 2026-08-16 (D5).** If set, `gfx.Background(None,
gfx.BackgroundMaterial(config.background_color))` is added to `self.scene`
before anything else touches it. Exists so a golden demo's visual
identity can be pure configuration -- see
`docs/implementation/golden-demos.md`'s public-API rule and
`configuration/CLAUDE.md`. `None` (the default) adds nothing, so a bare
`RenderWindow`/`pyflow run` still renders exactly the transparent frame
it always did -- this is additive, not a behaviour change for anyone not
using it.

## Mesh Visualiser (TASK-013, done 2026-08-20)

Two things landed together, deliberately kept in different modules
since one is mesh-specific and the other is generic camera control any
future renderable content (TASK-017's fields, eventually) can reuse:

**`mesh_visualization.py`** -- mesh-specific, knows nothing about
cameras' live interaction: `build_mesh_grid_line(mesh, color)` turns a
`Mesh` (`src/pyflow/engine/mesh.py`) into one `gfx.Line` with
`LineSegmentMaterial` (each consecutive point-pair is its own segment,
so all of `mesh.num_faces` grid lines render in one draw call, not one
object per face). `fit_camera_to_mesh(camera, mesh)` centres and sizes a
camera on the mesh's bounding box (from `mesh_bounding_box`, which
scans every face's `face_vertices` -- works for any `Mesh`, not just a
structured one), with a 10% margin on each side
(`_VIEW_MARGIN_FRACTION`) -- found empirically while writing this
module's own tests: without it, a boundary grid line sits exactly on
the viewport edge and gets partially clipped.

**`window.py`'s new camera controls** -- generic, no `Mesh` import here
at all:
- `RenderWindow.apply_camera_config()` applies `config.zoom`/`config.pan`
  on top of whatever base view is already set. `pan` is an *offset*
  added to the camera's current position, not an absolute one, so it
  composes with `fit_camera_to_mesh` (or with nothing, for a
  non-mesh-visualising run) -- callers must call this *after* any base
  framing, not before.
- `_handle_wheel_zoom(dy)`, `_begin_pan`/`_update_pan`/`_end_pan` are the
  actual logic behind live mouse-wheel zoom and pointer-drag pan,
  deliberately factored out as plain methods (not closures inside
  `run()`) specifically so they're unit-testable
  (`tests/unit/test_rendering.py`) without a real event loop. `run()`
  wires them to `canvas.add_event_handler(..., "wheel"/"pointer_down"/
  "pointer_move"/"pointer_up")` in the same interactive-only branch
  `close_keys` already uses -- same mechanism, not a new one -- so
  they're exercised for real (not just the unit-tested logic in
  isolation) by `tests/integration/test_interactive_window.py`'s
  synthetic-event-injection technique.
- **Sign conventions were verified empirically, not assumed**, following
  this project's "check implementation details every time" practice
  (`docs/CHANGELOG-DESIGN.md`, TASK-012's `face_normal` bug): a small
  throwaway offscreen-render script confirmed which direction
  `camera.zoom` and `camera.local.position` actually move rendered
  content on screen *before* `_update_pan`'s `-`/`+` signs were chosen,
  rather than reasoning it out abstractly and hoping. `_update_pan`'s own
  docstring states the verified result plainly: dragging right/down
  moves the camera in *negative* x / *positive* y respectively, so the
  rendered content follows the cursor.
- `_handle_wheel_zoom` clamps to `config.zoom_min`/`config.zoom_max` --
  scrolling indefinitely can't zoom into numerical degeneracy or out to
  nothing rendering (TASK-013's own Acceptance Criteria, `docs/
  planning/roadmap.md`).

**`bootstrap.py` wires both together**, not `RenderWindow` itself:
if `config.rendering.grid_color` is set, it builds a
`StructuredCartesianMesh.from_config(config.mesh)`, adds its grid line
to `window.scene`, and calls `fit_camera_to_mesh` -- then
`apply_camera_config()` always runs, mesh or not, since zoom/pan aren't
mesh-specific. `RenderWindow` itself stays simulation/mesh-agnostic, per
its own docstring ("No simulation content") -- exactly the same
`bootstrap.py`-does-the-composing pattern `src/pyflow/CLAUDE.md`
documents for `configuration`+`engine`+`rendering` generally.
