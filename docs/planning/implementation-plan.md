# PyFlow Implementation Plan

Checked-by: stage-boundary

**Scope note (added 2026-08-15, updated same day):** This document is the
long-range, capability-level vision reference -- Capability Levels 0-10
below. It does not track individual in-progress tasks: for that, see
`docs/planning/roadmap.md`, which is authoritative for "what should I work
on right now." The MVP Definition and Upgrade Paths that were briefly
embedded here have since been extracted to their own artifacts,
`docs/implementation/mvp.md` and `docs/implementation/upgrade-paths.md`,
per `docs/planning/knowledge-architecture.md` KA-031/032. This
reconciliation, and the reasoning behind it, is recorded in
`docs/CHANGELOG-DESIGN.md`.

## Purpose

This document defines the long-range implementation vision for PyFlow.

It translates the project's capability map, engineering principles, and architectural decisions into a capability-driven view of how the simulation engine grows over time.

This document's primary goal is to describe the capability levels required
to evolve the MVP into the complete vision for PyFlow.

For the MVP definition itself, see `docs/implementation/mvp.md`. For the
upgrade paths available for each replaceable numerical component, see
`docs/implementation/upgrade-paths.md`. For "what should be built next, in
what order, with what verification criteria," see
`docs/planning/roadmap.md`.

Questions about *what* PyFlow should eventually be belong in the Capability Map.

Questions about *why* architectural decisions were made belong in the Architecture Decision Records (ADRs).

Questions about scientific background belong in the Handbook.

This document describes the capability-level shape of that work, not its execution order.

## Guiding Philosophy

The implementation roadmap follows a small number of practical rules.

### Working Software First

Except for Stage 0 (project infrastructure), every implementation stage must leave PyFlow in a working state.

Every stage must end with at least one Golden Demo that demonstrates the newly unlocked capability.

### Capability Unlocks

Stages are organised around capability unlocks rather than collections of unrelated features.

Each stage should provide a meaningful increase in what PyFlow can simulate.

### Replaceable Components

Every major numerical component should be implemented behind a stable interface wherever practical.

Future improvements should primarily involve adding new implementations rather than modifying existing ones.

Examples include:

- Advection schemes
- Time integration methods
- Pressure-velocity coupling algorithms
- Linear solvers
- Boundary conditions

### Smallest Useful Implementation

Every capability should initially be implemented using the simplest reasonable algorithm.

The purpose of the MVP is correctness, understandability and architectural validation—not maximum numerical accuracy.

Improved algorithms should be introduced as independent upgrade tasks after the capability has been demonstrated.

### Explicit Dependencies

Every task records the capabilities it depends upon.

Implementation order should be determined by these dependencies rather than by document order.

### Objective Completion

Every task has explicit verification criteria and a Definition of Done.

Tasks are complete only when all verification conditions have been satisfied.

See `docs/implementation/mvp.md` for the MVP definition.

## Capability Levels

Capability Levels are not the same unit as `roadmap.md`'s Stages, and do
not map onto them one-to-one -- several Stages can serve one Level. The
correspondence table is maintained in `roadmap.md`, which owns execution
order; do not restate it here. Definitions of Stage, Capability Level and
Release are in `docs/glossary.md`.

Level 7 had no corresponding Stage at all until 2026-08-21, which also
made the "Dam Break / Free Surface" entry in the Golden Demos table below
unreachable from the roadmap. **Resolved: `roadmap.md` Stage 11
(Additional Numerical Frameworks) was added to serve it**, renumbering
the former Stages 10-12 to 11-13 (itself renumbered again 2026-08-31 to
make room for a new Stage 7 -- see that document's own "Third
divergence" entry). See that document's "Stages and
Capability Levels" section for the mapping, the architectural caution
attached to the new Stage, and the evidence the decision was taken
against.

Each capability level unlocks a coherent new area of functionality.

Every level after Level 0 must leave PyFlow in a working state with at least one Golden Demo demonstrating the newly unlocked capability.

Later levels should primarily extend existing interfaces rather than modify them.

---

### Level 0 — Project Foundation

Purpose

Establish the engineering infrastructure required to support long-term development.

Unlocks

- Repository structure
- Documentation system
- Planning system
- Handbook
- Capability map
- ADR process
- Build system
- Automated testing
- Continuous Integration
- Logging
- Configuration framework
- Basic rendering window

Golden Demo

- Open a rendering window.
- Display an empty simulation.

---

### Level 1 — Simulation Engine

Purpose

Construct the reusable simulation engine.

Unlocks

- Structured mesh
- Field storage
- Numerical operator interfaces
- Time integration
- Pressure-velocity coupling
- Linear solver
- Boundary conditions

Golden Demo

Passive scalar transport.

**Method of Manufactured Solutions (MMS), noted 2026-08-27 as a
candidate technique, not yet used anywhere** -- found while compiling
the classical-validation-benchmark catalog below
(`docs/planning/backlog.md`, "Physical correctness validation"): the
order-of-accuracy claims this Level's own tasks carry (TASK-024
Diffusion's measured convergence rate; TASK-025 RK4's fourth-order
accuracy, isolated from spatial error) need *some* problem with a known
exact answer to measure against, and not every scheme has one as
convenient as Taylor-Green's closed-form decay (Level 2, below). MMS is
the general-purpose alternative: pick an arbitrary smooth function as
the "exact solution," substitute it into the governing equation to
derive the source term that makes it exact, then check the scheme's
measured order against the known solution on refined meshes -- no
natural physical case required. TASK-023 (First-order Upwind Advection)
did not need this, since its own boundedness/conservation claims don't
require measuring an order of accuracy against an exact solution; TASK-024
was the first task where this Level's own criteria might actually need
it, if no simpler natural case (e.g. a linear or exponential profile
solving the pure-diffusion equation exactly) covered the claim already.

**Closed 2026-08-27, TASK-024: not needed.** A simpler natural case
covered the claim, per this note's own stated condition -- the Laplacian
eigenfunction sin(pi x) sin(pi y) on a unit square, whose exact Laplacian
(-2 pi^2 times itself) is known in closed form with no source term to
derive, measured over strictly interior cells only (`docs/planning/
roadmap.md` TASK-024's own Design Decision Four -- only the interior
central-difference formula carries a documented second-order claim, not
the boundary treatment). MMS stays available, uncommitted, for a future
task that genuinely lacks a natural closed-form case.

**TASK-025 (RK4) didn't need it either, same day**: exponential decay
(`dy/dt = -k*y`, exact solution `y0 * exp(-k*t)`) is exactly the
"exponential profile" case this note's own condition names above, and
measures temporal order directly with no spatial term involved at all
(`docs/planning/roadmap.md` TASK-025's own Design decisions).

---

### Level 2 — First Fluid Simulation

Purpose

Validate the complete incompressible flow engine.

Unlocks

- Velocity field
- Pressure solve
- Incompressible Navier-Stokes

Golden Demo

Lid-driven cavity. **The quantitative target has a name and a number,
recorded here 2026-08-27 and drafted into a real acceptance criterion on
2026-08-28:** Ghia, Ghia & Shin (1982) publish tabulated centerline
velocity profiles for this exact case at several Reynolds numbers;
`adr/ADR-007-executable-acceptance-criteria.md`'s own worked example
already uses "Reynolds number 100... matches Ghia et al. within 2%" to
illustrate what an executable physics criterion looks like, and
`docs/glossary.md`'s definition of "Validation" cites the same paper.
This note previously said neither committed Stage 5 to that Reynolds
number or that tolerance, and asked whoever drafted that Stage's
criteria to reach for Ghia et al. rather than invent a fresh reference.
**They did, and the answer to the tolerance half was no** (`docs/
planning/roadmap.md`, Stage 5 Completion Criterion 5, 2026-08-28,
maintainer's call): Reynolds number 100 is adopted, the 2% is not.
The MVP's advection scheme is first-order upwind, whose numerical
diffusion at MVP mesh resolutions dominates the error, so a fixed 2%
would be a bar the MVP's own documented numerics are not built to clear.
The criterion is convergence instead -- error against Ghia's profiles
decreasing monotonically across at least three mesh resolutions, plus
the qualitative structure (primary vortex centre, both secondary corner
vortices) at the finest -- with the absolute tolerance stated and
defended in the feature file against the mesh actually used.

**Heat diffusion, added 2026-08-28** -- maintainer's call, taken while
drafting Stage 5's Completion Criteria and reconciling them against
`docs/implementation/mvp.md`'s own Definition of Done, which is a
condition Stage 5 has carried since 2026-08-22. `mvp.md` requires the
MVP to reproduce three validation cases -- passive scalar transport,
heat diffusion, lid-driven cavity -- while this document and
`planning/data/demos.yaml` both placed Heat Diffusion at Level 3, which
is Stage 6. **Decided: Level 2 owes it, as a scalar.** Heat diffusion
*is* the diffusion equation on a transported scalar; only the field's
name differs, and PyFlow can run it with no Temperature field at all.
Level 3's "Heat transport" (below) is then the named-Temperature
version with buoyancy coupling -- a genuinely different claim, not this
one repeated -- the same reuse-at-a-later-Level pattern Taylor-Green
vortex already follows between Levels 2 and 4.

**Couette flow, added 2026-08-27** (`docs/planning/backlog.md`,
"physical correctness validation") -- plane shear flow between two
parallel plates, one stationary and one moving at a constant velocity,
with no imposed pressure gradient. Its velocity profile is exactly
linear -- the simplest possible incompressible Navier-Stokes validation
case there is, simpler even than Poiseuille flow below: it needs no
pressure-gradient boundary condition at all, only two no-slip walls
(one with a nonzero prescribed velocity) and viscous diffusion doing
all the work. Missing from this catalog until now despite Poiseuille,
Taylor-Green and lid-driven cavity all being present -- found while
compiling the full classical-benchmark list this Level's own Golden
Demos draw from. A natural first rung before Poiseuille's pressure-gradient
case, not a replacement for it.

**Poiseuille flow** (added 2026-08-20, `docs/planning/backlog.md`
"physical correctness validation") -- steady laminar channel flow, whose
velocity profile has a known closed-form analytical solution. A simpler,
earlier validation case than lid-driven cavity's recirculating flow:
where lid-driven cavity proves the engine works end to end, Poiseuille
flow proves the *result is quantitatively right* against an exact
answer, not just plausible-looking.

**Taylor-Green vortex and Kelvin-Helmholtz instability** (moved here
2026-08-20 from an earlier draft that placed them at Level 4 --
maintainer's correction: these are not primarily about *comparing*
numerical schemes, they are the more fundamental claim that correct
numerics plus the right initial conditions *must* reproduce a known
emergent phenomenon, which is exactly this Level's own purpose). Both
need nothing Level 3+ unlocks -- a base incompressible Navier-Stokes
solver and the ability to configure a non-uniform initial condition
(Taylor-Green: a specific analytical velocity pattern; Kelvin-Helmholtz:
two counter- or co-flowing streams with a velocity-shear layer between
them) are enough to produce either. Observing the *correct* phenomenon
under the *correct* configuration becomes an acceptance criterion for
TASK-034 (Navier-Stokes Timestep, this Level's own MVP-defining task),
not a separate demo bolted on afterward. Level 4 reuses these same
setups rather than duplicating them -- see its own note below.

---

### Level 3 — Multiple Transported Fields

Purpose

Demonstrate that the engine can transport arbitrary physical quantities.

Unlocks

- Temperature
- Density
- Humidity
- Passive tracers

Golden Demo

Heat transport.

Smoke transport.

Multi-field plume.

Thermal buoyancy.

**Thermal buoyancy was added to this list on 2026-08-30**, when Stage 6's
Completion Criterion 9 compared this list against
`docs/planning/roadmap.md`'s Stage 6 demo list and the Golden Demos
table below. It had been named in the roadmap since that stage was
drafted, and cited from this document's own Rayleigh-Bénard paragraph as
"already named" there -- but never listed here, which is the list a
reader looking for Level 3's demos actually reads.

**"Heat transport" here is the named-Temperature version, not the first
heat demo** (clarified 2026-08-28, when Level 2 took ownership of Heat
Diffusion -- see that Level's own note). The distinction is the point of
this Level: Level 2's Heat Diffusion demo runs the diffusion equation on
an anonymous transported scalar, which needs no Temperature field at
all. This Level's claim is that a *named* field with its own physical
coupling (buoyancy, TASK-035) adds nothing to the engine -- which is
only demonstrated if the anonymous version already worked.

**Rayleigh-Bénard convection** (added 2026-08-20, same reference as
above) -- a fluid layer heated from below, once Temperature and Density
are both unlocked at this Level. Extends the "Thermal buoyancy" demo
already named under `docs/planning/roadmap.md`'s Stage 6 Golden Demos
(TASK-035's; this read "TASK-038" until 2026-08-30, when that list
gained a heading of its own) into a real
instability/pattern-formation validation case: convective rolls only
form, and only in the right direction, if buoyancy's sign is correct --
directly the class of error the 2026-08-18 scientific-accuracy review
found in `docs/handbook/physics/buoyancy.md` (see Validation,
`docs/glossary.md`). Has a known quantitative target too, not just a
qualitative one: **the critical Rayleigh number for instability
onset is approximately 1708 for the rigid-rigid (no-slip top and
bottom) case** -- the classical linear-stability result (Rayleigh 1916;
the definitive treatment is Chandrasekhar, *Hydrodynamic and
Hydromagnetic Stability*, 1961), and the boundary condition PyFlow's own
no-slip walls actually produce. (The number is boundary-condition
dependent -- roughly 657.5 for the free-free case and 1101 for
rigid-free -- so the specific value to check against must be picked to
match whichever walls this demo's own configuration actually uses, not
quoted out of context. Recorded 2026-08-27.)

**Decided 2026-08-30, when Stage 6's completion criteria were drafted
(that stage's own design question five, maintainer's call): the
quantitative threshold is not Stage 6's bar.** Stage 6 checks the
qualitative onset -- rolls form when the layer is heated from below and
do not when it is heated from above, which no sign error survives -- and
the critical-Rayleigh-number comparison is deferred to Stage 8 (Better
Numerics) at the earliest. The reasoning is the one Stage 5 already
applied to Ghia et al.'s illustrative 2%: hitting a critical threshold
on a first-order-upwind solver at MVP mesh resolutions is a criterion
meetable only by loosening its own number later, which is not a
criterion. The number is not discarded -- it is waiting for a scheme
that could clear it.

**Claimed 2026-09-04, when Stage 8's completion criteria were drafted
(maintainer's call): it is that stage's Completion Criterion 7, and no
longer "at the earliest".** `docs/planning/roadmap.md`'s Stage 8 now
carries it as a numbered criterion -- onset located by a sweep across
Rayleigh numbers and reported as a bracketing interval rather than
asserted at a single run, bounded against whichever of 1708 / 1101 /
657.5 the configuration's own walls imply, with the tolerance stated and
defended against the mesh it was measured on, and with a sensitivity
check that the same sweep on `first_order_upwind` lands measurably
further away. That last bullet is what makes it evidence about better
numerics rather than a physics check Stage 6 could have attempted.

---

### Level 4 — Numerical Improvements

Purpose

Improve simulation quality without changing architecture.

Unlocks

- Additional advection schemes
- Improved diffusion
- Additional time integrators
- Alternative pressure coupling
- Additional linear solvers

Golden Demo

Numerical comparison between algorithms.

**Taylor-Green vortex and Kelvin-Helmholtz instability, reused from
Level 2, not re-specified here** (added 2026-08-20, revised same day to
reuse rather than duplicate -- see Level 2's own note). Level 2 already
established that both must emerge correctly from the base solver; this
Level makes "numerical comparison between algorithms" a quantitative
comparison against that same, already-validated baseline, not a visual
one. Taylor-Green vortex has a known closed-form decaying analytical
solution, so different scheme combinations can be compared against the
*right answer*, and a scheme's measured order of accuracy checked
against its theoretical order -- the concrete instance of what
`docs/handbook/numerical-methods/time-integration.md` and `docs/
architecture/icds.md` already flag as unmeasured. Kelvin-Helmholtz
instability has no simple closed form once it rolls up, but schemes
differ visibly and measurably in how much numerical diffusion they add
before it can form at all -- a real, useful comparison a scalar-only
demo can't show.

---

### Level 5 — Geometry

Purpose

Move beyond rectangular domains.

Unlocks

- Internal obstacles
- Immersed boundaries
- Complex geometry

Golden Demo

Flow around a cylinder.

---

### Level 6 — Adaptive Resolution

Purpose

Increase accuracy only where needed.

Unlocks

- Adaptive mesh refinement

Golden Demo

Adaptive refinement around a vortex.

---

### Level 7 — Additional Numerical Frameworks

Purpose

Extend the simulation engine to support alternative numerical frameworks where justified.

Potential Unlocks

- SPH
- FLIP
- PIC

Golden Demo

Cross-framework comparison (changed 2026-08-21 -- see the note below).

**Scheduled 2026-08-21: `roadmap.md` Stage 11 serves this Level.** The
alternative considered was dropping the Level; the maintainer chose to
keep it. Read that Stage before designing anything here -- it carries an
architectural caution drawn from this project's own survey, which found
that a mesh-free particle method used as the *primary* solver alongside
a mesh-based one needs a separate engine rather than an extension of
this one (`docs/handbook/numerical-methods/compatibility.md`,
"Combinations needing separate engines"). The reading that does work is
the coupled one, where the particle method is an embedded secondary
phase.

**This Level's golden demo changed in the same decision.** It was
"Free-surface flow"; free-surface capability now arrives at Level 10
(Advanced Physics, "Multiphase flow"), so the demo here is a
cross-framework comparison -- the same problem solved by the FVM core
and by the alternative framework. A demo for a Level about *frameworks*
has to show the frameworks; a single free-surface scene does not, which
is what let this Level's demo drift into standing for the physics rather
than the machinery.

---

### Level 8 — Three-Dimensional Simulation

Purpose

Generalise the engine to 3D.

Unlocks

- 3D mesh
- 3D rendering
- 3D operators

Golden Demo

Three-dimensional cavity flow.

---

### Level 9 — High Performance Computing

Purpose

Improve computational performance.

Unlocks

- GPU execution
- Multi-threading
- MPI
- Distributed execution

Golden Demo

Performance benchmark.

---

### Level 10 — Advanced Physics

Purpose

Expand PyFlow beyond basic fluid dynamics.

Potential Unlocks

- Clouds
- Rain
- Combustion
- Radiation
- Reactive transport
- Multiphase flow, including **free surface** (moved here 2026-08-21
  from Level 7: free surface is a physical capability, and tying it to
  one numerical framework confused the machinery with the phenomenon)

Golden Demo

Dam Break (free-surface flow), moved here 2026-08-21. Others to be
defined as capabilities are implemented.

**Former prerequisite, filled 2026-08-21:** this Level's Golden Demo
needs a free-surface method with documented properties before it can be
scheduled (`docs/practices.md`'s physical-correctness rule), and
`docs/handbook/numerical-methods/` had none -- no VOF entry, no
level-set entry, only FVM↔SPH coupling under "Coupled methods", which is
a different capability (a separate dispersed-phase solver, not a single
continuous interface). `docs/handbook/numerical-methods/
free-surface-methods.md` now covers VOF and the level-set method,
including their conservation/sharpness trade-off and the CLSVOF hybrid.
This Level's demo can be scheduled; which of the two (or CLSVOF) Dam
Break actually implements is a decision for that Stage's own
specification, not one this document makes.

## Dependency Graph

The implementation roadmap follows the dependency graph below.

```text
Foundation
      │
      ▼
Simulation Engine
      │
      ▼
Fluid Simulation
      │
      ▼
Multiple Fields
      │
      ▼
Numerical Improvements
      │
      ▼
Geometry
      │
      ▼
Adaptive Resolution
      │
      ▼
Alternative Frameworks
      │
      ▼
Three Dimensions
      │
      ▼
High Performance
      │
      ▼
Advanced Physics
```

See `docs/implementation/upgrade-paths.md` for the upgrade paths, now
expanded there to KA-032's full twelve-category list.

## Milestones

- First rendered field
- First transported scalar
- First incompressible flow
- First benchmark
- First multiple-field simulation
- First interchangeable numerical method
- First adaptive mesh
- First three-dimensional simulation
- First GPU execution

## Golden Demos

Each Golden Demo permanently validates one or more major capabilities.

| Demo | Capability |
|------|------------|
| Empty Window | Rendering |
| Empty Mesh | Mesh (added 2026-08-20, TASK-013) |
| Field Display | Variables (added 2026-08-22, TASK-017) |
| Numerics Assembly | Numerical architecture (added 2026-08-23, TASK-021 -- proves the six-component assembly mechanism, not a physical capability; "no CFD yet") |
| Scalar Transport | Advection |
| Heat Diffusion | Diffusion (Level 2 as a transported scalar, decided 2026-08-28; reused at Multiple Transported Fields as named-Temperature heat transport) |
| Couette Flow | Incompressible Navier-Stokes (added 2026-08-27, physical correctness validation) |
| Multi-Field Plume | Multiple Transported Fields (added 2026-09-04 -- this Level's own claim, which its three earlier demos each show one field of; see `docs/implementation/golden-demos.md`) |
| Smoke Transport | Multiple Transported Fields (added 2026-08-30 -- named in Level 3's own Golden Demo list since this document was written, absent from this table until Stage 6's Criterion 9 compared the two) |
| Thermal Buoyancy | Buoyancy (added 2026-08-30, same comparison -- named only in `docs/planning/roadmap.md`'s Stage 6 list, so absent from Level 3's list and this table alike) |
| Poiseuille Flow | Incompressible Navier-Stokes (added 2026-08-20, physical correctness validation) |
| Lid-Driven Cavity | Pressure-Velocity Coupling |
| Rayleigh-Bénard Convection | Buoyancy (added 2026-08-20, physical correctness validation) |
| Taylor-Green Vortex | Incompressible Navier-Stokes (added 2026-08-20, physical correctness validation; reused, not re-specified, at Numerical Improvements) |
| Kelvin-Helmholtz Instability | Incompressible Navier-Stokes (added 2026-08-20, physical correctness validation; reused, not re-specified, at Numerical Improvements) |
| Flow Around Cylinder | Geometry |
| Vortex | Adaptive Mesh |
| Cross-Framework Comparison | Additional Numerical Frameworks (added 2026-08-21, replacing Dam Break at this Level) |
| Dam Break | Multiphase / Free Surface (moved 2026-08-21 from Additional Numerical Frameworks to Advanced Physics -- the capability is the physics, not the framework) |
| 3D Cavity | Three Dimensions |
| Performance Benchmark | High Performance (added 2026-08-21) |

**Performance Benchmark was missing from this table until 2026-08-21.**
Level 9 names it as its own Golden Demo and always had; the table simply
never listed it, and every other level with a named demo did have a row.
Found while building `planning/data/demos.yaml` -- turning the table into
an edge list made the hole obvious, where thirteen rows of prose had not.
Level 10 has no row and correctly so: its Golden Demo is "To be defined
as capabilities are implemented", a real deliberate absence.

**Flow Around Cylinder already has an unclaimed validation opportunity**
(noted 2026-08-20): past a Reynolds-number threshold, flow around a
cylinder sheds a von Kármán vortex street with a known
Reynolds-number-to-Strouhal-number correlation. `docs/planning/roadmap.md`
Stage 9 (Geometry, this demo's Stage) has no `TASK-NNN` numbers assigned
yet -- Stages 7-14 are all still at the looser "Tasks include" stage of
planning, unlike Stages 0-6. When that task exists and gets its own
acceptance criteria (`docs/practices.md`, "Acceptance criteria must be
testable"), include checking the shed frequency against
that correlation -- the demo already produces the phenomenon; nothing
currently plans to check it's the *right* phenomenon quantitatively.

## Definition of Done

Every implementation task is complete only when:

- Code implemented.
- Unit tests pass.
- Integration tests pass.
- Golden demo updated.
- Documentation updated.
- Handbook updated.
- Capability map updated.
- Changelog updated.
- Verification completed -- the implementation satisfies its own
  interface and acceptance criteria (`docs/glossary.md` "Verification").
- **Validation completed, where the task implements physics** (added
  2026-08-20) -- the implementation is checked against the physics it
  claims to model, not only against its own interface
  (`docs/glossary.md` "Validation"). Distinct from and in addition to
  verification above: code can satisfy its own contract while still
  being physically wrong. See `docs/planning/backlog.md` ("physical
  correctness validation") for what this means concretely per component.
