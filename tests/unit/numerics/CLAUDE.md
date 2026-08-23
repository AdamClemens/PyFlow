# CLAUDE

Contract test suites for TASK-018's five operator interfaces
(`src/pyflow/engine/numerics/`) -- one file per interface, each
parametrised over two test-only implementations plus a deliberately
inert third one, per Stage 3 Completion Criterion 2
(`docs/planning/roadmap.md`). Isolated logic, no process boundary --
same scope as the rest of `tests/unit/`, see `tests/unit/CLAUDE.md`.

`test_boundary_condition_contract.py` (TASK-019, done 2026-08-23) joins
them, minus the "inert implementation" teeth-check the other five use:
a real Dirichlet condition is *supposed* to return the same prescribed
value regardless of the field it's handed, so "varies with input" isn't
a property this interface has to prove -- its own two test-only
implementations (one value-shaped, one gradient-shaped) already
demonstrate two genuinely different behaviours without it. TASK-020/022
add one contract suite each as Stage 3 proceeds, following the same
shape as the original five.
