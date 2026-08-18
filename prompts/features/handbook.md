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

## Four Failure Modes the Existing Entries Actually Hit

Added 2026-08-18, after a scientific-accuracy review of all sixteen
entries. None of these is the invented-claim failure above; each produced
a sentence that read as confident and correct. Each directory's
`CLAUDE.md` carries the detail -- this is the summary a generating agent
needs before drafting.

- **Inconsistent notation between entries.** `fvm.md`'s conservation
  equation omitted the density factor where `fluxes.md`'s face-flux
  expression included it, which left the latter dimensionally
  inconsistent. Follow
  `fvm.md`'s stated convention, or say at the top of the entry which one
  you are using. An equation that is right in isolation can still be
  wrong next to its neighbour.
- **Sign conventions asserted without being checked.** `buoyancy.md` had
  the Boussinesq buoyancy term inverted for its own stated meaning of
  $\mathbf{g}$ -- warm fluid would have sunk. Both sides were flipped
  consistently, which is why it read as coherent. State the convention,
  then sanity-check the result in words ("a warmer parcel gets an upward
  force").
- **A cross-reference to a claim the target does not make.** `advection.md`
  attributed a point about WENO to `overview.md`, which never mentions
  WENO. Open the target and confirm it says what you are citing it for; a
  wrong cross-reference reads exactly as authoritative as a right one.
- **Standard-but-loose domain phrasing.** "Air holds water vapour" is
  near-universal and physically wrong -- saturation is a property of the
  vapour-liquid equilibrium, not a capacity of air. Fine in conversation,
  not fine in the entry whose subject is *why* condensation happens.
  Where a field has a common informal shorthand, check whether the entry
  depends on the mechanism the shorthand obscures.

Related: distinguish **boundedness**, **stability** and **accuracy** by
name rather than treating them as one axis (`docs/glossary.md` defines
the first two; `docs/handbook/numerical-methods/fluxes.md` develops the
distinction). Two entries and one ICD described a scheme as
"unconditionally stable" when they meant bounded.

## Definition of Done

An entry is done when it provides actionable understanding of the
concept -- a future developer could use it to make an implementation
decision -- and does not duplicate project-specific requirements found
elsewhere. It does not need to be exhaustive; it needs to be correct,
sourced, and useful on its own.
