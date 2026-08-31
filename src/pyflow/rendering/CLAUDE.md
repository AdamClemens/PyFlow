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
with an assertion on `frame_count` in place of the manual frame-count
read. Runs for real wherever a display exists and skips itself where one
doesn't (see the note above); re-run the command above by hand only if
you want to *watch* the window rather than just confirm it closes.

**The Escape key is injected on a frame count, not a wall-clock delay --
changed 2026-08-31 by the Stage 6 exit audit, which found that test
failing deterministically on this machine (`assert 2 > 2`).** It used a
shorter `loop.call_later(0.5, ...)` than the 6s manual recipe above and
then asserted more than two frames had been presented in that window.
Nothing about the render loop was wrong; the margin was. **Measured
directly, and worth recording because the manual recipe above depends on
the same numbers:** a real glfw window here takes roughly half a second
to begin painting at all, and then paints at about 30 fps -- 0.5s yields
2 frames, 1.0s yields 30, 2.0s yields 60. The 6s recipe's "164 frames
over 6s" is consistent with that (~27 fps once started). The test now
submits the key from an `on_frame` callback once three frames have been
presented, with a 5s `call_later` backstop so a genuinely frozen window
still fails the assertion rather than blocking `run()` forever. **Any
future test that wants to prove the window is live should wait on the
frame count, not on the clock.**

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
- **The signs were right; the *scale* was not** (found 2026-08-21 by a
  repository audit, fixed the same day). `_update_pan` converted pixels
  to world units with `camera.width / zoom / logical_width`, which is
  correct only when the camera's aspect ratio matches the canvas's.
  pygfx's `maintain_aspect` -- on by default, and the thing that stops a
  square mesh being stretched to fill a 16:9 window -- expands whichever
  axis is narrower than the viewport, so `camera.width` is the
  *reference* view, a lower bound on what is actually on screen. In the
  shipped default (a square mesh framed by `fit_camera_to_mesh` in a
  1280x720 window) horizontal drags moved the camera 1.78x too little,
  exactly the 16:9 ratio. `visible_world_size()` now does that
  conversion; it mirrors pygfx's own projection rule rather than reading
  `camera.projection_matrix` back, because that matrix is only correct
  after the renderer has pushed the viewport size in, which would make
  the function silently wrong before the first frame.

  The lesson worth carrying, beyond this one bug: **the empirical check
  above verified direction, and a direction check cannot catch a wrong
  constant.** The unit test written alongside it used a 4:3 camera on a
  4:3 canvas -- the one configuration where the buggy and correct
  formulas agree -- so it passed for two days. When verifying a
  conversion empirically, pick a fixture where every factor in it is
  distinct, not one where they cancel.
- `_handle_wheel_zoom` clamps to `config.zoom_min`/`config.zoom_max` --
  scrolling indefinitely can't zoom into numerical degeneracy or out to
  nothing rendering (TASK-013's own Acceptance Criteria, `docs/
  planning/roadmap.md`).

**`bootstrap.py` wires both together**, not `RenderWindow` itself:
if `config.rendering.show_mesh` is true, it builds a
`StructuredCartesianMesh.from_config(config.mesh)` and adds its grid
line to `window.scene` -- then `apply_camera_config()` always runs, mesh
or not, since zoom/pan aren't mesh-specific. (The gate was `grid_color
is not None` until 2026-08-21 -- a colour doubling as a feature switch,
so there was no way to show the mesh in the default colour; `show_mesh`
is now the switch and `grid_color` only a colour.) `RenderWindow` itself
stays simulation/mesh-agnostic, per its own docstring ("No simulation
content") -- exactly the same `bootstrap.py`-does-the-composing pattern
`src/pyflow/CLAUDE.md` documents for `configuration`+`engine`+
`rendering` generally. Camera framing itself moved from a direct
`fit_camera_to_mesh` call to `fit_camera_to_bounds` (below, TASK-017) --
see that entry for why.

## Field Rendering (TASK-017, done 2026-08-21)

**`field_visualization.py`** -- the field-specific counterpart to
`mesh_visualization.py`, same split of responsibility (this module only
turns a `ScalarField`/`VectorField` into `pygfx` geometry; it owns no
camera or render loop). Four public functions: `scalar_field_colors`
(a `ScalarField` -> per-cell `uint8` RGBA, pure colour math, no `pygfx`
involved, hence independently testable), `build_scalar_field_mesh` (one
flat-coloured quad per cell), `build_vector_field_arrows` (one line
segment per cell with a non-zero vector -- a cell whose vector is
exactly zero contributes no segment at all, not a zero-length one, so it
renders no arrow rather than a stray dot), and `build_field_legend` (a
sampled gradient strip). `_map_values_to_colors` is the one colour ramp
`scalar_field_colors` and `build_field_legend` both call, so the legend
is provably the field's own colour function, not a second
implementation of the gradient -- the specific claim TASK-017's own
Acceptance Criteria make about it.

**No function here takes a `Mesh` alongside a `Field`, and that is a
rule rather than a coincidence** (changed 2026-08-22, Stage 2 exit
audit -- `docs/planning/roadmap.md`). Both builders originally did:
`build_scalar_field_mesh(mesh, colors)` and
`build_vector_field_arrows(field, mesh, color, scale)`. Nothing checked
the two agreed, and for the arrows in particular that meant a segment's
tail (`mesh.cell_centroid(cell)`) and its direction
(`field.value_at(cell)`) were read from two references a caller had to
keep in step by hand -- and a mismatched pair with equal `num_cells`
would have rendered a confident, silently wrong picture rather than
raising. Stage 2 Completion Criterion 1 exists to stop exactly that: a
`Field` carries its mesh, so `field.mesh` is the only place to get it.
`build_scalar_field_mesh` now takes the `ScalarField` whose values
produced `colors`, and `build_vector_field_arrows` dropped its `mesh`
parameter outright. **Apply the same rule to anything Stage 3+ adds
here**: if a function has a field, it does not need a mesh argument;
if it genuinely operates on a mesh with no field involved, it belongs in
`mesh_visualization.py`.

**`gfx.Mesh` face colours are linear, not sRGB -- found empirically, not
assumed, and the reason `_srgb_decode` exists.** A pure `(255, 0, 0)`
face colour round-tripped through rendering exactly; an intermediate
`(100, 150, 200)` came back as `(168, 202, 229)`. `gfx.Line`/
`LineSegmentMaterial` (grid lines, TASK-013; arrows here) does **not**
do this -- confirmed by `test_empty_mesh.py`'s own pre-existing
exact-match assertion on an intermediate hex colour, which has always
passed with zero compensation. So `scalar_field_colors`'s callers get an
sRGB-decoded copy of whatever colour they're given right before it's
handed to a `gfx.Mesh` as a face colour (`_quads_to_mesh`, shared by
`build_scalar_field_mesh` and `build_field_legend`) -- callers of
`scalar_field_colors` itself see the plain, undistorted `uint8` values
throughout; the decode is this module's own internal concern.

**`LineSegmentMaterial` at `thickness=2.0` does not reproduce a colour
bit-exactly at every pixel even with `aa=False`** (found while writing
`tests/golden/test_field_display.py`) -- GPU line rasterization's own
edge coverage means a pixel right at a segment's endpoint/cap can be a
few `uint8` levels off the configured colour, even though every pixel
solidly inside the segment's own length is exact. Sample a segment's
*midpoint*, not its endpoint, when checking an arrow's colour for real;
the golden test allows a small (`<= 4`) tolerance for exactly this
reason, while every scalar-field-fill colour check in the same file
stays exact (quads don't have this edge-rasterization behaviour).

**`mesh_visualization.fit_camera_to_bounds`, factored out of
`fit_camera_to_mesh`** -- the latter is now one line,
`fit_camera_to_bounds(camera, mesh_bounding_box(mesh))`. Needed because
a field display's legend (drawn below the mesh, `bootstrap.py`) extends
past the mesh's own bounding box, so the camera has to be framed on the
combined box, and `mesh_visualization.py` has no business knowing what a
legend is. `bootstrap._add_field_display` returns whichever bounding box
the caller should actually frame -- the mesh's own bounds, or that
widened by the legend strip's height if one was drawn.

**`bootstrap.py`'s wiring, and the one real cross-field bug it exposed
while writing the golden test, not predicted in advance:** every cell's
arrow starts exactly at that cell's own centroid, and arrows are drawn
above the field fill (`_ARROWS_Z = 0.01` vs. the fill's implicit `0.0`)
-- so sampling a cell's centroid pixel against a config with *both*
patterns active sometimes reads the arrow's colour, not the field's.
`tests/golden/test_field_display.py`'s own per-cell scalar-colour checks
use a scalar-only config variant for exactly this reason, not the real
demo file -- see that file's `_SCALAR_ONLY_CONFIG` comment. The demo
itself (`examples/golden-demos/field_display.yaml`) still shows both
fields together, as intended; only the *test* needed isolating.
`_scalar_display_initializer`/`_vector_display_initializer` map
`FieldDisplayConfig`'s closed pattern names (`"radial_gradient"`,
`"rotational"`) to the actual `(x, y) -> value` callables `Field`'s own
general API expects -- the one place those two closed names and the
general callable mechanism meet.

**World-to-pixel mapping for the golden test's per-cell exactness
checks, verified empirically before being relied on, not derived on
paper alone:** `field_display.yaml`'s `rendering.width`/`height` are
chosen so the canvas aspect exactly matches the framed bounding box's
own aspect (25:29). With the two aspects equal, pygfx's
`maintain_aspect` has nothing to correct, so a plain linear world-to-
pixel formula holds exactly -- checked directly against a
deliberately-mismatched-aspect canvas first, where the plain formula is
*not* sufficient (`window.py`'s own `visible_world_size`, TASK-013,
exists for exactly that mismatched case). `empty_mesh.yaml` doesn't need
this care because its own tests only ever check "does a pixel of this
colour exist anywhere," never a specific predicted position.

## Numerics Assembly Reporting (TASK-021, done 2026-08-23)

**`RenderWindow.assembled_numerics: AssembledNumerics | None`, the one
attribute this package added for Stage 3's Numerics Assembly golden
demo.** A narrow, deliberate exception to `RenderWindow`'s own "no
simulation content" scope stated at the top of this file:
`RenderWindow` itself never calls `assemble_numerics` and knows nothing
about what the attribute holds beyond its type -- `bootstrap()`
(`src/pyflow/bootstrap.py`) is what assembles the six numerics
components on every run and stores the result here, purely so a caller
has one place to read back what got assembled (Stage 3 Completion
Criterion 8's "an accessor on what `bootstrap()` returns"). `None` only
for a `RenderWindow` built directly without going through `bootstrap()`
-- the same "`None` until populated" shape `last_image` already
established.

Importing `pyflow.engine.numerics.assembly` here is a new dependency
direction for this package (previously only `engine.logging_setup`,
a leaf module) -- accepted rather than routed around, since introducing
a `BootstrapResult` wrapper type instead would have changed
`bootstrap()`'s return type for every existing caller (tests,
`__main__.py`, this file's own module) merely to avoid one import,
which is a larger blast radius for a smaller problem.

## Live Simulation Reporting (TASK-030, done 2026-08-28)

**`RenderWindow.simulation_fields: Mapping[str, Field] | None`, the same
shape `assembled_numerics` above already established** -- another narrow,
deliberate exception to `RenderWindow`'s own "no simulation content"
scope: `RenderWindow` itself never calls `simulation.step()` and knows
nothing about what the mapping holds beyond its type.
`bootstrap.py`'s `_add_passive_scalar_transport` (the Passive Scalar
Transport golden demo's own mechanism -- the first config to wire a real
`simulation.step()` call into `RenderWindow.run(on_frame=...)`, not a
capability of this package's own) sets it once per frame, inside its own
`on_frame` closure, purely so a caller -- the golden demo's own
regression test, most directly -- has one place to read back the real
field state a rendered frame came from, not only its rendered pixels.
`None` for every run before this task's own (every existing demo) and
for a `RenderWindow` built directly without going through `bootstrap()`.

Importing `pyflow.engine.field` here is the same kind of new-but-narrow
dependency `assembled_numerics` above already accepted for
`pyflow.engine.numerics.assembly` -- `Field` is only ever used as a type
annotation, and the same "avoid a wrapper type that would change
`bootstrap()`'s return type for every caller" reasoning applies.

## HUD (Stage 7, Rendering Annotations, done 2026-08-31)

**`hud.py`** is the HUD-specific counterpart to `mesh_visualization.py`/
`field_visualization.py`, the same split this module's own opening
section already establishes: it only turns plain values -- strings,
world-space positions, bounds -- into `pygfx.Text` objects. It owns no
camera, no render loop, and no number formatting (that stays in
`bootstrap.py`, the one place that already holds `config.mesh`/
`config.numerics.timestep`/`config.units` together). Three public
functions: `build_title_text`, `build_stats_text` (one multi-line block,
lines joined with `\n`, so a per-frame update is a single `set_text`
call), `build_legend_labels` (min/max numeric labels at a legend strip's
own bottom corners, plus an optional field-name label above it).

**This closes the deferral `field_visualization.py`'s own module
docstring and `docs/planning/roadmap.md`'s TASK-017 entry recorded**:
numeric legend labels were held back specifically because pygfx's text
rendering had not been verified live, not because labelling was
considered unimportant. Verified directly against the installed
`pygfx==0.17.0` before building anything on it (not assumed): `gfx.Text`
renders real, visible glyphs in an offscreen render (458 non-background
pixels for a five-character string in a 200x200 canvas); `Text.set_text`
mutates content in place, reflected on the next render, with no
remove-and-rebuild needed; and `gfx.Text` has a `screen_space=True` mode
that would keep text a fixed pixel size regardless of camera zoom --
confirmed to exist and work, but deliberately **not used yet**, since the
maintainer's own choice for this iteration was the lower-risk,
already-proven pattern (world-space, camera-following, reusing the
legend strip's own bounds-extension approach) over a fixed overlay.
Revisit `screen_space` as a fast-follow now that it is verified, not
speculative.

**`gfx.Text` has no public way to read its own content back** -- found
while writing `tests/unit/test_hud.py`, not assumed: neither `Text` nor
its `Geometry` exposes a `.text` property. `text._text_blocks[i]._input`
is pygfx's own private `(kind, string)` pair, confirmed live and used
directly by both `test_hud.py` and `test_bootstrap.py`'s own
`_text_content` helpers (each module keeps its own copy, the same
"local by default" convention `tests/unit/CLAUDE.md` documents) -- a
future pygfx upgrade that changes this internal shape only needs fixing
in the two places that read it, not anywhere content is actually built.

**World-to-pixel mapping in `tests/golden/test_field_display.py`
recomputed, not left stale, when the HUD widened the framed view.** That
module's own pixel-exact per-cell/legend checks depend on the canvas
aspect exactly matching the framed bounding box's aspect
(`rendering/CLAUDE.md`'s own "World-to-pixel mapping" note, above) --
adding a title above and a stats block/legend labels below the mesh
changes that box, so `field_display.yaml`'s own `rendering.height`
(290 -> 395, keeping width at 250) and the test module's
`_FRAMED_BOUNDS`/`_CANVAS` constants were recalculated from
`bootstrap.py`'s own margin fractions and re-verified against a real
render, not guessed. One arrow-midpoint tolerance widened from 4 to 15
in the same pass -- re-measured at the new resolution, the same
GPU-line-rasterisation edge-coverage effect the original tolerance was
already accommodating, not a new defect.

**`bootstrap.py`'s `_add_legend` is a small extraction, not new
behaviour, with one real exception.** Before this stage, only the static
`_add_field_display` path (the Field Display demo) ever drew a legend
strip at all -- the live-stepping path (`_add_declared_field_transport`)
colour-mapped a declared field every frame with no legend beside it,
which is exactly backwards from what a viewer watching a live run needs
most. `_add_legend(window, field_display, mesh_bounds) -> _Bounds | None`
is the shared strip-drawing logic both paths now call, so a live run
with `field_display.render_field` set gets the same labelled legend a
static demo does. `_add_solved_velocity_rendering` (arrows only, no
scalar) always returns `None` for its own legend bounds -- there is
nothing to label.

**The HUD activates on its own, independent of what else is
configured -- reversed the same day it first shipped, after real user
feedback.** It originally only ran inside the same `if config.rendering.
show_mesh or show_fields or run_simulation:` block every other piece of
visible content shares, specifically to protect
`tests/features/empty_window.feature`'s own "every pixel is the
configured background colour" scenario from an HUD that activated
independently. That protected Empty Window at the cost of every *other*
demo with nothing else configured to show (Numerics Assembly, Stage 3's
own "no CFD yet" demo): a genuinely blank window with zero information,
which a real user hit and called out directly -- worse than the gap this
stage exists to close, since at least a title would have said what was
running. `bootstrap.py`'s own top-level condition now includes
`show_title or show_stats` (both default `True`), so the HUD -- and the
mesh construction/camera framing it needs -- runs whenever either is
true, regardless of `show_mesh`/`field_display`/a live simulation.
**Empty Window is the one demo that still wants the bare look, and now
asks for it explicitly** (`show_title: false`, `show_stats: false` in
`empty_window.yaml`) rather than getting it as an implicit side effect
of a condition built for something else.

**Layout is fixed-fraction margins against the mesh's own height
(`_TITLE_MARGIN_FRACTION`/`_LEGEND_LABEL_MARGIN_FRACTION`/
`_STATS_MARGIN_FRACTION` in `bootstrap.py`), not measured text extents.**
pygfx gives no cheap way to measure a `Text` object's rendered size
before it is added to a scene, so -- the same "fixed guess, not derived"
shape `_LEGEND_HEIGHT_FRACTION` already established for the legend strip
itself -- the margins are generous rather than tight: a too-tight margin
clips HUD text at typical zoom levels sooner than a too-generous one
wastes empty space. One known, minor layout imperfection, not a
correctness bug: `field_label` (when set) is placed inside the existing
mesh-to-legend gap, which is tight enough to visually crowd a small
mesh's own bottom row -- revisit if a real config using `field_label`
shows this in practice, not pre-emptively.

**`gfx.Text`'s `max_width` genuinely word-wraps, confirmed live before
relying on it, not assumed -- and every HUD text object now sets it to
the mesh's own world-space width.** Found necessary, not anticipated:
`field_display.yaml`'s own narrow, pixel-exact-testing canvas (250px
wide) clipped a longer `vector_label` line clean off the right edge of
the frame before this. `hud.py`'s `build_title_text`/`build_stats_text`/
`build_legend_labels` all gained a `max_width: float = 0` parameter (`0`
is pygfx's own "unbounded" default, so every existing caller is
unaffected); `bootstrap.py`'s `_add_hud` passes `mesh_max_x - mesh_min_x`
for all three. Wrapping adds vertical space the fixed-fraction margins
above don't specifically account for -- the same known, generous-not-
exact trade-off those margins already accept, now doing double duty.

**`FieldDisplayConfig.vector_label`, and the vector-scale stats line it
adds, close the other half of the same user feedback that reversed the
HUD's own gating above**: "arrows... [but] neither the direction nor
magnitude is clear." `bootstrap.py`'s `_stats_lines` appends
`"{vector_label}: length = {arrow_scale} x magnitude"` when a
`show_vector_scale` flag (computed in `bootstrap()`: a static
`vector_pattern` being shown, or a live velocity-only run rendering
arrows) is true *and* `vector_label` is set -- gated on arrows actually
being on screen, not merely on the label existing, so a stray
`vector_label` naming arrows nothing draws can't appear. Every shipped
golden demo with arrows (`field_display.yaml`, `lid_driven_cavity.yaml`)
sets one now; `smoke_transport.yaml`/`thermal_buoyancy.yaml`
(`velocity_solved` alongside a declared field, via
`_add_declared_field_transport`) don't, because that path has never
drawn velocity as arrows at all -- only the scalar it colour-maps -- so
there is nothing to label yet.

**Elapsed time's "step N" numbering was traced through `RenderWindow.
_draw`'s own increment-then-callback order, not assumed.** `_draw()`
increments `frame_count` *before* firing `on_frame`, and `bootstrap.py`'s
composed `on_frame` always runs the simulation-advance closure before
the HUD-update closure -- so by the time `_stats_lines` reads
`window.frame_count`, the state that will be shown starting the *next*
rendered frame has been advanced exactly `frame_count` times in total.
`elapsed = frame_count * config.numerics.timestep` is therefore what
agrees with what is actually on screen once the mutated text becomes
visible, not an off-by-one guess -- see `_stats_lines`'s own docstring
in `bootstrap.py` for the full trace.

**Physical units (`config.units`) format as a single labelled number,
not a dual "raw (converted)" display.** `_format_length`/`_format_time`
in `bootstrap.py` always show `value * scale` labelled with the
configured unit -- at the default scale (`1.0`) and unit (`"m"`/`"s"`),
this is the bare simulation number labelled in SI base units; a
configured `length_scale`/`length_unit` changes what number is shown,
not whether one is. Simpler than an earlier draft that showed both the
raw and converted number side by side, and it sidesteps the "when do I
show the parenthetical" question that shape would have raised, per this
project's own preference for the simplest design that satisfies the
actual requirement.

**Not yet built: a Gherkin `.feature` file for this stage.** Every HUD
behaviour above is covered by plain pytest (`tests/unit/test_hud.py`,
and object-presence/content checks added to `tests/unit/
test_bootstrap.py`), the same "checked by construction" shape this
package already uses for the legend's own colour-sharing guarantee, but
`adr/ADR-007-executable-acceptance-criteria.md`'s scope is "real
simulation work" specifically (its own Decision section: "Stage 4
onward... where physics begins"), and rendering annotations are not
physics -- the same category distinction that Stage's own exemption
already draws for Stage 3. Recorded here as a real, honest gap rather
than silently decided either way: revisit if a future session judges the
existing plain-pytest coverage insufficient, rather than assuming this
paragraph's reasoning is the last word on it.
