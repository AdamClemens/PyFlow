# Architecture Decision Records

Architecture Decision Records (ADRs) capture significant technical and architectural decisions.

They exist to preserve project knowledge and explain why important choices were made.

---

# When to Create an ADR

Create an ADR when a decision:

- significantly affects architecture
- changes project direction
- introduces long-term constraints
- selects between multiple viable approaches

---

# ADR Lifecycle

- Proposed
- Accepted
- Superseded
- Deprecated
- Rejected

**Accepted says the decision was made, not that it was carried out.**
Where an accepted ADR has not been implemented, say so in its `Status:`
line ("Accepted, not yet implemented") and give it an Implementation
Status section explaining what exists, what does not, and what would
unblock it. Added 2026-08-21, after an audit found ADR-001 reading as a
description of the repository -- "the graph is considered the source of
truth" -- while the graph was eleven empty files and every planning
document was hand-maintained. The deferral had been recorded elsewhere,
which is not the same thing: the root `CLAUDE.md` sends readers here for
the project's architecture, so an ADR that needs a second document to be
read correctly is not doing its job.

---

# Recommended Structure

Each ADR should answer four questions:

1. Why was this decision needed?
2. What decision was made?
3. What alternatives were considered?
4. What are the consequences?

---

# Naming Convention

ADR-001-short-title.md

ADR numbering is sequential and permanent.

Numbers are never reused.

---

# Philosophy

Architectural decisions should be recorded once.

Future contributors should be able to understand why a decision was made without relying on project history or individual memory.

ADRs should reference the Engineering Principles they support where applicable.
