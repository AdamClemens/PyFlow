# Dependency Tree

Hand-maintained ASCII tree of engine subsystem dependencies. Whether this
stays hand-maintained or becomes derived from Engine Architecture/ICDs
once those exist is still open -- see `docs/planning/backlog.md` §3.

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
