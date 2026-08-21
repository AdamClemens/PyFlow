# CLAUDE

The machine-readable knowledge graph: `model/` (schema) and `data/`
(content). Not documentation -- see `docs/planning/` for that (a
different directory, despite the similar name).

**Scope is `adr/ADR-006-knowledge-graph-scope.md`, not
`adr/ADR-001-knowledge-graph.md` alone.** ADR-001 decided there would be
a graph and said planning artefacts would be generated from it; ADR-006
(2026-08-21) narrowed that after the audit found ADR-001 describing a
repository that did not exist. The rule that matters when adding
anything here:

> The graph holds entities and the relationships between them. Prose
> holds reasoning, and is never generated.

If what you are about to add needs a paragraph to explain *why*, it
belongs in `docs/` and the graph should point at it with
`documented_in`. The roadmap in particular is 1,400 lines of reasoning
and stays hand-written.

The graph's primary product is **validation, not generation**
(ADR-006 rule 4). `make check-graph` fails on a dangling edge, an
undeclared relationship type, a path that doesn't resolve, or a
dependency cycle -- and it gates, unlike `make check-claims`, because
every rule is a definite structural fact rather than a judgement call.
`planning/model/validation.yaml` states the rules;
`tools/validators/check_graph.py` implements them;
`tests/unit/test_check_graph.py` has one test per rule id.

One document is generated from the graph so far:
`docs/planning/dependency-tree.md`, via `make dependency-tree`. Adding a
second is a real decision, not a default -- ADR-006 rule 3 asks that
generating be cheaper than maintaining the duplicate *and* checkable in
CI, which is the bar `docs/index.md` already clears and most planning
prose does not.

Three of the eleven files hold content (`data/components.yaml`,
`data/capabilities.yaml`, `data/demos.yaml`, plus all four of
`model/`). The rest are empty on purpose, each with a stated trigger in
`model/entities.yaml` -- `data/releases.yaml` most explicitly, since
`docs/planning/releases.md` is a sustained argument that PyFlow should
not have a release process yet, and an empty file matching a documented
deliberate absence is correct rather than incomplete.

These files are exempt from the repository's usual "no empty tracked
file" rule (`docs/planning/backlog.md` A3) -- they're data, not prose.
