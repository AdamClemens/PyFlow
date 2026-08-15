# Task Prompt Template

Reusable structure for delegating one PyFlow task to an agent. Instantiated
copies live alongside this file as `task-<slug>.md`. Grounded in the
Artifact Record Schema and Prompt Architecture described in
`docs/planning/knowledge-architecture.md` §5 and §17-18.

Only delegate a task once it has no open project-identity decisions left —
if picking an approach requires a judgment call only the maintainer should
make, resolve that first (see `docs/planning/backlog.md`), then instantiate
this template.

---

## Context

<1-2 sentence project mission, from CLAUDE.md/README>

<Relevant CLAUDE.md files, root -> target directory, concatenated verbatim
in that order. Where a lower file extends or overrides the parent, the
lower file wins.>

## Task

Target file(s): <exact path(s), to be created or modified>
Purpose: <why this file/change exists>
Scope: <precisely what's in scope -- and explicitly what's NOT>
Depends on: <files/decisions this task assumes are already resolved>
References: <source material to draw from, if any>

## Constraints

- Do not invent facts; if something is uncertain, flag it rather than guessing.
- Do not resolve contradictions silently -- report them instead.
- Preserve existing decisions and content unless explicitly told to change them.
- After making the change, update the nearest `CLAUDE.md` with guidance on
  how/when this file should be maintained going forward. If no CLAUDE.md
  exists yet at the appropriate level, create a minimal one.

## Definition of Done

- [ ] <concrete, checkable condition>
- [ ] <concrete, checkable condition>

## Output

<exact file(s) to produce/modify, and in what format>
