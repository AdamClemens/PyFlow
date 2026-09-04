# Stage Specification

Checked-by: gated (make check-stages)

Every section this document explains is one `docs/planning/stage-shape.yaml`
declares, and `make check-stages` fails if that file names a section this
document never mentions.

What a well-defined Stage looks like in `docs/planning/roadmap.md`: which
sections it has, when each becomes due, and what makes a good one.

**The machine-readable half is `docs/planning/stage-shape.yaml`**, applied
by `tools/validators/check_stages.py` and gated by `make check-stages`
(part of `make ci`). That file is authoritative for *which* sections
exist and when; this document is authoritative for *why* each one does
and what a bad one looks like. Neither restates the other -- the split is
the same one `planning/model/validation.yaml` and
`tools/validators/check_graph.py` already use for the knowledge graph
(P-011, one authoritative source per fact).

---

## Why this exists

**Stage 7 (Rendering Annotations) reached its exit audit with no
completion criteria, no discharge map and no status line.** `make ci` was
green throughout. Nothing anywhere noticed, and the reason is worth
stating plainly: there was no declared shape for the stage to be missing
from. `docs/practices.md`'s "A stage gets completion criteria before its
first task" had been a standing rule since 2026-08-21 and was already
being broken for the second time -- Stage 1 is why the rule exists, and
Stage 7 is why this check does.

A survey run during that audit found **no two stages shared a shape**:

| Stage | Goal | Golden Demo | Criteria | Discharge map | Status |
|-------|------|-------------|----------|---------------|--------|
| 0 | `## Goal` | — (Level 0 is exempt) | after the tasks | — | ✓ |
| 1 | bare label | after the tasks | ✓ | — | ✓ |
| 2 | bare label | **between two tasks** | ✓ | — | ✓ |
| 3 | bare label | after the tasks | ✓ | ✓ | ✓ |
| 4–5 | bare label | after the tasks | ✓ | ✓ | ✓ |
| 6 | bare label | **between two tasks** | ✓ | ✓ | ✓ |
| 7 | bare label | preamble | **written at the audit** | ✓ | at the audit |
| 8–13 | bare label | preamble | — (sketched) | — | — |
| 14 | bare label | **none at all** | — (sketched) | — | — |

Three stages could not be read correctly by someone looking for their
own material. Stage 6's demo list sat between TASK-038 and TASK-043,
where **two other documents had already misread it as TASK-038's** --
that stage had noticed the problem on 2026-08-30 and fixed it by adding
a heading, which was not enough, because position is what a reader goes
by when Markdown offers no nesting.

---

## The lifecycle

A stage's required sections depend on how far along it is. Demanding a
discharge map from a stage nobody has designed produces filler, and
filler in a planning document is worse than a gap: a gap is visible.

- **sketched** — no `## TASK-NNN` entries yet. A loose list of intended
  work, deliberately left alone until reached.
- **opened** — at least one task entry exists. The stage is being
  worked, whether or not anything is finished.
- **complete** — every task is marked Done, so the stage's own claims
  are due.

The state is derived from the roadmap itself, never declared. There is
no status field anywhere else, per
`adr/ADR-006-knowledge-graph-scope.md` rule 2.

---

## The sections

### goal

**Required from: sketched.** One paragraph saying what the stage is for,
in terms of what becomes true when it is finished.

**A Goal is the thing the criteria are drafted *from*.** This is its
whole job, and it is why "Solve incompressible flow" and "Demonstrate
field-centric architecture" are good ones: each is a claim that could
turn out false. Stage 7's -- "make a running simulation
self-explanatory on screen … without a viewer having to read the config
file" -- is good for the same reason, and the eight criteria eventually
written for it came straight out of the four questions it names.

A Goal that cannot be false ("improve rendering") gives criteria nothing
to be drafted against, and what gets written instead is the union of the
tasks' own acceptance criteria -- which `docs/practices.md` explains
cannot fail if the tasks passed, and so verifies nothing.

### intended-work

**Required from: sketched. Required until: sketched.** A bullet list of
what the stage is expected to contain, before it is broken into tasks.

**It is a placeholder, and it goes away.** Once the stage is broken
down, the `## TASK-NNN` entries *are* the work list, and a "Tasks
include" sketch surviving beside them is a second, staler copy of the
same fact -- the restated-fact failure mode this project keeps finding.
The checker enforces the disappearance as well as the presence.

### golden-demo

**Required from: sketched, for Stage 1 onward.** One runnable
configuration proving the stage did what it claimed, reachable through
`pyflow run` like every other demo (`docs/implementation/golden-demos.md`).

`docs/planning/implementation-plan.md` requires every Capability Level
after Level 0 to ship at least one, and a stage is how a Level gets
built -- so a stage naming none has nothing to be judged on. **Stage 0
is exempt because that document exempts Level 0 in as many words**, not
as a grandfather clause.

**A demo is a use case somebody can run.** If the Use cases section
below names something no demo demonstrates, that is worth noticing at
drafting time rather than at the exit audit.

### serves

**Required from: opened.** Which Capability Level
(`docs/planning/implementation-plan.md`) this stage advances.

Not required while sketched, because `roadmap.md`'s own Stage/Capability
Level correspondence table already carries it and a second copy would be
a restated fact. It becomes required when the stage opens because that
is when its criteria are drafted, and the Level's **Unlocks** list is
what they are drafted against.

Naming the Level rather than only its number is the same rule
`docs/practices.md` states for stages: a bare number is silently wrong
after a renumber, and this roadmap has renumbered three times.

### use-cases

**Required from: opened.** What a user can do after this stage that they
could not before -- concretely, in the user's terms, not the engine's.

**Distinct from the Capability Level's Unlocks list, which is coarser.**
Several stages can serve one Level: Level 1 (Simulation Engine) is built
by Stages 1, 2, 3 and 4 together, and its unlocks say nothing about
which of the four made what possible. The use cases are the stage's own.

**Write them as things somebody does, not as things that exist.**
"Declare several named fields in one configuration file and transport
them together in one run" is a use case; "field declaration
configuration" is a component name. The test is whether a reader who has
never seen the code could tell you had delivered it.

**Deliberately not required while sketched.** Inventing use cases for a
stage nobody has designed produces plausible fiction, which the root
`CLAUDE.md`'s Integrity section rules out. The stage's own Goal and
intended work carry it until then.

### completion-criteria

**Required from: opened.** The rule this whole mechanism exists to make
enforceable.

**Required from `opened`, not from the first *Done* task**, because
"before its first task" is what the rule says: a task entry exists the
moment a stage is broken down, so the check fires then rather than at
the close, when it would be too late to be anything but a retrospective.

`docs/practices.md` owns what makes a criterion good, and three of its
rules matter most here:

- **Criteria are about the stage's goal, not the union of its tasks'
  acceptance criteria.** A stage audit assembled from its tasks' criteria
  cannot fail if the tasks passed.
- **The intent lives in the qualifier.** Every qualifying clause becomes
  its own bullet at drafting time, and the audit checks the qualifier
  rather than the headline.
- **A criterion whose strong reading depends on a later task must say so
  when drafted**, naming that task in the same bullet.

**And each criterion needs something that would fail if it were
violated** -- the Merge Gate's third clause. Stage 7's audit found four
criteria describing behaviour that was correct with nothing checking it,
which is a criterion that cannot fail and therefore does not mean
anything.

### discharge-map

**Required from: opened, for Stage 3 onward.** A table mapping each
criterion to the task that discharges it, assigned when the stage opens
rather than reconstructed at the exit audit.

`since_stage: 3` because the convention began there. Stages 1 and 2
closed without one, and reconstructing a mapping for a stage that closed
weeks ago would be an invention dressed as a record -- this project would
rather carry a stated exception than a plausible fiction.

### status

**Required from: complete.** The per-criterion verdict table, and what
the exit audit found.

**The rows that failed say what was claimed, what was actually true, and
what was done about it**, rather than being quietly rewritten (the root
`CLAUDE.md`'s Integrity section). Every stage audit so far has changed at
least one verdict, and Stage 7's changed six of eight -- a status section
recording only successes is evidence the audit was not adversarial, not
evidence the stage was clean.

`docs/practices.md`: when a stage audit finds nothing, suspect the
criteria before congratulating the work.

---

## Where a section goes

**In the stage's preamble, above its first task.** That is where a
reader scanning for the stage's own material looks, and it is where
Stage 7's and every sketched stage's already are.

`make check-stages` enforces something narrower than that -- it fails
only on a section sitting *between* two task entries, which is where a
section stops being findable at all. Stages 0 through 6 put some of
theirs after the last task, and moving seven closed stages' sections
would be churn against historical records for no reader's benefit. The
burial is the defect; the trailing block is only a habit worth not
continuing.

---

## What a task entry is called

**`## TASK-NNN -- <Title>`, with the title on the heading line.**
`task-heading-carries-title` in `stage-shape.yaml` enforces it.

This is the one rule here that is not about a stage's own sections, and
it is here because the sections are not the only part of the roadmap
something else has to read. A number identifies a task; it does not name
one. `planning/data/features.yaml` takes its entity names from these
headings, `make check-graph`'s `entity-name-appears-in-sources` requires
each name to *be* a heading in this file, and any view of that data can
only show what the heading says.

**33 of the 45 entries failed this until 2026-09-04, and every one of
them had a title already** -- written on the line below the heading,
separated by a blank line, so it read as the entry's opening sentence.
Nothing caught it because nothing read a task heading for anything but
its number, which is also why the checker names the orphaned line rather
than asking for a title to be invented.

Found only when the graph's stage/task data was first rendered for a
reader. `docs/practices.md`'s "Render it and look at it before calling a
rendering stage done" was written about pixels; the same sentence holds
for a document, and this is what it turned up the first time it was
applied to one.

---

## What is deliberately not required

- **A design-questions section.** Five stages have one and it has six
  different names between them. Mandating it invites filler; the stages
  that needed one wrote one.
- **An "Intent, recorded now" section.** Same reasoning.
- **A fixed section order.** The ordering that exists is readable and
  varies for reasons; a rule about it would be style enforcement rather
  than a check that means something.
- **Anything about whether a criterion is any *good*.** Not a structural
  fact. `tools/validators/CLAUDE.md` records why a check needing
  judgement must not gate: it trains people to route around it. That job
  belongs to the exit audit under `prompts/common/AUDITOR.md`'s stance,
  and this specification only ensures the audit has something to read.

---

## Maintenance

Written 2026-09-03, from the Stage 7 exit audit and at the maintainer's
request for "a rule or document that describes the shape a well defined
stage ought to have".

**Adding a section means touching three files**, the same discipline
`planning/model/validation.yaml` already imposes: declare it in
`docs/planning/stage-shape.yaml`, explain it here, and add a case to
`tests/unit/test_check_stages.py`. The first and second are gated
against each other -- `make check-stages` fails if the shape file names
a section this document never mentions.

**Before adding a rule, decide whether it is a gate or a judgement**
(`tools/validators/CLAUDE.md`). Every rule here is a structural fact
about the document. A rule that needs a reader belongs in
`docs/practices.md`'s exit-audit checklist instead.
