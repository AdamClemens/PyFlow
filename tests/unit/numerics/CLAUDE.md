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
demonstrate two genuinely different behaviours without it.

`test_time_integrator_contract.py` (TASK-020, done 2026-08-23) also
skips that third class, for a different reason than boundary condition's:
this interface's own acceptance criteria already supply both halves the
inert-implementation pattern exists to prove -- the zero-derivative case
is the boundary an inert (ignores-its-input) implementation would also
pass, and the nonzero "same values, same result regardless of source"
case is the one it would fail. Its own two test-only implementations
(`_EulerIntegrator`, `_DoubleStepIntegrator`) have genuinely different
arithmetic rather than genuinely different shapes.

TASK-022 adds one more contract suite as Stage 3 proceeds, following the
same shape as the others -- see each suite for whether its own
acceptance criteria call for a third inert class or not.
