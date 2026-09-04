# Releases

Checked-by: stage-boundary

Per `docs/planning/backlog.md` E7. There is no KA entry for this
document -- the knowledge-architecture spec never specified one -- so
this file's content is set by that backlog item and by
`docs/glossary.md`'s existing "Release" definition, not by a KA content
requirement.

## Current State

**PyFlow 0.3.0.** Cut 2026-09-03, when Stage 7 (Rendering Annotations)
closed and its exit audit completed. Same ordering as 0.2.0 below: the
version number moves in the audit's own branch, the annotated tag is
created on `main` at the merge commit whose CI run is green on both
platforms, so a reader finding this row before the tag exists knows
which of the two is outstanding.

**The rule earned its place a second time, and more sharply than the
first.** Stage 7 had **no completion criteria at all** when its only
task merged -- nothing anywhere said what the stage had to achieve, so
"the stage closes" had no meaning to cut a release against. The audit
wrote the eight criteria, found six not fully met, and fixed a defect in
shipped behaviour reachable from a bundled demo: `lid_driven_cavity.
yaml` sets `field_display.vector_label` and starts from rest, so its
first frame stated a length-per-magnitude conversion for arrows that had
not been drawn. A release cut when TASK-044 merged would have shipped
that, and would have claimed a stage complete against criteria that did
not exist.

**PyFlow 0.2.0.** Cut 2026-08-31, when Stage 6 closed and its exit audit
completed. **The version number moved in the audit's own branch; the
annotated tag is created on `main`, at the merge commit whose CI run is
green on both platforms** -- that ordering is what the process paragraph
below requires ("an annotated git tag ... on `main`, at the commit whose
CI run is green on both platforms"), and it is stated here so a reader
finding this row before the tag exists knows which of the two is
outstanding rather than assuming the row is wrong -- the first release cut by the rule below rather than by the
trigger that created the rule, and the first to test that
"`0.MINOR.0` is cut when a stage closes **and its exit audit is
complete**" means what it says. It does: that audit changed three of
Stage 6's twelve verdicts, and one of the three was a defect in shipped
behaviour (a declared buoyancy coupling silently ignored unless
`numerics.source_term` was also set). A release cut when TASK-038
merged would have shipped it.

**PyFlow 0.1.0, the MVP release.** Cut 2026-08-29, when Stage 5 closed
and `docs/implementation/mvp.md`'s Definition of Done was discharged
item by item (`docs/planning/roadmap.md`, Stage 5 Completion Criterion
11).

Before that, this document recorded a deliberate deferral: no release,
no process, and three concrete conditions that would trigger writing
one. The second of them -- "Reaching the MVP... the first point at
which PyFlow is a genuinely usable simulation someone outside active
development might want to run" -- fired when TASK-034 landed.

**It fired a day before this document noticed**, which is worth keeping
rather than smoothing over. The Maintenance section below said "update
this document... the moment any trigger condition above is met", and
nothing did; the Stage 5 exit audit found it, along with
`docs/implementation/mvp.md` not recording that the MVP was reached
either. A trigger written as a checkable condition still needs somebody
to check it, and neither of the two documents that owned the MVP concept
was in the blast radius anybody greped. `docs/practices.md`'s
Blast Radius rule now names both by name.

## The Process

Deliberately small. PyFlow is a single-developer project with no
external consumers, so this describes what a release *is* here, not a
publication pipeline nobody needs yet.

**Versioning: `MAJOR.MINOR.PATCH`, semantic versioning
(<https://semver.org>), with `MINOR` carrying stage completion while
`MAJOR` stays 0.**

- **`0.MINOR.0` is cut when a stage closes and its exit audit is
  complete** -- not when its last task merges. The audit is what makes
  the stage's own claims true, and four stage audits in a row have
  changed a verdict (Stages 2, 3, 4 and 5 all did), so a release cut
  before one would be a release of unverified claims.
- **`0.MINOR.PATCH` with `PATCH > 0`** is for a correction to an already
  released stage: a real defect fixed, not a documentation pass.
- **`MAJOR` stays 0 until the public API is something PyFlow is willing
  to keep stable.** Today it is not: `PyFlowConfig`'s schema took its
  first deliberate breaking change in Stage 5 (`diffusion_coefficient`
  migrating into a new `fluid:` section, TASK-041), and the six
  `adr/ADR-003` interfaces are still expected to widen as stages add
  physics. `1.0.0` is a decision to stop doing that, and nothing has
  asked for it.
- **A breaking configuration change is allowed within `0.x` but is never
  silent** -- TASK-041's own precedent: the retired field's name is
  rejected at load time with a named error saying where it moved, not
  defaulted. That rule is stronger than semantic versioning requires of
  a `0.x` project, and it is the one this project actually cares about.

**What a release is, concretely.** An annotated git tag `vMAJOR.MINOR.PATCH`
on `main`, at the commit whose CI run is green on both platforms, with a
tag message naming the stage it closes and linking that stage's own exit
audit. That is the whole artifact.

**Where it is published: nowhere, yet, and that is a decision.** PyPI
is the obvious eventual home (BSD-3-Clause, scientific-Python ecosystem
alignment, `LICENSE`), and `pyproject.toml` is already shaped for it --
but publishing creates an obligation to keep working what someone
installed, which is exactly the obligation `MAJOR = 0` above says PyFlow
is not ready to take on. Publish when a real external consumer exists,
which is the first trigger below and remains unmet.

**Three places carry the version number and must move together**:
`pyproject.toml`'s `[project].version`, `src/pyflow/__init__.py`'s
`__version__` (whose own comment already says so), and `README.md`'s
"Current Version" line. `docs/glossary.md`'s "Release" entry and this
document's Current State section carry it in prose too.

## Release History

| Version | Date | Stage closed | Notes |
|---------|------|--------------|-------|
| 0.3.0 | 2026-09-03 | Stage 7 — Rendering Annotations | The render window explains itself without the config file: a title, a legend captioned with its field's name and labelled with `value_range`'s endpoints, labelled spatial axes (`docs/engineering-principles.md` P-019), cell/domain size, elapsed simulated time on a live run, real arrowheads on vector arrows with a legible minimum size, and an optional `units:` section converting lengths and times to real-world units -- all from configuration, through one new module (`src/pyflow/rendering/hud.py`) and one pair of gates (`rendering.show_title`/`show_stats`). No engine change at all. Golden demo: the existing Field Display, annotated. Includes one behaviour fix from the exit audit (a `vector_label` no longer states a length-per-magnitude conversion over a frame with no arrow drawn in it) and the stage's own eight completion criteria, written at that audit rather than before its first task -- the one stage since Stage 1 not to follow that rule, and its own first finding. |
| 0.2.0 | 2026-08-31 | Stage 6 — Additional Physical Fields | Four named transported physical fields (temperature, density, humidity, passive tracers) declared in a top-level `fields:` configuration section, and one Boussinesq body force (`src/pyflow/physics/buoyancy.py`) driving momentum from any of them -- `SourceTerm`'s first concrete implementation, and the first implementation of a numerics interface to live outside `engine/numerics/`. Three of the stage's five tasks added zero lines under `src/pyflow/`. Golden demos: Heat Transport, Smoke Transport, Thermal Buoyancy. Includes one breaking configuration change (`simulation.scalar_pattern` migrated into `fields:`, rejected at load with a named error) and one behaviour fix from the exit audit (a buoyancy coupling declared without a source term is now rejected instead of silently ignored). |
| 0.1.0 | 2026-08-29 | Stage 5 — First Fluid Solver | The MVP. Incompressible Navier-Stokes end to end: velocity transported as component fields, pressure solved from the incompressibility constraint, a genuinely multi-pass `PISO`, assembled by `navier_stokes_step`. Validated against Couette flow, Ghia, Ghia & Shin (1982) at Re = 100 under mesh refinement, and Taylor-Green vortex decay with a negative control. Golden demos: Lid-Driven Cavity, Heat Diffusion. |

Stages 0 through 4 predate this process and are deliberately not
retro-tagged: a tag is a claim that a released artifact was verified
against a published process, and no such process existed when they
closed. Their exit audits are the record instead
(`docs/planning/roadmap.md`).

## What Would Trigger Changing This Process

The same shape as before -- concrete conditions, so this section stays
checkable rather than aspirational. One of the original three has fired;
the other two have not.

- **A first external consumer** -- *not yet met*. Anyone depending on
  PyFlow who isn't actively developing it needs a published, installable
  artifact, which is what the "publish nowhere" decision above defers.
  This is also `docs/practices.md`'s Python-version-policy trigger for
  moving from "periodic review" to "deliberate stability" -- the same
  event changes both policies for the same underlying reason.
- **Reaching the MVP** -- *met 2026-08-29*, and what this rewrite
  discharges.
- **A maintainer decision to publish** -- *not yet met*, and
  independent of either condition above: the maintainer may simply
  decide a release should be published (to PyPI, or anywhere) before an
  external consumer exists.

When either open condition fires, rewrite the "Where it is published"
paragraph above with the actual publication mechanism -- not just its
trigger condition restated.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E7) as a recorded
deferral; rewritten 2026-08-29 with a real process when the MVP trigger
fired, at the maintainer's direction during the Stage 5 exit audit.

**Update this document, not just `docs/glossary.md`'s "Release" entry,
whenever a stage closes** -- the Release History table above is the one
place a reader can see what has actually been cut, and it goes stale the
same way every other restated fact does. The lesson from the one time
this failed (Current State, above) is that a trigger phrased as a
condition is only as good as whoever remembers to evaluate it, so the
obligation is now attached to something that happens on a schedule --
every stage exit -- rather than to a condition somebody has to think to
check.
