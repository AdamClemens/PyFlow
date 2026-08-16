# CLAUDE

Demo, tutorial and experiment scripts -- `golden-demos/`, `tutorials/`,
`experiments/`. Named `examples/` rather than the roadmap's original
`demos/` because it holds more than demos (`docs/planning/backlog.md`,
2026-08-15 decision).

**Deliberately not an importable Python package** -- no `__init__.py`,
and `golden-demos/` has a hyphen in it, which isn't legal in a dotted
import path anyway. Scripts here are meant to be run directly (`uv run
python examples/golden-demos/empty_window.py`); anything that needs to
reuse one in a test loads it by file path instead (see
`tests/golden/CLAUDE.md`).
