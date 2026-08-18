# CLAUDE

Four kinds of test, split by what they exercise:

- `unit/` -- isolated logic, no process boundary, no I/O.
- `integration/` -- crosses a real boundary: the packaged CLI entry
  point, file I/O, multiple `pyflow` subsystems working together. See
  `integration/CLAUDE.md` for the first concrete example.
- `golden/` -- regression tests for the golden demos specified in
  `docs/implementation/golden-demos.md`. See `golden/CLAUDE.md` for the
  rule that every demo needs a test running it through the real CLI as a
  subprocess.
- `performance/` -- benchmarks, not correctness tests. The one directory
  here still without a real test; its conventions get written when the
  first benchmark sets a precedent, not ahead of it
  (`docs/planning/backlog.md` E9).

This split was undocumented until 2026-08-15, when the first real test
(`integration/test_cli.py`) gave it a concrete precedent to write down
against. Each subdirectory's own `CLAUDE.md` carries its conventions,
written the same way -- against its first real test rather than
speculatively.

For how far along any of this is -- which tests exist, what they cover --
read the directories themselves or `docs/repository-manifest.md`. This
file described `unit/` and `golden/` as "empty" and "placeholders" until
2026-08-18, having been left unrevised when both got real tests on
2026-08-16; per `docs/practices.md`, completeness claims do not belong in
a file whose job is explaining the split.
