# CLAUDE

Demo, tutorial and experiment scripts -- `golden-demos/`, `tutorials/`,
`experiments/`. Named `examples/` rather than the roadmap's original
`demos/` because it holds more than demos (`docs/planning/backlog.md`,
2026-08-15 decision).

**`golden-demos/` holds configuration files, not Python** -- a golden
demo must run through the public `pyflow run --config <file>` CLI, per
`docs/implementation/golden-demos.md`'s public-API rule (2026-08-16), so
there is no demo-specific script to import or run directly. `tutorials/`
and `experiments/` are unaffected by that rule and may hold real Python
scripts once something is written for either.

**Not an importable Python package** -- no `__init__.py`, and
`golden-demos/` has a hyphen in it, which isn't legal in a dotted import
path anyway.
