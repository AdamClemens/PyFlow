# ADR Prompt Context

Per `docs/planning/knowledge-architecture.md` KA-041. Tells an agent what
an Architecture Decision Record must capture before it drafts one.

Read alongside, not instead of: `adr/README.md`, which is authoritative
on when to write an ADR, the lifecycle, the four questions an ADR
answers, and the naming convention. This file adds generation-specific
guidance on top of that; it does not restate it.

---

## What an ADR Is For

An ADR records that a decision was made, why, and what it cost -- not a
general technical essay on the subject the decision touches. A reader
should come away knowing what was chosen and why *this* project chose it,
not a survey of the field.

## Sourcing the Rationale

**Prefer project-specific reasoning over generic domain knowledge.**
Ground the rationale in what PyFlow actually needs -- its stated
principles (`docs/engineering-principles.md`), its architecture
(`adr/` itself, `docs/architecture/`), its MVP scope
(`docs/implementation/mvp.md`) -- rather than restating textbook
consensus and presenting it as the project's own reasoning.

This matters because it has gone wrong before: `adr/ADR-002-fvm-first.md`
was drafted from standard CFD domain knowledge because no
project-specific reasoning had been recorded at the time, and stayed
unreviewed against the numerical-methods survey that later supplied
that reasoning (`docs/planning/backlog.md`, item E12). Generic
domain-knowledge rationale is acceptable only as a stated fallback when
no project-specific reasoning exists yet -- and should be flagged as
such in the ADR's own text, with a follow-up to review it once
project-specific material exists, not left silently presented as
equivalent to a reasoned project decision.

## Filling the Structure

For each of `adr/README.md`'s four questions:

- **Why was this decision needed?** Name the concrete problem or fork in
  the road -- not "best practice suggests," but what specifically forced
  a choice now.
- **What decision was made?** State it unambiguously, in one or two
  sentences a reader could act on without reading further.
- **What alternatives were considered?** List the real candidates that
  were actually weighed, with enough detail to show they were seriously
  considered, not props for a foregone conclusion. Say what each one
  would have made easy or foreclosed.
- **What are the consequences?** Include what this decision costs to
  reverse later (`docs/engineering-principles.md` P-016: prefer
  reversible decisions until understanding justifies commitment) -- a
  decision that's cheap to undo can be recorded more provisionally than
  one that isn't.

Reference the Engineering Principles the decision supports where
applicable, per `adr/README.md`'s own philosophy section.

## Definition of Done

Concise, decision-oriented, explicit about alternatives and consequences
-- per KA-041. An ADR that reads like a tutorial on the subject, or that
omits alternatives seriously considered, has not met this bar regardless
of length.
