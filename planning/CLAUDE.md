# CLAUDE

The machine-readable knowledge graph: `model/` (schema) and `data/`
(content). Not documentation -- see `docs/planning/` for that (a
different directory, despite the similar name).

All eleven `.yaml` files here are currently empty by design, not
oversight -- populating the graph was deferred until real handbook/ADR
content existed to populate it with. That condition is now met (the
numerical-methods and physics handbook entries landed 2026-08-17); when
work starts, it's a deliberate decision to pick up, not a rediscovery.
See `docs/planning/backlog.md`, Part II, for the full status and
`adr/ADR-001-knowledge-graph.md` for why this is modelled as a graph
rather than a single tree.

These files are exempt from the repository's usual "no empty tracked
file" rule (`docs/planning/backlog.md` A3) -- they're data, not prose.
