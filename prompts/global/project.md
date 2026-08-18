# PyFlow — Global Project Context

Durable, project-wide context for any agent generating documentation,
code, or planning artefacts for PyFlow. Per
`docs/planning/knowledge-architecture.md` KA-039.

This document is deliberately stable. It should not need to change when
the current numerical architecture, implementation stage, or task list
changes -- see "Current State" below for where that lives instead.

## What PyFlow Is

PyFlow is a long-term, open-source Python project building a modular,
field-centric computational fluid dynamics engine capable of simulating
multiple interacting physical fields.

The project emphasises maintainability, extensibility, scientific
correctness, visualisation, education, and long-term sustainability.

## Vision

PyFlow separates physical phenomena from numerical implementation.

The engine transports arbitrary fields rather than implementing individual
physical simulations. Capabilities are described independently of the
algorithm, data structure, or library that implements them (see
`docs/glossary.md`, "Capability").

## Institutional Memory

Knowledge should never depend on individual memory. The repository is
designed to explain itself: project knowledge is captured explicitly
through documentation, architecture decision records, and generated
planning artefacts -- not carried in any one person's or agent's head
between sessions.

## Knowledge Architecture

PyFlow's knowledge is organised into layers:

Capability Map (`docs/planning/capability-map.md`)
    What the system can do.

Handbook (`docs/handbook/`)
    Stable scientific and engineering knowledge: `physics/` and
    `numerical-methods/`, each explained independently of PyFlow's
    implementation of it.

Architecture Decision Records (`adr/`)
    Why decisions were made.

Implementation Plan (`docs/planning/implementation-plan.md`)
    The long-range, capability-level view of what to build.

Roadmap (`docs/planning/roadmap.md`)
    The concrete, current-work-order view of what to build next.

Engineering Principles (`docs/engineering-principles.md`)
    Rules that guide engineering. Authoritative -- reference this file
    rather than restating or forking its content.

Practices (`docs/practices.md`)
    Working habits and session workflow.

Documentation Guidelines (`docs/documentation-guidelines.md`)
    Rules for documentation.

Dreams (`docs/planning/dreams.md`)
    Speculative future ideas, explicitly out of current scope.

## Quality Expectations

Every stage after Stage 0 must include working software, a visible
demonstration, updated documentation, and a completed Definition of Done.
Documentation is part of the implementation, not an afterthought to it.

## Current State

This document intentionally excludes current numerical architecture,
implementation status, and stage -- that's local/task context, not global
context, and it changes far more often than anything above. For what's
actually true right now, read:

- `docs/planning/roadmap.md` -- current stage and next task
- `docs/planning/backlog.md` -- outstanding decisions and known gaps
- `docs/implementation/mvp.md` -- what the MVP is
- `docs/planning/implementation-plan.md` -- capability levels

## Maintenance

Reviewed 2026-08-18. The Handbook entry above read "Largely unwritten --
see `docs/planning/backlog.md`" until then, which was both false (all
sixteen entries were written 2026-08-17) and a breach of this document's
own opening rule that it excludes current status. The status claim was
removed rather than corrected: updating it to "written" would only have
set up the next staleness. **Descriptions here should say what a document
is *for*, never how complete it is** -- completeness belongs in
`docs/repository-manifest.md` and `docs/planning/backlog.md`, which the
"Current State" section already points at.
