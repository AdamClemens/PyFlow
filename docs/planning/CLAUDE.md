# CLAUDE

Planning artefacts: `backlog.md`, `roadmap.md`, `implementation-plan.md`,
`capability-map.md`, `dreams.md`, `releases.md`, `status.md` (generated,
see below), and `knowledge-architecture.md` (the knowledge architecture
spec).

`releases.md` (written 2026-08-17, E7) records that PyFlow has no
release process yet as a deliberate deferral -- concrete trigger
conditions, not an open-ended "eventually" -- not that the file is
empty; keep that distinction if this line is edited again.

The glossary is **not** here -- it is `docs/glossary.md`, per KA-005.

`roadmap.md` is authoritative for execution ("what do I work on next, and
what does done mean for it"); `implementation-plan.md` is the long-range
capability-level vision. Neither owns the MVP definition or the upgrade
paths -- those are `docs/implementation/{mvp,upgrade-paths}.md`. Don't
let them re-absorb that content.

**`dependency-tree.md` is generated. Never edit it by hand** -- run
`make dependency-tree`, and change `planning/data/components.yaml` to
change what it says. `make check-dependency-tree` (in `make ci`) fails
if the committed copy is stale.

It was hand-maintained until 2026-08-21, and the open question recorded
here -- whether it should be derived from the Engine Architecture -- was
answered then by `adr/ADR-006-knowledge-graph-scope.md`: derived, from
`docs/architecture/engine.md`'s nine conceptual layers. The question had
been open since 2026-08-17 and mattered more than it looked: the tree
and `engine.md` described genuinely different subsystem sets, both
documents said so, and neither could fix it, because fixing it by
editing one is only choosing a winner by hand. Note the content also
changed shape, not just its source: the engine is a DAG rather than a
tree (Flux alone depends on five other layers), so the generated
document shows dependency *order* plus each component's direct
dependencies. An ASCII tree can only draw a node once, which is part of
why the hand-drawn one kept drifting.

`numerical-frameworks.md` used to live here. It was handbook content
filed under a planning name, and moved to
`docs/handbook/numerical-methods/{overview,compatibility}.md` on
2026-08-15. Scientific/numerical reference material belongs in the
handbook, not here -- this directory is for planning the project, not for
explaining the domain.

**`status.md` is generated. Never edit it by hand** -- run
`make status-report`, and change `roadmap.md` (or fix whatever's
actually wrong in the repository) to change what it says.
`make check-status` (in `make ci`) fails if the committed copy is stale
*or* if `roadmap.md`'s claimed counts disagree with the live repository
-- see `tools/generators/generate_status_report.py`'s module docstring
for the full reasoning and exactly which counts are checked.

Added 2026-08-26 after the roadmap's own "N tests at P% as of DATE"
paragraph, just above Stage 1, was found stale by 136 real tests and 5
real Gherkin scenarios -- the same restated-fact failure mode TASK-009's
CLAUDE.md count and Criterion 8's verdict had already hit once each.
Rather than re-reading that paragraph by hand at every stage boundary
(which is what caught it this time, and only because someone happened to
build a tool that reads it), the counts it makes are now cross-checked
by machine every time `make ci` runs. `roadmap.md` stays the
authoritative, hand-written source (ADR-006 rule 2: no second status
field); `status.md` is only ever a rendering of it, refused whenever
that rendering would be dishonest.

The HTML dashboard `make status-report` also writes, under `build/`, is
deliberately **not** part of `status.md` or this directory -- it is
gitignored, uncommitted, regenerated on demand, and exists for the
richer view (per-task tables, a progress bar per stage) that doesn't
need to survive a diff.
