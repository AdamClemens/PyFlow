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

**Only the offscreen backend is exercised by the automated test suite**
(`tests/unit/test_rendering.py`) -- it's the one that works headless, in
CI. The interactive glfw path was smoke-tested manually (a real window
opened, drew 5 frames, closed cleanly) but isn't part of `make test`: it
needs a real display, which CI runners don't have.
