# Engineering Practices

These practices describe **how** the project is developed.

---

# Session Workflow

Every design or implementation session follows this sequence.

1. Read the current design state: `docs/planning/roadmap.md` for what is
   next, `docs/planning/backlog.md` for what is outstanding.
2. Review open decisions (`docs/planning/backlog.md`, and the Open
   Questions entries in `docs/CHANGELOG-DESIGN.md`).
3. Perform design or implementation work.
4. Record any new decisions in `docs/CHANGELOG-DESIGN.md`, and as an ADR
   where the decision is architectural.
5. Update the affected documents, including `docs/planning/backlog.md`
   and the nearest `CLAUDE.md`.
6. Regenerate derived documentation.
7. Commit changes.

Steps 1 and 5 previously read "read the handbook" and "update the
handbook." That referred to the project-meta `docs/handbook.md`, retired
on 2026-08-15; the name now belongs to the scientific handbook under
`docs/handbook/`, which is not what a session should open with.

---

# Decision Recording

Capture decisions, not discussions.

Record:

- decision
- rationale
- alternatives considered
- consequences

Use ADRs where appropriate.

---

# Documentation Stability

Documentation should be organised according to expected rate of change.

## Rarely Changes

- Vision
- Engineering Principles

## Occasionally Changes

- Architecture
- Capability Map

## Frequently Changes

- Current Direction
- Open Questions
- Roadmap
- Release Status

---

# Planning Rules

- Generated artefacts are never edited manually.
- Everything that can be generated should be generated.
- Prefer a single authoritative source for information.
- Validate planning data before generating outputs.

---

# Development Rules

- Every stage after Stage 0 leaves PyFlow with a working simulation.
- Every feature satisfies the Definition of Done.
- Every capability should eventually have a demonstration.
- Every important artefact should be traceable.

Stage, Capability Level and Release are three distinct things; see
`docs/glossary.md` before using them interchangeably.

---

# Blast Radius

**Before making a change, work out what else it affects. Update all of it
in the same change.**

A change to code, documentation or a plan is rarely self-contained. Ask,
every time:

- What references this by name or path?
- What restates, summarises or depends on this information?
- What inventory tracks it (`docs/repository-manifest.md`,
  `docs/planning/knowledge-architecture.md`)?
- Which `CLAUDE.md` describes the directory it lives in?
- Which decisions were made *because* of how this used to be?

Then update those in the same change, not in a follow-up. A repository
that is briefly inconsistent is a repository someone will read while it
is wrong.

Searching for the thing's name is usually enough to find the radius; a
missed reference is nearly always one a `grep` would have caught.

If something in the radius genuinely cannot be updated now, **say so
explicitly** where the divergence is -- a recorded inconsistency is a
known problem, an unrecorded one is a trap. `docs/CHANGELOG-DESIGN.md` is
append-only by convention, so it is corrected by appending rather than by
rewriting.

This rule exists because the repository has already been bitten by it
four times, each caught only by a later audit:

- `docs/handbook.md` was retired and `README.md` updated, but
  `docs/practices.md` still told every session to "read the handbook".
- The MVP definition and upgrade paths moved out of
  `implementation-plan.md`, leaving `ADR-002`, `ADR-003`,
  `prompts/global/project.md` and `prompts/global/CLAUDE.md` all pointing
  at their old home.
- Artifacts were created and moved without updating the two inventories,
  until the manifest described roughly 35 files that did not exist.
- A numerical survey was written at a path no specification referenced,
  so both inventories reported it missing while it sat in the repository.

The `AGENTS.md` to `CLAUDE.md` rename is the counterexample: every
reference was enumerated and updated in one pass, and nothing broke.

## Specific instances of the rule

These follow from the above and are called out because they are the ones
most often missed:

Whenever a document is created or substantially filled in, update its
nearest `CLAUDE.md` in the same change with concrete guidance on how and
when to maintain that file. Do not wait for the directory to be
"finished" -- a future contributor arriving at that directory should
learn what matters there without reconstructing it from other documents.

Whenever an artifact is added, moved, or changes status, update
`docs/repository-manifest.md` and the corresponding entry in
`docs/planning/knowledge-architecture.md` together. They describe the
same artifacts from different angles and drift apart when only one is
touched.

The Definition of Done for documentation lives in
`docs/documentation-guidelines.md` and is not restated elsewhere.

---

# Design Rules

Future us is assumed to have forgotten everything.

Optimise for understanding over remembering.

When choosing between two equivalent solutions, prefer the one that is easier to understand and maintain.

End each design session by identifying the permanent knowledge created and recording it in the appropriate document before continuing development.
