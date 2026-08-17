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

Written: `numerical-methods/overview.md` (KA-007) and
`numerical-methods/compatibility.md` (KA-008), both moved here from
`docs/planning/numerical-frameworks.md` on 2026-08-15. **All sixteen
per-topic entries** (ten `numerical-methods/`, six `physics/`) were
written 2026-08-17 (`docs/planning/backlog.md` E3/E4) -- real domain
content with citations, following the dependency order each area's KA
entries state (`fvm.md` and `incompressible-flow.md` first in their
respective directories, since later entries in each build on them).
`docs/references/{books,papers,websites}.md` were populated from those
sixteen entries' citations the same day (E6).
