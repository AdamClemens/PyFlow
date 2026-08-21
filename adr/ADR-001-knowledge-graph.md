# ADR-001: Use a Typed Property Graph as the Planning Source of Truth

**Status:** Accepted; scope narrowed by `adr/ADR-006-knowledge-graph-scope.md`

---

# Implementation Status

**Added 2026-08-21, repository audit.** This ADR is accepted and this
section does not weaken it -- but read as written, it describes a
repository that does not exist. The graph "is considered the source of
truth" and planning artefacts "will be generated from this model"; in
fact `planning/model/*.yaml` and `planning/data/*.yaml` are eleven
zero-byte files, and `roadmap.md`, `capability-map.md`,
`dependency-tree.md` and `releases.md` are all hand-maintained Markdown.
Nothing has ever been generated from the graph.

The deferral is deliberate and was recorded -- in
`docs/repository-manifest.md` and `docs/planning/backlog.md` Part II --
but not here, which is the actual defect being fixed. The root
`CLAUDE.md` points a reader at `adr/` as the record of the project's
architecture; anyone who followed that pointer learned something untrue,
and no amount of accuracy in the manifest repairs that. **An ADR
recording a decision that has not been carried out must say so in the
ADR.**

**Resolved the same day by `adr/ADR-006-knowledge-graph-scope.md`,**
which narrowed this ADR's scope rather than superseding it -- the same
relationship `ADR-004` and `ADR-005` already have. Read the two
together. In short: the graph remains authoritative for the
relationships between entities, prose stays authoritative for reasoning
and is never generated, and a document becomes a generated view only
when generating it is cheaper than maintaining the duplicate *and* the
result is checkable in CI.

The sentence in **Decision** below that ADR-006 reverses is "planning
artefacts such as capability trees, dependency graphs, roadmaps and
release plans will be generated from this model wherever practical."
Dependency graphs are (`docs/planning/dependency-tree.md`, via
`make dependency-tree`). Roadmaps and release plans are not:
`docs/planning/roadmap.md` is 1,457 lines of reasoning, which is the
project's most valuable asset and not a renderable artefact. Everything
else in this ADR stands unchanged.

The tension ADR-006 had to settle, recorded here because it is what let
this sit unbuilt for ten days: this ADR plus P-002 ("everything that can
reasonably be generated should be generated") point one way, and the
root `CLAUDE.md`'s Planning Philosophy -- avoid spending time on the
planning system unless it directly benefits development -- points the
other. ADR-006 rule 3 is the reconciliation: generation has to pay for
itself, case by case.

---

# Context

PyFlow is intentionally being engineered to remain maintainable by a single developer over many years. Preserving project knowledge and reducing cognitive load are therefore considered primary architectural concerns rather than documentation concerns.

Traditional planning tools such as issue trackers and roadmaps focus primarily on execution. While valuable, they do not capture the rich relationships between project capabilities, engineering decisions, demonstrations, implementation features, references and future ideas.

As the project grows, relying on documentation alone would make it increasingly difficult to answer questions such as:

- Why does this capability exist?
- Which demonstrations validate it?
- Which architectural decisions influenced it?
- Which future capabilities depend upon it?
- Which scientific concepts underpin it?

The project therefore requires a planning model capable of representing both project knowledge and the relationships between that knowledge.

---

# Decision

PyFlow will use a typed property graph as the authoritative planning model.

The graph represents project knowledge rather than implementation.

Planning artefacts such as capability trees, dependency graphs, roadmaps and release plans will be generated from this model wherever practical.

The graph itself is considered the source of truth.

Generated views are not.

---

# Consequences

## Positive

- Single authoritative planning model.
- Eliminates duplication between planning artefacts.
- Rich traceability between concepts.
- Easy generation of multiple planning views.
- Supports future automation.
- Encourages consistent planning.

---

## Negative

- Additional tooling is required.
- Contributors must understand the planning model.
- The graph schema requires careful design.

---

# Alternatives Considered

## Traditional issue tracker

Rejected.

Issue trackers manage work rather than project knowledge.

---

## Markdown documentation only

Rejected.

Relationships become implicit and difficult to maintain.

---

## Relational database

Deferred.

Possible implementation, but storage is considered an implementation detail rather than an architectural decision.

---

## Graph database

Deferred.

A graph database may become appropriate in the future but is unnecessary during early development.

---

# Notes

This ADR intentionally specifies the planning architecture rather than the storage technology.

The representation of the graph may change over time without invalidating this decision.
