# PyFlow

> A modern, extensible fluid dynamics simulation engine focused on beautiful visualisation, scientific correctness, and maintainable engineering.

---

## Project Status

**Current Version:** 0.3.0 — cut 2026-09-03 when Stage 7 (Rendering Annotations) closed (`docs/planning/releases.md`).

PyFlow has completed **Stage 7 (Rendering Annotations)** and has not yet
begun Stage 9 (Better Numerics) -- Stage 8 (Recording & Playback), added
2026-09-07, comes first. Stage 0 built
the engineering
foundations; Stage 1 added the first real engine code -- a
`CoordinateSystem`, a `Mesh` with a structured Cartesian implementation,
and a mesh visualiser you can zoom and pan; Stage 2 added `Field` and
its scalar and vector implementations, plus the rendering that makes
them visible; Stage 3 added the six `adr/ADR-003-modular-numerical-
strategies.md` interfaces (advection, diffusion, time integration,
pressure-velocity coupling, linear solver, boundary condition) and the
configuration/assembly mechanism that resolves a configured name to a
real instance, with every interface still resolving only to a trivial,
non-physical reference implementation; Stage 4 gave each of those six
interfaces its first real, physically meaningful implementation
(`FirstOrderUpwindAdvection`, `CentralDifferenceDiffusion`, `RK4Integrator`,
`ConjugateGradientSolver`, `PISO`, `Dirichlet`/`Neumann`/periodic boundary
conditions) and, with them, PyFlow's first live-stepping simulation;
Stage 5 assembled those schemes into a real coupled velocity/pressure
solve (`navier_stokes_step`, a genuinely multi-pass `PISO`, pressure
solved from the incompressibility constraint) and, with it, PyFlow's
MVP -- see the Lid-Driven Cavity demo below; and Stage 6 added four
named transported physical fields (temperature, density, humidity,
passive tracers) and a Boussinesq buoyancy coupling, **three of its five
tasks adding no engine code at all** -- a field is a `fields:` entry in
a configuration file, not a class. See
`docs/planning/roadmap.md` for the per-task status
and each stage's exit audit, and `docs/implementation/golden-demos.md`
for what each stage's demonstration proves.

The project's primary objective is to build a reusable fluid simulation engine while documenting every significant engineering decision along the way.

---

## Vision

PyFlow aims to become a platform for exploring fluid dynamics through interactive simulation.

The project prioritises:

- scientific correctness where practical
- incremental development
- excellent visualisation
- maintainability
- enjoyable engineering

Every stage after Stage 0 produces a working, visible demonstration
(P-004, `docs/engineering-principles.md`). Not necessarily a
*simulation* -- Stage 1's demonstration draws an empty computational
mesh, which is exactly what "the domain is representable" looks like
when nothing is being transported through it yet. This line said
"working simulation" until 2026-08-21, overstating the principle it
was paraphrasing.

---

## Repository Philosophy

The repository is designed to explain itself.

Rather than relying on memory, project knowledge is captured explicitly through documentation, architectural decisions, and generated planning artefacts.

---

## Quick Start

Requires [`uv`](https://docs.astral.sh/uv/) and `make`. PyFlow tracks a
current Python version rather than an old floor -- see `.python-version`
and `docs/practices.md`'s Python version policy; `uv` provisions it
automatically, nothing to install separately.

In a clone of this repository:

```bash
make install   # creates .venv, installs dependencies, installs the git pre-commit hook
```

Then:

```bash
make demo      # opens the render window with the built-in default config -- press Escape/Enter or close the window to exit (no simulation configured by default; see "Current Phase" below for one that steps live)
make test      # runs the test suite, with a coverage report
make lint      # formats and lints code and docs (see the Makefile's own comment for exactly what runs)
make ci        # the full sequence CI runs on every push and pull request -- lint, typecheck, test, and the documentation/graph/inventory/manifest checks; see CLAUDE.md for what each one covers
```

To remove everything `make install` set up:

```bash
make clean
```

`make clean` prints what it can't remove and why when it runs -- run it
to see the current, authoritative list rather than trusting a copy of it
here, which could drift.

This section must stay current as functionality is added -- see
`docs/practices.md`.

---

## Where to Start

If you're new to the project, read these documents in order:

1. `CLAUDE.md` — the project's operating rules
2. `docs/glossary.md` — terminology, including what Stage, Capability
   Level and Release each mean here
3. `docs/practices.md` — how work is conducted
4. `docs/planning/capability-map.md` — what PyFlow is meant to be able to do
5. `docs/planning/roadmap.md` — what is being built, and what is done
6. `docs/planning/backlog.md` — what is outstanding and what is undecided

`docs/repository-manifest.md` is the inventory of every maintained
artifact if you want to know what exists before reading any of it.
`docs/index.md` is the full, generated map of every documentation page
grouped by directory, for once you know what you're looking for and just
need to find it.

---

## Current Phase

Stage 9 — Better Numerics -- not yet started. Stage 8 (Recording &
Playback) was **reopened and reclosed on the same day, 2026-09-09**: an
audit, prompted by the maintainer's own suspicion that it "never
actually went through a design/planning session," found the suspicion
correct. Its original five completion criteria (TASK-045/046/047,
2026-09-07) had stayed met; four more were added the same day they were
found missing -- the Goal's own "scrubbed to any point" had shipped
with no seek mechanism at all, and two of the stage's own stated
deferrals (declared-field playback, partial-overlap cache reuse) plus
one gap nobody had named (checkpoint retention) were pulled forward
rather than left indefinitely deferred. TASK-049/050/048/051 closed all
four, one branch each, the same day. Its live status, generated from
the roadmap rather than restated here:
[Stage 8 in the status report](docs/planning/status.md#stage-8----recording--playback).

**Stage 8's own record, for anyone tracking how reliably this section
stays current**: opened and closed in one day (2026-09-07), reopened
two days later, and reclosed the same day it was reopened -- each edit
to this paragraph has so far landed in the same change as the roadmap
event it describes, unlike the multi-day staleness windows the two
paragraphs below describe for Stages 7 and 8's own *earlier* drafts.
Don't read this as the pattern solved; read Stage 9's own eventual
entry here as the next real test of it.

**This sentence said "not yet started" for Stage 8 itself, twice, while
that stage was still open** -- once for the same reason a fourth time as
Stage 7's own case below (TASK-045 landed the same day the stage was
inserted, and the first draft of this update again left the word
stale), and a second time for a related but distinct reason: Stage 8's
own `Status as of` heading initially used free text that satisfied
`check_stages.py`'s looser "starts with 'Status as of'" match but not
`generate_status_report.py`'s stricter template, so the status line was
invisible to the checker rather than merely agreeing with a stale prose
claim. See `docs/planning/roadmap.md`'s own Stage 8 Status section for
that fix, and its own "Golden Demo" entry for the one real
course-correction along the way (Heat Diffusion turned out incompatible
with playback's own scope, found only once TASK-047 was actually
scoped, and the whole stage reconciled onto Lid-Driven Cavity instead).

**This sentence said "Stage 7 -- not yet started" for three days after
that stage's only task landed**, and `make check-status` did not catch
it: that check compares the stage this section *names* against the
roadmap's first stage not marked complete, and Stage 7 had no status
line at all, so both agreed on the number while the prose was wrong
about what had happened to it. Recorded because this section has now
gone stale at four consecutive stage boundaries, Stage 8's own two
included.

**Stage 5 is the MVP** (`docs/implementation/mvp.md`): PyFlow solves
incompressible Navier-Stokes end to end, and the Lid-Driven Cavity
golden demo renders a *solved* velocity field live. **Stage 6 is the
proof that the engine underneath it is field-centric**: four named
physical fields, added by configuration.

Stages 0 through 8 are complete, each closed against its own written
completion criteria (`docs/planning/roadmap.md`):

- Stage 0 — planning system, capability map, repository structure,
  development tooling, CI. Deliberately no CFD functionality.
- Stage 1 — `CoordinateSystem` and `Mesh` interfaces with their first
  concrete implementations, and the Empty Mesh golden demo. Geometry,
  still no physics.
- Stage 2 — the `Field` abstraction and how a physical quantity is
  stored against a mesh (`ScalarField`, `VectorField`), rendered as a
  colour map and arrows, in the Field Display golden demo. Values, but
  nothing yet acting on them.
- Stage 3 — the six `adr/ADR-003-modular-numerical-strategies.md`
  numerical operator interfaces (advection, diffusion, time
  integration, pressure-velocity coupling, linear solver, boundary
  condition), the configuration section and assembly registry that
  resolve a configured name to a real instance, and the Numerics
  Assembly golden demo. No real numerical scheme ships yet -- every
  interface resolves only to a trivial, non-physical reference
  implementation, an explicit exception recorded against that stage's
  own completion criteria.
- Stage 4 — each of Stage 3's six interfaces gets its first real,
  physically meaningful implementation (`FirstOrderUpwindAdvection`,
  `CentralDifferenceDiffusion`, `RK4Integrator`, `ConjugateGradientSolver`,
  `PISO`, and Dirichlet/Neumann/periodic boundary conditions), plus the
  simulation-stepping mechanism that drives a live `pyflow run`
  (`engine/simulation.py`), demonstrated in the Passive Scalar Transport
  golden demo. Individually real numerics, not yet assembled into the
  coupled velocity/pressure solve -- that was Stage 5's own job.
- Stage 5 — the coupled velocity/pressure solve, and PyFlow's MVP.
  Velocity became a transported field like any other (one `ScalarField`
  per component), pressure became a field *solved* from the
  incompressibility constraint rather than transported, `PISO` became
  genuinely multi-pass, and `navier_stokes_step` assembled the three
  into one incompressible timestep -- validated against Couette flow's
  exact linear profile, Ghia, Ghia & Shin (1982)'s tabulated cavity
  profiles at Re = 100 under mesh refinement, and Taylor-Green vortex
  decay with its own negative control. Two golden demos: Lid-Driven
  Cavity and Heat Diffusion. **Thirteen completion criteria, eight of
  which its exit audit found overstated and corrected** -- see that
  stage's own status section in `docs/planning/roadmap.md`.
- Stage 6 — four named transported physical fields (temperature,
  density, humidity, passive tracers) and one Boussinesq buoyancy
  coupling that serves two of them, on the claim Stage 5 existed to make
  testable: that nothing in the engine special-cases any particular
  field. **Its twelve completion criteria were written on 2026-08-29,
  before its first task**, per the standing rule every stage since Stage
  2 has followed. The measurable one was the point: adding a field is a
  configuration act, not a code change, and the last two tasks must add
  zero lines under `src/pyflow/`. **They added zero, and so did the
  task before them** -- three consecutive tasks whose whole content is a
  configuration file and a feature file. That is only measurable because
  the stage gained a fifth task, TASK-042 (Field Declaration
  Configuration), built first: PyFlow could not declare a second
  transported field at all, so there was nothing to add a field *with*.
  **Its exit audit found three of the twelve verdicts overstated, and a
  defect in shipped behaviour sitting just outside a fourth criterion
  that was met as written** -- a declared buoyancy coupling was silently
  ignored unless `numerics.source_term` was also set, now rejected at
  load -- and
  reports, as that stage's own Criterion 8 required, that its five tasks
  added 93 step definitions, 28% of the repository's whole step
  vocabulary, which is evidence against its own claim rather than for
  it.
**Stage 8 (Recording & Playback) is complete -- reopened and reclosed
the same day, 2026-09-09.** `pyflow record`/`pyflow resume`/`pyflow
play` (TASK-045/046/047, all 2026-09-07): record a run headlessly,
resume it from any checkpoint, or watch it back in a real window with
live pause, speed, and seek control -- no rendering window ever needed
for the first two, and no simulation code re-run for the third. Its own
Golden Demo is Lid-Driven Cavity (moved there from an earlier Heat
Diffusion choice once playback -- which renders a solved velocity field
-- turned out incompatible with a demo that has none; see
`docs/planning/roadmap.md`'s own Stage 8 Status section for the full
account). **Reopened and reclosed 2026-09-09** for four more criteria
an audit found the Goal itself already promised: opt-in checkpoint
retention (TASK-049, `--max-checkpoints-retained` on `record`/
`resume`), partial-overlap cache reuse (TASK-050, `pyflow play --cache
DIR` now reuses a full-subset request from a wider cached window with
no re-simulation), live scrub (TASK-048, Left/Right/Home/End and a
draggable scrub bar, verified against a real window to never pan the
camera underneath a drag), and combined solved-velocity + declared-field
playback (TASK-051, grounded in Smoke Transport -- `pyflow play` no
longer rejects a config just because it declares fields alongside a
solved velocity).
Try the whole pipeline as it stands today:

```bash
uv run python -m pyflow record --config examples/golden-demos/lid_driven_cavity.yaml --max-frames 500 --checkpoint-interval 100
# recorded 6 checkpoint(s) to checkpoints, frames [0, 100, 200, 300, 400, 500]
# wrote 6 checkpoint(s) to checkpoints
```

`checkpoints/checkpoint_00000500.pt` is a plain `torch.save`d file --
inspect one directly without any PyFlow-specific tooling:

```bash
uv run python -c "
import torch
c = torch.load('checkpoints/checkpoint_00000500.pt', weights_only=True)
print(c['frame_count'], list(c['fields']))
"
# 500 ['velocity.0', 'velocity.1']
```

Continue that same recording to frame 1000, with nothing but the
checkpoint just written -- no config file, no `--config` flag:

```bash
uv run python -m pyflow resume --checkpoint checkpoints/checkpoint_00000500.pt --max-frames 1000
```

`resume` reproduces exactly the trajectory an uninterrupted `record`
would have (`tests/unit/test_recording_determinism.py`'s own
bit-identical, mutation-tested claim) -- the prescribed state it doesn't
checkpoint (mesh geometry, any constant prescribed velocity) is
deterministically re-derived from the checkpoint's own embedded config
rather than approximated.

Now watch it -- a real window, auto-discovering the right checkpoint for
the range asked for:

```bash
uv run python -m pyflow play --checkpoints-dir checkpoints --to-frame 500
```

Space pauses/resumes; `+`/`-` change playback speed live; Left/Right
step one frame and Home/End jump to the loaded window's own edges;
drag the on-screen scrub bar to seek to any frame in between directly
(TASK-048) -- the drag never pans the camera underneath it, verified
against a real window, not just asserted. Add
`--cache cache` to materialize the window once and reuse it on a later
run without re-simulating -- a later request fully inside an
already-cached range reuses it too, sliced directly, even if its own
exact range was never cached before (TASK-050); add `--backend offscreen
--max-frames N` for
a headless/CI-safe run with no window at all (what `tests/integration/
test_playback_cli.py`'s own subprocess tests use). `pyflow play`
requires a solved velocity field (`simulation.velocity_solved: true`)
-- declared `fields` alongside it are rendered too, each its own
colour-mapped panel (TASK-051; try `--config
examples/golden-demos/smoke_transport.yaml` above instead of
Lid-Driven Cavity to see both a solved flow and a declared field
together). A config with no solved velocity at all (Heat Diffusion's
own shape) still has nothing for this to render, and is rejected the
same way it always was.

Stage 9 (Better Numerics) follows Stage 8 (Recording & Playback, added
2026-09-07) -- better advection and diffusion
schemes, and with them the quantitative Rayleigh-Bénard comparison Stage
6 deliberately deferred rather than met on a first-order-upwind solver.
**Its eight completion criteria were written on 2026-09-04, before the
stage was broken into tasks at all** -- earlier than
`docs/practices.md`'s rule asks and earlier than any stage before it --
and the Rayleigh-Bénard comparison is now Criterion 7 rather than a
deferral pointing here. (`docs/planning/status.md` is the live view of
where things stand.)

Try the most recent demonstration -- a warm patch rising under a real
Boussinesq body force, one Navier-Stokes timestep per frame:

```bash
uv run python -m pyflow run --config examples/golden-demos/thermal_buoyancy.yaml
# or, the shortcut (TASK-043): uv run python -m pyflow run --demos thermal_buoyancy
# `uv run python -m pyflow run --demos` lists every bundled demo and its number.
```

---

## Roadmap

The project progresses through incremental stages
(`docs/planning/roadmap.md`), against a longer-range view of capability
levels (`docs/planning/implementation-plan.md`).

Each stage after Stage 0 must include:

- working software
- visible demonstrations
- updated documentation
- completed Definition of Done

---

## License

[BSD 3-Clause](LICENSE)
