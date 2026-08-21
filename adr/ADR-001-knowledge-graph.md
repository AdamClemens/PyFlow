# ADR-001: Use a Typed Property Graph as the Planning Source of Truth

**Status:** Accepted, not yet implemented (see Implementation Status)

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

The stated unblock condition has now passed. The manifest's reason was
that "populating the graph is downstream of having real handbook and ADR
content to populate it with" -- all sixteen Handbook entries were
written 2026-08-17, and five ADRs exist. So the graph is no longer
blocked; it is simply unscheduled, and there is a real tension to settle
rather than leave implicit:

- This ADR commits PyFlow to the graph as the authoritative planning
  model, with generated views downstream of it (and P-002, "everything
  that can reasonably be generated should be generated", agrees).
- The root `CLAUDE.md`'s Planning Philosophy says the planning system
  exists to accelerate PyFlow, and to avoid spending time on it unless
  that directly benefits development.

Both are current, and they point in opposite directions for this
specific piece of work. **This is a decision for the maintainer, not
something to resolve by drift**, and it is recorded as an open item in
`docs/planning/backlog.md` Part II with three named options: schedule
the graph, narrow this ADR's scope to the subset that pays for itself,
or supersede it with an ADR that accepts hand-maintained planning
documents as the source of truth. Doing nothing is the one option that
should not be chosen silently, because it leaves an Accepted ADR
describing the repository incorrectly -- which is where this section
came from.

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
