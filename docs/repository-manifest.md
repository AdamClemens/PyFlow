# Repository Manifest

**Status:** Draft v0.2 (rewritten 2026-08-15)

## Purpose

This document is the inventory of maintained artifacts in the PyFlow
repository: what exists, where, what it is for, and how complete it is.

It tracks repository *knowledge*. It does not track software
functionality -- that is `docs/planning/roadmap.md` -- and it does not
specify what each artifact must contain -- that is
`docs/planning/knowledge-architecture.md` (the "KA" references below).
This document answers "what is in the repository and how done is it";
the KA spec answers "what should this artifact say."

Every maintained file should appear here exactly once, either as its own
row or under an explicitly stated collective rule.

**Open question:** whether this document should be hand-maintained at all.
A file inventory with statuses is an obvious generation candidate under
P-002 ("everything that can reasonably be generated should be
generated"), and hand-maintenance has already failed once -- v0.1 drifted
badly enough that it described roughly 35 handbook files that never
existed while omitting most of the repository. It was rewritten by hand
on 2026-08-15 to stop it misleading readers, which does not settle the
question. See `docs/planning/backlog.md`.

---

# Legend

- ⬜ Not Started -- file does not exist, or exists and is empty
- 🟨 Draft -- purpose defined, structure stable, core content present
- 🟩 Complete -- satisfies the documentation Definition of Done

Completeness is judged relative to the current project phase.

The Definition of Done for documentation is defined once, in
`docs/documentation-guidelines.md`. It is not restated here.

---

# Root

| File | Status | Purpose |
|------|--------|---------|
| README.md | 🟩 | Project overview and entry point; Quick Start section added 2026-08-15 (E11), kept current as functionality is added per `docs/practices.md` |
| CLAUDE.md | 🟨 | Root instructions for coding agents (KA-037) |
| LICENSE | 🟩 | Project licence (BSD-3-Clause) |
| pyproject.toml | 🟩 | Python project definition; `pyflow` package exists (B1); runtime dependencies (`torch`, `pygfx`) declared and locked per ADR-004/005 |
| Makefile | 🟩 | All eight targets verified working; `docs` correctly still a placeholder |
| uv.lock | 🟩 | Committed 2026-08-15; 62 packages resolved |
| .python-version | 🟩 | `3.14`, added 2026-08-15 per the Python version policy |
| .gitignore | 🟩 | Ignored paths |
| .gitattributes | 🟩 | Line-ending normalisation; verified via `git ls-files --eol` immediately after the first commit |
| .editorconfig | 🟩 | Editor conventions |
| .pre-commit-config.yaml | 🟩 | Hook configuration; run for real 2026-08-15 (B4) -- fixed two files on first run, clean on second |

Not present, deferred consciously rather than overlooked:
`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.

---

# docs/

## Core

| File | Status | Purpose |
|------|--------|---------|
| repository-manifest.md | 🟨 | This file -- inventory of maintained artifacts |
| engineering-principles.md | 🟨 | Long-term engineering philosophy (KA-002) |
| practices.md | 🟨 | Day-to-day development practices (KA-003) |
| documentation-guidelines.md | 🟨 | Documentation standards, incl. the documentation DoD (KA-004) |
| glossary.md | 🟨 | Project terminology (KA-005) |
| CHANGELOG-DESIGN.md | 🟨 | Append-only design decision history |

---

## docs/planning/

| File | Status | Purpose |
|------|--------|---------|
| knowledge-architecture.md | 🟨 | Specification of every planned knowledge artifact |
| roadmap.md | 🟨 | **Authoritative for execution**: stages, TASK-XXX, acceptance criteria |
| implementation-plan.md | 🟨 | Long-range capability-level vision, Levels 0-10 (KA-033) |
| capability-map.md | 🟨 | High-level project capabilities (KA-006) |
| backlog.md | 🟨 | Ordered Stage 0 work queue, deferred work, and audit history |
| dependency-tree.md | 🟨 | Hand-maintained engine subsystem dependency tree |
| dreams.md | 🟨 | Speculative future ideas, explicitly not commitments (KA-036) |
| releases.md | ⬜ | Empty. Deferred -- KA has no releases entry to build from |

---

## docs/architecture/

| File | Status | Purpose |
|------|--------|---------|
| engine.md | ⬜ | Conceptual engine architecture (KA-029) |
| icds.md | ⬜ | Interface Contract Definitions (KA-030) |
| overview.md | ⬜ | Architecture overview -- no KA entry; legitimate but unspecified |
| rendering.md | ⬜ | Architecture of the adopted renderer -- no KA entry |
| repository.md | ⬜ | Repository architecture -- no KA entry |
| compute-and-rendering-stack.md | 🟨 | Survey and compatibility matrix for array-library × renderer combinations; decision-support for the stack ADRs. Class question (A2b) resolved via `ADR-004`; A2c (instance) narrowed to CuPy-vs-PyTorch and wgpu/pygfx-vs-VisPy as of 2026-08-15, not yet decided |

`engine.md`, `icds.md`, `overview.md`, `rendering.md` and `repository.md`
are empty. `engine.md` and `icds.md` block ICD-dependent work.
`rendering.md` describes the renderer actually adopted and so cannot be
written until the stack decisions land; `compute-and-rendering-stack.md`
is the survey that informs them (now a first draft), and is deliberately
a separate document because it covers both axes.

---

## docs/handbook/

Scientific and engineering reference knowledge. Explains the domain;
does not describe PyFlow's implementation of it.

### numerical-methods/ (KA-016..025, plus KA-007/008)

| File | Status | Purpose |
|------|--------|---------|
| overview.md | 🟨 | Numerical method survey -- eight method families (KA-007) |
| compatibility.md | 🟨 | Which methods combine, and in what sense (KA-008) |
| fvm.md | ⬜ | Finite Volume Method (KA-016) -- the one to write first |
| meshes.md | ⬜ | Mesh concepts (KA-017) |
| variable-placement.md | ⬜ | Collocated vs. staggered (KA-018) |
| fluxes.md | ⬜ | Numerical fluxes (KA-019) |
| advection.md | ⬜ | Advection discretisation (KA-020) |
| diffusion.md | ⬜ | Diffusion discretisation (KA-021) |
| time-integration.md | ⬜ | Explicit and implicit integration (KA-022) |
| pressure-velocity-coupling.md | ⬜ | PISO/SIMPLE/SIMPLEC (KA-023) |
| linear-solvers.md | ⬜ | CG, BiCGSTAB, multigrid (KA-024) |
| boundary-conditions.md | ⬜ | Dirichlet, Neumann, periodic, Robin (KA-025) |

`overview.md` and `compatibility.md` were moved here from
`docs/planning/numerical-frameworks.md` on 2026-08-15 and split; that
path no longer exists.

### physics/ (KA-009..015)

| File | Status | Purpose |
|------|--------|---------|
| README.md | 🟨 | Handbook structure and entry conventions (KA-009) |
| incompressible-flow.md | ⬜ | Incompressible flow (KA-010) |
| heat-transfer.md | ⬜ | Heat transport (KA-011) |
| density.md | ⬜ | Density (KA-012) |
| humidity.md | ⬜ | Humidity and species transport (KA-013) |
| buoyancy.md | ⬜ | Buoyancy (KA-014) |
| cloud-formation.md | ⬜ | Cloud formation (KA-015) |

There is no `docs/handbook/README.md` and no
`numerical-methods/README.md`; only `physics/` has a structural README,
because only KA-009 specifies one.

---

## docs/implementation/

| File | Status | Purpose |
|------|--------|---------|
| mvp.md | 🟨 | **Authoritative** MVP definition (KA-031) |
| upgrade-paths.md | 🟨 | How each MVP component can be replaced or extended (KA-032) |
| golden-demos.md | 🟨 | What each golden demo must do and how it is verified (KA-035) |

`docs/implementation/stages/stage-0.md` (KA-034) does not exist and will
not be written. KA-034 was marked `superseded` on 2026-08-15:
`roadmap.md`'s Stage 0 section is the specification, and
`docs/planning/backlog.md` Part I is the queue that executes it. The two
Definition-of-Done items unique to KA-034 were promoted into
`roadmap.md`'s Stage 0 Completion Criteria first, so nothing was lost.
There is consequently no `stages/` subdirectory here, and none is
planned -- per-stage specifications live in `roadmap.md`.

---

## docs/references/

| File | Status | Purpose |
|------|--------|---------|
| books.md | ⬜ | Book references |
| papers.md | ⬜ | Paper references |
| websites.md | ⬜ | Web references |

All empty. Blocked on handbook content -- populate alongside it, not
before.

---

## docs/tutorials/

Empty of content. Reserved for written tutorials; runnable tutorial code
belongs in `examples/tutorials/`.

---

# adr/

| File | Status | Purpose |
|------|--------|---------|
| README.md | 🟩 | ADR conventions, lifecycle, numbering |
| ADR-001-knowledge-graph.md | 🟩 | Capability/knowledge graph architecture (KA-026) |
| ADR-002-fvm-first.md | 🟨 | Initial numerical method selection (KA-027) |
| ADR-003-modular-numerical-strategies.md | 🟩 | Strategy-based numerical engine (KA-028) |
| ADR-004-compute-rendering-class.md | 🟩 | Class 2 (GPU arrays, NumPy-shaped, general renderer) chosen over Taichi/Warp -- decides the *class* only |
| ADR-005-compute-rendering-instances.md | 🟩 | PyTorch (array library) and wgpu/pygfx (renderer) chosen within Class 2 |

ADR-002 is 🟨 rather than 🟩 deliberately: its rationale was drafted from
general CFD domain knowledge rather than from recorded project-specific
reasoning, and has not been reviewed against
`docs/handbook/numerical-methods/overview.md` (which it now cites). See
`docs/planning/backlog.md`.

ADRs use `adr/ADR-00N-title.md`, not the `docs/adr/ADR-000N-*.md` path
the KA spec originally named; the KA entries were corrected to match on
2026-08-15.

---

# prompts/

| File | Status | Purpose |
|------|--------|---------|
| global/project.md | 🟨 | Durable project-wide agent context (KA-039) |
| common/TEMPLATE.md | 🟩 | Reusable task-prompt structure |
| common/task-*.md | 🟩 | Four instantiated task prompts; retained as a record of what was asked |
| features/handbook.md | ⬜ | Handbook generation guidance (KA-040) |
| features/adr.md | ⬜ | ADR generation guidance (KA-041) |
| features/implementation-plan.md | ⬜ | Task generation guidance (KA-042) |
| features/agents.md | ⬜ | CLAUDE.md generation guidance (KA-043) |

The four `features/` files do not exist yet. KA-040..043 define exactly
these four; there is no `features/documentation.md`.

---

# planning/

Machine-readable knowledge graph: `model/{schema,entities,relationships,
validation}.yaml` and `data/{capabilities,components,concepts,demos,
features,references,releases}.yaml`.

All eleven files exist and are empty. ⬜ — intentionally deferred, not
overlooked: populating the graph is downstream of having real handbook
and ADR content to populate it with.

---

# src/

`src/pyflow/` with subpackages `engine/`, `physics/`, `rendering/`,
`configuration/`.

🟨 — **package skeleton exists (roadmap TASK-000, done 2026-08-15).** Six
`__init__.py`/`__main__.py` files, docstring-only, no implementation.
Imports successfully, `python -m pyflow` executes, `ruff check` and
`mypy --strict` both pass -- all verified directly, not assumed.
Implementation progress is tracked by `roadmap.md`, not by this
manifest; this note exists so a reader isn't left assuming the package
is either empty or complete.

---

# tests/

`tests/` with `unit/`, `integration/`, `golden/`, `performance/`.

🟨 — one real test (`integration/test_cli.py`, C1a, 2026-08-15),
`unit/`, `golden/`, `performance/` still empty. No coverage
configuration yet (C1b). Roadmap TASK-003, partial.

---

# examples/

`examples/` with `golden-demos/`, `tutorials/`, `experiments/`.

⬜ — directories only, no runnable code. Named `examples/` rather than
the roadmap's original `demos/` because it holds more than demos; the
roadmap was updated to match on 2026-08-15.

---

# tools/

`tools/` with `generators/`, `planner/`, `validators/`, `scripts/`.

⬜ — empty, and no document states what any of them is for. Either
document the intent or retire them; see `docs/planning/backlog.md`.

---

# assets/

`assets/` with `colourmaps/`, `icons/`, `shaders/`, `textures/`.

⬜ — empty. Expected to fill during rendering work (roadmap TASK-007
onward).

---

# .github/

`.github/workflows/` exists but contains no workflow definition. ⬜ —
roadmap TASK-004 (Continuous Integration), unstarted.

---

# CLAUDE.md files

**Collective rule:** every directory in the repository has a `CLAUDE.md`.
They are tracked collectively here, not as individual rows, because
per-directory agent guidance is a property of the directory rather than a
standalone artifact (KA-038).

As of 2026-08-15: 45 files exist; 29 are still the generic placeholder
and 16 carry real local content. The root `CLAUDE.md` permits the
placeholder only until something specific is known about a directory --
for several of these, something specific is already known and written
down elsewhere. See `docs/planning/backlog.md`.

---

# Maintenance Rules

Whenever a maintained artifact is added, moved, or its status changes:

1. Update this manifest.
2. Update the corresponding `Name:` / `Status:` in
   `docs/planning/knowledge-architecture.md` if the artifact has a KA
   entry. These two documents describe the same artifacts from different
   angles and drift apart if only one is updated -- which is exactly how
   v0.1 of this file decayed.
3. Link it from any appropriate index.
4. Update the nearest `CLAUDE.md` with concrete maintenance guidance.
5. Update any affected documentation.
