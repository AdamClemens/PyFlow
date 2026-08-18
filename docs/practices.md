# Engineering Practices

These practices describe **how** the project is developed.

---

# Session Workflow

Every design or implementation session follows this sequence.

1. Read the current design state: `docs/planning/roadmap.md` for what is
   next, `docs/planning/backlog.md` for what is outstanding.
2. Review open decisions (`docs/planning/backlog.md`, and the Open
   Questions entries in `docs/CHANGELOG-DESIGN.md`).
3. Perform design or implementation work.
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

- Every stage after Stage 0 leaves PyFlow with a working simulation.
- Every feature satisfies the Definition of Done.
- Every capability should eventually have a demonstration.
- Every important artefact should be traceable.

Stage, Capability Level and Release are three distinct things; see
`docs/glossary.md` before using them interchangeably.

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
  where it became stale.

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
