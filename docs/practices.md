# Engineering Practices

These practices describe **how** the project is developed.

---

# Session Workflow

Every design or implementation session follows this sequence.

1. Read the current design state: `docs/planning/roadmap.md` for what is
   next, `docs/planning/backlog.md` for what is outstanding.
2. Review open decisions (`docs/planning/backlog.md`, and the Open
   Questions entries in `docs/CHANGELOG-DESIGN.md`).
3. Perform design or implementation work -- for code, run the Auditor
   review cycle (see "Audit code before calling it done" below) before
   treating it as done.
4. Record any new decisions in `docs/CHANGELOG-DESIGN.md`, and as an ADR
   where the decision is architectural.
5. Update the affected documents, including `docs/planning/backlog.md`
   and the nearest `CLAUDE.md`.
6. Regenerate derived documentation.
7. For a session that touched multiple documents or ran several rounds,
   run the end-of-session consistency review below before finishing.
8. Commit changes.

Steps 1 and 5 previously read "read the handbook" and "update the
handbook." That referred to the project-meta `docs/handbook.md`, retired
on 2026-08-15; the name now belongs to the scientific handbook under
`docs/handbook/`, which is not what a session should open with.

**Step 1 means re-reading the source, not re-using a remembered summary
of it** -- including your own, from earlier in the same conversation.
When asked to resume or close out a previously-scoped body of work (e.g.
"close out the E block"), enumerate that scope directly from the
document -- grep the actual section headers/checkboxes -- before
starting, rather than continuing from what you last said was left. A
summary written mid-session is a snapshot; it goes stale the moment
anything lands afterward that you didn't see, which is routine across a
context-compaction boundary or a gap in visible history. Found
2026-08-17: an entire subsection (E2, three files) was missed on the
first pass of "close out the E block" because the plan came from a prior
turn's "what's left" list instead of a fresh grep of `### E` headers --
caught only because a completeness sweep happened to run afterward, not
because one was planned for.

## End-of-session consistency review

The repository must stay internally consistent enough that a fresh
agent, with no memory of this session, can trust what the documents say
and pick up the next piece of work without first having to re-derive
what actually happened. A long session, or one that revises its own
earlier decisions partway through, is exactly where this breaks: a
status line written correctly in round one is easy to leave stale once
round three changes what it describes.

**Run this as a reviewer who did not write the code, not as the session
that just finished it.** The 2026-08-24 Stage 3 exit audit is the
clearest evidence that the stance matters as much as the checklist:
`make ci` was green -- 473 tests, 19 scenarios, 99% coverage -- and
three real defects passed every check anyway, each one invisible to the
persona that had just written it and legible the moment a skeptical
second pass asked "what would make this claim false?" instead of "does
this look right?": a `logger.info` call standing in for the assertion
Criterion 8 actually required, a null solver reporting `converged=True`
on a zero solution that four other documents already called an
unconverged no-op, and a registry with no duplicate-name guard despite
the exact failure mode it enables being named in `icds.md`. Where the
exit audit runs in a fresh conversation with no memory of the
implementation session, this separation is automatic. Where it does
not, adopt the stance deliberately before working the list below --
reread each artifact as an adversary trying to find the one place it is
wrong, not as the author confirming it is right. The reusable form of
this stance, for any prompt that needs it, is `prompts/common/
AUDITOR.md`.

Run this before ending such a session -- checking the actual current
state directly, the same way a fresh agent would, not from memory of
what should be true:

1. The build is actually clean: run the project's real verification
   command (`make ci`), not a subset, and confirm the working tree
   (`git status`) is clean or holds only what's intentionally staged.
2. Grep for every restatement of anything a number describes -- file
   counts, test counts, coverage percentages, "N remaining," dates. If a
   review changed one instance, the same fact is very likely stated
   again elsewhere; find all of them, not just the one that prompted the
   check.
3. Grep for references to anything renamed, moved, or deleted this
   session -- old filenames, old function signatures, old parameter
   names. A stale cross-reference reads exactly as confidently as a
   correct one, which is what makes it dangerous.
4. Read every status table touched this session end to end (e.g.
   `roadmap.md`'s Stage 0 table) -- a line written mid-session, before a
   later round of the same task landed, is the single most common source
   of drift found so far.
5. Read every `CLAUDE.md` and doc section edited this session in full,
   not just the diff -- confirm it doesn't contradict itself, the
   current code, or another document.
6. Check that any "still to add" / "not yet" framing has become "done"
   wherever the thing it describes actually landed this session.
7. Check that the next thing a fresh agent would read (the next backlog
   group, the next task) doesn't rest on an assumption this session
   invalidated.
8. **Add a new item here whenever a review finds a drift this list
   wouldn't have caught.** This list is a record of what has actually
   gone wrong before, not a theoretical ideal -- it earns its keep by
   growing, the same way `docs/practices.md`'s "Blast Radius" section
   does.
9. If this session was itself framed as "close out/finish/resume group
   X," confirm the group's full scope was actually enumerated from the
   source document at the start, not carried over from an earlier
   summary -- grep for every item matching the group's own pattern (e.g.
   `### E`) and check each one landed or was deliberately left open with
   a stated reason. See Session Workflow step 1's note, added
   2026-08-17 after exactly this check being skipped let a whole
   subsection go unaddressed on the first pass.
10. Run `make check-claims` (added 2026-08-18). It reports documentation
    asserting that a file or directory is empty, unwritten, or a stub when
    it actually has content -- the mechanical half of the
    completeness-claim rule below. Advisory, not part of `make ci`: it
    exits 0 either way, and `tools/validators/CLAUDE.md` records the one
    known false positive, so read the findings rather than counting them.
11. **Re-read `docs/repository-manifest.md`'s `src/` and `tests/`
    sections against the actual tree, whether or not this session
    touched them** (added 2026-08-21). Steps 4 and 5 are both scoped to
    what a session *edited*, and step 2 to numbers a session knew it was
    changing -- which is why this drift got past all three for five
    days. Nobody edited the manifest; sessions that added tests did not
    think of themselves as changing "the test count", and by 2026-08-21
    it described `src/` as "docstring-only, no implementation" (1,470
    lines of it by then) and the suite as "42 tests, 87% coverage" (160
    at 99%). `make check-claims` cannot help here: this file and
    `docs/planning/backlog.md` are on its exclusion list, correctly,
    because tracking completeness is their job -- which leaves the two
    documents most likely to hold a stale completeness claim as the two
    nothing checks mechanically. This step is the compensating control.
    A count that describes the present also wants a date attached, so
    the next reader can see how old it is.

    **Half of this is now mechanised** (2026-08-21): `make check-manifest`
    fails if a tracked file is unmentioned, and
    `docs/repository-inventory.md` is generated, so the *file inventory*
    can no longer drift. What is left for this step is exactly what a
    generator cannot produce -- the test count, the coverage percentage,
    and any prose describing how complete something is. Those are still
    the failure mode that started this, so do not treat the green CI as
    covering them.
12. **At a stage boundary, audit the stage's completion criteria
    per-criterion** (added 2026-08-21) -- see "A stage gets completion
    criteria before its first task" below. Not part of every session's
    review; part of the one that closes a stage. If the stage has no
    criteria to audit, that is itself the first finding.

Derived from, and first written up after, the 2026-08-16 review pass
that found four specific drifts this way (a stale `TASK-003` status
line, a stale `CLAUDE.md` placeholder count repeated in three documents,
a stale file-by-file breakdown, and a stale summary left unflagged 90
lines above its own correction) -- see `docs/planning/backlog.md` and
`docs/CHANGELOG-DESIGN.md`, 2026-08-16, for the specifics that prompted
each checklist item.

---

# Decision Recording

Capture decisions, not discussions.

Record:

- decision
- rationale
- alternatives considered
- consequences

Use ADRs where appropriate.

---

# Version Control

Git is the primary historical record (Session Workflow, above, already
assumes this). This section makes the mechanics explicit -- what wasn't
previously stated anywhere: branch naming, commit granularity and
message form, what must pass before a commit, and how branching/review
will work as the project grows past one contributor.

Added 2026-08-19 (`docs/planning/backlog.md` F1), after the maintainer
flagged that engineering best-practice questions belonged here rather
than staying implicit. `docs/engineering-principles.md` states the
philosophy (P-007 proven practice, P-008 maintainability); this section
is what that philosophy means in the concrete, Git-specific case.

## Branch naming

Single primary branch: `main`. Renamed from `master` 2026-08-19 -- free
to do at that point (no remote, no collaborators, one branch existed);
doing it later, after a remote's default branch and any collaborator
tooling already point at `master`, would cost real friction for the same
result. Feature-branch naming is below.

## Name a Stage when you cite its number

**Decided 2026-08-21, after renumbering Stages 10-12 to 11-13** to make
room for the Stage serving Capability Level 7. Twelve references to
"Stage 10" existed outside `docs/planning/roadmap.md` -- three of them
inside accepted ADRs -- and every one meant "Three Dimensions". A bare
number is silently wrong after a renumber and greppable only by the
number that has just changed, which is the worst combination: the
search you would run finds the references that are still *right*.

So when referring to a Stage from outside `roadmap.md`, write the name
alongside the number: "Stage 11 (Three Dimensions)", not "Stage 11".
The name survives renumbering and gives the next person something
stable to grep for. Same reasoning for Capability Levels.

Renumbering itself is fine, and this is the second time the project has
chosen it over living with a collision (task IDs, 2026-08-15). Both
times it was cheap because it happened early. It stays cheap only if the
references outside the owning document can be found -- hence this rule.
ADRs are edited for this and only this: a cross-reference to a renamed
or renumbered thing is a pointer, not part of the decision the ADR
records.

**Scoped to renumbering, not a blanket ban on editing ADRs** (clarified
2026-08-22, having been read as one during a consistency sweep).
`adr/README.md` separately *requires* an accepted-but-unimplemented ADR
to carry an Implementation Status section, and adding one is not
touching the decision. The line to hold is: an ADR's Context, Decision
and Consequences record what was decided and why, on the evidence
available then, and are not rewritten when the world moves -- including
supporting figures quoted in the argument. Everything alongside them
that describes *the world today* is maintained like any other
documentation.

## Feature-branch naming

**Decided 2026-08-21.** This section previously read "No standing
feature-branch naming convention yet", written 2026-08-19 alongside the
never-commit-to-`main` rule. That was reasonable the day branches became
mandatory and there were none; two days later all of Stage 1 -- three
tasks and two pull requests -- had landed on a single branch named
`docs/development-discipline`, which is what it was called when it
started and not what it became.

`<kind>/<short-hyphenated-subject>`, where `<kind>` is one of:

- `feat/` -- new capability, typically a roadmap task (`feat/task-014-field-interface`).
- `fix/` -- a defect in something that already exists (`fix/ci-apt-mirror-hang`).
- `docs/` -- documentation, planning and process only, no `src/` changes.
- `chore/` -- tooling, dependencies, repository configuration.

One branch per coherent change, matching "Commit granularity" above at
the branch level: when a branch's subject stops describing what is
landing on it, open a new one rather than widening the name's meaning.
A branch that has to be described as "and also" is two branches.

Where a change genuinely spans kinds, `feat/` or `fix/` wins over
`docs/` -- the documentation update travels with the change it
describes (Blast Radius), so its presence never makes a branch a
documentation branch. Splitting is for work that is *separable*, not for
work that merely touches two directories: the 2026-08-21 audit response
used `fix/stage-1-audit-code` and `docs/stage-1-close-out` because the
second could not be written accurately until the first had landed, not
because one held code and the other prose.

## Branch granularity: one branch per task

**Decided 2026-08-21 (maintainer's call), reversing the same day's
earlier "one branch per Stage" decision -- kept below, struck through in
substance rather than deleted, because the reversal is itself the
useful record.** Stage-level branching lasted three commits
(`feat/stage-2-representing-fields`, TASK-014/015 bundled into one of
them) before the maintainer asked for the opposite: **every task gets
its own branch**, no exceptions, and there must be a standing rule that
makes this the default rather than something re-decided per session.
The reasoning that motivated the Stage-level default -- that Stage 2's
tasks are small and sequential -- was true and is still true; it was
simply the wrong thing to optimise branch granularity around. Task-level
branches keep each PR reviewable as one unit even when tasks are small,
and "one branch per task" needs no judgement call about when a Stage
stops being small enough for one branch, which "one branch per Stage,
for now" did.

`<kind>/task-<NNN>-<short-hyphenated-subject>` for a roadmap task
(`feat/task-017-field-rendering`), matching "Feature-branch naming"
above -- that section already gave this exact example
(`feat/task-014-field-interface`) before the Stage-level detour.

**One real transitional wrinkle, worth stating plainly rather than
smoothing over:** a later task in a Stage often depends on an earlier
task's code (TASK-017 needs `ScalarField`/`VectorField`, both only on
`feat/stage-2-representing-fields`, not yet on `main`). Until that
branch is reviewed and merged, a dependent task's branch has to be
created from *it*, not from `main` -- e.g. `feat/task-017-field-rendering`
branches from `feat/stage-2-representing-fields`'s tip, and its PR
target is `main` but its diff will include that branch's commits until
the first one merges. This is a consequence of arriving at task-level
branching mid-Stage, not a new standing pattern -- once
`feat/stage-2-representing-fields` merges, every task branch after it in
Stage 2 (TASK-039 included) branches from `main` directly, like any
other task. A task with no such dependency (TASK-039, which only touches
already-`main`-side configuration code) branches from `main`, or from
the same tip for lineage consistency if a maintainer would rather review
the whole Stage's history in one place before the first merge -- either
is defensible; record which was actually used when the branch is
created, not assumed from this note.

Every task still gets its own commit within its own branch (Commit
granularity, above) -- unchanged by either version of this section.

## Commit granularity

One logical change per commit. A commit should leave the repository
internally consistent (Blast Radius already applied within it), not a
partial step toward consistency that a later commit finishes. Splitting
one coherent change across several commits, and bundling two unrelated
changes into one, are both violations of this -- it is about coherence,
not diff size.

## Commit message form

Imperative-mood summary line ("Close E9: ...", not "Closed E9" or
"Closing E9"), short enough to read as one line. A body, where the
change needs one, explains *why*, not what -- the diff already shows
what changed; Decision Recording (above) is where the *why* should
already have been captured, so the commit message can point at it
rather than repeat it.

## Commit gate

The git hook `make install` wires up (`pre-commit install`) runs `make
lint`'s checks on every commit automatically -- format, lint, mypy, and
the whitespace/YAML/large-file/line-ending checks. It deliberately does
**not** run the test suite or the docs-link/docs-index checks: those are
`make ci`'s remaining steps, and a hook that runs the full suite on
every commit adds real friction to small commits that don't touch code
or docs structure.

**`make ci` must be run and pass before any commit is made** -- not
enforced mechanically by the hook, but required by this policy. This
was already the project's actual practice (every closed backlog item
cites a `make ci` run as its verification); this section makes it an
explicit rule rather than an unstated habit that a future session could
plausibly skip without anything catching it.

## Branching and review

**Decided 2026-08-19** (the trigger below fired the same day: a GitHub
remote was created). **Never commit directly to `main`.** All work
happens on a branch, merged to `main` only through a pull request --
`main` should always reflect what a PR actually introduced, not a commit
made straight against it. This was learned the practical way, not just
declared: the session that closed Stage 0's last criterion (CI executing
on a real runner) used exactly this branch-then-PR shape for its three
real fixes, and each PR's own CI run was what caught the bug the
previous attempt had missed -- direct commits to `main` would have
skipped that check entirely, discovering each bug only after it was
already on `main`. `docs/CHANGELOG-DESIGN.md` (2026-08-19) has the full
account, including a documentation-only commit pushed straight to `main`
minutes before this rule was made explicit -- the last one, not a
carved-out exception.

This section previously read "single-branch, direct-commit workflow
while the project remains single-developer," with review left
undecided until a second contributor or a remote existed. The remote
existing was the trigger, not a second contributor -- review isn't
required (still one developer), but the branch/PR mechanism is, because
it's what makes every change pass through CI before landing on `main`,
independent of who is or isn't reviewing it.

---

# Documentation Stability

Documentation should be organised according to expected rate of change.

## Rarely Changes

- Vision
- Engineering Principles

## Occasionally Changes

- Architecture
- Capability Map

## Frequently Changes

- Current Direction
- Open Questions
- Roadmap
- Release Status

---

# Planning Rules

- Generated artefacts are never edited manually.
- Everything that can be generated should be generated.
- Prefer a single authoritative source for information.
- Validate planning data before generating outputs.

---

# Development Rules

- Every stage after Stage 0 leaves PyFlow with a working **demonstration**
  (P-004, `docs/engineering-principles.md`). This read "a working
  simulation" until 2026-08-22 -- the same overstatement `README.md`
  corrected in its own copy on 2026-08-21 and this one was missed, which
  is a Blast Radius miss of exactly the kind the rule below exists to
  catch. Stages 1, 2 and 3 each end in a demonstration and none of them
  simulates anything.
- Every feature satisfies the Definition of Done.
- Every capability should eventually have a demonstration.
- Every important artefact should be traceable.

Stage, Capability Level and Release are three distinct things; see
`docs/glossary.md` before using them interchangeably.

## Acceptance criteria must be testable

**Decided 2026-08-19, moving into Stage 1** (`docs/planning/roadmap.md`
TASK-011 onward). Every Stage 0 task (TASK-000..010) had an explicit
"Acceptance Criteria" section; Stage 1's tasks, as originally written,
didn't -- TASK-011 was, at the time, just an "Implement" list ("Physical
coordinates", "Grid spacing", ...) with nothing stating what would prove
any of it done (it has both a full Acceptance Criteria section and a
working implementation now -- kept in the past tense here since this
paragraph is explaining why the rule was adopted, not reporting current
status; `docs/planning/roadmap.md` TASK-011 is the status). An acceptance
criterion that can't be checked by running
something and getting a definite pass/fail isn't one -- it's a
description of intent. Before starting a task, give it acceptance
criteria phrased as things a test can assert: a specific input and
expected output, a boundary condition, a property that holds ("index
conversions round-trip exactly"), not "coordinates work correctly" or
"the mesh behaves as expected." Write these into the task's own
`docs/planning/roadmap.md` entry, the same way Stage 0's tasks already
have them, rather than leaving Stage 1 as the looser exception.

**Extended 2026-08-20: for any task that implements physics, "testable"
must include physical correctness, not just software correctness.**
Prompted by a direct question -- does the backlog validate conservation
laws -- that surfaced a real gap: `docs/planning/implementation-plan.md`'s
Definition of Done had listed "Verification completed" for every task
since before this rule existed, but verification (does the code satisfy
its own interface) and validation (is the code physically correct) are
different properties, and only the first was ever checked by anything.
Code can pass every unit test while being physically wrong -- the
2026-08-18 scientific-accuracy review found exactly this shape of error
already, in prose rather than code: the Boussinesq buoyancy term's sign
was inverted in `docs/handbook/physics/buoyancy.md`, reading as
perfectly coherent until checked against which way warm fluid should
move. See `docs/glossary.md` ("Verification", "Validation") for the
distinction now recorded, and `docs/planning/backlog.md` ("physical
correctness validation") for what each numerical component and
implemented phenomenon needs concretely -- conservation checks for
components with a natural conservation property, comparison against a
known analytical/reference solution or published correlation where one
exists, and a qualitative direction/sign sanity check (the "heat rises"
class of check) for every implemented phenomenon regardless of whether
either of those is available. These are acceptance criteria, not
optional extras -- a task implementing physics is not done until its
physical correctness has been checked by a real, failing-on-violation
test, the same standing every other acceptance criterion already has.

**Extended again 2026-08-22: testable applies to the criterion's
qualifying clauses too, not only its headline.** See "The intent lives
in the qualifier" below. That is the third extension of this rule and
the one with the most evidence behind it -- six defects across two
stages, every one of them in a sentence this rule had already been
applied to, because it was applied to the part that looked like the
specification and not to the part that said why it mattered.

## A stage gets completion criteria before its first task

**Decided 2026-08-21, after Stage 1 closed without any.** Stage 0 had
nine completion criteria and a per-criterion exit audit. Stage 1 had
neither: its three tasks each had good Acceptance Criteria, each was
closed against them, and then the stage simply stopped. Nothing anywhere
recorded that Stage 1 was finished -- a fresh agent could not have told
without reading three task entries and inferring it, which is precisely
the dependence on individual memory P-001 exists to prevent.

Write a stage's completion criteria into `docs/planning/roadmap.md` when
the stage opens, before its first task starts, and audit them
per-criterion when it closes.

**The criteria must be about the stage's goal, not the union of its
tasks' Acceptance Criteria.** This is the part that does the work. A
stage audit assembled from its tasks' criteria cannot fail if the tasks
passed, so it verifies nothing. Stage 1's retrospective audit found five
of its eight criteria unmet, and four of those five sat inside code
whose *task* criteria were fully met -- because task criteria describe
what a component does when used correctly, and nobody was asking what
the stage as a whole guaranteed. (The fifth was documentation accuracy,
which no task owned at all.) `Mesh` satisfied every accessor criterion it had
and still returned confident nonsense for an id no cell owned.

The corollary: when a stage audit finds nothing, suspect the criteria
before congratulating the work.

### A deferral gated on a task must be revisited when that task closes

**Added 2026-08-22, same audit.** `assets/colourmaps/` was carved out of
the "no tracked file is empty" exit condition (`docs/planning/
backlog.md` A3) on the stated terms that its content "becomes known when
TASK-017 needs it, not before." TASK-017 landed on 2026-08-21 and
deliberately did not need it: field rendering ships one built-in
two-stop gradient and defers a colormap library until something exceeds
that.

That is an *answer*. But nothing recorded it, so for a day the carve-out
still read as an open question waiting on a task that had already
closed -- and an unrecorded answer is indistinguishable from a pending
one by anyone who wasn't there.

**When a task closes, grep for its own identifier before moving on.**
Anything that deferred a decision to that task is now due, whichever way
the task went, and "it landed and turned out not to need this" must be
written down as explicitly as "it landed and here it is." This is the
Blast Radius rule pointed backwards: the usual direction asks what a
change affects, and this asks what was waiting on it.

## The repository is self-consistent before a branch merges

**Standing rule, maintainer's instruction 2026-08-22.** A branch does
not merge to `main` until the repository is *entirely* self-consistent
-- not merely until the pipeline is green.

The distinction is the whole rule, and this project has five years of
evidence for it in five days. Every significant defect it has found was
green in CI at the moment it merged: pan tracking the pointer 1.78x too
slowly, `face_neighbours(9999)` returning cells 3330 and 3333, a mesh
config silently truncating `[10.9, 3.99]` to `(10, 3)`, a contract suite
proving strictly less than it claimed, and an architecture document
describing the Stage 0 repository for two stages. **"`make ci` passes"
has never once meant "this is ready."**

### What "ready to merge" means

All four, in order. Any one failing means the branch is not ready,
whatever the other three say.

1. **Mechanically green.** `make ci` in full, on the branch, plus a real
   CI run on both platforms for anything that touches code.
2. **Internally consistent.** Every restatement of every fact the branch
   changed is updated in the same branch -- the Blast Radius rule, run
   as a grep rather than remembered. Counts, statuses, dates, file
   lists, and the documents that describe what exists.
3. **The intent is met.** Every acceptance criterion the branch claims
   to discharge is checked by something that would fail if the intent
   were violated, not merely by something that passes. For Stage 4+
   simulation work that means a scenario
   (`adr/ADR-007-executable-acceptance-criteria.md`); everywhere else it
   means a named test, and the qualifier rule below applies to reading
   it.
4. **Said honestly.** "This is ready to merge" is a claim about all
   three above. If any part is unverified, say which part and why,
   rather than letting green CI stand in for the sentence.

### The pre-merge pass

The end-of-session consistency review at the top of this document is the
list of what to check. This rule is about *when*: that review is not an
end-of-session nicety, it is the merge gate, and a branch that skipped
it is not ready even if nothing turns out to be wrong.

Three of its steps are now mechanised -- `make check-references`
(prose naming a path that does not exist), `make check-scenarios` (a
Gherkin scenario nothing runs), and `make check-manifest` -- and they
gate. `make check-claims` stays advisory and must be *read*, not merely
run.

### Applied retroactively, and what that turned up

The rule was written after Stages 0-2 had already merged, so it was
applied backwards on the day it was adopted rather than assumed to have
held. It did not hold, and the record is more useful than the rule:

- **Stage 1** merged green and failed five of its own eight completion
  criteria when anyone finally looked, five days later.
- **Stage 2** merged green and failed three of nine.
- **The six-pass consistency sweep** on 2026-08-22 found stale claims in
  `docs/architecture/overview.md`, `rendering.md`,
  `knowledge-architecture.md`, `glossary.md` and two ADRs -- every one
  of them merged under green CI.

Those are now fixed and the criteria audited, so `main` is consistent as
of 2026-08-22 -- but the honest statement is that this rule has never
yet been satisfied *prospectively* by a branch. The first branch to do
so is the one that adopted it.

## When intent is ambiguous, hold a design session before implementing

**Standing rule, maintainer's instruction 2026-08-22**, and the
counterpart to the rule above: a merge gate that asks "is the intent
met?" is unanswerable when the intent was never settled.

**Trigger:** a task whose acceptance criteria cannot be written as
things that would fail. If drafting a criterion produces a sentence like
"behaves correctly", "works as expected", or "is reasonable", the
ambiguity is real and belongs to the specification, not to the
implementer's judgement at 2am.

**Output, and it is not a conversation log:** a recorded, *self-consistent*
plan -- criteria that could each fail, an explicit statement of what was
decided against, and every document the decision touches updated in the
same change. "Self-consistent" is the load-bearing word: a design
session that resolves one ambiguity by creating two contradictions
elsewhere has not finished.

**Do not resolve an ambiguity by picking the reading that is easiest to
implement.** That is the failure this rule exists to prevent, and it is
how a criterion ends up weaker than its qualifier -- the implementer
reads "must pass for every concrete `Field`", notices that the hard
reading needs a suite that does not exist, and writes the easy one. Ask.

**Do not defer a design session into the implementation either.** The
cost of disambiguating is roughly constant; the cost of having guessed
wrong compounds with everything built on the guess. Stage 2's contract
suite was cheap to fix eight days later only because nothing had been
written against it yet.

## Every task names the stage criteria it discharges

**Added 2026-08-22, from the same retro-audit.** A task entry in
`docs/planning/roadmap.md` gains a sixth section alongside Purpose /
Dependencies / Artifacts / Implementation / Acceptance Criteria:

> **Discharges:** which of its Stage's Completion Criteria this task
> advances, and -- for each one it claims to *close* -- the specific
> artifact that closes it: a test name, a file path, a run id. Not a
> tick.

Three things this buys, each of them a defect that has actually
happened:

1. **Every criterion gets an owner.** Documentation accuracy failed in
   Stage 1 (criterion 8) and again in Stage 2 (criterion 9), and it is
   the only criterion in either stage that no task pointed at. Work
   nobody owns is not done late; it is not done at all until someone
   audits for it.
2. **The criterion gets read while the code is being written.** Every
   row in the qualifier table above was found days after the code
   landed, by someone reading with intent to find fault. A task that has
   to name what it discharges has to open the criterion, which is the
   entire mechanism -- TASK-017 quoting "not as a value some other piece
   of code must remember to pass alongside it" while writing
   `build_vector_field_arrows(field, mesh, ...)` is a contradiction
   nobody types out on purpose.
3. **"Is the stage nearly done?" becomes readable rather than
   auditable.** Undischarged criteria are a list, visible at any moment,
   instead of a question that needs a two-hour review to answer.

**A discharge line that names no artifact is a rubber stamp**, and worth
less than nothing, because it converts an open question into a false
answer. If the artifact cannot be named, the criterion is not
discharged -- say so, and leave it open. "Partially: closes the first
half, second half still open" is a legitimate and useful entry.

**Criteria that no task can own get one anyway.** Documentation
accuracy, `make ci` green on a real runner, and the exit audit itself
are stage-level work, not task-level work -- which is exactly why they
went unclaimed twice. The Stage's *last* task discharges them, named as
such when the stage's criteria are written, not discovered at the end.

## The intent lives in the qualifier

**Added 2026-08-22, after the Stage 0-2 retro-audit** (below). This is
the most repeated defect this repository has produced, and it has one
shape.

An acceptance criterion is written as a headline plus a qualifying
clause -- an "e.g.", an "i.e.", a "not just", a "rather than", a "so
that". The headline says what to build. **The qualifier says what would
make building it pointless.** Implementation consistently satisfies the
headline and consistently misses the qualifier, because the headline is
what reads like a specification and the qualifier reads like commentary.

Six instances, from two stage audits:

| Where | Headline -- implemented and tested | Qualifier -- the actual intent, not tested | What shipped |
|---|---|---|---|
| Stage 1 C3, TASK-012 | discrete geometric closure, `sum(face_area * normal) == 0` per cell | "geometrically correct, **not merely plausible**" | no accessor validated a cell or face id; `face_neighbours(9999)` on a six-cell mesh returned cells 3330 and 3333 |
| Stage 1 C4, TASK-012 | "fully constructible from a `PyFlowConfig` alone -- no bespoke code" | "`PyFlowConfig` alone **determines** the mesh" | `extent: [10.9, 3.99]` silently became `(10, 3)` -- constructible, but not the mesh anyone configured |
| Stage 1 C6, TASK-013 | "a given drag distance pans by more world-space distance at low zoom than at high zoom" | "**i.e. pan tracks the pointer under the cursor**" | pan was monotonic in zoom and wrong by 1.78x; the weaker bullet passes at every scale factor |
| Stage 2 C1, TASK-017 | `Field` carries the mesh it belongs to | "**not as a value some other piece of code must remember to pass alongside it**" | `build_vector_field_arrows(field, mesh, ...)` took both, and nothing checked they agreed |
| Stage 2 C2, TASK-015 | "a shared, implementation-independent contract test suite", parametrised, cited by name in three task records | "that any future implementation (**e.g. a staggered placement**) must pass unchanged" -- and the AC's own preamble, "must pass for every concrete `Field`" | the suite asserted `values.shape == (num_cells, *component_shape)`, which no staggered placement could satisfy |
| TASK-016 (found by the retro-audit itself) | `magnitude()` checked against a hand-computed 3-4-5 vector giving 5 | "a hand-computed field where the norm **isn't trivially 0 or 1 anywhere**" | one of the two cells is `(0.0, 0.0)` |

The third row is the one that changed how seriously to take this. That
bug was recorded as a fixture-degeneracy failure -- a test whose 4:3
camera on a 4:3 canvas made two formulas agree -- and it is that. It is
*also* a qualifier failure, independently: "pan tracks the pointer under
the cursor" is an exact, aspect-ratio-independent property, and a test
of the sentence as written would have failed at 1.78x on any fixture.
Two separate rules would each have caught it, and neither was applied.

### At drafting time: every qualifier becomes a bullet, or is struck

When a task's acceptance criteria are written, no intent may survive as
prose. Each qualifying clause either becomes **its own bullet with its
own named test**, or is deleted as a claim the task is not actually
making.

Deleting is a real option and is often the right one. The point is that
the choice gets made deliberately, while the criteria are being written,
rather than resolved by default in favour of whatever the bullets happen
to say.

Run it against TASK-015 to see it work. "Must pass for every concrete
`Field`" has to become a bullet -- *"a `Field` implementation that is
not a `CollocatedField` passes this suite unchanged"* -- and the moment
anyone tries to write that test against a fixture typed
`list[type[CollocatedField[Any]]]`, the gap is obvious. On the day the
task was drafted, before any code. Either you build the `Field`-level
suite or you strike the claim; both are fine, and silently keeping the
sentence while testing something weaker is not.

**A preamble is a qualifier too, and the most dangerous kind**, because
it looks like a section header rather than a claim. TASK-011's
("Contract suite -- must pass for every `CoordinateSystem`") was honest:
round-trip, monotonicity and out-of-bounds handling are all genuinely
implementation-independent. TASK-012 and TASK-015 copied its shape onto
bullets that had not earned it. The shape is not the guarantee.

### At audit time: check the qualifier, not the headline

The same rule read backwards, for a stage exit audit or any review of
closed work. Take each criterion's "e.g.", "i.e.", "not just", "rather
than", "by construction, not by" clause and ask **could a passing
implementation still violate this sentence?** If yes, that is the
finding, whatever the headline says and whatever the tests are green on.

This is not a substitute for reading the code, and it does not find
defects the criteria never contemplated. What it finds cheaply, and
reliably, is the gap between what a task was for and what it settled
for.

### The sibling failure: rejection criteria stop at the constructor

Not a weakened qualifier but a missing one, found by the same
retro-audit and worth naming because it is mechanical enough to check
in seconds.

TASK-011 and TASK-012 both specified how construction rejects bad input
-- "constructing with `dx <= 0` or `dy <= 0` raises a specific, named
exception", "constructing with `nx <= 0` or `ny <= 0` raises a specific,
named exception (mirrors TASK-011's check)". Neither said anything about
what an *accessor* does with bad input. So `Mesh` validated its
constructor arguments thoroughly and `face_neighbours(9999)` on a
six-cell mesh returned cells 3330 and 3333, which is Stage 1's criterion
3 failure in full.

TASK-015 got this right -- `value_at`/`set_value_at` raise
`InvalidMeshEntityError` for an out-of-range cell, in the contract suite
-- but only because Stage 1's audit had already happened and
`InvalidMeshEntityError` existed to reuse.

**When a task adds a type with both a constructor and accessors, it
needs a rejection criterion for each.** The constructor one gets written
because invalid construction is the failure a designer imagines; the
accessor one gets forgotten because the designer is imagining correct
use. A confident wrong answer from an accessor is the worse of the two
failures, and the cheaper one to specify.

## Verify a conversion where its factors are distinct

**Decided 2026-08-21, from the pan-tracking bug** (`docs/CHANGELOG-DESIGN.md`,
that date). TASK-013 verified its camera pan empirically -- a throwaway
offscreen script confirming which way the content moves -- and wrote
down that it had. That was the right instinct and it still shipped a
scale error of 1.78x, because a direction check establishes a sign and
says nothing about a magnitude.

The unit test alongside it is the more important lesson. It used a 4:3
camera on a 4:3 canvas, and the buggy formula (`camera.width`) and the
correct one (the visible extent, which pygfx expands to the viewport
aspect) return the same number at that aspect ratio. The test was not
weak; it was *cancelled*.

So: when a test exists to pin a conversion, choose a fixture where every
factor in it is distinct -- different width and height, non-square
aspect, spacing that isn't 1, an origin that isn't 0. If two quantities
in the formula can be equal, make them unequal. The existing suites
already do this for geometry (`test_mesh_contract.py` deliberately uses
`origin=(1.5, -2.25)`, `spacing=(0.1, 0.3)`, a 3x2 extent, and says why);
this rule is that habit stated once, for conversions rather than only
for coordinates.

Related, and worth checking at the same time: **an acceptance criterion
phrased as a proportionality is satisfied by any constant multiple of
the right answer.** TASK-013's read "pan proportional to zoom", which
the broken implementation satisfied exactly. A criterion about a scale
needs a test that pins the scale.

## Test-driven development

**Decided 2026-08-19, moving into Stage 1.** For implementation work,
write the failing test first, confirm it fails for the right reason
(red), then write the minimum code that makes it pass (green). This
follows directly from the rule above -- criteria phrased as things a
test can assert are, by construction, tests waiting to be written before
the code they'd check. Stage 0's own tests were mostly written
alongside or after the code they cover (the code came first, `docs/
practices.md`'s own "Regression tests on discovery" rule exists for bugs
found *after* the fact); Stage 1 reverses that order for new
functionality specifically. Doesn't apply retroactively to Stage 0's
existing code or tests -- this is how Stage 1 onward gets built, not a
demand to rewrite what already works.

## Audit code before calling it done

**Any code-writing task is reviewed under the Auditor stance
(`prompts/common/AUDITOR.md`) before its Definition of Done is
considered met -- not after merge, and not by the same pass that wrote
it.** Get the tests green (Test-driven development, above), then
re-open the diff as a reviewer who did not write it and is trying to
find the one place it's wrong. Fix what it finds, then audit again;
repeat until a pass finds nothing, or every remaining finding is
explicitly deferred with a stated reason (root `CLAUDE.md`'s Merge Gate,
criterion 4, "said honestly"). A single self-reviewed pass is not the
cycle -- it's the thing the cycle exists to replace.

Added 2026-08-24, generalising the same stance the End-of-session
consistency review states above (see there for what a single
self-reviewed pass missed) down to the task level. The pre-merge pass
already runs this stance at the branch level; running it per task as
well means the defects it catches are cheaper to fix and don't reach the
merge gate -- or a stage-boundary exit audit -- in the first place.

## Interface-first for any layer with a genuinely anticipated second implementation

**Decided 2026-08-20, generalising a pattern first applied to TASK-011.**
TASK-011's `CoordinateSystem` was deliberately built as an interface
that assumes nothing about spacing or placement, plus a shared
implementation-independent contract test suite, plus one concrete
implementation -- because `docs/architecture/engine.md`'s own contract
for that layer already described it as needing to support more than one
shape eventually. When asked whether that was specific to coordinates
or should generalise, the maintainer's call: **it generalises to any
layer whose `engine.md` contract already anticipates multiple
implementations**, not only where `docs/architecture/icds.md` defines a
formal ICD. TASK-012 (Mesh) and TASK-014 (Field Interface) are the next
two instances -- both `engine.md` contracts already say "independent of
X" or "regardless of Y" for exactly this reason, so building them
concrete-first would only mean redoing the interface work later, once
the second implementation stops being hypothetical.

**This is not the same question as whether a layer gets a formal ICD.**
`icds.md` scopes ICDs to `ADR-003`'s six named, user-configuration-facing
components; Mesh and Variables are explicitly excluded there and remain
so -- that scope didn't change. What changed is purely an internal
engineering discipline: build behind an interface with contract tests
from the start, whether or not that interface is ever formally
documented as a user-facing configuration choice. A component can have
one without the other in either direction.

**Judgement call, not a mechanical rule:** the trigger is a real,
already-written architectural claim that a layer needs multiple
implementations (an `engine.md` contract phrase, an upgrade-path entry),
not any theoretical possibility that something might someday need to
vary. Building an interface for a layer nothing has ever suggested will
need a second implementation is exactly the speculative abstraction the
root `CLAUDE.md` and `src/pyflow/rendering/CLAUDE.md` both warn against.

## Regression tests on discovery

**Whenever a bug is found mid-task -- not reported by the maintainer,
but discovered while building or verifying something else -- add a
regression test with measurable pass/fail criteria in the same change
that fixes it.** A fix without a test that would have caught it leaves
the same bug free to reappear silently.

Maintainer's instruction, 2026-08-16, after two bugs were found and
fixed this way during Stage 0 (D3's rendering-window offscreen path
never actually presenting a frame; D4's circular import between `engine`
and `rendering`). The test should target the exact failure mode -- an
exact value, a specific exception, a concrete boundary condition -- not
a vague "doesn't crash" smoke check. If the bug can't be captured
automatically (interactive/display-dependent behaviour, for example),
document the manual verification command in the code's own `CLAUDE.md`
instead of skipping verification entirely -- see `src/pyflow/rendering/
CLAUDE.md`'s `close_keys` entry for the pattern.

## Python version policy

Not a fixed floor for its own sake, but not continuous tracking either.
**Periodically check whether a newer Python would benefit PyFlow, and
upgrade when it does** -- new performance work, a language feature worth
using, a dependency that wants it. There is no standing obligation to be
on the latest release; the obligation is to occasionally ask, not to
follow every release automatically.

PyFlow has no external consumers yet, so there is nothing to stay
compatible with today, which is what makes upgrading cheap to consider.
**Revisit the moment someone else depends on PyFlow** -- that is when a
conservative floor starts to earn its keep, and the policy should flip to
deliberate stability.

### The version is derived, not chosen first

**Correction, 2026-08-15 (maintainer's insight).** PyFlow does not need
to *specify* a Python version independently -- it needs one that every
eventual dependency actually supports. The version is the **intersection**
of what the chosen dependencies support, computed once the
dependency-defining decisions (principally A2c: the array library and
renderer) are made -- not asserted ahead of them and then defended
against whatever those decisions turn out to need.

This is not a hypothetical concern: it is exactly what went wrong on
2026-08-15 itself. Python 3.14 was set as A1b's chosen version *before*
`docs/planning/backlog.md` A2 existed. When Taichi (a rendering-class
candidate under consideration) turned out to cap at Python 3.13, that
had to be framed as "reopening" an already-closed decision, purely
because a specific number had been committed to too early -- something
that was never actually blocking anything got treated as a constraint to
argue around. Under the derive-last model, hitting a ceiling like that
is not a reopening; it is simply computing the answer, because nothing
was fixed yet.

**In practice:** the dev tooling (`uv`, `ruff`, `mypy`, `pytest`,
`pre-commit`) is unlikely to ever be the binding constraint -- these move
fast and adopt new Python quickly. The binding constraint is almost
always the heavier, compiled dependencies -- the array library and
renderer chosen in A2c, and whatever domain-specific libraries later
stages add. So in practice this means: don't pin `requires-python` as a
foundational, load-bearing decision during Stage 0's early tasks; treat
it as provisional until A2c's dependencies are locked in, then set it to
the highest version all of them support. After that point, the
*ongoing* policy above (periodic review, revisit when it benefits the
project) governs how the number moves.

The version appears in four places that must move together:
`requires-python` and the `Programming Language :: Python` classifier in
`pyproject.toml`, `[tool.ruff] target-version`, `[tool.mypy]
python_version`, and the CI matrix. Check that the pinned tool versions
actually support the target before bumping -- both were verified for 3.14
when 3.14 was first adopted (2026-08-15), and re-verified as the correct
answer once actually derived from A2c's candidates the same day (see
`docs/planning/backlog.md` A1b).

Adopted 2026-08-15 at Python 3.14; the previous 3.12 was arbitrary rather
than chosen.

## Tooling dependency update policy

Added 2026-08-19 (`docs/planning/backlog.md` F1) -- same shape as the
Python version policy above, generalised to the rest of the toolchain:
**periodically review whether pinned tool versions would benefit from an
update -- a bug fix, a new check, a security patch -- and update when
they do.** Not continuous tracking; there is no standing obligation to
be on the latest release of anything, here either.

Covers `.pre-commit-config.yaml`'s hook revisions and `uv.lock`'s
resolved packages. `pre-commit autoupdate` handles the mechanical part
for hook revisions (already noted in that file's own header comment);
`uv lock --upgrade` for `uv.lock`. **Verify the updated tool still
supports the pinned Python version before committing a bump** -- the
same check already required when Python itself moves, above -- since a
hook or package that silently drops support for the pinned interpreter
is a CI break waiting to happen, not a hypothetical.

### Standing watch items

A pin that exists to dodge a *known upstream defect* is different from
an ordinary version choice: it has a specific condition that releases
it, and without somewhere to write that condition down it becomes a pin
nobody remembers the reason for. List those here, with the trigger
stated as something checkable rather than a feeling.

- **`pytest<10`** (`pyproject.toml`, pinned 2026-08-22). `pytest-bdd`
  8.1.0 -- still the latest release -- passes `nodeid`/`baseid` to
  pytest's `_register_fixture`/`FixtureDef`, which pytest 9 reports as
  `PytestRemovedIn10Warning`. Verified by running a scenario under
  `-W error::pytest.PytestRemovedIn10Warning`, where it fails rather
  than warns; it passes normally only because warnings are not errors
  here.
  **Why this one matters more than a usual pin:** since
  `adr/ADR-007-executable-acceptance-criteria.md`, feature files *are*
  the acceptance criteria for Stage 4+ simulation work, so the failure
  mode is not "some tests break", it is "the acceptance criteria stop
  executing".
  **Trigger to unpin:** pytest-bdd releases a version containing the fix
  in its PR #827 (`fix: avoid deprecated nodeid argument to
  _register_fixture`, open as of 2026-08-05, against issue #823). Check
  by running the command above against the released version and
  expecting a pass. Until then the pin stays, and the exposure is
  narrow: only a pytest 10 release carrying something this project
  actually needs would make it cost anything.
  **If the fix never lands**, ADR-007 names the fallbacks in order --
  stay pinned, vendor a minimal Gherkin runner, or reverse the ADR.

---

# Blast Radius

**Before making a change, work out what else it affects. Update all of it
in the same change.**

A change to code, documentation or a plan is rarely self-contained. Ask,
every time:

- What references this by name or path?
- What restates, summarises or depends on this information?
- What inventory tracks it (`docs/repository-manifest.md`,
  `docs/planning/knowledge-architecture.md`)?
- Which `CLAUDE.md` describes the directory it lives in?
- Which decisions were made *because* of how this used to be?

Then update those in the same change, not in a follow-up. A repository
that is briefly inconsistent is a repository someone will read while it
is wrong.

Searching for the thing's name is usually enough to find the radius; a
missed reference is nearly always one a `grep` would have caught.

If something in the radius genuinely cannot be updated now, **say so
explicitly** where the divergence is -- a recorded inconsistency is a
known problem, an unrecorded one is a trap. `docs/CHANGELOG-DESIGN.md` is
append-only by convention, so it is corrected by appending rather than by
rewriting.

This rule exists because the repository has already been bitten by it
four times, each caught only by a later audit:

- `docs/handbook.md` was retired and `README.md` updated, but
  `docs/practices.md` still told every session to "read the handbook".
- The MVP definition and upgrade paths moved out of
  `implementation-plan.md`, leaving `ADR-002`, `ADR-003`,
  `prompts/global/project.md` and `prompts/global/CLAUDE.md` all pointing
  at their old home.
- Artifacts were created and moved without updating the two inventories,
  until the manifest described roughly 35 files that did not exist.
- A numerical survey was written at a path no specification referenced,
  so both inventories reported it missing while it sat in the repository.

The `AGENTS.md` to `CLAUDE.md` rename is the counterexample: every
reference was enumerated and updated in one pass, and nothing broke.

## Specific instances of the rule

These follow from the above and are called out because they are the ones
most often missed:

Whenever a document is created or substantially filled in, update its
nearest `CLAUDE.md` in the same change with concrete guidance on how and
when to maintain that file. Do not wait for the directory to be
"finished" -- a future contributor arriving at that directory should
learn what matters there without reconstructing it from other documents.

Whenever an artifact is added, moved, or changes status, update
`docs/repository-manifest.md` and the corresponding entry in
`docs/planning/knowledge-architecture.md` together. They describe the
same artifacts from different angles and drift apart when only one is
touched.

**Whenever functionality is added or changed that affects how a
developer installs, runs, tests or removes the project, update
`README.md`'s Quick Start section in the same change** (added
2026-08-15, maintainer's instruction). A Quick Start that lags behind
what the project actually does is worse than no Quick Start at all --
it actively misleads the person it exists to help, which is exactly the
"future contributor who has forgotten everything" this repository is
meant to explain itself to. Don't duplicate detail that would drift:
where a command already explains itself when run (e.g. `make clean`
stating what it can't remove and why), point at running it rather than
restating its output in the README.

The Definition of Done for documentation lives in
`docs/documentation-guidelines.md` and is not restated elsewhere.

**Completeness claims belong only in the two documents that track
completeness** (added 2026-08-18, after a documentation review found five
instances of the same drift in one pass). `docs/repository-manifest.md`
and `docs/planning/backlog.md` exist to record how finished things are.
When any *other* document says a file is "empty", "largely unwritten",
"a stub", or "not yet decided", it has taken on a job it will not keep up
with, and it goes stale silently -- the reader has no reason to doubt it.
All five instances found were false, and three had been false since the
day they were written:

- `prompts/global/project.md` called the Handbook "largely unwritten"
  the day after all sixteen entries were written -- in a document whose
  own opening paragraph says it excludes current status.
- `docs/glossary.md` said `docs/planning/releases.md` "is empty" after
  E7 wrote it.
- `docs/repository-manifest.md` and `docs/architecture/CLAUDE.md` both
  described the A2c instance decision as still open, on the same day
  `adr/ADR-005` decided it.
- `docs/architecture/engine.md` called `advection.md` "an empty stub"
  hours after E3 wrote it.

`make check-claims` mechanises the checkable half of this
(`tools/validators/check_claims.py`, added 2026-08-18): it resolves the
paths a completeness claim names and reports only where the claim
contradicts what is on disk. It cannot judge whether a claim is
legitimate, so it is advisory and reports rather than fails. It does not
replace reading; it means a stale claim has one more chance of being
caught than a person happening to notice it.

The fix in each case was to **delete the status claim, not update it** --
updating "unwritten" to "written" only sets up the next staleness. Say
what a document is *for*; link to the manifest or backlog for how far
along it is. Where a status genuinely must appear outside those two
documents (a status banner at the top of a decision-support document, for
example), phrase it as what has already happened -- "this fed decisions
X and Y" -- rather than as what remains open, since the former does not
rot.

**Deleting a directory or file changes counts stated elsewhere.** Retiring
`tools/planner/` and `tools/scripts/` (E10) also removed two `CLAUDE.md`
files, which `docs/planning/backlog.md` E9 correctly updated (45 -> 43)
while `docs/planning/roadmap.md`'s TASK-009 row and
`docs/repository-manifest.md` both kept saying 45. The end-of-session
checklist's "grep for every restatement of anything a number describes"
already covers this; it is called out here because a *deletion* is the
case most easily forgotten -- nothing in the change itself mentions the
number that just became wrong.

## Closing a backlog item is a Blast Radius event

**Added 2026-08-15, maintainer's instruction, after a backlog review
pass found real coherence bugs** (`docs/planning/backlog.md`, `git log`
"Backlog review pass"): items fully complete but still showing `[ ]`;
stale specific values (a Python version) left in place after they
changed; an item describing a workflow a newer tool had superseded
without saying so; a dependency relationship never stated explicitly;
items quietly unblocked by other work and still reading as blocked;
evidence-mappings citing an item ID that had since been split and no
longer existed. None of these were found by the audits that produced
them -- they were found by a dedicated re-read, which means they sat
wrong for a while first. **The backlog must always be current and
reliable** -- an agent picking up the next piece of work reads it as
ground truth, and a wrong backlog is more dangerous than an honestly
incomplete one, because it doesn't look wrong.

When an item's acceptance criteria are satisfied, in the **same
change**, not a later pass:

- **Mark it `[x]` immediately.** Don't leave a parent item open once
  every sub-step under it is checked -- flip the parent the moment the
  last child closes, not in a separate "closing" pass later.
- **Grep the file for the item's own ID** (e.g. `A1b`, `C1`). Every other
  item that names it -- as a dependency, a blocker, "follows X", "depends
  on X", "blocked on X" -- needs checking: is it unblocked now? Say so
  explicitly in that item's own text, not just implicitly via the closed
  item's checkbox.
- **If the item was split or renumbered** (one item becoming several,
  e.g. `C1` into `C1a`/`C1b`), grep for the **old** ID across the whole
  file -- evidence-mappings, cross-references, other items' prose -- and
  update every hit. A rename inside one item is invisible to everything
  that still points at the old name.
- **If the item was promoted from a Part III audit finding** (Part I
  items commonly say "promoted into Part I as E5" when they're created),
  the promotion only updates the *new* item -- the *original* Part III
  entry stays sitting there as `[ ]`, unless someone goes back and closes
  it too. Grep Part III for the finding's own description (not just the
  new item's ID, which the old entry won't mention) and mark it `[x]`,
  pointing at the item that actually closed it, rather than repeating
  the outcome. Found seven separate instances of exactly this drift on
  2026-08-17 (ADR-002, `compatibility.md`, `releases.md`,
  `dependency-tree.md`, both Handbook content findings, and the
  `docs/architecture/{overview,rendering,repository}.md` finding) --
  each one had been correctly promoted and correctly closed in Part I,
  with only the mechanical step of closing the Part III original missed
  every time.
- **Update any specific fact the item changed that other items restate**
  -- a version number, a tool name, a command, a file path. Don't leave
  the superseded value sitting in a different item's prose; that's the
  general Blast Radius rule, applied at closing time specifically because
  closing is exactly when such facts change.
- **If the item added a new capability** (a Makefile target, a script, a
  convention), search for every other place that duplicates what it now
  does, and point at the new capability instead of restating the
  sequence it replaces -- this is what keeps two definitions of the same
  thing from drifting apart, per P-011.
- **Write prospective language as retrospective the moment it's true.**
  An item that said "will produce X" should say "produced X" as soon as
  X exists -- don't leave forward-looking phrasing sitting past the point
  where it became stale. **Where the same fact is restated in a
  structured document rather than a one-off sentence, prefer the rule
  below to relying on this one.**

---

# Let a checked artifact carry status, not a tense

**Standing rule, 2026-08-24.** Where a document records whether
something has been built yet, say it by **naming an artifact whose
existence is checked** -- a module path, gated by `make
check-references` -- not by choosing a tense or a status-bearing label.
A named path that exists means built; naming only the roadmap task that
will build it means not yet. Updating is then *additive*: a task lands,
you add its path. There is no tense to rewrite and no label to rename.

`docs/architecture/engine.md`'s nine layer entries are the worked
example, converted on 2026-08-24.

**Why this exists.** The rule above it -- rewrite prospective language
when it becomes true -- is correct and has still failed three times,
because a status-bearing label makes the update *multiplicative* rather
than local. `engine.md` used two labels, `Arrives via:` (unbuilt) and
`Implemented in:` (built), so a task landing meant renaming a field in
`engine.md` *and* correcting every other document that had counted or
quoted which layers carried which label. Each failure was found by an
exit audit, never by CI:

- **Stage 2:** `engine.md`'s Variables entry still read "Arrives via"
  a day after TASK-014/015/016 landed -- one screen below that same
  document's rule saying it should not.
- **Stage 3:** `engine.md`'s own "Construction and Configuration"
  section still called per-layer strategy selection "Stage 3+ work, not
  yet done" after Stage 3 built it, and `src/pyflow/CLAUDE.md` still
  called `engine/numerics/` "planned for Stage 3".
- **Stage 3, the expensive one:** `docs/architecture/overview.md` said
  "the remaining seven layers read 'Arrives via'" when only Flux did,
  and called `icds.md` "still entirely target architecture" with "none
  of its six configuration-facing contracts has an interface yet" --
  the direct opposite of the truth, in a document TASK-021 never
  touched, and therefore outside a "check every touched file" sweep.

A tense cannot be checked by anything. A path can, and already is.

Doing this per-item, as each one closes, is cheaper than a later sweep
and is what prevents the sweep from being needed at all -- a dedicated
backlog review pass finding nothing is the goal this rule aims at, not
a review pass finding a list of bugs to fix.

---

# Design Rules

Future us is assumed to have forgotten everything.

Optimise for understanding over remembering.

When choosing between two equivalent solutions, prefer the one that is easier to understand and maintain.

End each design session by identifying the permanent knowledge created and recording it in the appropriate document before continuing development.
