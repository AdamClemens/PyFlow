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
never `glfw` -- CI runners have no display, so a test that opened a real
window would be red on every push. The interactive backend is verified
manually instead (see `src/pyflow/rendering/CLAUDE.md`). Follow this
split for any future test that touches rendering: if it needs a real
window, it doesn't belong in the automated suite.
