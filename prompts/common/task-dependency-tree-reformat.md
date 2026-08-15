# Task: Reformat dependency-tree.md

Generated from TEMPLATE.md. Backlog reference: docs/planning/backlog.md §3.

---

## Context

(Root CLAUDE.md excerpt as in task-repo-hygiene-configs.md.)

docs/CLAUDE.md (verbatim):
> Maintain documentation that is accurate, maintainable and easy to
> navigate... prefer improving existing documentation over creating new
> documents... Capture decisions rather than discussions... Prefer concise
> documents with clear responsibilities.

docs/planning/CLAUDE.md (verbatim, currently a placeholder):
> This directory contains project files. Follow the repository conventions
> and avoid changing unrelated content.

## Task

Target file: `docs/planning/dependency-tree.md`

Purpose: fix formatting only. The file currently has CRLF line endings and
is a raw, unfenced ASCII tree pasted directly into the markdown file
(visible as broken/duplicated blank lines when rendered).

Scope:
- Convert to LF line endings
- Wrap the ASCII tree in a fenced code block (` ```text ` or similar) so
  it renders correctly
- Do NOT add, remove, rename, or reorder any node in the tree
  (Simulation / Mesh / Field Storage / Numerical Operators / Advection /
  Diffusion / Gradient / Divergence / Sources / Pressure Coupling /
  Linear Solver / Time Integration / Rendering) — preserve exactly as-is
- Do NOT resolve whether this file should eventually be derived from
  Engine Architecture/ICDs instead of hand-maintained — that decision is
  still open (see docs/planning/backlog.md §3) and out of scope here

Depends on: none

References: current content of docs/planning/dependency-tree.md

## Constraints

(as TEMPLATE.md)

## Definition of Done

- [ ] File uses LF line endings throughout
- [ ] Tree content is inside a fenced code block and renders correctly
- [ ] Tree structure/content is byte-for-byte the same set of nodes as before
- [ ] docs/planning/CLAUDE.md updated with a line noting this file's
      current status (hand-maintained ASCII tree; ownership question open)
- [ ] docs/planning/backlog.md §3 item for dependency-tree.md formatting
      checked off (the ownership sub-question stays open)

## Output

Reformatted `docs/planning/dependency-tree.md`; updated `docs/planning/CLAUDE.md`.
