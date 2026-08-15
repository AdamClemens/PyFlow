# CLAUDE

This file contains instructions specific to `prompts/`.

These rules extend the repository-level `CLAUDE.md`.

---

# Purpose

Holds prompt material used to brief agents on PyFlow work: durable
project-wide context, per-artifact-kind feature context, and fully
instantiated, ready-to-run task prompts.

---

# Layout

- `common/` -- reusable material: the task-prompt `TEMPLATE.md`, and
  instantiated `task-*.md` prompts generated from it. See `common/CLAUDE.md`.
- `global/` -- durable, project-wide context for document-generation
  agents, per `docs/planning/knowledge-architecture.md` KA-039:
  `project.md`. See `global/CLAUDE.md`.
- `features/` -- per-artifact-kind prompt context (handbook, ADR,
  implementation-plan, CLAUDE.md files), per KA-040 through KA-043. See
  `features/CLAUDE.md`.

---

# Maintenance

This structure was reconciled against `knowledge-architecture.md` §17-18
on 2026-08-15 -- see `docs/CHANGELOG-DESIGN.md` for that entry. Update
this file if the layer split changes again.

`code/` and `docs/` (a code-vs-docs split with no basis in the KA spec)
and `common/BRIEF` (superseded by `global/project.md`) were retired the
same day, once `project.md` existed to actually replace BRIEF's role.
