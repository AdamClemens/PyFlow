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

# Documentation Rules

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
