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
