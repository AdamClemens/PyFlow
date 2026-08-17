# Handbook Prompt Context

Per `docs/planning/knowledge-architecture.md` KA-040. Tells an agent what
role a Handbook entry plays and what quality is expected, before it
drafts one of the physics or numerical-methods entries listed in
`docs/planning/backlog.md` Group E3/E4.

Read alongside, not instead of:

- `docs/documentation-guidelines.md` -- general documentation rules,
  which still apply here and are not repeated below.
- `docs/handbook/physics/README.md` -- what a physics entry must cover.
- `docs/handbook/numerical-methods/CLAUDE.md` -- the citation caution for
  numerical-methods entries, and which entries already have source
  material to draw from.

---

## What a Handbook Entry Is

Stable domain knowledge -- physical phenomena PyFlow models, or numerical
methods it implements -- explained on its own terms, independently of how
or whether PyFlow currently implements it. A reader who has never seen
PyFlow's source should be able to learn the concept from the entry alone.

This is the opposite job to an ADR or a roadmap task: those record a
decision or a unit of work; a Handbook entry records what is true about
the domain regardless of any decision PyFlow has made.

## What Good Looks Like

An entry should:

- explain the concept and establish its terminology, so later documents
  can use the term without redefining it;
- explain *why* the concept matters -- what it lets a simulation do, or
  what happens if it's ignored;
- describe how it relates to neighbouring concepts (which other entries
  to read alongside it);
- give sufficient technical depth to be useful -- governing equations,
  key assumptions, the shape of the trade-offs -- without becoming an
  exhaustive textbook chapter;
- clearly separate the physics/mathematics from any PyFlow-specific
  implementation choice (implementation belongs in
  `docs/architecture/`, not here);
- note numerical implications where relevant (a physics entry flagging
  what its equations demand of a solver; a method entry flagging what it
  assumes about the mesh or variable placement);
- link out to an authoritative source for anything not derived in full.

## What to Avoid

- Inventing or half-remembering a claim. If a fact can't be sourced with
  confidence, cite what is known and flag the gap explicitly rather than
  presenting a guess as settled -- this is domain content, where a
  confident wrong claim is expensive to leave standing.
- Restating project-specific task requirements, current implementation
  status, or roadmap state. Those belong in `docs/planning/roadmap.md` and
  change on a different schedule than domain knowledge should.
- Writing to fill the file rather than to teach the concept. An entry
  that exists but teaches nothing has not satisfied KA-040's Definition
  of Done any better than an empty one.

## Definition of Done

An entry is done when it provides actionable understanding of the
concept -- a future developer could use it to make an implementation
decision -- and does not duplicate project-specific requirements found
elsewhere. It does not need to be exhaustive; it needs to be correct,
sourced, and useful on its own.
