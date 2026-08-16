# CLAUDE

Regression tests for the golden demos specified in
`docs/implementation/golden-demos.md` -- one test module per demo, run
headlessly (offscreen rendering backend) since CI has no display.

`test_empty_window.py` (D5, 2026-08-16) is the first example: loads
`examples/golden-demos/empty_window.py` directly by file path (via
`importlib.util.spec_from_file_location`), not by import statement --
`examples/` is deliberately not an importable package (see
`examples/CLAUDE.md`), and `golden-demos` has a hyphen in it anyway, so a
normal dotted import was never an option. Asserts the demo actually
renders its documented deterministic output (a specific solid background
colour, exact pixel match), not just that it ran without raising --
"verifies meaningful behaviour" is the Definition of Done's own phrase
for this, in `docs/implementation/golden-demos.md`.
