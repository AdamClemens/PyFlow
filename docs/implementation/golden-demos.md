# PyFlow Golden Demo Specification

Per `docs/planning/knowledge-architecture.md` KA-035.

## Intent

A golden demo is both a useful demonstration and a functional regression
test of a meaningful vertical slice. Every Golden Demo listed in
`docs/planning/implementation-plan.md` ("Golden Demos" table) should
eventually have an entry here defining what "working" means for it
concretely enough to verify automatically.

## Where a demo's criteria actually live

**Since 2026-08-22, in `tests/features/<demo>.feature`** --
`adr/ADR-007-executable-acceptance-criteria.md`. Each demo's section
below describes what the demo *is* and why it exists; the scenarios in
its feature file are what "working" means, executably, and are the only
statement of it.

That split is deliberate. This document is for a reader deciding whether
a demo is worth having; the feature file is for deciding whether it
works. Before the retrofit both lived here as prose, and the prose could
be -- and in TASK-017's case was -- satisfied by a test that asserted
less than it said.

## Definition of Done (applies to every golden demo)

- Executable.
- Deterministic, or its non-determinism is appropriately controlled
  (e.g. a fixed random seed).
- Verifies meaningful behaviour, not just "it ran without crashing."
- Produces useful visual output where applicable.
- Documented.
- Included in regression testing.
- **Runs entirely through the public API.** (Added 2026-08-16, maintainer's
  rule.) A user must be able to replicate a golden demo exactly and
  simply -- which means a demo is "the relevant command, plus the
  specific configuration it needs," not a bespoke script that happens to
  call internal classes directly. Concretely: a demo's identity lives in
  a plain configuration file under `examples/golden-demos/`, and it is
  run via `pyflow run --config <that file>` -- the same command, and the
  same public `pyflow.bootstrap.bootstrap()` function underneath it, that
  any user has available. If a demo needs a capability configuration
  doesn't yet expose, that capability gets added to the public
  configuration schema (`src/pyflow/configuration/schema.py`) -- the
  fix is never demo-specific code working around the gap. **At least one
  regression test per demo must invoke it exactly this way** (the real
  CLI, as a subprocess, with the demo's own config file), not only
  through a shortcut that happens to produce the same result.

## Empty Window

Capability Level 0's golden demo (`implementation-plan.md`'s Golden
Demos table: "Empty Window | Rendering"). The simplest possible demo:
open a rendering window, display an empty scene, close cleanly. It
validates the Stage 0 engineering bootstrap chain (TASK-005/006/007/010,
`docs/planning/backlog.md` D1-D4) end to end -- not any CFD
functionality, since there isn't any yet.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/empty_window.yaml` -- one
  `rendering.background_color` setting, nothing else -- run via
  `uv run python -m pyflow run --config examples/golden-demos/empty_window.yaml`.
  There is no `empty_window.py`; the public configuration schema
  (`RenderingConfig.background_color`, added specifically so this demo
  could exist without bespoke code) is the only thing that makes this
  demo distinct from a bare `pyflow run`;
- a frame actually renders and gets presented -- one solid, deterministic
  background colour (`#1a1a2e`), not pygfx's default transparent black,
  so there is something concrete to assert on rather than "it didn't
  crash";
- the window closes cleanly, no unhandled exceptions;
- it runs headlessly via `--backend offscreen` for CI/regression use
  (`tests/golden/test_empty_window.py`) -- the same config file, the same
  command, with the one CLI override that turns any interactive run
  into a headless one -- and interactively (the config's own default,
  `glfw`) for a human actually watching it.

Not the same demo `mvp.md`'s "golden demo exists" criterion refers to --
that's the Initial Golden Demo below (Capability Level 1). Empty Window
exists purely to prove Stage 0's infrastructure works, before there is
any simulation to demonstrate.

## Empty Mesh

TASK-013's own golden demo (`docs/planning/roadmap.md`, "display an
empty computational mesh") -- Stage 1's proof that the Mesh layer
(TASK-011/012) and its visualisation (TASK-013) work together, still
before any physics exists.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/empty_mesh.yaml` -- a
  `rendering.show_mesh` switch, a `grid_color`, and a
  `background_color` for contrast,
  no `mesh:` section (`MeshConfig`'s own defaults -- a 10x10 uniform grid
  -- are already a reasonable mesh to display), run via
  `uv run python -m pyflow run --config examples/golden-demos/empty_mesh.yaml`;
- a frame renders and gets presented with both the configured grid-line
  colour and the configured background colour genuinely present as exact
  pixel values (`tests/golden/test_empty_mesh.py`) -- not just "the demo
  ran", and not just one of the two colours (a grid that failed to
  render at all would still show the background alone);
- the window closes cleanly;
- it runs headlessly via `--backend offscreen` for CI/regression use,
  same as Empty Window.

Zoom and pan (also TASK-013) are exercised more thoroughly by
`tests/unit/test_rendering.py` (the underlying camera-control logic) and
`tests/integration/test_interactive_window.py` (the real, live
mouse-wheel/pointer-drag wiring, skipped without a display) than by this
golden demo itself -- the demo's own job is proving the config-driven,
headless path works, per the Definition of Done above; live
interactivity isn't something an offscreen regression test can exercise
meaningfully.

## Field Display

TASK-017's own golden demo (`docs/planning/roadmap.md`, "display scalar
and vector fields") -- Stage 2's proof that the Variables layer
(TASK-014/015/016) and its visualisation (TASK-017) work together over
Stage 1's mesh, still before any physics exists. The fields hold values;
nothing yet transports them.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/field_display.yaml` -- a
  `field_display` section naming one scalar pattern
  (`radial_gradient`) and one vector pattern (`rotational`), their
  colours and value range, plus a `mesh.extent` and the window size,
  run via
  `uv run python -m pyflow run --config examples/golden-demos/field_display.yaml`;
- both fields render together: every cell's fill colour matches
  `scalar_field_colors`'s output for that cell's value **at that cell's
  own predicted screen position**, not merely "a pixel of this colour
  exists somewhere" -- the level of checking `empty_mesh.yaml` does not
  attempt, made possible here by choosing a canvas aspect ratio equal to
  the framed view's so the world-to-pixel mapping is exactly linear
  (`src/pyflow/rendering/CLAUDE.md`);
- the arrows are real: a segment at each cell whose direction and length
  match `build_vector_field_arrows`, and **no** segment at a cell whose
  vector is exactly zero;
- the legend is drawn from the same colour function the field is, which
  the test checks by sampling it rather than by inspecting the code.
  Numeric labels on the legend are deliberately not claimed -- see
  TASK-017's design decisions for why pygfx text rendering was not
  committed to unverified;
- the window closes cleanly, and it runs headlessly via
  `--backend offscreen`, same as Empty Window and Empty Mesh.

**This demo pins window size, which the other two deliberately do not**
(`examples/golden-demos/CLAUDE.md` tells a demo author to resist exactly
that). The exception is stated rather than silent: `rendering.width`/
`height` are 250x290 so the canvas aspect matches the framed bounding
box's 25:29, which is what makes per-cell pixel positions predictable
without correcting for pygfx's `maintain_aspect`. A demo that only
asserted "this colour appears somewhere" would not need it.

## Initial Golden Demo

A 2D air-current simulation, corresponding to the MVP
(`docs/implementation/mvp.md`). It must:

- construct the domain (structured 2D Cartesian mesh);
- configure the numerical components (via `src/pyflow/configuration/`,
  not hardcoded -- see `adr/ADR-003-modular-numerical-strategies.md`);
- execute timesteps;
- produce measurable velocity fields;
- render the result.

This is the demo the MVP's own Definition of Done refers to as "golden
demo exists."

## Future Demos

Add an entry here when a new capability is implemented, per
`docs/planning/implementation-plan.md`'s Golden Demos table (Scalar
Transport, Heat Diffusion, Poiseuille Flow, Lid-Driven Cavity,
Rayleigh-Bénard Convection, Taylor-Green Vortex, Kelvin-Helmholtz
Instability, Flow Around Cylinder, Vortex, Dam Break, 3D Cavity -- the
four added 2026-08-20, `docs/planning/backlog.md` "physical correctness
validation"). Do not add a demo entry for a capability that doesn't
exist yet -- these get written when the corresponding capability level
is reached, not speculatively ahead of it.

**The four added 2026-08-20 exist specifically to validate physical
correctness, not just demonstrate a capability** -- unlike every demo
already in this list, each has a known right answer (an analytical
solution, a critical parameter value, a published correlation) to check
against, not just "did it run and look plausible." When one is written,
its Definition of Done (above) still applies in full, plus a specific,
quantitative pass/fail check against that known answer -- see
`docs/planning/backlog.md` for what each one checks concretely.

## Relationship to `examples/golden-demos/`

This file defines *what* each golden demo must do and how it's verified.
`examples/golden-demos/` holds each demo's actual configuration file --
not code, per the public-API rule above. Empty Window's is
`empty_window.yaml`; the Initial Golden Demo's doesn't exist yet, since
the demo it configures doesn't either -- this is the specification, not
the implementation.
