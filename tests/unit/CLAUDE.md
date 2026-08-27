# CLAUDE

Isolated logic, no process boundary, no I/O beyond what `tmp_path`
fixtures give a test for free -- if it needs to cross a real boundary
(subprocess, the packaged CLI, multiple subsystems together), it belongs
in `tests/integration/` instead.

`test_configuration.py` is the first example: pure in-process calls
against `pyflow.configuration`, using `tmp_path` for YAML fixture files
rather than real filesystem state outside the test. Covers defaults,
partial overrides, and every rejection path (missing file, non-mapping
YAML, unknown section, unknown field, each specific validation failure)
-- one test per failure mode rather than one large test asserting several
things, so a broken assertion says exactly what broke.

`test_rendering.py` (D3) only exercises the `offscreen` render backend,
never `glfw` -- it needs no I/O beyond `tmp_path`-style isolation and no
real OS resource, which is exactly what keeps it a *unit* test per this
directory's own scope. Follow this split for any future test that
touches rendering purely in-process, with no real window.

**A test that does need a real window belongs in `tests/integration/`,
not here** (revised 2026-08-17) -- it's crossing a real boundary (an
actual OS window system), the defining trait of that directory per
`tests/CLAUDE.md`, not "isolated logic." `tests/integration/
test_interactive_window.py` is that test: a real `glfw` window, skipped
cleanly (not failed) when no display is available. Previously this
section said interactive-backend behaviour "doesn't belong in the
automated suite" at all and was verified by hand instead (see
`src/pyflow/rendering/CLAUDE.md`) -- that blanket claim turned out to be
wrong, not just outdated: a real display is checkable at runtime and,
where present, a real window can be driven, closed, and its frames
inspected entirely automatically. "No display, no CI" was true; "no
display, ever" was an unexamined generalisation from it.

**`test_simulation.py` (TASK-040, added 2026-08-27) is the first
`pytest-bdd` module in this directory, not only in `tests/golden/`.**
`adr/ADR-007-executable-acceptance-criteria.md`'s scope is "simulation
work", not "golden demos" -- `tests/features/simulation_orchestrator.feature`
is Stage 4's first feature file and the first with no config file under
`examples/golden-demos/` and no CLI subprocess run, since it exercises
the orchestration mechanism (`src/pyflow/engine/simulation.py`) directly
rather than a runnable demo. It binds its scenarios and supplies its own
step definitions and test-only doubles locally (a `_Context` dataclass
mutated in place by each step, the same pattern `tests/golden/_demo.py`'s
`DemoRun` establishes) rather than drawing on `tests/golden/conftest.py`'s
vocabulary, which is phrased entirely in terms of running and rendering a
demo and has nothing this module needs. A future non-golden-demo feature
file follows this module's shape, not `tests/golden/`'s.

**`test_first_order_upwind_advection.py` (TASK-023, added 2026-08-27)
is the second**, binding `tests/features/first_order_upwind_advection.feature`
-- Stage 4's first real numerical scheme's own physical-correctness
claims (bounded, conservative on a closed domain, not the same as
stable). Same shape as `test_simulation.py`: its own `_Context`
dataclass, its own local test-only `BoundaryCondition` doubles, no
golden-demo config file or CLI run.
