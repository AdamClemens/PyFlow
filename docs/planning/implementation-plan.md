# PyFlow Implementation Plan

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

One Level below (Level 7) currently has no corresponding Stage at all,
which also makes the "Dam Break / Free Surface" entry in the Golden Demos
table below unreachable from the roadmap. That divergence is recorded, not
resolved -- see `docs/planning/backlog.md`.

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

---

### Level 2 — First Fluid Simulation

Purpose

Validate the complete incompressible flow engine.

Unlocks

- Velocity field
- Pressure solve
- Incompressible Navier-Stokes

Golden Demo

Lid-driven cavity.

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

Free-surface flow.

**No roadmap Stage corresponds to this Level.** Either a Stage is added
or this Level is dropped -- open decision, see
`docs/planning/backlog.md`. Until then, treat this Level and the
"Dam Break" golden demo as unscheduled.

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
- Multiphase flow

Golden Demo

To be defined as capabilities are implemented.

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
| Scalar Transport | Advection |
| Heat Diffusion | Diffusion |
| Lid-Driven Cavity | Pressure-Velocity Coupling |
| Flow Around Cylinder | Geometry |
| Vortex | Adaptive Mesh |
| Dam Break | Free Surface |
| 3D Cavity | Three Dimensions |

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
- Verification completed.
