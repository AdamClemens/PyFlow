# CLAUDE

The graph's schema, not its content -- see `../data/` for that.

Four files, one job each (all written 2026-08-21):

- `schema.yaml` -- the shape an entity and an edge take. Written first,
  because the other three describe things in terms of it. Also records
  what is deliberately *absent* (no status field, no free-text
  rationale, no priority) and why, so nobody adds one back by reflex.
- `entities.yaml` -- the entity types, one per `../data/*.yaml` file,
  each with its prose source of truth and -- where the file is empty --
  the trigger that would justify populating it.
- `relationships.yaml` -- the allowed edge types and which entity
  categories may sit at each end. This is what makes the graph *typed*:
  an edge whose endpoints are the wrong categories fails
  `make check-graph` even when both ends exist.
- `validation.yaml` -- the rules a validator applies, declared here
  rather than living only in the script (P-011).
  `tests/unit/test_check_graph.py` has one test per rule id, so adding a
  rule means touching all three.

**Keep the type sets small and justified.** Every relationship type in
`relationships.yaml` has at least one real edge in `../data/` and at
least one consumer (a generated view or a validator rule). A type with
neither is a guess about what the project will need, and this repository
has retired enough of those already (`docs/planning/backlog.md` E9/E10).
The same file records what is deliberately *not* modelled -- the
capability map's hierarchy, demo-to-component edges -- with the reason,
so an apparent gap reads as a decision rather than an oversight.
