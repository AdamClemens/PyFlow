# CLAUDE

The Handbook: stable scientific and engineering knowledge, split per
`docs/planning/knowledge-architecture.md` §8-9 into two independent
collections:

- `physics/` -- physical phenomena PyFlow models (see `physics/README.md`
  and `physics/CLAUDE.md`)
- `numerical-methods/` -- numerical methods PyFlow implements, explained
  independently of the implementation (see `numerical-methods/CLAUDE.md`)

This directory did not exist before 2026-08-15; a flat `docs/handbook.md`
(project meta/planning content, unrelated to this) previously held the
name and was retired the same day -- see `docs/CHANGELOG-DESIGN.md`.

Written so far: `numerical-methods/overview.md` (KA-007) and
`numerical-methods/compatibility.md` (KA-008), both moved here from
`docs/planning/numerical-frameworks.md` on 2026-08-15. Every other entry
in both subdirectories is an empty stub at the correct KA-specified path
-- structure only. Writing that content is separate, later work (real
domain knowledge with citations, not something to do mechanically).
