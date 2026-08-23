# CLAUDE

TASK-018's five operator interfaces: `advection.py`, `diffusion.py`,
`gradient.py`, `divergence.py`, `source.py` -- one `ABC` each, no
concrete implementation under `src/` (Stage 3 Completion Criterion 1,
`docs/planning/roadmap.md`). `boundary_condition.py` (TASK-019, done
2026-08-23), `time_integrator.py` (TASK-020, done 2026-08-23) and
`linear_solver.py` (TASK-022, done 2026-08-23, built before TASK-021
despite the number) join them the same way. TASK-021 still adds
`pressure_coupling.py` and `assembly.py` to close out Stage 3.

Full design rationale -- why a subpackage, why every operator takes
`Field` rather than a concrete subclass, why the return shapes split
face-valued (Advection/Diffusion) from cell-valued
(Gradient/Divergence/Source), the `_check_velocity`/`_check_boundary_face`
rejection pattern, `BoundaryCondition`'s `kind`-property design, why
`TimeIntegrator.advance` takes a `Mapping[str, Field]` with no analogous
`_check_...` helper, and why `LinearSolver.solve` takes a plain dense
`matrix`/`rhs` pair rather than a dedicated "system" type -- lives in the
parent `src/pyflow/engine/CLAUDE.md`'s `numerics/` entry, not repeated
here.
