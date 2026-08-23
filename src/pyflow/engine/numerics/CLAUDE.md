# CLAUDE

TASK-018's five operator interfaces: `advection.py`, `diffusion.py`,
`gradient.py`, `divergence.py`, `source.py` -- one `ABC` each, no
concrete implementation under `src/` (Stage 3 Completion Criterion 1,
`docs/planning/roadmap.md`). TASK-019..022 add `boundary_condition.py`,
`time_integrator.py`, `linear_solver.py`, `pressure_coupling.py` and
`assembly.py` alongside these, per the Stage 3 build order.

Full design rationale -- why a subpackage, why every operator takes
`Field` rather than a concrete subclass, why the return shapes split
face-valued (Advection/Diffusion) from cell-valued
(Gradient/Divergence/Source), and the `_check_velocity` rejection
pattern -- lives in the parent `src/pyflow/engine/CLAUDE.md`'s
`numerics/` entry, not repeated here.
