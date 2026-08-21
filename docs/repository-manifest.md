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
| CLAUDE.md | 🟩 | Root instructions for coding agents (KA-037); Development Commands section added 2026-08-17 (E13) |
| LICENSE | 🟩 | Project licence (BSD-3-Clause) |
| pyproject.toml | 🟩 | Python project definition; `pyflow` package exists (B1); runtime dependencies `torch`/`pygfx` per ADR-004/005, plus `pyyaml` (D1, config loading) and `glfw` (D3, interactive render window), all locked |
| Makefile | 🟩 | All twelve targets verified working; `check-docs-index` added 2026-08-17 alongside `docs`, which is no longer a placeholder -- it now regenerates `docs/index.md`; advisory `check-claims` added 2026-08-18, deliberately outside `ci` |
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
| index.md | 🟩 | **Generated** navigable map of every documentation page, by directory (`tools/generators/generate_docs_index.py`, added 2026-08-17); regenerate with `make docs`, never hand-edit |
| engineering-principles.md | 🟨 | Long-term engineering philosophy (KA-002) |
| practices.md | 🟩 | Day-to-day development practices (KA-003); Version Control section and tooling dependency update policy added 2026-08-19 (F1) |
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
| dependency-tree.md | 🟩 | **Generated** engine subsystem dependency order, from `planning/data/components.yaml` (`tools/generators/generate_dependency_tree.py`, 2026-08-21); regenerate with `make dependency-tree`, never hand-edit |
| dreams.md | 🟨 | Speculative future ideas, explicitly not commitments (KA-036) |
| releases.md | 🟨 | No release process yet -- deliberate deferral, not an oversight, with concrete trigger conditions recorded (E7, 2026-08-17) |

---

## docs/architecture/

| File | Status | Purpose |
|------|--------|---------|
| engine.md | 🟨 | Conceptual engine architecture (KA-029) |
| icds.md | 🟨 | Interface Contract Definitions (KA-030) |
| overview.md | 🟩 | Top-level system map -- no KA entry; legitimate but unspecified |
| rendering.md | 🟩 | Architecture of the adopted renderer -- no KA entry |
| repository.md | 🟩 | Repository architecture -- no KA entry |
| compute-and-rendering-stack.md | 🟨 | Survey and compatibility matrix for array-library × renderer combinations; decision-support for the stack ADRs. Both questions it exists to support are decided: the class (A2b) via `ADR-004`, the instances (A2c, PyTorch + wgpu/pygfx) via `ADR-005`, both 2026-08-15. It remains the record of why, and of the options not taken. (This row read "not yet decided" for A2c until 2026-08-18 -- stale since the day it was written, since `ADR-005` landed the same day.) |

`engine.md` and `icds.md` written 2026-08-17 (`docs/planning/backlog.md`
E1a/E1b) -- 🟨 rather than 🟩 since both describe target architecture for
layers that don't exist as code yet (Stage 1-4), and `icds.md`'s
`numerics.*` configuration keys are explicitly proposed, not implemented.
`overview.md`, `rendering.md` and `repository.md` written 2026-08-17
(E2a/E2b/E2c) -- 🟩, since all three describe things that already exist
(the current system shape, the already-implemented renderer, the
repository's actual current layout), unlike `engine.md`/`icds.md`'s
necessarily forward-looking content. `compute-and-rendering-stack.md` is
the decision-support survey that informed `rendering.md`, and remains a
separate document because it covers both the array-library and renderer
axes together.

---

## docs/handbook/

Scientific and engineering reference knowledge. Explains the domain;
does not describe PyFlow's implementation of it.

### numerical-methods/ (KA-016..025, plus KA-007/008)

| File | Status | Purpose |
|------|--------|---------|
| overview.md | 🟨 | Numerical method survey -- eight method families (KA-007) |
| compatibility.md | 🟨 | Which methods combine, and in what sense (KA-008) |
| fvm.md | 🟨 | Finite Volume Method (KA-016) |
| meshes.md | 🟨 | Mesh concepts (KA-017) |
| variable-placement.md | 🟨 | Collocated vs. staggered (KA-018) |
| fluxes.md | 🟨 | Numerical fluxes (KA-019) |
| advection.md | 🟨 | Advection discretisation (KA-020) |
| diffusion.md | 🟨 | Diffusion discretisation (KA-021) |
| time-integration.md | 🟨 | Explicit and implicit integration (KA-022) |
| pressure-velocity-coupling.md | 🟨 | PISO/SIMPLE/SIMPLEC (KA-023) |
| linear-solvers.md | 🟨 | CG, BiCGSTAB, GMRES, multigrid (KA-024) |
| boundary-conditions.md | 🟨 | Dirichlet, Neumann, periodic, Robin (KA-025) |

`overview.md` and `compatibility.md` were moved here from
`docs/planning/numerical-frameworks.md` on 2026-08-15 and split; that
path no longer exists. The ten KA-016..025 entries were written
2026-08-17 (`docs/planning/backlog.md` E3), each with real technical
content and citations.

### physics/ (KA-009..015)

| File | Status | Purpose |
|------|--------|---------|
| README.md | 🟨 | Handbook structure and entry conventions (KA-009) |
| incompressible-flow.md | 🟨 | Incompressible flow (KA-010) |
| heat-transfer.md | 🟨 | Heat transport (KA-011) |
| density.md | 🟨 | Density (KA-012) |
| humidity.md | 🟨 | Humidity and species transport (KA-013) |
| buoyancy.md | 🟨 | Buoyancy (KA-014) |
| cloud-formation.md | 🟨 | Cloud formation (KA-015) |

All six written 2026-08-17 (`docs/planning/backlog.md` E4), each with
real content and citations. There is no `docs/handbook/README.md` and no
`numerical-methods/README.md`; only `physics/` has a structural README,
because only KA-009 specifies one.

---

## docs/implementation/

| File | Status | Purpose |
|------|--------|---------|
| mvp.md | 🟨 | **Authoritative** MVP definition (KA-031) |
| upgrade-paths.md | 🟨 | How each MVP component can be replaced or extended (KA-032) |
| golden-demos.md | 🟩 | What each golden demo must do and how it is verified (KA-035); Empty Window (D5, 2026-08-16) was the first demo actually built, Empty Mesh (TASK-013, 2026-08-20) the second |

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
| books.md | 🟨 | Book references |
| papers.md | 🟨 | Paper references |
| websites.md | 🟨 | Web references |

Populated 2026-08-17 (`docs/planning/backlog.md` E6) from what the
sixteen Handbook entries written the same session (E3/E4) actually cite.
`websites.md` has no entries yet -- every citation so far is a book or
paper -- and says so explicitly.

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
| ADR-002-fvm-first.md | 🟩 | Initial numerical method selection (KA-027) |
| ADR-003-modular-numerical-strategies.md | 🟩 | Strategy-based numerical engine (KA-028) |
| ADR-004-compute-rendering-class.md | 🟩 | Class 2 (GPU arrays, NumPy-shaped, general renderer) chosen over Taichi/Warp -- decides the *class* only |
| ADR-005-compute-rendering-instances.md | 🟩 | PyTorch (array library) and wgpu/pygfx (renderer) chosen within Class 2 |

ADR-002 was reviewed against `docs/handbook/numerical-methods/overview.md`
2026-08-17 (`docs/planning/backlog.md` E12): its rationale was originally
drafted from general CFD domain knowledge, before the survey existed to
supply project-specific reasoning, but no factual claim was found to
contradict it. The one real gap -- the survey's own per-method
"Suitability for PyFlow" verdicts and field-transport ratings were
available but not cited -- was closed in the same change.

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
| features/handbook.md | 🟨 | Handbook generation guidance (KA-040) |
| features/adr.md | 🟨 | ADR generation guidance (KA-041) |
| features/implementation-plan.md | 🟨 | Task generation guidance (KA-042) |
| features/agents.md | 🟨 | CLAUDE.md generation guidance (KA-043) |

All four `features/` files were written 2026-08-17 (`docs/planning/backlog.md`
E8). KA-040..043 define exactly these four; there is no
`features/documentation.md`.

---

# planning/

Machine-readable knowledge graph: `model/{schema,entities,relationships,
validation}.yaml` and `data/{capabilities,components,concepts,demos,
features,references,releases}.yaml`.

🟨 — **seven of eleven files hold content (2026-08-21).** All four
`model/` files, plus `data/components.yaml` (the nine engine layers),
`data/capabilities.yaml` (the eleven capability levels) and
`data/demos.yaml` (fourteen golden demos). Validated by
`make check-graph`, which is part of `make ci`;
`docs/planning/dependency-tree.md` is generated from
`data/components.yaml`.

The remaining four `data/` files are empty **on purpose, each with a
stated trigger in `model/entities.yaml`** -- not deferred-and-forgotten,
which is what this row used to describe. `releases.yaml` in particular
should be expected to stay empty indefinitely:
`docs/planning/releases.md` is a sustained argument that PyFlow should
not have a release process yet, and a file matching a documented
deliberate absence is correct rather than incomplete.

Scope is `adr/ADR-006-knowledge-graph-scope.md`, which narrowed
`adr/ADR-001-knowledge-graph.md` after the 2026-08-21 audit found it
describing a repository that did not exist. The short version: the graph
holds entities and relationships, prose holds reasoning and is never
generated. This row previously read "All eleven files exist and are
empty" with a deferral reason whose unblock condition had already passed
four days earlier.

---

# src/

`src/pyflow/` with subpackages `engine/`, `physics/`, `rendering/`,
`configuration/`.

🟨 — **real implementation through Stage 1 (roadmap TASK-000..013).**
15 Python files, about 1,470 lines: `configuration/` (schema + YAML
loader), `engine/` (`coordinate_system.py`, `mesh.py`,
`logging_setup.py`), `rendering/` (`canvas.py`, `window.py`,
`mesh_visualization.py`), plus `bootstrap.py` and `__main__.py` at the
package root. `physics/` is still a docstring-only `__init__.py` --
nothing before Stage 4 needs it. Implementation progress is tracked by
`roadmap.md`, not by this manifest; this note exists so a reader isn't
left assuming the package is either empty or complete.

This entry read "Six `__init__.py`/`__main__.py` files, docstring-only,
no implementation" until 2026-08-21 -- true when written on 2026-08-15,
false from 2026-08-16 onward, and still passing `make ci` every day
since. `make check-claims` could not have caught it either: this file is
on that script's exclusion list, deliberately, because tracking
completeness is its job. That exclusion is sound and is not being
removed, but it does mean **the two documents most likely to carry a
stale completeness claim are precisely the two nothing checks
mechanically.** Re-read this section against the actual tree at every
stage boundary, not only when something here is being edited.

---

# tests/

`tests/` with `unit/`, `integration/`, `golden/`, `performance/`.

🟨 — 22 test modules, **187 tests, 99% coverage** (2026-08-21).
`unit/` holds config/logging/rendering (D1/D2/D3), the tooling tests
(`test_check_docs.py`, `test_check_claims.py`,
`test_generate_docs_index.py`), `test_main.py`/`test_bootstrap.py` for
in-process CLI/bootstrap coverage, and Stage 1's contract and
implementation suites (`test_coordinate_system_contract.py`,
`test_uniform_vertex_coordinate_system.py`, `test_mesh_contract.py`,
`test_structured_cartesian_mesh.py`, `test_mesh_visualization.py`).
`integration/` holds `test_cli.py` (C1a), `test_bootstrap.py` (D4) --
the real subprocess versions -- `test_import_order.py`, a permanent
regression test for D4's circular import, `test_interactive_window.py`
(a real glfw window, skipped where no display exists), and
`test_claude_hooks.py` (2026-08-21: the `.claude/` hooks actually run,
and parse at an older interpreter floor). The repository-tooling tests
live in `unit/` alongside them: `test_check_docs.py`,
`test_check_claims.py`, `test_check_graph.py` and
`test_generate_docs_index.py`/`test_generate_dependency_tree.py`. `golden/` holds
`test_empty_window.py` (D5) and `test_empty_mesh.py` (TASK-013), both
running their demo via the real public CLI as their primary test, per
`docs/implementation/golden-demos.md`'s public-API rule.
`performance/` still empty (nothing to benchmark yet).

The count above read "42 tests, 87% coverage" from 2026-08-16 until
2026-08-21 -- see the `src/` section above for why neither `make ci` nor
`make check-claims` was ever going to notice. See `pyproject.toml`'s
`[tool.coverage.report]` comment for what's still structurally
unmeasurable and why. `tests/unit/`, `integration/`, `golden/`,
`performance/` each have an `__init__.py`, needed once
`unit/test_bootstrap.py` and `integration/test_bootstrap.py` coexisted --
both pytest and mypy identify test modules by bare basename without one,
and collided. Roadmap TASK-003, done.

---

# examples/

`examples/` with `golden-demos/`, `tutorials/`, `experiments/`.

🟨 — `golden-demos/empty_window.yaml` (D5, 2026-08-16) and
`golden-demos/empty_mesh.yaml` (TASK-013, 2026-08-20) are the two demos
so far: plain configuration files, no Python -- golden demos run through
the public `pyflow run --config <file>` CLI, per
`docs/implementation/golden-demos.md`'s public-API rule, so there is no
demo-specific script here (an earlier `empty_window.py` was replaced by
this file the same day the rule was written). `tutorials/`,
`experiments/` still empty. Named `examples/` rather than the roadmap's
original `demos/` because it holds more than demos; the roadmap was
updated to match on 2026-08-15.

---

# tools/

`tools/` with `generators/` and `validators/`.

🟩 — `validators/` holds `check_docs.py` (broken relative links, added
2026-08-17), `check_claims.py` (stale completeness claims, advisory,
2026-08-18) and `check_graph.py` (knowledge-graph consistency, gating,
2026-08-21); `generators/` holds `generate_dependency_tree.py`
(`docs/planning/dependency-tree.md` from the component graph,
2026-08-21) and `generate_docs_index.py` (generates
`docs/index.md`, also added 2026-08-17), each documented in its own
`CLAUDE.md`. `planner/` and `scripts/` -- empty since the first commit,
with no document ever stating what either was for -- were retired
2026-08-17 (E10, maintainer's decision) rather than left as speculative
placeholders.

---

# assets/

`assets/` with `colourmaps/`.

⬜ — empty. Expected to fill once field rendering needs colour maps
(roadmap TASK-017); explicitly carved out of A3's "no file tracked here
is empty" Stage 0 exit condition on the same terms as the
`planning/**.yaml` graph (2026-08-19, F3 exit audit) -- gated on later
work, not an oversight. `icons/`, `shaders/`, `textures/` retired
2026-08-19 (`docs/planning/backlog.md` E9) -- unlike `colourmaps/`, no
document anywhere ever stated what they were for, the same test that
retired
`tools/planner/`/`tools/scripts/` (E10).

---

# .claude/

`.claude/settings.json` (hook wiring), `.claude/hooks/post_edit_format.py`
(a `PostToolUse` hook running `ruff --fix`/`ruff format` on the single
file just edited), and `.claude/hooks/ruff.toml` (added 2026-08-21: a
scoped `target-version = "py39"` for hook scripts, which run under
whatever interpreter the harness provides rather than the project's
pinned 3.14). 🟩 — real, working configuration, and verified to run
rather than assumed: `tests/integration/test_claude_hooks.py` exercises
every command `settings.json` wires up. That test exists because the
hook had in fact been dead for four days -- see `.claude/hooks/CLAUDE.md`
for the full account.

**Found unrecorded in this manifest 2026-08-19 (F2 sweep,
`docs/planning/backlog.md`)** -- both existed with real content from
early in Stage 0 (`.claude/settings.json`'s mtime predates most of Group
D) but neither had ever been added here or to
`docs/planning/knowledge-architecture.md`, and neither directory had a
`CLAUDE.md` until this pass, despite the root `CLAUDE.md`'s collective
rule (KA-038) requiring one for every directory. Exactly the kind of gap
F2 exists to catch: an artifact area that grew unnoticed because nothing
prompted a Blast Radius check when it was created (no backlog item ever
added `.claude/` -- it came from tooling setup, not a tracked task). Not
itemised in `docs/planning/knowledge-architecture.md`, same as `tools/`
and `assets/`.

---

# .github/

`.github/workflows/ci.yml` (C2, 2026-08-16) -- `make ci` on push to
`main` (renamed from `master` 2026-08-19, F1) and every pull request,
matrixed on `ubuntu-latest` + `windows-latest`, Python from
`.python-version`. 🟩 — a remote was created 2026-08-19 and CI has now
actually run and gone green on both platforms, verified directly against
the run itself (`9c66e25`, the push that merged the second of two PRs),
not inferred from the PR merging. Getting there found three real bugs
`make ci` alone had never exercised -- a flaky `azure.archive.ubuntu.com`
apt mirror, a native `SIGABRT` in the interactive-display probe on a
truly headless runner, and a platform-dependent sort in the docs-index
generator -- each fixed and confirmed by a subsequent green run before
being reported as fixed; see `docs/CHANGELOG-DESIGN.md` (2026-08-19).
Roadmap TASK-004: **Done**.

---

# CLAUDE.md files

**Collective rule:** every directory in the repository has a `CLAUDE.md`.
They are tracked collectively here, not as individual rows, because
per-directory agent guidance is a property of the directory rather than a
standalone artifact (KA-038).

As of 2026-08-19: **42 files exist; 7 are still the generic placeholder**
and 35 carry real local content. (42 rather than 40 because F2
(`docs/planning/backlog.md`) found `.claude/` and `.claude/hooks/`
untracked by this manifest and by `docs/planning/knowledge-architecture.md`,
with no `CLAUDE.md` at all -- both written in the same change, both real
content, not placeholders. 40 itself down from 43 because `assets/icons/`,
`assets/shaders/`, `assets/textures/` were retired 2026-08-19, E9, taking
their placeholder files with them, on the same "nothing states what this
is for" test that retired `tools/planner/`/`tools/scripts/`, E10; 43
itself down from 45 for that same E10 retirement.) E9's *Done when* was
revised the same day it closed: no placeholder may remain in a directory
that has content, not no placeholder anywhere -- inventing
directory-specific guidance for a directory that is still genuinely
empty produces speculation, not knowledge. All 7 remaining placeholders
(`assets/`, `assets/colourmaps/`, `docs/tutorials/`,
`examples/experiments/`, `examples/tutorials/`, `src/pyflow/physics/`,
`tests/performance/`) sit in directories with no real content yet --
each either holds nothing or a bare docstring-only `__init__.py` -- so
E9 is closed under the revised criterion. `docs/planning/backlog.md` E9
holds the file-by-file breakdown and is the authoritative count; this
row and `docs/planning/roadmap.md`'s TASK-009 status both restate it, so
update all three together.

---

# Maintenance Rules

Whenever a maintained artifact is added, moved, or its status changes:

1. Update this manifest.
2. Update the corresponding `Name:` / `Status:` in
   `docs/planning/knowledge-architecture.md` if the artifact has a KA
   entry. These two documents describe the same artifacts from different
   angles and drift apart if only one is updated -- which is exactly how
   v0.1 of this file decayed.
3. Link it from any appropriate index. For a page under `docs/`,
   `docs/planning/`, `docs/architecture/`, `docs/handbook/{numerical-
   methods,physics}/`, `docs/implementation/`, `docs/references/`,
   `docs/tutorials/`, or `adr/`, this step is satisfied by running
   `make docs` (`docs/index.md` is generated, not hand-maintained --
   tools/generators/CLAUDE.md); do the same for any other index that
   still is hand-maintained.
4. Update the nearest `CLAUDE.md` with concrete maintenance guidance.
5. Update any affected documentation.
