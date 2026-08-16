# CLAUDE

Four kinds of test, split by what they exercise:

- `unit/` -- isolated logic, no process boundary, no I/O.
- `integration/` -- crosses a real boundary: the packaged CLI entry
  point, file I/O, multiple `pyflow` subsystems working together. See
  `integration/CLAUDE.md` for the first concrete example.
- `golden/` -- regression tests for the golden demos specified in
  `docs/implementation/golden-demos.md`. Empty until a golden demo
  exists to test (see `docs/planning/backlog.md` D5).
- `performance/` -- benchmarks, not correctness tests. Empty until
  there's something worth benchmarking.

This split was undocumented until 2026-08-15, when the first real test
(`integration/test_cli.py`) gave it a concrete precedent to write down
against (backlog E9). `unit/` and `golden/` remain placeholders until
their own first real test sets the same kind of precedent -- don't
invent their conventions speculatively ahead of that.
