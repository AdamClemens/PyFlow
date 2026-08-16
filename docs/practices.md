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
7. Commit changes.

Steps 1 and 5 previously read "read the handbook" and "update the
handbook." That referred to the project-meta `docs/handbook.md`, retired
on 2026-08-15; the name now belongs to the scientific handbook under
`docs/handbook/`, which is not what a session should open with.

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
