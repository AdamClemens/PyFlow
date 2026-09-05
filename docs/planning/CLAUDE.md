# CLAUDE

Planning artefacts: `backlog.md`, `roadmap.md`, `implementation-plan.md`,
`capability-map.md`, `dreams.md`, `releases.md`, `status.md` (generated,
see below), `knowledge-architecture.md` (the knowledge architecture
spec), and the pair that says what shape a Stage has --
`stage-specification.md` and `stage-shape.yaml` (see below).

`releases.md` (written 2026-08-17 as a recorded deferral, E7; rewritten
2026-08-29 with a real process) carries PyFlow's versioning scheme, what
a release is here, and the release history. **The deferral it used to
record ended when reaching the MVP fired one of its own three trigger
conditions**, which happened a day before anything noticed -- see that
file's own Current State section, and `docs/practices.md`'s "A checkable
trigger still needs somebody to check it". Its standing obligation is
now attached to a scheduled event: **update it whenever a stage closes**,
not when somebody thinks to re-evaluate a condition.

The glossary is **not** here -- it is `docs/glossary.md`, per KA-005.

**What shape a Stage in `roadmap.md` must have is
`stage-specification.md`, declared machine-readably in
`stage-shape.yaml` and gated by `make check-stages`** (both added
2026-09-03). Read the specification before opening a stage, not after:
the sections it requires from `opened` -- **Serves**, **Use cases**,
Completion Criteria, a discharge map -- are all due before the first
task entry exists, and the checker fires then rather than at the close.
The two files are gated against each other, so adding a section to the
shape without explaining it in the specification fails the build.

**A `sketched` stage may already carry some of them, so check before
writing rather than assuming a blank.** Stage 8 (Better Numerics) was
given its eight Completion Criteria and its **Serves** line on
2026-09-04, while still sketched -- earlier than the rule asks, at the
maintainer's request. What it deliberately does *not* have is **Use
cases** and a discharge map: a discharge map cannot be written before
the tasks it maps to exist, and use cases invented for an undesigned
stage are the plausible fiction `stage-specification.md` warns about.
**Both fall due in the change that adds that stage's first
`## TASK-NNN`**, and `make check-stages` fails it if they are missing --
so the obligation is on the checker rather than on anybody's memory.
The stage's own Discharge map section says the same thing where whoever
opens it will meet it.

**Every document in this directory also declares what keeps it honest**
(`Checked-by:`, near its top; `make check-documents`). Most of them say
`stage-boundary`, which means nothing mechanical reads their meaning and
they must be re-read whole when a stage closes -- see
`docs/documentation-guidelines.md` for what the three mechanisms are and
why they are not equally strong.

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
