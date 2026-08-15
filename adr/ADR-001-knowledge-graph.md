# ADR-001: Use a Typed Property Graph as the Planning Source of Truth

**Status:** Accepted

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
