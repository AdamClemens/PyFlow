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

For the definitions of Stage, Capability Level and Release, see
`docs/glossary.md`.

---

# Stage 0 — Engineering Infrastructure

## Goal

Establish the engineering environment required to support long-term, maintainable development of PyFlow.

Stage 0 intentionally contains no CFD functionality. Its purpose is to ensure that all subsequent development occurs within a consistent, automated, reproducible and well-documented engineering environment.

Completion of Stage 0 should allow a developer or coding agent to clone the repository and immediately begin implementing Stage 1.

### Status as of 2026-08-15

Stage 0 is in progress and substantially incomplete. The planning and
documentation groundwork is well advanced; the engineering environment is
not.

| Task | Status |
|------|--------|
| TASK-000 Engine Skeleton | **Done** 2026-08-15 -- `pyflow` package with `engine/physics/rendering/configuration`; imports, `python -m pyflow`, ruff and mypy --strict all verified passing |
| TASK-001 Development Environment | **Done** 2026-08-15 -- `uv.lock` and `.python-version` committed; `make install` → `clean` → `install` verified round-trip |
| TASK-002 Build System | **Done** 2026-08-15 -- all targets run for real (twelve as of 2026-08-18's advisory `check-claims`, on top of 2026-08-17's `check-docs`/`check-docs-index`); `lint` now runs the full pre-commit suite, `clean` states what it can't remove and why, new `ci` target added; `docs` is no longer a placeholder -- it regenerates `docs/index.md`, and `check-docs-index` fails CI if that file is stale |
| TASK-003 Automated Testing | **Done** 2026-08-16 -- coverage configured (`pytest-cov`), `make test` reports coverage; `unit/` and `golden/` now have real tests (D1-D5), only `performance/` remains empty, correctly (nothing to benchmark yet) |
| TASK-004 Continuous Integration | **Written, scope deliberately deferred** 2026-08-16 -- `.github/workflows/ci.yml` runs `make ci` on Linux + Windows, on push and pull request. Locally validated only (YAML parses, `make lint`'s `check-yaml` hook passes, mirrors the exact `make ci` sequence already proven to pass): the repository has no remote yet, so the workflow has never actually executed on a GitHub Actions runner. **Maintainer's call, 2026-08-16:** verifying it on a real runner is deferred until a 2D demo exists -- development stays local until then anyway, so "the CI pipeline" is understood to mean `make ci` / the local test suite for now, not a claim that GitHub Actions has run it. TASK-004's literal acceptance criterion ("every pull request executes the validation pipeline automatically") stays open until a remote exists and a real PR runs it -- deferred, not silently dropped. |
| TASK-005 Configuration Framework | **Done** 2026-08-16 -- YAML loading (`pyyaml`) into validated dataclasses (`PyFlowConfig`); `PyFlowConfig()` alone is a complete, valid default |
| TASK-006 Logging Framework | **Done** 2026-08-16 -- stdlib `logging`, centralised on the `pyflow` logger; every subsystem gets its logger via `get_logger(__name__)` and inherits level/formatting through the hierarchy |
| TASK-007 Rendering Framework | **Done** 2026-08-16 -- wgpu/pygfx (`adr/ADR-005`) window creation, render loop, clean shutdown; canvas backend (glfw interactive / offscreen headless) selected via configuration, both behind one interface (`src/pyflow/rendering/canvas.py`) |
| TASK-008 Repository Documentation | **Done** -- this row previously read "Partial -- core documents drafted; the Handbook is largely empty", stale since 2026-08-17 when all sixteen Handbook entries (E3/E4) were written; corrected 2026-08-19. All nine artifacts TASK-008 names (README, Handbook, ADRs, Capability Map, Implementation Plan, Engineering Principles, Documentation Guidelines, Practices, Dreams) exist with real content, verified directly by line count, not assumed |
| TASK-009 CLAUDE.md Hierarchy | **Done** 2026-08-19 -- 42 files exist (up from 40: F2 found `.claude/` and `.claude/hooks/` had no `CLAUDE.md` at all and were untracked by both inventories, fixed with real content, not placeholders; 40 itself down from 43: `assets/icons/`, `assets/shaders/`, `assets/textures/` retired 2026-08-19, E9, no document anywhere having ever stated what they were for, the same test that retired `tools/planner/`/`tools/scripts/`, 2026-08-17, E10; 43 itself down from 45 for that earlier retirement); 7 are still generic placeholders, 35 carry real content. E9's *Done when* was revised the same day it closed: no placeholder may remain in a directory that has content, not no placeholder anywhere -- all 7 remaining sit in directories with no real content yet (empty, or a bare docstring-only `__init__.py`), verified directly. `docs/planning/backlog.md` E9/F2 hold the file-by-file breakdown and are the authoritative count |
| TASK-010 Engine Bootstrap | **Done** 2026-08-16 -- `pyflow run` loads configuration, initialises logging, opens the render window, runs the loop, exits cleanly; verified with both the offscreen backend (automated, `tests/integration/test_bootstrap.py`) and the real interactive glfw backend (manual run, a real window opened and closed cleanly). `make ci`'s pass is what TASK-010 means by "the CI pipeline passes" here, per the C2 scope decision above -- not a claim that GitHub Actions itself has run it |

This paragraph previously said `make install` and `make test` were still
expected to fail, pending `uv.lock` and a test suite (B2/C1) -- stale
since 2026-08-16 and corrected 2026-08-19. Both now succeed: `uv.lock`
is committed (B2) and `make test` runs 64 tests with coverage (C1a/C1b).
All `make ci` targets (`lint`, `typecheck`, `test`, `check-docs`,
`check-docs-index`) pass, verified via the Makefile itself, not only via
`uv tool run` in isolation.

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
  `docs/planning/backlog.md` Part II.
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

---

# Stage 1 — Representing Space

Goal

Represent the simulation domain.

## TASK-011

Coordinate System

Implement

- Physical coordinates
- Grid spacing
- Index conversions
- Coordinate transforms

Depends on

None

---

## TASK-012

Structured Cartesian Mesh

Implement

- Uniform Cartesian grid
- Cell indexing
- Neighbour lookup
- Boundary identification

Depends on

TASK-011

---

## TASK-013

Mesh Visualiser

Implement

- Draw grid
- Display cell boundaries
- Zoom
- Pan

Depends on

TASK-012

Golden Demo

Display an empty computational mesh.

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

---

## TASK-015

Scalar Field

Implement

- Cell-centred storage
- Read/write access
- Initialisation
- Copy

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
