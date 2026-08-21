# CLAUDE

Standalone scripts that support the repository but aren't part of the
`pyflow` package itself. Two subdirectories now, both with a real
purpose:

- `generators/` -- scripts that write a file from the current state of
  the repository (e.g. `docs/index.md` from the doc tree). See its own
  `CLAUDE.md`.
- `validators/` -- repository-consistency checks that run outside
  `make lint` (e.g. broken relative Markdown links). See its own
  `CLAUDE.md`.

Every script here is run via a `Makefile` target (`make docs`,
`make dependency-tree`, `make inventory`, `make check-docs`,
`make check-docs-index`, `make check-graph`,
`make check-dependency-tree`, `make check-inventory`,
`make check-manifest`, `make check-claims`), never invoked ad hoc --
follow that pattern for anything added here.

**A target does not have to join `make ci`, and choosing correctly
matters.** `check-claims` is advisory and deliberately stays out,
because its findings need judgement rather than a pass/fail verdict.
`check-graph` (added 2026-08-21) is in, because every rule it applies is
a definite structural fact. Decide which kind a new check is *before*
wiring it up: a gate whose findings are arguable trains people to route
around it, and a warning that could have been a gate gets ignored.

**`planner/` and `scripts/` were retired 2026-08-17 (E10, maintainer's
decision).** Both had sat empty since the repository's first commit,
with no mention in the KA spec or roadmap and no organic content ever
appearing for either -- unlike `generators/` and `validators/`, which
both earned real content the same day this decision was made. Recreate
either only once something concrete needs to live there, following the
same pattern `generators/`/`validators/` themselves set: real content
first, `CLAUDE.md` and manifest entry in the same change, not a
speculative placeholder ahead of it.
