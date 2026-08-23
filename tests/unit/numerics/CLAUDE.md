# CLAUDE

Contract test suites for TASK-018's five operator interfaces
(`src/pyflow/engine/numerics/`) -- one file per interface, each
parametrised over two test-only implementations plus a deliberately
inert third one, per Stage 3 Completion Criterion 2
(`docs/planning/roadmap.md`). Isolated logic, no process boundary --
same scope as the rest of `tests/unit/`, see `tests/unit/CLAUDE.md`.

TASK-019..022 add one contract suite each alongside these, following
the same shape.
