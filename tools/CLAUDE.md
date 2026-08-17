# CLAUDE

Standalone scripts that support the repository but aren't part of the
`pyflow` package itself. Four subdirectories, two purposes and two still
unpurposed:

- `generators/` -- scripts that write a file from the current state of
  the repository (e.g. `docs/index.md` from the doc tree). See its own
  `CLAUDE.md`.
- `validators/` -- repository-consistency checks that run outside
  `make lint` (e.g. broken relative Markdown links). See its own
  `CLAUDE.md`.
- `planner/`, `scripts/` -- still empty. No document states what belongs
  in either; see `docs/planning/backlog.md` (E10) before adding anything
  here rather than inventing a purpose in passing.

Both real scripts are run via `Makefile` targets (`make docs`,
`make check-docs`, `make check-docs-index`), never invoked ad hoc --
follow that pattern for anything added here.
