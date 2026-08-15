# Task: Add CLAUDE.md to prompts/code and prompts/docs

**SUPERSEDED 2026-08-15** -- this task's Context section inferred that
`prompts/code/` and `prompts/docs/` were the KA §17-18 feature-level layer,
but reading KA §17-18 directly shows the spec actually calls for
`prompts/global/` + `prompts/features/{handbook,adr,implementation-plan,
agents}.md`, with no mention of a code/docs split. Left in place for now
rather than deleted -- not because of a blanket keep-don't-delete rule (no
such repo-wide convention exists; `prompts/common/CLAUDE.md`'s rule about
completed `task-*.md` files is narrower and doesn't really cover a
superseded, never-executed one like this). Flagged instead as a candidate
for the deliberate file-structure pruning pass, once we know what's
actually needed. Do not execute as written. See `docs/planning/backlog.md`
§1 "Prompt directory layout mismatch" for the decision and current state.

Generated from TEMPLATE.md. Backlog reference: docs/planning/backlog.md §3.

---

## Context

(Root CLAUDE.md excerpt as in task-repo-hygiene-configs.md.)

From docs/planning/knowledge-architecture.md §17-18 (Prompt Architecture):
prompts are layered as global context, feature-level context (by artifact
kind), and task-specific context. `prompts/code/` and `prompts/docs/` are
presumed to be the feature-level context layer for code-generation tasks
and documentation-generation tasks respectively, sitting alongside
`prompts/common/` (global context). This is an inference from the existing
directory names and the KA spec, not an explicit statement anywhere — flag
this inference in your output rather than presenting it as settled fact.

Every other top-level directory in the repo (`adr/`, `assets/`, `docs/`,
`examples/`, `planning/`, `src/`, `tests/`, `tools/`) has an `CLAUDE.md`.
`prompts/`, `prompts/code/`, and `prompts/docs/` currently do not (only
`prompts/common/` does, as of this backlog pass). This task covers
`prompts/code/` and `prompts/docs/` only — `prompts/` itself (the parent)
is a separate, smaller item, not yet on the backlog.

## Task

Target files: `prompts/code/CLAUDE.md`, `prompts/docs/CLAUDE.md` (new —
both directories are currently empty)

Purpose: bring these two directories in line with the rest of the repo,
and record their intended purpose before they're populated, so future
contributors (human or agent) know what belongs there.

Scope:
- Each CLAUDE.md should state the directory's inferred purpose (feature-
  level prompt context for its category), note that it's currently empty
  and awaiting real content, and reference
  `docs/planning/knowledge-architecture.md` §17-18 as the source of that
  inference
- Do NOT invent example prompt content to populate these directories with
  — that's separate, later work once there's enough underlying handbook/
  ADR content to write real feature-level context from
- Do NOT create `prompts/CLAUDE.md` (parent) as part of this task — flag
  it as a related but separate gap instead

Depends on: none

References: docs/planning/knowledge-architecture.md §17-18

## Constraints

(as TEMPLATE.md)

## Definition of Done

- [ ] `prompts/code/CLAUDE.md` and `prompts/docs/CLAUDE.md` both exist and
      are non-empty
- [ ] Both explicitly mark their stated purpose as inferred, not confirmed,
      and cite where the inference comes from
- [ ] Neither invents prompt content that doesn't exist yet
- [ ] docs/planning/backlog.md §3 item for these two directories checked off

## Output

`prompts/code/CLAUDE.md`, `prompts/docs/CLAUDE.md`.
