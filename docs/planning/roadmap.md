# PyFlow Execution Roadmap

This roadmap defines the chronological implementation order of PyFlow.

Each milestone produces a working engine that demonstrates one new capability. Existing functionality must continue to work throughout development.

This document is authoritative for execution: what to work on next, in
what order, and what "done" means for it (Purpose / Dependencies /
Artifacts / Implementation / Acceptance Criteria / Discharges per task).

**"Discharges" is the sixth section, added 2026-08-22** (`docs/
practices.md`, "Every task names the stage criteria it discharges"):
which of its Stage's Completion Criteria the task advances, and for each
one it closes, the artifact that closes it -- a test name, a file path,
a run id. Tasks written before that date do not have one; Stage 3 onward
do. **Acceptance Criteria are also now written under the qualifier rule**
(`docs/practices.md`, "The intent lives in the qualifier"): no intent
survives as prose, so every "e.g.", "i.e.", "not just" and "rather than"
is either its own bullet with its own test or is struck.

**From Stage 4 (TASK-023) onward, a task's Acceptance Criteria section
names a Gherkin `.feature` file rather than containing prose bullets**
(`adr/ADR-007-executable-acceptance-criteria.md`, 2026-08-22). The
scenarios in that file *are* the criteria -- there is no second artifact
for a test to be weaker than, which is the structural half of the same
defect the qualifier rule attacks at the drafting end. Stage 3 is
exempt and says so per task; Stages 0-2 keep the prose criteria they
were closed against, as the record of what they were closed against,
with a pointer where a golden demo was later retrofitted.

Related, each owning one thing this document does not:

- `docs/planning/implementation-plan.md` — the long-range Capability
  Level view
- `docs/implementation/mvp.md` — what the MVP is
- `docs/implementation/upgrade-paths.md` — how each component is later
  replaced or extended

**Note (2026-08-15):** Stage 1 onward's task IDs were renumbered to
continue from Stage 0 (TASK-011 onward) rather than restarting at
TASK-001 -- they previously collided with Stage 0's TASK-001..010 (e.g.
TASK-001 meant both "Development Environment" and "Coordinate System").
See `docs/CHANGELOG-DESIGN.md` for the mapping.

---

# Stages and Capability Levels

This document's Stages and `implementation-plan.md`'s Capability Levels
are two views of the same project, not two names for the same ladder.
Stages are execution units; Levels are capability bands. Several Stages
can serve one Level.

| Stage | Capability Level |
|-------|------------------|
| 0 — Engineering Infrastructure | 0 — Project Foundation |
| 1 — Representing Space | 1 — Simulation Engine |
| 2 — Representing Fields | 1 — Simulation Engine |
| 3 — Numerical Engine | 1 — Simulation Engine |
| 4 — First Numerical Methods | 1 — Simulation Engine |
| 5 — First Fluid Solver (MVP) | 2 — First Fluid Simulation |
| 6 — Additional Physical Fields | 3 — Multiple Transported Fields |
| 7 — Better Numerics | 4 — Numerical Improvements |
| 8 — Geometry | 5 — Geometry |
| 9 — Adaptive Resolution | 6 — Adaptive Resolution |
| 10 — Additional Numerical Frameworks | 7 — Additional Numerical Frameworks |
| 11 — Three Dimensions | 8 — Three-Dimensional Simulation |
| 12 — Performance | 9 — High Performance Computing |
| 13 — Advanced Physics | 10 — Advanced Physics |

**First divergence, resolved 2026-08-21 (maintainer's call): a Stage
was added.** Capability Level 7 had no corresponding Stage, leaving the
plan's "Dam Break / Free Surface" golden demo unreachable from this
roadmap -- open since 2026-08-15. Stage 10 (Additional Numerical
Frameworks) now serves it, and **Stages 10-12 were renumbered to 11-13**
to make room:

| Was | Is now |
|-----|--------|
| Stage 10 — Three Dimensions | Stage 11 — Three Dimensions |
| Stage 11 — Performance | Stage 12 — Performance |
| Stage 12 — Advanced Physics | Stage 13 — Advanced Physics |

No `TASK-NNN` identifiers moved: Stages 7-13 are all still at the looser
"Tasks include" level of planning, so nothing numbered existed to
renumber. That is the second time this project has renumbered rather
than lived with a collision (task IDs, 2026-08-15) and the second time
it was cheap because it happened early.

**The decision was made against the evidence assembled for it, which is
worth recording rather than smoothing over.** The 2026-08-21 audit
recommended dropping the Level, on three grounds:
`docs/handbook/numerical-methods/compatibility.md` ("Combinations
needing separate engines") says pairing a mesh-based method with a
mesh-free particle method as the *primary* solver means "hosting both as
first-class citizens of one shared internal architecture is
impractical"; `adr/ADR-002-fvm-first.md` had already placed SPH as
"left open as a possible future alternative framework", not core engine
scope; and SPH, FLIP, PIC and free-surface flow appear nowhere in
`docs/planning/dreams.md`, `docs/implementation/mvp.md` or
`docs/planning/capability-map.md`. The maintainer chose to keep the
Level and add the Stage. **Stage 10 below therefore carries an explicit
architectural caution**, so whoever reaches it meets the handbook's
finding before designing rather than after.

**Second known divergence, found and decided 2026-08-20:**
`docs/planning/capability-map.md`'s "Analysis" top-level capability
(Measurements, Diagnostics, Validation, Export, Comparison) has no Stage
or Capability Level anywhere in either this table or
`implementation-plan.md`'s ten Levels -- not even the loose "no Stage
yet" treatment Level 7 gets, since Analysis is not itself a numbered
Level at all. **Decided, maintainer's call: no dedicated Level.**
Validation and Comparison are handled distributed, folded into each
physics-implementing task's own acceptance criteria (`docs/planning/
backlog.md`, "physical correctness validation") -- concretely,
conservation checks per numerical solver and emergent-phenomena checks
(does the right instability emerge under the right configuration,
TASK-034 onward) landed as acceptance criteria on existing tasks rather
than a new deliverable. Measurements/Diagnostics/Export follow the same
pattern **Rendering** already set: no dedicated Level, tasks added to
whichever Stage needs them as each becomes useful (TASK-007, then
TASK-013, TASK-017 -- never one Level holding all of Rendering).

For the definitions of Stage, Capability Level and Release, see
`docs/glossary.md`.

---

# Stage 0 — Engineering Infrastructure

## Goal

Establish the engineering environment required to support long-term, maintainable development of PyFlow.

Stage 0 intentionally contains no CFD functionality. Its purpose is to ensure that all subsequent development occurs within a consistent, automated, reproducible and well-documented engineering environment.

Completion of Stage 0 should allow a developer or coding agent to clone the repository and immediately begin implementing Stage 1.

**Do not use TASK-000..010's Acceptance Criteria as a template for a new
task** (noted 2026-08-22, Stage 0-2 retro-audit). They predate
`docs/practices.md`'s "Acceptance criteria must be testable" rule, which
was adopted on 2026-08-19 moving into Stage 1, and most of them cannot
fail: "provides sufficient information for future development"
(TASK-008), "compact enough to minimise context-window usage"
(TASK-009), "All Stage 0 components integrate correctly" (TASK-010).
They are left exactly as written because they are the historical record
of what Stage 0 was closed against, and rewriting closed criteria to
look better is the opposite of an institutional memory -- but a task
drafted from here would inherit the defect the rule exists to prevent.
TASK-011 onward is the current shape; TASK-018 onward adds the
qualifier rule and a **Discharges** section on top of it.

### Status as of 2026-08-19: Stage 0 complete, all nine criteria met

The ninth and last criterion (CI executing, demonstrated by a green run)
closed the same day, a few hours after the rest of this audit: a remote
was created, and the first three real pushes each hit a genuine bug
`make ci` alone had never exercised (a flaky apt mirror hanging Ubuntu's
runner, a native crash in the interactive-display probe on a truly
headless machine, and a platform-dependent sort in the docs-index
generator) -- each found from a real log, fixed, and confirmed on a
subsequent green run before being called fixed, not asserted from the
fix looking right. The push that merged the last of the three
(`9c66e25`) is green on both platforms -- verified directly against the
run itself, not inferred from the PR merging. See the Completion
Criteria audit below for the full per-criterion record, and
`docs/CHANGELOG-DESIGN.md` (2026-08-19) for the three bugs themselves.

This previously read "in progress and substantially incomplete" (as of
2026-08-15, the day the engineering environment did not exist yet) --
stale since well before this correction; superseded by all eleven
TASK-000..010 rows below reading **Done**.

| Task | Status |
|------|--------|
| TASK-000 Engine Skeleton | **Done** 2026-08-15 -- `pyflow` package with `engine/physics/rendering/configuration`; imports, `python -m pyflow`, ruff and mypy --strict all verified passing |
| TASK-001 Development Environment | **Done** 2026-08-15 -- `uv.lock` and `.python-version` committed; `make install` → `clean` → `install` verified round-trip |
| TASK-002 Build System | **Done** 2026-08-15 -- all targets run for real (twelve as of 2026-08-18's advisory `check-claims`, on top of 2026-08-17's `check-docs`/`check-docs-index`); `lint` now runs the full pre-commit suite, `clean` states what it can't remove and why, new `ci` target added; `docs` is no longer a placeholder -- it regenerates `docs/index.md`, and `check-docs-index` fails CI if that file is stale |
| TASK-003 Automated Testing | **Done** 2026-08-16 -- coverage configured (`pytest-cov`), `make test` reports coverage; `unit/` and `golden/` now have real tests (D1-D5), only `performance/` remains empty, correctly (nothing to benchmark yet) |
| TASK-004 Continuous Integration | **Done** 2026-08-19 -- `.github/workflows/ci.yml` runs `make ci` on Linux + Windows, on push and pull request; a remote was created the same day, and the literal acceptance criterion ("every pull request executes the validation pipeline automatically") is met -- verified against real runs, not inferred: two PRs (#1, #2) each executed the pipeline automatically on open, and the push that merged #2 (`9c66e25`) is green on both platforms. Three real bugs surfaced along the way, each found from an actual log and confirmed fixed by a subsequent green run before being reported as fixed -- a flaky `azure.archive.ubuntu.com` apt mirror hanging Ubuntu's runner, a native `SIGABRT` in the interactive-display probe (`tests/integration/test_interactive_window.py`) on a truly headless machine, and a platform-dependent sort in `tools/generators/generate_docs_index.py` (`Path` comparison is case-insensitive on Windows, case-sensitive on POSIX). None of these were guessable from `make ci` passing locally alone -- see `docs/CHANGELOG-DESIGN.md` (2026-08-19) for each fix's own record. |
| TASK-005 Configuration Framework | **Done** 2026-08-16 -- YAML loading (`pyyaml`) into validated dataclasses (`PyFlowConfig`); `PyFlowConfig()` alone is a complete, valid default |
| TASK-006 Logging Framework | **Done** 2026-08-16 -- stdlib `logging`, centralised on the `pyflow` logger; every subsystem gets its logger via `get_logger(__name__)` and inherits level/formatting through the hierarchy |
| TASK-007 Rendering Framework | **Done** 2026-08-16 -- wgpu/pygfx (`adr/ADR-005`) window creation, render loop, clean shutdown; canvas backend (glfw interactive / offscreen headless) selected via configuration, both behind one interface (`src/pyflow/rendering/canvas.py`) |
| TASK-008 Repository Documentation | **Done** -- this row previously read "Partial -- core documents drafted; the Handbook is largely empty", stale since 2026-08-17 when all sixteen Handbook entries (E3/E4) were written; corrected 2026-08-19. All nine artifacts TASK-008 names (README, Handbook, ADRs, Capability Map, Implementation Plan, Engineering Principles, Documentation Guidelines, Practices, Dreams) exist with real content, verified directly by line count, not assumed |
| TASK-009 CLAUDE.md Hierarchy | **Done** 2026-08-19 -- 42 files exist (up from 40: F2 found `.claude/` and `.claude/hooks/` had no `CLAUDE.md` at all and were untracked by both inventories, fixed with real content, not placeholders; 40 itself down from 43: `assets/icons/`, `assets/shaders/`, `assets/textures/` retired 2026-08-19, E9, no document anywhere having ever stated what they were for, the same test that retired `tools/planner/`/`tools/scripts/`, 2026-08-17, E10; 43 itself down from 45 for that earlier retirement); **4** are still generic placeholders, 38 carry real content. E9's *Done when* was revised the same day it closed: no placeholder may remain in a directory that has content, not no placeholder anywhere -- all 4 remaining (`docs/tutorials/`, `examples/experiments/`, `examples/tutorials/`, `tests/performance/`) sit in directories with no real content yet, verified directly. **Count corrected 2026-08-22**, from 7 to 4: `assets/CLAUDE.md`, `assets/colourmaps/CLAUDE.md` and `src/pyflow/physics/CLAUDE.md` were given real content on 2026-08-22 (the first two once TASK-017 landed and settled what would actually fill `colourmaps/`; the third once drafting Stage 3 made the phenomena-vs-numerics boundary specific). That change did not update this count anywhere -- found by the consistency sweep that followed it, which is the same three-document blast radius this row already warns about. `docs/planning/backlog.md` E9/F2 hold the file-by-file breakdown and are the authoritative count |
| TASK-010 Engine Bootstrap | **Done** 2026-08-16 -- `pyflow run` loads configuration, initialises logging, opens the render window, runs the loop, exits cleanly; verified with both the offscreen backend (automated, `tests/integration/test_bootstrap.py`) and the real interactive glfw backend (manual run, a real window opened and closed cleanly). `make ci`'s pass is what TASK-010 means by "the CI pipeline passes" here, per the C2 scope decision above -- not a claim that GitHub Actions itself has run it |

This paragraph previously said `make install` and `make test` were still
expected to fail, pending `uv.lock` and a test suite (B2/C1) -- stale
since 2026-08-16 and corrected 2026-08-19. Both now succeed: `uv.lock`
is committed (B2) and `make test` runs the suite with coverage
(C1a/C1b): 337 tests at 99% as of 2026-08-22 (adopting executable
acceptance criteria and the merge gate), having been 64 when this
paragraph was rewritten on 2026-08-19, 202 earlier the same day, 212
after TASK-014, 226 after TASK-015, 250 after TASK-016, 287 after
TASK-017, 297 after TASK-039 and 315 after the Stage 2 exit audit.
**Fourteen of those 337 are Gherkin scenarios rather than pytest
functions** (`adr/ADR-007-executable-acceptance-criteria.md`), which is
why the total moved without the golden demos gaining coverage: the three
demos' fourteen checks were re-expressed, not added to. **All** `make ci`
targets pass, verified via the Makefile itself, not only via `uv tool
run` in isolation -- that is `lint`, `typecheck`, `test`, `check-docs`,
`check-docs-index`, `check-graph`, `check-dependency-tree`,
`check-inventory` and `check-manifest`, the last four of which this
sentence did not name until 2026-08-22 because they were added to the
target after it was written.

A live test count in a document nobody re-reads is a standing liability
-- this one went stale within a day of being written, and the identical
number in `docs/repository-manifest.md` went stale for five. Where a
count is *evidence for a past claim* (criterion 6 below, "64 tests
passing" during the 2026-08-19 fresh-clone check) it is a dated record
and should stay exactly as written. Where it describes the present, as
here, it needs a date attached so a reader can see how old it is.

Keep this table current -- it is the only place the roadmap states where
the project actually is, and `docs/planning/backlog.md` depends on it
being honest.

---

## TASK-000 — Create Engine Skeleton

### Purpose

Create the initial package structure and architectural skeleton for the PyFlow engine.

The repository should immediately communicate the intended architecture, even before any functionality has been implemented.

### Dependencies

None.

### Artifacts Produced

- Python package structure
- Placeholder packages
- Placeholder modules
- Initial package entry points

### Implementation

Create the `src/pyflow/` packages:

- engine/
- physics/
- rendering/
- configuration/

And the top-level repository directories:

- examples/ (demo, tutorial, and experiment scripts -- not an importable
  package; named `examples/` rather than `demos/` since it also holds
  `experiments/` and `tutorials/`, not only demos)
- tests/

Each package should contain placeholder modules representing the intended architecture.

No implementation beyond package initialisation is required.

### Acceptance Criteria

- The package imports successfully.
- No circular dependencies exist.
- The package structure matches the documented architecture.
- Example application entry point executes.

---

## TASK-001 — Development Environment

### Purpose

Create a fully reproducible development environment.

### Dependencies

TASK-000

### Artifacts Produced

- pyproject.toml
- uv.lock
- .python-version (optional)
- .pre-commit-config.yaml

### Implementation

Adopt:

- Python -- 3.14 as of 2026-08-15, derived from what the array library
  and renderer chosen in A2c actually support (confirmed: CuPy, PyTorch
  and jaxlib all ship cp314 wheels) rather than fixed independently
  beforehand; see the Python version policy in `docs/practices.md`
  ("the version is derived, not chosen first").
- uv
- Ruff
- Ruff Formatter
- MyPy
- PyTest
- pre-commit

Configure:

- dependency management
- formatting
- linting
- static type checking

### Acceptance Criteria

A clean clone can execute:

make install

followed by

make test

without manual configuration.

---

## TASK-002 — Build System

### Purpose

Provide a consistent interface for common engineering tasks.

### Dependencies

TASK-001

### Artifacts Produced

- Makefile

### Implementation

Provide commands for:

- install
- lint
- format
- typecheck
- test
- docs
- demo
- clean

### Acceptance Criteria

Every documented command executes successfully.

---

## TASK-003 — Automated Testing

### Purpose

Establish regression testing from the beginning of the project.

### Dependencies

TASK-002

### Artifacts Produced

- tests/
- pytest configuration
- coverage configuration

### Implementation

Configure:

- pytest
- coverage reporting
- smoke tests

### Acceptance Criteria

Tests execute locally and produce coverage reports.

---

## TASK-004 — Continuous Integration

### Purpose

Automatically validate every commit.

### Dependencies

TASK-003

### Artifacts Produced

- CI pipeline definition

### Implementation

Configure the CI pipeline to execute:

- installation
- linting
- formatting checks
- type checking
- unit tests

### Acceptance Criteria

Every pull request executes the validation pipeline automatically.

---

## TASK-005 — Configuration Framework

### Purpose

Separate engine construction from engine execution.

### Dependencies

TASK-000

### Artifacts Produced

- configuration package
- default configuration
- configuration loader

### Implementation

Initially support:

- loading configuration
- validation
- default values

Keep the implementation intentionally simple.

### Acceptance Criteria

The application can be started entirely from configuration.

---

## TASK-006 — Logging Framework

### Purpose

Provide consistent diagnostic output throughout the engine.

### Dependencies

TASK-000

### Artifacts Produced

- logging configuration
- logger factory

### Implementation

Provide:

- configurable log levels
- consistent formatting
- centralised logging configuration

### Acceptance Criteria

Every subsystem logs through the common logging framework.

---

## TASK-007 — Rendering Framework

### Purpose

Establish the rendering subsystem that will support all future visualisation.

### Dependencies

TASK-000

### Artifacts Produced

- rendering package
- renderer bootstrap
- application window

### Implementation

Rendering library selected: **wgpu/pygfx** (`adr/ADR-005-compute-rendering-instances.md`),
within the Class 2 compute-and-rendering architecture
(`adr/ADR-004-compute-rendering-class.md`). Do not re-litigate this
choice while implementing TASK-007 -- if it proves wrong, that is a new
ADR, not a silent substitution.

Implement:

- window creation
- render loop
- clean shutdown

### Acceptance Criteria

A rendering window opens, updates and closes cleanly.

---

## TASK-008 — Repository Documentation

### Purpose

Establish the repository as the authoritative source of project knowledge.

### Dependencies

None.

### Artifacts Produced

Initial drafts of:

- README
- Handbook
- ADRs
- Capability Map
- Implementation Plan
- Engineering Principles
- Documentation Guidelines
- Practices
- Dreams

### Implementation

Populate every core document with a meaningful first draft.

Avoid placeholder-only documents.

### Acceptance Criteria

Every core document exists and provides sufficient information for future development.

---

## TASK-009 — CLAUDE.md Hierarchy

### Purpose

Provide concise contextual guidance to coding agents throughout the repository.

### Dependencies

TASK-008

### Artifacts Produced

CLAUDE.md files throughout the repository hierarchy.

### Implementation

Create CLAUDE.md files from the repository root downwards.

Each file should:

- inherit parent guidance
- describe the purpose of its subtree
- define local conventions
- reference important local documentation
- avoid duplication
- remain intentionally concise

### Acceptance Criteria

Every actively developed subtree contains an CLAUDE.md file.

Each file provides sufficient local context while remaining compact enough to minimise context-window usage.

---

## TASK-010 — Engine Bootstraps

### Purpose

Validate that the engineering infrastructure functions as a coherent system.

### Dependencies

TASK-002
TASK-005
TASK-006
TASK-007

### Artifacts Produced

- example application
- bootstrap sequence

### Implementation

Create a minimal application that:

- loads configuration
- initialises logging
- opens the rendering window
- enters the application loop
- exits cleanly

No simulation functionality is required.

### Acceptance Criteria

A clean checkout can execute:

make demo

The application starts successfully.

The CI pipeline passes.

All Stage 0 components integrate correctly.

---

## Stage 0 Completion Criteria

This section, together with the task definitions above, **is** the Stage 0
specification. `knowledge-architecture.md` KA-034 originally called for a
separate `docs/implementation/stages/stage-0.md`; that entry was
superseded on 2026-08-15 in favour of this section, and the two
requirements it stated which this section had only implied were folded in
below (criteria 8 and 9). See KA-034 for the full resolution.

The ordered work queue for satisfying these is `docs/planning/backlog.md`
Part I, which maps each criterion below to the items that produce its
evidence. This section defines *what done means*; Part I defines *what to
do about it*.

Stage 0 is complete when:

- Every Stage 0 task satisfies its acceptance criteria.
- All engineering tooling is operational.
- Documentation has a complete first draft. **This means (decided
  2026-08-15): no file tracked in `docs/repository-manifest.md` is
  empty** -- each is either a genuine first draft or has been explicitly
  retired and removed from the manifest. Stated this way so the criterion
  can be checked mechanically rather than argued about. The eleven
  `planning/**.yaml` files are carved out as data rather than
  documentation and keep their existing deferral; see
  `docs/planning/backlog.md` Part II. `assets/`'s manifest row joined this
  carve-out 2026-08-19 (F3 exit audit) on the same terms -- colourmap
  files gated on Stage 1+ field-rendering work (TASK-017), not an
  oversight; writing placeholder content now to force a status change
  would be exactly the speculation E9 already refuses elsewhere.
- Repository structure reflects the intended architecture.
- Coding agents have contextual guidance throughout the repository.
- A developer can clone the repository and begin Stage 1 immediately.
- The engine successfully bootstraps into an empty rendering window.
- **CI executes.** Previously implied by "all engineering tooling is
  operational"; stated explicitly because a pipeline that exists but does
  not run satisfies the looser reading and not this one. From KA-034.
- **Stage 0 infrastructure is reproducible** -- a clean clone reaches a
  working environment through the documented commands, with dependencies
  locked rather than resolved afresh. From KA-034.

### Exit audit (2026-08-19, F3, `docs/planning/backlog.md`)

Checked each of the nine criteria above against direct evidence, not
carried-over status. **Eight of nine fully met at the time this audit
ran; the ninth (criterion 8) closed the same day**, a few hours later,
once a remote existed and a real push proved CI green -- see the note
below criterion 8 and the Status section above for what that took.

1. **Every Stage 0 task satisfies its acceptance criteria.** All 11
   TASK-000..010 rows above read **Done**, TASK-004 included as of the
   same day this audit ran -- see the Status section above and its own
   row for the three real bugs a genuine remote surfaced.
2. **All engineering tooling is operational.** Met -- `uv`, `make`,
   `python` all confirmed working repeatedly this session, most recently
   via a genuinely fresh `git clone` (below).
3. **Documentation has a complete first draft.** Met, with the `assets/`
   carve-out recorded above (2026-08-19) alongside the pre-existing
   `planning/**.yaml` one -- both are content gated on later work, not
   files anyone left empty by oversight.
4. **Repository structure reflects the intended architecture.** Met --
   `src/pyflow/` matches TASK-000's own package list
   (`docs/planning/backlog.md` B1); no open structural divergence
   recorded anywhere.
5. **Coding agents have contextual guidance throughout.** Met -- and
   checked more thoroughly than before this session: F2's inventory
   sweep (2026-08-19) found `.claude/`, a directory with real content
   and zero `CLAUDE.md` coverage that nothing had previously flagged,
   and closed it in the same pass.
6. **A developer can clone the repository and begin Stage 1 immediately.**
   Met -- verified for real this session, not just asserted: a fresh
   `git clone` into an empty directory, then `make install` and `make
   ci`, both succeeded end to end (64 tests passing), and `pyflow run`
   opened a real render window from that clone. Stronger evidence than
   B2's original verification, which was a `make clean`/`make install`
   cycle in place, not an actual clone.
7. **The engine successfully bootstraps into an empty rendering window.**
   Met -- D4/D5, reconfirmed in the same fresh-clone test as criterion 6.
8. **CI executes.** **Met, closed 2026-08-19, a few hours after this
   audit's initial pass.** A remote was created and pushed to the same
   day; the first real CI runs found three genuine bugs `make ci` alone
   had never exercised (a flaky apt mirror hanging Ubuntu's runner
   indefinitely, a native `SIGABRT` in the interactive-display probe
   that no Python `except` could catch, and a platform-dependent sort
   in the docs-index generator), each diagnosed from a real log rather
   than guessed at, fixed, and confirmed by a subsequent green run
   before being called fixed. Verified directly: the push that merged
   the final fix (`9c66e25`) is green on both `ubuntu-latest` and
   `windows-latest`, checked against the run itself via the GitHub API,
   not inferred from the PR merging cleanly.
9. **Stage 0 infrastructure is reproducible.** Met -- same fresh-clone
   evidence as criterion 6: `uv.lock` resolved the exact locked versions,
   no network resolution surprises, dependencies locked rather than
   resolved afresh.

**Net result: Stage 0 is complete.** Criterion 8 was the one open item
this audit found, with an already-deliberate, already-stated trigger
condition (a remote existing) -- it closed for real the same day, and
the three bugs that surfaced closing it are exactly the kind of thing
`make ci` passing locally could never have caught, which is the entire
reason criterion 8 was worth stating separately from criterion 2 in the
first place.

---

# Stage 1 — Representing Space

Goal

Represent the simulation domain.

### Completion Criteria

Written 2026-08-21, after the fact. Stage 1 had no completion criteria
and no exit audit -- it was worked task by task, each closed against its
own Acceptance Criteria, and then simply stopped. Stage 0 had nine
criteria and a per-criterion audit; nothing anywhere recorded that
Stage 1 was finished at all, so a fresh agent reading this repository
could not have told. That is a direct failure of P-001 (knowledge should
never depend upon individual memory), and writing these criteria
retrospectively is the smaller half of the fix -- the larger half is
that **every stage from here gets its criteria written when the stage
opens, before its first task**, recorded as a standing rule in
`docs/practices.md`.

Criteria are deliberately about the stage's *goal* ("represent the
simulation domain"), not a restatement of the three tasks' own
Acceptance Criteria. A stage whose criteria are just the union of its
tasks' criteria cannot fail an audit that its tasks passed, which makes
the audit worthless -- and this one did find something.

1. **The domain is representable at two layers, with the lower one
   usable on its own.** A `CoordinateSystem` (index to physical position)
   exists independently of a `Mesh` (cells, faces, adjacency,
   boundaries), so that a future mesh type reuses the coordinate layer
   rather than reimplementing it.
2. **Both layers are interfaces with at least one concrete
   implementation behind them, and a shared contract suite that any
   second implementation must pass unchanged.** The contract suite is
   the criterion, not the implementation count: an interface with one
   implementation and no contract suite has not actually been shown to
   be an interface.
3. **The MVP mesh is geometrically correct, not merely plausible.**
   2D structured Cartesian, uniform spacing (`docs/implementation/
   mvp.md`), satisfying discrete geometric closure -- for every cell, the
   sum of `face_area * outward_normal` over its faces is zero. Stage 4+
   flux conservation silently depends on this.
4. **The domain is constructible entirely from configuration.**
   `PyFlowConfig` alone determines the mesh; no bespoke Python is needed
   to build one.
5. **Stage 1 has a working, visible demonstration** (P-004), runnable by
   a user through the public CLI, and regression-tested through that same
   CLI rather than through internal calls.
6. **The demonstration is interactive.** Zoom and pan work in a real
   window, verified against a real display rather than by inspection.
7. **`make ci` passes on both CI platforms**, on a real runner, not only
   locally.
8. **The documentation describes what now exists**: the architecture
   Mesh contract points at real code, every touched `CLAUDE.md` carries
   the implementation notes, and the inventories match the tree.

### Status as of 2026-08-21: Stage 1 complete, eight of eight criteria met

Met, but not on the day the code was written. Five of the eight --
criteria 3, 4, 5, 6 and 8 -- failed when this audit was actually run on
2026-08-21, five days after the last Stage 1 commit, and were closed by
the two branches that audit produced. Recorded that way rather than as a
clean pass, because the useful part of an exit audit is what it catches,
and because a stage that needed five of eight criteria repaired after
being treated as finished is the strongest available argument for
writing the criteria *before* the stage rather than after it.

| Criterion | Verdict |
|-----------|---------|
| 1. Two layers, lower usable alone | **Met.** `src/pyflow/engine/coordinate_system.py` and `mesh.py`. `StructuredCartesianMesh` owns a `UniformVertexCoordinateSystem` rather than reimplementing the mapping; `spacing` has one source of truth. |
| 2. Interfaces with contract suites | **Met.** `tests/unit/test_coordinate_system_contract.py` and `test_mesh_contract.py` are both parametrised over an implementation list, so a second implementation joins by adding a factory, not by writing tests. Each layer also has an implementation-specific suite for claims the contract must *not* assert. |
| 3. Geometrically correct, not merely plausible | **Met, after a fix.** `test_geometric_closure` passed from the day it was written. But no accessor validated its cell or face id, so `face_neighbours(9999)` on a six-cell mesh returned cells 3330 and 3333 rather than raising -- correct geometry reachable only through ids that happened to be valid. Closed 2026-08-21 by `InvalidMeshEntityError` and a contract-suite criterion for it. |
| 4. Constructible from configuration | **Met, after a fix.** `MeshConfig` and `StructuredCartesianMesh.from_config` did the job, but `extent: [10.9, 3.99]` was silently truncated to `(10, 3)` -- a user could configure a mesh and get a different one, with nothing printed. Fixed the same day. |
| 5. Working demonstration via the public CLI | **Met, after a fix.** `examples/golden-demos/empty_mesh.yaml` and `tests/golden/test_empty_mesh.py` were correct throughout. The criterion is nonetheless recorded as fixed because asking for the mesh required naming a grid colour: the demo was reachable, but "show the mesh" was not expressible on its own. `rendering.show_mesh` now is. |
| 6. Interactive, verified against a real display | **Met, after a fix, and this is the one worth reading.** Zoom and pan were both wired up and both covered by tests that ran against a real display. Pan was nevertheless wrong: it moved the camera 1.78x too little horizontally in the shipped default configuration, because pygfx's `maintain_aspect` makes the visible extent larger than `camera.width`. The unit test that would have caught it used a 4:3 camera on a 4:3 canvas -- the single aspect ratio at which the bug is invisible. See `docs/CHANGELOG-DESIGN.md` (2026-08-21). |
| 7. `make ci` green on a real runner | **Met.** The merge of PR #6 into `main` (`0c136f2`, 2026-08-20) is green on both `ubuntu-latest` and `windows-latest` -- checked against the actual run via `gh run list`, not inferred from the PR having merged. |
| 8. Documentation matches the tree | **Not met on 2026-08-20; met 2026-08-21.** `docs/architecture/engine.md` and every `CLAUDE.md` were accurate. The inventories were not: `docs/repository-manifest.md` still described `src/` as "six `__init__.py`/`__main__.py` files, docstring-only, no implementation" and the test suite as "42 tests, 87% coverage" (actually 160 at 99%), and `README.md` still told a reader the project was in Stage 0 with no simulation code written. All corrected in the same pass that wrote this table. |

**What this stage should hand forward.** Two process failures, both
already turned into rules rather than left as observations:

- **A stage with no exit criteria cannot be audited, and will not be.**
  Stage 1's three tasks each passed their own criteria, and three of the
  four defects found on 2026-08-21 sat squarely inside code those
  criteria covered -- because task criteria describe what a component
  does when used correctly, and nothing was asking what the stage as a
  whole guaranteed. `docs/practices.md` now requires a stage's criteria
  before its first task.
- **A test whose fixture makes two formulas agree is not evidence.** The
  pan bug and the missing id validation both had passing tests over
  them. `docs/practices.md` carries the general form of this.

---

## TASK-011 — Coordinate System

**Status: Done, 2026-08-20.** `src/pyflow/engine/coordinate_system.py`
implements `CoordinateSystem` and `UniformVertexCoordinateSystem`
exactly as specified below; both test suites named in the Acceptance
Criteria exist and pass (`tests/unit/test_coordinate_system_contract.py`,
`tests/unit/test_uniform_vertex_coordinate_system.py`), `make ci` is
clean, and coverage on the new module is 100%. See
`src/pyflow/engine/CLAUDE.md` for implementation notes, including one
process deviation worth stating plainly rather than glossing over: the
interface and implementation were drafted a beat ahead of their tests
rather than strictly after, diverging from this file's own TDD rule
below -- the tests were still written and verified in the same session
before this status line was written, so nothing here is unverified, but
the ordering itself wasn't red-then-green as the rule asks.

**Amended 2026-08-21 (repository audit).** The named exception this
task's Acceptance Criteria require is now `OffGridCoordinateError`,
renamed from `CoordinateOutOfBoundsError`. The criterion below asks for
"out-of-bounds handling"; that phrasing described a condition this layer
does not have. A `CoordinateSystem` has no extent -- every integer index
is valid, and bounds are `Mesh`'s concern (TASK-012, whose own
`InvalidMeshEntityError` covers them as of the same audit). What
`to_index` actually rejects is a coordinate lying *between* grid points.
The criterion itself is unchanged in substance and still met: a named
exception, honoured identically by every implementation. Read
"out-of-bounds handling" below as "off-grid handling".

### Purpose

Establish the mapping between a grid index and a physical position --
the layer beneath the `Mesh` layer itself (`docs/architecture/engine.md`):
no cells, no neighbours, no boundaries yet (TASK-012), just coordinates.
`docs/handbook/numerical-methods/meshes.md`'s Geometry section computes
cell centroids *from* a mesh's vertex coordinates, not the reverse --
this is that vertex layer.

### Dependencies

None.

### Design decision, recorded here (maintainer's call, 2026-08-19)

**The interface must not assume uniform spacing or vertex placement --
those are properties of the first concrete implementation, not the
contract.** `docs/implementation/upgrade-paths.md`'s Mesh path already
commits to adaptive refinement eventually, and the project wants
cell-center placement configurable alongside vertex placement, not
bolted on later by breaking the interface. Same pattern already proven
in this codebase: `src/pyflow/rendering/canvas.py`'s `create_canvas`
selects a concrete canvas behind `rendercanvas.base.BaseRenderCanvas`,
per `adr/ADR-003-modular-numerical-strategies.md`'s standing commitment
to interfaces-first, swappable-implementations-behind-them. Applied here
for the first time to a component PyFlow owns outright (no third-party
base class to borrow), so this task defines its own `CoordinateSystem`
interface rather than reusing someone else's.

### Artifacts Produced

- `CoordinateSystem` interface (`src/pyflow/engine/`) -- index-to-physical
  and physical-to-index conversion, nothing else. No method or property
  implies constant spacing or a specific placement convention.
- A shared, implementation-independent **contract test suite**: written
  once, run against every `CoordinateSystem` implementation that exists
  now or is added later, asserting only what must hold regardless of
  implementation (below).
- `UniformVertexCoordinateSystem`, the first concrete implementation:
  vertex-based, uniform spacing, matching MVP (`docs/implementation/mvp.md`:
  2D, structured Cartesian, uniform grid spacing).
- Implementation-specific tests for `UniformVertexCoordinateSystem` --
  every concrete implementation gets its own, in addition to passing the
  shared contract suite; passing the contract suite alone is necessary
  but not sufficient; it does not prove an implementation's *own*
  specific claims (exact formulas, its own error conditions).

### Implementation

Test-driven (`docs/practices.md`): write the contract suite and
`UniformVertexCoordinateSystem`'s own tests before the code they check,
red before green.

1. Define `CoordinateSystem` as the interface every implementation
   satisfies.
2. Write the contract test suite against that interface, parametrised
   so a future implementation is added by adding it to the
   parametrisation, not by writing new contract tests.
3. Implement `UniformVertexCoordinateSystem`, constructed from an origin
   `(x0, y0)` and uniform spacing `(dx, dy)`, satisfying the contract
   suite plus its own implementation-specific tests.

**Deliberately not built now, planned for later:** a cell-center-based
implementation, added as its own task once something in Stage 1+
actually needs it, following `src/pyflow/rendering/CLAUDE.md`'s own
reasoning for not building a third canvas backend ahead of a real
consumer. When it lands, it must pass the same contract suite unchanged
-- if it can't, that is a signal the contract was wrong, not that the
new implementation is.

### Acceptance Criteria

**Contract suite (implementation-independent -- must pass for every
`CoordinateSystem`):**

- Round-trip: `to_index(to_physical(i, j)) == (i, j)` for every valid
  `(i, j)`, not just a sampled few.
- Monotonicity: increasing `i` never decreases the physical
  x-coordinate (and equivalently for `j`/y) -- holds under uniform
  *and* non-uniform spacing, so it stays valid once a second
  implementation exists.
- Out-of-bounds handling is explicit and consistent: a named exception
  or a documented sentinel, whichever the interface commits to, honoured
  identically by every implementation.

**`UniformVertexCoordinateSystem`-specific:**

- `to_physical(i, j) == (x0 + i*dx, y0 + j*dy)` exactly, for at least
  `i, j` in `{0, 1, -1, a large value}`.
- The physical distance between adjacent indices equals `dx`/`dy`
  exactly, checked at more than one location in the grid (proves
  *uniform*, not just correct at one point) -- an invariant of this
  implementation specifically, not asserted anywhere in the contract
  suite.
- Constructing with `dx <= 0` or `dy <= 0` raises a specific, named
  exception.

---

## TASK-012

Structured Cartesian Mesh

**Status: Done, 2026-08-20.** `src/pyflow/engine/mesh.py` implements
`Mesh` and `StructuredCartesianMesh` exactly as specified in this task's
Acceptance Criteria below; both test suites named there exist and pass
(`tests/unit/test_mesh_contract.py`,
`tests/unit/test_structured_cartesian_mesh.py`), `MeshConfig` exists in
`src/pyflow/configuration/schema.py` following `RenderingConfig`'s
pattern, `make ci` is clean, and coverage on the new module is 100%. See
`src/pyflow/engine/CLAUDE.md` for implementation notes. Unlike TASK-011,
this one followed strict TDD throughout -- every test in both suites was
written and confirmed to fail for the right reason (missing
module/class) before any implementation code existed.

**Amended 2026-08-21 (repository audit).** Every `Mesh` accessor now
rejects an out-of-range cell or face id with `InvalidMeshEntityError`
(an `IndexError` subclass), and the contract suite asserts it for every
implementation. This closes a gap the original Acceptance Criteria below
did not state: they specify what each accessor returns for a *valid* id
and say nothing about an invalid one, so the implementation returned a
plausible wrong answer rather than raising -- `face_neighbours(9999)` on
a six-cell mesh named cells 3330 and 3333. That is precisely the failure
mode "Geometric closure" below exists to keep out of the numerics, and
it is the shape of error Stage 3's operator loops (TASK-018) will
produce when index arithmetic goes wrong. Treat "every accessor rejects
an id outside its range" as an additional contract-suite criterion.

Implement

- Uniform Cartesian grid
- Cell indexing
- Neighbour lookup
- Boundary identification

**Two design decisions carried forward from TASK-011 (maintainer's call,
2026-08-20):**

1. **Same interface-first pattern as `CoordinateSystem`.** A `Mesh`
   interface, deliberately not assuming structured-vs-unstructured any
   more than TASK-011's interface assumed vertex-vs-cell-center --
   matching `docs/architecture/engine.md`'s own Mesh contract ("exposes
   cell geometry, adjacency/neighbour lookup, and boundary
   identification, independent of whether the mesh is structured or
   unstructured") and `upgrade-paths.md`'s Mesh path (structured 2D →
   structured 3D → unstructured → ...). `StructuredCartesianMesh` is the
   first concrete implementation; a shared, implementation-independent
   contract test suite covers what every `Mesh` must satisfy, the same
   shape as TASK-011's. Note this is an *internal engineering pattern*,
   distinct from `docs/architecture/icds.md`'s formal ICD documents --
   `icds.md` explicitly scopes ICDs to `ADR-003`'s six named components
   only, and that scope is unchanged; Mesh still doesn't get a formal
   ICD, it just gets built with the same swappable-implementation
   discipline internally.
2. **Mesh must become configurable via the public schema** (origin,
   spacing, extent) as part of this task's own acceptance criteria, not
   deferred to TASK-013. TASK-013's golden demo ("display an empty
   computational mesh") must run entirely through the public
   `pyflow run --config <file>` CLI with no bespoke code
   (`docs/implementation/golden-demos.md`'s Definition of Done) --
   exactly the reason `RenderingConfig.background_color` exists, added
   specifically so Empty Window could be configuration-only. Without a
   mesh configuration section, TASK-013 cannot be built without
   demo-specific code.

Depends on

TASK-011

### Acceptance Criteria

**Contract suite (implementation-independent -- must pass for every
`Mesh`):**

- Every cell has a well-defined volume (area, in 2D) and centroid,
  computed from the mesh's vertex coordinates
  (`docs/handbook/numerical-methods/meshes.md`'s Geometry section) --
  never asserted directly.
- Every face has an area (length, in 2D) and an outward-pointing normal.
- Neighbour connectivity is symmetric: if cell A names cell B as its
  neighbour across face F, cell B names A across that same F -- checked
  for every interior face, not sampled.
- Boundary identification is exhaustive and exclusive: every face is
  classified as exactly one of {interior, boundary}; every interior face
  has exactly two owning cells, every boundary face exactly one.
- **Geometric closure:** for every cell, the sum of `face_area *
  outward_normal` over all its faces is the zero vector (within
  floating-point tolerance) -- the discrete Gauss/divergence-theorem
  check every real mesh-validity tool runs (OpenFOAM's `checkMesh` calls
  this "closed cells"). Stated now under the physical-correctness
  extension to the acceptance-criteria rule (`docs/practices.md`): this
  is the geometric precondition every later flux-conservation check
  (Stage 4+) silently depends on -- cheaper to catch a broken mesh here
  than to misdiagnose a conservation failure two stages later as a flux-
  scheme bug.

**`StructuredCartesianMesh`-specific:**

- Cell `(i, j)`'s volume/area equals `dx * dy` exactly, for every cell
  (uniform mesh).
- Cell `(i, j)`'s centroid equals the average of its four corner
  vertices as given by the configured `CoordinateSystem` (TASK-011) --
  not computed independently of it.
- Face areas equal `dx` (north/south faces) or `dy` (east/west faces)
  exactly.
- Neighbour lookup is index arithmetic: cell `(i, j)`'s neighbours are
  exactly `(i±1, j)` and `(i, j±1)`, restricted to those that exist.
- Boundary faces are exactly those on the domain edge (`i = 0`, `i =
  nx-1`, `j = 0`, `j = ny-1`); every other face is interior.
- Constructing with `nx <= 0` or `ny <= 0` raises a specific, named
  exception (mirrors TASK-011's `dx <= 0`/`dy <= 0` check).

**Configuration (public schema)** -- from this task's own design
decision 2, above:

- A `MeshConfig` section exists in `PyFlowConfig`, following
  `RenderingConfig`'s established pattern
  (`src/pyflow/configuration/schema.py`): origin, spacing, extent, all
  defaulted so `PyFlowConfig()` alone stays valid.
- Invalid values (`nx <= 0`, `dx <= 0`, etc.) raise via
  `MeshConfig.validate()`, the same mechanism `RenderingConfig` already
  uses.
- A `StructuredCartesianMesh` is fully constructible from a
  `PyFlowConfig` alone -- no bespoke code -- since TASK-013's golden demo
  must run entirely through `pyflow run --config <file>`.

**Knock-on notes for later stages, not acted on here:** the geometric-
closure check above becomes the thing Stage 4/5's flux-conservation
checks build on -- worth a forward pointer from `docs/planning/
backlog.md`'s "physical correctness validation" item once that's
revisited. And TASK-018 (Stage 3, Operator Interfaces) will consume
whatever face/neighbour/boundary method names get decided when this task
is implemented -- those names become load-bearing the moment Stage 3 is
drafted, so worth getting them right now rather than renaming later.

---

## TASK-013

Mesh Visualiser

**Status: Done, 2026-08-20.** `src/pyflow/rendering/mesh_visualization.py`
(`build_mesh_grid_line`, `fit_camera_to_mesh`) and `RenderWindow`'s new
camera controls (`apply_camera_config`, live wheel-zoom/pointer-drag-pan)
implement this task's Acceptance Criteria in full, wired together by
`bootstrap.py`. Golden demo: `examples/golden-demos/empty_mesh.yaml`,
`tests/golden/test_empty_mesh.py`. `make ci` is clean; the two
live-interactivity tests
(`tests/integration/test_interactive_window.py::test_wheel_event_zooms_the_camera_live`,
`::test_pointer_drag_pans_the_camera_live`) need a real display and are
skipped on headless CI, same as every other test in that file. See
`src/pyflow/rendering/CLAUDE.md` for implementation notes, including one
new interface decision this task made concrete: `Mesh.face_vertices`,
deferred as "not built yet" when TASK-012 closed, added here once this
task was the real consumer that needed it
(`src/pyflow/engine/CLAUDE.md`).

**Amended 2026-08-21 (repository audit), two corrections:**

1. **Drag-panning did not actually track the cursor.** The criterion
   below asks for pan "proportional to zoom"; the implementation divided
   `camera.width` by zoom and by the viewport width, which is only the
   right scale when the camera's aspect ratio matches the canvas's.
   pygfx's `maintain_aspect` (on by default, and what stops the mesh
   being stretched) expands whichever axis is narrower than the
   viewport, so the visible extent is larger than `camera.width` says.
   In the shipped default -- a square mesh framed in a 1280x720 window
   -- horizontal panning moved the camera 1.78x too little. Fixed with
   `rendering.window.visible_world_size`. The single unit test covering
   pan used a 4:3 camera on a 4:3 canvas, the one configuration where
   the bug cannot appear; there is now a deliberately mismatched-aspect
   test beside it. Worth generalising: an acceptance criterion phrased
   as a proportionality ("proportional to zoom") is satisfied by any
   constant multiple of the right answer, so it needs a test that pins
   the constant, not just the trend.
2. **`grid-line visibility` and grid-line *colour* were the same
   field.** The criterion below already names them separately -- "zoom,
   pan, and grid-line visibility" -- but the implementation used
   `grid_color is not None` as the visibility switch, so the mesh could
   not be shown in the default colour and a colour could not be recorded
   without switching the mesh on. `rendering.show_mesh` is now the
   switch; `grid_color` is only a colour.

Implement

- Draw grid
- Display cell boundaries
- Zoom
- Pan

Depends on

TASK-012

Golden Demo

Display an empty computational mesh.

**Criteria retrofitted to a feature file 2026-08-22.** The prose
Acceptance Criteria above are left exactly as written -- they are what
this task was closed against, and rewriting a closed record is the
opposite of an institutional memory. But the demo's own criteria now
also exist executably as `tests/features/empty_mesh.feature`, which
`tests/golden/test_empty_mesh.py` binds. The retrofit was done on the
three existing demos deliberately, so
`adr/ADR-007-executable-acceptance-criteria.md`'s mechanism was proven
on work that already existed rather than first attempted on unbuilt
physics.

### Acceptance Criteria

**Rendering correctness:**

- Given a `StructuredCartesianMesh` of known extent/spacing, the rendered
  frame contains a visible line at every internal cell boundary and every
  domain edge -- checked by pixel inspection via `bootstrap()`'s
  `last_image`, the same mechanism
  `test_empty_window_renders_configured_background` already uses, not
  just "the demo ran."
- For a fixed, deterministic camera/viewport, the number and
  pixel-position of rendered grid lines matches what the mesh's `(nx,
  ny)`/`(dx, dy)` predict exactly, for at least one small, hand-checkable
  mesh (e.g. 4x3 cells) -- not "some lines appear somewhere."
- Grid lines are visually distinguishable from the background colour by a
  fixed minimum pixel-value contrast, so the two checks above can't pass
  vacuously against a background that happens to match.

**Zoom -- configured initial state:**

- `PyFlowConfig` sets the starting zoom level; increasing it strictly
  increases on-screen pixel spacing between adjacent grid lines for a
  fixed viewport -- checked by comparing rendered frames from two
  separately-configured runs (works headless, feeds the golden-demo
  regression test).
- Zoom is a view transform only: `Mesh` (TASK-012) returns identical cell
  geometry regardless of zoom.

**Zoom -- live, interactive:**

- Scrolling the mouse wheel while the window is running changes zoom
  live, via `canvas.add_event_handler` -- the same mechanism `close_keys`
  (`src/pyflow/rendering/window.py`) already uses (rendercanvas `wheel`
  events), not a new one. Verified the same way
  `test_interactive_window.py`'s close-key test verifies keyboard input:
  inject a synthetic wheel event into a genuinely blocking `run()` via
  `canvas.submit_event`, then assert the rendered frame's grid-line
  spacing changed.
- Live zoom is bounded by a configured min/max, so scrolling indefinitely
  can't zoom into numerical degeneracy (grid lines collapsing to
  sub-pixel spacing) or out to nothing rendering -- an explicit boundary
  case, matching TASK-011's precedent of naming boundary handling
  explicitly rather than leaving it implicit.

**Pan -- configured initial state:**

- `PyFlowConfig` sets the starting pan offset; the rendered grid shifts
  by the corresponding pixel amount (proportional to zoom), same
  config-comparison test technique as zoom's initial state.
- Panning far enough that the configured mesh starts outside the viewport
  renders an empty, background-only frame -- not an error.

**Pan -- live, interactive:**

- Pointer-down + pointer-move + pointer-up while running pans the view
  live, same `add_event_handler`/`submit_event` test technique as live
  zoom.
- A given drag distance in screen pixels pans by more world-space
  distance at low zoom than at high zoom -- i.e. pan tracks the pointer
  under the cursor, not a fixed world-space amount per pixel dragged.
  Concrete, testable property, not just "feels right."

**Test-boundary note, stated explicitly:** live interactivity needs a
real event loop, so it's only exercisable on the interactive backend --
it gets its own `tests/integration/` test (skipped where no display
exists, exactly `test_interactive_window.py`'s existing pattern),
separate from the config-driven golden-demo regression test, which stays
headless/offscreen per `docs/implementation/golden-demos.md`.

**Configuration (public schema) and golden demo:**

- Mesh visualisation is controllable entirely through `PyFlowConfig` --
  `MeshConfig` (TASK-012) plus whatever new fields zoom, pan, and
  grid-line visibility need -- no bespoke code.
- The golden demo ("display an empty computational mesh") is a config
  file under `examples/golden-demos/`, run via `pyflow run --config
  <file> --backend offscreen`, following `empty_window.yaml`'s precedent
  exactly: a subprocess test through the real CLI, a `bootstrap()`-based
  pixel test proving the grid actually rendered, and a determinism test
  (two runs produce identical frames) -- `tests/golden/
  test_empty_window.py`'s own three-test shape.

**Not applicable here, stated so its absence isn't mistaken for an
oversight:** the physical-correctness extension to the acceptance-
criteria rule applies to physics-implementing tasks; TASK-013 is pure
rendering, so it carries none.

**Knock-on note:** TASK-017 (Field Rendering) layers scalar colour maps
and vector arrows onto this same rendering path -- it should reuse this
task's zoom/pan configuration and live-interaction mechanism rather than
reinvent them.

---

# Stage 2 — Representing Fields

Goal

Represent physical quantities.

### Completion Criteria

Written 2026-08-21, before TASK-014 starts, per `docs/practices.md`'s
"A stage gets completion criteria before its first task" -- the rule
this project adopted after Stage 1 closed without any and a retrospective
audit found five of its eight criteria unmet. That rule requires these
to describe what Stage 2 as a whole guarantees, not the union of
TASK-014..017's own Acceptance Criteria -- a checklist assembled from
task criteria cannot fail an audit that the tasks already passed, which
is exactly why Stage 1's went unexamined for five days.

1. **Fields exist at an interface layer, with mesh association intrinsic
   rather than tracked alongside them.** A `Field` interface
   (`docs/architecture/engine.md`'s Variables contract) makes no
   assumption about arrangement -- collocated now, staggered later
   (`docs/implementation/upgrade-paths.md`) -- and every field carries
   the mesh it belongs to as part of what it *is*, not as a value some
   other piece of code must remember to pass alongside it.
2. **The interface has concrete implementations for both scalar and
   vector data, and a shared, implementation-independent contract test
   suite that any future implementation (e.g. a staggered placement)
   must pass unchanged** -- the same discipline TASK-011/012 already
   established for `CoordinateSystem` and `Mesh`. The contract suite is
   the criterion; an implementation with no contract suite has not been
   shown to satisfy an interface, only to exist.
3. **A field's storage is never independently sizeable from the mesh it
   claims to belong to.** Constructing a field ties its storage shape to
   its mesh's cell count by construction, not by a value that happens to
   agree during testing -- a mismatch (a field sized for one mesh handed
   to operators over another) is exactly the kind of confident-wrong-
   answer failure `InvalidMeshEntityError` was added to `Mesh` to catch
   at this same layer of the stack (`docs/planning/roadmap.md` TASK-012
   amendment, 2026-08-21).
4. **Initialisation is expressive enough for physics this stage does not
   yet implement, not only a uniform constant.** Decided already
   (TASK-015, 2026-08-20): general callable/expression-based
   initialisation from a cell's position, because Taylor-Green vortex,
   Poiseuille flow, Kelvin-Helmholtz and Rayleigh-Bénard all need a
   field set to a specific non-uniform function and none of them is
   nameable as a fixed preset today. A criterion here, not just a task
   note, because it is exactly the kind of gap that is cheap to build in
   now and expensive to retrofit once Stage 6's demos depend on fields
   already existing.
5. **Field data is read, written, copied and (for vector fields)
   accessed per-component and by magnitude entirely through the
   `Field`/subclass API, with no caller reaching into backing storage
   directly.** This is not fastidiousness: Stage 3's operator interfaces
   (TASK-018) will be written against whatever access surface this stage
   settles on, and every name and shape decided here becomes load-bearing
   the moment that task is drafted -- the same warning already recorded
   for `Mesh`'s own accessor names under TASK-012.
6. **Fields are visible, not only held in memory.** A user can configure
   a scalar field and a vector field and see both rendered -- colour map,
   arrows, legend -- reusing TASK-013's existing zoom/pan/live-interaction
   path rather than a second one built alongside it.
7. **Field visualisation is reachable entirely through configuration,
   per the public-API rule** (`docs/implementation/golden-demos.md`).
   The golden demo ("display scalar and vector fields") is a config file
   under `examples/golden-demos/`, run via `pyflow run --config <file>`,
   with the same three-test shape Empty Mesh established: a subprocess
   CLI test, a pixel-level rendering-correctness test, and a determinism
   test.
8. **`make ci` passes on both CI platforms, on a real runner** -- not
   only locally, matching Stage 0/1's own standard of evidence.
9. **Documentation describes what now exists.** `docs/architecture/
   engine.md`'s Variables entry, every touched `CLAUDE.md`, and both
   inventories (`docs/repository-manifest.md`,
   `docs/repository-inventory.md`) checked directly against the current
   tree, not assumed current because they were correct when written --
   the specific failure Stage 1's own audit found on this exact point.

**Not applicable here, stated so its absence isn't mistaken for an
oversight:** the physical-correctness acceptance-criteria extension
(`docs/practices.md`) applies to tasks that compute a physical result
and can be checked against a known answer. Nothing in Stage 2 solves an
equation -- it stores and displays data an equation will later act on --
so it carries none, the same carve-out TASK-013 stated for itself as
pure rendering.

### Status as of 2026-08-22: Stage 2 complete, nine of nine criteria met

Six passed as written. Three -- criteria 1, 2 and 9 -- did not, when the
exit audit was actually run on 2026-08-22, a day after the last Stage 2
commit, and were closed by the branch that audit produced. Recorded that
way rather than as a clean pass, for the reason Stage 1's table already
gives: the useful part of an exit audit is what it catches.

**This is the first stage whose criteria were written before its first
task**, which is the rule Stage 1's own audit produced, and it worked
roughly as intended. The three findings are worth separating on that
point.

- **Criterion 9** (documentation) failed the same way Stage 1's did --
  drift nobody was looking at. Writing criteria early does not, on its
  own, make anyone re-read them at the end.
- **Criterion 1** was satisfied where it was written and undone one
  layer up: fields carried their mesh, and the rendering functions
  consuming them took a mesh alongside anyway. A criterion about an
  interface is not automatically a criterion about its callers, and
  this one had to be read as though it were.
- **Criterion 2** is the interesting one. It failed because the
  criterion was **more demanding than the task criteria written under
  it** -- which is exactly what a stage criterion is for, and exactly
  what Stage 1's table said a union-of-tasks checklist could never do.
  No per-task audit could have found it, because every task passed its
  own.

| Criterion | Verdict |
|-----------|---------|
| 1. Fields at an interface layer, mesh association intrinsic | **Met, after a fix.** `Field.mesh` is set at construction and has no setter (`src/pyflow/engine/field.py`). But the rendering layer partly undid it: `build_scalar_field_mesh(mesh, colors)` and `build_vector_field_arrows(field, mesh, ...)` both took a mesh *alongside* the field, so an arrow's tail (`mesh.cell_centroid`) and its direction (`field.value_at`) came from two references nothing checked were the same one -- the "value some other piece of code must remember to pass alongside it" this criterion exists to eliminate, reintroduced one layer up. Both now read `field.mesh`; `build_scalar_field_mesh` takes the field, not the mesh. Fixed 2026-08-22 rather than left for TASK-018, because criterion 5 warns that this exact surface becomes load-bearing the moment Stage 3's operators are drafted against it. |
| 2. Interfaces with a contract suite a future implementation passes unchanged | **Not met on 2026-08-21; met 2026-08-22.** There was one contract suite, `tests/unit/test_field_contract.py`, and it was a `CollocatedField` suite: typed `list[type[CollocatedField[Any]]]`, asserting `values.shape == (num_cells, *component_shape)`. A staggered placement -- the criterion's own named example, and the reason `Field` carries no storage at all -- could never have passed it. So the collocated assumption `field.py`'s docstring says "cannot live on an interface both are meant to satisfy" was the one thing the only contract suite required. That suite is now `tests/unit/test_collocated_field_contract.py`, correctly named, and `tests/unit/test_field_contract.py` is a real `Field`-level suite: parametrised over factories, asserting only mesh association, name, and copy independence. A collocated implementation passes both; an alternative placement passes the first alone. |
| 3. Storage never independently sizeable from the mesh | **Met.** `CollocatedField.__init__` allocates `(mesh.num_cells, *component_shape)` itself and nothing can override the leading dimension. Checked against two differently-sized meshes, so a hardcoded constant cannot pass by coincidence. |
| 4. Initialisation expressive beyond a uniform constant | **Met.** Any `(x, y) -> value` callable, evaluated once per cell at that cell's centroid; the constant case is the degenerate form, not a second code path. The contract suite checks it with a function that reads both axes with different coefficients, so a bug reading one axis, swapping them, or ignoring the callable fails visibly. |
| 5. Data accessed entirely through the `Field` API | **Met.** `values`, `value_at`/`set_value_at`, `copy`, and -- for vectors -- `component(index)` and `magnitude()`. TASK-016 put `magnitude()` on `VectorField` specifically so TASK-017 would not reach into `values` to compute it, and TASK-017 didn't. One thing to know rather than to fix: `values` returns the live backing tensor, not a copy, so a caller *can* write through it and bypass `set_value_at`'s id checking. That is deliberate -- Stage 3's operators will want the whole tensor -- and it is the reason the id-checked accessors exist alongside it rather than instead of it. |
| 6. Fields visible, reusing TASK-013's interaction path | **Met.** `bootstrap.py` adds the field geometry to the same `RenderWindow.scene`, frames it with `fit_camera_to_bounds` (factored out of TASK-013's `fit_camera_to_mesh` precisely so the legend could widen the framed box), then runs the same `apply_camera_config`/zoom/pan path unchanged. No second camera, no second window. |
| 7. Reachable entirely through configuration, three-test demo shape | **Met.** `examples/golden-demos/field_display.yaml` plus `tests/golden/test_field_display.py`: a real subprocess CLI test, a per-cell pixel-position test for all nine cells of a hand-checkable 3x3 mesh, and a determinism test. Stronger than Empty Mesh's own pixel check, which only asserts a colour exists somewhere. |
| 8. `make ci` green on both platforms, on a real runner | **Met.** Run `32535101217` (the merge of PR #15 into `main`, `437c3aa`) is green on both `ubuntu-latest` and `windows-latest` -- checked against the actual run via `gh run list`/`gh run view`, not inferred from the PR having merged, the same standard Stage 1 set. |
| 9. Documentation describes what now exists | **Not met on 2026-08-21; met 2026-08-22.** Six separate drifts, all passing `make ci` cleanly: `docs/architecture/engine.md`'s Variables entry still said "**Arrives via:** Stage 2", against that same document's own Maintenance rule that it should read "implemented in" the moment the task lands; the Field Display golden demo existed in code but on no planning surface at all (no entry in `docs/implementation/golden-demos.md`, no row in `implementation-plan.md`'s Golden Demos table, no entity in `planning/data/demos.yaml`, whose header still said "two demos exist"); `README.md` said the project "is beginning Stage 2" and offered `empty_mesh.yaml` as the most recent demo; `docs/architecture/rendering.md` said "there is no field data flowing through it yet"; `docs/architecture/CLAUDE.md` and `docs/repository-manifest.md` both still described Mesh and Variables as layers that "don't exist as code yet"; and two roadmap test counts (TASK-016's "32", TASK-039's "260") were simply wrong against a real run. All corrected in the same pass that wrote this table. |

**What this stage should hand forward.**

- **A criterion can be wrong in the direction of being too weak to
  fail.** Criterion 2 said "contract test suite" and a contract test
  suite existed, which is why nothing noticed. What made it findable was
  reading the criterion's own parenthetical -- "(e.g. a staggered
  placement)" -- as a testable claim and asking whether such a thing
  could actually pass. **When auditing a criterion, audit its example,
  not just its headline**; the example is usually the part that says
  what the headline meant. Recorded as a rule in `docs/practices.md`,
  "The intent lives in the qualifier" -- and generalised there on
  2026-08-22, once a retro-audit of Stage 0-2 found the same shape in
  six findings rather than this one, and turned it from an audit
  technique into a drafting rule: a qualifier becomes a bullet with its
  own test, or is struck, at the time the criteria are written.
- **An interface that deliberately omits something needs a suite that
  omits it too.** `Field` carries no storage on purpose. A single
  contract suite covering `Field` and `CollocatedField` together could
  only ever have asserted the union, which is `CollocatedField` -- so
  the split in the code needed a matching split in the tests, and did
  not get one until this audit. One suite per interface, not one per
  hierarchy.
- **A deferral gated on a specific task must be revisited when that task
  closes, whichever way it went.** `assets/colourmaps/` was carved out
  of the Stage 0 "no empty tracked file" rule until "TASK-017 needs it".
  TASK-017 landed and deliberately did not need it -- an answer, not a
  pending question -- and nothing recorded the difference. Also
  recorded in `docs/practices.md`.

---

## TASK-014

Field Interface

**Status: Done, 2026-08-21.** `src/pyflow/engine/field.py` implements
`Field` exactly as specified by this task's Acceptance Criteria below;
`tests/unit/test_field.py` exists and passes (ten tests, exercising the
ABC directly through two minimal test-only subclasses, per this task's
own deferral of the parametrised contract suite to TASK-015), `make ci`
is clean, and coverage on the new module is 100%. Built strict TDD --
the test file was written and confirmed to fail for the right reason
(`ModuleNotFoundError`) before any implementation code existed. See
`src/pyflow/engine/CLAUDE.md` for implementation notes, including one
real design correction made while drafting these Acceptance Criteria
(`docs/CHANGELOG-DESIGN.md`, 2026-08-21): `Field` carries no storage of
its own, so it makes no assumption about collocated vs. staggered
arrangement.

### Purpose

Establish the `Field` abstraction -- mesh association, a name, and the
promise of an independent copy -- shared by every physical quantity the
engine will transport, regardless of what kind of data it holds (scalar,
vector, later maybe tensor) or how it's arranged over the mesh
(collocated now, staggered later). This is `docs/architecture/engine.md`'s
Variables layer, directly above `Mesh`.

### Dependencies

TASK-012 (Mesh) -- a `Field` is meaningless without a `Mesh` to belong to.

### Design decisions, recorded here

**Same interface-first pattern as TASK-011/TASK-012** (maintainer's
call, 2026-08-20). Matches `docs/architecture/engine.md`'s Variables
contract ("a common `Field` abstraction... shared by every physical
quantity... regardless of arrangement") and its upgrade path (collocated
→ alternative placement schemes, e.g. staggered). Internal engineering
discipline, not a formal ICD, same caveat as TASK-012 -- `icds.md` still
doesn't document Variables, per `ADR-003`'s unchanged scope.

**`Field` itself carries no storage at all.** Only `mesh`, `name`, and an
abstract `copy()` -- the same restraint `CoordinateSystem` (TASK-011)
showed by committing to nothing about vertex-vs-cell-center placement.
How a field's values map onto the mesh (every cell, for collocated;
split across cells and faces, for a future staggered arrangement) is
exactly what "collocated vs. staggered" differs on, so it cannot live on
the interface both are meant to satisfy. `CollocatedField` (TASK-015) is
where cell-centred storage, initialisation, and value access actually
get implemented, shared by every collocated field regardless of arity;
this task's own text originally named `CollocatedField` as arriving
alongside TASK-015/016, which this split keeps faith with.

**The parametrised contract test suite is deferred to TASK-015, not
written here, and this is deliberate.** A contract suite with zero
concrete implementations to parametrise over proves nothing --
`tests/unit/test_collocated_field_contract.py` (named
`test_field_contract.py` until 2026-08-22 -- see the Stage 2 exit audit
above) is written when `ScalarField` exists to run it against, exactly
as `test_coordinate_system_contract.py` and `test_mesh_contract.py` were
each written alongside their layer's first implementation. TASK-016 then extends that suite's parametrisation to
add `VectorField`, rather than duplicating it.

### Artifacts Produced

- `src/pyflow/engine/field.py` -- the `Field` ABC only. Concrete
  implementations live in their own modules (`collocated_field.py`,
  `scalar_field.py`, `vector_field.py`, TASK-015/016) rather than
  sharing `field.py` the way `mesh.py` shared interface and
  implementation in one task -- three separate tasks now produce three
  separate classes, and one shared file would make each task's diff read
  as touching work that isn't its own.

### Implementation

Test-driven (`docs/practices.md`), same standard TASK-012 met and
TASK-011 fell short of: write `Field`'s own tests before the class they
check, confirmed red for the right reason first.

1. Define `Field` as an `ABC` with a concrete `__init__(mesh, name)`
   storing both (validated: an empty `name` raises `ValueError`),
   concrete `mesh`/`name` properties, and one abstract method: `copy()`.

### Acceptance Criteria

- `Field` cannot be instantiated directly -- constructing it raises
  `TypeError`, checked rather than assumed.
- `mesh` returns exactly the `Mesh` passed at construction, unchanged
  for the field's lifetime.
- `name` returns exactly the string passed at construction.
- Constructing with an empty `name` raises `ValueError`.
- `copy()` is declared abstract -- every concrete subclass must supply
  its own; `Field` prescribes nothing about how, since it has no storage
  to copy. (Verified for real, for the first time, under TASK-015 --
  `Field` itself cannot be instantiated to check this directly.)

**Deliberately not built now, planned for later:** the parametrised
contract suite -- TASK-015's artifact, extended by TASK-016, per the
design decision above.

---

## TASK-015

Scalar Field

**Status: Done, 2026-08-21.** `src/pyflow/engine/collocated_field.py`
(`CollocatedField`) and `src/pyflow/engine/scalar_field.py`
(`ScalarField`) implement this task's Acceptance Criteria below exactly.
`tests/unit/test_collocated_field_contract.py` (the contract suite
TASK-014 deferred to this task, parametrised over `[ScalarField]` at the
time and named `test_field_contract.py` until 2026-08-22) and
`tests/unit/test_scalar_field.py` (implementation-specific) both exist
and pass -- 14 tests between them on the day this landed -- `make ci` is clean, and coverage on
both new modules is 100%. Built strict TDD, tests confirmed red
(`ModuleNotFoundError`) before any implementation code existed. See
`src/pyflow/engine/CLAUDE.md` and this task's own "Further design
decisions" above for one real typing correction found while
implementing, not while planning: `value_at`/`set_value_at` ended up
abstract on `CollocatedField`, typed via `Generic[T]`, rather than
concretely returning a tensor, because the concrete version made
`ScalarField`'s `float`-returning override incompatible under
`mypy --strict`.

### Purpose

The first concrete `Field` family: `CollocatedField`, the shared
cell-centred storage/initialisation/access logic every collocated field
needs regardless of arity, and `ScalarField`, its single-value-per-cell
leaf. Also the task that makes `Field`'s contract suite real, per
TASK-014's own deferral.

### Dependencies

TASK-014.

### Design decisions carried forward from the original task text

**"Initialisation" must support a non-uniform, patterned initial
condition, not only a single uniform value** (noted 2026-08-20,
`docs/planning/backlog.md` "physical correctness validation"). Taylor-Green
vortex needs each cell initialised to a specific analytical function of
its position; Kelvin-Helmholtz instability and Rayleigh-Bénard
convection need two distinct regions or a gradient, not a constant.

**Mechanism: general callable/expression-based, not a fixed set of named
presets** (maintainer's call, 2026-08-20). A field initialises from any
function of a cell's position -- the constant case is that callable's
degenerate form, not a second code path, implemented once in
`CollocatedField.__init__` so every subclass (including TASK-016's) gets
it for free. Supports every validation demo named so far
(`docs/implementation/golden-demos.md` "Future Demos") without this task
being revisited each time a new demo needs a shape nobody thought to
name in advance.

### Further design decisions

**Storage is a `torch.Tensor`, `torch.float64` by default.** The first
module that actually stores numerical data in one, rather than the
Python floats/tuples `CoordinateSystem`/`Mesh` use for geometry --
PyTorch is the array library `ADR-005` already committed the project to.
`float64`, not PyTorch's own `float32` default, to match the double
precision those two layers already carry throughout; revisited only if
Stage 12 (Performance) profiling gives a real reason to trade it for GPU
throughput, not before, per this project's "don't build ahead of a real
consumer" (TASK-011) applied to a trade-off rather than a capability.
Device placement (CPU vs. GPU) is out of scope for the same reason --
storage is always a CPU tensor until Stage 12.

**A collocated field's storage shape is tied to its mesh by
construction, not merely validated against it** -- Stage 2 Completion
Criterion 3. `CollocatedField.__init__` allocates
`(mesh.num_cells, *component_shape)` itself; nothing else can set or
override the leading dimension, so no code path can produce a field
whose storage disagrees with its mesh's cell count. `component_shape` is
the one abstract property a leaf class supplies (`()` for `ScalarField`,
`(num_components,)` for `VectorField`, TASK-016).

**Invalid cell ids reuse `Mesh`'s own `InvalidMeshEntityError`, not a new
exception type.** A field's cell id has exactly the same valid range as
its mesh's -- checked directly against `mesh.num_cells`, not by calling
into `Mesh`'s own private validation -- so this is the same failure
condition `Mesh` already names, not a new one at a different layer.

**`value_at`/`set_value_at` are abstract on `CollocatedField`, not
concretely implemented returning a tensor -- found while implementing,
recorded here rather than left only in the code.** A concrete
`CollocatedField.value_at(self, cell: int) -> torch.Tensor` would make
`ScalarField.value_at(self, cell: int) -> float` an incompatible
override under `mypy --strict`, since `float` and `torch.Tensor` aren't
related types. `CollocatedField(Field, Generic[T])` instead declares
`value_at`/`set_value_at` abstract over a type parameter `T`; a leaf
class (`ScalarField` is `CollocatedField[float]`) satisfies them by
converting through the shared, concrete `_tensor_at`/`_set_tensor_at`
helpers, which do the actual id-checked tensor access. `Field.copy`
needed the matching fix -- typed `-> Self` (`typing.Self`), not
`-> Field`, so that calling `copy()` on a `CollocatedField[Any]`-typed
value keeps `.values`/`.set_value_at` available rather than losing them
to the abstract base's own declared type.

### Artifacts Produced

- `src/pyflow/engine/collocated_field.py` -- `CollocatedField(Field,
  Generic[T])`: still abstract (`component_shape`, `value_at`,
  `set_value_at` all unresolved), concrete everywhere else -- storage
  allocation, generic initialiser application, `values` (the full
  backing tensor), the protected `_tensor_at`/`_set_tensor_at` helpers,
  `_check_cell`.
- `src/pyflow/engine/scalar_field.py` -- `ScalarField(CollocatedField[float])`:
  `component_shape = ()`; `value_at`/`set_value_at` implemented to
  return/accept a plain `float` rather than a 0-d tensor, for ergonomics
  -- compatible with, not an exception to, the generic contract, which
  only requires `torch.as_tensor(field.value_at(cell))` to match
  `field.values[cell]`.
- `tests/unit/test_collocated_field_contract.py` -- the shared,
  implementation-independent contract suite (TASK-014's deferred
  artifact); named `test_field_contract.py` when this task landed, and
  renamed 2026-08-22 once a `Field`-level suite took that name (Stage 2
  exit audit, above). Parametrised over `[ScalarField]` at the time
  (typed
  `type[CollocatedField[Any]]` so the suite can call `value_at`/
  `set_value_at` generically without per-implementation casts);
  TASK-016 adds `VectorField` to the same parametrisation rather than
  writing a second suite.
- `tests/unit/test_scalar_field.py` -- `ScalarField`'s own specific
  claims.

### Implementation

Test-driven, contract suite and `ScalarField`'s own tests written and
confirmed red before any implementation code, per `docs/practices.md`.

1. Write the contract suite against `Field`/`CollocatedField`,
   parametrised so a future implementation joins by extending the
   parametrisation, not by writing new contract tests.
2. Implement `CollocatedField`, then `ScalarField` on top of it.

### Acceptance Criteria

**Contract suite (implementation-independent -- must pass for every
concrete `Field`, `ScalarField` included):**

- Constructing a field allocates storage shaped exactly
  `(mesh.num_cells, *component_shape)` -- checked against at least two
  differently-sized meshes, so a hardcoded constant cannot pass by
  coincidence (`docs/practices.md`'s distinct-factors rule).
- A `None` initialiser produces all-zero storage.
- A constant initialiser produces that exact value at every cell.
- A callable initialiser `f(x, y) -> value` is evaluated once per cell
  against that cell's `mesh.cell_centroid`, and the stored value at
  every cell matches calling `f` directly at that cell's centroid --
  checked against a function that is not constant in either axis (e.g.
  reads both `x` and `y` differently), not one a constant-initialiser
  bug could also satisfy.
- `value_at(cell)` / `set_value_at(cell, value)` round-trip exactly, for
  every valid cell id.
- Reading or writing an invalid cell id raises `InvalidMeshEntityError`,
  identically to `Mesh`'s own accessors for the same id.
- `copy()` returns an independent instance: mutating the copy leaves the
  original's `values` unchanged and vice versa, verified by an actual
  mutate-then-compare.

**`ScalarField`-specific:**

- `value_at(cell)` returns a Python `float`, not a tensor -- an
  ergonomic promise beyond what the contract suite requires.
- The callable-initialisation check above, re-verified for the scalar
  case with e.g. `lambda x, y: x + 10 * y`, so a formula reading only
  one axis or swapping `x`/`y` fails visibly.
- `copy()`'s independence, re-verified specifically against
  `ScalarField`'s own storage (not only inherited from the contract
  suite) -- catches a hypothetical override that broke it.

---

## TASK-016

Vector Field

**Status: Done, 2026-08-21.** `src/pyflow/engine/vector_field.py`
(`VectorField`) implements this task's Acceptance Criteria below
exactly. `tests/unit/test_vector_field.py` (implementation-specific) and
the extended `tests/unit/test_collocated_field_contract.py`
(`_IMPLEMENTATIONS = [ScalarField, VectorField]`; named
`test_field_contract.py` until 2026-08-22) both exist and pass -- 38
tests between the contract suite and the two implementation-specific
files (this read "32" until the 2026-08-22 exit audit counted them: the
contract suite collects 16 once parametrised over both implementations,
`test_vector_field.py` 16, `test_scalar_field.py` 6) -- `make ci` is clean, and coverage on the new module is 100%.
Built strict TDD, tests confirmed red (`ModuleNotFoundError`) before any
implementation code existed.

### Purpose

The second concrete `Field` leaf: a fixed number of components per cell
(2, for the MVP's 2D velocity), built on TASK-015's `CollocatedField`
and extending its contract suite rather than writing a second one.

### Dependencies

TASK-014, TASK-015 (`CollocatedField` and the contract suite it defined
both come from there).

### Artifacts Produced

- `src/pyflow/engine/vector_field.py` --
  `VectorField(CollocatedField[tuple[float, ...]])`.
- `tests/unit/test_collocated_field_contract.py` -- extended,
  `VectorField` added to the existing parametrisation (TASK-015's file,
  not a new one; renamed from `test_field_contract.py` on 2026-08-22).
- `tests/unit/test_vector_field.py` -- `VectorField`'s own specific
  claims.

### Implementation

1. `VectorField(mesh, name, num_components=2, initial_value=None)`;
   `component_shape = (num_components,)` -- `num_components` is set on
   the instance *before* calling `super().__init__()`, since
   `CollocatedField.__init__` reads `component_shape` to size storage.
   `value_at`/`set_value_at` implemented (satisfying the abstract
   methods `CollocatedField` declares over its type parameter, per
   TASK-015's own correction -- not "overridden" from a concrete base,
   since there is none) to return/accept a `tuple[float, ...]`/
   `Sequence[float]` of length `num_components` -- the vector analogue
   of `ScalarField`'s float.
2. `component(index)` -- the tensor of every cell's value at that
   component, shape `(num_cells,)` -- generic indexed access, not named
   `x`/`y` properties, so the API doesn't hardcode exactly two
   components even though the MVP only ever constructs two.
3. `magnitude()` -- the Euclidean norm per cell, shape `(num_cells,)` --
   the "visualisation support" TASK-017 consumes directly, computed once
   here rather than TASK-017 reaching into `values` itself.
4. Add `VectorField` to the collocated contract suite's existing
   parametrisation.

### Acceptance Criteria

**Contract suite:** unchanged from TASK-014/015, now also passing for
`VectorField` via the extended parametrisation -- no new contract
assertions, per the design decision recorded under TASK-014.

**`VectorField`-specific:**

- `value_at(cell)` returns a `tuple[float, ...]` of length
  `num_components`; `set_value_at(cell, value)` accepts a sequence of the
  same length and raises `ValueError` for a mismatched length.
- The callable-initialisation check re-verified for the vector case with
  components that behave differently from each other (e.g.
  `lambda x, y: (x, -y)`), so a swapped or duplicated component fails
  visibly.
- Constructing with `num_components <= 0` raises a specific, named
  exception (mirrors TASK-011's `dx <= 0`, TASK-012's `nx <= 0`).
- `component(index)` for every valid index returns a `(num_cells,)`
  tensor whose value at cell `c` equals `value_at(c)[index]`, for every
  cell -- checked against a field where every component differs.
- `component(index)` for an invalid index raises `IndexError`.
- `magnitude()` returns a `(num_cells,)` tensor equal to the Euclidean
  norm of `value_at(c)` at every cell `c`, checked against a
  hand-computed field where the norm isn't trivially 0 or 1 anywhere, so
  a bug returning the sum or a single component cannot pass by
  coincidence.

  **Not honoured when implemented; corrected 2026-08-22.**
  `test_magnitude_is_the_euclidean_norm_not_the_sum_or_a_single_component`
  used a two-cell field of `(3, 4)` and `(0, 0)` -- one discriminating
  cell and one trivially-zero one, against a criterion that says "isn't
  trivially 0 or 1 **anywhere**". The second cell is now `(-5, 12)`, so
  both cells discriminate and one carries a negative component. Found by
  the Stage 0-2 retro-audit (`docs/practices.md`, "The intent lives in
  the qualifier") reading each criterion's qualifying clause against the
  test that claimed to satisfy it. The original test was not *wrong* --
  3-4-5 does rule out sum-and-single-component -- which is exactly why
  nothing noticed: a weaker check that still catches the bug you were
  thinking of reads as a passing criterion.

---

## TASK-017

Field Rendering

**Status: Done, 2026-08-21.** `src/pyflow/rendering/field_visualization.py`
(`scalar_field_colors`, `build_scalar_field_mesh`,
`build_vector_field_arrows`, `build_field_legend`), `FieldDisplayConfig`
(`src/pyflow/configuration/schema.py`), and `bootstrap.py`'s wiring
implement this task's Acceptance Criteria below. Golden demo:
`examples/golden-demos/field_display.yaml`,
`tests/golden/test_field_display.py` (8 tests, including exact
per-cell pixel-position checks for all nine cells of a hand-checkable
3x3 mesh, the legend gradient, and the vector arrows). Also touches
`mesh_visualization.py` (`fit_camera_to_bounds`, factored out of
`fit_camera_to_mesh` so the camera can be framed on a box larger than
the mesh itself, for the legend) and adds `tests/unit/
test_field_visualization.py` and three new cases in `tests/unit/
test_bootstrap.py`. `make ci` is clean; coverage on every new/touched
module is 100%. See `src/pyflow/rendering/CLAUDE.md` for implementation
notes, including two real findings from running the tests, not
predicted in advance: `gfx.Mesh` face colours are linear, not sRGB
(`_srgb_decode`), and every cell's arrow starts exactly at that cell's
own centroid, which can overlap the field-colour pixel a naive per-cell
check would sample.

### Purpose

Make fields visible: scalar fields as a colour map, vector fields as
arrows, both sharing one legend built from the exact same colour
function the field itself is drawn with. `ADR-005`'s own negative
consequences already flag this as real implementation work, not a
library call -- wgpu/pygfx provides no turnkey colour maps, glyphs, or
legends the way VTK/PyVista would have.

### Dependencies

TASK-013 (reuses its zoom/pan/camera path), TASK-015, TASK-016.

### Design decisions, recorded here

**One built-in colour ramp, not a colormap library.** A two-stop linear
gradient (`low_color` → `high_color`, both configurable, defaulting to a
blue→red ramp) is sufficient to make a scalar field visible and testable
at the pixel level. A perceptually-uniform library (viridis, plasma, ...)
is deferred until a real need exceeds a two-stop gradient, per P-016 --
nothing in Stage 2 needs one, and adding it later is a colour-mapping
function, not an architecture change.

**Arrows are plain line segments, not glyphs with arrowheads.** A line
from each cell's centroid, direction and length set by that cell's
vector value (scaled by a configurable factor, capped so adjacent arrows
don't overlap at the mesh's own spacing), reuses exactly the
line-drawing mechanism `build_mesh_grid_line`
(`src/pyflow/rendering/mesh_visualization.py`, TASK-013) already
established, rather than a second rendering primitive. A triangular
arrowhead would be a real visual improvement, and is also not
independently checkable at the pixel level in any way a plain segment's
own direction and length aren't -- deferred, not because it's hard, but
because nothing in this task's Acceptance Criteria needs it to be
checkable, and building it anyway is exactly the "beyond what the task
requires" the repository's own `CLAUDE.md` warns against.

**The legend is a colour strip, not a labelled colour bar with rendered
numeric text.** wgpu/pygfx's text-rendering support has not been
verified live, unlike every other rendering claim this project has made
(`ADR-005`, `docs/CHANGELOG-DESIGN.md`'s live-verification precedent
throughout) -- committing to rendered numeric labels now would be
exactly the kind of unverified claim `docs/practices.md`'s Integrity
section rules out. The legend's own Acceptance Criteria below check that
it uses the same colour function as the field, not that it displays
numbers. Revisit numeric labelling as its own task once pygfx's text
support is actually checked live, not folded silently into this one.

**Configuration surface is a small, closed demo schema -- deliberately
narrower than `Field`'s own general-callable API.** TASK-015/016 decided
fields initialise from an arbitrary Python callable; a YAML config file
cannot carry a Python callable, and a safe expression parser for one is
real scope this stage doesn't need. `FieldDisplayConfig` (new,
`src/pyflow/configuration/schema.py`) offers a small, named set of
patterns for the golden demo only -- e.g. `"radial_gradient"` for the
scalar field, `"rotational"` for the vector field -- distinct from, and
not claiming to be, the general mechanism real simulation code uses.
Real scenarios (Stage 4 onward) construct fields directly in Python,
where the general callable API already applies in full; this schema
exists only so TASK-017's own golden demo can satisfy the public-API
rule without a YAML expression language nobody else needs yet.

### Artifacts Produced

- `src/pyflow/rendering/field_visualization.py` -- colour-map function
  (`scalar_field_colors`), arrow-line builder
  (`build_vector_field_arrows`), and legend builder
  (`build_field_legend`), following `mesh_visualization.py`'s existing
  shape: pure functions returning pygfx-ready geometry, not owning the
  render loop themselves.
- `FieldDisplayConfig` in `src/pyflow/configuration/schema.py`, following
  `RenderingConfig`/`MeshConfig`'s established pattern -- every field
  defaulted, `PyFlowConfig()` alone stays valid, invalid values raise via
  the same `validate()` mechanism.
- `examples/golden-demos/field_display.yaml` and
  `tests/golden/test_field_display.py`.

### Implementation

1. `scalar_field_colors(field, low_color, high_color, value_range)` --
   normalises each cell's value into `[0, 1]` against `value_range`
   (clamped at the ends, not extrapolated), linearly interpolates
   `low_color` → `high_color`, returns per-cell RGBA.
2. `build_vector_field_arrows(field, mesh, scale)` -- one line segment
   per cell, from centroid to `centroid + scale * value_at(cell)`.
3. `build_field_legend(low_color, high_color, value_range, position)` --
   a small rectangular strip, sampled through the same
   `scalar_field_colors` function the field itself uses, not a second
   implementation of the gradient.
4. Wire into `RenderWindow`/`bootstrap.py`, gated by `FieldDisplayConfig`,
   reusing the existing camera/zoom/pan path unchanged.

### Acceptance Criteria

**Rendering correctness -- scalar colour map:**

- Given a `ScalarField` of known, non-uniform values and a fixed,
  deterministic camera/viewport, the rendered frame's pixel colour at
  each cell's on-screen location matches `scalar_field_colors`'s output
  for that cell's value, within tolerance -- checked by pixel inspection
  via `bootstrap()`'s `last_image`, the same mechanism TASK-013
  established, for at least one small, hand-checkable mesh.
- Two cells with different values render as visibly different colours,
  by a fixed minimum pixel-value contrast -- rules out a mapping
  function that happens to collapse to one colour for the test's own
  chosen values.

**Rendering correctness -- vector arrows:**

- Given a `VectorField` of known, non-uniform per-cell vectors, the
  rendered frame contains a line segment at each cell's centroid whose
  on-screen direction and length match `build_vector_field_arrows`'s
  output -- checked the same way TASK-013 checked grid-line pixel
  position, for a hand-checkable mesh with vectors that differ in both
  direction and magnitude across cells.
- A zero vector at a cell renders no arrow at that cell (no spurious
  zero-length line drawn as a dot or artifact).

**Legend:**

- A legend region appears in the rendered frame at a fixed, configured
  screen location, and its pixel colours at the sampled low/mid/high
  points equal `scalar_field_colors`'s output for the corresponding
  values -- proving it shares the field's own colour function rather
  than an independently-tuned one.

  **This criterion cannot currently fail, and that is worth stating
  rather than leaving as an apparent pass** (2026-08-22 retro-audit).
  The colour map is a two-stop *linear* ramp. Any independent
  implementation of a linear ramp with the same endpoints and the same
  `value_range` is not a different function -- it is the same function
  -- so sampling three points cannot distinguish "shares
  `_map_values_to_colors`" from "reimplements it identically". The
  qualifier ("proving it shares...") is therefore satisfied by
  construction (`build_field_legend` calls `_map_values_to_colors`;
  verified by reading, `src/pyflow/rendering/CLAUDE.md`) and not by the
  test. **It becomes a real, falsifiable criterion the moment the colour
  map stops being linear** -- a perceptually-uniform ramp, a
  discontinuous one, a log scale -- at which point the sampled points
  must include one where the two implementations would diverge. Whoever
  adds a non-linear colour map owns making this test real; until then it
  is a structural guarantee wearing a test's clothes.
- **Not claimed or tested:** numeric labels on the legend, per the
  design decision above -- stated so its absence isn't mistaken for an
  oversight.

**Configuration and golden demo:**

- Field display is controllable entirely through `PyFlowConfig` --
  `FieldDisplayConfig`'s closed demo patterns -- no bespoke code, per
  the public-API rule.
- The golden demo ("display scalar and vector fields") is
  `examples/golden-demos/field_display.yaml`, run via `pyflow run
  --config <file> --backend offscreen`, following `empty_mesh.yaml`'s
  precedent exactly: a subprocess CLI test through the real command, a
  `bootstrap()`-based pixel test proving both the scalar map and the
  vector arrows actually rendered, and a determinism test (two runs
  produce identical frames).

**Not applicable here, stated so its absence isn't mistaken for an
oversight:** the physical-correctness acceptance-criteria extension
(`docs/practices.md`) applies to tasks that compute and check a physical
result; this task renders values it's given, it doesn't compute them --
same carve-out TASK-013 and Stage 2's own Completion Criteria already
state.

**Knock-on note:** whatever `FieldDisplayConfig`'s closed pattern set
looks like will be the thing a later "real scenario" config surface
(Stage 4+, once actual initial conditions are configuration-driven
rather than Python-constructed) either reuses or deliberately supersedes
-- worth flagging when that surface is designed rather than assuming
this one silently becomes it.

Golden Demo

Display scalar and vector fields.

**Criteria retrofitted to a feature file 2026-08-22** --
`tests/features/field_display.feature`, bound by
`tests/golden/test_field_display.py`, with the per-cell/legend/arrow
steps that only this demo can use kept in that module and the
demo-independent ones in `tests/golden/conftest.py`. Same reasoning as
TASK-013's note above; the prose criteria stay as the record.

**One thing the retrofit made plain, and it is the case for the whole
change:** the legend criterion above ("proving it shares the field's own
colour function") had already been marked as unable to fail, by the
2026-08-22 retro-audit reading the prose. Written as a scenario, the
same gap is visible at drafting time rather than at audit time -- there
is no way to phrase "prove it shares the function" as steps without
noticing that a linear ramp is indistinguishable from an identical
linear ramp.

---

## TASK-039

Configuration File Generator

**Numbered out of sequence, deliberately -- read this before the
number below looks like a mistake.** Added 2026-08-21 (maintainer's
request), mid-Stage-2, after TASK-038 (Stage 6) already existed as the
highest assigned `TASK-NNN`. Stages 7-13 have no numbered tasks yet
(`docs/planning/roadmap.md`'s own "Tasks include" bullets), so
renumbering everything from here to make room would touch nothing
concrete -- but TASK-018 through TASK-038 are real, assigned identifiers
already cited elsewhere (`docs/architecture/engine.md`,
`docs/architecture/icds.md`, `docs/CHANGELOG-DESIGN.md`'s dated
records), and `docs/practices.md`'s renumbering rule is explicit that
renumbering only stays cheap "if it happened early" -- it didn't, here.
This task is physically placed at the end of Stage 2, where it belongs
by dependency and reading order; its number is `TASK-039`, the next
free one, not `TASK-018`. Same principle `docs/practices.md`'s "Name a
Stage when you cite its number" already established for Stages, applied
to a task for the first time: position in the document, not the number,
is what says which Stage this belongs to.

**Status: Done, 2026-08-21.** `src/pyflow/configuration/generator.py`
(`generate_config_yaml`) and `pyflow generate-config [--output PATH]`
in `src/pyflow/__main__.py`, built strict TDD against
`tests/unit/test_generator.py` (default and non-default round trips
through `load_config`, the non-default case covering every tuple-typed
field with distinct values; the top-level key-order check) and
`tests/integration/test_cli.py` (stdout, and `--output` followed by a
real `pyflow run --config <path> --backend offscreen --max-frames 1`
subprocess), plus a complementary in-process `tests/unit/test_main.py`
pair for `__main__.py` coverage, the same pattern `test_bootstrap.py`
already established. `make ci` is clean; 297 tests at 99% overall,
`generator.py` itself at 100%. (This line read "260 tests" until the
2026-08-22 exit audit checked it against a real run -- 297 is what
`make ci` collected on the day this landed, and what
`docs/repository-manifest.md` recorded in the same commit. Neither
number was load-bearing; the wrong one is recorded here rather than
silently swapped, because a count nobody re-derived is exactly the
class of claim `make ci` cannot check.) Implementation matched the Implementation
section below exactly (`asdict()`, `_tuples_to_lists`, `sort_keys=False`)
-- no design correction needed there. One real finding outside the
module itself: `make lint`'s pre-commit `mypy` hook runs in its own
isolated environment, separate from `uv sync`'s, and had no
`additional_dependencies` at all -- so it had no `types-pyyaml`, fell
back to a looser bundled stub for `yaml.safe_dump`'s overloads, and
flagged `Returning Any from function declared to return "str"` on a line
`uv run mypy --strict` passed clean. Fixed at the actual gap
(`additional_dependencies: [types-pyyaml]` added to that hook in
`.pre-commit-config.yaml`), not with a `cast` in `generator.py` papering
over a discrepancy between two `make` targets that are supposed to be
the same check. See `src/pyflow/configuration/CLAUDE.md` for the full
account.

### Purpose

Generate a valid `PyFlowConfig` YAML file from the schema itself, rather
than requiring every config author -- a golden demo, a user, a future
scenario -- to hand-write YAML against `src/pyflow/configuration/
schema.py` from memory and discover a wrong section or field name only
when `load_config` rejects it. `loader.py` already validates YAML
*after* it's written; this is the schema's other direction, YAML
*generated from* the dataclasses, so a config author starts from
something already correct rather than typing toward correctness.
Motivated now, not before: TASK-017 just added `FieldDisplayConfig`, the
fourth config section, and every Stage from here adds more --
`RenderingConfig` alone gained eight fields since TASK-007's original
three, none of which a hand-written config from that day would know
about.

### Dependencies

None functionally, but sequenced last in Stage 2 (after TASK-017) so it
scaffolds the full schema TASK-014..017 leaves behind, not a partial one
that needs revisiting the moment `FieldDisplayConfig` lands.

### Design decisions, recorded here

**Scope: generate a complete, valid, hand-editable scaffold -- not an
interactive wizard, not per-field CLI overrides, not inline
documentation comments.** "So we don't need to write them by hand"
(maintainer's own framing) is satisfied by a correct starting file a
user then edits the values they care about into; anything past that is
speculative scope this task doesn't yet have a real consumer for
(`docs/engineering-principles.md`'s reversible-decisions preference,
already applied this way to `CoordinateSystem`'s deferred second
implementation and `rendering/canvas.py`'s deferred third backend).
Per-field override flags and inline comments (which `PyYAML`'s
`safe_dump` cannot produce without hand-rolling the serialiser, since
comments aren't part of the YAML data model it round-trips) are
explicitly deferred, not forgotten -- revisit if a real workflow needs
them.

**Reuses `dataclasses.asdict()`, not a hand-written serialiser.** Every
config section is already a plain `@dataclass`; `asdict()` recursively
converts a `PyFlowConfig` instance (nested dataclasses included) into
plain dicts with no extra code, the same "don't restate a fact the
schema already knows" reasoning `docs/CLAUDE.md` states for generated
documentation, applied here to generated configuration instead. One real
gap `asdict()` leaves: it preserves Python `tuple`s (`MeshConfig.origin`,
`RenderingConfig.pan`), and `yaml.safe_dump` has no representer for a
bare tuple (`SafeDumper` deliberately excludes the `!!python/tuple` tag
the full `Dumper` would use) -- a small recursive tuple-to-list
conversion closes that gap before dumping, the config-generation mirror
of `MeshConfig.__post_init__`'s existing list-to-tuple normalisation on
the read side.

**A CLI subcommand, not a `tools/generators/` script.** `tools/
generators/` (`generate_docs_index.py`, `generate_dependency_tree.py`,
`generate_repository_inventory.py`) regenerates committed repository
artifacts that `make ci` checks for staleness -- documentation about the
repository itself. A config scaffold is not a repository artifact; it's
something a user or golden-demo author produces for their own run, the
same category of thing `pyflow run` already is. `pyflow generate-config`
joins `pyflow run` as `__main__.py`'s second subcommand.

### Artifacts Produced

- `src/pyflow/configuration/generator.py` -- `generate_config_yaml(config:
  PyFlowConfig | None = None) -> str`, returning the YAML text for
  `config` (defaulting to `PyFlowConfig()`, i.e. the schema's own
  defaults) with every tuple normalised to a list first.
- `pyflow generate-config [--output PATH]` in `src/pyflow/__main__.py` --
  prints to stdout by default (pipeable: `pyflow generate-config >
  my_config.yaml`), or writes directly to `PATH` if given.

### Implementation

Test-driven (`docs/practices.md`): write `generate_config.py`'s tests
before the module, confirmed red first.

1. `generate_config_yaml`: `dataclasses.asdict(config)`, then a small
   recursive pass converting every `tuple` found (at any nesting depth)
   to a `list`, then `yaml.safe_dump(..., sort_keys=False)` --
   `sort_keys=False` so the output's section order matches
   `PyFlowConfig`'s own declared field order (`logging`, `rendering`,
   `mesh`, `field_display`), not an alphabetised one a reader has to
   re-map against the schema.
2. Wire `generate-config` into `__main__.py`'s existing
   `argparse` subparser structure, alongside `run`.

### Acceptance Criteria

- `generate_config_yaml(PyFlowConfig())`'s output, fed back through
  `load_config` (via a temporary file, since `load_config` reads from a
  path) with no edits, round-trips: the resulting `PyFlowConfig` equals
  `PyFlowConfig()` field-for-field -- the actual claim this task makes,
  checked exactly rather than "it produced some YAML."
- The same round-trip holds for a non-default `PyFlowConfig` (every
  section's fields set to non-default values, including at least one
  tuple-typed field) -- proves the tuple-to-list conversion specifically,
  not just the scalar fields a default-only check could pass without it.
- The generated YAML's top-level key order matches `PyFlowConfig`'s own
  declared field order, checked directly against the parsed YAML
  (`yaml.safe_load` preserves insertion order), not assumed from
  `sort_keys=False` alone.
- `pyflow generate-config` with no arguments prints valid YAML to stdout
  -- a real subprocess test, per this project's public-API/CLI-testing
  convention (`tests/integration/test_cli.py`).
- `pyflow generate-config --output <path>` writes the same content to
  `<path>` and prints nothing to stdout; the written file loads cleanly
  via `pyflow run --config <path> --backend offscreen --max-frames 1`
  (real subprocess, real round-trip through the actual CLI a user would
  use, not just `load_config` called in-process).

---

# Stage 3 — Numerical Engine

Goal

Create the interchangeable numerical architecture.

### Completion Criteria

Written 2026-08-22, before TASK-018 starts, per `docs/practices.md`'s
"A stage gets completion criteria before its first task". **This is the
first stage written under two further rules, both from the Stage 0-2
retro-audit the same day**: every qualifying clause below is its own
checkable bullet rather than prose attached to a headline ("The intent
lives in the qualifier"), and every criterion names the task that
discharges it ("Every task names the stage criteria it discharges"). The
second is why the discharge map follows the criteria rather than being
reconstructed at the exit audit -- documentation accuracy went unclaimed
by any task in both Stage 1 and Stage 2, and failed in both.

Criteria are about the stage's goal -- *an interchangeable numerical
architecture* -- not the union of TASK-018..022's own Acceptance
Criteria.

1. **All six of `adr/ADR-003-modular-numerical-strategies.md`'s
   configuration-selected components exist as interfaces, and none of
   them has a concrete numerical implementation.**
   - Advection, Diffusion, Time Integrator, Pressure–Velocity Coupling,
     Linear Solver and Boundary Condition each exist as an abstract base
     class.
   - Instantiating any of them directly raises `TypeError`; so does a
     subclass that omits any abstract method (the shape
     `tests/unit/test_field.py` established for `Field`).
   - **No concrete scheme ships in `src/` this stage.** Every
     implementation of these six anywhere in the repository at the end
     of Stage 3 lives under `tests/`. This is a deliberate absence, not
     a shortfall: criterion 3's replaceability claim is not testable
     against a single wired-in implementation, and shipping upwind
     advection here would make Stage 4 the first point at which anyone
     could tell whether the architecture works.
2. **Each interface has a contract test suite, exercised by at least two
   distinct test-only implementations.**
   - One parametrised suite per interface, joined by adding a factory.
   - **Two implementations minimum, not one.** Stage 2 shipped a suite
     parametrised over two classes that was still specific to their
     shared base, and a suite with one implementation cannot show it is
     implementation-independent at all -- it can only show that
     implementation exists.
   - No assertion in any of these suites refers to a named numerical
     scheme or its numerics.
3. **Adding an implementation requires editing no existing function
   body.**
   - Assembly looks each of the six up by its configured name; it does
     not branch on the name.
   - Checked directly: a test registers a test-only advection
     implementation under a new name, configures it, assembles a
     simulation, and gets that implementation back -- with no edit
     anywhere under `src/`.
4. **Selection happens once, at construction; execution never re-reads
   it.**
   - The assembled object holds implementation *instances*.
   - Checked directly: mutating the `PyFlowConfig` object after assembly
     changes nothing about the assembled simulation.
5. **All six are selected through configuration, using the mechanism
   that already exists rather than a parallel one.**
   - A `numerics` section in `PyFlowConfig`, each field `Literal[...]`-
     typed and validated in `validate()`, exactly as
     `rendering.backend` already is.
   - **An unknown name fails at `load_config` time with a named
     exception, not at first use** -- `docs/architecture/icds.md` states
     this as the mechanism's whole point, and a value that only explodes
     three layers down when someone finally calls it is the failure it
     names.
   - `PyFlowConfig()` alone stays valid: every field defaulted.
   - `pyflow generate-config` emits the `numerics` section, and its
     output still round-trips through `load_config` unchanged (TASK-039's
     guarantee, which silently stops covering the schema the moment a
     section is added without extending it).
6. **The one real cross-layer dependency is expressed in the interfaces,
   not only in documentation.**
   - `icds.md` names it: Pressure–Velocity Coupling "requires a
     configured Linear Solver to solve the pressure-correction equation
     it produces each timestep -- the one real cross-layer dependency
     among the six".
   - The coupling interface therefore takes a `LinearSolver` at
     construction; a coupling strategy cannot be built without one, and
     a test asserts that.
   - A criterion rather than a design note because Stage 2 demonstrated
     what a correctly-stated constraint living only in prose is worth:
     `engine.md`'s own maintenance rule sat one screen below the entry
     that violated it.
7. **Boundary-condition validity is checked across the whole
   configuration, not per face.**
   - `periodic` on one boundary without its pair also `periodic` raises.
   - Velocity prescribed on every boundary with non-zero net flux
     raises.
   - Velocity and pressure both prescribed on the same boundary raises.
   - All three at configuration-validation time, before anything is
     assembled. `icds.md` calls this "a whole-configuration constraint,
     which validation should check across boundaries rather than
     per-face"; a per-face validator cannot express any of the three.
8. **Stage 3 has a demonstration, and it is honest about having nothing
   new to draw.**
   - The golden demo config names all six components; `pyflow run`
     assembles them, and the run reports the assembled set -- both as a
     log line and as an accessor on what `bootstrap()` returns.
   - A regression test asserts the reported set equals the configured
     set, invoked through the real CLI as a subprocess.
   - **Carve-out, stated so its absence isn't mistaken for an
     oversight:** this stage adds no new rendered output. P-004 asks
     every stage after Stage 0 for a working, visible demonstration; the
     honest form here is that Field Display continues to run unchanged
     with a full `numerics` section present -- which is itself the claim
     worth a test, since a new configuration surface is exactly the kind
     of thing that breaks an existing path silently.
9. **`make ci` passes on both CI platforms, on a real runner** -- not
   only locally, matching Stage 0/1/2's standard of evidence, read from
   the actual run rather than inferred from a merged PR.
10. **Documentation describes what now exists.**
    - `docs/architecture/engine.md`'s six affected layer entries convert
      from "Arrives via" to "Implemented in", each stating explicitly
      that the *interface* arrived here and the concrete implementation
      is Stage 4.
    - `docs/architecture/icds.md`'s "Configuration mechanism (proposed,
      not yet implemented)" becomes implemented, with the real section
      and field names, and the paragraph saying to treat the names as
      provisional is removed.
    - Every touched `CLAUDE.md`, and both inventories, checked against
      the tree directly.

**Two things are deliberately not applicable here, stated so their
absence isn't mistaken for an oversight.**

*The physical-correctness extension* (`docs/practices.md`): nothing in
Stage 3 computes a physical result -- it defines the interfaces Stage
4's implementations will compute through. The first
physical-correctness criteria belong to TASK-023 onward.

*Executable Gherkin criteria*
(`adr/ADR-007-executable-acceptance-criteria.md`): this stage's claims
are architectural -- can an implementation be swapped without editing a
caller, is selection fixed at construction -- and have no
user-observable behaviour to describe. A scenario for "the ABC cannot be
instantiated" would be ceremony, not clarity, and using a form where it
does not fit is how a form gets abandoned. Stage 3's criteria stay
prose bullets checked by contract suites in plain pytest, which is what
those are good at. **This exemption is Stage 3's alone**; it does not
extend to Stage 4.

### Discharge map

Every criterion has an owning task, assigned now rather than
reconstructed at the exit audit. A task's own **Discharges** section is
authoritative; this table is the index.

| Criterion | Discharged by |
|-----------|---------------|
| 1. Six interfaces, no implementations | TASK-018 (advection, diffusion, gradient, divergence, sources), TASK-019 (boundary condition), TASK-020 (time integrator), TASK-022 (linear solver), TASK-021 (pressure coupling) -- jointly; each closes its own share |
| 2. Contract suite per interface, two implementations each | Each of TASK-018..022 for its own interfaces |
| 3. Adding an implementation edits no existing function | TASK-021 (which builds the assembly path, being last) |
| 4. Selection fixed at construction | TASK-021 |
| 5. Configuration selects all six, `numerics` section | TASK-021, extended incrementally by each task before it |
| 6. Cross-layer dependency in the interface | TASK-022 defines `LinearSolver`; TASK-021 consumes it |
| 7. Whole-configuration boundary validation | TASK-019 |
| 8. Demonstration and its carve-out | TASK-021 |
| 9. `make ci` green on a real runner | TASK-021 |
| 10. Documentation matches the tree | TASK-021 |

**TASK-021 is the stage's last task and therefore owns the stage-level
criteria** -- the demonstration, CI evidence, and documentation
accuracy. That assignment is the whole point of the discharge rule:
those three are not task-level work, which is exactly why nobody claimed
them in Stage 1 or Stage 2, and why documentation accuracy failed in
both.

**Build order is TASK-018, 019, 020, 022, 021 -- not numerical order.**
TASK-022 (Linear Solver) precedes TASK-021 (Pressure Coupling) because
criterion 6 makes the dependency structural: the coupling interface
takes a `LinearSolver` at construction, so that type must exist first.
The tasks appear below in build order and keep their existing numbers,
following the precedent TASK-039 set -- position in this document, not
the number, says what happens when. Renumbering was considered and
rejected on `docs/practices.md`'s own grounds: TASK-021 and TASK-022 are
already cited by number in `docs/architecture/engine.md`'s
Pressure-Velocity Coupling and Linear Solvers entries.

---

## TASK-018

Operator Interfaces

### Purpose

Define the interfaces for the five numerical operators that compute what
a field's values do over one step: Advection, Diffusion, Gradient,
Divergence and Source terms. These are `docs/architecture/engine.md`'s
Flux layer expressed as code -- that document is explicit that no class
named `Flux` need exist, because the flux is what these operators
jointly compute.

No implementations. See Stage 3 Completion Criterion 1 for why that is a
deliberate deferral rather than an unfinished job.

### Dependencies

TASK-014/015/016 (`Field`, `ScalarField`, `VectorField` -- every
operator's input and output), TASK-012 (`Mesh` -- faces, neighbours,
boundaries).

### Design decisions, recorded here

**The six interfaces live in a new `src/pyflow/engine/numerics/`
subpackage, not directly in `engine/` and not in `physics/`.**
`engine/` currently holds five modules and would hold eleven; the six
numerical strategies are a coherent group with one shared purpose
(`ADR-003`'s configuration-selected components) and one shared
configuration section, which is what a subpackage is for. `physics/` is
deliberately *not* the home: it is reserved for phenomena --
temperature, buoyancy, species (Stage 6, TASK-035..038) -- and a
numerical scheme is machinery, not a phenomenon. This extends TASK-000's
package structure rather than contradicting it; `src/pyflow/CLAUDE.md`
records the four top-level subpackages and gains this note.

**Advection and Diffusion are separate interfaces, not one
`FluxScheme`.** `ADR-003` names them as two independently selected
components, and `docs/handbook/numerical-methods/compatibility.md`
records that their combinations have real stability interactions -- an
interaction between two things you can choose separately, which is only
expressible if they *are* separate. Merging them would make
`numerics.advection` and `numerics.diffusion` a single field, which no
document anywhere asks for.

**Gradient, Divergence and Source get interfaces but no configuration
field.** `ADR-003` names six configuration-selected components and these
three are not among them. They are interfaces because the operators that
consume them should not hard-code a discretisation, and they are not
configuration because nothing has yet identified a second implementation
a user would choose between (P-016). Revisit if one appears; adding a
`numerics` field later is additive.

**Operators take a `Field` and return a `Field`-shaped result, never a
mesh alongside it.** Stage 2 Completion Criterion 1, and the specific
defect its exit audit found in `build_vector_field_arrows(field, mesh,
...)`. A field carries its mesh; an operator signature that also takes
one creates a pair nothing checks.

### Artifacts Produced

- `src/pyflow/engine/numerics/__init__.py`, and one module per
  interface: `advection.py`, `diffusion.py`, `gradient.py`,
  `divergence.py`, `source.py`.
- `tests/unit/numerics/test_<name>_contract.py` -- one parametrised
  contract suite per interface.
- Test-only implementations, two per interface, in the test tree.

### Implementation

Test-driven; each contract suite written and confirmed red before its
interface exists, per `docs/practices.md`.

1. Write each contract suite against the interface it is about to
   define, parametrised over factories.
2. Define each ABC. Abstract methods only; no numerics.
3. Write two minimal test-only implementations per interface -- one
   trivial (e.g. returns zeros), one that actually varies with its
   input, so a suite cannot pass against an operator that ignores its
   arguments.

### Acceptance Criteria

**Per interface (all five):**

- The ABC cannot be instantiated directly: `TypeError`.
- A subclass omitting any abstract method cannot be instantiated:
  `TypeError`.
- The set of abstract methods is asserted explicitly, so adding one
  later is a visible change rather than a silent tightening.
- Every operator's public method takes a `Field` (and, where the
  physics needs it, a second `Field` such as velocity) and takes **no
  `Mesh` argument** -- asserted against the signature, not left to
  review.
- The contract suite runs against **two** distinct test-only
  implementations, and every assertion in it passes for both.
- One of those two implementations produces output that varies with its
  input, and at least one contract assertion fails if an implementation
  ignores its input entirely -- checked by a deliberately-inert third
  implementation asserted to fail, so the suite is shown to have teeth
  rather than assumed to.

**Advection specifically:**

- Its method signature takes the transported field *and* a velocity
  field, per `engine.md`'s contract ("given a field and a velocity
  field").
- A velocity field whose `component_shape` does not match the mesh's
  dimensionality raises a named exception -- an accessor-level rejection
  criterion, per `docs/practices.md`'s "rejection criteria stop at the
  constructor".

**Diffusion specifically:**

- Its method signature takes the field alone, per `engine.md` ("given a
  field, produces the diffusive contribution").

**Not applicable here:** the physical-correctness extension. No
numerics exist in this task to be correct or incorrect; TASK-023/024
carry those criteria.

### Discharges

- **Criterion 1**, for Advection and Diffusion (its share of the six),
  plus Gradient/Divergence/Source which are not part of the six.
  *Closed by:* `tests/unit/numerics/test_*_contract.py`'s
  instantiation-rejection tests.
- **Criterion 2**, for its five interfaces. *Closed by:* the same five
  suites, each parametrised over two test-only implementations, plus the
  inert-implementation check that proves the suite discriminates.
- **Criterion 5**, partially: adds `numerics.advection` and
  `numerics.diffusion` to the new `NumericsConfig`. The section is not
  complete until TASK-021; the round-trip and unknown-name criteria are
  checked for these two fields here.

---

## TASK-019

Boundary Condition Interface

### Purpose

Define the interface for how a field behaves at a domain edge where no
neighbouring control volume supplies a flux, and -- the harder and more
easily-missed half -- the validation that a *set* of boundary conditions
is jointly consistent.

### Dependencies

TASK-012 (`Mesh` boundary identification), TASK-014..016 (`Field`),
TASK-018 (the operators that consume a boundary face's value).

### Design decisions, recorded here

**Boundary conditions are configured per boundary, not simulation-wide
-- the only one of the six that is not a single scalar choice.**
`docs/architecture/icds.md` states this directly: "different edges of
the same domain typically need different condition types". So
`numerics.boundary_conditions` is a mapping, e.g. `{north: dirichlet,
south: neumann, east: periodic, west: periodic}`.

**Joint consistency is validated in `PyFlowConfig.validate()`, not by
each condition object.** No individual condition can see the others, and
all three constraints `icds.md` records are relations *between*
boundaries. A per-face validator is structurally incapable of expressing
them, which is why criterion 7 states the whole-configuration
requirement rather than leaving it to the implementer to notice.

### Artifacts Produced

- `src/pyflow/engine/numerics/boundary_condition.py` -- the ABC.
- `BoundaryConditionsConfig` within `NumericsConfig`
  (`src/pyflow/configuration/schema.py`), with the cross-boundary
  validation.
- `tests/unit/numerics/test_boundary_condition_contract.py`, and
  configuration tests for each rejection.

### Implementation

1. Contract suite first, red, then the ABC.
2. Two test-only conditions: one supplying a face value, one supplying a
   face gradient -- the Dirichlet/Neumann shapes without being them.
3. Cross-boundary validation in `validate()`, one test per rejection.

### Acceptance Criteria

**Interface:**

- The ABC cannot be instantiated; a subclass missing an abstract method
  cannot be instantiated; the abstract-method set is asserted
  explicitly.
- Given a boundary face and the field's interior state, the interface
  produces the face value or gradient the interior scheme needs --
  exercised through both test-only implementations.
- Applying a condition to a face the mesh does not classify as a
  boundary raises a named exception. An accessor-level rejection
  criterion, deliberately, per `docs/practices.md`.

**Whole-configuration validation -- each its own rejection test:**

- `east: periodic` with `west: dirichlet` raises at `load_config` time,
  naming both boundaries.
- The same for every other pairing (`north`/`south`), so the check is
  shown to be general rather than hardcoded for one axis.
- A configuration prescribing velocity on all four boundaries whose
  values do not sum to zero net flux raises, and the message says which
  quantity failed. `docs/handbook/numerical-methods/
  boundary-conditions.md`: such a configuration produces a pressure
  equation with no solution at all.
- The same configuration *with* zero net flux is accepted -- so the
  check is shown to reject the physics rather than the shape.
- Prescribing both velocity and pressure on one boundary raises.
- Every one of the above fails at `load_config`, before any assembly --
  asserted by the exception surfacing from the loader, not from a later
  call.

**Not applicable here:** the physical-correctness extension -- with one
exception that *is* physical and is listed above rather than deferred:
the zero-net-flux check is a conservation statement, and it is an
acceptance criterion of this task because the configuration it rejects
has no solution, not merely a bad one.

### Discharges

- **Criterion 1**, for Boundary Condition. *Closed by:*
  `test_boundary_condition_contract.py`'s instantiation-rejection tests.
- **Criterion 2**, for Boundary Condition. *Closed by:* the same suite
  over two test-only implementations.
- **Criterion 7**, entirely. *Closed by:* the six rejection tests above,
  all asserting at `load_config` time.
- **Criterion 5**, partially: adds `numerics.boundary_conditions`.

---

## TASK-020

Time Integrator Interface

### Purpose

Define the interface that advances every transported field from one
timestep to the next, given the state and its time derivative.

### Dependencies

TASK-014..016 (`Field`), TASK-018 (the operators that produce the
derivative).

### Design decisions, recorded here

**The integrator consumes a time derivative, not the schemes that
produced it.** `engine.md`'s core principle, and `icds.md` states the
consequence explicitly: the time integrator is "independent of which
advection/diffusion/pressure-coupling schemes are configured, by
construction". That independence is testable and is an acceptance
criterion below rather than an aspiration.

**The interface advances a *set* of fields, not one.** `engine.md`:
"independent of which fields exist or how many". An interface that
advances a single field would force the caller to loop and would make
coupled systems (Stage 5's velocity/pressure) express themselves
outside the interface.

**A fixed timestep is configured directly; no automatic stability
limit.** `icds.md` records this as the MVP position. Naming it here
stops a future reader reading its absence as an oversight.

### Artifacts Produced

- `src/pyflow/engine/numerics/time_integrator.py` -- the ABC.
- `numerics.time_integration` and a `numerics.timestep` value in
  `NumericsConfig`.
- `tests/unit/numerics/test_time_integrator_contract.py`.

### Implementation

1. Contract suite first, red, then the ABC.
2. Two test-only integrators with genuinely different update rules --
   e.g. explicit Euler and a two-stage scheme -- so the suite cannot
   accidentally encode one scheme's arithmetic.

### Acceptance Criteria

- The ABC cannot be instantiated; a subclass missing an abstract method
  cannot be instantiated; the abstract-method set is asserted
  explicitly.
- Advancing a set of fields returns a set with the same names and the
  same meshes, and leaves the input set unmutated -- checked by
  comparing the input's values before and after, not by inspection.
- The interface is exercised with one field and with three, so "however
  many fields exist" is checked rather than claimed.
- **Scheme independence is checked directly:** the same test-only
  integrator produces the same result when handed a derivative computed
  by two different test-only advection implementations, given the same
  derivative values. This is `icds.md`'s "by construction" claim turned
  into a test, because "by construction" is exactly the kind of phrase
  the Stage 0-2 retro-audit found standing in for one.
- A zero derivative advances the state by nothing, exactly -- the
  boundary case, and the one an integrator that ignores its input would
  also pass, which is why the varying case above is separately
  required.
- `numerics.timestep <= 0` raises at `load_config` time, named.

**Not applicable here:** the physical-correctness extension. Order of
accuracy is a property of RK4 (TASK-025), not of this interface. Stated
because `icds.md` discusses fourth-order accuracy under this layer and a
reader may expect a criterion for it here.

### Discharges

- **Criterion 1**, for Time Integrator. *Closed by:*
  `test_time_integrator_contract.py`'s instantiation-rejection tests.
- **Criterion 2**, for Time Integrator. *Closed by:* the same suite over
  two structurally different test-only integrators.
- **Criterion 5**, partially: adds `numerics.time_integration` and
  `numerics.timestep`.

---

## TASK-022

Linear Solver Interface

**Built before TASK-021 despite the number** -- see the Stage 3 discharge
map. Criterion 6 makes Pressure–Velocity Coupling structurally dependent
on this type, so it exists first.

### Purpose

Define the interface that solves the linear system pressure-velocity
coupling (and any other implicit step) produces, independent of where
the system came from.

### Dependencies

TASK-014..016 (`Field` -- the solution is field-shaped).

### Design decisions, recorded here

**The interface takes a system and returns a solution, and knows nothing
about pressure.** `engine.md`: "given a linear system, produces its
solution, independent of the system's origin". A solver that knew it was
solving a pressure-correction equation could not be reused for the
implicit steps its upgrade path anticipates.

**Convergence is reported, not assumed.** A solver that silently returns
its last iterate when it fails to converge produces a plausible wrong
answer -- the failure mode this repository has now recorded three times
(`Mesh` accessors, mesh config truncation, pan scale). The interface
therefore returns convergence information alongside the solution, and
the caller is required to be able to tell.

**The null-space requirement belongs to the *implementation*
(TASK-026), not this interface, and is recorded here so it is not lost
in between.** `icds.md`: when every boundary prescribes velocity and
none prescribes pressure -- the lid-driven cavity, an MVP validation
case -- the pressure system is positive *semi*-definite and the constant
mode must be removed. That is a property of the system and the concrete
solver, not of "solve a linear system". TASK-026 carries the criterion;
this task carries the pointer.

### Artifacts Produced

- `src/pyflow/engine/numerics/linear_solver.py` -- the ABC, and the
  result type carrying solution plus convergence information.
- `numerics.linear_solver`, plus its tolerance and iteration-limit
  fields, in `NumericsConfig`.
- `tests/unit/numerics/test_linear_solver_contract.py`.

### Implementation

1. Contract suite first, red, then the ABC.
2. Two test-only solvers: one exact (solves a tiny system directly), one
   iterative-shaped that can be made to fail to converge on demand --
   the second exists specifically so the non-convergence criteria below
   are checkable at all.

### Acceptance Criteria

- The ABC cannot be instantiated; a subclass missing an abstract method
  cannot be instantiated; the abstract-method set is asserted
  explicitly.
- Solving a system with a known exact solution returns that solution
  within the configured tolerance, for both test-only solvers.
- **Non-convergence is reported, not returned as an answer:** the
  failing test-only solver, run against a system it cannot converge on
  within the configured iteration limit, produces a result whose
  convergence flag is false and whose iteration count equals the limit.
  A caller that checks the flag can tell; a caller that ignores it gets
  a value, which is why the flag is on the result type rather than being
  a log line.
- The interface is exercised with two systems of different sizes, so a
  solver hardcoded to one size cannot pass.
- `numerics.linear_solver_tolerance <= 0` and
  `numerics.linear_solver_max_iterations <= 0` each raise at
  `load_config` time, named.

**Not applicable here:** the physical-correctness extension, and the
null-space handling above -- both belong to TASK-026, the concrete
Conjugate Gradient implementation.

### Discharges

- **Criterion 1**, for Linear Solver. *Closed by:*
  `test_linear_solver_contract.py`'s instantiation-rejection tests.
- **Criterion 2**, for Linear Solver. *Closed by:* the same suite over
  an exact and an iterative test-only solver.
- **Criterion 6**, its first half: defines the `LinearSolver` type
  TASK-021's interface will require. *Closed by:* the type existing;
  the requirement itself is TASK-021's to close.
- **Criterion 5**, partially: adds `numerics.linear_solver` and its two
  numeric fields.

---

## TASK-021

Pressure Coupling Interface

**Built last** -- see the Stage 3 discharge map. It depends on TASK-022's
type, and as the stage's final task it owns the stage-level criteria:
the demonstration, CI evidence, and documentation accuracy.

### Purpose

Define the interface that enforces incompressibility -- given a
provisional velocity field, produce a corrected, divergence-free one and
the pressure field consistent with it -- and, as the last task in the
stage, assemble all six components from configuration and demonstrate
that the assembly works.

### Dependencies

TASK-022 (`LinearSolver`, required at construction), TASK-018, TASK-019,
TASK-020, TASK-014..016.

**Real cross-layer dependency, recorded 2026-08-20 and now structural:**
`docs/architecture/icds.md`'s Pressure–Velocity Coupling ICD states it
directly -- this strategy "requires a configured Linear Solver to solve
the pressure-correction equation it produces each timestep... the one
real cross-layer dependency among the six". Until 2026-08-22 this was
recorded as "design TASK-021's interface with TASK-022's shape already
in mind" -- advice. Stage 3 Completion Criterion 6 makes it a
constructor argument instead, because the Stage 2 exit audit is a
sustained demonstration of what advice living in prose is worth.

### Design decisions, recorded here

**Assembly lives in a new `src/pyflow/engine/numerics/assembly.py`, not
in `bootstrap.py`.** `bootstrap.py` composes configuration, engine and
rendering for a *run*; assembling six numerical strategies from a
`NumericsConfig` is one subsystem's own concern and belongs beside the
interfaces it instantiates. `bootstrap.py` calls it, the same way it
calls `StructuredCartesianMesh.from_config`.

**Implementations are looked up in a registry keyed by configured name,
not selected by an `if`/`match` chain.** Criterion 3 is the reason: a
chain has to be edited for every new scheme, which is precisely the
"adding a new implementation rather than modifying existing ones"
`docs/planning/implementation-plan.md` promises. The registry is the
mechanism `create_canvas` already gestures at with two backends; this is
the same idea at the point where it starts to pay.

### Artifacts Produced

- `src/pyflow/engine/numerics/pressure_coupling.py` -- the ABC, taking a
  `LinearSolver` at construction.
- `src/pyflow/engine/numerics/assembly.py` -- the registry and
  `assemble_numerics(config) -> AssembledNumerics`.
- `numerics.pressure_coupling` in `NumericsConfig`, completing the
  section.
- `examples/golden-demos/numerics_assembly.yaml` and
  `tests/golden/test_numerics_assembly.py`.
- Documentation: `engine.md`'s six entries, `icds.md`'s configuration
  section, `docs/implementation/golden-demos.md`'s new demo entry, the
  Golden Demos table, `planning/data/demos.yaml`, both inventories.

### Implementation

1. Contract suite first, red, then the ABC.
2. Two test-only coupling strategies, each constructed with a test-only
   `LinearSolver`.
3. The registry and `assemble_numerics`.
4. The demo config, its three-test regression shape, and the
   documentation pass.

### Acceptance Criteria

**Interface:**

- The ABC cannot be instantiated; a subclass missing an abstract method
  cannot be instantiated; the abstract-method set is asserted
  explicitly.
- **Constructing any coupling strategy without a `LinearSolver` fails**
  -- asserted as a real raised exception, not only as a type annotation
  `mypy` would catch, since a type annotation is not a runtime
  guarantee and criterion 6 is about the interface, not the checker.
- Given a provisional velocity field, the interface returns both a
  corrected velocity field and a pressure field -- both checked for
  presence and mesh association, not for numerical correctness, which is
  TASK-027's.
- The contract suite runs against two test-only strategies.

**Assembly -- criteria 3 and 4:**

- A test registers a test-only advection implementation under a name no
  `src/` module knows, configures it, calls `assemble_numerics`, and
  gets that implementation back. **No file under `src/` is edited for
  this test to pass** -- that is the criterion, and the test is written
  so that it would fail if the lookup were an `if`/`match` chain.
- `assemble_numerics` returns implementation *instances*, and mutating
  the `PyFlowConfig` afterwards changes nothing about them -- checked by
  mutating and re-reading.
- An unknown name for any of the six raises at `load_config` time,
  named, before assembly is reached -- checked once per component, so a
  validator wired up for five of six fails.

**Configuration -- criterion 5:**

- `PyFlowConfig()` alone is valid with the full `numerics` section
  defaulted.
- `pyflow generate-config` emits the `numerics` section, and its output
  round-trips through `load_config` to an equal `PyFlowConfig` -- the
  non-default case too, per TASK-039's own criteria, which this task
  extends rather than assumes still hold.

**Golden demo -- criterion 8:**

- `examples/golden-demos/numerics_assembly.yaml` names all six
  components; `pyflow run --config <it> --backend offscreen` assembles
  them and the run reports the assembled set.
- A subprocess CLI test asserts the reported set equals the configured
  set.
- A determinism test: two runs report identically.
- **Field Display still runs unchanged** with a full `numerics` section
  added to its config, producing pixel-identical output to the same
  config without one -- the claim the carve-out in criterion 8 rests on,
  checked rather than assumed.

**Stage-level -- criteria 9 and 10:**

- `make ci` green on both `ubuntu-latest` and `windows-latest`, read
  from the actual run.
- `engine.md`'s six entries say "Implemented in", each stating the
  interface arrived in Stage 3 and the implementation arrives in Stage
  4; `icds.md`'s provisional-names paragraph is gone and its
  configuration keys match the code; the new demo appears in
  `golden-demos.md`, the Golden Demos table and `demos.yaml`; both
  inventories match the tree.

**Not applicable here:** the physical-correctness extension. This task
defines and assembles; TASK-027 (PISO) computes.

### Discharges

- **Criterion 1**, for Pressure–Velocity Coupling.
- **Criterion 2**, for Pressure–Velocity Coupling.
- **Criterion 3**, entirely. *Closed by:* the register-a-new-name test.
- **Criterion 4**, entirely. *Closed by:* the mutate-config-after-assembly
  test.
- **Criterion 5**, entirely -- completing what TASK-018/019/020/022
  each added. *Closed by:* the `generate-config` round-trip over the
  full section.
- **Criterion 6**, its second half. *Closed by:* the
  construct-without-a-solver rejection test.
- **Criterion 8**, entirely. *Closed by:*
  `tests/golden/test_numerics_assembly.py` and the Field Display
  regression check.
- **Criterion 9**. *Closed by:* the CI run id, recorded in this task's
  Status line when it lands.
- **Criterion 10**. *Closed by:* the documentation pass listed above.

Golden Demo

Engine initialises entirely through interfaces. No CFD yet.

---

# Stage 4 — First Numerical Methods

Goal

Implement the simplest valid implementation of every interface.

### Completion Criteria — due when this Stage opens, not now

Written per `docs/practices.md`, criteria arrive **before a stage's
first task**, which means at this stage's open -- after Stage 3 has
delivered the interfaces these implementations must satisfy, not four
stages ahead of them. Writing them now would commit to what Stage 4
guarantees before the shapes it guarantees things about exist, which is
the speculation `docs/engineering-principles.md` P-016 and this
repository's Planning Philosophy both refuse.

**This is the first stage that implements physics**, so its criteria
carry the physical-correctness extension (`docs/practices.md`) in full,
and every task below carries it too.

### Every task in this Stage carries executable acceptance criteria

**This is where "real simulation work" begins, and therefore where
`adr/ADR-007-executable-acceptance-criteria.md` applies** (maintainer's
instruction, 2026-08-22). Each task below gets a Gherkin `.feature`
file under `tests/features/`, and the scenarios in it *are* that task's
acceptance criteria -- not a restatement of prose bullets kept
elsewhere. `make check-scenarios` gates on every scenario actually
running.

The step vocabulary in `tests/golden/conftest.py` is the starting
point, proven on the three existing golden demos when this decision was
taken. Stage 4 will need physics-shaped additions to it -- a domain
initialised to a known state, a solver advanced N steps, a quantity
compared against an analytical answer -- and those belong in the shared
vocabulary from the first task that needs them, not re-derived per task.

**The intent lines below are what those scenarios must be written
against.** They are not the criteria and are not sufficient as ones;
they are the qualifier, isolated in advance so a scenario cannot quietly
be written to the weaker reading.

### Intent, recorded now

Recorded 2026-08-22, ahead of the criteria, because it is the durable
half and the half this repository keeps losing. Each line states what
the task must not merely *nominally* satisfy (`docs/practices.md`,
"The intent lives in the qualifier").

## TASK-023

First-order Upwind Advection

**Intent:** upwind's defining property is **boundedness** -- it cannot
manufacture a cell or face value outside the range of the values it
interpolates between (`docs/handbook/numerical-methods/advection.md`).
That is a testable invariant over an arbitrary field, not a description.
"Produces a plausibly-advected field" is not this task; a scheme that
overshoots is not upwind, however smooth it looks.

**Also intended, and easy to lose:** boundedness is *not* stability.
The handbook is explicit that upwind advanced by an explicit integrator
still has a CFL limit. A criterion asserting boundedness must not be
read as having covered stability.

---

## TASK-024

Central Difference Diffusion

**Intent:** the claim is **second-order accuracy on a uniform orthogonal
mesh** (`docs/handbook/numerical-methods/diffusion.md`), which is a
measured convergence rate under mesh refinement, not a qualitative
"the field diffuses". A first-order-accurate implementation diffuses
perfectly plausibly.

---

## TASK-025

RK4 Time Integration

**Intent:** the claim is **fourth-order accuracy in time for the ODE
system it is handed** -- measured against a problem with an exact
solution, with spatial error isolated so it cannot dominate.
`docs/architecture/icds.md` warns in advance that the *finished
solver's* observed temporal order will be well below four, capped by
first-order upwind and by the coupling's operator splitting. So a
measured order of ~1 in an end-to-end test is expected behaviour and
proves nothing about this task; the criterion has to isolate the
integrator or it cannot fail for the right reason.

---

## TASK-026

Conjugate Gradient Solver

**Intent:** converging on a made-up symmetric positive-definite system
is not this task. The system that matters is the one PISO actually
produces, and `docs/architecture/icds.md` records that when every
boundary prescribes velocity and none prescribes pressure -- the
lid-driven cavity, an MVP validation case -- **it is positive
*semi*-definite**, pressure being fixed only up to an additive constant.
This implementation must remove that null space (pin a reference cell,
or project the constant mode out each iteration). Stated as this task's
intent because it is a precondition on the MVP configuration, not a
future concern, and because a solver that converges on the easy system
and stalls on the real one passes every obvious test.

**Also intended:** non-convergence must remain distinguishable from a
converged answer, per the `LinearSolver` contract (TASK-022).

---

## TASK-027

PISO Pressure Coupling

**Intent:** the claim is that the corrected velocity field is
**divergence-free to a stated tolerance** -- computed and asserted, cell
by cell. Not "the pressure loop runs", not "the flow looks
incompressible".

---

## TASK-028

Dirichlet Boundary

**Intent:** the criterion is what the *interior scheme* computes at a
boundary face, not what the condition object returns when asked. A
condition can return the right face value and still be wired into the
flux computation wrongly; only the second is the thing anyone depends
on.

---

## TASK-029

Neumann Boundary

**Intent:** as TASK-028, for a prescribed **gradient** -- and the
zero-gradient case must not be the only one tested, since a
zero-gradient condition is also what a boundary that was silently
skipped entirely would produce.

---

## TASK-030

Periodic Boundary

**Intent:** the claim is that a field advected once around a periodic
domain returns to its starting distribution -- a round-trip invariant,
which is the only check that distinguishes a genuine wrapped-neighbour
lookup from a mirrored or clamped one at a single boundary.

Golden Demo

Passive scalar transport.

---

# Stage 5 — First Fluid Solver

Goal

Solve incompressible flow.

### Completion Criteria — due when this Stage opens, not now

Same reasoning as Stage 4's, above. This stage defines the MVP
(`docs/implementation/mvp.md`), so its criteria and `mvp.md`'s own
Definition of Done must be reconciled explicitly when they are written,
not assumed to agree.

**Executable acceptance criteria apply here in full**
(`adr/ADR-007-executable-acceptance-criteria.md`): every task below is
simulation work. TASK-034's own criteria are the sharpest test of the
form -- "the right instability emerges under the right configuration,
and does not emerge under a configuration where it should not" is a
pair of scenarios, and reads as one.

### Intent, recorded now

## TASK-031

Velocity Field Support

**Intent:** velocity is the first field the engine *transports* rather
than merely stores. The distinction worth a criterion is that nothing
here may special-case velocity -- Stage 6 adds four more transported
fields (TASK-035..038) on the claim that the architecture is
field-centric, and that claim is only testable if velocity went through
the same path they will.

---

## TASK-032

Pressure Field

**Intent:** pressure is *not* transported -- it is solved for, from the
incompressibility constraint. A criterion that treats it as another
advected scalar has misunderstood the task. See
`docs/handbook/numerical-methods/pressure-velocity-coupling.md`.

---

## TASK-033

Pressure Correction Loop

**Intent:** the loop's claim is that divergence **decreases
monotonically with each corrector iteration** and reaches the configured
tolerance -- measured across iterations, not asserted at the end. A loop
that reaches tolerance by luck on iteration one and diverges thereafter
passes an end-state check.

---

## TASK-034

Navier-Stokes Timestep

**Pause/rewind/replay, noted here as future scope (2026-08-20, raised by
the maintainer while scoping TASK-013's live zoom/pan):** not an
acceptance criterion of this task, but the natural place to build it once
a real timestepping loop exists here -- nothing before this task has one
to pause. Practical as a checkpoint-based design -- periodic full-state
snapshots plus deterministic replay between them, not storing every
frame, which gets expensive fast for field-rich simulations -- and it
leans directly on the determinism `docs/implementation/golden-demos.md`'s
Definition of Done already requires of every demo ("deterministic, or its
non-determinism is appropriately controlled"): replay-from-checkpoint is
only cheap if re-running the same steps reproduces the same state, which
is already a standing requirement, not a new one this would add. Revisit
when this task is actually scoped, not before -- recorded now only so the
idea isn't lost between this session and Stage 5.

**Intent:** this task's acceptance criteria already include emergent
phenomena -- "does the right instability emerge under the right
configuration" (`docs/planning/roadmap.md`'s own "Stages and Capability
Levels" note, 2026-08-20; `docs/planning/backlog.md`, "physical
correctness validation"). The qualifier to hold on to: **the right
phenomenon under the right configuration**, which means a
configuration under which it should *not* emerge must be tested too. An
instability that appears regardless of parameters is not the
instability.

Golden Demo

Lid-driven cavity.

This defines the MVP of PyFlow.

---

# Stage 6 — Additional Physical Fields

Goal

Demonstrate field-centric architecture.

### Completion Criteria — due when this Stage opens, not now

Same reasoning as Stage 4's, and **executable acceptance criteria apply
here in full** (`adr/ADR-007-executable-acceptance-criteria.md`) -- with
one thing worth noticing in advance. If this stage's goal holds, its
four tasks should need almost no new *steps*: adding a transported
field to a field-centric architecture ought to reuse Stage 4's
vocabulary nearly unchanged. **A large crop of new step definitions here
is itself evidence against the stage's own claim**, and worth reporting
as a finding rather than absorbing quietly.

One criterion is already determined by this stage's own goal and should
survive into them: **this stage's tasks must add no new machinery.** "Demonstrate field-centric architecture" is
falsified, not evidenced, by four tasks that each need engine changes to
land.

### Intent, recorded now

## TASK-035

Temperature

**Intent:** the first field added *after* the architecture claimed to be
field-centric, so the measure of success is how little else changes.
A criterion counting the lines this task adds outside `physics/` is a
legitimate and probably better test of the stage's goal than anything
about temperature itself.

**Also:** buoyancy coupling has a sign, and
`docs/handbook/physics/buoyancy.md` had it inverted in prose for days
before the 2026-08-18 review caught it. A "heat rises" direction check
is an acceptance criterion, not a nicety.

---

## TASK-036

Density

**Intent:** density enters the momentum equation, so unlike temperature
it is not a passive addition. The criterion that matters is whether a
variable-density configuration conserves mass, not whether the field
exists.

---

## TASK-037

Humidity

**Intent:** as TASK-035 -- a transported scalar whose value is mostly
that it needed no new machinery. If it does need new machinery, that is
the finding, and it belongs in the stage's exit audit rather than being
absorbed quietly.

---

## TASK-038

Passive Tracers

**Intent:** "passive" is the testable word: a tracer must have **no
measurable effect on the velocity field**. Checked by running the same
configuration with and without tracers and comparing the velocity field
exactly -- the only check that can fail.

Golden Demos

- Heat diffusion
- Smoke transport
- Thermal buoyancy

---

# Stage 7 — Better Numerics

Goal

Improve accuracy without changing architecture.

Tasks include

- TVD
- QUICK
- WENO
- Adaptive timestep
- Additional linear solvers
- Alternative pressure coupling

Golden Demo

Compare numerical schemes by changing configuration only.

---

# Stage 8 — Geometry

Goal

Support realistic domains.

Tasks include

- Internal obstacles
- Immersed boundaries
- Complex boundaries

Golden Demo

Flow around a cylinder.

---

# Stage 9 — Adaptive Resolution

Goal

Increase efficiency.

Tasks include

- Adaptive Mesh Refinement
- Error estimation
- Dynamic refinement

Golden Demo

Adaptive vortex refinement.

---

# Stage 10 — Additional Numerical Frameworks

Goal

Support numerical frameworks other than FVM where a problem is genuinely
better served by one.

**Read this before designing anything here.** The project's own survey
concluded that the headline case does not work the way this Stage's name
suggests. `docs/handbook/numerical-methods/compatibility.md`
("Combinations needing separate engines") finds that using a mesh-free
particle method as the *primary* solver for a large sub-domain, beside a
mesh-based one, means "hosting both as first-class citizens of one
shared internal architecture is impractical" -- production practice runs
each as a separate program exchanging state at coarse synchronisation
points. `adr/ADR-002-fvm-first.md` reached the compatible conclusion
from the other direction, leaving SPH and LBM "open as a possible future
alternative framework, not part of the core engine".

That does not make this Stage impossible; it makes one reading of it
impossible. The reading the handbook *does* support is the coupled one:
`compatibility.md` records "FVM (carrier phase) ↔ SPH or DEM (dispersed
phase)" under **Coupled methods**, for particle-laden, granular and
free-surface flow -- an embedded secondary method inside the existing
architecture, not a replacement for it. Scope this Stage that way, or
scope it as a genuinely separate engine with a defined co-simulation
boundary, and say which in the Stage's own acceptance criteria before
any task here is written.

Tasks include

- A framework-selection seam at construction, following
  `adr/ADR-003-modular-numerical-strategies.md`'s existing pattern
- One alternative framework implemented behind it (SPH the likeliest,
  per the survey)
- Coupling or co-simulation boundary between it and the FVM core
- Rendering for whatever representation the alternative framework uses

Golden Demo

Cross-framework comparison: the same problem solved by the FVM core and
by the alternative framework, compared. **Not** free-surface flow --
that capability arrives at Capability Level 10 (Advanced Physics,
"Multiphase flow"), a decision made alongside this one on 2026-08-21.
This Stage's demo has to demonstrate *the frameworks*, which a
side-by-side comparison does directly and a single free-surface scene
does not.

---

# Stage 11 — Three Dimensions

Goal

Generalise every existing capability.

Tasks include

- 3D mesh
- 3D fields
- 3D rendering
- 3D operators

Golden Demo

3D lid-driven cavity.

---

# Stage 12 — Performance

Goal

Scale PyFlow.

Tasks include

- GPU execution
- Multi-threading
- MPI
- Performance profiling

Golden Demo

Performance benchmark suite.

---

# Stage 13 — Advanced Physics

Goal

Extend PyFlow beyond classical CFD.

Possible capabilities

- Cloud formation
- Rain
- Combustion
- Radiation
- Multiphase flow
- Electromagnetics

Each capability should build upon the existing engine wherever possible rather than introducing new execution paths.
