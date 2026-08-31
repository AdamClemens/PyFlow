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
that's Lid-Driven Cavity below (Capability Level 2), built by TASK-034
and the reason `mvp.md` now records the MVP as reached. Empty Window
exists purely to prove Stage 0's infrastructure works, before there is
any simulation to demonstrate.

*(This sentence read "the Initial Golden Demo below (Capability Level
1)" until the Stage 5 exit audit, 2026-08-29 -- wrong in both halves
once TASK-034 landed: the section it points at was renamed to the demo
it actually built, and the lid-driven cavity is `implementation-plan.md`
Level 2, never Level 1. `planning/data/demos.yaml`'s own
`demo-lid-driven-cavity -> capability-level-2` edge had said so all
along, which is exactly the kind of disagreement between a graph edge
and a hand-restated fact that `adr/ADR-006-knowledge-graph-scope.md`
moved relationships into the graph to avoid.)*

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

## Numerics Assembly

TASK-021's own golden demo (`docs/planning/roadmap.md`, Stage 3
Completion Criterion 8) -- "Engine initialises entirely through
interfaces. No CFD yet." Proves that the six `adr/ADR-003-modular-
numerical-strategies.md` components (`engine/numerics/assembly.py`'s
registry) resolve from configuration to real instances end to end,
through the real CLI, with **no new rendered output**: this is the
stage's honest carve-out (Stage 3 Completion Criterion 8) rather than an
oversight, since Stage 3 adds no visualisation of its own.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/numerics_assembly.yaml` -- a
  `numerics` section naming all six components explicitly (even though
  every value is already `NumericsConfig`'s own default), run via
  `uv run python -m pyflow run --config examples/golden-demos/numerics_assembly.yaml`;
- `pyflow run` assembles all six and reports the assembled set, both as
  a log line and as `RenderWindow.assembled_numerics` -- checked by
  calling `bootstrap()` directly and comparing the reported set against
  the YAML's own `numerics` section, not just "it didn't raise";
- assembling the same configuration twice reports an identical set
  (`tests/golden/test_numerics_assembly.py`'s determinism scenario);
- **adding a `numerics` section to an existing demo's config changes
  nothing about what renders** -- checked directly against
  `field_display.yaml`: the same config, with and without an explicit
  (non-default) `numerics` section, renders pixel-identical output. This
  is the specific claim the "no new rendered output" carve-out rests on,
  not merely asserted;
- it runs headlessly via `--backend offscreen`, same as every other
  demo.

**What "assembled" means here is deliberately not physical.** No
concrete implementation of any of the six components ships under `src/`
this stage (Stage 3 Completion Criterion 1) -- `assemble_numerics`
resolves each configured name to a trivial, non-physical reference
implementation (`engine/numerics/assembly.py`'s own docstring explains
why one exists under `src/` at all: a real CLI subprocess needs
*something* to assemble into). This demo proves the assembly mechanism
works, not that PyFlow computes anything yet; the first demo that
computes real physics is Passive Scalar Transport, below (Stage 4).

## Passive Scalar Transport

TASK-030's own golden demo (`docs/planning/roadmap.md`, Stage 4
Completion Criterion 1) -- PyFlow's first demo that computes real
physics, and the first `pyflow run` that steps a real simulation
forward *live*, one timestep per rendered frame, rather than rendering
one static picture. Called "Scalar Transport" in
`docs/planning/implementation-plan.md`'s own Golden Demos table and
`planning/data/demos.yaml` (`demo-scalar-transport`) -- the same demo,
named there before it was built; `mvp.md`'s own validation bullet and
this task's own roadmap entry both say "Passive scalar transport",
which is the name used here and for the real artifact
(`passive_scalar_transport.yaml`). Not reconciled across those two
documents in this change -- noted here rather than left silent, per the
Blast Radius rule's "if something in the radius cannot be updated now,
say so explicitly."

"Working" means, concretely:

- the demo *is* `examples/golden-demos/passive_scalar_transport.yaml` --
  a `fields:` section declaring one named field's `gaussian_blob`
  initial condition and diffusivity (`FieldConfig`,
  `src/pyflow/configuration/schema.py`, TASK-042), a `simulation`
  section naming the `uniform` prescribed velocity that transports it, a
  `numerics` section whose east/west boundaries are `periodic` and
  north/south are `neumann` (zero gradient -- the prescribed velocity is
  purely horizontal, so nothing crosses them, but diffusion still needs
  some condition there regardless of flow direction), run via
  `uv run python -m pyflow run --config examples/golden-demos/passive_scalar_transport.yaml`;
- a real `simulation.step()` call advances the field once per rendered
  frame (`src/pyflow/bootstrap.py`'s `_add_declared_field_transport`,
  wired through `RenderWindow.run(on_frame=...)`) -- checked directly,
  not only by pixel-diffing: the field's own mass-weighted centroid
  moves downstream by approximately the prescribed velocity times the
  elapsed real time, measured across two independent real runs at
  different frame counts (`tests/golden/test_passive_scalar_transport.py`),
  within a tolerance derived from an actual measured run (~4% agreement),
  not guessed;
- the periodic wrap is exercised by this live run, not only proven in
  isolation: rendered offscreen at increasing frame counts, the blob is
  seen translating downstream and, once total elapsed travel reaches one
  full domain width, reappearing spread across both the east and west
  edges -- verified visually during this task's own build, not asserted
  by the regression test above (which checks displacement over a
  shorter interval, before any wrap occurs, per its own module
  docstring); the wrap's own correctness claim belongs to
  `periodic_boundary.feature`, checked in isolation as a convergence
  property (see that task's own Design decisions,
  `docs/planning/roadmap.md` TASK-030);
- it runs headlessly via `--backend offscreen`, same as every other
  demo.

**The velocity field is prescribed, not solved** -- for this demo, and
deliberately so. Stage 5 solved Navier-Stokes for real (TASK-034,
2026-08-29; see the Lid-Driven Cavity entry below for the demo that
renders a *solved* field), but this one's velocity stays a fixed,
uniform vector from configuration, transporting the scalar the same way
a wind field transports smoke without itself being computed from the
smoke. That is the whole point of it: it isolates transport from the
coupled solve, which is what makes it still worth running after the
coupled solve exists.

## Lid-Driven Cavity

TASK-034's own golden demo (`docs/planning/roadmap.md`, Stage 5
Completion Criterion 8) -- **the Initial Golden Demo described below,
now built.** A square cavity, no-slip on every wall, the top wall
moving tangentially at a constant speed: the classic incompressible
Navier-Stokes benchmark, and the demo the MVP's own Definition of Done
refers to as "golden demo exists."

"Working" means, concretely:

- the demo *is* `examples/golden-demos/lid_driven_cavity.yaml` -- a
  `numerics.boundary_conditions.north.field_values` entry
  (`velocity.0`/`velocity.1`, `VectorField.component_name`) sets the
  lid's own tangential-only prescribed velocity, every other wall keeps
  the schema's own no-slip default; `simulation.velocity_solved: true`
  with no `fields:` declared selects `bootstrap.py`'s own velocity-only
  live path (`_add_solved_velocity_rendering`); run via
  `uv run python -m pyflow run --config examples/golden-demos/lid_driven_cavity.yaml`;
- every rendered frame is a real `simulation.navier_stokes_step()` call
  -- predictor, corrector, corrected state -- not only `simulation.step()`
  (`_add_passive_scalar_transport`'s own `velocity_solved` path never
  pressure-corrects, a genuine pre-existing gap this task's own
  `navier_stokes_step` is what actually closes for a live run);
- the velocity field is rendered as arrows (`build_vector_field_arrows`,
  TASK-017, rebuilt every frame the same "remove the old object, build a
  new one" way the scalar demo's own mesh is) -- **the first velocity
  field PyFlow has ever rendered that was *solved*, not prescribed or
  seeded** (`docs/implementation/mvp.md`'s own "visualisation shows the
  result", true here for the first time);
- `tests/golden/test_lid_driven_cavity.py` checks the demo is
  reproducible via the real CLI, that the rendered velocity has genuinely
  moved away from its at-rest initial condition, and that the same
  configuration run twice is bit-identical;
- it runs headlessly via `--backend offscreen`, same as every other demo.

**The quantitative comparison against Ghia, Ghia & Shin (1982) is not
this file's own regression test.** `tests/features/
navier_stokes_timestep.feature`'s own scenario runs the comparison
directly against the engine at three mesh resolutions to a measured
steady state -- the most computationally expensive check in this
project, deliberately kept separate from a demo's own lightweight
reproducibility smoke test (`docs/planning/roadmap.md` TASK-034's own
Design decision). This demo's own regression test does not assert an
absolute divergence bound either, for a related, measured reason: at
this demo's own coarse mesh and early frame count, `GreenGaussDivergence`'s
naive face-averaged divergence is not the Rhie-Chow-consistent measure
`PISO`'s own corrector loop actually drives to tolerance, and is
additionally distorted near the lid's own two corner singularities (a
genuine, well-documented property of this exact benchmark, not an
artefact) -- see `tests/golden/test_lid_driven_cavity.py`'s own module
docstring for the measured finding.

## Heat Diffusion

TASK-034's second golden demo -- Stage 5's own reconciliation of
`docs/implementation/mvp.md`'s Validation section (2026-08-28,
maintainer's call, `docs/planning/roadmap.md` Stage 5 Completion
Criterion 8): heat diffusion *is* the diffusion equation on a
transported scalar, with no named Temperature field needed (that field,
and its buoyancy coupling, is Stage 6's TASK-035 -- a genuinely
different claim, not this one repeated). `docs/planning/
implementation-plan.md` and `planning/data/demos.yaml` are amended in
the same change as that decision, not left to diverge.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/heat_diffusion.yaml` -- a
  declared field (`fields:`, TASK-042) whose `initial_condition:
  sinusoidal_mode` (TASK-034's own new pattern, `bootstrap.py`'s
  `_simulation_scalar_initializer`) and own `diffusion_coefficient` seed
  a single spatial Fourier mode, one full wavelength across the mesh's
  own x-extent, on a domain periodic on every edge and no prescribed
  velocity at all -- pure diffusion, no advection; run via
  `uv run python -m pyflow run --config examples/golden-demos/heat_diffusion.yaml`;
- **it validates something quantitative, per `mvp.md`'s own Validation
  section rather than its Components one**: a single mode decays
  exponentially at a rate set only by the declared field's own
  `diffusion_coefficient` and the mode's own wavenumber -- an exact,
  closed-form answer, checked
  directly (`tests/golden/test_heat_diffusion.py`, the same "bootstrap
  at two frame counts, measure across real elapsed time"
  shape `test_passive_scalar_transport.py` already established), not
  only "heat visibly spread". Distinct from Stage 4's own diffusion
  criteria (`central_difference_diffusion.feature`), which measured
  spatial convergence order and conservation -- neither of which is a
  decay *rate*;
- it runs headlessly via `--backend offscreen`, same as every other demo.

## Heat Transport

TASK-035's first golden demo -- `docs/planning/implementation-plan.md`
Level 3's own named-Temperature demo, reusing Heat Diffusion's own
physics (above) on a field the configuration actually names
`temperature`. This demo's whole content is that naming the field and
giving it a real identity costs nothing -- no buoyancy coupling here
(Thermal Buoyancy, below, is that demo).

"Working" means, concretely:

- the demo *is* `examples/golden-demos/heat_transport.yaml` -- identical
  mesh, timestep and diffusion coefficient to `heat_diffusion.yaml`, the
  one declared field named `temperature` instead of `tracer`; run via
  `uv run python -m pyflow run --config examples/golden-demos/heat_transport.yaml`;
- it validates the same quantitative claim Heat Diffusion does, checked
  directly (`tests/golden/test_heat_transport.py`, reusing that module's
  own two-frame-count decay measurement) -- **and the two measured rates
  agree**, since that agreement is the entire content of this demo's own
  claim that naming a field costs nothing;
- it runs headlessly via `--backend offscreen`, same as every other demo.

## Thermal Buoyancy

TASK-035's second golden demo -- `docs/planning/implementation-plan.md`
Level 3's own Golden Demo list. A warm patch in an otherwise still,
uniform-temperature domain rises under a Boussinesq body force --
`tests/features/temperature_field.feature`'s own "warm fluid rises"
claim (`tests/unit/test_temperature_field.py`), demonstrated here as a
reproducible, visible run rather than re-validated.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/thermal_buoyancy.yaml` -- a
  declared `temperature` field (`initial_condition: gaussian_blob`) with
  its own buoyancy coupling (`buoyancy_reference_value`/
  `buoyancy_coefficient`), `numerics.source_term: boussinesq_buoyancy`,
  and `simulation.velocity_solved: true` together -- the first golden
  demo combining a declared field with solved, pressure-corrected
  velocity in one run. `bootstrap.py`'s `_add_declared_field_transport`
  (TASK-042) already supported this combination generically, so no
  `bootstrap.py` change was needed to build this demo; run via
  `uv run python -m pyflow run --config examples/golden-demos/thermal_buoyancy.yaml`;
- **it validates something quantitative, not just "something moved"**:
  the temperature field's own warmest cell has positive (upward)
  vertical velocity after several real timesteps, checked directly
  (`tests/golden/test_thermal_buoyancy.py`) against the sign design
  question derived in advance (`docs/planning/roadmap.md` TASK-035's own
  "The sign, derived here" section) rather than read off the
  implementation;
- it runs headlessly via `--backend offscreen`, same as every other demo.

## Smoke Transport

TASK-038's own golden demo -- `docs/planning/implementation-plan.md`
Level 3's own Golden Demo list, and Stage 6's third and last demo
(`planning/data/demos.yaml`'s `demo-smoke-transport`: "Passive tracers
carried by a solved velocity field, with no effect on it"). The same
lid-driven-cavity flow `lid_driven_cavity.yaml` already proved stable,
now also carrying a declared `smoke` field.

"Working" means, concretely:

- the demo *is* `examples/golden-demos/smoke_transport.yaml` -- an
  identical mesh, timestep, viscosity and moving-lid boundary to
  `lid_driven_cavity.yaml`, plus one declared `smoke` field
  (`initial_condition: gaussian_blob`, `fields:`, TASK-042) and no
  buoyancy coupling; run via
  `uv run python -m pyflow run --config examples/golden-demos/smoke_transport.yaml`;
- the smoke field is genuinely carried by the recirculating flow, checked
  directly (`tests/golden/test_smoke_transport.py`, the same "bootstrap
  at two frame counts, compare" shape `test_heat_diffusion.py`/
  `test_heat_transport.py` already established) -- not only "something
  rendered";
- **the exactness of "passive" is deliberately not re-proven here.**
  Stage 6 Completion Criterion 5's own claim (no measurable effect on
  velocity, and not itself inert) is `tests/features/passive_tracers.
  feature`, checked against a small, purpose-built fixture with and
  without the tracer declared -- this demo's own job, per the Definition
  of Done above, is a reproducible, visible run, not a second copy of
  that proof;
- it runs headlessly via `--backend offscreen`, same as every other demo.

## Future Demos

Add an entry here when a new capability is implemented, per
`docs/planning/implementation-plan.md`'s Golden Demos table (Poiseuille
Flow, Rayleigh-Bénard Convection, Taylor-Green Vortex,
Kelvin-Helmholtz Instability, Flow Around Cylinder, Vortex, Dam Break,
3D Cavity -- Thermal Buoyancy and Smoke Transport moved to their own
sections above now that TASK-035/038 built them; this parenthetical is a
restated list and went stale the moment each happened, which is why it
is amended in the same change rather than after --
**Scalar Transport, Heat Diffusion, Lid-Driven Cavity, Heat Transport,
Thermal Buoyancy and Smoke Transport are built and have their own
sections above, not listed here any more.** The remaining ones added
2026-08-20, `docs/planning/backlog.md` "physical correctness
validation". Do not add a demo entry for a capability that doesn't
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
`empty_window.yaml`; the Lid-Driven Cavity's (the demo this file used to
call "Initial Golden Demo" before TASK-034 built it) is
`lid_driven_cavity.yaml` -- this is the specification, not the
implementation.
