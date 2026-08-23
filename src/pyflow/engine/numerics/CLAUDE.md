# CLAUDE

TASK-018's five operator interfaces: `advection.py`, `diffusion.py`,
`gradient.py`, `divergence.py`, `source.py` -- one `ABC` each, no
concrete implementation under `src/` (Stage 3 Completion Criterion 1,
`docs/planning/roadmap.md`). `boundary_condition.py` (TASK-019, done
2026-08-23) joins them the same way. TASK-020/022/021 add
`time_integrator.py`, `linear_solver.py`, `pressure_coupling.py` and
`assembly.py` as Stage 3 proceeds, per its build order.

Full design rationale -- why a subpackage, why every operator takes
`Field` rather than a concrete subclass, why the return shapes split
face-valued (Advection/Diffusion) from cell-valued
(Gradient/Divergence/Source), the `_check_velocity`/`_check_boundary_face`
rejection pattern, and `BoundaryCondition`'s `kind`-property design --
lives in the parent `src/pyflow/engine/CLAUDE.md`'s `numerics/` entry,
not repeated here.
