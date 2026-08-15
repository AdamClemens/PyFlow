# CLAUDE

Planning artefacts: `backlog.md`, `roadmap.md`, `implementation-plan.md`,
`capability-map.md`, `dreams.md`, `releases.md` (empty), and
`knowledge-architecture.md` (the knowledge architecture spec).

The glossary is **not** here -- it is `docs/glossary.md`, per KA-005.

`roadmap.md` is authoritative for execution ("what do I work on next, and
what does done mean for it"); `implementation-plan.md` is the long-range
capability-level vision. Neither owns the MVP definition or the upgrade
paths -- those are `docs/implementation/{mvp,upgrade-paths}.md`. Don't
let them re-absorb that content.

`dependency-tree.md` is a hand-maintained ASCII tree of engine subsystem
dependencies (reformatted to LF + fenced code block 2026-08-15). Whether
it should instead be derived from Engine Architecture/ICDs once those
exist is still an open question -- see `backlog.md`. Don't resolve that
silently; it's an explicit decision to make, not a formatting fix.

`numerical-frameworks.md` used to live here. It was handbook content
filed under a planning name, and moved to
`docs/handbook/numerical-methods/{overview,compatibility}.md` on
2026-08-15. Scientific/numerical reference material belongs in the
handbook, not here -- this directory is for planning the project, not for
explaining the domain.
