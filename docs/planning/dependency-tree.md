# Dependency Tree

Hand-maintained ASCII tree of engine subsystem dependencies. Whether this
stays hand-maintained or becomes derived from Engine Architecture/ICDs is
still open -- both now exist (`docs/architecture/engine.md`,
`docs/architecture/icds.md`, written 2026-08-17), which unblocks the
question without answering it; see `docs/planning/backlog.md` Part II.
Note in the meantime: this tree's structure (Gradient/Divergence/Sources
under "Numerical Operators", no separate Flux/Variables/Boundary
Conditions node) does not match `engine.md`'s nine conceptual layers --
see `engine.md`'s "Relationship to Other Architecture Documents" section.

```text
Simulation
│
├── Mesh
├── Field Storage
├── Numerical Operators
│      │
│      ├── Advection
│      ├── Diffusion
│      ├── Gradient
│      ├── Divergence
│      └── Sources
│
├── Pressure Coupling
│
├── Linear Solver
│
├── Time Integration
│
└── Rendering
```
