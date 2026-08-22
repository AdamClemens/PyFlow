# Rendering Architecture

The architecture of the renderer PyFlow actually adopted: wgpu/pygfx
(`adr/ADR-005-compute-rendering-instances.md`).

**No `docs/planning/knowledge-architecture.md` entry corresponds to this
document**, and that is deliberate rather than an omission. KA §11
(Implementation Architecture Knowledge) itemises `engine.md` (KA-029) and
`icds.md` (KA-030) only; this document, `overview.md` and `repository.md`
are architecture documents the project turned out to want that KA never
enumerated. `docs/architecture/CLAUDE.md` records that reasoning for all
three -- KA does not have to name every architecture document worth
writing.

Distinct from `docs/architecture/compute-and-rendering-stack.md`: that
document is decision-support, comparing candidate array-library/renderer
pairings before a choice was made. This document is the architecture of
the pairing actually chosen, as implemented in
`src/pyflow/rendering/{canvas,window}.py`. Read `adr/ADR-004` and
`adr/ADR-005` for *why* wgpu/pygfx was chosen; this document is about how
it is used, not why.

---

## The Layering

Three pieces, each swappable independently of the others:

```text
RenderingConfig (configuration/schema.py)
        │  selects backend: "glfw" | "offscreen"
        ▼
create_canvas() (rendering/canvas.py)
        │  builds a rendercanvas.base.BaseRenderCanvas
        ▼
RenderWindow (rendering/window.py)
        │  owns pygfx.WgpuRenderer + Scene + Camera; runs the render loop
        ▼
pygfx.WgpuRenderer
        │  depends only on BaseRenderCanvas, not on which concrete
        │  canvas class it was given
```

This is `adr/ADR-003-modular-numerical-strategies.md`'s "implementations
swappable behind a stable interface, selected at construction" pattern,
applied one layer below the whole renderer -- to the *windowing library*
specifically, per `docs/planning/backlog.md` D3's own framing. `pygfx`
and `wgpu` are fixed by `ADR-005`; what is swappable, right now, without
touching `RenderWindow` or the render loop at all, is which windowing
backend supplies the canvas.

## The Canvas Seam

`rendering/canvas.py`'s `create_canvas(config)` is the entire seam: given
a `RenderingConfig`, it returns either a `rendercanvas.glfw.
GlfwRenderCanvas` (interactive) or a `rendercanvas.offscreen.
OffscreenRenderCanvas` (headless -- no window, GUI toolkit, or event
loop; returns rendered frames as a NumPy array directly). Both implement
the same `rendercanvas.base.BaseRenderCanvas` protocol, which is all
`pygfx.WgpuRenderer` actually depends on -- `RenderWindow` never branches
on which one it received.

**Adding a third backend** (Qt/PySide6, the maintainer's stated
long-term ambition for a real GUI toolkit) means adding one branch to
`create_canvas`/`get_loop`, not touching `window.py` or the render loop
-- deliberately not built yet, since Stage 0 does not need it and an
unused abstraction is exactly the speculative complexity the root
`CLAUDE.md` warns against.

**Headless rendering is not a special case bolted on for CI.** It is one
of exactly two backends the same seam already supports, selected the
same way the interactive backend is (`RenderingConfig.backend`) --
what makes D5's golden-demo regression testing and CI both possible
without a display.

## The Render Loop

`RenderWindow.run()` is identical code for both backends up to the point
where the backends' event models diverge:

- **Offscreen** has no event loop (`rendercanvas.offscreen`'s own
  docstring: "No scheduling"). `run()` registers the draw callback via
  `request_draw()` once, then calls `canvas.draw()` directly,
  `max_frames` times (default 1) -- `canvas.draw()`, not
  `renderer.render()` directly, is what actually triggers presentation
  and populates `last_image`; calling `render()` alone renders into the
  texture but is never presented (a real bug found while building D5's
  golden demo, not assumed away -- see `src/pyflow/rendering/CLAUDE.md`).
- **Interactive** backends self-reschedule: each `on_draw` callback
  renders a frame, then calls `canvas.request_draw(on_draw)` again unless
  `max_frames` has been reached, so the window keeps repainting on its
  own until closed. `get_loop(config).run()` then blocks, running the
  backend's real event loop, until the canvas closes.

**`close_keys`** (default `("Escape", "Enter")`) is wired into every
interactive window by default -- not an opt-in. This exists because a
real usability bug reached `pyflow run` itself: every earlier
verification of the render loop used `max_frames` to bound the run, so
the "a real person, with no bound, needs to close this" scenario was
never once exercised before the maintainer hit it directly. It is now
treated as a hard requirement for anything built on `RenderWindow`, not
an optional nicety -- see `src/pyflow/rendering/CLAUDE.md` for the full
account and its regression coverage
(`tests/integration/test_interactive_window.py`).

**`on_frame`**, called once per frame immediately after rendering, is the
hook a future real-time simulation loop will use to advance simulation
state each frame -- the same shape `request_draw` already uses to
advance drawing each frame. It exists today only for the acceptance
suite that proves distinct frames actually render (`RenderWindow.run`'s
own docstring), but it is not a test-only seam: advancing state once per
frame is exactly what driving a live simulation through this render loop
will need, once Stage 1 onward gives `RenderWindow` something to
animate.

## Relation to the Timestep

**Nothing here computes a timestep.** `RenderWindow` and its render loop
are pure presentation -- they own a scene, a camera, and the mechanics of
getting pixels on screen or into a buffer, with no dependency on
`docs/architecture/engine.md`'s numerical layers at all. The relationship
these two documents will eventually need to describe -- how a simulation
timestep and a render frame are scheduled relative to each other (locked
step, decoupled, capped at a target frame rate) -- does not exist yet,
because nothing produces a timestep to schedule against: Stage 0 has no
simulation, only an empty (or single-colour) `Scene`. `on_frame` is the
seam this future scheduling will attach through; the scheduling policy
itself is Stage 1+ work, not specified here ahead of having anything to
schedule.

## Adding a Second Renderer

The maintainer's stated ambition, and consistent with
`adr/ADR-004-compute-rendering-class.md`'s explicit framing of "which
classes keep a second renderer cheap" as its own assessment axis. Given
the layering above, a second renderer is a **construction-time choice**,
the same way canvas backend already is -- provided it can itself
implement (or wrap something implementing) whatever narrow interface
`RenderWindow` is refactored to depend on, rather than depending on
`pygfx.WgpuRenderer` concretely the way it does today. **This refactor
has not happened**: `RenderWindow.__init__` currently constructs a
`pygfx.WgpuRenderer` directly, so today the swappable unit is the
*canvas* (windowing backend), not the *renderer* (pygfx itself). Recorded
here as the honest current state, not glossed over -- the canvas seam is
real precedent for how a renderer seam would be built, not proof one
already exists.

## Data Flow: Compute to Pixels

Per `adr/ADR-004`/`ADR-005`: PyTorch tensors (the array library, once
Stage 1+ populates real field data) round-trip through host memory to
reach wgpu/pygfx's GPU buffers -- there is no confirmed zero-copy path
today. PyTorch's DLPack support and wgpu's compute-shader access on the
same device are a documented but unconfirmed path to a future
optimisation, not relied upon now (`ADR-005`'s own Notes section).
Nothing in the current `RenderWindow`/`canvas.py` implementation assumes
otherwise.

**Field data now does flow through this path** (updated 2026-08-22;
this paragraph said "there is no field data flowing through it yet" until
then, which stopped being true when TASK-017 landed on 2026-08-21).
`scalar_field_colors` (`src/pyflow/rendering/field_visualization.py`)
calls `field.values.numpy()` on a `torch.Tensor` and the resulting
colours reach the GPU through `gfx.Geometry`, which is exactly the
host-memory round trip described above. It is still not a *cost* worth
measuring: the conversion happens once at scene construction, over one
value per mesh cell, not per frame and not per timestep. The claim to
re-examine is the per-frame one, and the first thing that will make it
concrete is a field whose values change while the window is open --
Stage 4 onward, not this.

## What wgpu/pygfx Does Not Provide

`ADR-005`'s accepted trade-off, stated here because it is exactly the
kind of thing a developer approaching Stage 1's Mesh Visualiser
(`docs/planning/roadmap.md` TASK-013) or Stage 2's Field Rendering
(TASK-017) needs to know before starting: **no turnkey colour maps,
vector glyphs, or legends.** VTK/PyVista would have provided these
largely for free; wgpu/pygfx does not, so implementing them is real
PyFlow work, not configuration of an existing feature. Budget for this
as implementation effort in those tasks, not assume it is already
covered by the rendering library.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E2c), against
`src/pyflow/rendering/{canvas,window}.py` as actually implemented (D3-D5)
and `adr/ADR-004`/`ADR-005`'s decision record -- not written speculatively
ahead of the implementation the way `engine.md` necessarily was for
Stage 1+ layers, since the rendering subsystem already exists and this
document describes it as built. Update this document in the same change
as any change to the canvas seam, the render loop's backend branching, or
the renderer-seam refactor noted above as not yet done -- once that
refactor lands, this document's "Adding a Second Renderer" section
becomes the wrong tense and needs rewriting, not just a note appended.

Reviewed 2026-08-18: the header previously read "Per KA §11
(`engine.md`'s neighbouring, un-numbered architecture document -- see that
file's own header for why no KA entry exists for either)", which was wrong
twice over -- `engine.md` *is* numbered (KA-029), and its header does not
discuss this document at all. The reasoning lives in
`docs/architecture/CLAUDE.md`, which the header now points at.
