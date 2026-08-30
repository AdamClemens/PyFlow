# CLAUDE

Golden demo *configuration*, not code. The specification -- what each
demo must do, how it's verified -- lives at
`docs/implementation/golden-demos.md` (KA-035), not here.

**A golden demo is a config file plus the public `pyflow run` command --
never a bespoke script.** (Maintainer's rule, 2026-08-16.) A user must be
able to replicate a demo exactly and simply: `uv run python -m pyflow
run --config examples/golden-demos/<name>.yaml`. If a demo needs
something configuration doesn't yet expose, add that capability to
`src/pyflow/configuration/schema.py` -- a public, documented option
anyone can use -- rather than writing demo-specific Python that reaches
around it. This directory used to hold `empty_window.py`, a script that
called `RenderWindow` directly; it was replaced the same day the rule
was written, once the one thing that made it "Empty Window" (a solid
background colour) became `RenderingConfig.background_color`, a real
configuration option instead of code.

Nine demos live here as of 2026-08-30 (TASK-035, Stage 6), one per
stage that has produced a visible capability, plus one that deliberately
has nothing new to render:

- `empty_window.yaml` (D5, 2026-08-16), Capability Level 0's: sets
  `rendering.background_color`, nothing else -- everything about running
  it (window size, interactive vs. headless, how many frames) is already
  a `pyflow run` concern, not this demo's.
- `empty_mesh.yaml` (TASK-013, 2026-08-20), Stage 1's: `show_mesh`, a
  grid colour, a background colour, and no `mesh:` section at all, since
  `MeshConfig`'s defaults are already a reasonable mesh to draw.
- `field_display.yaml` (TASK-017, 2026-08-21), Stage 2's: one scalar
  pattern and one vector pattern from `FieldDisplayConfig`'s closed set,
  drawn together over one mesh with a shared legend.
- `numerics_assembly.yaml` (TASK-021, 2026-08-23), Stage 3's: a
  `numerics` section naming all six `adr/ADR-003-modular-numerical-
  strategies.md` components explicitly, deliberately no `mesh`/
  `field_display` section at all -- Stage 3's honest "no new rendered
  output" carve-out means this demo proves configuration assembles into
  real (if physically trivial) instances, not that anything new
  appears on screen.
- `passive_scalar_transport.yaml` (TASK-030, 2026-08-28), Stage 4's --
  PyFlow's first demo that computes real physics, and the first
  `pyflow run` that steps a real simulation forward live rather than
  rendering one static frame: a `fields` section (`gaussian_blob`
  initial condition and its own diffusivity, TASK-042) plus a
  `simulation` section (`uniform` prescribed velocity) and a `numerics`
  section whose east/west edges are `periodic`. See
  `docs/implementation/golden-demos.md`'s own section for what "working"
  means concretely.
- `heat_diffusion.yaml` (TASK-034, 2026-08-29), Stage 5's own
  reconciliation of `mvp.md`'s Validation section: a single sinusoidal
  mode (a declared field's own `initial_condition: sinusoidal_mode` and
  `diffusion_coefficient`, `fields:`, TASK-042 -- lived under
  `simulation.scalar_pattern` until that section's migration) decaying
  on a fully periodic domain with no velocity at all -- pure diffusion,
  checked against its own exact closed-form decay rate.
- `lid_driven_cavity.yaml` (TASK-034, 2026-08-29), Stage 5's own -- the
  MVP's own golden demo (this document used to call it "the Initial
  Golden Demo" before this task built it). `simulation.velocity_solved:
  true` with no `fields:` declared selects `bootstrap.py`'s own new
  velocity-only live path; the moving lid is a `numerics.
  boundary_conditions.north.field_values` entry
  (`velocity.0`/`velocity.1`), not a new config field -- see this task's
  own roadmap entry for why `velocity_tangential` (Stage 5's own design
  question two) was never built.
- `heat_transport.yaml` (TASK-035, 2026-08-30), Stage 6's own: identical
  physics to `heat_diffusion.yaml` above, on a field the configuration
  actually names `temperature` -- this demo's whole content is that
  naming the field costs nothing. No buoyancy coupling here.
- `thermal_buoyancy.yaml` (TASK-035, 2026-08-30), Stage 6's other: a
  warm patch (`initial_condition: gaussian_blob`) rises under a
  Boussinesq body force -- `fields:`'s own `buoyancy_reference_value`/
  `buoyancy_coefficient`, `numerics.source_term: boussinesq_buoyancy`,
  `simulation.velocity_solved: true` together. The first demo combining
  a declared field with solved velocity; `_add_declared_field_transport`
  (TASK-042) already handled that combination generically, so nothing in
  `bootstrap.py` needed to change to run it. Mesh kept deliberately small
  (12x16) -- `PISO`'s dense Poisson matrix construction cost is what
  gates this demo's own runtime, measured directly before settling on
  this resolution (a 24x32 mesh cost roughly 5x longer per `bootstrap()`
  call for no additional demonstrative value).

Every demo here should follow the same shape:

- a plain YAML file setting only what makes that demo *that demo* --
  resist the pull to also pin window size, backend, or anything else
  `pyflow run`'s own flags already cover. **`field_display.yaml` is the
  one standing exception, and it states its own reason in a comment at
  the top of the file**: it pins `rendering.width`/`height` to 250x290
  so the canvas aspect exactly matches the framed view's, which is what
  lets its tests predict where each cell lands in pixels rather than
  only asserting a colour exists somewhere. Break this rule the same
  way -- because a test needs a specific, checkable geometry -- or not
  at all;
- `tests/golden/test_<name>.py` must include at least one test that runs
  it exactly as a user would: the real CLI, as a subprocess, with
  `--config examples/golden-demos/<name>.yaml`. `--backend offscreen` is
  the one sanctioned override, for headless CI -- a user could type that
  same flag themselves for the same reason;
- deeper verification (pixel content, determinism) can use
  `pyflow.bootstrap.bootstrap()` directly -- still the public API, just
  the Python entry point rather than the CLI one, used because it's the
  only way to get the rendered frame back for inspection.

**Closing an interactive window by keypress (Escape/Enter) is
`RenderWindow.run()`'s own default** (`src/pyflow/rendering/window.py`,
`close_keys`), on for every interactive window PyFlow opens, not
something a demo needs to arrange. Nothing to do here for a new demo.
