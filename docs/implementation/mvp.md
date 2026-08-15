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
