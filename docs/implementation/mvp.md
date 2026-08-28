# PyFlow MVP Definition

Per `docs/planning/knowledge-architecture.md` KA-031. Extracted from
`docs/planning/implementation-plan.md` on 2026-08-15 into its own artifact.

## Intent

The MVP of PyFlow is defined as the smallest implementation that validates
the complete engine architecture and produces a useful simulation --
deliberately small but complete, rather than a collection of partially
implemented numerical components.

The purpose of the MVP is correctness, understandability, and
architectural validation -- not maximum numerical accuracy. Improved
algorithms are introduced as independent upgrade tasks afterward (see
`docs/implementation/upgrade-paths.md`).

## Non-Negotiable Condition

The MVP must produce a working simulation.

## MVP Components

### Simulation

- Two-dimensional.
- Structured Cartesian mesh.
- Uniform grid spacing.
- Single incompressible fluid.

### Numerical Framework

- Finite Volume Method (see `adr/ADR-002-fvm-first.md`).
- Collocated variable arrangement.
- First-order upwind advection.
- Central-difference diffusion.
- RK4 time integration.
- PISO pressure-velocity coupling.
- Conjugate Gradient pressure solver.

### Boundary Conditions

- Dirichlet.
- Neumann.
- Periodic (where practical).

### Rendering

Real-time visualisation of scalar and vector fields.

### Configuration

Simulation components are selected through configuration rather than by
modifying engine code (see `adr/ADR-003-modular-numerical-strategies.md`).

### Validation

The MVP shall successfully reproduce:

- Passive scalar transport.
- Heat diffusion.
- Lid-driven cavity flow.

**"Heat diffusion" here means the diffusion equation on a transported
scalar, not a named Temperature field** (recorded 2026-08-28,
maintainer's call). The distinction was never stated, and the project
had drifted on it: `docs/planning/implementation-plan.md` and
`planning/data/demos.yaml` both placed the Heat Diffusion demo at
Capability Level 3 -- Stage 6, one stage *after* the MVP -- while this
document required the MVP to reproduce it. Found by the reconciliation
`docs/planning/roadmap.md`'s Stage 5 Completion Criterion 11 requires
between this document and that stage's criteria, and decided in favour
of this document: heat diffusion is the diffusion equation with a
different name on the field, so PyFlow can run it with no Temperature
field at all. Stage 6's TASK-035 then adds the named field with
buoyancy coupling, which is a different claim rather than this one
repeated. Both other documents were amended in the same change.

## Definition of Done

- Simulation runs end-to-end.
- Physical fields evolve.
- Boundary conditions operate.
- Pressure/velocity coupling works.
- Numerical solution is measurable.
- Visualisation shows the result.
- Golden demo exists.
- Documentation describes the implemented functionality.
- Tests verify the core behaviour.
- Capability map is updated.
