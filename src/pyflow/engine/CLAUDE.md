# CLAUDE

Core numerical engine: mesh, field storage, operator interfaces, time
integration, pressure-velocity coupling, linear solvers, boundary
conditions -- the reusable simulation machinery, independent of any
specific physics.

As of 2026-08-15, this package's scope also covers what were briefly
separate, undocumented `interaction/`, `io/`, `simulation/`, and `util/`
packages before that day's structural reconciliation (see
`docs/planning/backlog.md` §1 "TASK-000 package structure mismatch" and
`docs/CHANGELOG-DESIGN.md`): simulation-state I/O, the orchestration/
run-loop tying mesh+fields+time-stepping together, and shared low-level
utilities all live here for now. Split any of these back out into their
own package only once they've grown large enough to justify it -- don't
pre-emptively recreate the split without a documented reason next time.

**`logging_setup.py`** (TASK-006, done 2026-08-16, D2) is the first
occupant of that "shared low-level utilities" scope: `configure_logging`
sets up the `pyflow` logger once at startup (level + formatting), and
every subsystem gets its own logger via `get_logger(__name__)` -- a
child of `pyflow` that inherits level and handler through the normal
logging hierarchy, so "every subsystem logs through the common
framework" is a naming convention, not a mechanism each module has to
opt into.

**Not the application bootstrap** -- that's `src/pyflow/bootstrap.py`,
deliberately *not* in this package. See `src/pyflow/CLAUDE.md` for why
(a real circular import, found 2026-08-16). The "orchestration/run-loop"
mentioned above is the future simulation run-loop (mesh+fields+
time-stepping, once physics exist), a different thing from startup
bootstrap.
