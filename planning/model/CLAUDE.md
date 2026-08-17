# CLAUDE

The graph's schema, not its content -- see `../data/` for that.

Four empty files, one job each once populated:

- `schema.yaml` -- the shape of the entity/relationship types themselves.
- `entities.yaml` -- entity type definitions.
- `relationships.yaml` -- allowed relationship types between entities.
- `validation.yaml` -- rules for checking `../data/*.yaml` conforms to
  the schema.

Write `schema.yaml` first -- the other three depend on it existing.
Deferred pending a maintainer decision to start; see `../CLAUDE.md` and
`docs/planning/backlog.md` Part II.
