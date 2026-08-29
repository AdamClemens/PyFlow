# PyFlow

> A modern, extensible fluid dynamics simulation engine focused on beautiful visualisation, scientific correctness, and maintainable engineering.

---

## Project Status

**Current Version:** 0.1.0 — the MVP release, cut 2026-08-29 when Stage 5 closed (`docs/planning/releases.md`).

PyFlow has completed **Stage 5 (First Fluid Solver)** -- its MVP -- and
has not yet begun Stage 6 (Additional Physical Fields). Stage 0 built
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
MVP -- see the Lid-Driven Cavity demo below. See
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

Stage 6 — Additional Physical Fields -- not yet started (Stage 5 closed
2026-08-29, PR #47).

**Stage 5 is the MVP** (`docs/implementation/mvp.md`): PyFlow now solves
incompressible Navier-Stokes end to end, and the Lid-Driven Cavity
golden demo renders a *solved* velocity field live.

Stages 0 through 5 are complete, each closed against its own written
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

Stage 6 will add four more transported physical fields (temperature,
density, humidity, passive tracers) on the claim Stage 5 exists to make
testable: that nothing in the engine special-cases any particular field.
**Its completion criteria are due when it opens, not now**, per the
standing rule every stage since Stage 2 has followed
(`docs/planning/status.md` is the live view of where things stand). One
criterion is already determined by the stage's own goal and should
survive into them: its
tasks must add no new machinery. "Demonstrate field-centric
architecture" is falsified, not evidenced, by four tasks that each need
engine changes to land -- so a large crop of new step definitions in
Stage 6 is itself evidence against the stage's own claim, and worth
reporting as a finding rather than absorbing quietly.

Try the most recent demonstration -- the lid-driven cavity, solved and
rendered live, one real Navier-Stokes timestep per frame:

```bash
uv run python -m pyflow run --config examples/golden-demos/lid_driven_cavity.yaml
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
