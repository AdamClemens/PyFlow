# PyFlow Execution Roadmap

This roadmap defines the chronological implementation order of PyFlow.

Each milestone produces a working engine that demonstrates one new capability. Existing functionality must continue to work throughout development.

This document is authoritative for execution: what to work on next, in
what order, and what "done" means for it (Purpose / Dependencies /
Artifacts / Implementation / Acceptance Criteria per task).

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
| *(none)* | **7 — Additional Numerical Frameworks** |
| 10 — Three Dimensions | 8 — Three-Dimensional Simulation |
| 11 — Performance | 9 — High Performance Computing |
| 12 — Advanced Physics | 10 — Advanced Physics |

**Known divergence:** Capability Level 7 (SPH/FLIP/PIC, golden demo
"free-surface flow") has no corresponding Stage, so the plan's "Dam
Break / Free Surface" golden demo is currently unreachable from this
roadmap. Whether to add a Stage for it or drop the Level is an open
decision -- see `docs/planning/backlog.md`. It is recorded here rather
than silently reconciled because either answer is a real scope change.

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
| TASK-009 CLAUDE.md Hierarchy | **Done** 2026-08-19 -- 42 files exist (up from 40: F2 found `.claude/` and `.claude/hooks/` had no `CLAUDE.md` at all and were untracked by both inventories, fixed with real content, not placeholders; 40 itself down from 43: `assets/icons/`, `assets/shaders/`, `assets/textures/` retired 2026-08-19, E9, no document anywhere having ever stated what they were for, the same test that retired `tools/planner/`/`tools/scripts/`, 2026-08-17, E10; 43 itself down from 45 for that earlier retirement); 7 are still generic placeholders, 35 carry real content. E9's *Done when* was revised the same day it closed: no placeholder may remain in a directory that has content, not no placeholder anywhere -- all 7 remaining sit in directories with no real content yet (empty, or a bare docstring-only `__init__.py`), verified directly. `docs/planning/backlog.md` E9/F2 hold the file-by-file breakdown and are the authoritative count |
| TASK-010 Engine Bootstrap | **Done** 2026-08-16 -- `pyflow run` loads configuration, initialises logging, opens the render window, runs the loop, exits cleanly; verified with both the offscreen backend (automated, `tests/integration/test_bootstrap.py`) and the real interactive glfw backend (manual run, a real window opened and closed cleanly). `make ci`'s pass is what TASK-010 means by "the CI pipeline passes" here, per the C2 scope decision above -- not a claim that GitHub Actions itself has run it |

This paragraph previously said `make install` and `make test` were still
expected to fail, pending `uv.lock` and a test suite (B2/C1) -- stale
since 2026-08-16 and corrected 2026-08-19. Both now succeed: `uv.lock`
is committed (B2) and `make test` runs the suite with coverage
(C1a/C1b): 202 tests at 99% as of 2026-08-21, having been 64 when this
paragraph was rewritten on 2026-08-19. All `make ci` targets (`lint`,
`typecheck`, `test`, `check-docs`, `check-docs-index`) pass, verified
via the Makefile itself, not only via `uv tool run` in isolation.

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

## TASK-014

Field Interface

Implement

- Abstract Field interface
- Common operations
- Metadata
- Mesh association

**Same interface-first pattern as TASK-011/TASK-012** (maintainer's
call, 2026-08-20): the `Field` interface deliberately does not assume
collocated storage, matching `docs/architecture/engine.md`'s own
Variables contract ("a common `Field` abstraction... shared by every
physical quantity... regardless of arrangement") and its upgrade path
(collocated → alternative placement schemes, e.g. staggered).
`CollocatedField` (TASK-015/016) is the first concrete implementation; a
shared contract test suite covers what every `Field` must satisfy
regardless of placement. Same caveat as TASK-012: this is internal
engineering discipline, not a formal ICD -- `icds.md` still doesn't
document Variables, per `ADR-003`'s unchanged scope.

---

## TASK-015

Scalar Field

Implement

- Cell-centred storage
- Read/write access
- Initialisation
- Copy

**"Initialisation" must support a non-uniform, patterned initial
condition, not only a single uniform value** (noted 2026-08-20,
`docs/planning/backlog.md` "physical correctness validation"). Later
validation golden demos depend on this directly: Taylor-Green vortex
needs each cell initialised to a specific analytical function of its
position; Kelvin-Helmholtz instability and Rayleigh-Bénard convection
need two distinct regions or a gradient, not a constant. Write this into
this task's own acceptance criteria when it's reached, rather than
discovering the gap only once Level 2's demos need it.

**Mechanism decided 2026-08-20 (maintainer's call): general
callable/expression-based, not a fixed set of named presets.** A field
initialises from any function of a cell's position, not a closed list of
patterns ("step", "gradient", ...). Directly what Taylor-Green vortex
needs (each cell set to a specific analytical function, not one this
task's author could have anticipated as a named preset), and Poiseuille
flow's parabolic profile, Kelvin-Helmholtz's shear layer, and
Rayleigh-Bénard's temperature gradient are all expressible as one too --
supports every validation demo named so far and whatever comes later,
without needing this task revisited each time a new demo needs a shape
nobody thought to name in advance.

Depends on

TASK-014

---

## TASK-016

Vector Field

Implement

- Multiple components
- Component access
- Magnitude
- Visualisation support

Depends on

TASK-014

---

## TASK-017

Field Rendering

Implement

- Scalar colour maps
- Vector arrows
- Legends

Golden Demo

Display scalar and vector fields.

---

# Stage 3 — Numerical Engine

Goal

Create the interchangeable numerical architecture.

## TASK-018

Operator Interfaces

Define interfaces for

- Advection
- Diffusion
- Gradient
- Divergence
- Source terms

No implementations yet.

---

## TASK-019

Boundary Condition Interface

Implement interface only.

---

## TASK-020

Time Integrator Interface

Implement interface only.

---

## TASK-021

Pressure Coupling Interface

Implement interface only.

**Real cross-layer dependency on TASK-022, found 2026-08-20:**
`docs/architecture/icds.md`'s Pressure-Velocity Coupling ICD states this
directly -- "requires a configured Linear Solver to solve the
pressure-correction equation it produces each timestep... the one real
cross-layer dependency among the six [ADR-003 components]." Not a hard
build-order dependency the way TASK-012 needs TASK-011's actual class to
exist (an interface's method signature can reference a `LinearSolver`
type before that interface has a concrete implementation) -- but design
TASK-021's interface with TASK-022's shape already in mind, not in
ignorance of it, since every other one of the six is independent of the
others' choice and this is the sole exception.

---

## TASK-022

Linear Solver Interface

Implement interface only.

Golden Demo

Engine initialises entirely through interfaces.

No CFD yet.

---

# Stage 4 — First Numerical Methods

Goal

Implement the simplest valid implementation of every interface.

## TASK-023

First-order Upwind Advection

---

## TASK-024

Central Difference Diffusion

---

## TASK-025

RK4 Time Integration

---

## TASK-026

Conjugate Gradient Solver

---

## TASK-027

PISO Pressure Coupling

---

## TASK-028

Dirichlet Boundary

---

## TASK-029

Neumann Boundary

---

## TASK-030

Periodic Boundary

Golden Demo

Passive scalar transport.

---

# Stage 5 — First Fluid Solver

Goal

Solve incompressible flow.

## TASK-031

Velocity Field Support

---

## TASK-032

Pressure Field

---

## TASK-033

Pressure Correction Loop

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

Golden Demo

Lid-driven cavity.

This defines the MVP of PyFlow.

---

# Stage 6 — Additional Physical Fields

Goal

Demonstrate field-centric architecture.

## TASK-035

Temperature

---

## TASK-036

Density

---

## TASK-037

Humidity

---

## TASK-038

Passive Tracers

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

# Stage 10 — Three Dimensions

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

# Stage 11 — Performance

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

# Stage 12 — Advanced Physics

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
