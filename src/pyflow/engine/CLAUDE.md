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

**`coordinate_system.py`** (TASK-011, done 2026-08-20) is the first
occupant of this package's actual numerical-engine scope (mesh, fields,
operators, ...), not just shared utilities. `CoordinateSystem` is the
layer beneath `Mesh` (TASK-012): index-to-physical and
physical-to-index conversion only, deliberately assuming nothing about
spacing or vertex-vs-cell-center placement -- see
`docs/planning/roadmap.md` TASK-011 for the full design rationale.
`UniformVertexCoordinateSystem` is the first concrete implementation,
matching the MVP (`docs/implementation/mvp.md`: 2D structured Cartesian,
uniform spacing). Built test-first per `docs/practices.md`'s TDD rule,
except the interface/implementation itself was drafted a beat before its
tests rather than strictly after -- worth naming rather than quietly
presenting as clean red-green, even though the tests were written and
verified against it in the same session before anything was called done.
Two test modules cover it, per TASK-011's own Acceptance Criteria split:
`tests/unit/test_coordinate_system_contract.py` (the shared,
implementation-independent contract suite -- parametrised, so a future
`CoordinateSystem` implementation joins by adding a factory there, not by
writing new tests) and `tests/unit/test_uniform_vertex_coordinate_system.py`
(this implementation's own specific claims: exact formula, uniform
spacing, its own error condition). `CoordinateOutOfBoundsError` is the
one exception class every implementation's `to_index` raises for an
off-grid coordinate -- shared, not per-implementation, so calling code
catches one type regardless of which concrete `CoordinateSystem` it
holds.

A cell-center-based implementation is deliberately not built yet --
planned for when Stage 1+ actually needs it (TASK-011's own note in
`docs/planning/roadmap.md`), following this package's `src/pyflow/
rendering/CLAUDE.md` sibling's same reasoning for not building a third
canvas backend ahead of a real consumer.

**Not the application bootstrap** -- that's `src/pyflow/bootstrap.py`,
deliberately *not* in this package. See `src/pyflow/CLAUDE.md` for why
(a real circular import, found 2026-08-16). The "orchestration/run-loop"
mentioned above is the future simulation run-loop (mesh+fields+
time-stepping, once physics exist), a different thing from startup
bootstrap.
