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
| 7 — Rendering Annotations | — (no dedicated Level; see "Rendering" below) |
| 8 — Better Numerics | 4 — Numerical Improvements |
| 9 — Geometry | 5 — Geometry |
| 10 — Adaptive Resolution | 6 — Adaptive Resolution |
| 11 — Additional Numerical Frameworks | 7 — Additional Numerical Frameworks |
| 12 — Three Dimensions | 8 — Three-Dimensional Simulation |
| 13 — Performance | 9 — High Performance Computing |
| 14 — Advanced Physics | 10 — Advanced Physics |

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

**Third divergence, resolved 2026-08-31 (maintainer's call): a Stage was
added, the same shape as the first.** A running simulation's own render
window carried no title, no labelled legend, no timestep/time readout,
and no cell/domain size -- a real usability gap, not a Capability Level
this roadmap had already scheduled for, so it gets a Stage the same way
the first divergence's SPH/particle-method work did: inserted where it
belongs by dependency and reading order (after Stage 6, since it
annotates a rendering pipeline several stages have already extended;
before Stage 8's own numerics work, since neither depends on the other
and there is no reason to make a viewer wait for better numerics to see
what is on screen today), not appended at the end. Like Rendering
generally, it gets no dedicated Capability Level -- the Stage/Capability
Level table at the top of this section already marks its row that way,
the same "no dedicated Level, tasks added to whichever Stage needs them"
pattern the paragraph above this one restates for Measurements/
Diagnostics/Export. **Stages 7-13 were renumbered to 8-14** to make room:

| Was | Is now |
|-----|--------|
| Stage 7 — Better Numerics | Stage 8 — Better Numerics |
| Stage 8 — Geometry | Stage 9 — Geometry |
| Stage 9 — Adaptive Resolution | Stage 10 — Adaptive Resolution |
| Stage 10 — Additional Numerical Frameworks | Stage 11 — Additional Numerical Frameworks |
| Stage 11 — Three Dimensions | Stage 12 — Three Dimensions |
| Stage 12 — Performance | Stage 13 — Performance |
| Stage 13 — Advanced Physics | Stage 14 — Advanced Physics |

No `TASK-NNN` identifiers moved, the same reason the first divergence's
renumbering needed none: Stages 7 (old)-13 were all still at the looser
"Tasks include" level of planning, nothing numbered to renumber. Checked
before renumbering, not assumed cheap: `grep -rE "Stage
(7|8|9|10|11|12|13)\b"` outside this file found 66 occurrences across 14
files at the time this was drafted -- most already written as "Stage N
(Name)" per this document's own naming rule (`docs/practices.md`, "Name
a Stage when you cite its number"), which is what made the sweep
tractable; each was checked individually rather than replaced by a blind
substitution, and a dated entry in `docs/CHANGELOG-DESIGN.md` or
`docs/practices.md` describing the *first* divergence's own renumbering
event was left as the historical record it is, not rewritten to describe
this one.

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
| TASK-009 CLAUDE.md Hierarchy | **Done** 2026-08-19, count kept current since -- 46 files exist as of 2026-08-29 (up from 45 as of 2026-08-23: `tests/fixtures/CLAUDE.md` joined with TASK-034, real content from the day it was created, the same "one file added, count updated in the same change" discipline this row exists to model; 45 itself up from 42 as of 2026-08-22: `tests/features/CLAUDE.md` joined the same day as ADR-007, missed by that day's own consistency sweep; `src/pyflow/engine/numerics/CLAUDE.md` and `tests/unit/numerics/CLAUDE.md` joined with TASK-018, 2026-08-23 -- all three real content, found and fixed while drafting TASK-018, the same "count restated in three places, one file added, count not touched" failure this row exists to warn about. 42 itself up from 40: F2 found `.claude/` and `.claude/hooks/` had no `CLAUDE.md` at all and were untracked by both inventories, fixed with real content, not placeholders; 40 itself down from 43: `assets/icons/`, `assets/shaders/`, `assets/textures/` retired 2026-08-19, E9, no document anywhere having ever stated what they were for, the same test that retired `tools/planner/`/`tools/scripts/`, 2026-08-17, E10; 43 itself down from 45 for that earlier retirement); **4** are still generic placeholders, 41 carry real content. E9's *Done when* was revised the same day it closed: no placeholder may remain in a directory that has content, not no placeholder anywhere -- all 4 remaining (`docs/tutorials/`, `examples/experiments/`, `examples/tutorials/`, `tests/performance/`) sit in directories with no real content yet, verified directly. `docs/planning/backlog.md` E9/F2 hold the file-by-file breakdown and are the authoritative count |
| TASK-010 Engine Bootstrap | **Done** 2026-08-16 -- `pyflow run` loads configuration, initialises logging, opens the render window, runs the loop, exits cleanly; verified with both the offscreen backend (automated, `tests/integration/test_bootstrap.py`) and the real interactive glfw backend (manual run, a real window opened and closed cleanly). `make ci`'s pass is what TASK-010 means by "the CI pipeline passes" here, per the C2 scope decision above -- not a claim that GitHub Actions itself has run it |

This paragraph previously said `make install` and `make test` were still
expected to fail, pending `uv.lock` and a test suite (B2/C1) -- stale
since 2026-08-16 and corrected 2026-08-19. Both now succeed: `uv.lock`
is committed (B2) and `make test` runs the suite with coverage
(C1a/C1b): **898 tests as of 2026-09-03**, up from 763 at Stage 6's
exit audit. **The last 53 are the Stage 7 exit audit's own** (2026-09-03), and every one of them exists because a criterion had no check that would fail if it were violated: 41 in the new `tests/unit/test_golden_demo_annotations.py` (four P-019 conformance checks parametrised across all ten bundled demos, plus the guard that the sweep reaches them at all), four new Gherkin scenarios in `field_display.feature` checking the annotations are rasterised inside the framed view rather than merely present in the scene, and seven in `test_bootstrap.py` -- four pinning the vector-scale line to arrows actually drawn (the one real defect this audit found), one for `units.time_scale`/`time_unit` at the rendered text, one for `max_width` at the wiring rather than only at `hud.py`'s own pass-through, and one pinning Criterion 6's own qualifier -- that switching the HUD off leaves the camera framed on the mesh alone, not merely stops drawing text. The fifty-third is in `tests/unit/test_generate_status_report.py`, and it is the same shape: `find_drift`'s three roadmap claim patterns had every test around them fed a synthetic string, so all of them passed while the real document drifted out from under the pattern -- twice already, and nearly a third time in this very change. Before that -- TASK-043
(`pyflow run --demos`) added eighteen: nine in `tests/unit/
test_golden_demos.py`, five in `tests/unit/test_main.py`, four in
`tests/integration/test_cli.py`. TASK-044 (the rendering HUD, including
its own same-day revision from user feedback) added 48: 37 in its first
cut (twelve in `tests/unit/test_hud.py`, twelve in `tests/unit/
test_bootstrap.py`, six new plus one parametrised case's own seven
variants in `tests/unit/test_configuration.py`), 11 more in its revision
(four covering `max_width` in `test_hud.py`, four in `test_bootstrap.py`
-- one net from replacing a single now-reversed test with two, plus
three new for the vector-scale stats line -- and two dedicated plus one
parametrised case's own variant in `test_configuration.py` for
`vector_label`). **A further 16 landed after that merge, from the
"revised again the next day" round TASK-044's own entry records above**:
9 for axis labels (5 in `test_hud.py`, 4 in `test_bootstrap.py`), 6 for
the arrowhead fix and its own follow-up minimum-length floor (in
`test_field_visualization.py`), and 1 regression test in
`test_generate_status_report.py` for the `TEST_COUNT_CLAIM` regex itself
going silently inert -- see that file's own test for the full account.
**Coverage percentage is deliberately not restated
here.** Both tasks independently hit the same `pytest-cov` finding while
landing, worth recording once here rather than twice: a `uv run pytest
-n auto` run occasionally reports a wildly understated figure (93%,
`schema.py` at 81%, `loader.py` at 74%, neither touched by either task)
against a reproducible 99% on an identical re-run of the identical
command -- `pytest-cov`'s own coverage-combining under parallel workers
occasionally drops a worker's contribution, not a real regression in
anything either task changed. Caught only because the same command was
run twice and disagreed with itself; `generate_status_report.py` does
not cross-check this figure at all (`tool.coverage.report`'s own
comment: no `fail-under` threshold is set, deliberately), so a spurious
low reading copied into a commit message or documentation without a
second run to check it would have gone uncaught. A single run's
percentage is not trustworthy evidence on its own, on this project or
elsewhere; re-run before trusting one. 761 as that
stage's fifth and last task (TASK-038) closed on 2026-08-30, 756 at
TASK-037's own close, 752 at
TASK-036's own close, 748 at TASK-035's own close, 707 at TASK-042's own
close, 689 at Stage 6's design phase, 688 at Stage 5's close, 672 as
TASK-034 closed and 653
after TASK-033. TASK-042
(Field Declaration Configuration) added eighteen: ten new Gherkin
scenarios in `tests/unit/test_field_declaration_configuration.py`
(`field_declaration.feature`) plus eight plain pytest functions
covering `FieldConfig`'s own per-field type validation in
`tests/unit/test_configuration.py`, the same split TASK-041 used for
`FluidConfig`. The one added at Stage 6's design phase, before that, was
finding a second inert check --
`check_references.py` had never checked `.feature` paths at all, so its
`PLANNED` table's four Stage 5 feature-file entries could not have
fired; `tests/unit/test_check_references.py::test_a_feature_file_is_a_checked_path`
is the regression, verified against the pre-fix tuple rather than
assumed. The Stage 5 exit audit added sixteen: six rejection tests plus
one acceptance test for the periodic-prescription rule it built
(Criterion 6), six for `generate_status_report.py`'s new README
Current-Phase drift check plus one regression test for the
Gherkin-scenario claim pattern it found silently inert, one new Gherkin
scenario each in `navier_stokes_timestep.feature` (Criterion 13's
`LinearSolver` substitution check) and `pressure_correction_loop.feature`
(Criterion 3's initial-divergence clause), and one in
`tests/unit/test_bootstrap.py` for the `velocity_solved` defect it found
in shipped behaviour (Criterion 12). Before that, TASK-034's own ten new Gherkin scenarios
in `tests/unit/test_navier_stokes_timestep.py`, two new plain (non-BDD)
unit tests in `tests/unit/test_piso_pressure_coupling.py` proving the
new `_poisson_matrix` cache, one new periodic-aware test each in
`test_gradient_contract.py`/`test_divergence_contract.py`, and five new
Gherkin scenarios across the two new golden-demo modules
(`test_heat_diffusion.py`, `test_lid_driven_cavity.py`). Having been 64
when
this paragraph was rewritten on 2026-08-19, 202 earlier the same day,
212 after TASK-014, 226 after TASK-015, 250 after TASK-016, 287 after
TASK-017, 297 after TASK-039, 315 after the Stage 2 exit audit and 337
as of 2026-08-22 (the count this paragraph itself read until
2026-08-26's correction, which is exactly the failure the next
paragraph warns about -- it was already off by 136 real tests the day
`tools/generators/generate_status_report.py` first ran against it), 508
as of 2026-08-26, 515 after TASK-040's first pass (Simulation
Orchestrator, Stage 4's first task despite its number): five new Gherkin
scenarios in `tests/unit/test_simulation.py` plus two rejection-path
tests added to `tests/unit/numerics/test_assembly.py` when its
advection/diffusion resolution split apart to take its own inline
`UnknownSchemeError` rather than sharing `_resolve`'s -- and 518 after
that same task's own Auditor-stance review cycle found three more real
gaps (`prompts/common/AUDITOR.md`): no test proved the resolved
boundary-conditions mapping actually reached the advection/diffusion
factories, that mapping was shared mutable state with no defensive
copy, and `linear_solver`'s own `UnknownSchemeError` path had never had
a dedicated test either. 531 after TASK-023 (First-order Upwind
Advection, Stage 4's second task): eight new Gherkin scenarios in
`tests/unit/test_first_order_upwind_advection.py`, `boundary_face_name`'s
own two tests in `test_structured_cartesian_mesh.py`,
`FirstOrderUpwindAdvection` joining `test_advection_contract.py`'s
existing parametrised suite, and `test_assembly.py`'s now-inaccurate
joint null-advection-and-diffusion check replaced by two (one per
component, since advection is no longer null). 546 after TASK-024
(Central Difference Diffusion, Stage 4's third task): six new Gherkin
scenarios in `tests/unit/test_central_difference_diffusion.py`,
`face_centroid_distance`'s own four tests (two contract-suite invariants
in `test_mesh_contract.py`, two exact-formula checks in
`test_structured_cartesian_mesh.py`), `CentralDifferenceDiffusion`
joining `test_diffusion_contract.py`'s existing parametrised suite,
`test_assembly.py`'s null-diffusion check replaced by a real-scheme one
plus a new boundary-conditions-and-coefficient capture test, and three
new `NumericsConfig.diffusion_coefficient` load/reject tests in
`test_configuration.py`.
553 after TASK-025 (RK4 Time Integration, Stage 4's fourth task): two
new Gherkin scenarios in `tests/unit/test_rk4_time_integration.py`;
`RK4Integrator` joining `test_time_integrator_contract.py`'s existing
parametrised suite as a third factory alongside `euler`/`double_step`,
which multiplies every test already parametrised over that fixture (five
of them) rather than adding five new ones outright; and
`test_assembly.py`'s null-time-integrator check replaced by a
real-scheme one, net zero there. Net +7, not the "join adds N, nothing
else changes" shape TASK-023/024 both had -- widening an existing
fixture's own parametrisation, not just appending a new test, is a
different arithmetic and is recorded as such rather than glossed over.
560 after TASK-026 (Conjugate Gradient Solver, Stage 4's fifth task):
two new Gherkin scenarios in `tests/unit/test_conjugate_gradient_solver.py`;
`ConjugateGradientSolver` joining `test_linear_solver_contract.py`'s
existing parametrised suite as a third factory alongside `exact`/`jacobi`
-- a real "add a factory, edit nothing existing" join this time, unlike
TASK-025's, since `LinearSolver.solve`'s own signature needed no change
-- which multiplies the one existing test already parametrised over both
`make_solver` and two systems (2x2/3x3) by one more factory (+2); a new
generic contract-suite test, `test_a_zero_right_hand_side_solves_to_the_
zero_vector_immediately`, parametrised over all three solvers (+3),
added because it happens to be exactly what proves
`ConjugateGradientSolver`'s own early-convergence-check branch is real
behaviour rather than dead code (found while confirming 100% coverage,
not invented to pad the count -- a claim true for every `LinearSolver`
implementation, not a TASK-026-specific test smuggled into the shared
suite); and `test_assembly.py`'s null-linear-solver check replaced by a
real-scheme one, net zero there. +7 again, same "widened parametrisation"
shape as TASK-025's own climb, not TASK-023/024's "add N, touch nothing
else".
572 after TASK-027 (PISO Pressure Coupling, Stage 4's sixth task): two
new Gherkin scenarios in `tests/unit/test_piso_pressure_coupling.py`;
`GreenGaussGradient`/`GreenGaussDivergence` each joining
`test_gradient_contract.py`'s/`test_divergence_contract.py`'s own
parametrised suites as a real third factory (+1 each on the existing
shape tests, plus two dedicated correctness/rejection tests each: an
exact-for-a-linear-field check, an `UnconfiguredBoundaryFaceError`
check, and -- divergence only -- an `IncompatibleVectorFieldError`
check); `PISO` joining `test_pressure_coupling_contract.py`'s own suite
the same way; and `test_assembly.py`'s null-pressure-coupling check
replaced by a real-scheme one plus a new boundary-conditions-threading
capture test, the same shape TASK-024's own diffusion join used. +12
overall, a genuinely different arithmetic from any prior Stage 4 task's
own climb -- three interfaces gained a real fixture in one change, not
one, because Design decision One (above) made this task responsible for
`Gradient`/`Divergence` as well as `PressureCoupling`.
580 after TASK-028 (Dirichlet Boundary, Stage 4's seventh task): two new
Gherkin scenarios in `tests/unit/test_dirichlet_boundary.py`;
`DirichletBoundaryCondition` joining
`test_boundary_condition_contract.py`'s existing parametrised suite as a
real third factory (+2 on the two existing tests already parametrised
over it, the same "widened parametrisation" arithmetic TASK-025's/
TASK-026's own joins used) plus a new dedicated
kind-and-value test (+1); `test_assembly.py`'s own real-scheme-resolution
test for the sixth component (+1); and two new `NumericsConfig.
boundary_conditions.<face>.scalar_value` load/reject tests in
`test_configuration.py` (+2), the same shape TASK-024's own
`diffusion_coefficient` tests used. +8 overall; unlike every prior task
in this run, no existing test's own body changed shape (`test_assembly.py`'s
`test_null_boundary_conditions_evaluate_the_configured_value` was
renamed and had its fixture's own `velocity`/`pressure` arguments
replaced with `scalar_value` -- a fixture edit, not a new test -- since
the previous version was asserting the old, now-corrected semantics).
588 after TASK-029 (Neumann Boundary, Stage 4's eighth task): two new
Gherkin scenarios in `tests/unit/test_neumann_boundary.py`;
`NeumannBoundaryCondition` joining
`test_boundary_condition_contract.py`'s existing parametrised suite as a
real fourth factory (+2 on the two existing tests already parametrised
over it, the same widened-parametrisation arithmetic TASK-028's own join
used) plus a new dedicated kind-and-gradient test (+1); a new
real-scheme-resolution test for the eighth and final component (+1),
built against an explicit `"neumann"`-typed config rather than the
default one, since every default face is `"dirichlet"`; and two new
`NumericsConfig.boundary_conditions.<face>.scalar_gradient` load/reject
tests in `test_configuration.py` (+2), `scalar_value`'s own mirror. +8
overall, the identical arithmetic to TASK-028's own climb.
`test_assembly.py`'s own boundary-conditions-evaluate test had its
Neumann fixture's own `velocity` value changed to be deliberately
distinct from `scalar_gradient` (a fixture edit, not a new test) --
found necessary by mutation testing: the previous fixture's shared
`0.0` for both fields meant a regression reading `velocity` instead of
`scalar_gradient` would have passed unnoticed.
603 after TASK-030 (Periodic Boundary, Stage 4's ninth and last task):
four new tests in `test_structured_cartesian_mesh.py` for
`wrapped_neighbour_cell` (correct pairing on all four edges, split into
one rejection test per face orientation -- vertical and horizontal --
rather than one, found necessary while confirming coverage: a single
`next(...)`-selected interior face always picked the vertical branch
first, leaving the horizontal `raise` line untested); three new Gherkin
scenarios in `tests/unit/test_periodic_boundary.py` (`periodic_boundary.
feature`, this task's own Acceptance Criteria -- advection reading the
wrapped neighbour, diffusion computing the gradient at one full cell
width, and a convergence-based round-trip invariant, below); two new
capture tests in `test_assembly.py` for `periodic_pairs` threading into
the advection/diffusion factories, the periodic analogue of TASK-040's/
TASK-024's own boundary-conditions capture tests; and four new
`SimulationConfig` load/reject tests in `test_configuration.py`
(reads the section, rejects an unknown `scalar_pattern`/`velocity_
pattern`, rejects a non-numeric `velocity`), the same shape every prior
config-section addition in this run used. Two new Gherkin scenarios in
`tests/golden/test_passive_scalar_transport.py` (`passive_scalar_
transport.feature`) for the golden demo this task also builds (Stage 4
Completion Criterion 1's own "a real simulation-stepping mechanism
running live", not this task's own Acceptance Criteria -- see this
task's own Intent above). +15 overall.

**The round-trip scenario's own criterion needed a genuine correctness
finding to get right, not just "matches exactly", found by running the
real numbers before writing the assertion (the same discipline TASK-026's
null-space check and TASK-027's Rhie-Chow investigation used).** A plain
"advect a field once around a periodic domain, assert it returns to its
starting distribution" fails even for a *correct* wrap: first-order
upwind's own O(dx) numerical diffusion smooths any field over the
distance it travels, and refining the timestep alone does not shrink
that error (the RK4-integrated semi-discrete system converges to a fixed,
spatially-truncation-dominated limit as `dt -> 0`, verified directly:
identical results at `num_steps` ranging 10-160 on a fixed mesh). What a
*wrong* wrap (mirrored or clamped to the owner's own cell at the
periodic boundary, instead of the opposite edge) cannot reproduce is
refinement actually closing the gap -- measured directly on a genuinely
periodic-compatible fixture (a sine wave in x, period equal to the
domain width, plus a `100*y` term so every row is checked -- a plain
linear ramp was tried first and rejected: wrapping it creates an
artificial discontinuity at the seam that numerical diffusion then
smooths, confounding this specific claim), a real wrap's own round-trip
error drops by roughly 62% over a 4x mesh refinement (16 to 64 cells),
while a mirrored/clamped one (a throwaway mutation, built and run
specifically to check this) drops by only roughly 16% and stays several
times larger throughout. The scenario asserts the fine-resolution error
stays under two thirds of the coarse one -- comfortably separates the two
outcomes measured, confirmed to actually fail under the mirrored/clamped
mutation before being trusted.
**The demo's own centroid-displacement tolerance was measured the same
way, not guessed**: a real run of `passive_scalar_transport.yaml` agrees
with the closed-form `velocity * dt * steps` prediction to within ~4%;
the scenario's own `rel=0.15` bound stays comfortably above that margin
without being so loose a genuinely broken stepping loop (frozen,
backwards, or off by a large factor) could still pass -- confirmed
directly: a mutation that froze `state` every frame (never actually
calling `simulation.step`) fails this scenario.
The rest of the climb to 508 that same day is
`tests/unit/test_generate_status_report.py` -- the new tool's own test
suite -- growing from 23 to 35 tests as that tool itself grew, a live
demonstration that this count moves for reasons having nothing to do
with the fluid solver and everything to do with why it needs checking
rather than re-reading. The same is true again, 2026-08-28: 603 to 605
from a CLI help-message accuracy fix, no Stage 4/5 task work involved --
`pyflow --help`'s top-level text still described the CLI as a "Stage 0
skeleton -- no simulation functionality yet" and never mentioned
`--config` or how to run a golden demo, caught by a user auditing the
CLI directly. Fixed in `src/pyflow/__main__.py`'s `description`/`epilog`
(phrased by capability now, not roadmap stage number, so it survives a
stage exit unedited), with two new tests holding it there --
`test_top_level_help_describes_current_capabilities`
(`tests/unit/test_main.py`) and its subprocess-boundary mirror in
`tests/integration/test_cli.py` -- and a dated rule in
`src/pyflow/CLAUDE.md` requiring this text be revisited whenever a
subcommand, flag, or golden demo changes. 606 the same day, after the
Stage 4 exit audit: one new Gherkin scenario in
`first_order_upwind_advection.feature` ("Conservation on a fully
periodic domain"), added because the existing closed-domain conservation
scenario turned out to pass for any flux array whatsoever -- see this
Stage's own Completion Criterion 4 row, below, for the mutation evidence
and why the weak scenario was annotated rather than deleted. 614 the
same day: `tools/generators/generate_config_template.py`'s own test
suite (`tests/unit/test_generate_config_template.py`), eight tests, built
at a user's direct request for an annotated, always-current example
config -- again no Stage 4/5 task work involved, the same "count moves
for reasons having nothing to do with the fluid solver" pattern the
paragraph above already records. 622 after TASK-041 (Fluid Configuration
Section, Stage 5's first task): four new Gherkin scenarios in
`tests/integration/test_fluid_configuration.py`
(`fluid_configuration.feature`) and four new `FluidConfig.viscosity`
load/reject tests in `test_configuration.py`, the same shape every prior
config-section addition in this run used -- this is Stage 5's own first
climb, not another Stage 4 audit finding. 642 after TASK-031 (Velocity
Field Support, Stage 5's second task, all four subtasks in one branch):
thirteen new Gherkin scenarios in `tests/unit/test_velocity_field_support.py`
(`velocity_field_support.feature`) covering the four subtasks together,
six new `SimulationConfig.velocity_solved`/`BoundaryFaceConfig.
field_values`/`field_gradients` load/reject tests in `test_configuration.py`
-- the same config-section-addition shape again, this time three small
fields across two sections rather than one -- and one new
`test_bootstrap.py` test proving `bootstrap()`'s own live loop actually
decomposes/steps/reassembles velocity, not only `simulation.step()`
called directly (found necessary by its own coverage report: the new
`velocity_solved` branches in `_add_passive_scalar_transport` were
otherwise unexercised by anything in this run). 647 after TASK-032
(Pressure Field, Stage 5's third task): five new Gherkin scenarios in
`tests/unit/test_pressure_field.py` (`pressure_field.feature`), proving
properties `PISO` (TASK-027, Stage 4) already computed but Stage 4's own
criteria never had cause to check -- constant pressure for a
divergence-free provisional field, the null-space remedy actually
holding, `step` rejecting a `PressureField` -- against the real `PISO`
class throughout, no new pressure-solving mechanism. **136 of those 898
are Gherkin scenarios rather than pytest functions**
(`adr/ADR-007-executable-acceptance-criteria.md`; up from fourteen with
`field_display.feature` gaining scenarios and `numerics_assembly.feature`
joining, TASK-021; to 24 with TASK-040's own
`simulation_orchestrator.feature`, Stage 4's first -- not a golden demo,
so its scenarios describe the orchestration mechanism itself rather than
a runnable config file, per that feature file's own header comment; to
32 with TASK-023's own `first_order_upwind_advection.feature`, eight
scenarios covering boundedness, boundary treatment, the CFL-limit
stable/unstable pair, and conservation; to 38 with TASK-024's own
`central_difference_diffusion.feature`, six scenarios covering the
interior and boundary flux formulas, the unconfigured-boundary rejection,
second-order convergence, and conservation; to 40 with TASK-025's own
`rk4_time_integration.feature`, two scenarios covering genuine four-stage
evaluation at four distinct states and fourth-order accuracy under
timestep refinement; and to 42 with TASK-026's own `conjugate_gradient_
solver.feature`, two scenarios covering convergence on a positive
semi-definite system with the null space handled, and non-convergence
staying distinguishable from a converged answer; and to 44 with
TASK-027's own `piso_pressure_coupling.feature`, two scenarios covering
a single correction pass's measured, bounded divergence reduction and
non-convergence in the pressure solve staying distinguishable from a
plausible answer; and to 46 with TASK-028's own `dirichlet_boundary.
feature`, two scenarios each building a real interior scheme
(Advection, Diffusion) together with a real `DirichletBoundaryCondition`,
proving the wiring, not only `evaluate()` in isolation, per this task's
own Intent; and to 48 with TASK-029's own `neumann_boundary.feature`,
two scenarios each building a real interior scheme together with a real
`NeumannBoundaryCondition`, both prescribing a nonzero gradient
throughout -- diffusion's own reads the gradient's numeric value
directly, advection's own proves the opposite, that it is never read;
and to 51 with TASK-030's own `periodic_boundary.feature`: advection
reading the wrapped neighbour, diffusion computing the gradient at one
full cell width, and a round-trip invariant measured as convergence
under mesh refinement rather than exact equality at one resolution
(this task's own Design decisions record the numerical finding that
makes "matches exactly" the wrong claim to check); and to 53 with
TASK-030's own golden demo, `passive_scalar_transport.feature` -- the
required CLI-subprocess scenario every demo carries, and a quantitative
claim that the transported field's own mass-weighted centroid moves
downstream at approximately the prescribed velocity over real elapsed
time, not only that rendered pixels changed; and to 54 with the Stage 4
exit audit's own addition to `first_order_upwind_advection.feature`,
above -- the only scenario in this list added by an audit rather than by
the task that owned the criterion; and to 58 with TASK-041's own
`fluid_configuration.feature`, Stage 5's first task and its first four
scenarios: a fluid section loading both its fields, one field's default
surviving the other being set, the retired `numerics.diffusion_
coefficient` field rejected by name rather than silently defaulted, and
the Passive Scalar Transport golden demo still running through the real
CLI after its own config migrated to the new section); and to 71 with
TASK-031's own `velocity_field_support.feature`, thirteen scenarios
across its four subtasks: a `VectorField` decompose/reassemble round
trip plus its two rejection paths; viscosity and a scalar's own
diffusion coefficient each moving one field's flux and leaving the
other's alone, both directions; two ordinary scalars (not a velocity
pair) each seeing their own prescribed value at one shared wall,
independently of the other's; and velocity's own components advanced
by the same `step` call as a scalar, a transported scalar's result
unchanged by whether the velocity carrying it was solved or prescribed,
self-advection matching a hand-derived result, the existing
`IncompatibleVelocityFieldError` check surviving the new path, and the
orchestrator's own source still carrying no field-name-specific
branching for velocity); and to 76 with TASK-032's own
`pressure_field.feature`, five scenarios: a divergence-free provisional
field yielding pressure constant to solver tolerance, a divergent one
yielding non-constant pressure, adding a constant to the solved pressure
leaving the corrected velocity unchanged (the null-space remedy made
observable), `step` rejecting a `fields` mapping containing a
`PressureField` by name, and a boundary configuration violating the
zero-net-flux compatibility condition failing to load before any
pressure solve is attempted; and to 79 with TASK-033's own
`pressure_correction_loop.feature`, three scenarios: a real solver's
corrector loop converging with a non-increasing recorded divergence
sequence, a deliberately halving solver forcing and proving multiple
genuine (strictly decreasing) passes, and exhausting the iteration limit
raising `DivergenceDidNotConvergeError` rather than returning a
best-effort result; and to 94 with TASK-034's own three feature files,
Stage 5's fifth and last task: ten scenarios in
`navier_stokes_timestep.feature` (the predictor/corrector/corrected
sequence, both null tests, determinism, the ADR-003 substitution check,
Couette flow, the Ghia cavity comparison, the Taylor-Green matched/
mismatched pair, and kinetic-energy conservation), three in
`lid_driven_cavity.feature`, and two in `heat_diffusion.feature` -- the
MVP's own two golden demos. **672 tests overall**: 653 after TASK-033
(recorded above), plus TASK-034's own fifteen new Gherkin scenarios
across those three feature files, plus four more plain pytest
functions -- two new (non-BDD) unit tests in `test_piso_pressure_
coupling.py` proving the new `PISO._poisson_matrix` cache is reused
across calls and safely recomputed for a different mesh, and one new
periodic-aware test each in `test_gradient_contract.py`/
`test_divergence_contract.py`; and to 105 scenarios with TASK-042's own
`field_declaration.feature`, Stage 6's first task, ten scenarios: four
named fields loading and transporting together in one step, the
`simulation.scalar_pattern` migration rejected by name, `field_display.
scalar_pattern` staying unaffected in the same scenario file, a
duplicated field name rejected, a name colliding with a velocity
component or with pressure each rejected, a non-positive diffusion
coefficient rejected, an unrecognised initial condition rejected, naming
which declared field the renderer colours actually selecting it, and
naming an undeclared field as that selector rejected. **707 tests
overall**: 689 at Stage 6's design phase (recorded above), plus
TASK-042's own ten new Gherkin scenarios and eight new plain pytest
functions in `tests/unit/test_configuration.py` covering `FieldConfig`'s
own per-field validation, the same split TASK-041 used for
`FluidConfig`; and to 118 scenarios with TASK-035's own three feature
files, Stage 6's second task: nine in `temperature_field.feature` (the
analytic decay rate agreeing with Heat Diffusion's own, warm fluid
rising, reversing gravity reversing it, the null case exact, the
configured-source-term substitution check, a run with no buoyancy
coupling behaving identically regardless of which source term is
selected, the Rayleigh-Bénard qualitative pair, the unsolved-velocity
rejection, and the structural no-`"temperature"`-literal check), plus
two each in `heat_transport.feature`/`thermal_buoyancy.feature`, its own
two brand-new golden demos. **748 tests overall**: 707 at TASK-042's own
close (recorded above), plus TASK-035's own thirteen new Gherkin
scenarios across those three feature files, six new plain pytest
functions in `tests/unit/numerics/test_assembly.py` covering the seventh
(`source_term`) registry, thirteen new plain pytest functions in
`tests/unit/test_configuration.py` covering `fluid.gravity`, `FieldConfig`'s
own buoyancy-coupling pairing, and `numerics.source_term`, four new
plain pytest functions in `tests/unit/test_buoyancy.py` covering
`BoussinesqBuoyancy`'s own mechanics (a coupling naming an absent field,
a zero gravity component, summing several couplings, a non-velocity
field) beside its Gherkin-checked physical-correctness claims, and five
more found while correcting the registration-timing defect this task's
own Status note records above: three in the new `tests/integration/
test_boussinesq_buoyancy_registration.py`, plus two new parametrised
cases (`pyflow.physics`, `pyflow.physics.buoyancy`) added to the
pre-existing `test_import_order.py`; and to 122 scenarios with TASK-036's
own `density_field.feature`, Stage 6's third task, four scenarios: a
denser patch sinking (the mirror of TASK-035's own rising warm patch), a
single `BoussinesqBuoyancy` instance constructed from a configuration
declaring both a temperature and a density coupling (Criterion 4's own
substitution check, proving one object rather than two that merely agree
in sign), the density field's own domain integral conserved under pure
advection, and the pressure corrector still driving divergence to
tolerance whether or not a density field is present. **752 tests
overall**: 748 at TASK-035's own close (recorded above), plus these four
new Gherkin scenarios in `tests/unit/test_density_field.py` and no new
plain pytest functions -- Criterion 1's own "expected: zero lines under
`src/pyflow/`" held exactly, verified directly via `git diff --stat`,
not merely expected; and to 126 scenarios with TASK-037's own
`humidity_field.feature`, Stage 6's fourth task, four scenarios:
temperature and humidity transported together each decaying at their own
configured rate (Criterion 3's first bullet, `coefficient_overrides`
proven to generalise past momentum for the first time with a pair of
*non-buoyant* fields), a committed configuration prescribing different
`field_values` for temperature and humidity at the same wall resolved
through real `load_config` -> `assemble_numerics` (Criterion 3's second
bullet, the first scenario to exercise that surface through
configuration rather than by hand-constructing the condition object the
way `velocity_field_support.feature` does), the humidity field's own
domain integral conserved under pure advection (Criterion 6, the same
shape `density_field.feature` already established), and temperature left
bit-identical whether or not a humidity field is also declared (the
cross-field-leak regression guard). **756 tests overall**: 752 at
TASK-036's own close (recorded above), plus these four new Gherkin
scenarios in `tests/unit/test_humidity_field.py` and no new plain pytest
functions -- Criterion 1's own "expected: zero lines under
`src/pyflow/`" held exactly again, verified directly via `git diff
--stat`, not merely expected; and to 132 scenarios -- 131 with
TASK-038's own two feature files, plus one this stage's exit audit added
(a seventh rejection surface, `temperature_field.feature`) -- TASK-038's
own
`passive_tracers.feature` (three scenarios) and `smoke_transport.feature`
(two), Stage 6's fifth and last task: a passive tracer proven exactly
passive and not inert in one scenario (Criterion 5, both bullets
together, the same "in the same scenario" shape the criterion's own text
demands); four named tracers transported together each behaving
independently, discharging Criterion 1's own "at least four named
fields... alongside a solved velocity" bullet the cheap way its own
Acceptance Criteria named in advance; a structural check that
`simulation.py`'s own source carries none of this stage's four
phenomenon names, closing a real gap no earlier task's Discharges had
claimed (only `"velocity"` and `"temperature"` had ever been checked);
the required CLI-subprocess scenario for the Smoke Transport demo; and
the smoke field genuinely differing after several real timesteps than
after one, under the same recirculating lid-driven flow
`lid_driven_cavity.yaml` already proved stable. **761 tests overall**:
756 at TASK-037's own close (recorded above), plus these five new
Gherkin scenarios across `tests/unit/test_passive_tracers.py` and
`tests/golden/test_smoke_transport.py`, and no new plain pytest
functions -- Criterion 1's own "expected: zero lines under
`src/pyflow/`" held exactly a third time, verified directly via `git
diff --stat`, not merely expected.
**All** `make ci`
targets pass, verified via the Makefile itself, not only via `uv tool
run` in isolation -- that is `lint`, `typecheck`, `test`, `check-docs`,
`check-docs-index`, `check-graph`, `check-dependency-tree`,
`check-inventory`, `check-manifest`, `check-references`,
`check-scenarios` and `check-status`, the last three of which this
sentence did not name until 2026-08-26 because they were added to the
target after it was written.

A live test count in a document nobody re-reads is a standing liability
-- this one went stale within a day of being written the first time,
and the identical number in `docs/repository-manifest.md` went stale for
five, and both went stale again exactly the same way afterwards (see
above). **This is now checked, not just re-read**:
`tools/generators/generate_status_report.py` (`make check-status`, part
of `make ci` since 2026-08-26) parses the test count and Gherkin
scenario count out of this very paragraph and fails the build if they
disagree with what `pytest --collect-only` and `tests/features/*.feature`
actually say -- see `docs/planning/status.md`. Where a count is
*evidence for a past claim* (criterion 6 below, "64 tests passing"
during the 2026-08-19 fresh-clone check) it stays a dated record exactly
as written, and `generate_status_report.py` deliberately only reads the
most recently dated "N tests at P% as of DATE" occurrence in this
paragraph, not every historical figure in it.

Keep this table current -- it is the only place the roadmap states where
the project actually is, `docs/planning/backlog.md` depends on it being
honest, and since 2026-08-26 `make check-status` will say so if it
isn't.

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
Stage 13 (Performance) profiling gives a real reason to trade it for GPU
throughput, not before, per this project's "don't build ahead of a real
consumer" (TASK-011) applied to a trade-off rather than a capability.
Device placement (CPU vs. GPU) is out of scope for the same reason --
storage is always a CPU tensor until Stage 13.

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

**Arrows were plain line segments, not glyphs with arrowheads, until
Stage 7 (Rendering Annotations) reversed this 2026-09-01, from real user
feedback.** A line from each cell's centroid, direction and length set
by that cell's vector value (scaled by a configurable factor, capped so
adjacent arrows don't overlap at the mesh's own spacing), reused exactly
the line-drawing mechanism `build_mesh_grid_line`
(`src/pyflow/rendering/mesh_visualization.py`, TASK-013) already
established, rather than a second rendering primitive. The deferral's
own stated reasoning was sound at the time -- a triangular arrowhead is
not independently checkable at the pixel level in any way a plain
segment's own direction and length aren't, and nothing in this task's
own Acceptance Criteria needed one to be checkable -- but it turned out
to matter in practice once a real user looked at a genuinely small
vector field (Lid-Driven Cavity) and could not tell direction at all: a
bare line segment has no visual asymmetry, so which end is the tip is
not recoverable from the rendered pixels alone, however the arrow is
scaled. `build_vector_field_arrows` now appends two short chevron
segments at the tip (`_ARROWHEAD_ANGLE`/`_ARROWHEAD_LENGTH_FRACTION`,
`field_visualization.py`), proportional to the shaft's own length so a
near-zero vector still renders an honestly near-invisible head rather
than a fixed-size decoration overstating it. Checked with new geometry
tests (`tests/unit/test_field_visualization.py`'s own arrowhead section),
not only visually, and re-verified against real renders of both Field
Display and Lid-Driven Cavity before being trusted.

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
   - **Exception, decided 2026-08-23 (maintainer's choice, TASK-021):**
     `src/pyflow/engine/numerics/assembly.py` registers one trivial,
     non-physical reference implementation per component (zero flux, an
     unconverged no-op solve, a pass-through velocity correction) under
     the exact MVP names this stage's config already validates. Exists
     solely so criterion 8's golden demo -- a real `pyflow run`
     subprocess, importing only `src/pyflow` -- has something to
     assemble into; without it, criterion 8 and this criterion's letter
     were flatly incompatible; TASK-021's own Status section records the
     other two options considered and why this one was chosen. Named and
     documented as reference implementations everywhere they appear, not
     as a first real implementation in disguise -- a real scheme
     (TASK-023 onward) still does not exist until Stage 4. This is the
     one narrowing this criterion has; it does not extend to any file
     other than `assembly.py`, and it does not make the reference classes
     "real" for any other criterion's purposes.
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

### Status as of 2026-08-23: Stage 3 complete, ten of ten criteria met

| Criterion | Verdict |
|-----------|---------|
| 1. Six interfaces, no real implementation | **Met, with one recorded exception.** All six ABCs exist under `src/pyflow/engine/numerics/`, each rejecting direct instantiation and an incomplete subclass. `assembly.py` registers one trivial, non-physical reference implementation per component under `src/` -- an explicit, maintainer-decided narrowing of this criterion's letter (2026-08-23), not an unrecorded violation; the criterion's own text above states it, why, and its limits. |
| 2. Contract suite per interface, ≥2 implementations | **Met.** Nine suites (`test_{advection,diffusion,gradient,divergence,source,boundary_condition,time_integrator,linear_solver,pressure_coupling}_contract.py` -- nine files, one per interface), each parametrised over at least two test-only implementations. Four suites (boundary condition, time integrator, linear solver, pressure coupling) skip the inert-implementation teeth-check the first five use, each for a reason stated in its own module and pinned by `tests/unit/numerics/CLAUDE.md`. |
| 3. Adding an implementation edits no function body | **Met.** `tests/unit/numerics/test_assembly.py::test_registering_a_new_name_resolves_without_editing_assembly` registers a name no `src/` module knows and gets it back from `assemble_numerics`, whose own body is unchanged. |
| 4. Selection fixed at construction | **Met.** `test_mutating_the_config_after_assembly_changes_nothing` mutates a `NumericsConfig` after calling `assemble_numerics` and checks the already-returned `AssembledNumerics` is unaffected. |
| 5. Configuration selects all six | **Met.** `NumericsConfig` has all six fields, each validated in `validate()`; `PyFlowConfig()` alone passes; `test_non_default_round_trip_including_tuple_fields`/`test_boundary_conditions_round_trip` round-trip non-default `numerics` values (including the ones TASK-021 itself did not add, since those already had exactly one valid name and nothing distinct to set) through `generate_config_yaml`/`load_config`. |
| 6. Cross-layer dependency in the interface | **Met.** `PressureCoupling.__init__` raises `TypeError` for anything that isn't a real `LinearSolver` instance -- `test_constructing_without_a_linear_solver_raises`/`test_constructing_with_a_non_solver_object_raises`, a runtime guarantee, not only a type annotation. |
| 7. Whole-configuration boundary validation | **Met** (TASK-019, unchanged since). |
| 8. Demonstration, honest about drawing nothing new | **Met as re-checked 2026-08-24; overstated on 2026-08-23.** `examples/golden-demos/numerics_assembly.yaml` names all six components; `tests/golden/test_numerics_assembly.py`'s five scenarios cover the real-CLI run, the reported set matching the configured set, the run reporting that set *through the real CLI* (added 2026-08-24), determinism across two runs, and -- the carve-out's own claim, checked rather than assumed -- adding a `numerics` section to `field_display.yaml` renders pixel-identical output. The original "Met" verdict counted four scenarios and did not notice that "the reported set matching the configured set" was checked only in-process, against a criterion whose own text says "invoked through the real CLI as a subprocess": the exit audit confirmed this directly by deleting the log line the criterion also requires and finding every existing test still passed. Recorded here rather than silently corrected, per this repository's Integrity section. |
| 9. `make ci` green on both CI platforms | **Met.** PR #25 (`feat/task-021-pressure-coupling-interface`), run 32666167045: `ci (ubuntu-latest)` green in 2m9s, `ci (windows-latest)` green in 4m24s -- checked against the actual run via `gh run watch`, not inferred from the PR merging. |
| 10. Documentation describes what now exists | **Met.** `engine.md`'s six affected entries read "Implemented in", each stating the interface arrived in Stage 3 and the concrete scheme is Stage 4; `icds.md`'s configuration-mechanism paragraph and all six "Configuration control" lines read as implemented, with the provisional-names caveat removed; the Golden Demos table, `golden-demos.md`, and `planning/data/demos.yaml` all name this stage's demo; every touched `CLAUDE.md` and both inventories were checked against the tree directly in this same change, not assumed current. **Superseded in form, 2026-08-24:** the 2026-08-24 exit audit found this criterion's "checked every touched file" scope was too narrow -- `docs/architecture/overview.md`, which TASK-021 never touched, still said seven layers were unbuilt and that `icds.md` was "entirely target architecture". `engine.md`'s "Arrives via"/"Implemented in" labels were therefore replaced by a single `Implementation:` line naming module paths, so status is carried by something `make check-references` gates rather than by a tense (`docs/practices.md`, "Let a checked artifact carry status, not a tense"). The criterion was met as written on 2026-08-23; the label names it quotes no longer exist. |

**What this stage should hand forward.** Criterion 1 and Criterion 8
were in real tension, not merely apparent: a real subprocess CLI run
(8) needs something to assemble into, and "no concrete implementation
under `src/`" (1) says there should be nothing there to assemble. Three
resolutions were possible and are recorded in TASK-021's own Status
section; the maintainer chose the one that narrows criterion 1 by a
stated, bounded exception rather than the one that would have loosened
the configuration schema's closed-`Literal` validation (a much larger
and less reversible change) or the one that would have kept the
subprocess from proving anything real. **When a stage's own completion
criteria conflict with each other, that is exactly the case
`docs/practices.md`'s "stop and hold a design session" rule exists for**
-- picking the reading that's easiest to implement, rather than
surfacing the conflict, is how a criterion quietly stops meaning what it
says.

---

## TASK-018

Operator Interfaces

**Status: Done, 2026-08-23.** `src/pyflow/engine/numerics/{advection,
diffusion,gradient,divergence,source}.py` implement this task's five
ABCs exactly as specified below; `tests/unit/numerics/test_*_contract.py`
(44 tests: instantiation rejection, abstract-method-set assertion,
signature check, the parametrised two-implementation suite, and the
inert-implementation "fails the varies check" proof, per interface)
exist and pass, built strict TDD -- every suite written and confirmed
red for `ModuleNotFoundError` before its interface existed.
`NumericsConfig` (`advection`/`diffusion` fields) landed in the same
change; see the correction noted below. `make ci` is clean: 384 tests,
99% overall coverage, 100% on every new module. See
`src/pyflow/engine/CLAUDE.md`'s `numerics/` entry and
`src/pyflow/configuration/CLAUDE.md`'s `NumericsConfig` entry for the
full account.

**Correction found and fixed during implementation:** this entry's
`Artifacts Produced`/`Acceptance Criteria` below never mentioned
`NumericsConfig`, even though its own `Discharges` section (unedited
below) already claimed "adds `numerics.advection` and
`numerics.diffusion` to the new `NumericsConfig`" -- and TASK-019/020/022
each state their own share of the same section directly under
`Artifacts Produced`. Treated as this entry's own drafting gap, not a
reason to leave the Discharges claim unbuilt: implemented to match the
other three tasks' pattern (`schema.py`'s `NumericsConfig` dataclass,
`Literal["first_order_upwind"]`/`Literal["central_difference"]` fields,
`validate()`, wired into `loader.py` and `PyFlowConfig`), with its own
tests (`tests/unit/test_configuration.py`,
`test_top_level_key_order_matches_pyflowconfig_field_order` in
`test_generator.py`, plus the three restatements of `PyFlowConfig`'s
key order this discovered and fixed in `tests/integration/test_cli.py`
and `tests/unit/test_main.py` -- the same "count/order restated in
several places, one changed, the rest not" failure
`docs/practices.md` already names elsewhere).

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
- `NumericsConfig` (`src/pyflow/configuration/schema.py`), with
  `advection`/`diffusion` fields, wired into `PyFlowConfig` and
  `load_config` -- see the correction noted above this task's Purpose.

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

**`NumericsConfig` (`advection`/`diffusion`):**

- `PyFlowConfig()` alone is valid with both fields defaulted
  (`"first_order_upwind"`/`"central_difference"`, `icds.md`'s sole
  named MVP choice for each).
- An unknown value for either field raises `ValueError` at
  `load_config` time, naming the field (`numerics.advection`/
  `numerics.diffusion`), before anything is assembled.
- `pyflow generate-config`'s output includes the `numerics` section and
  still round-trips through `load_config` to an equal `PyFlowConfig`.

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

**Status: Done, 2026-08-23.** `src/pyflow/engine/numerics/
boundary_condition.py` implements `BoundaryCondition` and
`NotABoundaryFaceError` exactly as specified below;
`tests/unit/numerics/test_boundary_condition_contract.py` (11 tests)
and the configuration tests in `tests/unit/test_configuration.py`/
`tests/unit/test_generator.py` exist and pass, built strict TDD. `make
ci` is clean: 407 tests, 99% overall coverage, 100% on every new/touched
module (`boundary_condition.py`, `schema.py`, `loader.py`).

**Two design decisions this task's own text left open, resolved during
implementation and recorded here:**

1. **`evaluate`'s "value or gradient" is one abstract method plus a
   `kind: Literal["value", "gradient"]` property**, not two abstract
   methods (one per shape). The interior caller reads `kind` first to
   know how to interpret the number `evaluate` returns; a condition
   implements exactly one shape, so a second abstract method every
   implementation must also fill (raising `NotImplementedError` for the
   shape it doesn't have) would be the same information expressed more
   awkwardly. `icds.md` also names a third shape ("periodic... a
   wrapped-neighbour reference") that fits neither `value` nor
   `gradient` -- deliberately not modelled here, since this task's own
   Implementation section already scopes itself to "the Dirichlet/
   Neumann shapes without being them" and nothing has yet built a
   periodic implementation to check the interface against (P-016).
2. **`BoundaryFaceConfig` has independent `velocity: float | None` and
   `pressure: float | None` fields, not one `quantity`-tagged value.**
   The Acceptance Criteria below require *representing* "both velocity
   and pressure prescribed on one boundary" so it can be rejected -- a
   single `quantity: Literal["velocity", "pressure"] | None` field
   makes that combination inexpressible, which would satisfy the
   criterion by construction rather than by a checked rejection.
   `velocity` is the boundary-*normal* component only (positive =
   outward) -- enough for the net-flux criterion below; a richer
   per-component value (e.g. lid-driven cavity's tangential wall speed)
   is deferred to whichever task builds a concrete condition against a
   real consumer, not modelled speculatively now.

**One further correction, found writing the net-flux test:** "values...
sum to zero net flux" (this task's own Acceptance Criteria, below) means
the flux integrated over each boundary's length, not the raw prescribed
values -- a rectangular (non-square) mesh has different north/south and
east/west edge lengths, so an unweighted sum of the four values is not
the net flux and would both wrongly accept and wrongly reject real
cases. `_validate_boundary_conditions_jointly`
(`src/pyflow/configuration/schema.py`) weights each boundary's velocity
by its edge length (`mesh.extent`/`mesh.spacing`) before summing;
`tests/unit/test_configuration.py`'s
`test_load_config_accepts_velocity_on_every_boundary_with_zero_weighted_net_flux`
uses a 4x2 mesh with an unweighted sum of -1 and a weighted sum of 0,
specifically so a future regression to the unweighted reading fails
loudly rather than passing by coincidence on a square-mesh fixture --
the same "distinct factors" discipline `docs/practices.md` already
requires of geometric contract suites, applied here to a conservation
check instead.

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
- `BoundaryFaceConfig` (one domain edge) and `BoundaryConditionsConfig`
  (all four) within `NumericsConfig`
  (`src/pyflow/configuration/schema.py`); the cross-boundary validation
  is a module-level function called from `PyFlowConfig.validate()`, per
  this task's own "not by each condition object" design decision above.
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

**Status: Done, 2026-08-23.** `src/pyflow/engine/numerics/
time_integrator.py` implements `TimeIntegrator` exactly as specified
below; `tests/unit/numerics/test_time_integrator_contract.py` (15 tests)
and the configuration tests in `tests/unit/test_configuration.py`/
`tests/unit/test_generator.py`/`tests/unit/test_main.py` exist and pass,
built strict TDD. `make ci` is clean: 426 tests, 99% overall coverage,
100% on every new/touched module (`time_integrator.py`, `schema.py`,
`generator.py`, `loader.py`).

**Correction, 2026-08-27 (TASK-025): `advance`'s signature below no
longer matches `src/pyflow/engine/numerics/time_integrator.py`.** This
task's own closed record is left as-is rather than rewritten (per
`docs/practices.md`, a closed task's criteria stay the historical record
of what they were closed against) -- `derivatives: Mapping[str,
torch.Tensor]` was widened to a re-evaluatable
`derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]`
because RK4 (TASK-025) needs to evaluate the derivative at intermediate
states a single snapshot cannot supply. Full reasoning:
`adr/ADR-008-time-integrator-derivative-callable.md` and TASK-025's own
Design decisions, below.

**One point this task's own Acceptance Criteria left open, resolved
during implementation:** "the same test-only integrator produces the
same result when handed a derivative computed by two different
test-only advection implementations" is read as *two different
derivative-producing code paths*, not literally two `AdvectionScheme`
subclasses -- `AdvectionScheme.flux` returns a `(mesh.num_faces,)`
tensor (`src/pyflow/engine/CLAUDE.md`'s numerics entry), while a time
derivative is cell-shaped, matching `field.values`
(`(mesh.num_cells, *component_shape)`); reusing `AdvectionScheme` here
literally would need a face-to-cell reduction the ABC has no reason to
define. The contract suite instead builds two small functions with
genuinely different arithmetic (`field.values * 2.0` vs.
`field.values + field.values`) engineered to agree numerically for the
fixture, which is what the criterion is actually checking: the
integrator sees only the resulting values, never which code produced
them.

**No inert third test-only implementation, unlike the five TASK-018
suites** -- see `tests/unit/numerics/CLAUDE.md` for why this interface's
own Acceptance Criteria (the zero-derivative case and the nonzero
scheme-independence case) already supply both halves of that pattern
without needing a third class.

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

**Status: Done, 2026-08-23.** `src/pyflow/engine/numerics/
linear_solver.py` implements `LinearSolver` and `LinearSolverResult`
exactly as specified below; `tests/unit/numerics/
test_linear_solver_contract.py` (10 tests) and the configuration tests
in `tests/unit/test_configuration.py`/`tests/unit/test_generator.py`/
`tests/unit/test_main.py` exist and pass, built strict TDD. `make ci` is
clean: 440 tests, 99% overall coverage, 100% on every new/touched module
(`linear_solver.py`, `schema.py`, `generator.py`, `loader.py`).

**One point this task's own Artifacts Produced bullet answers, and one
this task resolved during implementation, both worth recording:**

1. **No dedicated "system" type.** The bullet names only one new type
   ("the ABC, and the result type"), read as deliberate: `solve` takes
   `matrix`/`rhs` directly, two plain tensors, rather than a wrapper --
   `engine.md`'s own Contract sentence ("given a linear system, produces
   its solution") names exactly that pair as the system.
2. **`matrix` is a dense `(n, n)` tensor, not sparse or matrix-free.**
   Neither this task's text, `icds.md`, nor the handbook mandates a
   code-level representation -- only that Conjugate Gradient needs a
   symmetric positive-definite system (`icds.md`'s Linear Solver entry).
   Chosen for the MVP's small, toy-scale meshes, and left explicitly
   reversible: nothing under `src/` depends on it yet (Criterion 1), and
   the handbook's own "large, sparse" framing of the real
   pressure-correction system is exactly the signal that TASK-026's
   concrete Conjugate Gradient implementation may need to revisit this
   choice once a real mesh size makes a dense matrix impractical.

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
  TASK-021's interface requires. *Closed by:* the type existing; the
  requirement itself was TASK-021's to close, and is (its own Status
  section).
- **Criterion 5**, partially: adds `numerics.linear_solver` and its two
  numeric fields.

---

## TASK-021

Pressure Coupling Interface

**Built last** -- see the Stage 3 discharge map. It depends on TASK-022's
type, and as the stage's final task it owns the stage-level criteria:
the demonstration, CI evidence, and documentation accuracy.

**Status: Done, 2026-08-23. Stage 3 complete, all ten Completion
Criteria met** -- see this stage's own Status section at the end of its
Completion Criteria for the full per-criterion record, including the
real CI run (PR #25, run 32666167045) that closes Criterion 9.
`src/pyflow/engine/numerics/pressure_coupling.py` implements
`PressureCoupling` exactly as specified below;
`src/pyflow/engine/numerics/assembly.py` implements the registry and
`assemble_numerics`; `tests/unit/numerics/
test_pressure_coupling_contract.py` (10 tests) and `tests/unit/numerics/
test_assembly.py` (13 tests) exist and pass, built strict TDD; the
golden demo (`examples/golden-demos/numerics_assembly.yaml`,
`tests/features/numerics_assembly.feature`,
`tests/golden/test_numerics_assembly.py`, 4 scenarios) runs through the
real CLI. `make ci` is clean: 469 tests, 99% overall coverage, 100% on
every new/touched module.

**One decision this task's own text left open, escalated rather than
picked unilaterally, because it bears directly on Stage 3 Completion
Criterion 1:** the golden demo needs a real `pyflow run` subprocess to
assemble all six components and report them, but a subprocess imports
only `src/pyflow`, and Criterion 1 forbids any concrete implementation
of the six there. Presented to the maintainer as three options --
report configured names only without real instantiation; ship trivial
no-op reference implementations under `src/` as an explicit, narrow
exception; or keep zero implementations under `src/` and have the demo
subprocess import test code, loosening the four scheme-name fields from
closed `Literal`s to registry-validated strings. **Decided: the second
option** (2026-08-23, maintainer's choice). Criterion 1 is amended below
with the exception this creates, stated where a reader checking that
criterion would look for it, not left as an undocumented gap between the
criterion's text and what `assembly.py` actually does.

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
- **Criterion 9**. *Closed by:* PR #25, run 32666167045, green on both
  `ubuntu-latest` and `windows-latest` -- recorded in this task's Status
  line and the Stage 3 exit audit above.
- **Criterion 10**. *Closed by:* the documentation pass listed above.

Golden Demo

Engine initialises entirely through interfaces. No CFD yet.

---

# Stage 4 — First Numerical Methods

Goal

Implement the simplest valid implementation of every interface.

### Completion Criteria

Written 2026-08-25, before TASK-023 starts, per `docs/practices.md`'s "A
stage gets completion criteria before its first task" -- now that Stage
3 has actually delivered the interfaces these implementations must
satisfy (closed 2026-08-23), rather than committing to their shape four
stages ahead of them, which is the speculation `docs/engineering-
principles.md` P-016 and this repository's Planning Philosophy both
refuse.

Criteria are about the stage's goal -- *the simplest valid
implementation of every interface* -- not the union of TASK-023..030's
own Acceptance Criteria. Every qualifying clause is its own bullet
(`docs/practices.md`, "The intent lives in the qualifier") and every
criterion names the task(s) that discharge it (the discharge map below),
following the two rules Stage 3's criteria were the first to carry.

**Neither of Stage 3's two exemptions extends here** (stated there,
repeated for a reader who starts at this stage): the physical-
correctness extension applies in full, because this is the first stage
that computes anything, and executable Gherkin criteria apply in full,
because every task here has user-observable behaviour to describe.

1. **A real simulation-stepping mechanism exists, assembling a mesh, a
   set of transported fields, and an `AssembledNumerics` into an actual
   per-timestep state advance.** `docs/architecture/engine.md`'s Flux
   entry says a face flux is "jointly compute[d]" by the Advection/
   Diffusion/Gradient/Divergence interfaces but assigns the computing to
   no module; `src/pyflow/engine/CLAUDE.md` has called this "the future
   simulation run-loop... once physics exist" since before any physics
   existed, without ever scheduling it. Nothing else in this Stage can
   be demonstrated without it -- `accumulate_flux_to_cells`, this task's
   own discrete-Gauss-theorem helper, is what both TASK-023 and TASK-024
   reuse directly for their own physical-correctness scenarios, and
   TASK-030's golden demo cannot be assembled at all otherwise. **This
   bullet previously said TASK-024's own convergence-order claim "needs a
   field actually evolving over real timesteps" -- wrong, found while
   actually building TASK-024, corrected in the same change (restated
   twice more below and in this task's own entry, corrected in all three
   places).** Measuring order against real time-stepping would have
   needed TASK-025 (RK4), which does not exist yet; TASK-024 measures the
   spatial operator alone instead (`accumulate_flux_to_cells(mesh,
   diffusion.flux(field))` against a known exact Laplacian, no time
   integration at all), the same isolation TASK-025's own criterion later
   applies in the opposite direction.
   - Given a mesh-sharing set of fields and an `AssembledNumerics`, a
     single call returns a new set of fields advanced by one timestep,
     without mutating the input -- the same contract `TimeIntegrator.
     advance` already carries, extended to its caller.
   - **Face-flux accumulation is uniform across every face, boundary or
     interior, and is checked as such.** Resolved 2026-08-26 (TASK-040's
     own Design decision, below): a concrete Advection/Diffusion scheme
     is constructed with the boundary conditions it needs and computes a
     correct value at every face -- including boundary faces -- itself.
     The orchestrator does not know, and must not need to know, which
     faces are boundary faces to accumulate correctly; a scenario
     confirms this by checking that changing a boundary condition's
     prescribed value changes the accumulated derivative at the adjacent
     cell, without the orchestrator's own accumulation code path
     branching on `Mesh.is_boundary_face` anywhere.
   - **Not built as a new swappable interface.** `adr/ADR-003` names
     exactly six configuration-selected components and this is not a
     seventh; per P-016 (already applied to `CoordinateSystem`'s
     cell-center placement and `rendering/canvas.py`'s third backend),
     an ABC and contract suite are not built until a second
     implementation is real and anticipated, and nothing has anticipated
     a second way to do Gauss-theorem flux accumulation. A concrete
     class, not an interface.
2. **Every one of the six `adr/ADR-003-modular-numerical-strategies.md`
   components this Stage covers gains a real, physically-meaningful
   implementation, registered under the exact MVP name Stage 3's
   `NumericsConfig` already validates -- replacing, not shadowing, the
   `_Null*` reference registration that name currently resolves to.**
   - Advection (`first_order_upwind`), Diffusion (`central_difference`),
     Time Integrator (`rk4`), Linear Solver (`conjugate_gradient`),
     Pressure-Velocity Coupling (`piso`), and Boundary Condition's
     `dirichlet`/`neumann` types each get a concrete class under `src/`.
   - **No new closed-set member is added to any `Literal[...]` field.**
     `icds.md` names exactly one MVP choice per component; this Stage
     makes that name real, it does not add a second one to choose
     between (P-016) -- checked directly: no task's diff touches
     `AdvectionSchemeName`/`DiffusionSchemeName`/etc.'s own definition in
     `schema.py`.
   - A configuration naming any of these six MVP values, assembled via
     the existing `assemble_numerics`, resolves to the new real class,
     not the reference one -- checked by asserting the resolved
     instance's type, not just by the name still validating.
3. **Passing the existing Stage 3 contract suite remains required of
   every real implementation, and is shown to be insufficient on its
   own.** A real scheme joins the interface's existing parametrised
   contract-suite fixture list (`tests/unit/numerics/
   test_<x>_contract.py`'s own `_IMPLEMENTATIONS`-shaped list) -- the
   same "a future implementation joins by adding a factory" pattern
   TASK-011 established -- rather than being checked by some separate,
   equivalent mechanism; a real scheme must not require editing the
   suite itself (the Stage 3 Criterion 3 property -- "adding an
   implementation edits no existing function body" -- extended here to
   cover the existing *tests*, not only `assembly.py`'s own body).
   Passing that suite is necessary and explicitly not sufficient:
   nothing in this Stage may treat contract-suite conformance as
   evidence for criterion 4 below, which is a separate, physics-specific
   claim the contract suite cannot make (it is implementation-
   independent by construction, and boundedness, convergence order, and
   divergence-freedom are not).
4. **Physical correctness, per `docs/practices.md`'s testable-physics
   extension, stated per task rather than left generic.** Each bullet
   below is the qualifier already recorded under this Stage's own
   "Intent" section, turned into a checkable claim so it cannot be
   satisfied by the weaker headline next to it:
   - **Advection (TASK-023):** bounded -- for an arbitrary field, no
     interpolated face or cell value falls outside the range of the
     values it interpolates between. Checked as a property over a
     field that is *not* already monotonic (a monotonic input cannot
     distinguish a bounded scheme from an unbounded one that happens to
     agree on it). Not conflated with stability: a separate scenario
     shows the same scheme becomes unstable above its CFL limit, so
     boundedness is not read as having covered it. **Also required, a
     distinct claim from boundedness** (`docs/planning/backlog.md`,
     "physical correctness validation", found 2026-08-20 and folded in
     here rather than left as a standing backlog note): conservation --
     on a periodic or fully-closed domain (no sources, no open
     boundaries), the field's total summed over every cell agrees before
     and after N timesteps to within floating-point tolerance. FVM
     guarantees this by construction (`docs/handbook/numerical-methods/
     fvm.md`); a bounded scheme can still fail to conserve if its flux
     accounting is wrong, so this is not implied by the bullet above it.
   - **Diffusion (TASK-024):** second-order accurate -- a measured
     convergence rate under mesh refinement (at least three resolutions,
     a fitted order), not a qualitative "the field diffuses." **Also
     required, same source as Advection's conservation bullet above:**
     under zero-flux (Neumann) boundaries on every edge, an insulated
     domain's total quantity does not change over N timesteps -- a
     conservation check distinct from convergence order, since a scheme
     can be second-order accurate on a smooth solution and still leak
     mass through a flux-accounting bug.
   - **Time Integrator (TASK-025):** fourth-order accurate in time --
     measured against an ODE system with an exact solution, with spatial
     error isolated out (a manufactured or zero spatial term) so it
     cannot dominate the measured order. A separate note, not itself a
     passing criterion: the *finished* end-to-end solver's observed
     order is expected to be well below four (`icds.md`), so this
     criterion is scoped to the integrator alone and must say so in the
     scenario, not be inferred from a full-solver run that would fail
     it.
   - **Linear Solver (TASK-026):** converges on a manufactured system
     with the same character as the one PISO actually produces for the
     lid-driven cavity's boundary configuration -- positive
     *semi*-definite, pressure fixed up to an additive constant -- with
     the null space removed (a pinned reference cell or an equivalent
     projection), not only on a made-up well-conditioned system. This is
     checked in isolation, against a constructed matrix/rhs pair, **not**
     by running Stage 5's actual lid-driven-cavity demo, which does not
     exist yet -- the same isolation TASK-025's own bullet above already
     applies to the integrator. Non-convergence remains distinguishable
     from a converged answer via `LinearSolverResult.converged`,
     exercised by a case constructed to fail to converge.
   - **Pressure-Velocity Coupling (TASK-027):** a single correction pass
     measurably and boundedly reduces the divergence of a manufactured
     provisional velocity field, checked cell by cell against a stated
     tolerance -- not "the pressure loop runs" and not a qualitative
     "looks incompressible." **Checked in isolation, against a
     constructed provisional velocity field, the same isolation the
     Linear Solver bullet above already applies to TASK-026** -- not by
     running Stage 5's actual lid-driven-cavity demo, which does not
     exist yet. **The stronger claim -- divergence reaching a configured
     tolerance via monotonic multi-pass correction -- is Stage 5
     TASK-033's own claim, not this task's**: PyFlow's mesh is collocated
     (no staggered grid), and suppressing pressure-velocity decoupling
     under repeated correction needs Rhie-Chow interpolation, which needs
     momentum-equation coefficients this task's own interface has no way
     to supply -- verified directly before writing any implementation
     code (three correction strategies numerically tested against a real
     mesh, all leaving most of the original divergence uncorrected with
     no momentum re-solve to iterate against), not assumed. **Found and
     corrected 2026-08-27, before implementation started**: this bullet
     originally carried no isolation caveat at all, unlike the Linear
     Solver bullet immediately above it -- see `docs/practices.md`, "A
     criterion whose strong reading depends on a later task must say so
     when drafted."
   - **Dirichlet Boundary (TASK-028):** correctness is checked in what
     the *interior* advection/diffusion scheme computes at a boundary
     face using this condition, not only in what `evaluate()` returns in
     isolation -- a condition object can return the right value and
     still be wired into the flux computation wrongly, and only the
     first is what anything downstream depends on.
   - **Neumann Boundary (TASK-029):** as Dirichlet, for a prescribed
     gradient, with a nonzero-gradient case required in addition to
     zero-gradient -- a zero-gradient result is also what a boundary
     wired to nothing at all would silently produce.
   - **Periodic Boundary (TASK-030):** a field advected once fully
     around a periodic domain returns to its starting distribution -- a
     round-trip invariant, the only check that tells a genuine wrapped-
     neighbour lookup apart from one that mirrors or clamps at a single
     boundary instead.

**Not a Stage 4 obligation, stated so its absence from criterion 4 above
isn't mistaken for a gap:** the boundary-conditions half of `docs/
planning/backlog.md`'s conservation-checks item -- "a velocity-boundary
configuration that violates [global mass conservation] should fail
construction with a clear error" -- is already closed, by Stage 3
TASK-019's own Criterion 7 (`_validate_boundary_conditions_jointly`'s
zero-net-flux rejection, `tests/unit/test_configuration.py`
`test_load_config_accepts_velocity_on_every_boundary_with_zero_weighted_net_flux`
and its rejection counterpart). Found while drafting this Stage's
criteria, not by a task claiming it; `docs/planning/backlog.md` is
amended in the same change per `docs/practices.md`'s "grep for a task's
own identifier when it closes."

5. **Every real implementation's own error/rejection conditions are
   exercised against actual bad input, not only inherited untested from
   the interface's shared helper.** The lesson `docs/practices.md`'s
   "rejection criteria stop at the constructor" names directly: a
   concrete class calling `AdvectionScheme._check_velocity` or
   `BoundaryCondition._check_boundary_face` is not proven to reject
   anything until a test actually hands it a bad velocity field or an
   interior face and checks the raise -- passing the contract suite,
   which already tests the shared helper once, is not the same claim
   repeated per implementation. The orchestrator (TASK-040) carries the
   same obligation for its own rejection conditions -- e.g. a field not
   present in the `AssembledNumerics` it was handed, or a field whose
   mesh disagrees with the one the numerics were assembled against.
6. **Every task's acceptance criteria are a Gherkin `.feature` file
   under `tests/features/`, and `make check-scenarios` gates that every
   scenario it contains actually runs** -- the mechanism `adr/ADR-007-
   executable-acceptance-criteria.md` and the section below both commit
   this Stage to; restated here as a checkable exit condition, not left
   only as the drafting instruction it also is (TASK-040 included --
   its own step/state contract is user-observable behaviour, not
   architecture, so Stage 3's exemption does not carry over to it). The
   shared vocabulary a task's steps are built from gains physics-shaped
   additions from whichever task first needs them and is reused, not
   re-derived, by every task after -- a large crop of duplicated
   fixtures and helpers by the time this Stage closes is itself a
   finding against this criterion, the same shape of warning Stage 6's
   own criteria already state for a different claim.
   **Amended 2026-08-28, Stage 4 exit audit: this bullet originally
   named `tests/golden/conftest.py` as the venue, which is not reachable
   from where Stage 4's features actually live.** A `conftest.py`
   applies only to its own directory subtree, and all nine of this
   Stage's binding modules are under `tests/unit/` -- verified directly,
   not reasoned about: a `tests/unit/` scenario using a step defined in
   `tests/golden/conftest.py` fails with
   `pytest_bdd.exceptions.StepDefinitionNotFoundError`. The criterion
   was drafted on 2026-08-25 assuming this Stage's features would be
   golden-demo-shaped; TASK-040 then established (correctly) that most
   are unit-level, and nobody came back to this sentence. The venue is
   now `tests/unit/_numerics.py`, the counterpart to
   `tests/golden/_demo.py` -- and what is shared is deliberately the
   *building blocks* a step is written from (fixture constants,
   test-only doubles, independently-derived geometry helpers), not the
   step definitions themselves, since sharing those would mean sharing
   the `_Context` each module populates and coupling nine tasks' fixture
   objects into one type. See `tests/unit/CLAUDE.md`, amended in the
   same change, and that module's own docstring.
   - **Every scenario's fixture avoids a degenerate case that could make
     a wrong implementation agree with a right one by coincidence** --
     non-square mesh, non-trivial origin, spacing that isn't 1, a
     velocity not aligned with a mesh axis, values that aren't 0 or 1
     everywhere (`docs/practices.md`, "Verify a conversion where its
     factors are distinct" -- the rule the pan-tracking bug and the
     vector-magnitude bug both trace back to). Stated once, here, rather
     than repeated under each of TASK-023..040's own bullets above.
7. **No `_Null*` reference implementation remains registered under any
   MVP name this Stage was responsible for, by the time the Stage
   closes.** The obligation stated below ("One obligation this Stage
   inherits from Stage 3"), restated here as a stage-exit condition
   rather than left only as a per-task aside: checked directly by
   reading `assembly.py`'s registration calls at the bottom of the file
   against the six names this Stage's tasks claim to have implemented,
   not inferred from `DuplicateSchemeError` having never fired.
8. **Stage 4 has a working, visible demonstration: Passive Scalar
   Transport** (`docs/implementation/golden-demos.md` already names it
   as "the first demo that computes real physics," distinguished from
   Numerics Assembly, which proved only the assembly mechanism).
   - The demo *is* a config file under `examples/golden-demos/`, run via
     `pyflow run --config <file>`, per the public-API rule every golden
     demo already follows.
   - It exercises, at minimum, a transported scalar field under real
     Advection, Diffusion, a Boundary Condition (at least one of
     Dirichlet/Neumann), and the real Time Integrator together, stepped
     by TASK-040's orchestrator -- the four numerical components and the
     one assembly mechanism a scalar-transport problem actually needs.
   - **It is not required to exercise Linear Solver or Pressure-Velocity
     Coupling**, stated explicitly so their absence from this demo is
     not later mistaken for a gap: nothing transports velocity or solves
     for pressure until Stage 5 (TASK-031/033) gives the engine a
     velocity field to correct. TASK-026/027's own criterion 4 bullets
     above are checked by their own scenarios, independent of this demo.
   - Deterministic, and verified by at least one regression test that
     invokes it through the real CLI as a subprocess, per `docs/
     implementation/golden-demos.md`'s Definition of Done.
9. **`make ci` passes on both CI platforms, on a real runner** -- not
   only locally, matching every prior stage's standard of evidence, read
   from the actual run rather than inferred from a merged PR.
10. **Documentation describes what now exists.** `docs/architecture/
    icds.md`'s "Expected behaviour"/"Limitations" prose for each of the
    six affected components is checked against the real code, not left
    as the target-architecture description it was in Stage 3;
    `engine.md`'s `Implementation:` lines for these layers, and its Flux
    entry, name the concrete module (TASK-040's orchestrator, for Flux),
    not only the interface module Stage 3 left them naming. Every
    touched `CLAUDE.md` and both inventories (`docs/repository-
    manifest.md`, `docs/repository-inventory.md`) are checked against
    the tree directly, not assumed current -- the specific failure
    Stage 1 and Stage 2's own audits each found on this exact point.

### Two design questions, both now resolved

Both were flagged here on 2026-08-25 rather than left to surface
mid-implementation (`docs/practices.md`, "When intent is ambiguous, hold
a design session before implementing"), and both are now settled --
neither task can start drafting without the answer, so this section is
kept as the pointer rather than deleted once the open state it recorded
stopped being true.

- **Boundary-face substitution.** Resolved 2026-08-26 -- see TASK-040's
  own Design decision, below: a concrete scheme receives its boundary
  conditions at construction, not the orchestrator substituting a value
  after the fact.
- **Periodic's own shape.** Resolved 2026-08-26 -- see TASK-030's own
  Design decision, below: `BoundaryCondition` stays exactly as Stage 3
  scoped it (no third `kind`); a new, `StructuredCartesianMesh`-specific
  wrapped-neighbour lookup, additive and off the abstract `Mesh`
  interface, is what a scheme consults for a periodic face instead.

### Discharge map

Every criterion has an owning task, assigned now rather than
reconstructed at the exit audit, following Stage 3's own precedent. A
task's own **Discharges** section is authoritative; this table is the
index.

**Build order is TASK-040, 023, 024, 025, 026, 027, 028, 029, 030 -- not
numerical order.** TASK-040 is built first despite its number, the same
precedent TASK-022/021 set in Stage 3: criterion 1 makes the dependency
structural, not just convenient. TASK-023/024/028/029 each construct
their own concrete scheme with the boundary conditions TASK-040's
resolved assembly order hands them (its own Design decision, below), so
that mechanism has to exist first; TASK-024's own convergence-order
scenario reuses TASK-040's `accumulate_flux_to_cells` directly, as a
spatial operator rather than through real time-stepping (this sentence
previously said it needed a field actually evolving over real timesteps
-- corrected 2026-08-27 while building TASK-024, which measures order
against the discrete Laplacian alone, with no `TimeIntegrator` involved);
TASK-027 reuses TASK-040's own shared Gauss-theorem accumulation helper
for its concrete Divergence implementation (TASK-027's own Design
decision, below), so that helper has to exist first too. TASK-040 keeps
this number rather than being renumbered into the
023-030 run, following the same reasoning Stage 3 gave for keeping
TASK-021/022's own numbers: position in this document says what happens
when, the number does not.

| Criterion | Discharged by |
|-----------|---------------|
| 1. Simulation-stepping mechanism exists, face-flux accumulation uniform across every face | TASK-040 |
| 2. Real implementation replaces reference, under the existing MVP name | TASK-023 (advection), TASK-024 (diffusion), TASK-025 (time integrator), TASK-026 (linear solver), TASK-027 (pressure coupling), TASK-028 (dirichlet), TASK-029 (neumann) -- each for its own component |
| 3. Contract suite still holds, shown insufficient alone | Each of TASK-023..029 for its own interface; TASK-027 also for `test_gradient_contract.py`/`test_divergence_contract.py`, though neither is one of the six |
| 4. Physical correctness, per task | TASK-023..030, each for its own bullet above |
| 5. Real implementations' own rejection paths tested | TASK-023..030 and TASK-040, each for its own error conditions |
| 6. Executable Gherkin criteria, `make check-scenarios` gates | TASK-023..030 and TASK-040, each for its own `.feature` file |
| 7. No `_Null*` registration survives under an implemented name | TASK-023, 024, 025, 026, 027, 028, 029 -- each deletes its own reference registration in the same change |
| 8. Demonstration: Passive Scalar Transport | TASK-030 (this Stage's last task, per build order) |
| 9. `make ci` green on a real runner | TASK-030 |
| 10. Documentation matches the tree | TASK-030 |

**TASK-030 is this Stage's last task in build order and therefore owns
the stage-level criteria** -- the demonstration, CI evidence, and
documentation accuracy -- the same assignment Stage 3 made to its own
last task (TASK-021), for the same reason: those three are not task-
level work, which is exactly why nothing claimed them in Stage 1 or
Stage 2. **TASK-040 is this Stage's first task in build order and owns
criterion 1** -- the one criterion no later task could own, since every
later task depends on it existing rather than the reverse.

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

### One obligation this Stage inherits from Stage 3

**Every task here that lands a real scheme must delete the matching
reference registration** at the bottom of
`src/pyflow/engine/numerics/assembly.py`, in the same change. Those
`_Null*` classes exist only so Stage 3's golden demo had something to
assemble into (Stage 3 Completion Criterion 1's recorded exception);
leaving one in place while registering a real scheme under the same
name would be silent, since `AssembledNumerics.names` echoes the
configured name either way and every existing check is name-based.
`assembly.py`'s `DuplicateSchemeError` turns that into an import-time
error rather than a run that reports `first_order_upwind` while
computing zero flux. Added 2026-08-24, Stage 3 exit audit.

### Intent, recorded now

Recorded 2026-08-22, ahead of the criteria, because it is the durable
half and the half this repository keeps losing. Each line states what
the task must not merely *nominally* satisfy (`docs/practices.md`,
"The intent lives in the qualifier").

**TASK-040 was added 2026-08-26, after the rest of this Stage's Intent
lines and Completion Criteria were already drafted** -- found by asking
what would actually make TASK-024's convergence-order scenario and
TASK-030's own golden demo buildable, not anticipated when TASK-023..030
were first sketched. Numbered out of sequence rather than renumbered
into the 023-030 run, and built first regardless, per the Build order
note under the Discharge map above.

### Status as of 2026-08-28: Stage 4 complete, ten of ten criteria met

**Three of these ten verdicts were overstated when first written, and
the Stage 4 exit audit the same day found all three.** This line briefly
read "nine of ten" between the audit's first pass and its resolution of
Criterion 6, which is the one that needed a decision rather than a
correction. The table below is the corrected one;
the three amended rows say what was claimed, what was actually true, and
what was done about it, rather than being silently rewritten (root
`CLAUDE.md`'s Integrity section, and the precedent Stage 3's own
Criterion 8 row set). **Stage 4 closes at ten of ten, but not the ten it started with.**
Criterion 4 gained the scenario its own qualifier had always required;
Criterion 6's bullet was found unbuildable as written and amended to a
venue that exists, with the duplication it was aimed at actually
removed; Criterion 10's seven documentation defects are fixed. Nothing
here reopened a task. The distinction worth keeping is that "ten of ten"
was true on the second pass for reasons it was not true on the first --
the first table's ten was arrived at by not reading the second half of
three sentences. The audit was run under `prompts/common/AUDITOR.md`'s
stance against a green `make ci` (605 tests, 99% coverage, 53 scenarios
across 14 feature files) and a green real CI run on `main`
(33163793986). That makes four stage audits in a row -- Stages 1, 2, 3
and 4 -- to find real defects behind a green build. Stage 0's own audit
is the single exception, and it ran before there was a real CI runner
for anything to be green on.

The three that were wrong, and the one thing they have in common:
Criterion 4's advection-conservation scenario passed for reasons
unrelated to what it claimed to check (found by mutation, not by
reading); Criterion 6's shared-step-vocabulary half was never attempted
and the criterion had pre-declared exactly what its own failure would
look like; Criterion 10's documentation sweep checked the files Stage 4
*touched* rather than the files Stage 4 *invalidated*. All three were
legible only to a reader asking "what would make this false?" -- and the
third is Stage 3's own audit finding recurring unchanged one stage
later, which is why this audit's new rule (`docs/practices.md`, "A
stage's documentation sweep is a grep, not a diff review") is about that
one specifically.

| Criterion | Verdict |
|-----------|---------|
| 1. Simulation-stepping mechanism exists, face-flux accumulation uniform across every face | **Met** (TASK-040). `engine/simulation.py`'s `step()`/`accumulate_flux_to_cells` are real, unit-tested (`tests/unit/test_simulation.py`, `simulation_orchestrator.feature`), and never branch on `Mesh.is_boundary_face` -- a concrete Advection/Diffusion scheme handles a boundary face itself. |
| 2. Real implementation replaces reference, under the existing MVP name | **Met.** All seven names TASK-023..029 own resolve to a real scheme (`FirstOrderUpwindAdvection`, `CentralDifferenceDiffusion`, `RK4Integrator`, `ConjugateGradientSolver`, `PISO`, `DirichletBoundaryCondition`, `NeumannBoundaryCondition`), each checked by `isinstance` in `tests/unit/numerics/test_assembly.py`, not just by the name still validating. |
| 3. Contract suite still holds, shown insufficient alone | **Met.** Every real scheme joined its own interface's contract suite (`test_advection_contract.py` etc.) with no edit to any existing test body except where a real interface widening required one (`TimeIntegrator.advance`, `PressureCoupling.correct`, each its own recorded ADR); each scheme's own `.feature` file is what actually proves physical correctness, per this criterion's own "necessary and explicitly not sufficient". |
| 4. Physical correctness, per task | **Met as amended 2026-08-28; one bullet overstated as first written.** Each of TASK-023..030's own Intent lines is discharged by that task's own `.feature` file, and TASK-030's own round-trip invariant is checked as convergence under mesh refinement rather than exact equality at one resolution -- a genuine numerical finding, and mutation-verified by this audit to have real teeth (clamping the wrapped neighbour to the owner fails it: 1.052 against a 0.831 bound). **The Advection conservation bullet was not.** Its scenario ("Conservation on a closed domain") makes every boundary face's face-normal velocity zero, so every boundary flux is zero whatever face value the scheme picks, while interior faces cancel by construction inside `accumulate_flux_to_cells` -- meaning it passes for *any* flux array. Verified, not inferred: forcing every advective face flux to `0.0` leaves it passing. That is exactly the qualifier the criterion reserved ("a bounded scheme can still fail to conserve if its flux accounting is wrong, so this is not implied by the bullet above it"), and the criterion's own first-named fixture -- "a **periodic** or fully-closed domain" -- is the one that carries it. **Fixed in the audit's own change:** `first_order_upwind_advection.feature` gains "Conservation on a fully periodic domain" (all four edges periodic, velocity `(1.7, -0.9)`, no boundary condition configured at all), where every boundary face carries a genuinely nonzero flux and global cancellation is a real property of the wrap accounting. Mutation-verified in both directions: the clamped-wrap mutation fails the new scenario (total drifts 52.0 → 54.87) and leaves the old one passing. The weak scenario is kept, with its own limitation stated in the feature file rather than deleted -- it still checks that a zero-velocity boundary face contributes nothing *additively*. Diffusion's own conservation scenario was checked the same way and does have teeth (mutating its boundary-gradient branch drifts the total by 37.4). |
| 5. Real implementations' own rejection paths tested | **Met.** Every `UnconfiguredBoundaryFaceError`/`IncompatibleVelocityFieldError`/`IncompatibleVectorFieldError`/`NotABoundaryFaceError` (TASK-030's own, on `wrapped_neighbour_cell`) is exercised directly against real bad input, not only inherited-untested from a shared helper -- `docs/practices.md`'s "rejection criteria stop at the constructor" checked task by task. |
| 6. Executable Gherkin criteria, `make check-scenarios` gates | **Met as amended 2026-08-28; the second half was unmet, and the criterion turned out to be unbuildable as written.** The gating half was always real: `make check-scenarios` reports "All 54 scenario(s) across 14 feature file(s) are bound and run" (53 before this audit added one), verified directly. **The shared-vocabulary half was never attempted, and could not have been.** It named `tests/golden/conftest.py` as the venue; a `conftest.py` applies only to its own directory subtree, and all nine of this Stage's binding modules live in `tests/unit/`. Proven, not argued: a `tests/unit/` scenario using a step defined in `tests/golden/conftest.py` fails with `StepDefinitionNotFoundError`. So this was never "criterion versus convention" -- the criterion named a venue that could not serve its own consumers, and `tests/unit/CLAUDE.md`'s "each binding test supplies its own local steps" grew into the vacuum and hardened into a principle nobody re-examined. **What the duplication actually was**, measured at the stage boundary: the mesh constants `origin=(0.5, -1.0), spacing=(0.2, 0.3)` byte-identical in eight modules with only `extent` varying; `_FixedValueCondition` in three and `_FixedGradientCondition` in four; `_face_normal_velocity` in four, three byte-identical and the fourth genuinely wider (a periodic face has no mesh-reported neighbour, so the test must pass the wrapped one in); `_west_face` in four. Eight copies of one fixture is not eight independent fixtures -- it is one fixture with eight places to fix, which is the opposite of what per-module copies were meant to buy. **Resolved in the audit's own change, maintainer's decision:** `tests/unit/_numerics.py` now holds the shared building blocks (the counterpart to `tests/golden/_demo.py`, an in-repo precedent rather than a new pattern), and all nine binding modules import from it. Measured after: local condition-double declarations 9 to **0**, local `_face_normal_velocity` definitions 4 to **0**, local `_west_face` definitions 4 to **0**, modules carrying the mesh constants 8 to **0** (one comment still quotes them, describing a hand-derived fixture). The step-definition count is essentially unchanged (109 to 110, the audit's own new scenario) and that is the point: the criterion's target was re-derivation, not step count, and a step whose body is one call into a shared builder is not re-derived. Deliberately *not* a shared `tests/unit/conftest.py` of step definitions: that would require one `_Context` type across nine modules, which is the coupling the convention was right to warn about. Each module keeps its own `_Context`, its own step bodies, and any double only it needs. The criterion bullet above is amended to name the reachable venue; `tests/unit/CLAUDE.md`'s convention is amended to "local by default, shared where genuinely identical". |
| 7. No `_Null*` registration survives under an implemented name | **Met, closed at TASK-029, unaffected by TASK-030** (which retires one more genuinely-dead helper, `_resolve_with_argument`, but no `_Null*` class -- there were none left). `assembly.py`'s own registration calls at the bottom of the file name only real classes. |
| 8. Demonstration: Passive Scalar Transport | **Met** (TASK-030). `examples/golden-demos/passive_scalar_transport.yaml`, run via the real CLI; `tests/golden/test_passive_scalar_transport.py`'s own quantitative scenario (mass-weighted centroid displacement, tolerance measured from a real run); verified visually beyond the regression test -- rendered offscreen at increasing frame counts, the blob is seen translating and, by one full domain width of travel, wrapping around the periodic boundary. |
| 9. `make ci` green on a real runner | **Met.** PR #38 (`feat/task-030-periodic-boundary`), run 33159480722: `ci (ubuntu-latest)` green in 2m57s, `ci (windows-latest)` green in 5m30s -- checked against the actual run via `gh pr checks --watch`, not inferred from the PR merging. |
| 10. Documentation matches the tree | **Met as amended 2026-08-28; overstated as first written.** The mechanical half held then and holds now: `make check-references`/`check-manifest`/`check-inventory`/`check-dependency-tree`/`check-docs`/`check-docs-index`/`check-graph` all pass, and the stale forward-references TASK-030's own sweep found (two in `src/pyflow/engine/CLAUDE.md`, one in `docs/planning/backlog.md`) were genuinely fixed in that change. **The sweep's scope was wrong**, and in exactly the way Stage 3's own audit had already found once (this row's Stage 3 counterpart, `docs/architecture/overview.md`): it covered the files Stage 4 *touched*, not the files Stage 4 *invalidated*. Seven defects, all in files no Stage 4 task opened, all found by this audit and all fixed in its own change: **(a)** this criterion's own second clause -- "`engine.md`'s ... Flux entry name[s] the concrete module (TASK-040's orchestrator, for Flux)" -- was simply not done; the Flux entry named `gradient.py`/`divergence.py` and never `simulation.py`'s `accumulate_flux_to_cells`, the function that performs the "summed over each control volume's faces" its own **Represents** sentence describes. **(b)** Four entries in `engine.md` (Advection, Diffusion, Time Integration, Linear Solvers) each ended "see that module's own docstring for the {five, four, three, two} that still do" -- a decaying count of surviving `_Null*` reference classes, of which there have been **zero** since TASK-029, directly contradicting Criterion 7's own verdict two rows above. Each was written by the task that made it true and left by the four tasks that made it false. **(c)** `docs/architecture/rendering.md` still said simulation/render-frame scheduling "still does not exist, because nothing produces a timestep to schedule against ... the scheduling policy itself is **Stage 4+ work**" -- three commits after TASK-030 shipped that policy (locked step, one `simulation.step()` per rendered frame, `bootstrap.py`'s `_add_passive_scalar_transport` through `RenderWindow.run(on_frame=...)`). **(d)** `src/pyflow/bootstrap.py`'s own module docstring opened "No simulation functionality -- Stage 0's job..." twenty lines above its own `import ... simulation_step` -- the identical stale self-description `__main__.py`'s help text carried, found and fixed on the same day (commit 73ff113) by a blast-radius sweep that stopped at that one file. **The last three were found by the new rule the first four produced, run against the repository before this row was written** -- which is the only reason to trust it: **(e)** `docs/architecture/overview.md` still said "No concrete numerical *scheme* exists behind any of [the six] yet -- that is Stage 4", the second time that same file has gone stale about a stage that had already closed; **(f)** the same file, three lines further down, called the `numerics.*` configuration section "the part still missing, because the interfaces it would select among do not exist yet" -- contradicting its own bullet above it, since Stage 3 built both; **(g)** `adr/ADR-002-fvm-first.md` still carried "**What still does not exist:** a real Time Integration, Pressure-Velocity Coupling, or Linear Solver implementation", written by TASK-024 and falsified three days later by TASK-025/026/027, the tasks its own next sentence named. The rule that finds all seven is new in `docs/practices.md` ("A stage's documentation sweep is a grep, not a diff review"); (g) additionally records the narrower lesson that an ADR tracking implementation status inherits that status's maintenance burden, which is why no other ADR here does. |

**Criterion 9 could not be marked Met from a local checkout alone when
this table was first drafted** -- a local `make ci` pass is not the same
claim as a real CI run, per this repository's own standing distrust of a
green-CI claim nothing has actually watched (`docs/practices.md`,
`CLAUDE.md`'s Merge Gate), the same reasoning Stage 3's own table
applied. Left honestly pending until PR #38's own run actually
completed and was checked directly (above), rather than assumed the
moment the branch was pushed.

## TASK-040

Simulation Orchestrator

**Status: Done, 2026-08-27.** `src/pyflow/engine/simulation.py`
implements `accumulate_flux_to_cells` and `step` exactly as specified by
this task's Acceptance Criteria below; `tests/unit/test_simulation.py`
(binding `tests/features/simulation_orchestrator.feature`) exists and
passes, at 100% coverage. `src/pyflow/engine/numerics/assembly.py`'s
`register_advection_scheme`/`register_diffusion_scheme` and
`assemble_numerics` were reordered to the boundary-conditions-first
sequence this task's own Design decision below requires;
`tests/unit/numerics/test_assembly.py` was updated for the new factory
shape and gained two rejection-path tests
(`test_unknown_diffusion_name_raises_named`,
`test_unknown_time_integration_name_raises_named`) that a purely
mechanical signature change would otherwise have silently left
uncovered. **Audited under `prompts/common/AUDITOR.md`'s stance
(`/code-review high`) before this Status line was written, per
`docs/practices.md`'s "Audit code before calling it done" -- one pass
found three real gaps**, fixed in the same change: nothing proved
`assemble_numerics` actually threaded the resolved boundary-conditions
mapping into the advection/diffusion factories rather than an empty or
stale one (`test_advection_and_diffusion_factories_receive_the_resolved_boundary_conditions`,
`_CapturingAdvection`); that mapping was a plain `dict` shared, with no
defensive copy, across both factories and the returned `AssembledNumerics`
(now `MappingProxyType`, `test_boundary_conditions_is_immutable`); and
`linear_solver`'s own `UnknownSchemeError` path had never had a
dedicated test, a pre-existing gap this change's own review happened to
surface (`test_unknown_linear_solver_name_raises_named`). `make ci` is
clean; 518 tests at 99% overall (`docs/planning/roadmap.md`'s own
test-count paragraph, above Stage 1).

**A third design decision, found while implementing** (the "Two design
questions, both now resolved" section above only names two -- this one
was not visible until `step`'s own arithmetic had to be written): how an
advective and a diffusive face flux combine into one per-cell
derivative. Neither `engine.md` nor `icds.md` pins this down at the
implementation level -- `AdvectionScheme`/`DiffusionScheme`'s own
docstrings promise only "the ... contribution to that field's flux at
each face", not a sign. `docs/handbook/numerical-methods/fvm.md`'s own
conservation equation settles it: `d/dt \int_V \rho\phi\,dV =
-\oint_{\partial V} \rho\phi\mathbf{u}\cdot\mathbf{n}\,dA +
\oint_{\partial V} \Gamma\nabla\phi\cdot\mathbf{n}\,dA + \text{source}`
-- the advective face flux is
*subtracted* from the rate of change, the diffusive face flux *added*.
`step` therefore accumulates `diffusion_flux - advection_flux`, not
their sum -- see `simulation.py`'s own `step` docstring for the full
derivation. Recorded here rather than left for whichever of TASK-023/024
happened to be built first to improvise a convention the other would
then have to match.

**A second reading decision, on this task's own "mesh mismatch" bullet:**
`AssembledNumerics` carries no mesh of its own (it holds live component
instances, resolved independently of any mesh), so "a mesh that
disagrees with `numerics`' own assembled mesh" (Stage 4 Completion
Criterion 5's phrasing, echoed in this task's Acceptance Criteria below)
cannot be checked literally. Read as the buildable claim it is clearly
gesturing at instead: every field in `step`'s `fields` mapping must share
`velocity`'s own mesh, checked by identity (`field.mesh is
velocity.mesh`) -- `MismatchedMeshError` names the rejection.
Stated explicitly, per root `CLAUDE.md`'s Integrity section, rather than
silently picking a reading and leaving the mismatch between the
criterion's own words and what was actually built for someone else to
notice.

**Intent:** this is the piece nothing before it assigned anywhere.
`docs/architecture/engine.md`'s own Flux entry says a face flux is
"jointly compute[d]" by the Advection/Diffusion/Gradient/Divergence
interfaces but assigns the computing to no module, and `src/pyflow/
engine/CLAUDE.md` has called this "the future simulation run-loop...
once physics exist" since before any physics existed, without ever
scheduling it. Every other task in this Stage produces a component that
can only be observed *through* this one, in the sense that both
TASK-023's boundedness claim and TASK-024's convergence-order claim are
checked using this module's own `accumulate_flux_to_cells` directly
(this paragraph previously said TASK-024's claim "needs a field actually
evolving over real timesteps" -- corrected 2026-08-27 while building
TASK-024, whose convergence measurement turned out to need only the
spatial operator, no real time-stepping, restated correctly under
Completion Criterion 1 above), and TASK-030's golden demo cannot be
assembled at all without something that turns "six configured
strategies" into a running simulation.

**Also intended, and the reason this task is built first despite its
number:** `AssembledNumerics`, `Field`, and `Mesh` are all this task
needs to exist already (Stage 2/3) -- it is not blocked on any other
Stage 4 task, and every task after TASK-025/026 is blocked on it.

### Purpose

Turn a mesh, a set of transported fields, and an already-`assemble_numerics`-d
`AssembledNumerics` into an actual per-timestep state advance -- the
mechanism `engine.md`'s Flux entry describes but assigns to no module.
Also produce the one piece of shared geometric machinery a later task
(TASK-027) needs and must not reimplement: reducing a face-valued array
to a cell-valued one via the discrete Gauss theorem.

### Dependencies

TASK-012 (`Mesh`), TASK-014..016 (`Field`/`ScalarField`/`VectorField`),
TASK-018 (`AdvectionScheme`/`DiffusionScheme` -- `GradientScheme`/
`DivergenceScheme`/`SourceTerm` are TASK-027's own concern, not
consumed here), TASK-019 (`BoundaryCondition`), TASK-020
(`TimeIntegrator`), TASK-021 (`AssembledNumerics`/`assemble_numerics`).

### Design decisions, recorded here

**A concrete module, not a new swappable interface.** `adr/ADR-003`
names exactly six configuration-selected components and this is not a
seventh; per P-016 (already applied twice in this codebase --
`CoordinateSystem`'s cell-center placement, `rendering/canvas.py`'s
third backend), an ABC and contract suite are not built until a second
implementation is real and anticipated, and nothing has anticipated a
second way to do Gauss-theorem flux accumulation.

**Boundary-face handling, resolved 2026-08-26** (`docs/practices.md`,
"hold a design session when intent is ambiguous" -- the open question
this task's own drafting surfaced): `AdvectionScheme.flux`/
`DiffusionScheme.flux` take no `BoundaryCondition` argument, so neither
can know what to do at a boundary face on its own. Two readings were
possible.

*Rejected:* this task's own orchestrator substitutes a boundary
condition's value over the interior scheme's own output at every
boundary-face index, treating that output as always discarded there.
Rejected because the correct boundary treatment is genuinely
scheme-specific -- upwind's own boundary formula (use the prescribed
value directly, or extrapolate from the interior on outflow) has a
different shape from central-difference's (a one-sided difference for a
prescribed value, the prescribed value directly for a prescribed
gradient). An orchestrator that "corrects" a scheme's boundary output
would have to know each scheme's own interpolation logic to do it right,
which leaks scheme-specific knowledge into the one place `adr/ADR-003`
exists to keep generic -- and breaks the moment a second advection
scheme (Stage 8: TVD, QUICK, WENO) has a different boundary formula from
upwind's.

**Decided: each concrete scheme receives its own boundary conditions at
construction**, the same pattern `PressureCoupling.__init__(linear_solver)`
already established -- extra context at construction, not a new
parameter on the interface's own abstract method, so `flux(field,
velocity)`'s call signature and its existing contract suite stay exactly
as Stage 3 froze them.
- `register_advection_scheme`/`register_diffusion_scheme`'s factory
  type gains a boundary-conditions parameter, the same shape
  `register_pressure_coupling`'s factory already has for `LinearSolver`
  (`engine/numerics/assembly.py`).
- `assemble_numerics` resolves `boundary_conditions` *before* advection
  and diffusion, reordered from its current sequence (boundary
  conditions currently resolve last) -- a change confined to this
  module, which this Stage already touches for the `_Null*` retirement
  obligation below.
- **This task's own accumulation code therefore never branches on
  boundary vs. interior.** A concrete scheme's `flux()` output is
  correct at every face once it holds its own boundary conditions, so
  reducing a face array to cell derivatives (below) is uniform across
  the whole array -- simpler than the rejected reading, not just
  different from it.
- **Deliberately narrow for now, not generalised:** one global set of
  boundary conditions per simulation (`NumericsConfig.
  boundary_conditions`), shared across every transported field, matching
  the shape `BoundaryFaceConfig` already has. Correct for a single
  transported scalar (this Stage's own scope) but does not yet express
  "field A is 300K at this wall, field B is 0 at the same wall" for two
  fields at once. Not solved here (P-016 -- nothing yet needs it): Stage
  6's own completion criteria already state "this stage's tasks must add
  no new machinery," so if per-field boundary values turn out to be
  needed there, that criterion catches it rather than the gap slipping
  through unnoticed.
- **A related, narrower gap, found while resolving this and left for
  TASK-028's own drafting, not solved here:** `BoundaryFaceConfig` has
  `velocity`/`pressure` fields only -- no field for an arbitrary
  transported scalar's boundary value, which TASK-030's own Passive
  Scalar Transport demo needs to configure at all. **Resolved 2026-08-28,
  TASK-028**: `BoundaryFaceConfig.scalar_value: float = 0.0` -- see that
  task's own Design decision.

### Artifacts Produced

- `src/pyflow/engine/simulation.py`:
  - `accumulate_flux_to_cells(mesh: Mesh, face_values: torch.Tensor) ->
    torch.Tensor` -- the discrete-Gauss-theorem reduction (`sum(value *
    area * outward_normal_sign) / volume` per cell), generic over any
    `(mesh.num_faces,)` array regardless of which scheme produced it.
    **This is the shared piece TASK-027 reuses** for its own concrete
    `DivergenceScheme`'s face-to-cell step, rather than reimplementing
    the same geometric arithmetic a second time.
  - `step(fields: Mapping[str, Field], velocity: VectorField, numerics:
    AssembledNumerics, dt: float) -> dict[str, Field]` -- advances every
    field in `fields` by `dt`, using `numerics.advection`/`.diffusion`
    (already boundary-aware per the Design decision above) and
    `accumulate_flux_to_cells` to build each field's derivative, then
    `numerics.time_integration.advance(...)` to advance them together.
    Does not mutate `fields`, `velocity`, or `numerics` -- the same
    contract `TimeIntegrator.advance` already carries, extended to its
    caller. `velocity` is a separate, explicit argument rather than a
    member of `fields`, matching `AdvectionScheme.flux(field,
    velocity)`'s own two-argument shape: this Stage does not yet solve
    for velocity (Stage 5, TASK-031/033), so it is supplied fixed and is
    not itself among the fields `step` advances.
- `tests/features/simulation_orchestrator.feature` -- see Acceptance
  Criteria, below. (This bullet previously said the exact name might
  still shift when TASK-023's own drafting reached it; it did not, this
  task built and named the file itself, and the note is stale now that
  it exists under exactly this name.)

### Implementation

Test-driven, per `docs/practices.md`: the feature file's scenarios
written and confirmed to fail (`ModuleNotFoundError`) before
`simulation.py` exists.

1. `accumulate_flux_to_cells` first, against a hand-checkable mesh
   (`docs/practices.md`'s "verify a conversion where its factors are
   distinct" -- non-square, non-trivial origin) with a known face-value
   array and a hand-derived expected cell array.
2. `step`, against test-only `AdvectionScheme`/`DiffusionScheme`/
   `TimeIntegrator` implementations with known arithmetic (reusing
   Stage 3's own test-only implementations where their arithmetic is
   simple enough to hand-check a derivative against, rather than
   inventing new ones).
3. Reassemble `assembly.py`'s existing advection/diffusion factory
   registration to the new boundary-conditions-first order; confirm
   every existing Stage 3 test in `tests/unit/numerics/test_assembly.py`
   still passes unchanged.

### Acceptance Criteria

`tests/features/simulation_orchestrator.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`) is the criteria; not
restated here as prose. Written to cover, at minimum:

- `step` returns a new field per key in `fields`, none mutated, matching
  `TimeIntegrator.advance`'s own already-tested contract extended
  through this call.
- A zero-everywhere field with zero-everywhere boundary conditions stays
  at zero after `step` -- the boundary case an implementation that
  ignores its inputs would also pass, kept only as a sanity scenario
  alongside the one below that a trivial implementation cannot pass.
- Changing a boundary condition's prescribed value changes the
  accumulated derivative at the adjacent cell, without `step`'s own
  accumulation code path branching on `Mesh.is_boundary_face` anywhere
  -- Stage 4 Completion Criterion 1's own bullet, made executable.
- `accumulate_flux_to_cells` reproduces a hand-derived cell array from a
  hand-chosen face-value array on a small, non-square, non-trivially-
  origined mesh -- not sampled, checked for every cell.
- Passing `fields`/`velocity` with a mesh that disagrees with
  `numerics`' own assembled mesh raises a named exception (this task's
  own rejection-path obligation under Stage 4 Completion Criterion 5).

**Criterion 5's other named example is not discharged here, stated
explicitly rather than left as an unrecorded gap** (found during this
task's own review cycle): the Criterion 5 prose above also names "a
field not present in the `AssembledNumerics` it was handed" as an
illustrative rejection condition. `AssembledNumerics` holds live
component instances (advection scheme, diffusion scheme, ...), not
fields, so that phrase does not parse literally against `step`'s actual
signature any more than the mesh one did (the "second reading decision"
above) -- and unlike the mesh one, no buildable reading of it presented
itself while implementing. Left for whoever next has cause to read this
bullet closely to either supply the reading or correct the Criterion 5
prose that named it.

### Discharges

- **Criterion 1**, entirely. *Closed by:* `simulation_orchestrator.feature`'s
  own scenarios above, plus `accumulate_flux_to_cells`'s unit-level
  hand-derived check.
- **Criterion 5**, its own share: the mesh-mismatch rejection scenario
  above.
- **Criterion 6**, its own share: `simulation_orchestrator.feature`
  exists and every scenario in it is bound (`make check-scenarios`).

---

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

**Status: Done, 2026-08-27.** `src/pyflow/engine/numerics/advection.py`
implements `FirstOrderUpwindAdvection` exactly as specified below;
`tests/unit/test_first_order_upwind_advection.py` (binding `tests/
features/first_order_upwind_advection.feature`) exists and passes, at
100% coverage, and `FirstOrderUpwindAdvection` joined `tests/unit/
numerics/test_advection_contract.py`'s parametrised suite with no
existing test body in that file edited. `assembly.py` registers it under
`"first_order_upwind"`; `_NullAdvectionScheme` is deleted, not merely
unregistered. **Audited under `prompts/common/AUDITOR.md`'s stance
(`/code-review high`) before this Status line was written** -- fixed two
real gaps: `docs/architecture/engine.md`'s and `docs/architecture/icds.md`'s
own Advection entries still asserted the registered scheme "computes
nothing" and named TASK-023 as pending, both now false and neither
document touched by this task's first pass; and `_upwind_face_value`
repeated the `isinstance(field, CollocatedField)` check `flux` had
already performed once per call, now typed to avoid it. One finding was
deliberately not applied and is recorded as a deferred follow-up in
`mesh.py`'s own `BoundaryFaceName` docstring, rather than fixed
half-way: narrowing `FirstOrderUpwindAdvection`'s and `assembly.py`'s
`boundary_conditions` mappings from `Mapping[str, BoundaryCondition]` to
`Mapping[BoundaryFaceName, BoundaryCondition]` turned out to ripple
through every test-only factory registered against `assembly.py`'s
registries (`Callable` parameter contravariance rejects a `Mapping[str,
...]`-typed double where `Mapping[BoundaryFaceName, ...]` is required),
which is real but a wider, separate change from this task's own scope.
`make ci` is clean.

### Dependencies

TASK-018 (`AdvectionScheme`), TASK-012 (`Mesh`/`StructuredCartesianMesh`),
TASK-014..016 (`Field`/`ScalarField`/`VectorField`), TASK-019
(`BoundaryCondition`), and TASK-040's own Design decision (a concrete
scheme is constructed with the boundary conditions it needs, keyed by
named edge) -- this task is the first to actually build against that
decision rather than merely establish it.

### Design decisions, recorded here

**A `Mesh` needs to tell a concrete scheme which named boundary a face
lies on, and nothing before this task built that.** `NumericsConfig.
boundary_conditions` is keyed by `north`/`south`/`east`/`west`
(`configuration/schema.py`), but `Mesh`'s own accessors
(`is_boundary_face`, `face_neighbours`) only say *whether* a face is a
boundary face, never *which* named edge -- a gap invisible until a
concrete scheme actually needed to pick the right `BoundaryCondition`
out of the four it was constructed with.

**Decided: `StructuredCartesianMesh.boundary_face_name(face) ->
BoundaryFaceName | None`, additive, off the abstract `Mesh` interface**
-- the same shape TASK-030's own periodic wrapped-neighbour lookup
already commits to for its own analogous need (`docs/planning/
roadmap.md`, TASK-030's Design decision, below): only a structured,
axis-aligned mesh has a natural north/south/east/west concept, so
putting it on the abstract `Mesh` would assume every future
implementation (an unstructured mesh, in particular) has one to give.
`BoundaryFaceName` (`Literal["north", "south", "east", "west"]`) is
defined once in `mesh.py` and reused rather than repeated as a bare
string union. Tested in `tests/unit/test_structured_cartesian_mesh.py`
(the implementation-specific suite, not the shared `Mesh` contract, for
the same reason the method itself is additive) --
`test_boundary_face_name_matches_the_domain_edge_a_face_lies_on` checks
every face of a non-square, non-trivially-origined mesh against the
`(i, j)` index it was built from, independently of `mesh.py`'s own
internal face-id encoding.

**A second decision: what a concrete scheme does when inflow occurs at
a boundary face with no configured `BoundaryCondition` at all** (the
periodic case -- `boundary_condition.py`'s own scope is deliberately
just Dirichlet/Neumann, so `assemble_numerics` resolves no
`BoundaryCondition` object for a periodic-type boundary). Extrapolating
silently (as for a genuine zero-gradient Neumann boundary) would produce
a plausible-looking wrong answer for a periodic boundary, which needs
the *wrapped neighbour's* actual value, not an extrapolation --
precisely the failure mode `docs/practices.md` names repeatedly.
**Decided: raise `UnconfiguredBoundaryFaceError`** (a `ValueError`)
rather than default to extrapolation. Outflow at the same face never
raises it, since the upstream value is the owner's own and the boundary
condition is never consulted either way.

**A third decision: how the face-normal velocity used to pick the
upstream side is interpolated to a boundary face**, where there is no
neighbour cell to average with. Decided: the owner cell's own velocity,
used directly -- the only value available, and consistent with
`docs/handbook/numerical-methods/boundary-conditions.md`'s own
"typically extrapolated from the adjacent cell-centred value" framing
for a boundary's advective treatment generally.

### Artifacts Produced

- `src/pyflow/engine/mesh.py`: `BoundaryFaceName` (the shared
  `Literal["north", "south", "east", "west"]` type) and
  `StructuredCartesianMesh.boundary_face_name(face: int) ->
  BoundaryFaceName | None`.
- `src/pyflow/engine/numerics/advection.py`: `FirstOrderUpwindAdvection`
  (constructed with `boundary_conditions: Mapping[str,
  BoundaryCondition]`) and `UnconfiguredBoundaryFaceError`.
- `src/pyflow/engine/numerics/assembly.py`: `_NullAdvectionScheme`
  deleted; `register_advection_scheme("first_order_upwind", ...)`
  renamed to `FirstOrderUpwindAdvection` (Stage 4's inherited retirement
  obligation, above).
- `tests/features/first_order_upwind_advection.feature` -- see
  Acceptance Criteria, below.

### Implementation

Test-driven throughout, per `docs/practices.md`: `boundary_face_name`'s
own tests written and confirmed to fail (`AttributeError`) before the
method existed; the feature file's scenarios written and confirmed to
fail (`ModuleNotFoundError` on `FirstOrderUpwindAdvection`) before
`advection.py`'s concrete class existed. Every numeric fixture below
(the CFL-stable/unstable timestep pair, the closed-domain conservation
setup) was run and its actual output inspected before being fixed into
the permanent test, rather than hand-derived and trusted blind --
`docs/practices.md`'s "verify implementation details" rule, applied to
a case where the arithmetic is a differential-equation stability
argument, not a closed-form formula a reader could check by eye alone.

### Acceptance Criteria

`tests/features/first_order_upwind_advection.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`) is the criteria; not
restated here as prose. Written to cover, at minimum:

- Every interior face's implied value equals exactly one of its two
  neighbouring cells' own values (never a blend) -- boundedness, for a
  non-monotonic field and a velocity not aligned with either mesh axis,
  so neither a monotonic fixture nor an axis-aligned one could let a
  subtly wrong implementation agree with a right one by coincidence.
- A boundary face with outflow uses the interior cell's own value, never
  the boundary condition's -- and the reverse for inflow, split across
  the Dirichlet (fixed value used directly) and Neumann (extrapolated
  from the interior) shapes.
- Inflow at a boundary with no configured condition raises
  `UnconfiguredBoundaryFaceError` (this task's own rejection-path
  obligation under Stage 4 Completion Criterion 5).
- Bounded at half the CFL limit, the scheme's magnitude never exceeds
  its initial maximum over several timesteps; above twice the CFL limit,
  the same scheme's magnitude grows far beyond it -- boundedness is not
  stability, made executable, per this task's own Intent above.
- Conservation on a closed domain (every boundary cell's velocity
  exactly zero, interior cells nonzero): the field's total is unchanged
  to floating-point tolerance after many timesteps.

### Discharges

- **Stage 4 Completion Criterion 2**, its own share: `assemble_numerics`
  resolves `"first_order_upwind"` to `FirstOrderUpwindAdvection`, not
  `_NullAdvectionScheme` (`test_default_config_resolves_a_real_advection_scheme`).
- **Criterion 3**, its own share: `FirstOrderUpwindAdvection` joined
  `test_advection_contract.py`'s existing parametrised suite with no
  edit to any existing test body in that file.
- **Criterion 4**, its own Advection bullet, entirely -- boundedness and
  conservation, both above.
- **Criterion 5**, its own share: the `UnconfiguredBoundaryFaceError`
  rejection scenario above.
- **Criterion 6**, its own share: `first_order_upwind_advection.feature`
  exists and every scenario in it is bound (`make check-scenarios`).
- **Criterion 7**, its own share: `_NullAdvectionScheme` is deleted from
  `assembly.py` in this same change, not left registered alongside the
  real scheme.

---

## TASK-024

Central Difference Diffusion

**Intent:** the claim is **second-order accuracy on a uniform orthogonal
mesh** (`docs/handbook/numerical-methods/diffusion.md`), which is a
measured convergence rate under mesh refinement, not a qualitative
"the field diffuses". A first-order-accurate implementation diffuses
perfectly plausibly.

**Status: Done, 2026-08-27.** `src/pyflow/engine/numerics/diffusion.py`
implements `CentralDifferenceDiffusion` exactly as specified below;
`tests/unit/test_central_difference_diffusion.py` (binding `tests/
features/central_difference_diffusion.feature`) exists and passes, and
`CentralDifferenceDiffusion` joined `tests/unit/numerics/
test_diffusion_contract.py`'s parametrised suite with no existing test
body in that file edited. `assembly.py` registers it under
`"central_difference"`; `_NullDiffusionScheme` is deleted, not merely
unregistered. `make ci` is clean (`make check-status`'s counts updated
in this same change).

### Dependencies

TASK-018 (`DiffusionScheme`), TASK-012 (`Mesh`/`StructuredCartesianMesh`),
TASK-014..016 (`Field`/`ScalarField`), TASK-019 (`BoundaryCondition`),
TASK-023's own `UnconfiguredBoundaryFaceError`/boundary-aware-construction
precedent, and TASK-040's own Design decision (a concrete scheme is
constructed with the boundary conditions it needs).

### Design decisions, recorded here

**First: the diffusion coefficient (Gamma) has no existing config field,
and `DiffusionScheme.flux`'s signature is fixed to `(self, field)`, so
Gamma cannot be a per-call argument either.** The choice is between a
hardcoded constant and a real `NumericsConfig` field. **Decided: a real
field, `NumericsConfig.diffusion_coefficient: float = 1.0`, validated
positive** -- Gamma is a physical property of what's being transported
(viscosity, thermal diffusivity, ...), not a discretisation choice, and
hiding a physical parameter behind a hardcoded constant is the wrong
default even though neither of this task's own acceptance criteria
(convergence order, conservation) happens to depend on its value. Raised
directly during this task's own design review, not assumed from the
start -- an earlier draft of this decision proposed hardcoding it and
was corrected before implementation, on exactly that reasoning. Threaded
into `CentralDifferenceDiffusion`'s constructor via
`register_diffusion_scheme`'s factory type gaining a second parameter
(`_resolve_with_two_arguments`, a new `assembly.py` helper alongside
`_resolve_with_argument`, since diffusion alone among the six components
now needs two constructor arguments) -- the same "constructed with it,
not handed it after the fact" mechanism `boundary_conditions` already
established (TASK-040).

**Second: the central-difference formula needs the distance between two
cell centroids, and nothing in `mesh.py` returns it.** Decided: a new
**concrete** method, `Mesh.face_centroid_distance(face) -> float`, on
the *abstract* `Mesh` -- not additive on `StructuredCartesianMesh` only,
unlike TASK-023's own `boundary_face_name`. The difference: centroid
distance is a geometric quantity every FVM mesh has, structured or not,
the same category as `cell_volume`/`face_area`/`face_vertices` (already
abstract); `boundary_face_name`'s own "north/south/east/west" concept is
specifically tied to a structured, axis-aligned mesh, which is why *that*
one stayed concrete-only. Built entirely from already-abstract accessors
(`cell_centroid`, `face_neighbours`, `face_vertices`, `face_normal`) --
concrete rather than abstract, the same "provided for free from existing
primitives" shape `is_boundary_face`/`face_normal_from` already
establish -- so every `Mesh` implementation gets it without needing to
override it. Interior face: Euclidean distance between the two
neighbours' own centroids. Boundary face: the owner-centroid-to-face
distance, via the owner-to-face-midpoint vector projected onto
`face_normal` -- generalises correctly without hardcoding axis-aligned
spacing. `tests/unit/test_mesh_contract.py` gained two new
implementation-independent invariants (positive for every face; an
interior face's value agrees with the straightforward centroid-to-
centroid distance); `tests/unit/test_structured_cartesian_mesh.py`
checks the exact formula against known grid spacing.

**Third: the boundary-face diffusive flux formula, resolved per
`BoundaryCondition.kind`.** Dirichlet (`"value"`): the ordinary central
difference between the prescribed boundary value and the owner's own
value, divided by the owner-to-face distance. Neumann (`"gradient"`):
the prescribed gradient *read directly* -- the one place this scheme's
boundary handling differs in kind from `FirstOrderUpwindAdvection`'s:
advection's own Neumann case never reads its condition's numeric value
(zero-order extrapolation only), but diffusion's whole point at a
Neumann boundary *is* the prescribed flux-driving gradient, which is
exactly what `BoundaryCondition`'s "value or gradient, per kind" contract
was built to let a scheme do. No condition configured (the periodic
case) raises `UnconfiguredBoundaryFaceError` -- `diffusion.py`'s own
class, not a shared import from `advection.py`, since each numerics
interface module owns its own exception vocabulary, but the identical
underlying reasoning: never default silently to a plausible-looking
value. Unlike advection's version, there is no inflow/outflow carve-out
-- diffusion has no flow direction, so *every* boundary face needs a
configured condition, not only the ones flow happens to enter through.

**Fourth: how to measure "second-order accuracy" without TASK-025 (RK4)
existing yet.** Rather than real time-stepping, the convergence scenario
measures the *spatial* operator alone: for a smooth analytic field (the
Laplacian eigenfunction $\sin(\pi x)\sin(\pi y)$ on a unit square),
`accumulate_flux_to_cells(mesh, diffusion.flux(field))` is the discrete
Laplacian; compared against the exact analytic Laplacian across three
mesh resolutions, with a least-squares log-log fit for the observed
order. **A second, narrower decision fell out of actually running this
test**, not anticipated in advance: the discrete Laplacian error was
measured only over *strictly interior* cells (no face touching the
boundary), not every cell. A boundary cell's own Laplacian estimate
depends on the boundary formula above (Decision Three), whose own local
truncation error is a one-sided difference against an exact prescribed
value -- first order, not second, by direct Taylor expansion -- and nothing
in `docs/handbook/numerical-methods/diffusion.md` claims otherwise; it
states second-order accuracy for the *interior* central-difference
formula only. Measuring L-infinity error over every cell including the
boundary layer would have shown an observed order close to one, not two
-- not a bug, but a stronger and *undocumented* claim than the one this
task actually needs to make. Verified directly, not assumed: a
deliberate mutation of the boundary formula alone (see Implementation,
below) left the convergence scenario passing, confirming it measures
only what it claims to.

### Artifacts Produced

- `src/pyflow/engine/mesh.py`: `Mesh.face_centroid_distance(face: int)
  -> float`, concrete on the abstract base.
- `src/pyflow/engine/numerics/diffusion.py`: `CentralDifferenceDiffusion`
  and `UnconfiguredBoundaryFaceError`.
- `src/pyflow/engine/numerics/assembly.py`: `_NullDiffusionScheme`
  deleted; `register_diffusion_scheme`'s factory type gains
  `diffusion_coefficient`; `_resolve_with_two_arguments`, a new helper
  alongside `_resolve_with_argument`.
- `src/pyflow/configuration/schema.py`:
  `NumericsConfig.diffusion_coefficient: float = 1.0`.
- `tests/features/central_difference_diffusion.feature` -- see
  Acceptance Criteria, below.

### Implementation

**Mostly test-driven, per `docs/practices.md` -- with one real deviation,
recorded here rather than smoothed over, per root `CLAUDE.md`'s
Integrity section.** `face_centroid_distance`'s own contract/
implementation-specific tests, `NumericsConfig.diffusion_coefficient`'s
own load/reject tests, and `CentralDifferenceDiffusion`'s join to
`test_diffusion_contract.py`'s parametrised suite were each written and
confirmed to fail (`AttributeError`/`NameError`/`ImportError`) before
their own implementation existed, in that order. `central_difference_
diffusion.feature`'s own scenarios were **not** written first --
`CentralDifferenceDiffusion` already existed by the time the feature
file was drafted (built to satisfy the contract-suite join above), so
its first run against every scenario was green rather than red, which is
exactly the ordering `docs/practices.md`'s TDD rule exists to prevent.
Recovered rather than left unexamined: the implementation was
deliberately mutated twice after the fact (dropping the Gamma
multiplication entirely; separately corrupting both boundary-formula
branches) and every scenario expected to catch each specific bug was
confirmed to fail, with the scenarios *not* expected to catch a given
bug confirmed to keep passing (the interior-formula and convergence-order
scenarios, in particular, correctly unaffected by the boundary-formula
mutation -- direct evidence for Design Decision Four's own claim that the
convergence measurement is genuinely isolated from boundary accuracy).
The implementation was then restored to its correct form. This
demonstrates the scenarios discriminate a wrong implementation from a
right one; it does not change that they were built in the wrong order,
which is recorded here as what actually happened rather than
retrospectively presented as clean red-green.

### Acceptance Criteria

`tests/features/central_difference_diffusion.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`) is the criteria; not
restated here as prose. Written to cover, at minimum:

- Every interior face's flux equals Gamma times the neighbouring cells'
  value difference divided by their centroid distance -- the central-
  difference formula itself, checked directly against an independently
  computed expected value, not by calling back into the scheme under
  test.
- A boundary face with a Dirichlet condition uses the central difference
  to the prescribed value, over the owner-to-face distance; a boundary
  face with a Neumann condition uses the prescribed gradient directly,
  regardless of the owner's own value -- the two boundary shapes, split,
  per Design Decision Three above.
- A boundary face with no configured condition raises
  `UnconfiguredBoundaryFaceError` (this task's own rejection-path
  obligation under Stage 4 Completion Criterion 5).
- Second-order accuracy under mesh refinement (three resolutions,
  doubling), measured over strictly interior cells against a known exact
  Laplacian, with a fitted convergence order close to two -- Design
  Decision Four above, made executable.
- Conservation under zero-flux (Neumann, zero-gradient) boundaries on
  every edge: the field's total is unchanged to floating-point tolerance
  after many timesteps, mirroring TASK-023's own closed-domain
  conservation scenario.

### Discharges

- **Stage 4 Completion Criterion 2**, its own share: `assemble_numerics`
  resolves `"central_difference"` to `CentralDifferenceDiffusion`, not
  `_NullDiffusionScheme` (`test_default_config_resolves_a_real_diffusion_scheme`).
- **Criterion 3**, its own share: `CentralDifferenceDiffusion` joined
  `test_diffusion_contract.py`'s existing parametrised suite with no
  edit to any existing test body in that file.
- **Criterion 4**, its own Diffusion bullet, entirely -- second-order
  accuracy and conservation, both above.
- **Criterion 5**, its own share: the `UnconfiguredBoundaryFaceError`
  rejection scenario above.
- **Criterion 6**, its own share: `central_difference_diffusion.feature`
  exists and every scenario in it is bound (`make check-scenarios`).
- **Criterion 7**, its own share: `_NullDiffusionScheme` is deleted from
  `assembly.py` in this same change, not left registered alongside the
  real scheme.

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

**Status: Done, 2026-08-27.** `src/pyflow/engine/numerics/
time_integrator.py` implements `RK4Integrator` exactly as specified
below; `tests/unit/test_rk4_time_integration.py` (binding `tests/
features/rk4_time_integration.feature`) exists and passes, and
`RK4Integrator` joined `tests/unit/numerics/
test_time_integrator_contract.py`'s parametrised suite as a third
factory. `assembly.py` registers it under `"rk4"`; `_NullTimeIntegrator`
is deleted, not merely unregistered. `make ci` is clean (`make
check-status`'s counts updated in this same change).

### Dependencies

TASK-020 (`TimeIntegrator`), TASK-014..016 (`Field`/`ScalarField`),
TASK-040's own `simulation.step` (the one caller this task's own
interface change touches).

### Design decisions, recorded here

**A genuine architecture problem, found before any implementation code
was written, not during it: `TimeIntegrator.advance`'s existing signature
cannot support RK4 at all.** RK4 evaluates the derivative three more
times at intermediate states within the timestep
(`docs/handbook/numerical-methods/time-integration.md`), but TASK-020's
`advance(fields, derivatives: Mapping[str, torch.Tensor], dt)` only ever
receives a single precomputed snapshot, and `simulation.step` (TASK-040)
computed that snapshot once, before calling `advance`, with no way for
an integrator to ask for the derivative at any other state -- confirmed
by reading `step`'s own source, not assumed. This is exactly
`docs/practices.md`'s "hold a design session before implementing"
trigger (a criterion -- "fourth-order accurate" -- that cannot honestly
be met without settling this first), and `adr/ADR-003-modular-numerical-
strategies.md` names the resolution in advance: "If an interface itself
proves inadequate once real implementations exist, revising it should be
an explicit, recorded decision (a new or amended ADR), not a silent
change." Put to the maintainer directly rather than guessed: extend the
interface, accepting a real breaking change to a previously-"Done" Stage
3 interface, over scoping RK4 to a restricted problem class (e.g. one
where the derivative is analytically re-derivable from a single sample,
such as assuming it is proportional to the field's own value) that would
be a plausible-looking wrong answer the moment it drives the real,
generally non-proportional, spatially-varying engine dynamics -- the
exact failure class `docs/practices.md` names repeatedly.

**Decided and recorded as `adr/ADR-008-time-integrator-derivative-
callable.md`: `TimeIntegrator.advance`'s second parameter becomes
`derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]`,
replacing the old `derivatives: Mapping[str, torch.Tensor]`.** Calling
it with the current `fields` reproduces exactly what the old signature
offered -- everything `_EulerIntegrator`-shaped schemes need; a
multi-stage scheme calls it again at each intermediate state it
constructs. `simulation.step` now builds this callable as a closure over
`numerics`/`velocity`/`mesh` rather than a precomputed dict; `velocity`
stays fixed across every evaluation within one `step` call, since `step`
only ever advances `fields` (Stage 5's pressure coupling is what will
eventually advance velocity). This is a real, breaking migration of an
already-"Done" Stage 3 interface -- `test_time_integrator_contract.py`'s
own `_EulerIntegrator`/`_DoubleStepIntegrator` test doubles and
`test_simulation.py`'s own local `_EulerIntegrator` double all needed
their call sites adapted (same arithmetic, new call shape), which is
genuinely different from TASK-023/024's own "join adds a factory, edits
nothing existing" precedent -- recorded as such rather than presented as
that same shape.

**`RK4Integrator` lives in `time_integrator.py` itself, not a new
file** -- the same "interface and its first concrete scheme share one
module" precedent `advection.py`/`diffusion.py` already established.
`_advanced_by(fields, deltas)` is a small shared helper
(`.copy()`-then-`.values[:] =`, the same shape `_EulerIntegrator` already
used) reused four times: building each of the three intermediate stages
and the final weighted combination.

**No rejection path of its own, matching Euler/DoubleStep's own
precedent (TASK-020's design decision).** A mismatched key between
`fields` and what `derivative` returns is a plain `KeyError` from
reading the mapping, not a condition this interface needs to name and
reject -- Stage 4 Completion Criterion 5 has nothing for this task to
add.

**Convergence-order and multi-stage-evaluation scenarios both use a
manufactured derivative, never the real mesh/numerics** -- exactly what
Stage 4 Completion Criterion 4's own bullet asks for ("a manufactured or
zero spatial term"), and the mirror image of TASK-024's own isolation
(which measured spatial order with no time-stepping at all). Exponential
decay, `dy/dt = -k*y` per cell, closed-form `y(t) = y0 * exp(-k*t)`, on a
non-uniform-valued `ScalarField`. **A second claim was found necessary
alongside the accuracy one, not assumed sufficient on its own:** an
accuracy scenario alone cannot distinguish genuine four-stage RK4 from a
scheme that degenerates to fewer evaluations, or that re-evaluates but
reuses a stale intermediate state, unless the test problem happens to
make that distinction visible -- so a second scenario records every
state the derivative is called with and asserts all four are pairwise
distinct. **Verified directly, not assumed correct on inspection:** an
earlier draft of this second scenario only asserted "at least one pair
differs", and a deliberate mutation (stages three and four re-using
stage two's already-computed state, rather than re-evaluating) revealed
that weaker check still passed -- state one (`fields`) trivially differs
from state two, which was enough to satisfy "at least one pair" even
though three of the four calls were identical. Tightened to require
every pair pairwise distinct; the same mutation was re-run afterward and
now correctly fails both this scenario and the accuracy one (RK4
collapsing toward a two-stage method under-shoots fourth order). A
second mutation (dropping the final weighted combination to Euler's
`dt * k1` alone, while still performing all four evaluations) was
confirmed to fail the accuracy scenario but *not* the evaluation-count
scenario, exactly as expected -- each scenario catches the specific
defect it claims to, not a coincidentally-overlapping one.

### Artifacts Produced

- `src/pyflow/engine/numerics/time_integrator.py` -- widened `advance`
  signature; `RK4Integrator`.
- `src/pyflow/engine/simulation.py` -- `step` builds the `derivative`
  closure.
- `adr/ADR-008-time-integrator-derivative-callable.md`.
- `tests/features/rk4_time_integration.feature`,
  `tests/unit/test_rk4_time_integration.py`.

### Implementation

Strict TDD throughout, unlike TASK-024's own recorded deviation: the
interface-migration edits to `test_time_integrator_contract.py` and
`test_simulation.py` (adapting existing test doubles to the new callable
shape, adding the `rk4` factory), `test_assembly.py`'s real-scheme
resolution test, and `test_rk4_time_integration.py`'s own two scenarios
were all written first and confirmed to fail
(`ImportError`/`AttributeError`, since `RK4Integrator` and the widened
signature did not yet exist) before `time_integrator.py`/`simulation.py`
were touched. The two mutation-testing rounds under Design Decisions
above happened after the suite was fully green, as a check on the
suite's own teeth, not as part of reaching green in the first place.

### Acceptance Criteria

`tests/features/rk4_time_integration.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`) is the criteria; not
restated here as prose. Written to cover, at minimum:

- The derivative is evaluated exactly four times per step, at four
  states that are pairwise genuinely different from one another -- not
  inferred from the accuracy result, which alone cannot distinguish
  genuine four-stage evaluation from a degenerate scheme that happens to
  be accurate on an easy problem.
- Fourth-order accuracy under timestep refinement (four decreasing `dt`
  values), measured against a manufactured exponential-decay ODE with a
  known exact solution -- no real mesh or spatial scheme involved, so
  spatial error cannot dominate the measured temporal order.

### Discharges

- **Stage 4 Completion Criterion 2**, its own share: `assemble_numerics`
  resolves `"rk4"` to `RK4Integrator`, not `_NullTimeIntegrator`
  (`test_default_config_resolves_a_real_time_integrator`).
- **Criterion 3**, its own share: `RK4Integrator` joined
  `test_time_integrator_contract.py`'s existing parametrised suite --
  unlike TASK-023/024's own join, this one required adapting existing
  test bodies too, because the interface itself changed underneath them
  (Design Decisions above), not because the join mechanism differs.
- **Criterion 4**, its own Time Integrator bullet, entirely -- fourth-
  order accuracy, isolated from spatial error, above.
- **Criterion 5**: no new rejection scenario -- `RK4Integrator` has no
  rejection conditions of its own, the same as Euler/DoubleStep
  (Design decisions above).
- **Criterion 6**, its own share: `rk4_time_integration.feature` exists
  and every scenario in it is bound (`make check-scenarios`).
- **Criterion 7**, its own share: `_NullTimeIntegrator` is deleted from
  `assembly.py` in this same change, not left registered alongside the
  real scheme.

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

**Status: Done, 2026-08-27.** `src/pyflow/engine/numerics/
linear_solver.py` implements `ConjugateGradientSolver` exactly as
specified below; `tests/unit/test_conjugate_gradient_solver.py` (binding
`tests/features/conjugate_gradient_solver.feature`) exists and passes,
and `ConjugateGradientSolver` joined `tests/unit/numerics/
test_linear_solver_contract.py`'s parametrised suite with no edit to any
existing test body in that file -- unlike TASK-025's own join, since
`LinearSolver.solve`'s signature needed no change here. `assembly.py`
registers it under `"conjugate_gradient"`; `_NullLinearSolver` is
deleted, not merely unregistered. `make ci` is clean (`make
check-status`'s counts updated in this same change).

### Dependencies

TASK-022 (`LinearSolver`), TASK-024 (`CentralDifferenceDiffusion`,
reused to build this task's own test fixture -- see Design Decision Four),
TASK-040 (`accumulate_flux_to_cells`, same reuse).

### Design decisions, recorded here

**First: `LinearSolver.solve(matrix, rhs)` and `NumericsConfig.
linear_solver_tolerance`/`linear_solver_max_iterations` already exist
and already need nothing new (TASK-022's own design decision: tolerance
and iteration limit are a concrete solver's own tunables, bound at
construction, not passed per call).** The only registry change is the
same shape TASK-024 already established for `diffusion_coefficient`:
`register_linear_solver`'s factory type widens from `Callable[[],
LinearSolver]` to `Callable[[float, int], LinearSolver]`, resolved via
`assembly.py`'s existing generic `_resolve_with_two_arguments` helper
(already built for TASK-024, reused rather than duplicated). No ADR
needed, unlike TASK-025 -- nothing about the interface itself changes.

**Second, the real content of this task: reading "pin a reference cell,
or project the constant mode out each iteration"
(`docs/handbook/numerical-methods/linear-solvers.md`) literally and
applying it *unconditionally* is wrong, and was caught before any test or
implementation code existed, by a throwaway numerical prototype, not by
inspection.** A generic well-conditioned SPD system (the contract
suite's own `[[4, 1], [1, 3]]` fixture, `x_true = [1.5, -2.25]`) solved
by CG that unconditionally projects the residual's mean out every
iteration reports `converged=True` after one iteration and returns
`[1.8, -1.8]` -- a confident, wrong answer, not a crash or a
non-convergence flag. Exactly the "plausible-looking wrong answer"
failure mode `docs/practices.md` names repeatedly. **Decided: the
projection is gated, computed once per `solve` call from the matrix
itself** -- `matrix @ ones` close to zero relative to `matrix`'s own norm
signals the constant vector is in the null space (true for the real
PISO-shaped matrix, false for the contract suite's own generic systems,
confirmed both ways by the same prototype). When the gate is false, CG
runs exactly as every textbook describes it; when true, the constant
mode is projected out of the residual after every update. A
degenerate-direction guard (curvature `direction @ (matrix @ direction)`
below a tiny epsilon stops the loop rather than dividing by ~0) is
included as ordinary defensive practice; it is marked `# pragma: no
cover` in the implementation with a comment explaining why this
repository's own fixtures cannot realistically reach it (a nonzero
`direction` this algorithm ever constructs always has strictly positive
curvature, by construction, once the gate is correctly applied) --
`pyproject.toml`'s own `[tool.coverage.report]` section already has
precedent for this (the C1a/C1b subprocess-coverage gap), and
`src/pyflow/bootstrap.py` already uses the same directive for a
structurally-unreachable branch.

**Third, an honest finding, not smoothed over (root `CLAUDE.md`'s
Integrity section): mutation testing showed the projection *itself* --
as opposed to the gate that decides whether to apply it -- cannot be
shown to matter at any fixture size this repository can realistically
test.** Disabling the projection entirely (gate forced false even for
the genuine semi-definite fixture) was expected to degrade the solution
-- instead, both of this task's own scenarios kept passing unchanged.
Investigated directly, not left as a surprising green: starting from
`x0 = 0` with a consistent (zero-mean) `rhs` already keeps every CG
iterate in `range(matrix)` in exact arithmetic (a Krylov-subspace
argument -- `range` is `matrix`-invariant and contains `r0`), so the
projection is a defensive correction against floating-point roundoff
drift accumulating over *many* iterations, not what makes convergence
possible at all. A follow-up check at larger problem sizes (up to 225
cells, ~72 CG iterations, a real matrix built the same way as Design
Decision Four) found the drift without projection still only around
machine epsilon (`~1e-16`) -- nowhere near enough to matter at any
tolerance this project configures, and consistent with `icds.md`'s own
framing of PyFlow's MVP meshes as small. **What mutation testing did
confirm has real teeth: the *gate* itself** (Design Decision Two's
unconditional-projection mutation, above, caught immediately by the
existing generic contract-suite systems) **and non-convergence
reporting** (a mutation forcing `converged = True` unconditionally was
caught by this task's own non-convergence scenario). The projection code
stays -- it is cheap, mathematically justified, matches the handbook's
own explicit recommendation, and is expected to matter once a later
stage's meshes grow past what a dense solver and small iteration counts
can absorb -- but its own necessity is recorded as *not empirically
demonstrated* at MVP scale, rather than presented as verified when it
was not.

**Fourth: the semi-definite acceptance-criteria fixture is built from
the real diffusion operator, not a hand-typed matrix.**
`CentralDifferenceDiffusion`/`accumulate_flux_to_cells` (TASK-024/040)
on a small `StructuredCartesianMesh` with a zero-gradient condition on
every edge -- "every boundary prescribes velocity, none prescribes
pressure" made concrete -- assembled column by column from unit basis
fields: `matrix[:, j] = -accumulate_flux_to_cells(mesh,
diffusion.flux(e_j))`, negated because the raw operator this scheme
produces is negative semi-definite (the standard sign for a discrete
Laplacian), while a pressure-correction system is posed as the positive
semi-definite version. This is the closest available approximation to
"the system PISO actually produces" since PISO itself doesn't exist yet
(TASK-027) -- verified directly before being written into a test:
symmetric to floating-point tolerance, row sums ~1e-14 (zero), exactly
one eigenvalue ~0 via `torch.linalg.eigvalsh`, the rest strictly
positive. `rhs` is chosen with zero mean -- the compatibility condition
a real divergence field satisfies by mass conservation
(`icds.md`'s own note), not an arbitrary vector.

### Artifacts Produced

- `src/pyflow/engine/numerics/linear_solver.py` -- `ConjugateGradientSolver`.
- `src/pyflow/engine/numerics/assembly.py` -- widened
  `register_linear_solver`/`_linear_solver_registry`.
- `tests/features/conjugate_gradient_solver.feature`,
  `tests/unit/test_conjugate_gradient_solver.py`.

### Implementation

Strict TDD: `test_linear_solver_contract.py`'s new factory,
`test_assembly.py`'s real-scheme resolution test, and both of
`test_conjugate_gradient_solver.py`'s scenarios were written and
confirmed to fail (`ImportError`) before `ConjugateGradientSolver`
existed. The numerical prototyping under Design Decisions Two and Three
happened *before* any of those tests were written, using a disposable
script (not committed) -- exploratory verification of the algorithm's
own correctness, distinct from the TDD cycle for the acceptance criteria
themselves. Mutation testing (unconditional projection; projection
disabled entirely; always-converged) ran after the suite was green, the
same "check the suite's own teeth" pass TASK-024/025 both used.

### Acceptance Criteria

`tests/features/conjugate_gradient_solver.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`) is the criteria; not
restated here as prose. Written to cover, at minimum:

- Converges on the positive-semi-definite system built per Design
  Decision Four: reports `converged`, the residual `rhs - matrix @
  solution` is close to zero, and the solution stays bounded (finite,
  within a generous magnitude bound) -- not just "runs without raising".
- Non-convergence is reported, not returned as a plausible answer: a
  case with an iteration limit too low to reach the configured tolerance
  reports `converged=False` and `iterations` equal to that limit.

### Discharges

- **Stage 4 Completion Criterion 2**, its own share: `assemble_numerics`
  resolves `"conjugate_gradient"` to `ConjugateGradientSolver`, not
  `_NullLinearSolver` (`test_default_config_resolves_a_real_linear_solver`).
- **Criterion 3**, its own share: `ConjugateGradientSolver` joined
  `test_linear_solver_contract.py`'s existing parametrised suite with no
  edit to any existing test body in that file.
- **Criterion 4**, its own Linear Solver bullet, entirely -- the
  positive-semi-definite convergence claim and the non-convergence
  distinguishability claim, both above.
- **Criterion 5**: no new rejection scenario -- `ConjugateGradientSolver`
  has no rejection conditions of its own, the same reasoning as every
  other concrete `LinearSolver`/`TimeIntegrator` in this repository
  (symmetry is a mathematical precondition, never validated at runtime).
- **Criterion 6**, its own share: `conjugate_gradient_solver.feature`
  exists and every scenario in it is bound (`make check-scenarios`).
- **Criterion 7**, its own share: `_NullLinearSolver` is deleted from
  `assembly.py` in this same change, not left registered alongside the
  real scheme.

---

## TASK-027

PISO Pressure Coupling

**Status: Done, 2026-08-27, Stage 4's sixth task.**
`src/pyflow/engine/numerics/pressure_coupling.py` implements `PISO`;
`src/pyflow/engine/numerics/gradient.py`/`divergence.py` implement
`GreenGaussGradient`/`GreenGaussDivergence`, both built by this task --
see Design decision One below.

**Intent:** the claim is that a single correction pass **measurably and
boundedly reduces the divergence** of a manufactured provisional velocity
field, checked cell by cell against a stated tolerance -- not "the
pressure loop runs", not "the flow looks incompressible". **Checked in
isolation, against a constructed system, not against Stage 5's real
lid-driven-cavity demo, which does not exist yet** -- the full
"reaches a configured tolerance via monotonic multi-pass correction"
claim belongs to TASK-033 (Stage 5), not this task; see Design decision
Two below and `docs/practices.md`, "A criterion whose strong reading
depends on a later task must say so when drafted" (this Intent line
originally read like TASK-033's own claim, corrected 2026-08-27 before
implementation started, in the same pass that added that rule).

**Design decision One, resolved 2026-08-26 (`docs/practices.md`, "hold a
design session when intent is ambiguous" -- raised while auditing Stage
4's own Completion Criteria, not by anything TASK-027's original Intent
line above had flagged):** PISO cannot correct a provisional velocity
field without a pressure gradient (`u_corrected = u* - dt/rho * grad(p)`)
and cannot form the pressure-correction equation's right-hand side
without a velocity divergence (`div(u*)`) -- `GradientScheme` and
`DivergenceScheme` (TASK-018, Stage 3) are exactly these, and neither
has a concrete implementation anywhere. Nothing in this Stage's task
list had assigned building one, because neither is one of `adr/ADR-003`'s
six configuration-selected components (TASK-018's own design decision:
"nothing has yet identified a second implementation a user would choose
between") -- so they never went through the registry/MVP-name pattern
Criterion 2 and the `_Null*` retirement obligation both describe, and
were absent from both without anyone noticing until this question was
asked directly.

**Decided: this task owns building both concrete implementations**, as
its own Artifacts, constructed and held internally rather than resolved
by name through `assemble_numerics` -- there is no registry for either,
and building one now would be exactly the P-016 speculation this
project has refused everywhere else, since nothing has identified a
second Gradient or Divergence implementation to choose between.
- **Both are boundary-condition-aware at their own construction**, the
  same pattern this Stage's Advection/Diffusion schemes already use
  (TASK-040's own Design decision, above) -- a pressure gradient at a
  wall needs pressure's own boundary condition (typically zero-normal-
  gradient, an impermeable wall), and neither interface's abstract
  method takes one.
- **Divergence's own face-to-cell reduction reuses TASK-040's shared
  Gauss-theorem accumulation helper** (see TASK-040's own Artifacts,
  below) rather than reimplementing the same `sum(value * area *
  outward_normal) / volume` arithmetic a second time -- `Divergence`
  needs one extra step first (interpolating `field`'s cell-centred
  vector values to a face-normal component, which `Advection`/
  `Diffusion` do not, since they are face-valued already), but the
  accumulation itself is the identical geometric operation, and this
  project has already been burned once (Stage 3's `boundary_conditions`
  validation, `docs/practices.md`) by a fact recomputed in two places
  drifting apart.
- **Passing `test_gradient_contract.py`/`test_divergence_contract.py`
  (TASK-018, Stage 3) is still required of both**, exactly as Criterion 3
  already requires of the six named components, even though neither
  Gradient nor Divergence is one of them -- the contract-suite
  discipline is not conditional on a component having a configuration
  field, and a real implementation joins the existing parametrised
  fixture list the same way as any of the six.

**Design decision Two, resolved 2026-08-27, a second design session**
(`docs/practices.md`, "hold a design session when intent is ambiguous"),
**raised by the implementer while starting this task, not by an audit**:
what does "divergence-free to a stated tolerance" actually require on
PyFlow's mesh, and is it achievable inside this task's own scope?

Verified directly, before writing any test or implementation code, with
disposable prototype scripts (not committed): a naive per-cell
correction (`u_corrected = u* - dt * grad(p)`, `grad` computed via
Green-Gauss from a pressure field solved against the compact,
already-symmetric Laplacian `CentralDifferenceDiffusion` gives) reduces
the divergence of a manufactured provisional field by roughly 10-50%
depending on the fixture, not to near zero. Two more sophisticated
attempts -- a face-normal-derivative ("compact") gradient reconstruction,
and genuine Rhie-Chow momentum interpolation run across up to seven
correction passes -- were tried and measured; the compact-gradient
reconstruction made the residual *larger* than the uncorrected value
(amplifying the checkerboard mode instead of suppressing it), and the
multi-pass Rhie-Chow attempt improved by only a few percent per pass
(1.50 to 1.05 over seven passes on one fixture), converging far too
slowly to be useful. The common cause, proven algebraically (the discrete
integration-by-parts identity `sum(div(F)*phi*V) == -sum(F . grad(phi)*V)`
fails by a real, nonzero, per-face amount for the naive Green-Gauss
gradient/divergence pair, confirmed numerically before trusting the
algebra) and confirmed structurally (composing them into a Poisson
matrix gives one that is provably not symmetric, so `ConjugateGradientSolver`
-- the only registered `LinearSolver`, which requires a symmetric matrix
as a mathematical precondition -- cannot even be asked to solve it):
**PyFlow's mesh is collocated, and suppressing pressure-velocity
decoupling under repeated correction is exactly what Rhie-Chow
interpolation exists for, and Rhie-Chow only converges paired with a
momentum-equation re-solve between passes** -- coefficients this task's
own interface (`correct(provisional_velocity)`, no `dt`, no momentum
system, no outer-loop state) has no way to obtain, and building them
would mean building the momentum-equation machinery TASK-031/032/033
(Stage 5) are what this project has already assigned to build it.

**Decided, after two rounds of user consultation given the size of the
finding:** this task's own claim is scoped to what a single correction
pass can honestly deliver, checked in isolation -- Stage 4 Completion
Criterion 4's own bullet and this task's Intent line above were both
corrected in the same change to say so explicitly, and
`docs/practices.md` gained a new standing rule ("A criterion whose
strong reading depends on a later task must say so when drafted") so the
next task drafted with this shape states its own boundary the first
time, not after an implementer discovers it experimentally. Concretely:
- **`PressureCoupling.correct` gains a second parameter, `dt: float`**
  -- the interface widens from `correct(provisional_velocity)` to
  `correct(provisional_velocity, dt)`, the same category of change
  TASK-025's `TimeIntegrator.advance` widening was (a real, audited
  interface change, not a registry-only addition) -- needed to give the
  returned pressure field's units a real physical meaning
  (`u_corrected = u* - dt * grad(p)`, density folded to 1 per `fvm.md`'s
  own documented kinematic-pressure convention, since `NumericsConfig`
  has no density field and none is needed elsewhere yet).
- **The pressure-correction Poisson equation is solved via the compact,
  already-symmetric Laplacian `CentralDifferenceDiffusion` gives**
  (`diffusion_coefficient=1.0`, pressure's own zero-gradient boundary
  condition on every edge -- constructed internally, the impermeable-wall
  assumption Design decision One above already named), reusing TASK-024's
  own tested scheme rather than composing `GradientScheme`/
  `DivergenceScheme` into a matrix, which Design decision Two's own
  finding above proved is not symmetric and therefore not solvable by
  `ConjugateGradientSolver` at all.
- **The concrete `GradientScheme`/`DivergenceScheme` this task builds are
  still both real, necessary, and exercised**: `DivergenceScheme` computes
  `div(u*)`, the Poisson equation's right-hand side; `GradientScheme`
  computes the cell-centred pressure gradient the returned corrected
  velocity is built from. Neither is decorative -- the finding above is
  about what their *composition* cannot be used for (the matrix), not
  about whether either is used.

### Artifacts Produced

- `src/pyflow/engine/numerics/gradient.py` -- `GreenGaussGradient`,
  `UnconfiguredBoundaryFaceError`.
- `src/pyflow/engine/numerics/divergence.py` -- `GreenGaussDivergence`,
  `UnconfiguredBoundaryFaceError`, `IncompatibleVectorFieldError`.
- `src/pyflow/engine/numerics/pressure_coupling.py` -- `PISO`,
  `_ZeroGradientPressureCondition`, `PressureSolveDidNotConvergeError`;
  `PressureCoupling.correct` widened with `dt`
  (`adr/ADR-009-pressure-coupling-dt.md`).
- `src/pyflow/engine/numerics/assembly.py` -- widened
  `register_pressure_coupling`/`_pressure_coupling_registry` to take
  `boundary_conditions`.
- `src/pyflow/engine/simulation.py` -- `AssembledNumerics`'s import moved
  behind `TYPE_CHECKING` (a real circular import found while importing
  `pressure_coupling.py`, which now needs `accumulate_flux_to_cells` from
  this module; costs nothing at runtime since `from __future__ import
  annotations` already makes the annotation lazy).
- `adr/ADR-009-pressure-coupling-dt.md`.
- `tests/features/piso_pressure_coupling.feature`,
  `tests/unit/test_piso_pressure_coupling.py`.

### Implementation

Strict TDD: `test_pressure_coupling_contract.py`'s widened `correct`
signature and new `piso` factory, `test_gradient_contract.py`'s/
`test_divergence_contract.py`'s new `GreenGaussGradient`/
`GreenGaussDivergence` fixtures and their own dedicated correctness/
rejection tests, `test_assembly.py`'s real-resolution and
boundary-conditions-threading tests, and both of
`test_piso_pressure_coupling.py`'s scenarios were written and confirmed
to fail (`ImportError`/`AttributeError`) before `GreenGaussGradient`/
`GreenGaussDivergence`/`PISO` existed.

The numerical investigation under Design decision Two -- the naive
per-cell correction, the compact-gradient reconstruction, the multi-pass
Rhie-Chow attempt, the discrete integration-by-parts identity, and the
composed-matrix symmetry check -- happened *before* any of those tests
were written, using disposable scripts (not committed): exploratory
verification of what the algorithm could and could not honestly claim,
distinct from the TDD cycle for the acceptance criteria themselves, the
same separation TASK-025/026 both used. Two rounds of user consultation
(`AskUserQuestion`) resolved the resulting scope question before
implementation started, the same escalation TASK-025's own interface
question used, given the size of the finding and its effect on the
Stage's own Completion Criteria.

Mutation testing ran after the suite was green: removing `PISO`'s own
convergence check, flipping the velocity-correction sign, replacing
`GreenGaussGradient`'s/`GreenGaussDivergence`'s interior face averaging
with an owner-only value, and threading an empty mapping into the
pressure-coupling factory instead of the resolved one -- each caught by
an existing test, none requiring a new one.

### Acceptance Criteria

`tests/features/piso_pressure_coupling.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`) is the criteria; not
restated here as prose. Written to cover, at minimum:

- A single correction pass measurably and boundedly reduces the
  divergence of a manufactured, non-axis-aligned provisional velocity
  field on a closed box (every boundary prescribes zero normal
  velocity) -- checked cell by cell against a stated tolerance (70% of
  the provisional field's own maximum divergence magnitude, real margin
  above the roughly 46-54% reduction actually measured on this fixture),
  and the maximum magnitude strictly decreases. Checked in isolation,
  against a constructed system, not against Stage 5's real
  lid-driven-cavity demo, which does not exist yet.
- Non-convergence in the pressure solve is reported, not returned as a
  plausible answer: a `LinearSolver` that never reports convergence
  causes `PressureSolveDidNotConvergeError`, not a silently-wrong
  corrected velocity.

### Discharges

- **Stage 4 Completion Criterion 2**, its own share: `assemble_numerics`
  resolves `"piso"` to `PISO`, not `_NullPressureCoupling`
  (`test_default_config_resolves_a_real_pressure_coupling`).
- **Criterion 3**, its own share, for three interfaces at once: `PISO`
  joined `test_pressure_coupling_contract.py`'s existing parametrised
  suite with no edit to any existing test body; `GreenGaussGradient`/
  `GreenGaussDivergence` joined `test_gradient_contract.py`'s/
  `test_divergence_contract.py`'s own suites the same way, even though
  neither interface is one of the six `adr/ADR-003` components.
- **Criterion 4**, its own Pressure-Velocity Coupling bullet, scoped to
  what this task actually claims (see the bullet's own text, corrected
  2026-08-27, and Design decision Two above) -- both of this feature
  file's scenarios.
- **Criterion 5**: `GreenGaussGradient`'s/`GreenGaussDivergence`'s own
  `UnconfiguredBoundaryFaceError` and `GreenGaussDivergence`'s own
  `IncompatibleVectorFieldError`, each exercised against real bad input
  in `test_gradient_contract.py`/`test_divergence_contract.py`, not only
  inherited untested; `PISO`'s own `PressureSolveDidNotConvergeError`,
  exercised by this task's own second scenario.
- **Criterion 6**, its own share: `piso_pressure_coupling.feature`
  exists and every scenario in it is bound (`make check-scenarios`); its
  own fixture is non-square, non-trivially-origined, and its velocity
  field is not aligned with either mesh axis.
- **Criterion 7**, its own share: `_NullPressureCoupling` is deleted from
  `assembly.py` in this same change, not left registered alongside the
  real scheme.

---

## TASK-028

Dirichlet Boundary

**Status: Done, 2026-08-28, Stage 4's seventh task.**
`src/pyflow/engine/numerics/boundary_condition.py` implements
`DirichletBoundaryCondition`.

**Intent:** the criterion is what the *interior scheme* computes at a
boundary face, not what the condition object returns when asked. A
condition can return the right face value and still be wired into the
flux computation wrongly; only the second is the thing anyone depends
on.

**Design decision, resolved 2026-08-28, closing the gap TASK-040's own
drafting named and deliberately left here (above, "A related, narrower
gap... left for TASK-028's own drafting"):** `BoundaryFaceConfig` had
`velocity`/`pressure` fields only -- both reserved for the momentum/
pressure system (`icds.md`'s Compatibility requirements: mutual
exclusivity, net-flux-sums-to-zero) -- and nothing for an arbitrary
transported scalar's own Dirichlet value. Verified this was live, not
hypothetical, before drafting the fix: `_NullValueBoundaryCondition`
(the Stage 3 reference implementation this task retires) returned
`face_config.velocity` regardless of which field asked, so a real
Dirichlet-typed scalar-transport boundary -- exactly what TASK-030's
Passive Scalar Transport demo configures -- would have silently received
a velocity-shaped number as its own prescribed boundary value, the
"plausible-looking wrong answer" failure mode `docs/practices.md` names
repeatedly, not a crash.

**Resolved: `BoundaryFaceConfig` gains a third, independent field,
`scalar_value: float = 0.0`** (`src/pyflow/configuration/schema.py`) --
a plain `float`, not `float | None` like `velocity`/`pressure`, since it
carries none of their mutual-exclusivity or net-flux relations; defaults
to `0.0` for the same reason `velocity` does, so every existing default
`NumericsConfig` stays valid without a config author naming it.
`DirichletBoundaryCondition` reads only this field, never
`velocity`/`pressure`. **Deliberately not generalised further**: a
`DirichletBoundaryCondition` and PISO's own `GreenGaussDivergence`
reading the *same* resolved condition object for two different fields
(a transported scalar, velocity's own normal component) at the same
wall, each needing a different number, stays out of scope -- Stage 4
never exercises Advection/Diffusion and Pressure-Velocity Coupling under
real Dirichlet boundaries in the same run (TASK-030's own demo is
explicit that it "is not required to exercise ... Pressure-Velocity
Coupling"), and the general version of this problem is already recorded
as deferred (P-016) in this Stage's own Design decisions, above ("one
global set of boundary conditions per simulation... does not yet express
'field A is 300K at this wall, field B is 0 at the same wall' for two
fields at once").

**A narrower version of the same gap is inherited by TASK-029, named
here rather than left for that task to rediscover** (the standing rule
this pattern itself produced, `docs/practices.md`): Neumann's own
prescribed-gradient counterpart to `scalar_value` does not exist yet --
`BoundaryFaceConfig` has no scalar-gradient field either. TASK-029's own
drafting must add one (or state explicitly why it does not need to).

### Artifacts Produced

- `src/pyflow/engine/numerics/boundary_condition.py`:
  `DirichletBoundaryCondition(value: float)` -- the Dirichlet shape's
  first real implementation, sharing the module with the interface the
  same way every other Stage 4 concrete scheme does.
- `src/pyflow/configuration/schema.py`:
  `BoundaryFaceConfig.scalar_value: float = 0.0`, validated with the
  same `_require_number` every other numeric field on this dataclass
  uses.
- `src/pyflow/engine/numerics/assembly.py`:
  `_dirichlet_boundary_condition(face_config) -> DirichletBoundaryCondition`,
  registered under `"dirichlet"` in place of the retired
  `_NullValueBoundaryCondition`.
- `tests/features/dirichlet_boundary.feature` -- see Acceptance Criteria.

### Implementation

`DirichletBoundaryCondition.evaluate` ignores `field` entirely and
returns its own stored value regardless -- the same "prescribed,
independent of interior state" shape
`test_boundary_condition_contract.py`'s own `_FixedValueCondition` test
double already established, now real. `kind` is `"value"`.
`register_boundary_condition_type("dirichlet", ...)`'s factory type is
unchanged (`Callable[[BoundaryFaceConfig], BoundaryCondition]`) --
unlike TASK-025/027, this task needed no interface widening, so no new
ADR.

### Acceptance Criteria

- **Criterion 2/7**: `_NullValueBoundaryCondition` is deleted, not
  merely unregistered, and `register_boundary_condition_type("dirichlet",
  ...)` now names `_dirichlet_boundary_condition` (which constructs the
  real `DirichletBoundaryCondition`).
- **Criterion 3**: `DirichletBoundaryCondition` joins
  `test_boundary_condition_contract.py`'s existing parametrised suite as
  a real third factory, with no edit to any existing test body.
- **Criterion 4, this task's own claim, per the Intent above**:
  `tests/features/dirichlet_boundary.feature`'s two scenarios each build
  a *real* interior scheme (`FirstOrderUpwindAdvection`,
  `CentralDifferenceDiffusion`) together with a real
  `DirichletBoundaryCondition` -- never a hand-written double standing in
  for the condition under test -- and check the scheme's own computed
  flux against the exact formula, not `evaluate()` alone.
- **Criterion 6**: `dirichlet_boundary.feature` exists and both scenarios
  are bound (`make check-scenarios`), via `tests/unit/
  test_dirichlet_boundary.py`.
- Config-surface correctness, not itself one of the numbered criteria but
  required by the Design decision above: `test_configuration.py` gained
  a real load test (`numerics.boundary_conditions.<face>.scalar_value`
  reads from YAML) and a rejection test (non-numeric value), and
  `test_assembly.py`'s own boundary-conditions-evaluate test was
  rewritten to use `scalar_value`, not `velocity`/`pressure`, for its
  Dirichlet fixtures -- the previous version would have silently kept
  passing against the old (wrong) semantics, since nothing had yet
  distinguished the two.

### Discharges

Stage 4 Completion Criteria 2, 3, 4, 6 and 7, Dirichlet's own share
(Criterion 1 -- the simulation-stepping mechanism -- was TASK-040's;
Criterion 5's rejection-path share is the inherited
`NotABoundaryFaceError`, already proven generically by the contract
suite once `DirichletBoundaryCondition` joined it, so this task adds no
exception class of its own).

---

## TASK-029

Neumann Boundary

**Status: Done, 2026-08-28, Stage 4's eighth task.**
`src/pyflow/engine/numerics/boundary_condition.py` implements
`NeumannBoundaryCondition`.

**Intent:** as TASK-028, for a prescribed **gradient** -- and the
zero-gradient case must not be the only one tested, since a
zero-gradient condition is also what a boundary that was silently
skipped entirely would produce.

**Inherited context, named at drafting per `docs/practices.md`'s "A
criterion whose strong reading depends on a later task must say so when
drafted" (TASK-028's own Design decision above named this explicitly,
rather than leaving it to be rediscovered here):** `BoundaryFaceConfig`
has no field yet for an arbitrary transported scalar's own prescribed
*gradient* -- only `scalar_value` (TASK-028, the Dirichlet counterpart)
exists. This task's own drafting must add one (mirroring `scalar_value`:
a plain `float`, not `float | None`, no mutual-exclusivity/net-flux
relation to `velocity`/`pressure`) or state explicitly why it does not
need to.

**Resolved: `BoundaryFaceConfig.scalar_gradient: float = 0.0`**,
`scalar_value`'s exact mirror -- same reasoning throughout (no mutual
exclusivity/net-flux relation, defaults to `0.0` so every existing
default `NumericsConfig` stays valid). `NeumannBoundaryCondition` reads
only this field.

**Milestone this task closes, worth recording explicitly rather than
letting it pass unremarked: zero `_Null*` reference implementations
remain in `assembly.py`.** All six `adr/ADR-003` components now have a
real concrete scheme under `src/` -- Stage 3 Completion Criterion 1's
carve-out (`docs/planning/roadmap.md`'s own Stage 3 section, and
`assembly.py`'s own module docstring) is fully retired, seven tasks
after `first_order_upwind` was the first name retired (TASK-023,
2026-08-27) and one day after Dirichlet was the sixth (TASK-028). See
`docs/repository-manifest.md`'s own updated count.

### Artifacts Produced

- `src/pyflow/engine/numerics/boundary_condition.py`:
  `NeumannBoundaryCondition(gradient: float)` -- the Neumann shape's
  first real implementation, sharing the module with the interface and
  `DirichletBoundaryCondition` the same way every other Stage 4 concrete
  scheme does.
- `src/pyflow/configuration/schema.py`:
  `BoundaryFaceConfig.scalar_gradient: float = 0.0`, validated with the
  same `_require_number` every other numeric field on this dataclass
  uses.
- `src/pyflow/engine/numerics/assembly.py`:
  `_neumann_boundary_condition(face_config) -> NeumannBoundaryCondition`,
  registered under `"neumann"` in place of the retired
  `_NullGradientBoundaryCondition` -- the last `_Null*` class and
  `_null_boundary_value` helper it alone used are both deleted, not
  merely unregistered.
- `tests/features/neumann_boundary.feature` -- see Acceptance Criteria.

### Implementation

`NeumannBoundaryCondition.evaluate` ignores `field` entirely and returns
its own stored gradient regardless -- the same "prescribed, independent
of interior state" shape `DirichletBoundaryCondition`
(`boundary_condition.py`) and
`test_boundary_condition_contract.py`'s own `_FixedGradientCondition`
test double already established. `kind` is `"gradient"`.
`register_boundary_condition_type("neumann", ...)`'s factory type is
unchanged -- no interface change, no new ADR, same as TASK-028.

### Acceptance Criteria

- **Criterion 2/7**: `_NullGradientBoundaryCondition` is deleted, not
  merely unregistered, and `register_boundary_condition_type("neumann",
  ...)` now names `_neumann_boundary_condition` (which constructs the
  real `NeumannBoundaryCondition`).
- **Criterion 3**: `NeumannBoundaryCondition` joins
  `test_boundary_condition_contract.py`'s existing parametrised suite as
  a real fourth factory, with no edit to any existing test body.
- **Criterion 4, this task's own claim, per the Intent above**:
  `tests/features/neumann_boundary.feature`'s two scenarios each build a
  *real* interior scheme (`CentralDifferenceDiffusion`,
  `FirstOrderUpwindAdvection`) together with a real
  `NeumannBoundaryCondition`, **both prescribing a nonzero gradient
  throughout** -- diffusion's own scenario proves the gradient's numeric
  value is read directly into the flux formula; advection's own proves
  the opposite (the value is never read, zero-order extrapolation only),
  and a zero-gradient fixture could not have told either from a boundary
  wired to nothing at all.
- **Criterion 6**: `neumann_boundary.feature` exists and both scenarios
  are bound (`make check-scenarios`), via `tests/unit/
  test_neumann_boundary.py`.
- Config-surface correctness: `test_configuration.py` gained a real load
  test (`numerics.boundary_conditions.<face>.scalar_gradient` reads from
  YAML) and a rejection test (non-numeric value), and
  `test_assembly.py`'s own boundary-conditions-evaluate test now uses a
  `velocity` deliberately distinct from `scalar_gradient` for its
  Neumann fixture (`docs/practices.md`'s "distinct factors" rule) --
  verified by mutation that the previous, coincidentally-equal fixture
  values would not have caught a regression reading the wrong field.

### Discharges

Stage 4 Completion Criteria 2, 3, 4, 6 and 7, Neumann's own share
(Criterion 1 was TASK-040's; Criterion 5's rejection-path share is the
inherited `NotABoundaryFaceError`, already proven generically by the
contract suite once `NeumannBoundaryCondition` joined it).

---

## TASK-030

Periodic Boundary

**Status: Done, 2026-08-28, Stage 4's ninth and last task.**
Periodic bypasses `BoundaryCondition` entirely (see the Design decision
below); the real mechanism is `src/pyflow/engine/mesh.py`'s
`wrapped_neighbour_cell`, read directly by
`src/pyflow/engine/numerics/advection.py`/`diffusion.py`.

**Intent:** the claim is that a field advected once around a periodic
domain returns to its starting distribution -- a round-trip invariant,
which is the only check that distinguishes a genuine wrapped-neighbour
lookup from a mirrored or clamped one at a single boundary.

**Design decision, resolved 2026-08-26 (before this task's own Acceptance
Criteria are drafted, per `docs/practices.md`'s "hold a design session
when intent is ambiguous"):** `BoundaryCondition.evaluate` returns a
`value` or a `gradient`; `icds.md` names periodic's own shape as "a
wrapped-neighbour reference," which is neither. Three readings were
possible.

*Rejected: extend `BoundaryCondition` with a third `kind`.* TASK-019's
own scope decision (Stage 3) was deliberate, not an oversight -- "the
Dirichlet/Neumann shapes without being them," with periodic left
unmodelled until a concrete implementation existed to check an interface
against (P-016). Reopening a closed Stage 3 interface now, to return
`float | int` depending on `kind`, would both re-litigate a decision
already made for a stated reason and weaken `evaluate`'s own return
type for the two shapes that already work. Nothing has changed since
Stage 3 closed to justify reopening it.

*Rejected: fabricate a `BoundaryCondition` instance for periodic anyway,
whose `evaluate` returns the wrapped cell's current value cast to
`float`.* This is what "a value" tempts a reader into building, and it
is wrong for the same reason TASK-040's own rejected reading was: it
would make `BoundaryCondition` respond to `kind` with a *value* that is
actually a live read of another cell's state, not a prescribed number --
`evaluate`'s own docstring ("the face value or gradient... needs")
already commits to it being one of exactly two fixed shapes, and
smuggling a third through the same method typed `-> float` produces
exactly the "plausible wrong answer from a technically-passing accessor"
shape `docs/practices.md` has named three times already (`Mesh`
id-validation, `extent` truncation, the pan-tracking bug).

**Decided: periodic bypasses `BoundaryCondition` entirely, exactly as
Stage 3 already left it** (`assembly.py`'s own docstring: "a periodic
face resolves no such instance"). A wrapped-neighbour lookup is mesh
geometry, not a prescribed value, so it lives where the other
structured-only geometric facts already live: **a new,
`StructuredCartesianMesh`-specific method** (a name in the shape of
`wrapped_neighbour_cell(face) -> int`, exact name left to this task's own
drafting), **not added to the abstract `Mesh` interface** -- the same
precedent `cell_id`/`cell_index` already set (structured-only concepts,
kept off the ABC because an unstructured mesh has no `(i, j)` to define
them against, and "the same relative position on the opposite edge" is
equally meaningless for an unstructured mesh). This is purely additive,
the same shape TASK-013's `face_vertices` addition to `Mesh` already
was ("added once TASK-013 actually needed it," `src/pyflow/engine/
CLAUDE.md`) -- no existing `Mesh`/`StructuredCartesianMesh` method's
behaviour changes, and Stage 1's own closed contract suite is untouched.

Consequences for this task's own build:
- A concrete Advection/Diffusion scheme, already constructed with its
  `Mapping[str, BoundaryCondition]` per TASK-040's own resolution, also
  receives which face names are periodic and their pairing (e.g. a
  `Mapping[str, str]` such as `{"east": "west", "west": "east"}`,
  containing only the faces actually configured periodic -- empty for
  every scenario before this task's own). Absence from this mapping is
  not read as "periodic" by omission; a face is periodic only if named
  in it, keeping the two conditions (prescribed value/gradient vs.
  wrapped-neighbour) explicit rather than inferred from a double
  negative.
- At a face named in that mapping, the scheme calls
  `wrapped_neighbour_cell` (via `field.mesh`, already available to it)
  instead of consulting a `BoundaryCondition`, and computes its normal
  interior-style formula against that cell's actual field value -- the
  same formula it already uses for a real interior neighbour, since a
  periodic face is arithmetically an interior connection once the
  correct second cell is known.
- **No change to `assemble_numerics`'s existing behaviour for
  `boundary_conditions`** beyond what TASK-040 already does: periodic
  faces still resolve no `BoundaryCondition` instance and still appear
  only in `AssembledNumerics.names`. The new periodic-pairing mapping is
  a *second*, separate piece of information the advection/diffusion
  factories receive, built from the same `NumericsConfig.
  boundary_conditions` the existing loop already reads.
- Stage 3's own whole-configuration validation (TASK-019, Criterion 7 --
  a periodic face's pair must also be periodic) already guarantees every
  periodic face this task encounters has a validly-paired partner before
  assembly runs, so this task adds no new whole-configuration rejection
  of its own on that point.
- **An accessor-level rejection criterion is still owed**
  (`docs/practices.md`, "rejection criteria stop at the constructor"):
  `wrapped_neighbour_cell` on a non-boundary face is meaningless the
  same way `BoundaryCondition.evaluate` on one is, and must raise a
  named exception, not return a plausible wrong cell.

Golden Demo

Passive scalar transport.

**Documentation obligation, not an Acceptance Criterion of this task's
own:** this is the task Stage 4 Completion Criterion 1 names as the one
that needs a real simulation-stepping mechanism running live -- "TASK-030's
golden demo cannot be assembled at all" without it, above. Once this
task wires `simulation.step()` into a real run (via `RenderWindow.run
(on_frame=...)`, per that hook's own docstring), replace
`docs/architecture/sequences.md` Section 2's "Planned: driving `step()`
from a live run" subsection with the real, built sequence, in the same
change -- that document names this task as the anchor for exactly this,
and should not still say "not built yet" once it is.

**Done, 2026-08-28, in the same change as the rest of this task.**
`docs/architecture/sequences.md` Section 2 now describes the real,
built sequence -- see that document's own updated section. The demo
itself is `examples/golden-demos/passive_scalar_transport.yaml`: a
prescribed uniform velocity carries a Gaussian scalar blob across a
mesh whose east/west edges are periodic (north/south are `neumann` with
a zero gradient -- an insulated wall, since the prescribed velocity is
purely horizontal and never crosses them). Verified visually, not only
by its own regression test: rendered offscreen at several frame counts,
the blob is seen translating downstream and, by the frame count
corresponding to one full domain width of travel, reappearing spread
across both the east and west edges -- the periodic wrap, genuinely
exercised by a live run, not only by `periodic_boundary.feature`'s own
isolated checks.

### Artifacts Produced

- `src/pyflow/engine/mesh.py`: `NotABoundaryFaceError`;
  `StructuredCartesianMesh.wrapped_neighbour_cell(face) -> int` -- the
  periodic wrap's own geometry (Design decision above).
- `src/pyflow/engine/numerics/advection.py`,
  `src/pyflow/engine/numerics/diffusion.py`: both concrete schemes gain a
  `periodic_pairs: Mapping[str, str]` constructor parameter and consult
  it before falling through their existing interior-neighbour formula --
  no interface change, no new ADR (mirrors `diffusion_coefficient`'s own
  TASK-024 precedent).
- `src/pyflow/engine/numerics/assembly.py`: `_PAIRED_BOUNDARY`;
  `periodic_pairs` built alongside `boundary_conditions` in
  `assemble_numerics`'s existing per-face loop; `register_advection_
  scheme`/`register_diffusion_scheme`'s factory types widen accordingly;
  `_resolve_with_three_arguments` (diffusion's own factory now takes
  three constructor arguments); `_resolve_with_argument` (the one-argument
  helper) deleted as genuinely dead code, its only caller (advection)
  having moved to `_resolve_with_two_arguments`.
- `src/pyflow/configuration/schema.py`: `SimulationConfig`
  (`scalar_pattern`, `velocity_pattern`, `velocity`) -- the Passive
  Scalar Transport demo's own configuration surface, distinct from
  `FieldDisplayConfig` (static single-frame display) since this seeds a
  real, repeatedly-stepped run.
- `src/pyflow/bootstrap.py`: `_simulation_scalar_initializer`/
  `_simulation_velocity_initializer`; `_add_passive_scalar_transport`,
  wiring a real `simulation.step()` call into `RenderWindow.run(
  on_frame=...)` -- the first config in this project's history to do so.
- `src/pyflow/rendering/window.py`: `RenderWindow.simulation_fields` --
  the live simulation's own field state, read back by the golden demo's
  regression test the same way `assembled_numerics` already lets a
  caller read back what got assembled.
- `tests/features/periodic_boundary.feature`,
  `tests/features/passive_scalar_transport.feature` -- see Acceptance
  Criteria.

### Implementation

**The periodic distance is `2 * mesh.face_centroid_distance(face)`, not
a new geometry accessor** -- verified numerically before relying on it:
on a mesh with distinct `dx`/`dy` and a non-trivial origin, doubling a
boundary face's own owner-to-face distance reproduces the true uniform
grid spacing exactly, matching an ordinary interior face's distance on
the same mesh to float precision. The periodic "neighbour" is one full
cell-width away, not the real wrapped cell's actual (far-side-of-the-
domain) centroid, so the plain interior formula `hypot(neighbour.xy -
owner.xy)` would be wildly wrong if applied naively across the wrap.

`FirstOrderUpwindAdvection.flux`/`CentralDifferenceDiffusion.flux`: at a
boundary face, if its named edge is a key in `periodic_pairs`,
`mesh.wrapped_neighbour_cell(face)` stands in for `neighbour` (and, for
diffusion, the doubled distance stands in for the boundary formula's
own owner-to-face distance) before either scheme's existing
`neighbour is not None` code path runs -- literally the same formula
already used for a real interior neighbour. `boundary_conditions` is
never consulted for a periodic face; `periodic_pairs` and
`boundary_conditions` are deliberately two separate mappings, keeping
"prescribed value/gradient" and "wrapped-neighbour" explicit rather than
inferred from one mapping's absence.

`bootstrap.py`'s live-stepping branch rebuilds the rendered `gfx.Mesh`
from scratch each frame (`window.scene.remove` the old one,
`build_scalar_field_mesh` a new one) rather than mutating the geometry's
own colour buffer in place -- `build_scalar_field_mesh`/
`scalar_field_colors` are already proven correct (TASK-017); an in-place
buffer mutation would be new, unverified pygfx-API surface for a small
win on a small demo mesh. `gfx.Scene.remove` was verified to behave as
expected (add then remove leaves `len(scene.children) == 0`) before
being relied on, the same "check implementation details directly"
discipline every prior rendering addition in this codebase has used.

### Acceptance Criteria

- **Criterion 4, this task's own claim, per the Intent above:** the
  round-trip invariant is checked as *convergence under mesh refinement*,
  not exact equality at one resolution -- found necessary by running the
  real numbers first: first-order upwind's own O(dx) numerical diffusion
  smooths any field over the distance it travels regardless of whether
  the wrap itself is correct, and refining the timestep alone does not
  shrink that error (verified: near-identical results at `num_steps`
  10-160 on a fixed mesh, since the RK4-integrated semi-discrete system
  converges to a fixed, spatially-truncation-dominated limit as
  `dt -> 0`). A real wrap's own round-trip error drops by roughly 62%
  over a 4x mesh refinement; a mirrored/clamped one (built and run as a
  throwaway mutation specifically to check this) drops by only roughly
  16% and stays several times larger throughout -- `periodic_boundary.
  feature`'s own scenario asserts the fine-resolution error stays under
  two thirds of the coarse one, confirmed to actually fail under that
  same mutation before being trusted.
- Advection/diffusion's own wiring is checked directly (not only via the
  round-trip): a real periodic pairing reads the wrapped neighbour's own
  value/gradient at the correct distance, verified by mutation (reverting
  the wrap to the owner's own cell, or the distance to the un-doubled
  one, both fail the corresponding scenario).
- **An accessor-level rejection criterion, per the Design decision's own
  "still owed" note:** `wrapped_neighbour_cell` raises `NotABoundaryFaceError`
  on an interior face, exercised directly for both a vertical and a
  horizontal interior face (`test_structured_cartesian_mesh.py`) -- found
  necessary while confirming coverage, since a single `next(...)`-selected
  interior face always picked the vertical branch first, leaving the
  horizontal `raise` line genuinely untested by one test alone.
- Config-surface correctness: `test_configuration.py` gained
  `SimulationConfig` load/reject tests, the same shape every prior
  config-section addition in this run used.
- **Stage 4 Completion Criterion 1, the golden demo:** `passive_scalar_
  transport.feature`'s own quantitative scenario checks the transported
  field's mass-weighted centroid moves downstream by approximately
  `velocity * dt * steps`, measured over two independent real runs
  (`bootstrap()`, offscreen) rather than only by pixel-diffing two
  frames -- "physical fields evolve" (`docs/implementation/mvp.md`'s
  Definition of Done) checked directly. The tolerance (`rel=0.15`) was
  measured from a real run (~4% actual agreement), not guessed, and
  confirmed to fail under a mutation that froze the simulation state
  every frame.
- **Stage 3 Completion Criterion 1's carve-out**, already closed at
  TASK-029, stays closed -- this task adds no new `_Null*` class, and
  deletes one more genuinely dead helper (`_resolve_with_argument`).

### Discharges

Stage 4 Completion Criteria 1 (the golden demo, jointly with TASK-040's
own orchestration mechanism), 3, 4 and 5's rejection-path share
(`NotABoundaryFaceError`), Periodic Boundary's own share; Stage 4
Completion Criterion 6, this task's own two feature files
(`periodic_boundary.feature`, `passive_scalar_transport.feature`), both
bound (`make check-scenarios`); Stage 4 Completion Criterion 7, restated
closed (already true since TASK-029, unaffected by this task).

---

# Stage 5 — First Fluid Solver

Goal

Solve incompressible flow.

### Completion Criteria

Written 2026-08-28, before TASK-031 starts, per `docs/practices.md`'s "A
stage gets completion criteria before its first task" -- now that Stage
4 has actually delivered the concrete schemes these tasks must couple
(closed 2026-08-28), rather than committing to their shape while the
components they compose were still `_Null*` registrations.

Criteria are about the stage's goal -- *solve incompressible flow* --
not the union of TASK-031..034's own Acceptance Criteria. Every
qualifying clause is its own bullet (`docs/practices.md`, "The intent
lives in the qualifier") and every criterion names the task(s) that
discharge it (the discharge map below), following the two rules Stage 3
and Stage 4 both carried.

**Neither of Stage 3's two exemptions extends here**, same as Stage 4:
the physical-correctness extension applies in full, and executable
Gherkin criteria apply in full
(`adr/ADR-007-executable-acceptance-criteria.md`) -- every task below is
simulation work. TASK-034's own criteria are the sharpest test of that
form: "the right instability emerges under the right configuration, and
does not emerge under a configuration where it should not" is a pair of
scenarios, and reads as one.

**This stage defines the MVP, so `docs/implementation/mvp.md`'s own
Definition of Done is reconciled against these criteria explicitly, in
Criterion 11 below** -- the condition this section carried as a
placeholder from 2026-08-22 until it was drafted. Two conflicts came out
of doing that rather than assuming the two documents agreed, both
decided by the maintainer on 2026-08-28 and both recorded where they
were found: the fate of `mvp.md`'s "heat diffusion" validation case
(Criterion 8), and whether Ghia et al.'s illustrative 2% is this stage's
actual bar (Criterion 5).

1. **Velocity is transported by the same mechanism every other field
   is.** The stage's field-centric claim is only worth anything if
   nothing here special-cases velocity -- Stage 6 adds four more
   transported fields (TASK-035..038) on exactly that claim, and it is
   testable only if velocity went through the path they will.
   - The orchestrator advances velocity through the same
     `src/pyflow/engine/simulation.py` `step` path a scalar takes: the
     same `AdvectionScheme`/`DiffusionScheme`, the same
     `accumulate_flux_to_cells`, the same `TimeIntegrator`. **Checked
     structurally as well as behaviourally, by the mechanism Stage 4
     already established for exactly this shape of claim** --
     `tests/unit/test_simulation.py` asserts `"is_boundary_face" not in
     inspect.getsource(simulation)` to hold TASK-040 to Stage 4
     Criterion 1's uniformity clause. The same assertion, for the names
     this criterion forbids, is what makes "nothing special-cases
     velocity" a test rather than a hope: no `"velocity"` string
     literal, and no `isinstance(..., VectorField)`, in the
     orchestrator's own module.
   - **A scalar transported alongside velocity in the same run is
     advanced by the same call, and its result does not depend on
     velocity being solved rather than prescribed.** The executable form
     of "no engine change", which a scenario can actually check and a
     diff review cannot: run a scalar with a *solved* velocity field,
     capture that velocity, then run the same scalar with that same
     velocity *prescribed* as Stage 4's demo does -- the scalar's field
     must agree to floating-point tolerance. A transport path that
     quietly treats a solved velocity differently fails this; one that
     does not, cannot. Stated as a Stage 5 criterion rather than left
     for Stage 6 to discover: the "no new machinery" claim Stage 6's own
     criteria already make is far cheaper to check here, with two
     fields, than there, with five.
   - **Momentum diffusion is viscosity, and is not the same number as a
     scalar's diffusivity.** `NumericsConfig.diffusion_coefficient`
     (`src/pyflow/configuration/schema.py`) is currently one global
     constant serving the one transported scalar Stage 4 had. A
     configuration that sets a fluid's viscosity must not silently set
     an unrelated scalar's diffusivity, and a Reynolds number cannot be
     configured at all until the two are distinguishable. Design
     question four settles where they live (a new `fluid:` section, with
     `diffusion_coefficient` migrating into it); this criterion is the
     behavioural half, and holds whatever the section is called.
   - **Design question one is resolved (per-component `ScalarField`s),
     and the criterion is what stops that answer being implemented as a
     special case.** Velocity is transported as its components, so the
     transport path sees scalars and nothing about it may know that two
     particular scalars are somebody's velocity: no name-keyed branch,
     and the assembly back into a `VectorField` happens at the
     consumers that need one, not inside the transport path. An
     implementation that hardcodes the pair `("u", "v")` has moved the
     special case rather than removed it.
2. **Pressure is solved from the incompressibility constraint, not
   transported.** A criterion that treats pressure as another advected
   scalar has misunderstood the task
   (`docs/handbook/numerical-methods/pressure-velocity-coupling.md`:
   pressure "is best understood as a constraint-enforcing field, not a
   transported one").
   - Pressure never appears among the fields `step` advances, and
     handing `step` a `fields` mapping that contains the pressure field
     raises a named error rather than quietly advecting it. **Stated at
     the API level deliberately, not the configuration level** -- there
     is no configuration surface today that names which fields are
     transported (`SimulationConfig` seeds one scalar pattern and one
     velocity pattern, nothing more), so "a configuration that tries to
     transport pressure" is not currently expressible and a criterion
     phrased that way could not be discharged. `step`'s own signature is
     where the guard is real, and it is the same place
     `MismatchedMeshError` already guards.
   - Pressure is determined by the velocity field it is solved against,
     checked as a *pair* of scenarios, not either alone: a provisional
     velocity that is already divergence-free yields a pressure field
     that is constant to solver tolerance, and one with a known nonzero
     divergence yields one that is not. A solver stuck at zero passes
     the first scenario and fails the second, which is the point of
     requiring both.
   - **The null space is removed explicitly, and which remedy was
     chosen is visible and tested.** Every boundary of the MVP's own
     lid-driven cavity prescribes velocity, so the discrete pressure
     system is singular and positive *semi*-definite with a
     one-dimensional null space of constant vectors
     (`pressure-velocity-coupling.md`, "When the Pressure Equation Has
     No Unique Solution"). Either remedy that document names -- a
     pinned reference cell, or a mean-subtracting projection -- is
     acceptable; leaving it implicit is not, and the criterion is
     checked by adding a constant to the pressure field and confirming
     the corrected velocity is unchanged to floating-point tolerance.
   - **The compatibility condition is not re-implemented here.** Zero
     net boundary flux is already rejected at configuration-load time
     by Stage 3 TASK-019's `_validate_boundary_conditions_jointly`.
     This stage's own share is showing the solve *depends* on it: a
     configuration violating it fails to load, rather than failing deep
     inside the linear solver with a confusing message.
3. **Divergence decreases monotonically with each corrector iteration,
   and reaches the configured tolerance -- measured across iterations,
   not asserted at the end.** A loop that reaches tolerance by luck on
   iteration one and diverges thereafter passes an end-state check; the
   recorded sequence of per-iteration maximum divergence magnitudes is
   non-increasing at every element, and its last element is at or below
   the configured tolerance.
   - **Non-increasing is not sufficient on its own, and the scenario
     must close that hole explicitly.** A corrector that does nothing at
     all produces a *constant* sequence, which is non-increasing, and if
     the fixture's starting field happens to be near-divergence-free the
     final element passes too -- the exact shape of "passes for reasons
     unrelated to what it claims" that Stage 4's own exit audit found in
     the Advection conservation scenario, and found by mutation rather
     than by reading. So: the fixture's initial maximum divergence is
     stated and is orders of magnitude above the configured tolerance,
     the decrease is *strict* across at least the first two passes, and
     the whole scenario is mutation-checked by making the corrector a
     no-op and confirming it fails.
   - **The tolerance must be genuinely configured, not a constant in the
     test.** `NumericsConfig` has no divergence tolerance today --
     `linear_solver_tolerance` is the inner CG solve's, a different
     number for a different convergence question -- so this criterion
     depends on Criterion 12's config surface existing, and says so
     rather than letting an implementer read "configured" as "chosen in
     the fixture".
   - **This is where Stage 4 Completion Criterion 4's Pressure-Velocity
     Coupling bullet's stronger claim is discharged**, the deferral
     TASK-027 recorded explicitly rather than silently narrowing its own
     criterion. When this task closes, that bullet, TASK-027's own entry
     and `docs/practices.md`'s "A criterion whose strong reading depends
     on a later task must say so when drafted" are all re-read against
     what actually landed -- `docs/practices.md`'s "A deferral gated on
     a task must be revisited when that task closes", applied
     deliberately rather than remembered.
   - **`piso` must become the algorithm it is named after, or the name
     must be corrected.** `PISO` is registered under that name today but
     is honestly documented as a single `dt`-scaled correction pass, not
     Issa's multi-pass algorithm
     (`src/pyflow/engine/numerics/pressure_coupling.py`'s own class
     docstring). `mvp.md` names PISO as an MVP component and
     `pressure-velocity-coupling.md` describes it as "two or more
     pressure-correction passes within a single timestep". Either this
     stage makes the registered scheme genuinely multi-pass, or
     `mvp.md`, `docs/architecture/icds.md` and `PressureCouplingName`
     are corrected in the same change. The MVP must not ship claiming an
     algorithm by name only.
   - Non-convergence is reported, never returned as a plausible field --
     already true of `PressureSolveDidNotConvergeError` for a single
     solve, extended here to the loop's own iteration limit: exhausting
     the corrector passes without reaching tolerance is an error, not a
     quietly-returned best effort.
4. **One timestep solves momentum and continuity together, and the
   sequence is checked, not only its endpoint.** Predictor, corrector
   loop, corrected state -- the assembled per-step sequence
   `pressure-velocity-coupling.md` describes, with each part observable.
   - **Two null tests the rest cannot substitute for**, stated as a
     pair because the obvious single version of this does not hold: a
     divergence-free field is not automatically a *steady* solution (a
     vortex is divergence-free and advects itself), and a uniform flow
     cannot exist inside a closed domain at all, since no-penetration
     walls forbid it. So:
     - **Uniform flow on a fully periodic domain, zero viscosity, no
       forcing:** stays divergence-free and translates at exactly the
       prescribed speed, unchanged in shape, over many steps. Genuinely
       steady, so any spurious pressure correction shows up immediately.
     - **Fluid at rest in a closed domain, every wall no-slip:** stays
       at rest, to floating-point tolerance, over many steps. Trivial to
       state and the sharpest guard in this list -- an implementation
       that manufactures velocity out of its own correction term fails
       it and passes almost everything else here.
   - Deterministic: the same configuration run twice produces identical
     state, checked directly. Already required of every golden demo
     (`docs/implementation/golden-demos.md`'s Definition of Done),
     restated here because Criterion 8's demo and any future
     checkpoint/replay both rest on it.
     - **Identical within a process; agreeing to a stated tolerance
       across platforms.** Criterion 9 requires green CI on both Ubuntu
       and Windows, and this stage is the first to run an iterative
       solve whose result depends on accumulated floating-point
       arithmetic -- BLAS ordering and library versions differ between
       the two runners, so a demo regression test asserting exact values
       is a cross-platform flake waiting to happen rather than a
       determinism check. Stated in advance because the failure mode is
       a red build on one platform only, which reads like a real defect
       and costs a session to diagnose.
   - **Checkpoint/pause/rewind is explicitly not a criterion of this
     stage**, stated so its absence is not later mistaken for a gap: it
     is recorded as future scope under TASK-034 below, and
     `docs/architecture/sequences.md` Section 3 carries it as a
     "Planned: checkpointing" placeholder anchored to that task. If it
     is built here, that placeholder is replaced with the real sequence
     in the same change (that document's own obligation). If it is not,
     the placeholder stays accurate and nothing is owed.
5. **Physical correctness against a known answer, per case** -- per
   `docs/practices.md`'s testable-physics extension, and stated per case
   rather than left generic, the same shape Stage 4's own Criterion 4
   took.
   - **Couette flow, first, and to a tight tolerance rather than a
     generous one.** Plane shear flow between two plates, one
     stationary and one moving, with no imposed pressure gradient: the
     steady velocity profile is exactly linear, and is checked against
     that analytic profile cell by cell. The simplest incompressible
     Navier-Stokes case there is
     (`docs/planning/implementation-plan.md` Level 2), and the one that
     isolates viscous diffusion plus the wall treatment from any
     pressure-gradient effect -- which is exactly why it comes before
     the cavity rather than after it.
     - **The tolerance is tight because the nonlinear term vanishes
       identically here, not because the scheme is accurate.** With
       `v = 0` everywhere and `u` a function of `y` alone, the
       convective term `u du/dx + v du/dy` is exactly zero, so
       first-order upwind's numerical diffusion -- the error term that
       makes the cavity's own tolerance a negotiation below -- has no
       gradient to act on and contributes nothing. Agreement should be
       at solver tolerance, and a scenario that passes only at a loose
       tolerance is evidence of a defect rather than of discretisation
       error. Recorded here so that nobody later reads a loosened
       Couette tolerance as the same kind of honest concession the
       cavity's is.
   - **Lid-driven cavity against Ghia, Ghia & Shin (1982)**, whose
     tabulated centreline velocity profiles at Reynolds number 100 are
     the published reference three other documents already point at
     (`adr/ADR-007-executable-acceptance-criteria.md`'s worked example,
     `docs/glossary.md`'s "Validation" definition,
     `docs/planning/implementation-plan.md` Level 2, which asked
     whoever drafted these criteria to reach for it rather than invent a
     fresh reference).
     - **The criterion is convergence, not a fixed percentage**
       (decided 2026-08-28, maintainer's call, recorded because the
       obvious reading was the other one): the error against Ghia's
       tabulated profiles must *decrease monotonically across at least
       three mesh resolutions*, and the qualitative structure must be
       right at the finest -- primary vortex centre within a stated
       distance of Ghia's, and both downstream secondary corner vortices
       present.
     - **The reference values are committed data with their citation
       attached, not literals typed into an assertion.** Ghia et al.'s
       tabulated `u` along the vertical centreline and `v` along the
       horizontal one, for Re = 100, plus the paper's own primary-vortex
       centre coordinates, belong in a small committed fixture naming
       the paper, table and column each number came from. **The values
       are read off the paper itself, not from memory or a secondary
       source** -- the widely-quoted primary-vortex centre for Re = 100
       is approximately `(0.617, 0.734)` in unit-cavity coordinates, and
       that approximation is written here as a sanity check on the
       fixture, not as the number to assert against. This repository has
       no test-data directory yet, so wherever it lands is a new
       convention: `docs/repository-manifest.md` and the nearest
       `CLAUDE.md` are updated in the same change, per the Blast Radius
       rule.
     - **"Steady" is a measured residual, not a step count.** The
       comparison is against Ghia's *steady-state* solution, so the run
       has to reach steady state to be comparable at all -- and a fixed
       number of timesteps is not evidence that it did, at any
       resolution, let alone at three. The scenario states the
       steadiness measure it uses (e.g. the maximum per-cell velocity
       change per step falling below a stated threshold) and fails on
       *not reaching it* rather than silently comparing an unconverged
       field. This matters more under mesh refinement than anywhere
       else: a finer mesh needs both more steps and a smaller timestep
       (design question four), so a step count that sufficed at the
       coarsest resolution is guaranteed not to suffice at the finest.
     - **The runtime this implies is part of the criterion, not a
       surprise to discover in CI.** Three resolutions run to steady
       state is the most expensive check this project will have
       attempted; the whole suite runs in under two minutes today. If
       the honest version does not fit that budget, the resolution to
       state is where the check runs and how it stays a real gate --
       not a quietly reduced number of resolutions.
     - **ADR-007's illustrative "within 2%" does not bind this stage.**
       That number appears in a worked example showing what an
       executable physics criterion *looks like*, and in the glossary's
       definition of validation; neither was ever a commitment, and
       `implementation-plan.md` Level 2 says so directly. The MVP's
       advection scheme is first-order upwind, whose numerical diffusion
       at MVP mesh resolutions is the dominant error term
       (`docs/handbook/numerical-methods/advection.md`;
       `docs/implementation/upgrade-paths.md` is where a better scheme
       lands). A criterion that could only be met by quietly loosening
       its own number later is not a criterion, which is why the
       convergence claim above is the one that gates and the absolute
       tolerance is stated and defended in the feature file against the
       mesh actually used.
   - **The emergent phenomenon, and its negative control.** The
     qualifier this stage has carried since 2026-08-20 (this document's
     own "Stages and Capability Levels" note; `docs/planning/backlog.md`,
     "physical correctness validation"): the right phenomenon under the
     right configuration, which means a configuration under which it
     should *not* emerge is tested too. An instability that appears
     regardless of parameters is not the instability. Named candidates
     rather than left generic -- Kelvin-Helmholtz roll-up present above
     a shear layer's instability threshold and absent below it, or
     Taylor-Green's closed-form decay rate matched at one viscosity and
     demonstrably not at another; both are Level 2 cases already
     (`docs/planning/implementation-plan.md`), and either pair satisfies
     this bullet.
     - **Which of the two to use is decided by measurement, and the
       risk that neither survives is stated now rather than met as a
       surprise.** Both phenomena are sensitive to numerical diffusion,
       and the MVP's advection scheme is the most diffusive one there
       is: upwind can suppress Kelvin-Helmholtz roll-up entirely at
       coarse resolution, and can dominate Taylor-Green's physical decay
       rate so that the measured rate reflects the scheme rather than
       the viscosity. Measure before committing a scenario to either.
       **If neither survives at a resolution this stage can afford,
       that is a real finding about the MVP's numerics -- report it and
       rescope with the maintainer** (Stage 8 is where a less diffusive
       scheme lands, `docs/implementation/upgrade-paths.md`). It is not
       licence to quietly drop the negative control, which is the half
       of this bullet that does the work.
   - **Conservation, a claim none of the three above makes.** On a
     closed domain with no forcing, an inviscid flow's total kinetic
     energy must not *grow* -- **checked step by step, not as a net
     change over the run.** The distinction is the whole value of the
     bullet: first-order upwind is strongly dissipative, so the net
     trend is downward whatever the pressure correction does, and a net
     check therefore passes trivially while a correction that injects
     energy on individual steps goes unseen. No single step increases
     total kinetic energy. A pressure correction that injects energy can
     still match a steady-state profile comparison and still be wrong;
     this is the bullet that catches it, and it is the velocity
     counterpart of the conservation checks Stage 4 already required of
     Advection and Diffusion separately (`docs/planning/backlog.md`,
     conservation checks -- whose Pressure-Velocity Coupling bullet
     names this stage's own TASK-033 as where mass conservation proper
     gets its check).
6. **Every real implementation's own error and rejection conditions are
   exercised against actual bad input**, not inherited untested from an
   interface's shared helper -- Stage 4's own Criterion 5, which applies
   here unchanged and is restated rather than assumed to carry over. The
   specific new surfaces this stage creates: a velocity field whose
   component count disagrees with the mesh's dimensionality, a
   configuration that names a boundary treatment velocity has no meaning
   for, a corrector loop that exhausts its iteration limit, and -- from
   design question one's per-component answer -- a component set whose
   size disagrees with the mesh's dimensionality, or components defined
   over different meshes. `MismatchedMeshError` already has the shape
   for the last of those but has never been asked about a reassembled
   vector.
7. **Every task's acceptance criteria are a Gherkin `.feature` file
   under `tests/features/`, and `make check-scenarios` gates that every
   scenario it contains actually runs.** The mechanism
   `adr/ADR-007-executable-acceptance-criteria.md` commits this stage to;
   restated as a checkable exit condition, not left only as the drafting
   instruction it also is.
   - Steps are built from the shared building blocks
     (`tests/unit/_numerics.py` for unit-level scenarios,
     `tests/golden/_demo.py` for demo-level ones), not re-derived -- and
     the venue is named correctly here rather than assumed, since Stage
     4's own version of this bullet named an unreachable one for three
     days (`tests/golden/conftest.py`, corrected at that stage's exit
     audit: a `conftest.py` applies only to its own directory subtree).
   - **Every scenario's fixture avoids a degenerate case that could let
     a wrong implementation agree with a right one by coincidence** --
     non-square mesh, non-trivial origin, spacing that isn't 1, values
     that aren't 0 or 1 everywhere, and, specific to this stage, a
     viscosity that isn't 1, a lid velocity that isn't 1, and a timestep
     that isn't the mesh spacing. Stated once here rather than repeated
     under each task.
8. **Stage 5 has working, visible demonstrations: Lid-Driven Cavity and
   Heat Diffusion.**
   - Each demo *is* a config file under `examples/golden-demos/`, run
     via `pyflow run --config <file>`, per the public-API rule every
     golden demo already follows
     (`docs/implementation/golden-demos.md`), with at least one
     regression test per demo invoking it through the real CLI as a
     subprocess.
   - **Lid-Driven Cavity is the MVP's own golden demo** -- the "Initial
     Golden Demo" `docs/implementation/golden-demos.md` and `mvp.md`'s
     "golden demo exists" both refer to. It renders a *solved* velocity
     field live, through the existing field rendering (TASK-017), which
     is what makes `mvp.md`'s "visualisation shows the result" true for
     the first time: every velocity PyFlow has rendered until now was
     prescribed or seeded, never computed. **If rendering a solved field
     turns out to need work the existing renderer cannot do, that is a
     finding to report and schedule, not a silent addition to this
     stage** -- no rendering task is planned here, and the criterion is
     stated this way so that its absence is a decision rather than an
     oversight.
   - **Heat Diffusion is Stage 5's, resolved 2026-08-28 (maintainer's
     call) rather than assumed either way.** `mvp.md`'s Validation
     section requires the MVP to reproduce three cases -- passive scalar
     transport (closed by Stage 4's TASK-030), heat diffusion, and
     lid-driven cavity -- while `docs/planning/implementation-plan.md`
     and `planning/data/demos.yaml` both placed Heat Diffusion at
     Capability Level 3 alone, which is Stage 6. That was a real
     divergence between the document defining this stage's own exit bar
     and the two describing the long-range plan, and it was found by
     doing the reconciliation Criterion 11 requires rather than assuming
     the two agreed. **Decided: Stage 5 owes it, as a scalar.** Heat diffusion
     *is* the diffusion equation on a transported scalar; only the
     field's name differs, and PyFlow can run it with no Temperature
     field at all (`docs/handbook/numerical-methods/diffusion.md`).
     Stage 6's own TASK-035 then adds the named Temperature field with
     buoyancy coupling, which is a genuinely different claim, not this
     one repeated. `implementation-plan.md` and
     `planning/data/demos.yaml` are amended in the same change as this
     criterion, not left to be rediscovered.
     - **It validates something quantitative, because `mvp.md` lists it
       under Validation rather than under Components.** A demo that
       shows heat spreading and nothing more would satisfy the letter of
       this bullet and none of its purpose --
       `docs/implementation/golden-demos.md`'s Definition of Done
       already asks for "meaningful behaviour, not just 'it ran without
       crashing'", and this case has an exact answer available: a single
       sinusoidal mode on a periodic domain decays exponentially at a
       rate set by the diffusion coefficient and the mode's wavenumber,
       so the measured decay rate is checkable against the analytic one
       rather than against a picture. Distinct from Stage 4's own
       diffusion criteria, which measured spatial convergence order and
       conservation -- neither of which is a decay *rate*.
   - **Poiseuille flow, Taylor-Green vortex and Kelvin-Helmholtz
     instability are not required as demos here**, stated so their
     absence is not read as a gap: all three are Level 2 catalog entries
     (`docs/planning/implementation-plan.md`), and
     `docs/implementation/golden-demos.md`'s own rule is not to write a
     demo entry for a capability that does not exist yet. Taylor-Green
     and Kelvin-Helmholtz appear in Criterion 5 as *scenarios*, which is
     a weaker and sufficient obligation; Poiseuille appears in neither
     and stays scheduled where it is.
9. **`make ci` passes on both CI platforms, on a real runner** -- not
   only locally, matching every prior stage's standard of evidence, read
   from the actual run rather than inferred from a merged PR.
10. **Documentation describes what now exists**, and the sweep is a grep
    against what this stage *invalidated*, not a review of what it
    touched (`docs/practices.md`, "A stage's documentation sweep is a
    grep, not a diff review" -- the rule Stage 4's own exit audit
    produced after finding seven stale claims in files no Stage 4 task
    had opened).
    - **`docs/architecture/icds.md`'s Pressure-Velocity Coupling entry
      is the one this stage is most likely to falsify, and it is
      specific rather than general.** That entry currently records, in
      detail, that `piso` "is not, and does not claim to be, the full
      multi-pass Issa algorithm", and names TASK-033 as where the
      stronger claim belongs -- written by TASK-027 on 2026-08-27 and
      accurate today. Criterion 3 is what makes it stop being accurate.
      Re-read it, its `Choices:` line and its `Expected behaviour`
      prose against what actually landed.
    - `docs/architecture/engine.md`'s `Implementation:` lines for the
      Variables, Flux and Pressure-Velocity Coupling layers name the
      concrete modules, and that document's own maintenance rule
      (don't rewrite the tense, per its closing section) is followed
      rather than worked around.
    - `docs/implementation/golden-demos.md` gains a real entry for each
      demo Criterion 8 lands, written when the demo exists rather than
      ahead of it.
    - Every touched `CLAUDE.md` and both inventories
      (`docs/repository-manifest.md`, `docs/repository-inventory.md`)
      are checked against the tree directly.
    - **The capability map is part of this criterion, not an
      afterthought** -- `mvp.md`'s Definition of Done names "capability
      map is updated" as its own bullet, and it is the one bullet no
      previous stage has ever had cause to touch:
      `docs/planning/capability-map.md`,
      `planning/data/capabilities.yaml` and
      `docs/planning/implementation-plan.md`'s Level 2 all describe a
      capability this stage is what realises.
11. **`docs/implementation/mvp.md`'s own Definition of Done is
    discharged item by item, or its divergence is recorded at source.**
    This stage defines the MVP, so its exit *is* the MVP's exit; the
    reconciliation is written here, when the criteria are drafted,
    rather than reconstructed at the exit audit.

    | `mvp.md` Definition of Done | Where it is discharged |
    |------|------|
    | Simulation runs end-to-end | Criteria 4 and 8 |
    | Physical fields evolve | Criteria 1 and 2 (velocity and pressure; a scalar already evolved in Stage 4) |
    | Boundary conditions operate | Criterion 5's Couette and cavity bullets -- a moving wall and a no-slip wall, which is velocity's own boundary treatment, distinct from the scalar boundaries Stage 4 closed |
    | Pressure/velocity coupling works | Criterion 3, in the strong sense TASK-027 explicitly deferred |
    | Numerical solution is measurable | Criterion 5 |
    | Visualisation shows the result | Criterion 8's Lid-Driven Cavity bullet |
    | Golden demo exists | Criterion 8 |
    | Documentation describes the implemented functionality | Criterion 10 |
    | Tests verify the core behaviour | Criterion 7 |
    | Capability map is updated | Criterion 10's own capability-map bullet |

    **`mvp.md`'s Components and Validation sections are reconciled too,
    not only its Definition of Done** -- four findings, recorded here
    rather than left for the exit audit:
    - *Already true, nothing owed:* 2D, structured Cartesian, uniform
      spacing, single incompressible fluid, FVM, collocated arrangement,
      first-order upwind, central-difference diffusion, RK4, Conjugate
      Gradient, and Dirichlet/Neumann/Periodic boundaries. All landed
      across Stages 1-4; this stage adds none of them. **Rendering is
      the one entry here that is true but untested in the way that
      matters** -- `mvp.md` requires "real-time visualisation of scalar
      and vector fields", which exists (TASK-017), but no vector field
      PyFlow has rendered was ever *solved*; Criterion 8 is where that
      stops being an assumption.
    - *Owed by Criterion 3:* PISO. Named as an MVP component, currently
      a single-pass approximation registered under that name.
    - *Owed by Criterion 8:* the Validation section's three cases. One is
      closed (passive scalar transport, TASK-030); the other two are
      this stage's, per the Heat Diffusion decision recorded above.
    - *Owed by Criterion 12, and nearly missed:* `mvp.md`'s
      **Configuration** component -- "simulation components are selected
      through configuration rather than by modifying engine code". The
      first draft of this reconciliation filed that under "already true,
      nothing owed", because `adr/ADR-003`'s six components have been
      configuration-selected since Stage 3. That reading is too
      generous by exactly the physics this stage adds: a *component* is
      selectable, but not one of the physical parameters a fluid
      simulation is actually specified by. See Criterion 12.
12. **Everything this stage adds is configuration-driven, validated, and
    documented -- not reachable only from a test fixture.**
    `docs/implementation/golden-demos.md`'s standing rule is that "if a
    demo needs a capability configuration doesn't yet expose, that
    capability gets added to the public configuration schema... the fix
    is never demo-specific code working around the gap." Stage 5 needs
    more of that than any stage so far, and the gap is concrete rather
    than anticipated -- checked field by field against
    `src/pyflow/configuration/schema.py` while drafting these criteria,
    not assumed:
    - **A viscosity, in a new `fluid:` section** (design question four,
      resolved 2026-08-28). `NumericsConfig.diffusion_coefficient` is
      one global constant serving the one transported scalar Stage 4
      had, and Criterion 5's Reynolds-number comparison cannot be
      configured without separating the two. **This is the project's
      first breaking configuration change**, because
      `diffusion_coefficient` migrates into the same new section rather
      than being left behind in `numerics:` -- the migration and its
      enumerated blast radius are recorded with that question's answer,
      and `examples/golden-demos/passive_scalar_transport.yaml` is the
      one committed config that has to move with it. **Carried out by
      TASK-041, which exists for this** rather than by whichever task
      first happened to need a viscosity.
    - **A corrector-loop tolerance, and an iteration limit.** Neither
      exists; `linear_solver_tolerance`/`linear_solver_max_iterations`
      are the inner CG solve's, a different convergence question at a
      different level. Criterion 3 says "the configured tolerance" and
      means it.
    - **A tangential boundary velocity**, `velocity_tangential` beside
      the existing normal one (design question two, resolved
      2026-08-28) -- with no way to say "this wall moves along itself",
      neither the cavity nor Couette can be configured at all. It also
      has to reach *two* component fields with different values at the
      same wall, which is design question one's recorded wrinkle.
    - **A way to say velocity is solved rather than prescribed.**
      `SimulationConfig.velocity`/`velocity_pattern` are documented as
      "a prescribed (not solved) constant vector -- Stage 5 is what
      eventually solves Navier-Stokes for real". This stage is that, so
      that sentence stops being true and something has to express the
      difference.
    - **Whatever the run-length or steadiness control turns out to be**,
      per Criterion 5's steady-state bullet -- a demo that must reach
      steady state needs to say so somewhere a config author can see.
    - Every field added is validated the way every existing one is (a
      rejection test per field, `tests/unit/test_configuration.py`'s own
      shape) and appears in the regenerated
      `docs/implementation/config-template.yaml` with a comment stating
      what counts as a valid value -- `make check-config-template` and
      `test_every_live_config_field_has_a_comment` both already gate
      this.
    - **P-016 applies to the six component-name sets, not to the pattern
      sets, and the difference is worth stating before someone applies
      the wrong one.** Stage 4's Criterion 2 forbade adding a member to
      `AdvectionSchemeName` and its five siblings, because a second
      scheme nobody needs is speculation. `ScalarTransportPattern`/
      `VelocityPrescriptionPattern` are the opposite case: a member is
      added there precisely *because* a demo needs it, which is the
      justification P-016 asks for, and Criterion 5's cases will need
      several (a lid-driven configuration, a shear layer, whatever the
      emergent-phenomenon pair settles on). Adding those is expected;
      adding a second advection scheme is not.
13. **The finished solver runs through `adr/ADR-003`'s seams, not around
    them** -- checked by substitution, not by reading the call sites.
    `docs/implementation/mvp.md` states the MVP's purpose as
    "correctness, understandability, and **architectural validation**",
    and this stage is the first time all six configuration-selected
    components are used together in one running simulation. Nothing
    before it could have checked the claim: `step` consumes
    `numerics.advection`/`.diffusion`/`.time_integration` and has never
    touched `numerics.pressure_coupling` or `.linear_solver` at all,
    because Stage 4 had nothing to correct.
    - A `PressureCoupling` test double, registered under its own name
      through the existing `register_pressure_coupling` registry and
      selected by configuration, is demonstrably the object the timestep
      calls -- so a solver that constructs `PISO` directly fails,
      however correct its physics. The same substitution check for
      `LinearSolver`, which reaches the timestep only through the
      coupling and has never been exercised end-to-end either.
    - **This is the criterion an otherwise-passing Stage 5 is most
      likely to fail silently**, which is why it is stated separately
      rather than assumed to follow from Criterion 4. A hardcoded `PISO`
      inside the timestep passes Criteria 1-5 exactly as well as a
      configured one does, produces the same Ghia comparison, and
      quietly retires the architectural claim the MVP exists to
      validate. Stage 4's Criterion 2 checked that a *name resolves* to
      a real instance; this checks that the resolved instance is what
      actually runs.

### Seven design questions: six resolved, one open

Flagged here at stage open rather than left to surface mid-implementation
(`docs/practices.md`, "When intent is ambiguous, hold a design session
before implementing"), following Stage 4's own precedent of recording its
two on the day its criteria were drafted and resolving each before the
task that needed it started.

**Six were put to the maintainer and decided on 2026-08-28, the same day
they were raised; the seventh is deliberately still open.** Each is kept
below as the question it was, with its answer, rather than rewritten into
a decision that reads as though it was never in doubt -- the same
treatment Stage 4's "Two design questions, both now resolved" section
gives its own pair. The one still open is question three (Rhie-Chow's
momentum coefficients), because it is the only one whose answer depends
on a measurement nobody has taken: TASK-027 already established that
reasoning about it without numbers produces a confident wrong answer.

**One: how does a vector field go through an interface that returns one
value per face? (TASK-031.)** `AdvectionScheme.flux(field, velocity)` and
`DiffusionScheme.flux(field)` both return a tensor of shape
`(mesh.num_faces,)` -- one scalar per face -- and
`FirstOrderUpwindAdvection`/`CentralDifferenceDiffusion` both read a cell
value with `float(field.value_at(cell))`. **Verified directly, not
reasoned about: handing either scheme a `VectorField` raises `TypeError:
float() argument must be a string or a real number, not 'tuple'`** -- so
velocity cannot go through the Stage 4 transport path today at all, and
Criterion 1 cannot be satisfied without answering this. Three readings,
none yet chosen:
- Momentum is transported as one `ScalarField` per component, with the
  `VectorField` assembled from them for the consumers that need one
  (`AdvectionScheme`'s own `velocity` argument, `GreenGaussDivergence`,
  rendering). Cheapest, and makes "velocity is transported like a scalar"
  literally true rather than analogously true.
- `flux` widens to return `(num_faces, num_components)`, with a scalar
  field being the one-component case. The most uniform, and the most
  expensive: it is a change to two Stage 3 interfaces and their contract
  suites, in the category `adr/ADR-008-time-integrator-derivative-callable.md`
  and `adr/ADR-009-pressure-coupling-dt.md` were.
- `step` adapts per component internally, leaving both interfaces
  untouched. Cheapest to write and the worst fit for Criterion 1's
  structural clause, since the adapter is exactly the special-casing that
  criterion forbids.

**Resolved 2026-08-28, maintainer's call: per-component `ScalarField`s.**
Momentum is transported as one `ScalarField` per component, with a
`VectorField` assembled from them for the consumers that genuinely need
one -- `AdvectionScheme.flux`'s own `velocity` argument,
`GreenGaussDivergence`, and rendering. It changes no Stage 3 interface,
works with both concrete schemes exactly as they stand, and makes
Criterion 1's claim literally rather than analogously true: velocity is
transported by the same code path a scalar is because it *is* a set of
scalars while in transport. **The wrinkle it inherits, recorded now
rather than met later:** `u` and `v` need different boundary values at
the same wall -- a no-slip moving lid is `u = U, v = 0` -- which is
precisely the "one global set of boundary conditions... does not yet
express field A and field B at the same wall" limitation TASK-040
deferred. Question two's answer supplies the wall's own tangential
value; how that reaches two component fields with different numbers is
TASK-031's to resolve, and it is the first real consumer of that
deferred case rather than a new problem.

**Two: `BoundaryFaceConfig.velocity` is the boundary-normal component
only, and a lid-driven cavity's lid is tangential. (TASK-031/034.)** That
field's own docstring already flagged this and deferred it "to whichever
task builds a concrete condition against a real consumer (P-016)" -- this
stage is that consumer, for two of its own cases at once: the cavity's
moving lid and Couette's moving plate are both tangential, and every wall
in both is no-slip, which is a *tangential* zero. A normal-component-only
boundary value cannot express either. Whatever is decided has a blast
radius that must be worked out in the same change:
`_validate_boundary_conditions_jointly`'s zero-net-flux check reads this
field and is about normal flux specifically,
`docs/implementation/config-template.yaml` is generated from the schema
and its own `FIELD_COMMENTS`, and `pyflow generate-config` (TASK-039)
emits it.

**Resolved 2026-08-28, maintainer's call: a second scalar,
`velocity_tangential`, beside the existing normal one.** In 2D each
boundary face has exactly one tangential direction, so a scalar is
sufficient and a vector would be a representation carrying information
the face geometry already supplies. It introduces no new concept, leaves
`velocity`'s meaning and the zero-net-flux validation that reads it
untouched, and the generated config template picks the field up on its
own. The two alternatives considered and not taken: making `velocity` a
component pair (cleanest single representation, but it changes an
existing field's type and moves every config, demo, template and the
joint validation with it), and a separate `wall_velocity` describing the
wall's own motion (arguably the most honest physics, at the cost of a
new concept plus consistency validation between it and `velocity`).

**Three: what does the corrector loop need that TASK-027's interface
could not supply? (TASK-033.)** Criterion 3's monotonic-convergence claim
is the one TASK-027 measured and could not make: on PyFlow's collocated
mesh, suppressing pressure-velocity decoupling under repeated correction
needs Rhie-Chow interpolation, which needs momentum-equation
coefficients, and TASK-027 verified numerically that three correction
strategies without them all leave most of the original divergence in
place (that task's own Design decision Two). TASK-031/032 are what
finally produce a momentum system to draw those coefficients from, so the
question is what carries them: a widened `PressureCoupling.correct` (the
`adr/ADR-009-pressure-coupling-dt.md` precedent, which widened it once
already), a momentum operator handed to the strategy at construction (the
`LinearSolver` precedent), or outer-loop state the strategy owns. **This
is the question most likely to move the stage's own scope, and the one to
resolve with numerical prototyping before Criterion 3 is turned into a
feature file** -- a criterion that cannot be met is worse than one
drafted late.

**Deliberately still open, 2026-08-28** -- the only one of the seven not
decided when the other six were. Not an omission: TASK-027 already
demonstrated what deciding this from an armchair costs. Three correction
strategies that all looked reasonable on paper each left most of the
original divergence in place, and the reason (the composed Green-Gauss
Poisson matrix is provably not symmetric) only became visible once
someone measured. Whichever mechanism carries the coefficients, the
choice is between three shapes that differ in cost and blast radius but
not in whether they *can* work -- and which of them is needed at all
depends on how far a momentum-coupled iteration actually converges,
which nobody yet knows. Answer it at TASK-033, with numbers, and record
it here.

**Four: what shape does this stage's new configuration surface take?
(TASK-031, with TASK-034 as its last consumer.)** Criterion 12 lists
what is missing and why each is needed; this question is how it is
expressed, and it wants deciding once rather than five times as each
task hits its own piece. The pieces, in the order they bite: a
kinematic viscosity separable from `NumericsConfig.
diffusion_coefficient` (Criterion 5 compares at Re = UL/nu, and the two
numbers are indistinguishable today); a corrector-loop tolerance and
iteration limit distinct from the inner CG solve's; a tangential
boundary velocity (design question two); a way to say velocity is
*solved* rather than prescribed; and whatever controls run length or
steadiness. Two further constraints on any answer, both already written
down elsewhere and easy to miss:
- TASK-040's own Design decision recorded that PyFlow has *one* global
  set of boundary conditions shared across every transported field,
  "correct for a single transported scalar... but does not yet express
  'field A is 300K at this wall, field B is 0 at the same wall'". Stage
  5 is the first stage with two genuinely different transported fields
  in one run -- velocity at a moving lid and a scalar at the same wall
  -- so the case that note deferred to Stage 6's "no new machinery"
  criterion may bite here first.
- **How the timestep is chosen under mesh refinement.**
  `NumericsConfig.timestep` is a single fixed number, and Criterion 5's
  cavity comparison runs the same case at three resolutions. Explicit
  RK4 is stability-limited by both the CFL condition (`dt` with `dx`)
  and the diffusive limit (`dt` with `dx` squared), so a timestep that
  is stable at the coarsest resolution is *guaranteed* to be unstable at
  the finest. Either the timestep becomes derivable from the mesh and
  the configured viscosity, or every refinement level carries its own
  configured timestep and the derivation lives in the scenario. Nothing
  in the repository does either today.

**Resolved 2026-08-28, maintainer's call, and this one costs a
migration: a new top-level configuration section for the fluid's own
physical properties, separate from `numerics:`.** Viscosity is a
property of the simulated fluid, not a numerical parameter, and the
repository defends that exact boundary in code
(`src/pyflow/physics/CLAUDE.md`: "phenomena here, numerical machinery
there"); a configuration that files viscosity under `numerics:` makes
the same category error the package layout refuses. Chosen over the
smaller option of flat additions to `NumericsConfig` beside
`linear_solver_tolerance`, which would have matched the existing style
and touched nothing.
- **`numerics.diffusion_coefficient` moves into the new section too**,
  and that is the real cost of this answer rather than an optional
  tidy-up: leaving it behind would put a scalar's diffusivity and a
  fluid's viscosity -- the same kind of quantity -- in two different
  sections, which is worse than either arrangement chosen
  consistently. That makes this a **breaking configuration change**, the
  first the project has made. Its blast radius, enumerated rather than
  discovered: `examples/golden-demos/passive_scalar_transport.yaml`
  (the one committed config that sets it),
  `tools/generators/generate_config_template.py`'s own
  `FIELD_COMMENTS`/`SECTION_COMMENTS` and the regenerated
  `docs/implementation/config-template.yaml`,
  `src/pyflow/configuration/schema.py`'s `PyFlowConfig` and loader, and
  `pyflow generate-config` (TASK-039). `make check-config-template`
  gates the template half automatically; the rest is a grep for the
  field name. **TASK-041 (below) is the task that carries this out**,
  split off on 2026-08-28 rather than left inside TASK-031, where it
  would have made a task about velocity transport responsible for the
  project's first breaking configuration change.
- **Named `fluid:`, not `physics:`** -- the section holds material
  properties (viscosity now, density when Stage 6 needs it), and
  `physics` already means something narrower and specific in this
  repository (`src/pyflow/physics/`: phenomena, not properties). Reusing
  the word for two different meanings in the same project is how the
  competing-vocabularies problem `docs/planning/backlog.md` records
  starts. A naming call rather than a structural one, and TASK-031 may
  overturn it with a better name as long as it does not reuse
  `physics`.
- The corrector-loop tolerance and iteration limit stay in `numerics:`,
  beside `linear_solver_tolerance`/`linear_solver_max_iterations`: those
  genuinely are numerical parameters, and the split this answer draws is
  the whole point of drawing it. Solved-vs-prescribed velocity and any
  run-length control stay in `simulation:`, which already describes what
  a run does rather than what the fluid is.

**Five: where does the pressure correction sit relative to RK4's
stages? (TASK-033/034.)** Not surfaced by anything before this pass, and
it decides what Criterion 4's "predictor, corrector loop, corrected
state" sequence actually *is*. `RK4Integrator.advance` evaluates its
`derivative` callable at four states within one timestep
(`adr/ADR-008-time-integrator-derivative-callable.md`), and the
projection has to happen somewhere relative to those four:
- **Outside the integrator** -- RK4 advances momentum with no pressure
  term to a provisional velocity, then the corrector loop projects once
  per timestep. The classical fractional-step arrangement, one pressure
  solve per step, and the reading `docs/handbook/numerical-methods/
  time-integration.md` and TASK-025's own criterion already anticipate
  when they say the finished solver's observed order will be "well below
  four". Its cost is exactly that: the splitting error caps the temporal
  order however good the integrator is, and RK4's intermediate stages
  see a velocity field that is not divergence-free.
- **Inside each stage** -- every `derivative` evaluation projects, so
  each stage sees a divergence-free field. More accurate, and four
  pressure solves per timestep instead of one.
The choice is not free either way, and it interacts with design question
three: whichever arrangement is chosen is what the corrector loop's
monotonic-convergence claim is measured *within*.

**Resolved 2026-08-28, maintainer's call: once per timestep, outside the
integrator** -- the classical fractional-step arrangement. RK4 advances
momentum with no pressure term to a provisional velocity, then the
corrector loop projects once. The splitting error caps the coupled
solver's temporal order well below RK4's own fourth, which is not a
concession this decision makes but a consequence
`docs/handbook/numerical-methods/time-integration.md`,
`docs/architecture/icds.md` and TASK-025's own criterion have all
already written down and expected. **The argument that settles it is
the error budget:** first-order upwind's numerical diffusion is the
dominant error term at every mesh this stage will run (Criterion 5's own
cavity bullet turns on exactly that), so paying four pressure solves per
timestep instead of one buys a reduction in splitting error that nothing
in this stage could measure. Revisit when Stage 8's less diffusive
schemes make the splitting error visible, not before. Recorded in the
scenario as well as here, per this question's own original instruction.

**Six: does the pressure gradient reach momentum through `SourceTerm`,
or only through the projection? (TASK-032/033.)** `src/pyflow/engine/
numerics/source.py`'s `SourceTerm` has existed since TASK-018 with no
concrete implementation, no registry entry, and no consumer -- the one
Stage 3 interface nothing has ever used. A momentum equation's pressure
gradient is the obvious candidate for its first implementation; a
projection method equally obviously does not need it, because the
correction *is* the gradient's effect. **Answer it explicitly either
way.** If the answer is no, say so where `SourceTerm` lives, so that an
interface with no implementation two stages after the physics arrived
reads as a decision rather than the oversight it currently resembles --
the same treatment Gradient/Divergence got at TASK-027, which is what
stopped them being invisible.

**Resolved 2026-08-28, maintainer's call: no -- and the reason is
recorded in `source.py` itself**, done in the same change as this
answer rather than left as an obligation for TASK-032 to remember. A
projection method does not route the pressure gradient through a source
term: the correction *is* that gradient's effect on the velocity field,
applied after the predictor, so implementing `SourceTerm` here would add
machinery nothing calls. Question five's answer is what makes this
clean-cut -- had the projection gone inside RK4's stages, the pressure
gradient would have had to enter the derivative evaluation, which is
exactly where a source term belongs. Stage 6's buoyancy coupling
(TASK-035) remains the natural first consumer: a body force *is* a
source term in the way a projection correction is not.

**Seven: does anything this stage builds belong in
`src/pyflow/physics/`? (TASK-031/034.)** The repository already
contradicts itself here, and the contradiction was found by asking the
question rather than by either document being reviewed:
`src/pyflow/physics/__init__.py`'s own docstring says the package is for
"physical models governing the fields the engine transports --
incompressible flow first", which is precisely this stage's subject,
while `src/pyflow/physics/CLAUDE.md` opens "**Empty until Stage 6, and
empty on purpose**" and lists only Stage 6's phenomena. Both were
written before anyone had a momentum equation to file. The boundary
that `CLAUDE.md` states is a good one and worth keeping -- phenomena
here, discretisation in `engine/numerics/`, because `adr/ADR-003`'s
swappability claim and Stage 6's field-centric claim both become
untestable if the two mix -- but it does not by itself settle where an
incompressible-flow momentum equation sits, since the equation is
physics and nearly everything this stage actually writes is its
discretisation. **Whichever way it goes, those two files stop
contradicting each other in the same change.** Stage 6's own measurable
claim depends on the answer too: its TASK-035 intent proposes "counting
the lines this task adds outside `physics/`" as the test of that
stage's goal, which measures very little if `physics/` is still empty
when Stage 6 starts.

**Resolved 2026-08-28, maintainer's call: everything Stage 5 builds
stays in `engine/`, and `physics/__init__.py`'s docstring is corrected
-- done in the same change as this answer**, so the contradiction does
not outlive the session that found it. Nearly all of what this stage
writes is discretisation and orchestration, which
`src/pyflow/physics/CLAUDE.md` explicitly excludes, and that file is the
more carefully reasoned of the two: it defends the phenomena/machinery
line as the thing that keeps `adr/ADR-003`'s swappability claim and
Stage 6's field-centric claim testable at all. The docstring's
"incompressible flow first" was written at TASK-000, before either claim
existed, and describing the package by the physics PyFlow simulates
rather than by the code that belongs in it is what made it read as a
Stage 5 obligation. Stage 6's own metric is unaffected: counting lines
added outside `physics/` works from an empty baseline, and arguably
works better, since every line TASK-035 adds inside it is then genuinely
attributable to that task.

### Discharge map

Every criterion has an owning task, assigned now rather than
reconstructed at the exit audit, following Stage 3 and Stage 4's own
precedent. A task's own **Discharges** section is authoritative; this
table is the index.

**Build order is TASK-041, 031, 032, 033, 034**, and structural rather
than convenient: TASK-041 settles the configuration surface everything
after it reads, TASK-032's pressure field has nothing to be solved
against until velocity is transported, TASK-033's corrector loop has
nothing to correct until both exist, and TASK-034 assembles what the
rest build. Numerical order from 031 onward, for once.

**TASK-041 was added 2026-08-28, after this stage's criteria were
drafted and while auditing whether it was ready to start** -- the same
shape of late addition Stage 4 made with TASK-040, and for the same kind
of reason. Design question four's answer (a new `fluid:` section, with
`numerics.diffusion_coefficient` migrating into it) had landed inside
TASK-031 by default, which gave "Velocity Field Support" a cross-cutting
breaking configuration change with no velocity in it and made it the
widest task in the stage. It keeps its own number and takes first
position: **position in this document says what happens when, the number
does not**, the same reasoning TASK-040 and TASK-021/022 were kept under.

The only thing that could reorder the rest is design question three's
answer, if it turns out the momentum coefficients TASK-033 needs must be
produced by TASK-031's own work rather than read from it -- which would
make part of TASK-033 a TASK-031 obligation, not a reordering.

| Criterion | Discharged by |
|-----------|---------------|
| 1. Velocity transported by the same mechanism as every other field | TASK-031, subtasks a, c and d between them |
| 2. Pressure solved from the constraint, not transported | TASK-032 |
| 3. Divergence decreases monotonically to the configured tolerance | TASK-033 |
| 4. One timestep solves momentum and continuity together | TASK-034 |
| 5. Physical correctness against a known answer, per case | TASK-034, each for its own bullet, Couette flow included -- TASK-033 supplies the corrector loop it needs but does not itself run the comparison |
| 6. Rejection paths exercised against real bad input | TASK-041 and TASK-031..034, each for its own error conditions |
| 7. Executable Gherkin criteria, `make check-scenarios` gates | TASK-041 and TASK-031..034, each for its own `.feature` file -- TASK-041 included, and its entry says why a task that computes nothing still owes one |
| 8. Demonstrations: Lid-Driven Cavity and Heat Diffusion | TASK-034 (this stage's last task) |
| 9. `make ci` green on a real runner | TASK-034 |
| 10. Documentation matches the tree, capability map included | TASK-034 |
| 11. `mvp.md`'s Definition of Done discharged item by item | TASK-034, reading Criterion 11's own table back against what landed |
| 12. Configuration surface is real, validated and documented | TASK-041 for the `fluid:` section, viscosity and `diffusion_coefficient`'s migration; TASK-031 for solved-vs-prescribed velocity and whatever its subtask (c) needs; TASK-033 for the corrector tolerance and iteration limit; TASK-034 for the tangential boundary value and whatever run-length control the demos need. Design question four settles the *shape* once, so these are additions in one established style rather than four tasks each inventing their own |
| 13. The solver runs through ADR-003's seams, checked by substitution | TASK-034, the first task with a whole timestep to substitute into -- though TASK-033 is where the coupling first reaches the step at all, so a substitution check landing there instead discharges it equally well |

**TASK-034 is this stage's last task in build order and therefore owns
the stage-level criteria** -- the demonstrations, the CI evidence, the
documentation sweep and the MVP reconciliation -- the same assignment
Stage 4 made to TASK-030 for the same reason.

### Intent, recorded now

Recorded 2026-08-22, ahead of the criteria above, because it is the
durable half and the half this repository keeps losing. Each line states
what the task must not merely *nominally* satisfy (`docs/practices.md`,
"The intent lives in the qualifier"). The Completion Criteria above were
drafted against these on 2026-08-28, not in place of them.

### Status as of 2026-08-29: Stage 5 complete, thirteen of thirteen criteria met

**Eight of these thirteen verdicts were overstated when first written,
and this stage's exit audit found all eight.** The first table was written on
2026-08-29 as TASK-034 closed, in the session that wrote TASK-034; this
one is the corrected table, produced by a separate pass run under
`prompts/common/AUDITOR.md`'s stance. The eight amended rows say what
was claimed, what was actually true, and what was done about it, rather
than being silently rewritten (root `CLAUDE.md`'s Integrity section, and the
precedent Stage 3's Criterion 8 and Stage 4's own three amended rows
both set). **Stage 5 closes at thirteen of thirteen, but not the
thirteen it started with.** Criterion 5 gained the stated, defended
absolute tolerance its own text always asked for; Criterion 6's second
named rejection surface was built rather than assumed inherited;
Criterion 7's degenerate-fixture rule gained the one exception Ghia's
own reference frame forces, recorded rather than quietly taken;
Criterion 9 was discharged against a real two-platform run rather than a
local pass; Criterion 10's six documentation defects are fixed;
Criterion 11's own MVP -- the thing this stage exists to deliver -- is
now recorded as reached in the two documents that own that concept,
rather than only inside this table; Criterion 12's `velocity_solved` now
means the same thing on both live paths, instead of solving on one and
self-advecting on the other;
Criterion 13's *second* substitution check -- the one its own text names
and nobody built -- now exists and is mutation-verified. Nothing here
reopened a task.

**One of the eight was a defect in shipped behaviour, not only in a
verdict**, and it is the one worth reading first: Criterion 12's, where
a configuration field named `velocity_solved` produced a
pressure-corrected velocity or a merely self-advected one depending on
whether a `scalar_pattern` happened to be set. It had been honestly
recorded by both TASK-031 and TASK-034 -- in two `CLAUDE.md` files, and
against no criterion. **A gap recorded in a `CLAUDE.md` is a gap
somebody chose not to fix; a gap recorded against a criterion is one the
stage cannot close over.** That distinction is what let this one through
a criterion whose own text is "not reachable only from a test fixture".

**The distinction worth keeping is the same one Stage 4's audit found,
recurring:** the first table's thirteen was arrived at by reading the
first half of most of these criteria and stopping -- and, in Criterion
12's case, by reading a known gap's own honest write-up without asking
which criterion it fell under. Criterion 13 says "The same
substitution check for `LinearSolver`" in its second sentence;
Criterion 6 lists five surfaces and the audit found four;
Criterion 5's own tolerance clause is the last line of its Ghia bullet.
Every one of them was a sentence the criterion had already written down.

**Criterion 10 is the one this audit would flag as a standing pattern
rather than a one-off.** Six stale claims, in six files no Stage 5 task
opened -- and one of them, `README.md`'s own "Current Phase" section, is
the *second* time that exact section has gone a full stage stale (the
Stage 2 exit audit found it claiming the project "is beginning Stage
2"). A rule that has now failed twice is not a rule; this audit
therefore made it mechanical instead, per `docs/practices.md`'s "Let a
checked artifact carry status, not a tense":
`tools/generators/generate_status_report.py`'s drift check now reads
README's Current Phase section and fails `make ci` when the stage it
names is not the roadmap's own first stage not marked complete.

**A second check turned out to be inert rather than absent, which is
worse.** `generate_status_report.py`'s Gherkin-scenario drift rule
required a literal space before "are Gherkin scenarios"; a later edit
hard-wrapped this document's line between the count and that phrase, and
a pattern that stops matching reports *nothing to check* -- which reads
exactly like a clean pass. The roadmap sat claiming 79 scenarios against
a live 94, behind a green gate, which is precisely the failure mode
`make check-scenarios` exists to prevent for feature files, reproduced
inside the checker. All three claim patterns are now whitespace-
tolerant, with a regression test quoting the real wrapped sentence.

**Evidence.** Criterion 9 is discharged by two real runs, both green on
`ubuntu-latest` and `windows-latest`, read from `gh run view`'s own
per-job output: `33269489214` (this stage's last PR, #47) and
`33270312866` (the merge of that PR to `main`). This audit's own branch
additionally passes `make ci` locally, and its own CI run is what the
Merge Gate requires before *it* merges -- stated rather than assumed,
since a local pass is not that evidence.

| Criterion | Verdict |
|-----------|---------|
| 1. Velocity transported by the same mechanism as every other field | **Met.** TASK-031's own subtasks a/c/d. The structural no-special-casing check is `tests/unit/test_velocity_field_support.py`'s own `_then_no_special_casing_in_orchestrator`, bound to `velocity_field_support.feature`'s last scenario -- it inspects `inspect.getsource(simulation)`, the whole module, so `navier_stokes_step` is covered by it too. *(The first table named `test_navier_stokes_timestep.py` as the home of this check; it is not, and never was. Corrected rather than quietly moved.)* |
| 2. Pressure solved from the constraint, not transported | **Met.** TASK-032. The null-space bullet's "removed explicitly, and which remedy was chosen is visible and tested" is genuinely discharged: `ConjugateGradientSolver`'s own *gated* mean-subtracting projection, documented in `icds.md` and `engine.md` and checked by `pressure_field.feature`'s own constant-shift scenario -- re-verified against the source in this audit rather than taken from the first table. |
| 3. Divergence decreases monotonically to the configured tolerance | **Met as amended 2026-08-29; one clause was unasserted as first written.** The loop is genuinely multi-pass (TASK-033) and the iteration-limit and partial-correction scenarios both have real teeth. **But the criterion's own "the fixture's initial maximum divergence is stated and is orders of magnitude above the configured tolerance" was stated nowhere and asserted nowhere** -- and that clause is load-bearing, since it is exactly what stops "non-increasing at every element" and "last element at or below tolerance" from passing for a corrector that does nothing. Measured in this audit: the fixture starts at 1.85 against a configured 1e-4, four orders of magnitude, so the claim was true all along and unchecked. **Fixed in the audit's own change:** `pressure_correction_loop.feature`'s first scenario gains "the recorded divergence sequence starts orders of magnitude above the configured tolerance", with the measured figure written into the feature file and the module's own bound set an order of magnitude below it. |
| 4. One timestep solves momentum and continuity together | **Met.** `navier_stokes_step`; predictor/corrector/corrected sequence, both null tests, determinism -- all real-engine scenarios, all passing. Checkpointing is correctly absent (this criterion excludes it); `docs/architecture/sequences.md`'s placeholder was re-anchored in this audit, since "update once TASK-034 lands" stopped being actionable the moment TASK-034 landed without building it. |
| 5. Physical correctness against a known answer, per case | **Met as amended 2026-08-29; the Ghia bullet's last clause was undischarged.** Couette at solver tolerance; Taylor-Green matched/mismatched pair; kinetic energy never increasing; Ghia convergence across three real resolutions plus the finest's own vortex structure -- all real and all passing. **But the criterion's own "the absolute tolerance is stated and defended in the feature file against the mesh actually used" had no counterpart in the scenario**: only monotonic decrease was asserted, which errors of 10, 5 and 2 would satisfy exactly as well as the real ones do. **Fixed in the audit's own change** -- the finest resolution's own error against Ghia's profiles is now bounded by a stated, measured figure, defended in the feature file against the mesh it was measured on. |
| 6. Rejection paths exercised against real bad input | **Met as amended 2026-08-29; one of the five named surfaces was never built.** Four were: the velocity component-count check, the component-set-size and cross-mesh reassembly checks, and the corrector loop's own iteration-limit exhaustion. **"A configuration that names a boundary treatment velocity has no meaning for" was not**, and no task recorded dropping it -- a periodic boundary carrying a prescribed velocity, pressure, scalar value or per-field override loaded cleanly and was then ignored outright by `assemble_numerics`, which skips the boundary-condition registry entirely for `type: periodic`. **Fixed in the audit's own change** (maintainer's call: build it rather than record it as dropped): `_validate_boundary_conditions_jointly` gains a fourth rule, scoped to non-default values so every periodic configuration this repository already ships stays valid, with six rejection tests and one acceptance test in `tests/unit/test_configuration.py` beside its two sibling rules. |
| 7. Executable Gherkin criteria, `make check-scenarios` gates | **Met as amended 2026-08-29; one exception was taken and not recorded.** The gating half was always real. **The degenerate-fixture half was not, for the cavity**: this criterion requires every scenario's fixture to use "a non-square mesh, non-trivial origin... and a lid velocity that isn't 1", and the Ghia cavity fixture is square, at origin `(0, 0)`, with a lid velocity of exactly 1.0. Two of those three are forced -- Ghia's tabulated Re = 100 profiles are nondimensionalised on a unit square with a unit lid speed, so a non-square cavity or a different lid speed would not be comparable to the reference at all. **The origin was not forced**, and the maintainer's call was to fix what could be fixed rather than only record it: the cavity fixture now sits at a non-trivial origin, converting to unit-cavity coordinates explicitly where the comparison needs them. The two genuinely-forced exceptions are recorded in the feature file where a reader meets them. |
| 8. Demonstrations: Lid-Driven Cavity and Heat Diffusion | **Met.** Both built, both with a CLI-subprocess regression test and a quantitative physical check; neither demo test asserts absolute field values, which is what keeps Criterion 4's cross-platform clause honest. |
| 9. `make ci` green on a real runner | **Met.** Two runs, both `success` on `ubuntu-latest` and `windows-latest`, read from `gh run view`'s own per-job output rather than inferred from a merged PR: `33269489214` (PR #47) and `33270312866` (its merge to `main`). *(The first table recorded this as the audit's one honest gap, correctly: it was written before either run's result was checked.)* |
| 10. Documentation matches the tree, capability map included | **Not met on 2026-08-29 as first claimed; met after this audit.** Six stale claims, in six files no Stage 5 task opened -- the exact failure mode `docs/practices.md`'s "A stage's documentation sweep is a grep, not a diff review" names, and which Stage 4's own audit produced that rule after finding seven of. **`README.md`'s "Current Phase" section said "Stage 5 -- First Fluid Solver -- not yet started", on the day Stage 5 closed**, alongside "Stage 5 will solve incompressible flow" and a "most recent demonstration" that was two demos out of date. **`docs/architecture/sequences.md`** -- the document whose only stated job is "in what order do things actually happen when PyFlow runs" -- contained no mention of pressure, predictor, corrector or `navier_stokes_step` at all, and still asked to be updated "once TASK-034 lands". **`docs/architecture/rendering.md`** claimed the field-to-GPU conversion happens "not per frame and not per timestep... Stage 4 onward, not this", stale since TASK-030 and now doubly so -- the third stale claim in that one file about a stage that had already closed. **`src/pyflow/configuration/schema.py`**'s `NumericsConfig` docstring said "the other four still resolve to their own reference implementation", flatly contradicted by `assembly.py`'s own "zero `_Null*` classes remain". **`adr/ADR-003`** still described `PISO` in the present tense as a single correction pass. And **`docs/implementation/golden-demos.md`** pointed `mvp.md`'s "golden demo exists" criterion at "the Initial Golden Demo below (Capability Level 1)" -- wrong in both halves once TASK-034 landed, and contradicted by `planning/data/demos.yaml`'s own `demo-lid-driven-cavity -> capability-level-2` edge, which had been right all along. All six fixed in the audit's own change, and README's own half made mechanical rather than remembered (above). Capability map: verified directly -- `planning/data/demos.yaml`/`capabilities.yaml` already carried both demos with `validates -> capability-level-2` edges, and `docs/planning/capability-map.md` is deliberately status-free, so nothing was owed there. |
| 11. `mvp.md`'s Definition of Done discharged item by item | **Met as amended 2026-08-29.** Every row of its own table holds, re-read against the tree rather than against the first table. **But neither `docs/implementation/mvp.md` nor `docs/planning/releases.md` said the MVP had been reached** -- and `releases.md` names "Reaching the MVP" as one of exactly three concrete triggers for defining a release process, with a Maintenance section instructing that it be updated "the moment any trigger condition above is met". The trigger fired when TASK-034 landed. Fixed in the audit's own change, at the maintainer's direction: `mvp.md` records the MVP as reached, and `releases.md` is rewritten with a real release process rather than a restated trigger. |
| 12. Everything this stage adds is configuration-driven, validated, documented | **Not met on 2026-08-29 as first claimed; met after this audit.** `simulation.velocity_solved` had two live paths and meant two different things. With no `scalar_pattern`, `bootstrap.py`'s `_add_solved_velocity_rendering` called `navier_stokes_step` and produced a genuinely incompressible velocity. **With a `scalar_pattern`, `_add_passive_scalar_transport` transported velocity's components like any other scalar and never pressure-corrected them** -- so a configuration saying "solved" produced a velocity that was not, chosen by whether a scalar happened to be configured, with no error and nothing rendered differently. Measured, not argued: maximum divergence sat at 9.16 -> 8.24 -> 6.95 over 1, 10 and 40 frames uncorrected, against 2.30 -> 0.47 -> 0.057 corrected. **TASK-031 and TASK-034 both knew** -- it is recorded in `src/pyflow/configuration/CLAUDE.md` and in `bootstrap.py`'s own docstrings as a "real, pre-existing gap this task did not close" -- **and it was recorded against no criterion, which is exactly how it survived this row being marked met the first time.** A gap written down in a `CLAUDE.md` is a gap somebody chose not to fix; a gap written down against a criterion is a gap the stage cannot close over. **Fixed in the audit's own change** (maintainer's call: route it through, rather than reject the combination or record it): both live paths now call `navier_stokes_step`, with a regression test asserting the scalar-plus-solved-velocity path's own divergence collapses, measured against both behaviours before its bound was chosen. Otherwise met, with one deliberate exception recorded rather than silently narrowed: run-length/steadiness stayed a validation-scenario constant, not a config field (TASK-034's own Discharges explain why neither the demos nor the direct-engine Ghia scenario need one). `fluid:`, the corrector-loop tunables, solved-vs-prescribed velocity, and per-field wall values (superseding `velocity_tangential`) are all real, validated, documented config surface. `simulation.stable_timestep` is engine code no live run reaches -- noted rather than filed as a violation, since the *capability* it serves (choosing a timestep) is configured, and the helper is a stated, documented derivation rather than a hidden one. |
| 13. The solver runs through ADR-003's seams, checked by substitution | **Not met on 2026-08-29 as first claimed; met after this audit.** This criterion names **two** substitution checks. The `PressureCoupling` one was built and is real. **The `LinearSolver` one -- "which reaches the timestep only through the coupling and has never been exercised end-to-end either" -- was not**: `register_linear_solver` was never called anywhere outside `assembly.py`'s own built-in registration, so a `PISO` that constructed its own `ConjugateGradientSolver` instead of using the resolved one would have passed every scenario in this repository. Confirmed by mutation, not argued: making `PISO.__init__` discard its injected solver leaves the whole suite green. **Fixed in the audit's own change** -- `navier_stokes_timestep.feature` gains a scenario registering a recording `LinearSolver` under its own name, selected through `NumericsConfig`, and asserting the timestep's own pressure solve asked it; verified to fail under exactly that mutation and to pass without it. This is the criterion its own text called "the one an otherwise-passing Stage 5 is most likely to fail silently", and it was half-failing silently. |

## TASK-041

Fluid Configuration Section

**Status: Done, 2026-08-28, Stage 5's first task.** A real gap between
this task's own Dependencies section (below, "no engine dependency at
all") and the live repository was found while implementing, not
predicted in advance: `src/pyflow/engine/numerics/assembly.py`'s
`assemble_numerics` already read `NumericsConfig.diffusion_coefficient`
directly (TASK-024, 2026-08-27), so migrating the field out from under
it was a real, required engine-side change, not the zero-engine-impact
migration the Dependencies section below claims. Recorded honestly here
rather than silently fixed and left for a reader to rediscover
(`docs/CLAUDE.md`'s Integrity section): `assemble_numerics` gained a
second parameter, `diffusion_coefficient: float = 1.0` (the default
preserves every existing caller that only cares about scheme selection),
and `bootstrap.py`'s own call site now threads
`config.fluid.diffusion_coefficient` through explicitly. See
`src/pyflow/engine/numerics/assembly.py`'s own docstring and
`src/pyflow/engine/CLAUDE.md`'s `assembly.py` entry for the mechanical
detail.

**Added 2026-08-28, while auditing this stage's own readiness to start
-- not anticipated when Stage 5's criteria were drafted the same day.**
Design question four's answer (a new `fluid:` section, with
`numerics.diffusion_coefficient` migrating into it) landed inside
TASK-031's scope by default, which made "Velocity Field Support" the
widest task in the stage and gave it a cross-cutting breaking change
that has nothing to do with velocity. Split out for the same reason
Stage 4 added TASK-040 out of numerical order: the work is real, it is
independently verifiable, and everything after it is easier once it
exists. **Numbered 041 and placed first in this stage's document order
-- position says what happens when, the number does not**, exactly as
TASK-040 and TASK-021/022 before it.

**Intent:** this is a configuration change with no physics in it, and
the temptation is to treat it as a rename. It is not. It is the first
change this project has made that **invalidates configuration files
users may already have**, and the criterion that matters is that the
break is complete and visible rather than partial and silent -- a config
still setting `numerics.diffusion_coefficient` must fail loudly, not be
quietly ignored while the simulation runs with a default.

### Purpose

Give the physical properties of the simulated fluid a home of their own,
separate from the numerical parameters that act on them, and move the
one property already misfiled there into it.

### Dependencies

TASK-005 (the configuration framework), TASK-019 (`NumericsConfig` and
whole-configuration validation), TASK-039 (`pyflow generate-config`),
and the `make config-template` generator added 2026-08-28. **Wrong as
drafted, corrected once implementation found the gap (this task's own
Status note, above): `viscosity` alone has no engine dependency until
TASK-031b, but `diffusion_coefficient` already had one the moment this
task moved it out of `NumericsConfig` --
`src/pyflow/engine/numerics/assembly.py`'s `assemble_numerics` (TASK-024)
already read it off that section directly.** Closed in this task, not
deferred: `assemble_numerics` gained a `diffusion_coefficient: float`
parameter (defaulted to `1.0` so every scheme-selection-only caller is
unaffected) and `bootstrap.py` threads
`config.fluid.diffusion_coefficient` through it explicitly.

### Design decision, inherited rather than made here

Design question four, resolved 2026-08-28 (above): the section is named
`fluid:` rather than `physics:`, viscosity lives in it, and
`diffusion_coefficient` migrates into it rather than being left behind.
That question's own answer records why, including the naming argument
and the enumerated blast radius. **This task does not reopen it**; it
carries it out.

**One decision this task does make: it ships `viscosity` rather than
performing the migration alone.** A pure move -- creating a section and
relocating one field, with nothing new in it -- would be a breaking
change buying nothing until TASK-031 arrives, which is a poor trade and
a hard thing to justify to a user whose config just broke. Shipping the
field that gives the section its reason to exist makes the break worth
making once. The cost is stated plainly: `fluid.viscosity` is a
configurable value that nothing reads until TASK-031b, which is the
narrow, deliberate exception to P-016 this task takes rather than
pretends away.

### Artifacts Produced

- `src/pyflow/configuration/schema.py` -- a `FluidConfig` dataclass
  (`viscosity`, `diffusion_coefficient`), its `validate`, and its slot on
  `PyFlowConfig`; `diffusion_coefficient` removed from `NumericsConfig`.
- `tools/generators/generate_config_template.py` -- a `SECTION_COMMENTS`
  entry for the new section and `FIELD_COMMENTS` for both its fields;
  the stale `numerics.diffusion_coefficient` entry removed.
- `docs/implementation/config-template.yaml` -- regenerated, never
  hand-edited (`make config-template`).
- `examples/golden-demos/passive_scalar_transport.yaml` -- the one
  committed config that sets the migrating field.
- `tests/features/fluid_configuration.feature` and its binding module,
  `tests/integration/test_fluid_configuration.py` -- `tests/integration/`,
  not `tests/unit/`, because its own migration scenario needs a real CLI
  subprocess run (`tests/CLAUDE.md`'s own split); not a golden demo
  either, so it supplies its own local steps.
- **Not predicted when this task was drafted, found while implementing
  (this task's own Status note, above):**
  `src/pyflow/engine/numerics/assembly.py` -- `assemble_numerics` gained
  a `diffusion_coefficient: float = 1.0` parameter, since it could no
  longer read the field off `NumericsConfig`; `src/pyflow/bootstrap.py`
  -- its one call site now threads `config.fluid.diffusion_coefficient`
  through explicitly. `tests/unit/numerics/test_assembly.py`,
  `tests/unit/test_main.py`, `tests/unit/test_generator.py` and
  `tests/integration/test_cli.py` -- each asserted the old
  `NumericsConfig`/`PyFlowConfig` shape directly (a `diffusion_coefficient`
  field, or a fixed top-level key order) and needed updating to the new
  one.

**Why this task has a `.feature` file when it computes nothing**, stated
rather than assumed: Stage 5 Criterion 7 says *every* task's acceptance
criteria are a Gherkin file, and Stage 3's exemption does not extend
here (`adr/ADR-007-executable-acceptance-criteria.md` -- that exemption
is for criteria "about architecture... with no user-observable behaviour
to describe"). Loading a configuration file *is* user-observable
behaviour, and this task's central claim -- an old config fails loudly,
a new one works, the demo still runs -- is scenario-shaped rather than
assertion-shaped. The per-field rejection tests stay in
`tests/unit/test_configuration.py` where every other field's already
are; the feature file carries the migration's own claims, not a Gherkin
restatement of type validation.

### Acceptance Criteria

`tests/features/fluid_configuration.feature` is the criteria. Written to
cover, at minimum:

- A configuration setting `fluid.viscosity` and `fluid.diffusion_
  coefficient` loads, and both values arrive on the loaded config
  object.
- **A configuration still setting `numerics.diffusion_coefficient` is
  rejected with a named error that says where the field went** -- not
  ignored, not silently defaulted. This is the task's whole point: a
  breaking change that fails quietly is worse than one that fails.
- The Passive Scalar Transport golden demo still runs through the real
  CLI and still produces its own already-tested result -- the migration
  changed where a number lives, not what the simulation does. Checked by
  running it, not by inspecting the config.
- `viscosity` and `diffusion_coefficient` are independent fields:
  setting one leaves the other at its own default. (That they have
  *different effects* is TASK-031b's claim, which cannot be made here --
  nothing reads viscosity yet.)
- Each field rejects bad input with a named error
  (`tests/unit/test_configuration.py`, Criterion 12), and the
  regenerated template carries a comment for both, which
  `make check-config-template` and
  `test_every_live_config_field_has_a_comment` already gate.

### Discharges

Criterion 12, its viscosity and `diffusion_coefficient`-migration share.
Criterion 6 and Criterion 7, its own share.

---

## TASK-031

Velocity Field Support

**Status: Done, 2026-08-29, Stage 5's second task -- all four subtasks
in one branch, per the roadmap's own "meant to be done in one session"
instruction.** Three design choices made while implementing, not
anticipated when this task was drafted, recorded here rather than left
implicit:

- **`IncompatibleVelocityFieldError` moved from `advection.py` to
  `vector_field.py`.** Subtask (a)'s own rejection (a component count
  disagreeing with the mesh's dimensionality) needed the same class
  `AdvectionScheme._check_velocity` already raises, per subtask (d)'s
  own criterion ("the existing named error") -- but `vector_field.py`
  cannot import it back from `advection.py`, which already imports
  `VectorField` from there. Co-located with `VectorField` instead
  (`advection.py` now imports it from there); every other importer is
  unaffected, since the name still resolves the same way through
  `engine/numerics/__init__.py`'s own re-export.
- **`SimulationConfig.velocity_solved: bool`, not a widened
  `velocity_pattern`.** A pattern says what shape the initial condition
  has; solved-vs-prescribed says what happens to it afterward -- the
  same switch-vs-configured-thing distinction this project already
  learned once (`RenderingConfig.show_mesh`/`grid_color`,
  `src/pyflow/configuration/CLAUDE.md`) and did not want to relearn here.
- **`bootstrap.py`'s own live-loop wiring (`_add_passive_scalar_transport`)
  supports `velocity_solved` only alongside a configured `scalar_pattern`**
  -- a velocity-only live run has no rendering path yet (no per-frame
  vector-arrow display exists), so `velocity_solved` set without a
  scalar is validated but has no visible effect through `bootstrap.py`
  today. The mechanism itself (`step` transporting velocity's own
  components) is proven directly against `simulation.step()`
  (`tests/features/velocity_field_support.feature`), independent of this
  gap; TASK-034's own Lid-Driven Cavity is the likely first real
  consumer of velocity-only live rendering. Recorded here rather than
  silently narrowed, the same honesty TASK-041's own Status note applied
  to its own found gap.

**Intent:** velocity is the first field the engine *transports* rather
than merely stores. The distinction worth a criterion is that nothing
here may special-case velocity -- Stage 6 adds four more transported
fields (TASK-035..038) on the claim that the architecture is
field-centric, and that claim is only testable if velocity went through
the same path they will.

### Purpose

Make velocity a transported field: something `src/pyflow/engine/
simulation.py`'s `step` advances, using the same Advection, Diffusion
and Time Integrator components a scalar already goes through, rather
than something supplied fixed from configuration as Stage 4's own
Passive Scalar Transport demo does
(`src/pyflow/configuration/schema.py`'s `SimulationConfig.velocity`, "a
prescribed (not solved) constant vector").

### Dependencies

TASK-012 (`Mesh`), TASK-014..016 (`Field`/`ScalarField`/`VectorField`),
TASK-023 (`FirstOrderUpwindAdvection`), TASK-024
(`CentralDifferenceDiffusion`), TASK-025 (`RK4TimeIntegrator`),
TASK-028/029 (the real Dirichlet/Neumann conditions a velocity boundary
resolves to), TASK-040 (`step`, `accumulate_flux_to_cells`), and
**TASK-041**, which supplies the `fluid.viscosity` this task's own
subtask (b) is the first thing to read.

### Design questions, all resolved for this task

**One, two and four, all answered 2026-08-28 (maintainer's calls, above)
-- so nothing blocks this task's drafting.** In the order they bite
here:
- **One:** momentum is transported as one `ScalarField` per component,
  with a `VectorField` assembled for the consumers that need one. No
  Stage 3 interface changes.
- **Four:** a new `fluid:` configuration section holds viscosity, with
  `numerics.diffusion_coefficient` migrating into it. **Carried out by
  TASK-041, not here** -- this task consumes that surface rather than
  building it, which is why TASK-041 exists at all.
- **Two:** `velocity_tangential` beside the existing normal
  `BoundaryFaceConfig.velocity`. Listed against TASK-034 as well,
  because whichever task first needs a no-slip *moving* wall is where it
  lands; subtask (c) below needs per-component wall values but not
  necessarily a moving one.

**The one thing these answers leave for this task to work out** is how a
single wall's boundary values reach two component fields that need
different numbers there (`u = U`, `v = 0` at a moving lid) -- design
question one's own recorded wrinkle, the first real consumer of the "one
global set of boundary conditions" limitation TASK-040 deferred, and the
reason subtask (c) exists as its own step rather than as part of (d).

### Subtasks

**Four steps, meant to be done in one session**, not four sessions:
they share a branch, a test module and a review cycle, and none of them
is worth a `Status:` line of its own. The split exists because this task
has four separable claims and a single undifferentiated "velocity works
now" is exactly the shape of task that gets called done while one of its
claims was never checked. **Each subtask below is done when its own
acceptance criteria pass**; the task is done when all four do, plus the
whole-task obligations under Acceptance Criteria at the end.

Strict TDD applies within each (`docs/practices.md`): the subtask's
failing scenarios first, then its implementation, before moving to the
next. Build them in order -- (b) needs (a)'s decomposition, (c) needs
something to give boundary values *to*, and (d) is the wiring the first
three make possible.

#### TASK-031a -- Velocity as component fields

A `VectorField` decomposes into one `ScalarField` per component, and
those components reassemble into an equal `VectorField`. This is the
whole of design question one's answer, isolated from anything that
transports or configures.

*Acceptance criteria:*
- Round trip: decompose then reassemble reproduces the original field's
  values exactly, on a non-square mesh with non-unit spacing and a
  non-trivial origin, for values that are not 0 or 1 anywhere.
- Component fields carry the mesh they came from, and each is a real
  `ScalarField` -- usable by any existing scheme with no adapter.
- The naming convention for a component field is fixed and stated once,
  in the code, not re-derived per caller.
- Reassembly rejects, with named errors: a component count that
  disagrees with the mesh's dimensionality, and components defined over
  different meshes (Criterion 6).

#### TASK-031b -- Viscosity, distinct from a scalar's diffusivity

`fluid.viscosity` (TASK-041) becomes the diffusion coefficient the
*momentum* components are diffused with, while a transported scalar
keeps using `fluid.diffusion_coefficient`. This is the smallest subtask
and it is separated deliberately: it is the one whose failure mode is
silent, since a run using the wrong coefficient produces a plausible
flow rather than an error.

*Acceptance criteria:*
- Changing `fluid.viscosity` changes the diffusive flux computed for a
  velocity component and leaves a scalar's own diffusive flux
  unchanged; changing `fluid.diffusion_coefficient` does the reverse.
  Both directions, since either alone passes if the two are wired to the
  same number.
- The two configured values are different from each other and neither is
  1 in the fixture -- Criterion 7's degenerate-fixture rule, which this
  subtask is the easiest place in the stage to violate.

#### TASK-031c -- Per-field boundary values at one wall

Two transported fields get different boundary values at the *same* wall.
Required by (a)'s answer -- `u` and `v` are two fields and a wall gives
them different numbers -- and the first real consumer of the limitation
TASK-040 recorded ("does not yet express 'field A is 300K at this wall,
field B is 0 at the same wall'").

*Acceptance criteria:*
- Two fields transported in one run, with different prescribed values at
  the same named boundary, each see their own -- checked in what the
  interior scheme computes at that boundary face, not only in what
  `evaluate()` returns (the TASK-028 rule, restated because it is the
  one that catches wiring errors).
- A velocity component's wall value is not read from the field
  `scalar_value` that a transported scalar uses, and vice versa,
  demonstrated by changing one and observing the other's flux is
  unchanged.
- Whatever mechanism this introduces is not velocity-specific: it is
  exercised by two *scalars* with different wall values, not only by a
  velocity pair (Criterion 1's "applies to any field" clause, and the
  thing that makes Stage 6's four fields cheap).

#### TASK-031d -- Velocity advanced by `step`

The wiring: `step` advances velocity's components alongside any scalar,
through the same schemes, with no branch that knows which fields are
whose.

*Acceptance criteria:*
- Velocity is advanced by the same `step` call, over the same timestep,
  that advances a scalar -- and a run carrying both advances both.
- **The scalar's own result is identical whether the velocity carrying
  it was solved or prescribed** (Criterion 1's executable form of "no
  engine change"): capture a solved velocity field, re-run the scalar
  against that same field supplied the way Stage 4 supplies one, and
  compare to floating-point tolerance.
- The orchestrator module's source contains no `"velocity"` string
  literal, no `VectorField` `isinstance` check, and no hardcoded
  component-name pair, asserted the way `tests/unit/test_simulation.py`
  already asserts the absence of `is_boundary_face` -- Criterion 1's
  structural clause, using the mechanism Stage 4 established rather than
  a new one.
- Velocity advected by itself reproduces a hand-derived result on a
  small non-square mesh with non-unit spacing -- self-advection is the
  one nonlinearity in the momentum equation, and the case a scalar
  transported by a *prescribed* velocity never exercises. Hand-derived
  means derived by hand: `docs/practices.md`'s standing rule, and the
  only check here that would catch a sign error.
- A velocity field whose component count disagrees with the mesh's
  dimensionality is rejected with the existing named error
  (`IncompatibleVelocityFieldError`), exercised against this task's own
  new path rather than assumed inherited (Criterion 6).

### Artifacts Produced

- `tests/features/velocity_field_support.feature` -- this task's
  Acceptance Criteria, per
  `adr/ADR-007-executable-acceptance-criteria.md`. One feature file with
  its scenarios grouped by subtask, not four files: the subtasks are one
  session's work and one task's claim, and `make check-scenarios` cares
  that every scenario runs, not how many files they live in.
  `tests/unit/test_velocity_field_support.py` binds them, per
  `tests/unit/`'s own scope (isolated logic, no process boundary) --
  every scenario is checked against the engine mechanism directly, none
  needs a CLI subprocess.
- `src/pyflow/engine/vector_field.py` -- `VectorField.decompose`/
  `.assemble`/`.component_name` (subtask a), plus
  `IncompatibleVelocityFieldError`/`ComponentCountMismatchError`/
  `ComponentMeshMismatchError` (moved and new, above). **This is where
  the component-to-`VectorField` assembly helper landed** -- the
  previously-open question resolved in favour of `vector_field.py` over
  `simulation.py`, since `decompose`/`assemble` are properties of a
  `VectorField`'s own shape, not of the orchestration loop.
- `src/pyflow/engine/numerics/boundary_condition.py` -- `Dirichlet
  BoundaryCondition`/`NeumannBoundaryCondition` gain an `overrides:
  Mapping[str, float]` constructor parameter, dispatched by `field.name`
  at `evaluate()` time (subtask c). Every existing call site passing
  only a value is unaffected.
- `src/pyflow/engine/numerics/diffusion.py` -- `CentralDifferenceDiffusion`
  gains a `coefficient_overrides: Mapping[str, float]` constructor
  parameter, the same per-field-name-dispatch shape (subtask b).
- `src/pyflow/engine/numerics/assembly.py` -- `assemble_numerics` gains
  a `coefficient_overrides` parameter, threaded to the diffusion factory
  via a new `_resolve_with_four_arguments`; `register_diffusion_scheme`'s
  factory type widens to match. Stays field-name-agnostic itself --
  which names get an override is decided by whoever calls it.
- `src/pyflow/bootstrap.py` -- `_add_passive_scalar_transport` decomposes/
  reassembles velocity around each `step` call when `velocity_solved` is
  set (subtask d, see this task's own Status note above for the one
  scope limit), and threads the viscosity override into
  `assemble_numerics`.
- `src/pyflow/configuration/schema.py` -- `SimulationConfig.
  velocity_solved: bool` (the solved-vs-prescribed control), and
  `BoundaryFaceConfig.field_values`/`field_gradients: dict[str, float]`
  (subtask c's per-field boundary overrides). **Not the `fluid:` section
  itself, which is TASK-041's.**
- `tools/generators/generate_config_template.py` -- comment entries for
  the three fields above, which `make check-config-template` gates.

### Acceptance Criteria

`tests/features/velocity_field_support.feature` is the criteria, not
restated here as prose: the four subtasks' own criteria above are what
it covers, and they are written where the work is rather than gathered
into a second list that would drift from them.

**Two obligations belong to the task as a whole rather than to any
subtask**, and are the reason this section still exists:
- Every configuration field this task adds rejects bad input with a
  named error, the same shape every other config section's tests already
  take (`tests/unit/test_configuration.py`), and appears in the
  regenerated template with a comment saying what counts as valid
  (Criterion 12).
- The four subtasks' scenarios share the fixtures and building blocks in
  `tests/unit/_numerics.py` rather than each re-deriving a mesh and a
  boundary condition (Criterion 7) -- four subtasks in one module is the
  easiest place in this stage to accumulate exactly the duplication
  Stage 4's exit audit had to undo.

### Discharges

Criterion 1, entirely (subtasks a, c and d between them). Criterion 12,
its solved-vs-prescribed share -- **its viscosity and migration share
is TASK-041's**. Criterion 6 and Criterion 7, its own share.

---

## TASK-032

Pressure Field

**Status: Done, 2026-08-29, Stage 5's third task.** `PISO` (TASK-027,
Stage 4) already performs the solve this task's own criteria describe;
this task adds no new pressure-solving mechanism, only the properties
Stage 4's own criteria never had cause to check and the one genuinely
missing API-level guard:

- **The local design question resolved: pressure gets a type of its
  own, `PressureField(ScalarField)`** (`src/pyflow/engine/scalar_field.py`)
  -- a marker subclass with no behaviour of its own, `PISO.correct` now
  constructs one instead of a plain `ScalarField`. `simulation.step`
  gains a real `isinstance` check, raising `PressureFieldTransportError`
  (a new class, `simulation.py`) if `fields` contains one -- the "stated
  at the API level" shape Criterion 2 asks for, checked directly against
  the object handed in rather than by name.
- **`PressureField` lives in `scalar_field.py`, not
  `engine/numerics/pressure_coupling.py`** (its one real producer) --
  `simulation.py` needs to import it and cannot import from
  `pressure_coupling.py` without a circular import (that module already
  imports `accumulate_flux_to_cells` from `simulation.py`). The same
  circular-import reasoning TASK-031a's own `IncompatibleVelocityFieldError`
  move used.
- **`PressureCoupling.correct`'s own abstract signature is unchanged**
  (`-> tuple[VectorField, ScalarField]`) -- no Stage 3 interface change;
  a `PressureField` instance already satisfies it (valid covariant
  return narrowing under `mypy --strict`).

**Intent:** pressure is *not* transported -- it is solved for, from the
incompressibility constraint. A criterion that treats it as another
advected scalar has misunderstood the task. See
`docs/handbook/numerical-methods/pressure-velocity-coupling.md`.

### Purpose

Give the engine a real pressure field: one produced by a solve against
the current velocity field, with its null space removed explicitly, and
one that no part of the transport path advances.

### Dependencies

TASK-031 (a transported velocity field to solve against), TASK-026
(`ConjugateGradientSolver`), TASK-027 (`PISO`, `GreenGaussGradient`,
`GreenGaussDivergence`, and the compact symmetric Laplacian that task
already builds the Poisson matrix from).

### Design question, resolved

**Six above, answered 2026-08-28: no `SourceTerm` implementation.** The
pressure gradient reaches velocity as the projection correction, not as
a source term, so this task adds no concrete `SourceTerm` -- and the
reason is already recorded in `src/pyflow/engine/numerics/source.py`'s
own module docstring, written when the decision was taken rather than
left as an obligation for this task to remember. Nothing to decide here;
the note exists so that a reader who wonders why the interface is still
empty finds an answer next to it.

### Artifacts Produced

- `tests/features/pressure_field.feature` -- this task's Acceptance
  Criteria. `tests/unit/test_pressure_field.py` binds them, per
  `tests/unit/`'s own scope (isolated logic, no process boundary) --
  every scenario is checked against the real `PISO`/`GreenGaussGradient`
  machinery directly, none needs a CLI subprocess.
- `src/pyflow/engine/scalar_field.py` -- `PressureField(ScalarField)`,
  resolving this task's one local design question (a type of its own,
  not a plain `ScalarField` the coupling owns).
- `src/pyflow/engine/simulation.py` -- `step` gains an `isinstance`
  guard against `PressureField`, raising a new
  `PressureFieldTransportError`.
- `src/pyflow/engine/numerics/pressure_coupling.py` -- `PISO.correct`
  constructs a `PressureField` instead of a plain `ScalarField`; no
  signature change.

### Acceptance Criteria

`tests/features/pressure_field.feature` is the criteria. Written to
cover, at minimum:

- The divergence-free/divergent pair Criterion 2 requires: constant
  pressure to solver tolerance for an already-divergence-free velocity
  field, non-constant for one with a known nonzero divergence. Both
  scenarios, since either alone is passed by an implementation that
  always returns the same answer.
- Adding a constant to the pressure field leaves the corrected velocity
  unchanged to floating-point tolerance -- the null-space property made
  observable, and the check that says which remedy was chosen was
  actually applied.
- Pressure is not among the fields `step` advances, and a configuration
  that tries to transport it is rejected with a named error
  (Criterion 2's first bullet, and this task's share of Criterion 6).
- A boundary configuration violating the zero-net-flux compatibility
  condition fails at load time, not inside the solver -- checked against
  Stage 3's existing `_validate_boundary_conditions_jointly`, which is
  where that rejection already lives and is deliberately not
  reimplemented here.

### Discharges

Criterion 2, entirely. Criterion 6 and Criterion 7, its own share.

---

## TASK-033

Pressure Correction Loop

**Status: Done, 2026-08-29, Stage 5's fourth task.** `PISO`'s single
correction pass (TASK-027) becomes a genuine corrector loop: each pass
measures the maximum cell divergence, records it, and either returns (at
or below `numerics.pressure_correction_tolerance`) or solves another
pass, up to `numerics.pressure_correction_max_iterations` before raising
rather than returning a best-effort result.

- **Design question three, resolved by numerical prototyping before any
  test or implementation code was written, the same sequence TASK-027
  used:** what carries the momentum-equation coefficients Rhie-Chow
  needs, given PyFlow's momentum predictor is fully explicit (RK4, no
  implicit assembly to draw a coefficient from)? Answer: `a_P = V/dt` --
  the unsteady term is the *only* contribution to `a_P` for this
  architecture, and PyFlow's uniform cell volume makes `V/a_P = dt` one
  constant for the whole mesh, not a per-cell field. No new
  momentum-coefficient machinery, and no widened `PressureCoupling.
  correct` -- `tolerance`/`max_iterations` are bound at `PISO`'s own
  construction, the same "strategy owns its own tunables" shape
  `ConjugateGradientSolver` already established. No ADR: the abstract
  interface is byte-for-byte unchanged.
- **The second half of the answer, and the one TASK-027 actually got
  wrong, not merely incomplete:** pairing the `a_P = V/dt` correction
  with the *same* compact Laplacian the Poisson matrix is built from
  (`_rhie_chow_divergence`, reusing `_poisson_matrix`'s own
  `CentralDifferenceDiffusion`-based operator) is what restores the
  discrete adjoint property -- not the composed `GreenGaussGradient`/
  `GreenGaussDivergence` pair TASK-027 tried and measured stalling at a
  few percent reduction per pass. Verified numerically before being
  trusted: a manufactured provisional velocity field (both a linear and
  a nonlinear fixture, disposable prototype scripts, not committed)
  converges to floating-point-exact zero divergence in a *single*
  corrector pass once the operators match. This is also why the
  feature file's second scenario needs a deliberately handicapped
  `_HalvingSolver` test double rather than a real linear solver: on
  PyFlow's uniform MVP mesh, the real corrector loop converges in one or
  two passes, too fast to demonstrate genuine multi-pass behaviour on
  its own -- the double halves the exact correction every pass instead,
  producing an exactly-verifiable geometric decay (confirmed to hold to
  ~13 significant figures across many passes before being written into
  the test) that forces and proves multiple genuine iterations.
- **`DivergenceDidNotConvergeError` is new, and distinct from
  `PressureSolveDidNotConvergeError`** (TASK-027): the former is the
  *outer* corrector loop exhausting its iteration limit while divergence
  never reaches tolerance (the inner solves all report success); the
  latter is one pass's own inner linear solve failing to converge. A
  loop using a solver that always reports `converged=True` but never
  actually reduces divergence exercises the first and never the second
  -- the third scenario's own fixture.
- **Couette flow's exact linear profile (Stage 5 Completion Criterion 5)
  is not a scenario in this task's own feature file, deliberately** --
  the feature file's own header comment records why: this task lays the
  corrector-loop groundwork the scenario needs (a genuinely convergent
  `PISO`), not the demonstration itself, which needs a fully assembled
  timestep only TASK-034 has. The Discharges line below still reads
  "jointly with TASK-034" for that reason, not as a claim that a partial
  scenario exists here.

**Intent:** the loop's claim is that divergence **decreases
monotonically with each corrector iteration** and reaches the configured
tolerance -- measured across iterations, not asserted at the end. A loop
that reaches tolerance by luck on iteration one and diverges thereafter
passes an end-state check.

**This is also where Stage 4 Completion Criterion 4's Pressure-Velocity
Coupling bullet's stronger claim actually gets discharged** (see that
bullet, and TASK-027's own Context below it) -- TASK-027 built a real,
single-pass `PressureCoupling` strategy, checked in isolation against a
manufactured system, because the collocated mesh's pressure-velocity
decoupling can't be suppressed under repeated correction without
Rhie-Chow interpolation, which needs momentum-equation coefficients only
TASK-031 (Velocity Field Support)/TASK-032 (Pressure Field) give this
engine. This task is where a real, wired velocity/pressure field
finally exists to iterate against, and where the monotonic-convergence
claim TASK-027 explicitly deferred is meant to be checked.

### Purpose

Turn one correction pass into a corrector *loop* that converges: the
"two or more pressure-correction passes within a single timestep" PISO
is defined by (`docs/handbook/numerical-methods/pressure-velocity-
coupling.md`), with the momentum coupling that makes repeated passes
actually reduce divergence rather than stall.

### Dependencies

TASK-031, TASK-032, and TASK-027's own finding -- which is a dependency
in the literal sense: this task starts from a measured negative result
about what does not work, not from a blank page.

### Open design questions

**Three above -- the only one of this stage's seven left open when the
other six were decided, and this task owned it. Resolved 2026-08-29:
outer-loop state the strategy owns (`a_P = V/dt`, bound at `PISO`'s own
construction), not a widened `PressureCoupling.correct` or a momentum
operator handed in separately.** Found by numerical prototyping before
writing this task's feature file, the same sequence TASK-027 used
(several disposable prototype scripts, then a scoping decision, then the
tests) -- see this task's own Status paragraph above for the finding
itself. It was left open deliberately when the other six were decided,
because TASK-027 already demonstrated what deciding this one without
measurements costs.

**Five above is no longer open, and that is what makes three
measurable.** The correction sits outside the integrator, once per
timestep (resolved 2026-08-28, maintainer's call): RK4 advances momentum
to a provisional velocity with no pressure term, then this task's
corrector loop projects. So "within a single timestep" in the
monotonic-convergence claim above means *within that one projection's
corrector passes* -- an unambiguous sequence to record and assert on,
which is exactly what it was not while the arrangement was undecided.

### Artifacts Produced

- `tests/features/pressure_correction_loop.feature` -- this task's
  Acceptance Criteria. `tests/unit/test_pressure_correction_loop.py`
  binds it, per `tests/unit/`'s own scope -- every scenario is checked
  against the real `PISO` directly, no CLI subprocess.
- `src/pyflow/configuration/schema.py` -- `NumericsConfig.
  pressure_correction_tolerance`/`pressure_correction_max_iterations`,
  the outer corrector loop's own tunables (Criterion 12's own share),
  distinct from `linear_solver_tolerance`/`linear_solver_max_iterations`,
  which govern each pass's inner solve.
- `src/pyflow/engine/numerics/pressure_coupling.py` --
  `DivergenceDidNotConvergeError`, and `PISO.last_divergence_history`,
  the recorded per-pass sequence the feature file's own scenarios assert
  against directly.
- **No ADR**: design question three resolved to outer-loop state bound at
  `PISO`'s own construction, not a Stage 3 interface widening --
  `PressureCoupling.correct`'s abstract signature is unchanged. The
  Artifacts bullet drafted for this task anticipated needing one; it
  didn't, the same way TASK-032's own local design question needed none
  either.

### Acceptance Criteria

`tests/features/pressure_correction_loop.feature` is the criteria.
Covers:

- The recorded sequence of per-iteration maximum divergence magnitudes
  within one timestep is non-increasing at every element, and its last
  element is at or below the configured tolerance -- the sequence
  asserted, not just its last value.
- A solver that only partially corrects divergence each pass still takes
  multiple genuine (strictly decreasing) passes to converge -- the
  scenario a real solver's own fast convergence on PyFlow's uniform MVP
  mesh cannot demonstrate on its own; see the Status paragraph above for
  why a deterministic `_HalvingSolver` double is what exercises this.
- Exhausting the corrector iteration limit without reaching tolerance
  raises `DivergenceDidNotConvergeError` rather than returning a best
  effort, the same honesty `PressureSolveDidNotConvergeError` already
  applies to a single solve (Criterion 3's last bullet, and this task's
  share of Criterion 6) -- and is a genuinely different error, since the
  fixture's own inner solves all report success.
- `piso` is genuinely multi-pass, not renamed, per Criterion 3 -- visible
  in the scenario (a real solver converging over a recorded sequence),
  not only in the class's own docstring.
- **Couette flow's exact linear profile is deliberately not a scenario
  here** -- left to TASK-034 alone, which has the fully assembled
  timestep the comparison needs; see the Status paragraph above.

### Discharges

Criterion 3, entirely. Criterion 12, its corrector-tolerance and
iteration-limit share. Criterion 6 and Criterion 7, its own share.
Criterion 5's Couette bullet stays with TASK-034 alone -- not discharged
here, and the "jointly" phrasing this section originally carried is
corrected: this task supplies the corrector loop the comparison depends
on, not part of the scenario itself. **Stage 4 Completion Criterion 4's
Pressure-Velocity Coupling deferral, re-read at this task's close rather
than assumed discharged: confirmed genuinely resolved.** `icds.md`'s own
Pressure-Velocity Coupling entry is updated in the same change (its own
"is not, and does not claim to be, the full multi-pass Issa algorithm"
sentence no longer describes the shipped `PISO`) -- see that document for
the reading that replaces it.

---

## TASK-034

Navier-Stokes Timestep

**Status: Done, 2026-08-29, Stage 5's fifth and last task in build
order -- this defines the MVP.** `pyflow.engine.simulation.
navier_stokes_step` assembles TASK-031/032/033 into one real
predictor/corrector/corrected-state timestep, reached only through
whichever `PressureCoupling`/`LinearSolver` `assemble_numerics`
resolved (Criterion 13's own substitution check passes: a registered
test double is demonstrably what the timestep calls, not a hardcoded
`PISO`). Eleven scenarios in `tests/features/navier_stokes_timestep.feature`,
bound by `tests/unit/test_navier_stokes_timestep.py`, all real-engine
(no config file, no CLI run -- this is the mechanism, not a demo):

- The predictor/corrector/corrected sequence, each part observable via
  `NavierStokesStepResult`'s own three fields.
- Both null tests: a uniform, non-axis-aligned velocity field on a
  fully periodic, zero-viscosity domain stays exactly the same value and
  at solver-tolerance divergence over 20 real steps; fluid initially at
  rest in a closed no-slip domain stays at rest to floating-point
  tolerance over the same 20 steps.
- Determinism: two independent runs from the same initial state produce
  bit-identical corrected velocity and pressure.
- The ADR-003 substitution check: a `PressureCoupling` test double
  registered under its own name and selected by configuration is
  demonstrably what `navier_stokes_step` calls.
- Couette flow: an impulsively-started channel (periodic in the flow
  direction, no-slip walls, one stationary and one moving tangentially)
  reaches a measured steady state (residual-based, not a step count)
  whose streamwise profile matches the exact linear solution to
  `abs=1e-6`, with the wall-normal component staying zero throughout.
- **The Ghia cavity comparison -- this project's most computationally
  expensive test, deliberately.** Three real runs (resolutions 9, 13,
  17, chosen odd so the centreline always lands exactly on a cell-centre
  column/row) to a measured steady state at Re = 100: the RMS error
  against Ghia, Ghia & Shin (1982)'s own Table I (`tests/fixtures/
  ghia_1982_re100.py`, cross-checked against two independent public
  reproductions of the paper's own table, not transcribed from memory)
  decreases strictly across all three resolutions; the finest
  resolution's own primary vortex (found by minimum velocity magnitude
  in a central sub-region, avoiding the near-wall low-velocity artefact
  a naive whole-domain search picks up) lands within 0.1 of Ghia's own
  reference point in unit-cavity coordinates; both downstream secondary
  corner vortices are detected via opposite-sign discrete vorticity in
  each bottom corner's own sub-region. **Confirmed passing on a real run
  before this status was written**: 1 passed in 683.82s (11m24s).
- The emergent-phenomenon pair, **Taylor-Green vortex decay, chosen over
  Kelvin-Helmholtz roll-up by measurement**: at a viscosity where
  physical diffusion dominates, the measured decay rate matched the
  exact `2 * wavenumber**2 * viscosity` rate to within ~0.3%; at a 100x
  smaller viscosity (mesh and advection scheme held fixed), the measured
  rate was off by a factor of roughly 3.8 -- upwind's own numerical
  diffusion dominating once the physical rate no longer does, exactly
  the failure this bullet exists to catch.
- Kinetic-energy conservation: zero increase, to floating-point
  precision, over 20 real steps on a divergent-initial-condition,
  near-zero-viscosity, closed no-slip fixture -- checked step by step,
  not net over the run.

Two golden demos, each its own config file, feature file and
CLI-subprocess-tested regression suite: **Lid-Driven Cavity**
(`examples/golden-demos/lid_driven_cavity.yaml`, `tests/golden/
test_lid_driven_cavity.py`) -- the MVP's own golden demo, the first
velocity field PyFlow has ever rendered that was *solved*, live, via
`bootstrap.py`'s new `_add_solved_velocity_rendering` and a real
`navier_stokes_step` every frame; and **Heat Diffusion**
(`examples/golden-demos/heat_diffusion.yaml`, `tests/golden/
test_heat_diffusion.py`) -- a single sinusoidal mode
(`SimulationConfig.scalar_pattern`'s new `"sinusoidal_mode"` value) on a
fully periodic domain, decaying at the exact analytic rate to within
~0.6% on a real measured run.

**Three real findings, made and closed within this task rather than
discovered afterward:**

1. **`GreenGaussGradient`/`GreenGaussDivergence`/`PISO` had no periodic-
   boundary support at all** -- found while building the periodic null
   test, which cannot reach `PISO` without it (even *measuring* an
   already divergence-free field's divergence raised
   `UnconfiguredBoundaryFaceError` unconditionally for any periodic
   face). Both operators gained a `periodic_pairs` constructor
   parameter, the same shape `CentralDifferenceDiffusion` already had
   since TASK-030; `PISO` gained a fifth, defaulted parameter threading
   it to `_diffusion` (which had been silently passed a hardcoded `{}`
   regardless of what `PISO` itself was told), `_gradient`,
   `_divergence`, and its own `_rhie_chow_divergence` correction loop.
   Verified directly: a uniform field measures exactly `0.0` divergence
   through this path; a hand-assigned non-uniform field gives a real
   nonzero value matching a hand-derivation built directly from
   `mesh.wrapped_neighbour_cell`. No ADR -- the same registry-level
   widening, no-interface-change shape TASK-030's own periodic addition
   used.
2. **`PISO._poisson_matrix` was rebuilt from scratch every single
   timestep**, even though it depends only on the fixed mesh and
   pressure boundary treatment -- found while timing the cavity
   validation's own first real run (n=8: 285ms/step; n=16: 3607ms/step,
   dominated 70-92% by matrix construction). Caching it per `PISO`
   instance (by mesh identity) cut those to 81ms and 469ms respectively
   -- a 3.5x and 7.7x reduction -- and is what made the three-resolution
   comparison fit inside an 11-minute test rather than an estimated
   multi-hour one. `tests/unit/test_piso_pressure_coupling.py` gained
   two new plain (non-BDD) unit tests proving the cache is reused across
   calls on the same mesh and safely recomputed for a different one.
3. **`velocity_tangential` (Stage 5's own design question two,
   resolved 2026-08-28) was never built -- `BoundaryFaceConfig.
   field_values`/`field_gradients` (TASK-031c, landed the very next day)
   already supply the exact mechanism that question needed.** A
   per-field-name override at one wall (`velocity.0 = U, velocity.1 = 0`
   at a moving lid) is already fully general, needs no new config field,
   and no per-wall tangential-axis wiring inside `assembly.py` (which
   stays field-name-agnostic by design). Recorded here explicitly, per
   root `CLAUDE.md`'s Validation section, rather than silently building
   something different from what was decided without saying so.

`make ci` green (see this session's own run for the final test/coverage
figures, folded into the count paragraph above Stage 0); `mypy --strict`
clean; `ruff` clean.

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

**Documentation obligation, not an Acceptance Criterion of this task's
own:** `docs/architecture/sequences.md` Section 3 quotes this paragraph's
checkpoint-based design directly as its "Planned: checkpointing"
placeholder, anchored to this task. Once checkpointing is actually built
here, replace that placeholder with the real, built sequence in the same
change -- that document should not still say "not built yet, and not an
open design question either" once it is built.

**Intent:** this task's acceptance criteria already include emergent
phenomena -- "does the right instability emerge under the right
configuration" (this document's own "Stages and Capability Levels" note,
2026-08-20; `docs/planning/backlog.md`, "physical correctness
validation"). The qualifier to hold on to: **the right phenomenon under
the right configuration**, which means a configuration under which it
should *not* emerge must be tested too. An instability that appears
regardless of parameters is not the instability.

### Purpose

Assemble the first three tasks into one incompressible Navier-Stokes
timestep -- predictor, corrector loop, corrected state -- and then use
it: the demonstrations, the quantitative validation against published
and analytic answers, and the stage-level exit obligations this stage's
last task owns.

### Dependencies

TASK-031, TASK-032, TASK-033; TASK-017 (field rendering, for the demos'
own visual output); TASK-030's own demo wiring
(`src/pyflow/bootstrap.py`'s live per-frame stepping), which is the
mechanism a live demo already uses and this one extends rather than
replaces.

### Design questions: the shape is settled, two pieces land here

**Two above is answered, but resolved differently than drafted -- a
finding, recorded rather than silently substituted.** `velocity_tangential`
(2026-08-28) was Stage 5's own answer to "a lid-driven cavity's lid is
tangential", but `BoundaryFaceConfig.field_values`/`field_gradients`
(TASK-031c) landed the very next day, after that decision, and already
supply the exact general mechanism the question needed: a per-field-name
override at one wall (`velocity.0 = U, velocity.1 = 0` at the lid,
`VectorField.component_name`), with no new config field, no per-wall
tangential-axis wiring inside `assembly.py` (which stays field-name-
agnostic by design), and no new concept to document. A no-slip
*stationary* wall needs no override at all -- `scalar_value = 0.0`
already zeroes both components identically, since normal and tangential
are both zero there. `velocity_tangential` itself was never built.
`tests/unit/test_navier_stokes_timestep.py`'s own module docstring
records the same finding next to the code it governs.

**Four's timestep half, resolved**: `pyflow.engine.simulation.
stable_timestep(mesh, viscosity, velocity_scale, safety_factor=0.25)` --
`min(dx/velocity_scale, dx**2/viscosity) * safety_factor`, the tighter of
the CFL and diffusive stability limits this scheme combination (explicit
RK4, first-order upwind, central-difference diffusion) actually needs.
**`0.25` is measured, not derived**: a disposable prototype swept safety
factors across a mixed advection/diffusion regime, a diffusion-dominated
one, and an advection-dominated one; `0.3` was the largest factor that
stayed stable for 500 steps in every regime tried, `0.35` already blew
up in the mixed one, and `0.25` keeps real margin below that measured
edge. Used directly by every resolution's own dt in the Couette,
Taylor-Green and Ghia cavity scenarios below -- no hand-tuned per-
resolution timestep anywhere, so the cavity's own three-resolution
comparison is a genuine convergence study, not one measuring how well
each resolution's own dt was picked.

### Artifacts Produced

- `tests/features/navier_stokes_timestep.feature` -- this task's own
  Acceptance Criteria, eleven scenarios; bound by `tests/unit/
  test_navier_stokes_timestep.py`.
- `tests/features/lid_driven_cavity.feature` and `tests/features/
  heat_diffusion.feature` -- one `.feature` file per demo Criterion 8
  requires, the same pairing every golden demo already has; bound by
  `tests/golden/test_lid_driven_cavity.py`/`test_heat_diffusion.py`.
- `examples/golden-demos/lid_driven_cavity.yaml` and `examples/golden-demos/
  heat_diffusion.yaml`.
- `pyflow.engine.simulation.navier_stokes_step`/`NavierStokesStepResult`/
  `stable_timestep` -- the predictor/corrector/corrected-state assembly
  and its own timestep-derivation helper.
- `pyflow.bootstrap._add_solved_velocity_rendering` -- the velocity-only
  live rendering path `_add_passive_scalar_transport`'s own docstring
  named as this task's likely first consumer, now built.
- `SimulationConfig.scalar_pattern`'s new `"sinusoidal_mode"` value
  (`ScalarTransportPattern`), the Heat Diffusion demo's own initial
  condition.
- **`tests/fixtures/`, a new top-level test-data convention** (this
  repository had none) -- `ghia_1982_re100.py`, the committed Ghia,
  Ghia & Shin (1982) Table I reference data (u along the vertical
  centreline, v along the horizontal one, the primary vortex centre),
  cited and cross-checked against two independent public reproductions
  of the paper's own table before being trusted (this environment has no
  direct access to the original print journal -- the fixture's own
  docstring states that limit explicitly rather than silently). Recorded
  in `docs/repository-manifest.md` and this directory's own new
  `CLAUDE.md`, per the Blast Radius rule.
- **A real periodic-boundary extension to `GreenGaussGradient`/
  `GreenGaussDivergence`/`PISO`**, not anticipated when this task was
  drafted -- found necessary to make the periodic null test reachable at
  all; see this task's own Design decisions below.
- **A `PISO._poisson_matrix` caching fix**, found necessary while
  measuring the Ghia cavity validation's own real runtime; see this
  task's own Design decisions below.
- Entries in `docs/implementation/golden-demos.md` for each demo built,
  written when it exists rather than ahead of it, per that document's own
  rule.

### Acceptance Criteria

`tests/features/navier_stokes_timestep.feature`, plus each demo's own
feature file, are the criteria. Written to cover, at minimum:

- The predictor/corrector/corrected sequence, each part observable --
  not only the end state (Criterion 4).
- Both null tests, per Criterion 4: uniform flow on a fully periodic
  domain translates unchanged and stays divergence-free; fluid at rest
  in a closed, no-slip domain stays at rest. Not one combined scenario
  -- a uniform flow cannot exist inside a closed domain at all.
- Determinism: the same configuration run twice produces identical
  state.
- Couette flow against its exact linear profile, at solver tolerance
  rather than a loose one -- this task's own scenario alone (TASK-033
  deliberately left it here, since it needs a fully assembled timestep;
  see that task's own Status paragraph), and see Criterion 5's own note
  on why the nonlinear term vanishing makes that reachable.
- Lid-driven cavity against Ghia, Ghia & Shin (1982) at Re = 100:
  monotonically decreasing error across at least three mesh resolutions,
  plus the qualitative structure at the finest -- **not** a fixed
  percentage, per Criterion 5's own bullet and the 2026-08-28 decision
  recorded there. The reference values come from a committed fixture
  citing the paper's own table, and steadiness is a measured residual
  rather than a step count.
- The emergent-phenomenon pair: the instability under a configuration
  that should produce it, and its absence under one that should not --
  with the candidate chosen by measurement, per Criterion 5's note on
  what the MVP's numerical diffusion may suppress. **Taylor-Green vortex
  decay, not Kelvin-Helmholtz roll-up -- chosen by measurement, per
  Criterion 5's own instruction, not by preference.** Reuses this task's
  own periodic-domain infrastructure directly and has a closed-form decay
  rate (`2 * wavenumber**2 * viscosity`) to measure against rather than
  needing a roll-up detector. Measured directly before being trusted: at
  a viscosity where physical diffusion dominates, the measured rate
  agreed with the exact rate to within ~0.3%; at a 100x smaller
  viscosity (mesh and advection scheme held fixed), the measured rate
  was off by a factor of roughly 3.8 -- upwind's own numerical diffusion
  dominating, exactly the failure mode this bullet exists to catch.
- No single step increases total kinetic energy for an inviscid,
  unforced, closed-domain flow -- step by step, not net over the run,
  since upwind's own dissipation makes the net check pass regardless.
  Measured directly (not merely a priori true even for a correct
  implementation): zero increase, to floating-point precision, over 20
  real steps on a divergent-initial-condition fixture at near-zero
  viscosity.

### Discharges

**Amended 2026-08-29 by the Stage 5 exit audit; this section claimed
more than the task delivered.** As written it read "Criteria 4, 8, 9,
10, 11 and 13, entirely" plus "Criterion 5, all bullets". Four of those
were short, and the stage's own status section above records each:
Criterion 13's `LinearSolver` substitution check was never built (only
the `PressureCoupling` one); Criterion 5's stated-and-defended absolute
tolerance was never written; Criterion 10 left five stale claims in
files this task did not open; Criterion 9 was recorded against a local
`make ci` rather than a real two-platform run. Criterion 6's second
named rejection surface was owed by no task and built by none. All are
now discharged, by the audit rather than by this task, which is the
distinction this amendment exists to preserve.

Criteria 4, 8 and 11, entirely. Criteria 5, 9, 10 and 13, entirely **as
completed by that audit**. Criterion 5's bullets are otherwise all this
task's, including the Couette one entirely -- TASK-033 supplies the
corrector loop it depends on but does not itself scenario-test it (see
that task's own Discharges). Criterion 12, its tangential-boundary share --
**discharged by the `field_values` finding above, not by building
`velocity_tangential`** -- and its run-length/steadiness share:
**deliberately not a new config field.** The Ghia cavity scenario's own
residual-based steadiness detection runs directly against the engine
(`AssembledNumerics` constructed by hand, not through `PyFlowConfig` at
all), so there is no live-run config surface for it to occupy; the two
golden demos themselves never claim to reach steady state (a live
`pyflow run` is stopped by a user, or by `--max-frames`, an existing CLI
flag, not a new config field), so neither needs one either. Criterion 6
and Criterion 7, its own share.

Golden Demo

Lid-driven cavity.

This defines the MVP of PyFlow.

---

# Stage 6 — Additional Physical Fields

Goal

Demonstrate field-centric architecture.

### Completion Criteria

Written 2026-08-29, before this stage's first task, per `docs/practices.md`'s
"A stage gets completion criteria before its first task" -- **the fifth
stage to satisfy that rule**, after Stages 2, 3, 4 and 5, and the first
drafted the same day the previous stage closed rather than after a gap.

**The count is five, not seven, and the difference is worth one
sentence** because the obvious number is wrong in a way that would
propagate. Six stages carried completion criteria before this one, but
two of them did not satisfy this rule: Stage 0's predate it, and Stage
1's own section says "Written 2026-08-21, after the fact" -- that
retrospective audit, which found five of eight criteria unmet, is
*why* the rule exists. A first draft of this paragraph said "the
seventh stage in a row", copying the shape of the claim Stage 5's own
commit message made ("the sixth stage in a row") without opening
Stage 1's section to check it. Counting stages-with-criteria and
counting stages-that-followed-the-rule are different counts, and only
the second one means anything here.

Criteria are about the stage's goal -- *demonstrate field-centric
architecture* -- not the union of this stage's tasks' own Acceptance
Criteria. Every qualifying clause is its own bullet
(`docs/practices.md`, "The intent lives in the qualifier") and every
criterion names the task that discharges it (the discharge map below),
following the three stages before this one.

**Neither of Stage 3's two exemptions extends here**, same as Stages 4
and 5: the physical-correctness extension applies in full, and
executable Gherkin criteria apply in full
(`adr/ADR-007-executable-acceptance-criteria.md`) -- every task below
either transports a physical quantity or configures one that is.

**This stage's goal is a claim about the repository, not about
temperature.** The intent recorded on 2026-08-22 (below) already said
the measure of TASK-035's success "is how little else changes", and that
this stage's tasks "must add no new machinery". Those two sentences
*are* the goal; drafting these criteria turned them into things a run
can fail. Doing that rather than assuming they were already precise
found two facts that make the naive reading of both sentences false
today, and both are recorded as design questions below rather than
smoothed over. **A third arrived a day later, while the task entries
were being written, and it invalidated a criterion rather than the
goal** -- design question six, which is why Criterion 2's headline no
longer reads the way it was first drafted.

**PyFlow cannot express a second transported field at all.**
`SimulationConfig` (`src/pyflow/configuration/schema.py`) seeds exactly
one scalar, through one `scalar_pattern` enum, and `bootstrap.py` names
it `"tracer"` in source. There is no configuration surface that declares
a field, so "adding a field changes nothing else" cannot be true or
false yet -- there is nothing to add a field *with*. Verified by reading
both modules rather than assumed, and the reading cuts the other way
too: the machinery that makes per-field *coefficients* work
(`CentralDifferenceDiffusion`'s `coefficient_overrides`,
`DirichletBoundaryCondition.overrides`, both TASK-031) already exists and
is genuinely field-name-keyed, so what is missing is the declaration
surface above it and nothing below it. Design question one.

**Buoyancy is not machinery-free, and it is this stage's own headline
demo.** `simulation.step`'s derivative is exactly
`accumulate_flux_to_cells(mesh, diffusion.flux(field) -
advection.flux(field))` -- there is no source contribution in it, no
`SourceTerm` implementation anywhere, no registry entry for one, and no
configuration field naming one. A Boussinesq body force is a source
term (`docs/handbook/physics/buoyancy.md`), so TASK-035 cannot both
couple temperature to momentum and add no engine code. Stage 5 saw this
coming and wrote it down -- `src/pyflow/engine/numerics/source.py`'s own
docstring names TASK-035 as the interface's "natural first
implementation" -- which makes it a predicted arrival rather than a
surprise, but not a free one. Design question two.

1. **A transported field is added by configuration, not by code.** The
   stage's goal, stated as the thing that would falsify it. A run must
   be able to transport several named fields at once, each declared in
   the configuration file, with no source change per field.
   - **At least four named fields transport in one run**, in a single
     configuration, alongside a solved velocity -- not four separate
     one-field runs, which would never exercise the sharing that makes
     this claim interesting.
   - **A field is a name and its coefficients, not a type.** No
     `TemperatureField`, `DensityField`, `HumidityField` or
     `TracerField` class. `PressureField` is the one precedent for a
     field subclass and it earned that by needing a *guard*
     (`PressureFieldTransportError`); a transported scalar needs no
     guard, and giving each phenomenon a class is precisely the
     special-casing this stage exists to show is unnecessary.
   - **Checked structurally, by the mechanism Stages 4 and 5 both used
     for exactly this shape of claim**: no `"temperature"`, `"density"`,
     `"humidity"` or `"tracer"` string literal anywhere in
     `inspect.getsource(simulation)`, the same assertion
     `tests/features/velocity_field_support.feature` already makes for
     `"velocity"` and `is_boundary_face`. A stage that demonstrates
     field-centricity by hardcoding four field names in the orchestrator
     has demonstrated the opposite.
   - **The measurable half, and what this criterion is really about:
     the last two tasks add zero lines under `src/pyflow/`.** TASK-037
     (Humidity) and TASK-038 (Passive Tracers) are transported scalars
     with their own diffusivity and nothing else; if the declaration
     surface is right, each is a configuration file and a feature file.
     A nonzero count is not automatically a failure -- it is a
     *finding*, reported with what the lines were for, because "how
     little else changes" is only a demonstration if somebody counts.
     Measured with `git diff --stat` for `src/pyflow/` across each of
     those two tasks' branches, so the verdict is a number somebody
     reproduces rather than a judgement somebody makes.
   - **TASK-042's own line count is deliberately not part of that
     measurement, and the reason has to be stated or this criterion
     reads as rigged.** The claim this stage makes is about the
     *marginal* cost of an additional field, not the one-off cost of
     being able to declare one at all -- which is why the measurement
     sits on the last two tasks and not the first. What stops that being
     a loophole is that `src/pyflow/configuration/schema.py` is inside
     the measured tree: a declaration surface that has to grow once per
     field shows up as a nonzero count against TASK-037 and TASK-038
     exactly as an engine change would. **The loophole this leaves open,
     stated rather than left for the exit audit to find: TASK-042 could
     satisfy the letter of this by anticipating all four fields
     specifically.** The guard is its own intent line -- that
     TASK-037 and TASK-038, neither designed in detail when TASK-042 is
     built, need nothing TASK-035 did not already need -- and the exit
     audit reads `schema.py`'s field list for phenomenon-specific names
     rather than only counting lines.
2. **No new interface, and exactly one existing interface's signature
   changes -- named here in advance.**
   `adr/ADR-003-modular-numerical-strategies.md` names six swappable
   components; this stage adds a seventh to none of them, and P-016
   forbids inventing one for a need this stage does not have.
   - **`SourceTerm` gets its first concrete implementation, and that is
     the interface arriving at the consumer Stage 5 predicted for it,
     not a new component.**
   - **Its signature widens, once, to `source(self, field: Field, state:
     Mapping[str, Field]) -> torch.Tensor`** (`src/pyflow/engine/
     numerics/source.py`). **This criterion read "no existing
     interface's signature changes" until 2026-08-30 and it was
     unbuildable as written** -- buoyancy acts on `velocity.1` and is
     computed from the *temperature* field, which `source(field)` never
     receives, so the criterion forbade the only thing that would make
     TASK-035 work. Found by tracing the call through
     `simulation.step`'s own `derivative` rather than by reading the
     interface, and put to the maintainer as design question six rather
     than resolved by the reading that was easiest to implement. **The
     criterion's own escape clause is what was used**: it said a
     signature change "is a design session, not an edit", and this is
     that design session.
   - **One change, and the exit audit reads the diff against that
     number.** The permitted widening is exactly the one above; any
     second interface change this stage makes is a Criterion 2 failure
     whatever its justification, because the value of naming one in
     advance is entirely in the count.
   - **`simulation.step`'s derivative gains the source contribution,
     and that change is bounded and stated.** The engine's own diff for
     this stage is confined to: the `source.py` signature widening
     above, wiring a source term into the derivative evaluation, a
     seventh registry in `assembly.py`, and the `AssembledNumerics`
     field that carries it. Four files, named. Any engine file outside
     that list that this stage modifies is named in the exit audit with
     the reason -- and the audit reads the actual diff, not this list.
   - **No numerics interface learns what a phenomenon is.**
     `AdvectionScheme`, `DiffusionScheme`, `TimeIntegrator`,
     `LinearSolver`, `PressureCoupling` and `BoundaryCondition` are
     untouched by every task in this stage. This is the code half of
     `src/pyflow/physics/CLAUDE.md`'s boundary, and the half that makes
     ADR-003's swappability claim and this stage's claim independently
     testable rather than mutually assumed.
3. **Every field carries its own physical coefficients, through the
   mechanisms that already exist.** Per-field diffusivity and per-field
   boundary values were both built in Stage 5 (TASK-031b/031c) and have
   had exactly one consumer each -- momentum. This stage is the first
   real test of whether they generalise.
   - Two fields transported in one run **at different diffusivities each
     diffuse at their own rate**, measured against the analytic decay
     rate of a sinusoidal mode, not merely observed to differ. Two wrong
     rates also differ.
   - Two fields transported in one run **take different values at the
     same wall**, through `BoundaryFaceConfig.field_values`/
     `field_gradients` -- the surface TASK-031c built and that only
     velocity's two components have ever used.
   - **No second per-field coefficient mechanism is added.** The
     qualifier that makes this criterion mean something: reusing
     `coefficient_overrides` and `overrides` *is* the claim, so a task
     that instead adds its own field-keyed dictionary somewhere else has
     failed this criterion while passing the two bullets above.
4. **Buoyancy is one coupling, not one per field.** The stage adds two
   fields that can drive motion (temperature and density) and two that
   cannot (humidity, tracers). If the first two need two mechanisms, the
   architecture is not field-centric; it is phenomenon-shaped with extra
   steps.
   - **One Boussinesq body-force implementation**, exercised by both a
     temperature-driven and a density-driven configuration, reached
     through the same configured seam in both.
   - **Warm fluid rises.** A warm patch in an otherwise still, uniform
     domain acquires an upward vertical velocity within a stated number
     of steps. This is the exact defect the 2026-08-18 scientific-
     accuracy review found in `docs/handbook/physics/buoyancy.md`'s prose
     -- an inverted sign that read as completely coherent -- and
     `docs/planning/backlog.md`'s "physical sanity checks" item names
     this stage as where it becomes a test.
   - **Reversing gravity reverses the motion**, and gravity is
     configured rather than hardcoded. A sign check against a constant
     compiled into the source proves the constant, not the physics.
   - **The null case is exact, not approximate.** With no temperature
     difference for it to act on, a run carrying a temperature field
     produces a velocity field *identical* to the same run without one
     -- element by element, not to a tolerance. A buoyancy term that
     leaks a small spurious force passes a tolerance and fails this.
5. **A passive tracer is exactly passive.** The recorded intent's own
   word, and the only reading of it that can fail.
   - The same configuration run with and without the tracer produces
     velocity fields that agree **exactly, element by element** -- not
     to a floating-point tolerance, which a genuinely coupled tracer
     could also satisfy on a short enough run.
   - **And the tracer is not inert:** in the same scenario, the tracer
     field itself changes -- it is advected somewhere. Without this
     bullet the criterion above is passed perfectly by a tracer the
     engine ignores completely, which is the "passes for reasons
     unrelated to what it claims" shape Stage 4's and Stage 5's exit
     audits each found once.
6. **Physical correctness against a known answer, per case** -- per
   `docs/practices.md`'s testable-physics extension, stated per case
   rather than generically, the same shape Stages 4 and 5 both used.
   - **Temperature: the analytic decay rate.** A sinusoidal temperature
     mode on a periodic domain decays at a rate set by the thermal
     diffusivity and the wavenumber, checked against the measured rate.
     Deliberately the same physical check Stage 5's Heat Diffusion demo
     already runs on an anonymous scalar -- **and the scenario must show
     the two agree**, since that agreement is the whole content of this
     stage's claim about naming a field.
   - **Humidity: species mass is conserved.** The domain integral of the
     humidity field is unchanged, to a stated tolerance, under pure
     advection on a periodic domain with no source -- the species-
     transport analogue of Stage 4's own advection conservation check
     (`docs/handbook/physics/humidity.md`).
   - **Buoyancy: convection onset.** Rayleigh-Bénard convection is the
     validation case `docs/planning/implementation-plan.md` Level 3 and
     `planning/data/demos.yaml` both already place here, and its known
     answer is a critical Rayleigh number, approximately 1708 for the
     rigid-rigid case PyFlow's no-slip walls produce. **Design question
     five, resolved 2026-08-30: that number is not this stage's bar.**
     The bar is the qualitative one -- rolls form when the layer is
     heated from below and do not when it is heated from above, which no
     sign error survives. The quantitative comparison is deferred rather
     than dropped, to Stage 8 (Better Numerics) at the earliest, and
     `docs/planning/backlog.md`'s own Rayleigh-Bénard item is amended to
     say so rather than left reading as though this stage owed it.
   - **Density: what conservation means here.** The recorded intent asks
     whether "a variable-density configuration conserves mass", which
     reads as a claim about the continuity equation. **Design question
     three, resolved 2026-08-30: this stage is Boussinesq**, so it is
     not that claim -- continuity stays divergence-free, and the
     criterion is that the density field's own domain integral is
     conserved by its transport. What that excludes is stated in the
     question's answer below and again in TASK-036's own entry, so its
     absence cannot later be read as a gap.
7. **Rejection paths are exercised against real bad input**, and each
   named surface is a configuration somebody would plausibly write
   rather than a constructed impossibility. The list is stated now so
   the exit audit counts against it rather than against whatever got
   built: a configuration still setting `simulation.scalar_pattern`
   after TASK-042 migrates it; two declared fields with the same name; a
   declared field whose name collides with a velocity component
   (`VectorField.component_name`) or with the pressure field; a declared
   field with a non-positive diffusivity, mirroring `FluidConfig`'s
   existing checks on `viscosity`/`diffusion_coefficient`; a buoyancy
   coupling declared in a run whose velocity is not solved; and an
   unknown initial-condition pattern for a declared field.
   - **The fourth surface changed while the tasks were being drafted,
     and the change is recorded rather than made silently.** As first
     written it was "a buoyancy coupling naming a field that is not
     declared", which the resolved design shape makes unreachable: the
     coupling is declared *on* a field, so there is no name to dangle.
     The surface that replaces it is a real one that loads cleanly today
     and does nothing -- a body force in a run whose velocity is
     prescribed rather than solved. A criterion whose named surface
     turns out not to exist is amended at drafting time, which is the
     cheapest moment (`docs/practices.md`, "At drafting time: every
     qualifier becomes a bullet, or is struck"); the migration break was
     added in the same pass, having been TASK-042's headline criterion
     and absent from this list.
   - **Each fails at configuration load, with a message naming the field
     and what to do about it**, not with an `AttributeError` or a
     `KeyError` raised deep inside `bootstrap`. This is the accessor
     half of `docs/practices.md`'s "rejection criteria stop at the
     constructor": the declaration surface is new, so its construction
     and its use each need a rejection criterion, and the second is the
     one that gets forgotten.
8. **Executable Gherkin criteria, with `make check-scenarios` gating --
   and this stage's step-definition count is reported as evidence for or
   against its own goal.** The intent recorded on 2026-08-22 says a large
   crop of new step definitions "is itself evidence against the stage's
   own claim, and worth reporting as a finding rather than absorbing
   quietly". That is only true if somebody counts, so: the exit audit
   states how many step definitions this stage added and how many it
   reused from Stage 4's and Stage 5's vocabulary, both figures measured
   rather than estimated. A large number is reported as a finding
   whatever else passes.
   - **The five feature-file names this stage's task entries promise are
     themselves checked**, via `tools/validators/check_references.py`'s
     `PLANNED` table. That was not true when these criteria were drafted:
     `.feature` had never been in that script's extension tuple, so no
     feature path in any document was checked and Stage 5's own four
     `PLANNED` entries could not have fired. Fixed on 2026-08-30 with a
     regression test verified against the pre-fix tuple, and generalised
     into `docs/practices.md`'s "A rule that matches nothing reports
     nothing". It matters to this criterion specifically: under
     `adr/ADR-007-executable-acceptance-criteria.md` a task's feature
     file *is* its acceptance criteria, so a task landing under a
     different filename than its entry names is a task whose criteria
     nobody can find.
9. **Demonstrations: Heat Transport, Smoke Transport and Thermal
   Buoyancy run from committed configuration**, each meeting
   `docs/implementation/golden-demos.md`'s own Definition of Done.
   - **The three demo lists this stage inherited did not agree, and
     reconciling them was part of this criterion rather than a tidy-up
     afterwards -- done 2026-08-30, in the change that wrote this
     stage's task entries, not deferred to a task.** This document's
     Stage 6 named three demos. Heat Transport was already carried
     everywhere it needed to be, as a second `validates` edge on
     `planning/data/demos.yaml`'s `demo-heat-diffusion` and a
     parenthetical on that demo's Golden Demos table row -- the
     reuse-at-a-later-Level pattern Taylor-Green already follows.
     **Smoke Transport and Thermal Buoyancy were the real gap**: neither
     had a graph entity or a table row, and Thermal Buoyancy was not in
     `docs/planning/implementation-plan.md` Level 3's own Golden Demo
     list either, which is what made the three lists diverge. Both now
     have both, and Level 3's list names all three; what remains for
     this criterion is that they *run*.
   - **The first version of this bullet said all three were missing from
     the table and the graph, which was wrong**, and is corrected here
     rather than quietly restated: Heat Transport's reuse edge was found
     by opening `demos.yaml` to add the entities, not by re-reading the
     claim. Recorded because the whole point of this criterion is that
     lists get compared by reading them, and a comparison written from
     two of the three lists is the same defect one level up.
   - **Heat Transport is the named-Temperature claim, not Stage 5's Heat
     Diffusion repeated** (`docs/planning/implementation-plan.md` Level
     3's own note, 2026-08-28): the anonymous-scalar version already
     works, and this demo's content is that naming the field and
     coupling it to momentum cost nothing.
10. **`make ci` green on a real runner, both platforms.** Read from
    `gh run view`'s own per-job output for a named run id, on
    `ubuntu-latest` and `windows-latest` both -- not from a local pass,
    which is not that evidence. The Stage 5 exit audit had to correct
    this exact verdict once.
11. **Documentation matches the tree, `src/pyflow/physics/` included.**
    The stage-level criterion no task naturally owns, and the one that
    has now gone unmet or overstated in four separate stage audits.
    - **`src/pyflow/physics/CLAUDE.md`'s "Empty until Stage 6, and empty
      on purpose" and `__init__.py`'s matching docstring both become
      false during this stage**, and are rewritten by the task that
      falsifies them, in that task's own change -- not left for the exit
      audit to find. `docs/architecture/overview.md`'s two "physics/
      still empty (Stage 6)" claims are in the same radius, and
      `README.md`'s Current Phase section is now checked mechanically
      (`tools/generators/generate_status_report.py`, made to read it by
      the Stage 5 exit audit after that section went a full stage stale
      twice).
    - **`make check-claims` is run and its findings triaged**, since
      "this directory is empty" is exactly the claim it exists to catch,
      and this stage is the one that makes four such claims wrong.
12. **The configuration surface is real, validated and documented** --
    the criterion Stage 5 nearly missed by assuming that a component
    being selectable meant a simulation being specifiable, and which
    this stage needs more than Stage 5 did, because everything above
    rests on it. Checked field by field against
    `src/pyflow/configuration/schema.py`, PyFlow today can express none
    of: a second transported field, a per-field initial condition, a
    per-field diffusivity, a gravity vector, a thermal expansion
    coefficient, a reference temperature or density, or which field the
    renderer should colour.
    - Every field added carries its own validation and its own rejection
      test, beside the ones `FluidConfig` and `SimulationConfig` already
      have.
    - `make check-config-template` covers the new surface, and
      `pyflow generate-config` emits a loadable scaffold containing it.
      Both already gate, so this bullet states what must not be
      bypassed rather than new work.

### Six design questions, all resolved

Five raised 2026-08-29 when these criteria were drafted and a sixth on
2026-08-30 while writing the task entries, each put to the maintainer
the day it was raised and answered directly. Recorded
below as questions-with-answers rather than rewritten into decisions
that read as though they were never in doubt -- Stage 4's and Stage 5's
own precedent, and the reason a reader can tell which parts of this
stage were chosen and which were obvious.

**One: does this stage get a configuration task of its own, built
first?** `SimulationConfig` seeds exactly one scalar field, named
`"tracer"` in `bootstrap.py`'s own source, chosen from a two-value
`ScalarTransportPattern` enum. Every criterion above needs a way to
*declare* fields -- a name, an initial condition, a diffusivity, a
boundary treatment, and for temperature and density a coupling -- and
adding four bespoke `SimulationConfig` flags instead would be four
special cases wearing a field-centric label. That work is cross-cutting
(schema, loader, template generator, `pyflow generate-config`,
`bootstrap`, at least one committed demo config), contains no physics,
and is exactly the shape Stage 5 split out as TASK-041 after finding it
had landed inside TASK-031 by default.

**Resolved: yes -- TASK-042 (Field Declaration Configuration), built
first.** The alternative considered and rejected was folding it into
TASK-035, which would have made "Temperature" responsible for the
stage's whole configuration surface and repeated the mistake Stage 5
corrected mid-stage. **It is numbered 042 and placed first in this
stage's document order** -- position says what happens when, the number
does not, the same arrangement TASK-040 and TASK-041 were both kept
under. What this buys is not tidiness: it is what makes Criterion 1's
"the last two tasks add zero lines under `src/pyflow/`" a measurement
rather than an aspiration, because once the declaration surface exists
there is nothing left for TASK-037 and TASK-038 to add.

**Two: does implementing `SourceTerm` falsify this stage's own "no new
machinery" claim?** Buoyancy needs a body force in the momentum
equation, `step`'s derivative has no source contribution today, and
`SourceTerm` has no implementation, no registry entry and no consumer.
Three readings: (a) the claim means *no engine code at all*, in which
case buoyancy belongs to a later stage; (b) the claim means *no new
interface*, and implementing one Stage 3 designed for exactly this
consumer is the architecture working rather than failing; (c) the claim
is retired as too strong to be useful.

**Resolved: reading (b).** The claim means no new *interface* and no
change to an existing one's signature -- which is what Criterion 2 says,
drafted under this reading and now confirmed rather than assumed.
`adr/ADR-003-modular-numerical-strategies.md`'s six components stay six;
`SourceTerm`'s own abstract signature is unchanged; and the engine diff
this stage is allowed is bounded in advance to three things (the
derivative's source contribution, a seventh registry in `assembly.py`,
the `AssembledNumerics` field carrying it) and *measured* against the
real diff at the exit audit rather than asserted. Reading (a) was
rejected on the grounds that it would strip this stage of the only demo
that distinguishes it from Stage 5 -- Heat Transport without buoyancy is
Heat Diffusion with a different field name -- and reading (c) on the
grounds that it discards the one criterion that is genuinely about the
stage's goal. **The honest cost of (b), stated so the exit audit does
not have to rediscover it: TASK-035 is not a zero-engine-change task,
and this stage's claim is now about its other four tasks.**

**Three: is density Boussinesq, or genuinely variable?**
`docs/handbook/physics/density.md` sets out both and commits to neither
("not assumed by this document to be PyFlow's eventual implementation
choice"). The recorded intent's "whether a variable-density
configuration conserves mass" reads as the second; every other document
that touches the question reaches for the first.

**Resolved: Boussinesq.** Density variation is neglected everywhere
except the gravity term: continuity stays divergence-free, Stage 5's
projection and corrector are untouched, and density is a transported
scalar that reaches momentum through the same body force temperature
does. **What this excludes is stated explicitly here so its absence is
not later mistaken for a gap** -- the treatment Stage 5 Criterion 4 gave
checkpointing: PyFlow does not, after this stage, solve a genuinely
variable-density flow. The divergence-free constraint is not replaced by
a statement about the divergence of the mass flux, there is no second
pressure equation, and "conserves mass" in TASK-036's criteria means the
density field's own domain integral is conserved by its transport, not
that continuity has been generalised. Doing the other thing is a rewrite
of Stage 5's solver inside a stage whose goal is that nothing changes,
and would need a stage of its own.

**Four: where does the buoyancy implementation live?** A Boussinesq body
force is a phenomenon expressed through a numerics interface, so it has
a foot in both halves of `src/pyflow/physics/CLAUDE.md`'s boundary.

**Resolved: `src/pyflow/physics/`, and the repository had already
decided it -- the question was worth asking and its answer was already
written down.** That file's own "here, eventually" list names
"temperature, density, humidity, passive tracers (Stage 6, TASK-035..038),
buoyancy coupling" explicitly. What was genuinely undecided is the
*split*, and that is the part worth recording: **the `SourceTerm`
interface stays in `src/pyflow/engine/numerics/source.py` and the
concrete phenomenon implementing it lives under `src/pyflow/physics/`**,
which is the first time in this repository that an implementation of a
numerics interface sits outside `engine/numerics/`. A reader meeting
that split needs the reason next to it, and the reason is that it is
exactly what that boundary claims: the interface is machinery, the
Boussinesq body force is physics. It is also what makes Criterion 1's
line count meaningful -- a stage that fills `physics/` and leaves
`engine/` almost alone is that boundary working, and a stage that does
the reverse is it failing.

**Five: is Rayleigh-Bénard's critical Rayleigh number this stage's
bar?** `docs/planning/backlog.md` records approximately 1708 for the
rigid-rigid case, with the caveat that the value is boundary-condition
dependent and must match the walls the demo actually configures.

**Resolved: no -- the qualitative onset check is this stage's bar.**
Rolls form when the layer is heated from below and do not when it is
heated from above; no sign error survives that, which is what this
stage's own validation needs. Hitting approximately 1708 quantitatively
on a first-order-upwind solver at MVP mesh resolutions is the same shape
of risk Stage 5 met and decided against when it rejected ADR-007's
illustrative "within 2%" for Ghia's profiles in favour of convergence
across resolutions: a criterion meetable only by loosening its own
number later is not a criterion. **The number is not discarded, it is
reassigned**, and `docs/planning/backlog.md`'s own Rayleigh-Bénard item
is amended in the same change rather than left reading as though this
stage owed it: the critical-Rayleigh-number comparison becomes due when
a scheme exists that could clear it, which is Stage 8 (Better Numerics)
at the earliest. Criterion 6's buoyancy bullet is written to the
qualitative bar and says which half was deferred and why.

**Six: how does a source term see a field it is not being asked
about?** Raised 2026-08-30, while writing TASK-035's entry, and the only
one of the six found by tracing a call rather than by comparing
documents. `SourceTerm.source(self, field: Field)` receives only the
field being advanced. Buoyancy acts on momentum's own `velocity.1` and
is computed from the *temperature* field, which that signature never
passes it -- so the interface Stage 3 designed for exactly this consumer
cannot express its first consumer. Criterion 2 as drafted forbade the
obvious fix outright ("no existing interface's signature changes"),
which made it a criterion that could not be met rather than a constraint
that could be respected. Three ways out: widen the signature to take the
state; keep it and have `step` bind the source term to the current state
at each derivative evaluation; or construct the term with the field it
reads, once per step, accepting a stale reference inside RK4's four
stages.

**Resolved: widen the signature, to `source(self, field: Field, state:
Mapping[str, Field]) -> torch.Tensor`.** `SourceTerm` has no
implementations, so nothing breaks, and the widening makes a cross-field
dependency explicit in a type rather than hidden inside a closure --
`docs/practices.md`'s Design Rules ask for the version that is easier to
understand where two are equivalent, and these are not even equivalent:
the binding alternative introduces a concept this repository has no
precedent for, and the third is a first-order splitting whose accuracy
cost would have to be stated and defended. It also costs nothing to get
RK4 consistency: `derivative` already receives the intermediate state,
so a source term evaluated at each of RK4's stages sees that stage's
temperature rather than the step's opening one.

**It is also owed an ADR, and TASK-035 owes it.** This repository has
recorded a Stage 3 interface signature change as an ADR twice --
`adr/ADR-008-time-integrator-derivative-callable.md` when
`TimeIntegrator.advance`'s derivative parameter widened for RK4, and
`adr/ADR-009-pressure-coupling-dt.md` when `PressureCoupling.correct`
gained `dt` -- both written by the task that made the change rather than
by the design pass that decided it. `adr/ADR-010-source-term-state.md`
follows the same pattern, is named in TASK-035's Artifacts Produced, and
is registered in `tools/validators/check_references.py`'s `PLANNED`
table so forgetting it is a build failure rather than something a
reviewer has to notice.

**Criterion 2 is amended in the same change rather than quietly
satisfied**, and its headline now reads "exactly one existing
interface's signature changes -- named here in advance". That is the
honest shape: the count is the constraint, and a criterion that names
one permitted change and measures the diff against it is stronger than
one that forbade a change nobody could avoid. The escape clause the
original wording carried -- "if it must change, that is a design
session, not an edit" -- is what was used, on the day the need was
found, rather than during TASK-035's implementation.

### Discharge map

Every criterion has an owning task, assigned now rather than
reconstructed at the exit audit, following Stages 3, 4 and 5. A task's
own **Discharges** section is authoritative; this table is the index.

**Build order is TASK-042, 035, 036, 037, 038**, and structural rather
than convenient: TASK-042 settles the declaration surface every task
after it reads, TASK-035 builds the one piece of engine wiring this
stage is allowed and the buoyancy coupling that depends on it, TASK-036
proves that coupling serves a second field without a second
implementation, and TASK-037 and TASK-038 are the two tasks whose whole
content is that they need nothing. **The order is also the argument**:
if the last two tasks are not trivial by the time they are reached, the
stage's goal is not met, whatever the first three achieved.

| Criterion | Discharged by |
|-----------|---------------|
| 1. A transported field is added by configuration, not by code | TASK-042 builds the surface; TASK-037 and TASK-038 are the measurement, and the exit audit reads `git diff --stat` for `src/pyflow/` across each of their branches rather than judging it |
| 2. No new interface, and no existing interface's signature changes | TASK-035, the only task in this stage permitted to touch `src/pyflow/engine/` at all; verified against the real diff at the exit audit |
| 3. Every field carries its own physical coefficients, through mechanisms that already exist | TASK-042 for the configuration half; TASK-037 for the behavioural half, being the first task to run two fields at two diffusivities with two wall values |
| 4. Buoyancy is one coupling, not one per field | TASK-035 builds it; TASK-036 is what makes it a *claim* rather than an implementation detail, by driving a second field through the same object |
| 5. A passive tracer is exactly passive | TASK-038 |
| 6. Physical correctness against a known answer, per case | TASK-035 (the analytic decay rate, the buoyancy sign, convection onset), TASK-036 (density's own conservation and the mirrored sink direction), TASK-037 (species mass conservation) |
| 7. Rejection paths exercised against real bad input | TASK-042 for five of the six named surfaces, since five are properties of the declaration surface it builds; TASK-035 for the sixth (a buoyancy coupling in a run whose velocity is not solved) |
| 8. Executable Gherkin criteria, `make check-scenarios` gates | TASK-042 and TASK-035..038, each for its own `.feature` file; TASK-038 for the step-definition count, being this stage's last task |
| 9. Demonstrations: Heat Transport, Smoke Transport, Thermal Buoyancy | TASK-035 (Heat Transport, Thermal Buoyancy), TASK-038 (Smoke Transport). The three-document reconciliation the criterion names was done when these criteria were written, not deferred to the task -- see the Golden Demos section below |
| 10. `make ci` green on a real runner, both platforms | TASK-038 |
| 11. Documentation matches the tree, `src/pyflow/physics/` included | TASK-035 for the four claims it is the task to falsify (`physics/CLAUDE.md`, `physics/__init__.py`, and `docs/architecture/overview.md`'s two); TASK-038 for the stage-wide sweep and `make check-claims` |
| 12. The configuration surface is real, validated and documented | TASK-042 for the declaration surface, the migration and the rendered-field selector; TASK-035 for gravity and the buoyancy coupling's own fields |

**TASK-038 is this stage's last task in build order and therefore owns
the stage-level criteria** -- the CI evidence, the documentation sweep,
the step-definition count and the exit audit itself -- the same
assignment Stage 4 made to TASK-030 and Stage 5 to TASK-034, and made
here when the criteria were written rather than discovered at the end
(`docs/practices.md`, "Criteria that no task can own get one anyway").

### Intent, recorded now

Recorded 2026-08-22, ahead of the criteria above, because it is the
durable half and the half this repository keeps losing. Each line states
what the task must not merely *nominally* satisfy (`docs/practices.md`,
"The intent lives in the qualifier"). The Completion Criteria above were
drafted against these on 2026-08-29, not in place of them. **TASK-042
carries no 2026-08-22 intent line because it did not exist then** -- it
was added on 2026-08-30 by design question one, and its intent is
recorded in its own entry, dated as such rather than backdated into this
list.

### Status as of 2026-08-31: Stage 6 complete, twelve of twelve criteria met

**Three of these twelve verdicts did not survive the audit as the stage
left them -- Criteria 4, 6 and 11 -- and a fourth, Criterion 7, was met
exactly as written while a defect in shipped behaviour sat just outside
what it named.** That last distinction is worth keeping rather than
rounding off: the criterion enumerated six rejection surfaces and six
exist, so nothing about the verdict was overstated. What the enumeration
missed was a seventh, and a criterion cannot be blamed for a surface
nobody thought of -- which is exactly why the exit audit reads the
repository rather than only the criteria. Unlike Stages 3, 4 and 5, this stage's task
list closed without any verdict table at all -- TASK-038 deliberately
left this section unwritten (its own Status note says so) so that the
first table ever written for Stage 6 would be written under
`prompts/common/AUDITOR.md`'s stance, in a separate pass, rather than by
the session that closed the last task. This is that table. The rows that
failed say what was claimed, what was actually true, and what was done
about it, rather than being quietly rewritten (root `CLAUDE.md`'s
Integrity section).

**The stage's own goal held, and held on the measurement it named in
advance.** TASK-037 and TASK-038 each added **zero** lines under
`src/pyflow/` -- `git diff --numstat` across each task's own branch
returns nothing at all for that tree -- and so did TASK-036, a third
task Criterion 1 never asked about. Adding temperature, density,
humidity and passive tracers to PyFlow cost one configuration section
(TASK-042), one body-force coupling (TASK-035), and nothing else.

**What failed.** Criterion 6's own closing sentence had not been carried
out: it says `docs/planning/backlog.md`'s Rayleigh-Bénard item "is
amended in the same change", and the commit that drafted it claimed
"both documents that name it say so now" -- only one of the two was
amended. Criterion 4's substitution check proved less than it
claimed: the scenario meant to show *one* `BoussinesqBuoyancy` reached
through the configured seam reimplemented `bootstrap.py`'s own
coupling-map construction inside its step definition, so a `bootstrap.py`
that dropped a declaration would have passed it. Criterion 7 named six
rejection surfaces and six exist -- but a seventh was reachable and
silently inert: a field declaring a buoyancy coupling while
`numerics.source_term` is left at its default loads cleanly and produces
no body force at all, measured at maximum vertical velocity **0.0**
against **0.451** with the term selected. That is the same shape as the
`velocity_solved` defect the Stage 5 audit found -- a plausible
configuration whose stated intent the engine silently ignores -- and it
is fixed here, not recorded. Criterion 11 failed the way it has now
failed in five consecutive stage audits.

**One thing this audit could not close cleanly, stated plainly rather
than folded into Criterion 10's verdict: `make ci` was red on this
branch before the audit touched it**, and for a reason no CI run can
see.
`tests/integration/test_interactive_window.py::test_close_key_terminates_the_render_loop_and_process_cleanly`
failed deterministically (`assert 2 > 2`). It is not Stage 6's doing --
`git diff` shows `src/pyflow/rendering/` and that test file byte-
identical to Stage 5's close -- and it carries `_needs_a_real_display`,
so both CI runners skip it and neither could ever have caught it. The
cause was measured, not guessed: a real glfw window takes about half a
second to begin painting and then paints at about 30 fps, and the test
raced a fixed 0.5s delay against that startup (0.5s gives 2 frames, 1.0s
gives 30, 2.0s gives 60). It now waits on a frame count with a timeout
backstop, so a genuinely frozen window still fails rather than hangs.
**The general point is worth more than the fix: for this repository,
"CI is green" and "`make ci` passes" are not the same statement**, and
Criterion 10 only ever asked for the first.

| Criterion | Verdict |
|-----------|---------|
| 1. A transported field is added by configuration, not by code | **Met, on every bullet, and the measurable one is a number rather than a judgement.** Four named fields in one run alongside a solved velocity: `tests/features/passive_tracers.feature`'s four-tracer scenario, one configuration, one `bootstrap()` call, each tracer at its own diffusivity so a shared-tensor bug cannot pass by coincidence -- and each identical whether transported alone or alongside the other three. No phenomenon field class: `src/pyflow/engine/` declares `Field`, `CollocatedField`, `ScalarField`, `VectorField` and `PressureField` and nothing else; there is no `TemperatureField`, `DensityField`, `HumidityField` or `TracerField`, verified by reading the class list rather than by grep alone. The structural check is `passive_tracers.feature`'s own fourth scenario, asserting all four literals absent from `inspect.getsource(simulation)` -- added by TASK-038 after it found only `"velocity"` and `"temperature"` had ever been checked. **The measurement: TASK-037 and TASK-038 each add zero lines under `src/pyflow/`** (`git diff --numstat` returns no rows at all for that tree across either branch), **and so does TASK-036** -- three consecutive tasks, where the criterion asked for two. For contrast, TASK-042 added 366 and removed 107 across five files, TASK-035 added 643 and removed 57 across eleven. The anticipation loophole the criterion named in advance is not exercised: `FieldConfig`'s fields are `name`, `initial_condition`, `diffusion_coefficient`, `buoyancy_reference_value` and `buoyancy_coefficient`, none of which names a phenomenon, and the buoyancy pair is deliberately generic precisely so density could reuse it with the opposite sign. |
| 2. No new interface, and exactly one existing interface's signature changes -- named here in advance | **Met, with two engine files named that the criterion's own list did not.** `SourceTerm` gained its first concrete implementation; `adr/ADR-003`'s six components stay six. Exactly one signature change, and it is the one named in advance: `source(self, field: Field, state: Mapping[str, Field])`, recorded as `adr/ADR-010-source-term-state.md`. The whole-stage diff under `src/pyflow/engine/` is `numerics/assembly.py` (+103), `numerics/source.py` (+39/-28) and `simulation.py` (+16/-1) -- the three code files the criterion named, and no others. **The two the criterion did not name are `src/pyflow/engine/CLAUDE.md` (+85) and `src/pyflow/engine/numerics/CLAUDE.md` (+19)**, both documenting the three changes above; named here because the criterion's own text says any engine file outside its list "is named in the exit audit with the reason". No numerics interface learned what a phenomenon is: `advection.py`, `diffusion.py`, `time_integrator.py`, `linear_solver.py`, `pressure_coupling.py` and `boundary_condition.py` are untouched by every task in this stage -- read off the diff, not assumed. |
| 3. Every field carries its own physical coefficients, through the mechanisms that already exist | **Met, with one qualification the criterion's own last bullet makes worth stating.** Two fields at two diffusivities, each decaying at its own analytic rate rather than merely differing: `tests/features/humidity_field.feature`'s first scenario -- the first time `CentralDifferenceDiffusion.coefficient_overrides` has carried **two** entries whose rates both had to be right (TASK-042 already gave it one non-momentum entry per declared field, so the single-field case was not the test; two fields at two rates, each measured against its own closed form, is what a shared-rate bug cannot pass). Two fields taking different values at the same wall through `BoundaryFaceConfig.field_values`: its second scenario, the first to reach that surface through real `load_config` → `assemble_numerics` rather than a hand-built condition. **The qualification: TASK-035 did add a new field-keyed dictionary** -- `buoyancy_couplings`, built in `bootstrap.py` and threaded to `BoussinesqBuoyancy` on the same "assemble_numerics stays field-name-agnostic" split `coefficient_overrides` established. Judged not a failure of this criterion, and the reasoning is recorded rather than assumed: the bullet forbids *replacing* the per-field coefficient mechanisms this stage exists to test, and a buoyancy reference/coefficient pair is a quantity neither `coefficient_overrides` nor `overrides` could carry. Diffusivity and wall values -- the two coefficients that already had mechanisms -- both went through those mechanisms unchanged. |
| 4. Buoyancy is one coupling, not one per field | **Met after this audit; the one check that made it a *claim* rather than an implementation detail was overstated as it landed.** One `BoussinesqBuoyancy` serves both couplings -- TASK-036 added zero lines under `src/pyflow/` and reused the class with `c = +1/rho_0` where temperature uses `c = -beta`. Warm fluid rises and reversing a *configured* gravity reverses it (`temperature_field.feature`); a denser patch sinks (`density_field.feature`), which a sign error common to both couplings could not survive. The null case is exact: a uniform temperature field leaves velocity bit-identical to carrying no temperature field at all, `torch.equal`, not a tolerance. **What failed: `density_field.feature`'s "one instance, both couplings" scenario built the coupling map itself** -- a line-for-line copy of `bootstrap.py`'s loop -- and handed it to `assemble_numerics`, so it proved that `assemble_numerics` forwards a map the *test* wrote. Criterion 4's own words are "reached through the same configured seam in both", and a seam a test reimplements is not the seam. Rewritten in this audit to go through real `bootstrap()` and to probe the assembled instance with each declared field alone; verified to fail (`density's declared coupling drove nothing downward`) when `bootstrap.py` is made to drop the second declaration. **The sign was also re-derived independently against `docs/handbook/physics/buoyancy.md`** rather than taken from TASK-035's own derivation: that entry's per-volume form divided by `rho_0` gives `-beta (T - T_0) g` and `(rho - rho_0)/rho_0 g`, which is exactly `c * (phi - phi_0) * g` under the two coefficients the configuration supplies. |
| 5. A passive tracer is exactly passive | **Met, both bullets, in the one scenario the criterion insisted they share.** The same configuration run with and without a declared tracer produces bit-identical velocity components (`torch.equal`), and in that same scenario the tracer itself is measurably different after several timesteps than after one -- so the exactness above cannot be passed by a tracer the engine ignores. Four tracers transported together are pairwise distinct and each identical to its own solo run. |
| 6. Physical correctness against a known answer, per case | **Met on all four cases; the criterion's own closing sentence had not been carried out, and is now.** Temperature: a sinusoidal mode's measured decay rate matches `Gamma * k^2` within 10%, through a real configured field, and `tests/features/heat_transport.feature` runs the identical check on the committed demo -- the agreement Stage 5's anonymous scalar and this stage's named field were required to show. Humidity and density: each field's own domain integral unchanged to 1e-9 under pure advection on a periodic domain with diffusion and source both zeroed, so only transport could leak. Buoyancy: a layer heated from below develops more than twice the vertical-velocity RMS of the same layer heated from above (Rayleigh number ~2.0e4 against a critical ~1708, so the unstable case is genuinely supercritical), which is the qualitative bar design question five settled. **What was missing: the criterion says `docs/planning/backlog.md`'s Rayleigh-Bénard item "is amended in the same change rather than left reading as though this stage owed it", and the commit that drafted it recorded "both documents that name it say so now". Only `docs/planning/implementation-plan.md` was amended.** Two documents name ~1708; the backlog was the other one, and its bullet still read as though Level 3 owed the number. Amended in this audit's own change. |
| 7. Rejection paths are exercised against real bad input | **Met as to the six surfaces named in advance -- and a seventh existed, was reachable from an ordinary configuration file, and did nothing.** The six: the `simulation.scalar_pattern` migration break, a duplicate field name, a name colliding with a velocity component, a name colliding with the pressure field, a non-positive diffusivity and an unknown initial-condition pattern (all `tests/features/field_declaration.feature`), plus a buoyancy coupling in a run whose velocity is not solved (`temperature_field.feature`). Each fails at `load_config` with a message naming the field, and each rejection step definition calls `load_config` directly and never reaches `bootstrap()` -- which is the accessor half made structural rather than asserted. **The seventh, found by this audit: a field declaring a buoyancy coupling while `numerics.source_term` is left at its default `"none"`.** It loads cleanly, transports the field, and no force ever reaches momentum -- measured end to end through `bootstrap()` at maximum vertical velocity **0.0**, against **0.451** for the identical configuration with `boussinesq_buoyancy` selected. `tests/unit/test_density_field.py`'s own committed two-coupling configuration was one such file, and its comment (`"none"-equivalent`) shows the assumption that hid it. **Fixed rather than recorded**, at the maintainer's standing direction: `_validate_buoyancy_couplings` now rejects it with a message naming the field, `numerics.source_term`, and what to set it to; the scenario was written first and watched fail. The rule is phrased as "no source term selected" rather than "not `boussinesq_buoyancy`", so a future term does not have to be added to it. |
| 8. Executable Gherkin criteria, `make check-scenarios` gating -- and the step-definition count reported as evidence for or against the stage's own goal | **Met, and the count is reported as a finding, as the criterion requires whatever else passes. It is large.** Stage 6's five tasks added **93 step definitions**, taking the repository from 241 to 334 -- 28% of its entire step vocabulary, in one stage -- across **8 new feature files** and **+36 scenarios** (95 to 131). Both figures are measured (`grep -cE '^@(given|when|then)'` per module, at this stage's base commit and at its last task) rather than estimated. **Reuse, measured the same way, is small and concentrated:** the three golden-demo modules (`test_heat_transport.py`, `test_thermal_buoyancy.py`, `test_smoke_transport.py`) define 2 definitions each and reuse `tests/golden/conftest.py`'s demo vocabulary for the rest -- 9 reused step usages across 3 files; the five mechanism-level modules reuse nothing and define 87 between them. **The honest reading, since the criterion asks for one:** the number does not support this stage's claim. It has a structural explanation -- `tests/features/CLAUDE.md`'s own convention is that a step only one feature could use lives in that feature's module, and five of the eight files are engine-level with no shared vocabulary to draw on -- but an explanation is not a defence, and 93 is the figure. What it is *not* evidence of is engine special-casing: the same stage added zero `src/pyflow/` lines in three of its five tasks. `make check-scenarios` gates and reports all 132 scenarios across 29 feature files bound and running; `check_references.py`'s `PLANNED` table is empty, every promised artifact having landed. Three feature files exist beyond the five the task entries promised (`heat_transport`, `thermal_buoyancy`, `smoke_transport`), each recorded in its own task's Status note when it was added. |
| 9. Demonstrations: Heat Transport, Smoke Transport and Thermal Buoyancy run from committed configuration | **Met, and the three-list reconciliation the criterion names had genuinely been done when the criteria were drafted -- verified rather than taken on trust.** All three run: `examples/golden-demos/heat_transport.yaml`, `smoke_transport.yaml`, `thermal_buoyancy.yaml`, each with a `tests/golden/` module invoking the real CLI as a subprocess with the demo's own config file (the Definition of Done's own strongest clause) plus a second scenario checking something physical rather than exit status -- the named field's analytic decay rate, the smoke field genuinely carried by the recirculating flow, the warm patch's vertical velocity positive at its own warmest cell. Each has a section in `docs/implementation/golden-demos.md`, a row in `docs/planning/implementation-plan.md`'s Golden Demos table, an entity in `planning/data/demos.yaml` with a `validates` edge to Capability Level 3, and a name in Level 3's own Golden Demo list -- all four checked directly, in all three cases. |
| 10. `make ci` green on a real runner, both platforms | **Met -- GitHub Actions run `33384025409`, on commit `8d1b81e`, both jobs `success`.** Read from `gh run view`'s own per-job output rather than from a local pass, the distinction the Stage 5 exit audit had to correct once: `ci (ubuntu-latest)` succeeded at 11:01:02Z (13m07s) and `ci (windows-latest)` at 11:13:11Z (25m16s), and in both the `make ci` step itself is `success` -- not merely the job. Windows takes roughly twice as long, which is why "green on a real runner" has always meant waiting for the second one. A second run covers the two documentation-only commits that follow (this row itself, and the audit's own blast-radius follow-ups), since a run cannot cover the commit that records it. **See the paragraph above this table for the separate and more useful finding:** `make ci` was red *locally* on this branch, on a display-dependent test both CI runners skip, so a green run here has never been the same statement as a green `make ci`. |
| 11. Documentation matches the tree, `src/pyflow/physics/` included | **Not met as the stage left it; met after this audit -- the fifth consecutive stage in which this row failed, and the largest crop yet at ten findings.** What the stage did do, correctly and in the task that falsified them: `src/pyflow/physics/CLAUDE.md`, `physics/__init__.py` and both of `docs/architecture/overview.md`'s "physics/ still empty" claims were rewritten by TASK-035 itself. **What it missed, all of it in files no Stage 6 task opened:** (a) **`docs/architecture/sequences.md`'s `step()` diagram still showed the derivative as `accumulate_flux_to_cells(mesh, diffusive_flux - advective_flux)` with no source term at all** -- in the document whose only stated job is runtime sequences, about the single line of engine code this stage changed, which is the *same document and the same failure* the Stage 5 audit found and wrote `docs/practices.md`'s fourth grep against; (b) **four live references to `bootstrap.py`'s `_add_passive_scalar_transport`**, renamed by TASK-042, in `sequences.md` (prose, a mermaid participant and a call arrow), `docs/architecture/rendering.md` (twice), `docs/architecture/CLAUDE.md` and `docs/implementation/golden-demos.md` -- `make check-references` resolves repository *paths*, not identifiers, so a renamed function goes stale behind a green gate; (c) `docs/implementation/golden-demos.md` still asserting that `velocity_solved` path "never pressure-corrects", stale since the *Stage 5* audit closed that gap and doubly so after the rename; (d) **`docs/architecture/icds.md`** carrying "the other four names still resolve to their own reference implementation" -- the identical sentence, about the identical four names, that the Stage 5 audit fixed in `schema.py` and did not sweep for elsewhere -- plus a three-parameter-stale `assemble_numerics` signature and no mention anywhere of `numerics.source_term`, now a real user-facing configuration key with two choices; (e) `src/pyflow/engine/CLAUDE.md` listing `SourceTerm` among "interfaces with no configuration field", eleven hundred lines above its own entry recording that it gained one; (f) **`planning/data/demos.yaml`'s header claiming "Three demos exist and run today" against a live ten** -- a hand-written count beside a directory four stages kept adding to, in a file whose own design principle is that status does not live there, and one `make check-claims` could not have found because it reads Markdown only; (g) `docs/architecture/overview.md`'s "all three subpackages it composes", against a `bootstrap()` that has composed four since TASK-035; (h) `docs/repository-manifest.md`'s "the six registries", now seven; (i) **four separate documents describing `bootstrap.py` as importing `BoussinesqBuoyancy` "to get the class itself"** when the real line is a bare `import pyflow.physics.buoyancy  # noqa: F401` referencing no name -- a rationale that reads as an invitation to delete an import that looks unused; and (j) **`docs/repository-manifest.md`'s `tests/` section claiming "56 test modules, 605 tests, 99% coverage (2026-08-28)" against a live 74 and 763** -- 158 tests stale, covering all of Stage 6 and the back half of Stage 5, and found only because `docs/practices.md`'s end-of-session step 11 says to re-read that file's `src/` and `tests/` sections *whether or not the session touched them*. It got past the Stage 5 exit audit too. The step is sound and needs no amendment; it needs running. All ten fixed in this audit's own change, plus `docs/architecture/engine.md`'s Time Integration entry, whose **Represents** sentence has always named a "source" contribution and now names what computes it. **`make check-claims` was run and triaged: 2 findings, both confirmed legitimate** (a document quoting the rule, and one describing its own directory). It reported 14 before this audit fixed the checker itself -- it walked the working tree against a hardcoded skip-list that had fallen behind `.claude/worktrees/`, so 12 of the 14 were this repository's own documents seen a second time through an open worktree, burying the 2 real candidates in an advisory report whose whole value is that a human reads every line. It now reads `git ls-files`, the same source `check_references.py` and `check_manifest.py` already use, with a regression test verified against the old implementation. **Nothing was owed to `docs/handbook/physics/buoyancy.md`** -- checked rather than assumed: no handbook entry names a `src/pyflow` path, and that directory's own `README.md` says entries separate physical knowledge from implementation. |
| 12. The configuration surface is real, validated and documented | **Met, and its one real hole is Criterion 7's seventh surface above.** Checked field by field against the criterion's own list of seven things PyFlow could not express when it was written: a second transported field (`fields:`), a per-field initial condition (`FieldConfig.initial_condition`), a per-field diffusivity (`diffusion_coefficient`), a gravity vector (`FluidConfig.gravity`), a thermal expansion coefficient and a reference temperature or density (`buoyancy_coefficient`/`buoyancy_reference_value`, deliberately named for neither phenomenon so density reuses both), and which field the renderer colours (`field_display.render_field`). All seven exist. Every one carries its own validation and its own rejection test. `make check-config-template` covers the new surface and `pyflow generate-config` emits a loadable scaffold containing it -- both gate, and both pass, checked by running them rather than by trusting that they gate. **One nuance worth stating so the tick is not unexamined**: the scaffold emits `fields: []`, an empty list, so a user gets the *key* but no worked example of a declaration; the whole surface (every sub-field, what is valid, and now what combination is rejected) is described in `docs/implementation/config-template.yaml`'s comment above that line, which is the document that exists for exactly this reason -- `PyYAML`'s `safe_dump` cannot emit comments. Not filed as a gap: the criterion asks for a loadable scaffold and a documented surface, and both exist in the places the project decided they should. The hole was not a missing field but a missing *relation*: nothing checked a declared coupling against the source term that would have to compute it, which is precisely the "a component being selectable is not a simulation being specifiable" shape this criterion was written against. |

**Blast radius of the fixes, for a reader checking this table against
the branch.** Behaviour: `src/pyflow/configuration/schema.py`
(`_validate_buoyancy_couplings`, one new rejection) and the two
committed configurations that were silently inert under it
(`tests/unit/test_configuration.py`, `tests/unit/test_density_field.py`
-- both now select a source term, which is the check finding real cases
on its first run). Criteria: `tests/features/temperature_field.feature`
(+1 scenario) and `tests/features/density_field.feature` (one scenario
rewritten). Tests: the marker-source-term substitution check now
asserts the double's own *value* by running it twice at two constants
and requiring the result to double exactly -- it previously asserted
only "nonzero", which any source term satisfies; and
`_rayleigh_benard_rms`'s docstring claimed four checkpoints and a
monotonicity check where the code had one checkpoint and no
monotonicity, reached through a vestigial comprehension.
Tooling: `tools/validators/check_claims.py`, plus its regression test
and `tools/validators/CLAUDE.md`'s record of why the mechanism changed;
`tools/generators/generate_config_template.py`'s comments for the
`fields:` section and `numerics.source_term`, with the template
regenerated. `src/pyflow/rendering/CLAUDE.md` carries the measured
window timings the interactive-window fix depended on -- found by this
audit's own blast-radius sweep, since that file described the test's old
0.5s delay as part of a manual verification recipe that shares the same
numbers.
Documents: the ten listed under Criterion 11, plus
`docs/planning/backlog.md`'s two amendments (Criterion 6's promised
Rayleigh-Bénard deferral, and a note that the buoyancy half of the
"physical sanity checks" item landed while the rest stays open), and a
note on Stage 8's own section recording that it inherits the
critical-Rayleigh-number comparison -- previously carried only in the
two documents that deferred it, neither of which a reader opening Stage
8 would reach.

**Rules recorded, rather than fixes left as one-offs.**
`docs/practices.md` gains two: **"A configuration field that states an
intention needs a check that something can act on it"** (the
`velocity_solved` and `source_term` defects are one shape seen twice,
which is what makes it a rule), and **"`make check-references` resolves
paths, not identifiers"** (with the reason no gate is proposed, so
nobody builds one twice). `tests/features/CLAUDE.md` gains two writing
rules from the two weak scenarios: a scenario must not reimplement the
thing it is testing, and an equivalence scenario has to build both of
the things it says are equivalent.

**Aggregate check against Stages 1-6, run as part of this audit at the
maintainer's request.** Every stage-level capability claim the
repository makes about itself was read back against the tree rather than
against the previous stage's claim: `README.md`'s per-stage list,
`docs/planning/implementation-plan.md`'s Capability Levels and Golden
Demos table, `docs/implementation/mvp.md`, `docs/architecture/`'s three
top-level documents, and `planning/data/`'s graph. **The sum holds --
the per-stage claims and the tree agree, and no stage claims a
capability the next stage had to build.** Two aggregate statements were
stale and both are corrected here: `README.md` said in two places that
PyFlow "has not yet begun Stage 6", and `planning/data/demos.yaml` said
three golden demos exist where ten do. `docs/planning/capability-map.md`
is deliberately status-free and owed nothing, verified by reading it
rather than assumed -- the same conclusion the Stage 5 audit reached,
re-checked rather than inherited.

## TASK-042

Field Declaration Configuration

**Status: Done, 2026-08-30, Stage 6's first task.** Artifact:
`src/pyflow/configuration/schema.py`. A real contradiction was found and
fixed while implementing, not predicted in advance: this task's own
Artifacts Produced section (below) claimed it would add the run's
gravitational acceleration to that file, while TASK-035's own Artifacts
Produced section claims *it* adds that field "on the surface TASK-042
built" -- and this task's Acceptance Criteria test neither gravity nor a
buoyancy coefficient. Resolved in favour of TASK-035's claim and this
task's own Acceptance Criteria (the buildable, tested reading): the
Artifacts Produced bullet below was corrected before either task's own
share was built, recorded there rather than silently.

**Added 2026-08-30, by design question one, before this stage's first
task started** -- unlike TASK-040 and TASK-041, which were both added
mid-stage after the work had already landed inside another task by
default. That is the whole reason this one exists at the point it does:
the same failure was visible in advance for once, in the shape of a
criterion ("a transported field is added by configuration") that no task
could discharge because no configuration surface existed to add one
with. **Numbered 042 and placed first in document order** -- position
says what happens when, the number does not.

**Intent (2026-08-30):** this is the task the stage's goal actually
rests on, and it contains no physics at all. The temptation is to build
the narrowest surface that lets TASK-035 declare a temperature field.
The measure of success is the opposite: that TASK-037 and TASK-038,
neither of which is designed yet in any detail, turn out to need nothing
from this task that TASK-035 did not already need. **A declaration
surface that has to grow once per field is the special-casing this stage
exists to disprove, relocated into `schema.py`.**

**Also:** this is the project's *second* breaking configuration change,
and TASK-041 set the standard for the first -- a config still setting
the old field must fail with an error saying where it went, not be
silently defaulted. `simulation.scalar_pattern` is the field being
migrated here, and leaving it in place beside a `fields:` declaration
would mean two ways to declare a transported field, which is precisely
the second mechanism Criterion 3's qualifier forbids.

### Purpose

Give a configuration file a way to declare the transported fields a run
carries -- each with its own name, initial condition, diffusivity,
boundary treatment and, where it has one, its coupling to momentum -- so
that every task after it in this stage is a configuration entry and a
feature file rather than a code change.

### Dependencies

TASK-005 (the configuration framework), TASK-019 (`NumericsConfig` and
whole-configuration validation), TASK-039 (`pyflow generate-config`),
TASK-041 (`FluidConfig`, and the migration precedent this task follows),
TASK-031b/031c (`coefficient_overrides` and
`DirichletBoundaryCondition.overrides` -- the per-field mechanisms this
surface feeds, which already exist and must not be duplicated).

No engine dependency beyond reading those two existing mechanisms.
**Stated with TASK-041's own correction in view rather than repeated
blindly:** that task's entry claimed "no engine dependency at all" and
was wrong, because `assemble_numerics` already read the field being
migrated. The same question was asked here before the claim was made --
`bootstrap.py` is what builds fields from `simulation.scalar_pattern`,
and `assemble_numerics` reads `fluid.diffusion_coefficient` and the
per-field override map that `bootstrap` assembles -- so this task
changes `bootstrap.py` and the shape of the override map it builds, and
that is named here rather than discovered during implementation.

### Design decisions, made here

- **A top-level `fields:` section, not an extension of `simulation:`.**
  `SimulationConfig`'s own scope is live stepping (what runs, how fast);
  a field declaration is what the run *contains*, and it is neither a
  numerical scheme (`numerics:`) nor a property of the fluid as a whole
  (`fluid:`). The same category reasoning TASK-041 used to refuse
  filing viscosity under `numerics:`.
- **`simulation.scalar_pattern` migrates into it and the break is
  loud.** Leaving it would leave two ways to declare a transported
  field. `examples/golden-demos/passive_scalar_transport.yaml` and
  `heat_diffusion.yaml` both set it today and are both migrated in the
  same change.
  - **There are two fields called `scalar_pattern`, and only one of
    them moves.** `FieldDisplayConfig.scalar_pattern` seeds one static
    rendered frame and takes a different closed set of values
    (`radial_gradient` among them); `SimulationConfig.scalar_pattern`
    seeds a live transported field. `examples/golden-demos/
    field_display.yaml` sets the *display* one and must keep working
    untouched. Found by checking which demo configs set the field rather
    than assuming, and recorded here because the two obvious ways to
    implement the loud break are both wrong on this point: a rejection
    keyed on the bare key name would break `field_display.yaml`, and a
    message reading "`scalar_pattern` has moved" would be actively
    misleading to whoever is reading it about the other one.
- **Gravity is one property of the run, on `fluid:`; the buoyancy
  coupling's own coefficients are per-field.** A domain has one gravity
  vector and any number of fields that respond to it, so putting `g` on
  each field's declaration would invite two fields to disagree about
  which way is down. The coupling's reference value and coefficient are
  properties of the *field*, and belong with it -- which is also what
  keeps Criterion 4's "one coupling" claim expressible: two declarations
  in one file, one implementation behind them.
- **The renderer's field is named, not inferred.** With one scalar there
  was nothing to choose; with four there is, and inferring it (first
  declared, alphabetically first) is a rule a reader has to know rather
  than read.

**Three further decisions made while implementing, not anticipated by
the bullets above:**

- **`fields:` is a list of declarations, each carrying its own `name`,
  not a mapping keyed by name.** A mapping reads more naturally in YAML,
  but `PyYAML`'s `SafeLoader` silently keeps only the *last* value for a
  duplicate mapping key -- which would make "two declared fields with
  the same name" (Acceptance Criteria, below) undetectable rather than a
  rejectable condition, since only one entry would ever reach Python at
  all. A list lets `_validate_field_declarations` see every declaration,
  including a duplicate one, and reject it with a named error.
- **`FieldConfig.diffusion_coefficient`, not `diffusivity`.** Named to
  mirror `FluidConfig.diffusion_coefficient` exactly -- the same
  physical quantity, this field's own override of that default, read
  through the same `coefficient_overrides` mechanism
  (`CentralDifferenceDiffusion`, TASK-031b) `bootstrap.py` already
  builds for velocity's own viscosity override. A different name for the
  same quantity would read as two concepts where there is one.
- **Reserved names (`"pressure"`, `"velocity.0"`, `"velocity.1"`) are
  hardcoded in `schema.py`, not imported from `engine`.** `configuration`
  has no dependency on `engine` (Stage 0's own layering, `docs/planning/
  roadmap.md` TASK-005); both names are fixed conventions stated once in
  their own modules' docstrings (`PressureField`, `VectorField.
  component_name`), not values that could drift independently of this
  constant.

### Artifacts Produced

- `tests/features/field_declaration.feature` -- this task's Acceptance
  Criteria. Bound from `tests/unit/`, per that directory's own scope:
  every scenario is a configuration loading or failing to load, and one
  end-to-end run; none needs a rendered frame.
- `src/pyflow/configuration/schema.py` -- the `fields:` section, its
  per-field validation, the `scalar_pattern` migration and its loud
  failure, and the rendered-field selector. **Not `fluid.gravity`,
  despite an earlier draft of this bullet naming it here** -- TASK-035's
  own Artifacts Produced section adds `fluid.gravity` and the per-field
  buoyancy coupling's own fields "on the surface TASK-042 built," and
  this task's Acceptance Criteria below test neither gravity nor a
  buoyancy coefficient. Caught before either task's own share was built,
  2026-08-30.
- `src/pyflow/bootstrap.py` -- builds the declared fields instead of one
  hardcoded `"tracer"`, and assembles the per-field diffusivity override
  map from the declarations rather than from `velocity_solved`.
- `tools/generators/generate_config_template.py` -- `FIELD_COMMENTS`/
  `SECTION_COMMENTS` for the new section, per
  `src/pyflow/configuration/CLAUDE.md`'s standing rule that the template
  stays current as the schema evolves. `make check-config-template`
  gates this.
- `examples/golden-demos/passive_scalar_transport.yaml` and
  `heat_diffusion.yaml` -- migrated to the new section.

### Acceptance Criteria

`tests/features/field_declaration.feature` is the criteria
(`adr/ADR-007-executable-acceptance-criteria.md`). **A task that
computes nothing still owes one, for the reason TASK-041's entry already
records**: Criterion 8 says every task, ADR-007's Stage 3 exemption is
for criteria with no user-observable behaviour, and loading a
configuration is user-observable. Written to cover, at minimum:

- A configuration declaring four named fields loads, and a run
  transports all four in one step -- Criterion 1's first bullet, and the
  one scenario that cannot be satisfied by a surface that merely parses.
- A configuration still setting `simulation.scalar_pattern` fails with
  an error naming the field's new home -- the loud break, and this
  task's own headline, mirroring TASK-041's central criterion.
- **And a configuration setting `field_display.scalar_pattern` still
  loads and renders unchanged**, in the same scenario file. The
  same-named sibling field that does not move (see the design decision
  above); without this scenario the criterion above is satisfied by a
  check on the bare key name, which would break
  `examples/golden-demos/field_display.yaml`.
- Two declared fields with the same name are rejected with a named
  error.
- A declared field whose name collides with a velocity component
  (`VectorField.component_name`) or with the pressure field is rejected
  with a named error. **The velocity half is not hypothetical**: the
  transport path is keyed on field name, so a field declared as
  `velocity.0` would silently become momentum's own component.
- A declared field with a non-positive diffusivity is rejected, mirroring
  `FluidConfig`'s existing checks on `viscosity`/`diffusion_coefficient`.
- An unknown initial-condition pattern for a declared field is rejected,
  naming the field and the valid patterns.
- Each rejection above happens at configuration load, with the field
  named in the message -- not as a `KeyError` inside `bootstrap`. The
  accessor half of `docs/practices.md`'s "rejection criteria stop at the
  constructor", which this task needs because the surface is new.
- A declaration that names which field the renderer colours produces
  that field's colour map, and naming an undeclared field is rejected.

Per-field type validation stays in `tests/unit/test_configuration.py`
beside its siblings, the same split TASK-041 used.

### Discharges

Criterion 12, the declaration surface and the migration. Criterion 1's
configuration half (its measurement half belongs to TASK-037/038).
Criterion 7, five of its six named surfaces. Criterion 3's configuration
half. Criterion 8, its own feature file.

---

## TASK-035

Temperature

**Status: Done, 2026-08-30.** Artifact: `src/pyflow/physics/buoyancy.py`.
Two findings surfaced while implementing, neither anticipated by the
sections below:

- **`engine/numerics/assembly.py` cannot import `BoussinesqBuoyancy` to
  register it, unlike every other name this module registers** --
  `engine/CLAUDE.md`'s own opening line ("independent of any specific
  physics") forbids it, since the concrete class deliberately lives in
  `physics/`, not `engine/numerics/`. **This finding was recorded here
  once already, with the wrong fix.** The first version had `bootstrap.py`
  call `register_source_term("boussinesq_buoyancy", BoussinesqBuoyancy)`
  from inside its own `bootstrap()` function body -- which addressed
  *where* the call could live but not *when* it ran: the name resolved
  only after `bootstrap()` had actually executed once in the process,
  unlike every one of `adr/ADR-003`'s six components, self-registered the
  instant `assembly.py` is imported. Found by a direct question about the
  consequences of that placement, asked after this task's own PR was
  first reported ready, not by a test -- `assemble_numerics(NumericsConfig
  (source_term="boussinesq_buoyancy"))`, called with no prior `bootstrap()`
  call, raised `UnknownSchemeError`. **Corrected in the same task, before
  merge**: `physics/buoyancy.py` now self-registers at its own module
  scope, the identical pattern every other concrete scheme already uses,
  and `bootstrap.py`'s own pre-existing import of the class is what
  triggers it -- no call inside a function body at all.
  `tests/integration/test_boussinesq_buoyancy_registration.py` (new)
  pins the corrected behaviour in a fresh subprocess, the only way to
  genuinely prove "resolvable without `bootstrap()` ever running", the
  same reasoning `test_import_order.py` already established. Recorded in
  `assembly.py`'s, `source.py`'s, `bootstrap.py`'s and `physics/
  CLAUDE.md`'s own docstrings, where a reader meets it regardless of
  which module they open first.
- **This task builds two brand-new golden demos, and the Artifacts
  Produced section below names only one feature file
  (`temperature_field.feature`) for the whole task.** Every prior task
  that built a brand-new demo (TASK-030, TASK-034) gave each of its own
  demos a dedicated `.feature` file rather than folding a new demo's
  claims into a mechanism-level one -- followed here for the same
  reason, rather than silently deviating from precedent: `tests/features/
  heat_transport.feature` and `tests/features/thermal_buoyancy.feature`
  are both real artifacts of this task, alongside
  `temperature_field.feature`.

**Intent:** the first field added *after* the architecture claimed to be
field-centric, so the measure of success is how little else changes.
A criterion counting the lines this task adds outside `physics/` is a
legitimate and probably better test of the stage's goal than anything
about temperature itself.

**Also:** buoyancy coupling has a sign, and
`docs/handbook/physics/buoyancy.md` had it inverted in prose for days
before the 2026-08-18 review caught it. A "heat rises" direction check
is an acceptance criterion, not a nicety.

**Read against the resolved design questions (2026-08-30): this is the
one task in Stage 6 that is not a zero-engine-change task, and saying so
plainly is better than letting its own intent line above read as a
promise it cannot keep.** Design question two settled that implementing
`SourceTerm` is the interface arriving at its predicted consumer rather
than new machinery -- but the wiring is real, and Criterion 2 bounds it
to three specific changes precisely so that "how little else changes"
stays measurable for the tasks after this one.

### Purpose

Add a named temperature field, and with it the one coupling this stage
needs: a Boussinesq body force that turns a temperature difference into
vertical motion, reaching momentum through `SourceTerm` -- the Stage 3
interface that has had no implementation, no registry entry and no
consumer since it was written.

### Dependencies

TASK-042 (the declaration surface), TASK-034 (`navier_stokes_step`, the
timestep a body force enters), TASK-018 (`SourceTerm`), TASK-021
(`assemble_numerics` and its registries), TASK-025 (`RK4Integrator` --
the source contribution is evaluated inside `derivative`, so it is
re-evaluated at each of RK4's stages, unlike Stage 5's pressure
projection which sits outside the integrator entirely).

### The sign, derived here rather than left to the implementer

`docs/handbook/physics/buoyancy.md` gives the Boussinesq body force as
`f = (rho - rho_0) g`, approximately `-rho_0 beta (T - T_0) g`, with `g`
the gravitational acceleration **vector, pointing downward**. PyFlow's
momentum equation is per unit mass -- `fluid.viscosity` is used as a
kinematic diffusivity by `CentralDifferenceDiffusion`, not a dynamic one
-- so the per-unit-mass form is what this task implements, and both
couplings this stage needs are the same expression:

> `f = c * (phi - phi_0) * g`, with `c = -beta` for a temperature field
> and `c = +1 / rho_0` for a density field.

Worked through in both directions, because a sign that reads coherently
is exactly the defect this repository already found once in this
document's prose. With `g = (0, -9.81)`: a warm parcel has `T > T_0`, so
`f = -beta (T - T_0) (0, -9.81) = (0, +9.81 beta (T - T_0))`, which
points **up** -- warm fluid rises. A heavy parcel has `rho > rho_0`, so
`f = ((rho - rho_0) / rho_0) (0, -9.81)`, which points **down** --
dense fluid sinks. Both correct, from one expression, which is why
Criterion 4's "one coupling, not one per field" is a real claim about
this stage's code rather than a hope.

**The single expression is the design decision, not an implementation
convenience.** Two implementations that happen to agree in sign today
would satisfy every scenario TASK-035 can write and fail Criterion 4 the
moment TASK-036 needs its own; that is why TASK-036's criteria check the
*object*, not only the direction.

### Artifacts Produced

- `tests/features/temperature_field.feature` -- this task's Acceptance
  Criteria for the engine mechanism itself.
- `tests/features/heat_transport.feature` and `tests/features/
  thermal_buoyancy.feature` -- this task's own two brand-new golden
  demos' acceptance criteria, not named here when this bullet list was
  first drafted (found while implementing -- see the Status note above).
- `src/pyflow/physics/buoyancy.py` -- `BoussinesqBuoyancy(SourceTerm)`,
  the first concrete implementation of a numerics interface to live
  outside `engine/numerics/` (design question four, resolved above, with
  the reason recorded in that module's own docstring where a reader
  meets it).
- `src/pyflow/engine/numerics/source.py` -- `SourceTerm.source` widens
  to take the state mapping alongside the field (design question six,
  resolved 2026-08-30). The one interface signature change Criterion 2
  permits this stage, and the reason belongs in that module's own
  docstring where a reader meets it.
- `adr/ADR-010-source-term-state.md` -- that widening's own ADR, the
  third Stage 3 interface change to get one (`adr/ADR-008-time-
  integrator-derivative-callable.md`, `adr/ADR-009-pressure-coupling-
  dt.md`), written by the task that makes the change as both of those
  were.
- `src/pyflow/engine/simulation.py` -- `step`'s `derivative` gains the
  source contribution, passing it the same `state` it was called with,
  so the term is re-evaluated at each of RK4's stages rather than held
  from the step's opening state.
- `src/pyflow/engine/numerics/assembly.py` -- a seventh registry and the
  `AssembledNumerics` field carrying the assembled source term.

Four engine files, which is Criterion 2's whole permitted diff for this
stage. Anything else under `src/pyflow/engine/` that this task touches
is a finding.
- `src/pyflow/configuration/schema.py` -- `fluid.gravity` and the
  per-field buoyancy coupling's own fields, on the surface TASK-042
  built.
- `src/pyflow/physics/CLAUDE.md` and `src/pyflow/physics/__init__.py` --
  both opened by stating this package was empty until Stage 6 and empty
  on purpose. **This is the task that made those sentences false, so it
  is the task that rewrote them**, in the same change, rather than
  leaving them for the exit audit (Criterion 11) -- done: both now open
  with "No longer empty as of TASK-035."
- `docs/architecture/overview.md` -- its two "physics/ still empty
  (Stage 6)" claims, same reasoning.
- `examples/golden-demos/heat_transport.yaml` and
  `examples/golden-demos/thermal_buoyancy.yaml` -- two of this stage's
  three golden demos, with their entries in
  `docs/implementation/golden-demos.md`.
- `tests/integration/test_boussinesq_buoyancy_registration.py` -- not
  anticipated when this list was first drafted, added while correcting
  the registration-timing defect this task's own Status note records
  above.

### Acceptance Criteria

`tests/features/temperature_field.feature` is the criteria. Written to
cover, at minimum:

- A named temperature field transports and diffuses at its own
  configured thermal diffusivity, checked against the analytic decay
  rate of a sinusoidal mode -- **and agreeing, to a stated tolerance,
  with the result Stage 5's Heat Diffusion demo already gets from an
  anonymous scalar.** The agreement is the criterion, not the decay: it
  is the entire content of this stage's claim that naming a field costs
  nothing.
- **Warm fluid rises.** A warm patch in an otherwise still, uniform
  domain acquires an upward vertical velocity within a stated number of
  steps, with the expected sign derived above rather than read off the
  implementation.
- **Reversing gravity reverses the motion**, from configuration alone.
  The check that says the sign came from physics and not from a constant
  that happens to be right.
- **The null case is exact.** With a uniform temperature field -- no
  difference for the force to act on -- the velocity field is identical,
  element by element, to the same run carrying no temperature field at
  all. A tolerance would pass a term leaking a small spurious force;
  equality will not.
- **The configured source term is the one the timestep calls**, checked
  by registering a test double under a name the configuration selects
  and observing the timestep's result change -- Stage 5 Criterion 13's
  own substitution mechanism, applied to this stage's seventh seam. A
  timestep that constructs `BoussinesqBuoyancy` directly passes every
  other scenario here and retires ADR-003's claim for the one component
  this stage adds.
- **Rayleigh-Bénard convection: rolls form when the layer is heated from
  below and do not when it is heated from above.** The qualitative bar
  design question five settled on, stated with the deferral visible: the
  critical Rayleigh number (approximately 1708, rigid-rigid) is not this
  stage's bar and is not silently absent -- the feature file says so
  where a reader meets the scenario.
- A buoyancy coupling declared in a run whose velocity is *not* solved
  is rejected at configuration load -- a body force with nothing to act
  on, which loads cleanly and does nothing today. Criterion 7's sixth
  surface, and the one that belongs here rather than to TASK-042,
  because only this task knows the coupling exists.
- **No `"temperature"` string literal anywhere in
  `inspect.getsource(simulation)`** -- Criterion 1's structural check,
  the same assertion `velocity_field_support.feature` already makes for
  `"velocity"`. The widened `SourceTerm` signature is what makes this
  passable: the orchestrator hands the source term the whole state and
  the *phenomenon* decides which field drives which, so the orchestrator
  never needs to know a temperature field exists.
- **A field with no source term configured is advanced exactly as it is
  today.** Every scenario Stages 4 and 5 wrote runs unchanged, and a run
  with no buoyancy declared produces bit-identical results to the same
  run before this task -- the regression guard for putting a new term
  inside `derivative`, which every existing field now passes through.

### Discharges

Criterion 4, the implementation half (TASK-036 closes the claim).
Criterion 2, entirely -- this is the only task permitted to touch
`src/pyflow/engine/`, and the exit audit measures its diff against the
three permitted changes. Criterion 6, the analytic decay rate, the
buoyancy sign and convection onset. Criterion 11, the four claims this
task falsifies. Criterion 12, gravity and the coupling's own fields.
Criterion 7's sixth surface. Criterion 8, its own three feature files
(`temperature_field.feature` plus one per golden demo -- found necessary
while implementing, see the Status note above).
Criterion 9, two of three demos.

---

## TASK-036

Density

**Status: Done, 2026-08-30.** Artifact: `tests/features/density_field.feature`.
Genuinely zero lines under `src/pyflow/` -- verified directly via `git
diff --stat main -- src/pyflow/`, not merely expected: `BoussinesqBuoyancy`
needed nothing new to drive a second field, confirming Criterion 4's own
claim rather than merely restating it. **This task's own "committed
configuration declaring a density field with its own buoyancy coupling"
(Artifacts Produced, below) is the one bullet in this stage with no exact
path named**, unlike every golden demo bullet elsewhere -- resolved as
YAML content embedded directly in `tests/unit/test_density_field.py`
(`_TWO_COUPLINGS_CONFIG`), written to a real file via `tmp_path`: no
golden demo exists for Density (Criterion 9 names only Heat Transport,
Smoke Transport and Thermal Buoyancy), so there is no `examples/`
location this content would otherwise belong under. Recorded as the
reading chosen, per this project's own practice of stating which of two
admissible readings a criterion was built against.

**Intent:** density enters the momentum equation, so unlike temperature
it is not a passive addition. The criterion that matters is whether a
variable-density configuration conserves mass, not whether the field
exists.

**Read against design question three, resolved 2026-08-30: this stage is
Boussinesq, so "conserves mass" here means the density field's own
domain integral is conserved by its transport -- not that continuity has
been generalised.** The intent line above admits the stronger reading,
and the stronger reading is a different solver: it would replace Stage
5's divergence-free constraint, its pressure equation and its corrector,
inside a stage whose goal is that nothing changes. Recorded rather than
quietly narrowed, so that a reader meeting the 2026-08-22 sentence knows
which of its two readings this stage built.

**This task's real subject, after that answer, is Criterion 4.** It is
what turns TASK-035's buoyancy implementation from an implementation
into a claim: a second field, with a physically different coefficient,
driving motion through the same object.

### Purpose

Add a named density field that drives motion through the coupling
TASK-035 already built, and show that doing so takes no second
implementation and no engine change.

### Dependencies

TASK-042 (the declaration surface), TASK-035 (`BoussinesqBuoyancy`,
`fluid.gravity`, and the source-term wiring). Nothing else -- and the
absence is the point: if this task needs anything under
`src/pyflow/engine/`, Criterion 2 has failed and the finding belongs in
the exit audit rather than in a quiet commit.

### Artifacts Produced

- `tests/features/density_field.feature` -- this task's Acceptance
  Criteria.
- A committed configuration declaring a density field with its own
  buoyancy coupling.
- **Expected: zero lines under `src/pyflow/`.** Stated as an expectation
  rather than a certainty, since the coefficient this task needs
  (`c = +1 / rho_0`) is a value on a surface TASK-035 already built and
  should require nothing new. A nonzero count is a Criterion 4 finding
  and is reported as one.

### Acceptance Criteria

`tests/features/density_field.feature` is the criteria. Written to
cover, at minimum:

- **Dense fluid sinks.** A denser patch in an otherwise still, uniform
  domain acquires a downward vertical velocity -- the mirror of
  TASK-035's rising warm patch, and a scenario that fails if the shared
  coupling's coefficient convention was wrong in the direction that
  temperature alone could not detect.
- **The same object drives both.** A configuration declaring a
  temperature field and a density field together reaches one
  `BoussinesqBuoyancy` implementation for both, checked by substituting
  a registered test double and observing *both* couplings change. Two
  implementations that agree in sign pass every direction check above
  and fail this one, which is why Criterion 4 is written about the
  object rather than the behaviour.
- **The density field's domain integral is conserved** by its own
  transport, to a stated tolerance, on a periodic domain with no source
  -- and the scenario says in the feature file which reading of
  "conserves mass" this is, and which it is not.
- **Continuity is unchanged.** A run carrying a density field produces
  the same divergence behaviour as one without: the corrector still
  drives cell divergence to the configured tolerance. The executable
  form of design question three's exclusion, and the scenario that would
  fail if somebody started generalising continuity halfway.

### Discharges

Criterion 4, the claim half -- the criterion is not closed by TASK-035
alone and says so. Criterion 6, density's own conservation and sink
direction. Criterion 1, its share of the zero-lines measurement.
Criterion 8, its own feature file.

---

## TASK-037

Humidity

**Status: Done, 2026-08-30.** Artifact: `tests/features/humidity_field.feature`.
Genuinely zero lines under `src/pyflow/` -- verified directly via `git
diff --stat main -- src/pyflow/`, not merely expected: the same finding
TASK-036 made for density, now confirmed for a second, unrelated field --
`coefficient_overrides`/`field_values`/`field_gradients` needed nothing
new to carry a second scalar and a second wall value, and
`_add_declared_field_transport` (TASK-042) already transports every
`config.fields` entry together with no per-field code path. Four
scenarios: the two-field decay-rate check (Criterion 3's first bullet,
`coefficient_overrides` proven to generalise past momentum for the first
time with two *non-buoyant* fields rather than temperature/density's
own buoyancy-coupled pair), the `field_values` wall check (Criterion 3's
second bullet, the first scenario anywhere to exercise
`BoundaryFaceConfig.field_values`/`field_gradients` through real
`load_config` -> `assemble_numerics` for two named scalars rather than
constructing `DirichletBoundaryCondition` by hand the way
`velocity_field_support.feature` does), the pure-advection conservation
check (Criterion 6, `density_field.feature`'s own shape applied to
humidity), and the no-cross-field-leak check (a regression guard: running
the identical configuration with and without a declared humidity field
leaves temperature bit-identical). The `field_values` scenario's own
mutation check (deliberately dropping `field_values` from
`_dirichlet_boundary_condition`'s constructor call) was run and confirmed
to fail before being trusted, the same discipline every other Stage 4/5/6
task in this document records.

**Intent:** as TASK-035 -- a transported scalar whose value is mostly
that it needed no new machinery. If it does need new machinery, that is
the finding, and it belongs in the stage's exit audit rather than being
absorbed quietly.

**Read against the criteria (2026-08-30): this is one of the two tasks
this stage's goal is actually measured on.** It has no coupling, no
engine dependency and no new physics -- `docs/handbook/physics/
humidity.md` says so directly ("species transport needs no new numerical
machinery"). Its entire content is that the claim holds.

### Purpose

Add a named humidity field, transported alongside temperature at its own
mass diffusivity, taking its own value at a shared wall -- the first
real test of whether Stage 5's per-field coefficient and boundary
mechanisms generalise past momentum.

### Dependencies

TASK-042 (the declaration surface). TASK-035 only for the temperature
field its two-field scenarios run alongside, not for any mechanism.

### Artifacts Produced

- `tests/features/humidity_field.feature` -- this task's Acceptance
  Criteria.
- A committed configuration declaring a humidity field alongside a
  temperature field, at different diffusivities and with different
  values at the same wall.
- **Expected: zero lines under `src/pyflow/`.** Criterion 1's
  measurement, read from `git diff --stat` for `src/pyflow/` across this
  task's branch.

### Acceptance Criteria

`tests/features/humidity_field.feature` is the criteria. Written to
cover, at minimum:

- **Two fields transported in one run at different diffusivities each
  diffuse at their own rate**, each measured against the analytic decay
  rate of a sinusoidal mode -- not merely observed to differ, since two
  wrong rates also differ. Criterion 3's first bullet, and the first
  time `coefficient_overrides` carries anything but momentum.
- **Two fields take different values at the same wall**, through
  `BoundaryFaceConfig.field_values`/`field_gradients` -- the surface
  TASK-031c built for velocity's two components and nothing else has
  used since.
- **Species mass is conserved**: the humidity field's domain integral is
  unchanged, to a stated tolerance, under pure advection on a periodic
  domain with no source.
- **Humidity does not perturb temperature.** Running the same
  configuration with and without the humidity field leaves the
  temperature field identical, element by element. A shared diffusion
  scheme dispatching on field name is exactly where a leak between two
  fields would live, and nothing has ever checked it.

### Discharges

Criterion 3, the behavioural half. Criterion 6, species mass
conservation. Criterion 1, its half of the zero-lines measurement.
Criterion 8, its own feature file.

---

## TASK-038

Passive Tracers

**Status: Done, 2026-08-30, this stage's own last task.** Artifacts:
`tests/features/passive_tracers.feature` (three scenarios),
`tests/features/smoke_transport.feature` (two scenarios), and
`examples/golden-demos/smoke_transport.yaml`. Genuinely zero lines under
`src/pyflow/` -- verified directly via `git diff --stat main --
src/pyflow/`, the same finding TASK-036/037 each made: `fields:`
declaring more than one scalar, `coefficient_overrides`, and
`_add_declared_field_transport`'s own generic multi-field handling
(TASK-042) already carry a tracer exactly the way they carry any other
declared field.

**A real gap found while auditing Criterion 1's own structural bullet,
fixed in this task's own change rather than left for the (separate)
exit audit to rediscover**: no earlier Stage 6 task's own Discharges
claimed "no `"density"`, `"humidity"` or `"tracer"` string literal in
`inspect.getsource(simulation)`" -- only `"velocity"` (TASK-031) and
`"temperature"` (TASK-035) were ever checked, and `grep` confirmed the
claim was true but unasserted for the other three. Added as a fourth
`passive_tracers.feature` scenario, checking all four literals at once.

**This task's own two feature files are two, not one, the same
TASK-035-shaped gap TASK-036/037 each avoided by having no second demo
to name.** This task's own Artifacts Produced bullet (below) named only
`passive_tracers.feature`; `smoke_transport.feature` (bound from
`tests/golden/`, per every other golden demo's own precedent) is a
second real artifact the demo itself needed, found while implementing.

**This stage's exit audit is deliberately not in this change** -- see
this task's own Artifacts Produced bullet below, and Stage 5's own
precedent (a separate `audit/stage-5-exit` pass, after TASK-034's PR
merged, found eight overstated verdicts). Stage 6's own
Completion Criteria section still reads as drafted, with no
"Status as of..." verdict table, until that separate pass runs.

**Intent:** "passive" is the testable word: a tracer must have **no
measurable effect on the velocity field**. Checked by running the same
configuration with and without tracers and comparing the velocity field
exactly -- the only check that can fail.

**Also (2026-08-30): this is the stage's last task, so it owns the
stage-level criteria** -- the CI evidence, the documentation sweep, the
step-definition count and the exit audit -- named here when the criteria
were written rather than discovered at the end
(`docs/practices.md`, "Criteria that no task can own get one anyway").

### Purpose

Add passive tracers, and close the stage: the Smoke Transport demo, the
exactness of "passive", and the stage-level evidence no earlier task can
produce.

### Dependencies

TASK-042 (the declaration surface). TASK-034 (`navier_stokes_step`) for
the solved velocity a tracer is carried by. No mechanism dependency on
TASK-035..037.

### Artifacts Produced

- `tests/features/passive_tracers.feature` -- this task's Acceptance
  Criteria for the engine mechanism itself.
- `tests/features/smoke_transport.feature` -- this task's own golden
  demo's acceptance criteria, not named here when this bullet list was
  first drafted (found while implementing -- see the Status note above).
- `examples/golden-demos/smoke_transport.yaml` -- this stage's third
  golden demo, with its entry in `docs/implementation/golden-demos.md`.
- **Expected: zero lines under `src/pyflow/`**, on the same measurement
  as TASK-037.
- This stage's exit audit, written into this document's own Stage 6
  status section, per-criterion, under `prompts/common/AUDITOR.md`'s
  stance and in a separate pass from the session that closes the task
  -- the arrangement Stage 5's audit demonstrated the value of by
  finding eight overstated verdicts.

### Acceptance Criteria

`tests/features/passive_tracers.feature` is the criteria. Written to
cover, at minimum:

- **The same configuration run with and without the tracer produces
  velocity fields that agree exactly, element by element** -- not to a
  floating-point tolerance, which a genuinely coupled tracer could also
  satisfy on a short enough run.
- **And the tracer is not inert:** in the same scenario, the tracer
  field itself changes -- it is advected somewhere. Without this the
  scenario above is passed perfectly by a tracer the engine ignores
  completely.
- **Several tracers at once behave as several**, each carried by the
  same velocity and none affecting another -- the multi-field case
  Criterion 1's first bullet asks for, exercised where it is cheapest to
  check.
- The Smoke Transport demo runs from committed configuration and meets
  `docs/implementation/golden-demos.md`'s Definition of Done.

### Discharges

Criterion 5, entirely. Criterion 9, Smoke Transport. Criterion 10, with
a named `gh run view` run id on both `ubuntu-latest` and
`windows-latest`. Criterion 11, the stage-wide sweep and
`make check-claims`. Criterion 8, its own feature file and the
step-definition count. Criterion 1, the multi-field run.

---

### Golden Demos

Stage-level, not TASK-038's. **The list sat directly beneath TASK-038
with no heading of its own until 2026-08-30, and two documents had
already read it as that task's** -- `docs/planning/backlog.md` and
`docs/planning/implementation-plan.md` both cite "TASK-038's 'Thermal
buoyancy' golden demo", which is a demo TASK-035 owns. Both citations
are corrected in the same change as this heading. A list that is
indistinguishable from the section above it will be read as belonging to
it.

- Heat transport (a named Temperature field, with buoyancy coupling) --
  TASK-035
- Smoke transport -- TASK-038
- Thermal buoyancy -- TASK-035

**This list read "Heat diffusion" until 2026-08-28**, when Stage 5's own
Completion Criteria took ownership of that demo (maintainer's call, Stage
5 Criterion 8): `docs/implementation/mvp.md` requires the MVP to
reproduce heat diffusion, the MVP is Stage 5, and heat diffusion is the
diffusion equation on a transported scalar -- no Temperature field
needed. What is left here is the genuinely different claim, and the one
this stage's own goal is about: a *named* field with its own physical
coupling adds no new machinery. Rewriting the bullet rather than deleting
it, because the demo is not gone -- it is reused, the same way
`docs/planning/implementation-plan.md` reuses Taylor-Green vortex between
Levels 2 and 4.

**Three documents named three different lists until 2026-08-30**, found
by reading them side by side while drafting Criterion 9 rather than one
at a time. Only one of the three demos was carried everywhere:
**Heat Transport** already had a second `validates` edge on
`planning/data/demos.yaml`'s `demo-heat-diffusion` and a parenthetical
on that demo's Golden Demos table row, the same reuse-at-a-later-Level
pattern Taylor-Green follows between Levels 2 and 4. **Smoke Transport**
appeared only in `docs/planning/implementation-plan.md` Level 3's
Golden Demo prose, with no table row and no graph entity. **Thermal
Buoyancy** appeared only here and in that document's Rayleigh-Bénard
paragraph, which cites it as "already named under `docs/planning/
roadmap.md`" -- named here and nowhere that a reader looking for the
demo list would find it. Reconciled in the same change rather than left
for TASK-035 to trip over: both now have Golden Demos table rows and
`demos.yaml` entities with `validates` edges to Capability Level 3, and
Level 3's own Golden Demo list names all three. Rayleigh-Bénard stays
where it is, as this stage's validation case rather than a fourth golden
demo, and Criterion 6 records that its critical-Rayleigh-number
comparison is deferred to Stage 8 (Better Numerics) at the earliest.

---

## TASK-043

`pyflow run --demos` Shortcut

**Numbered out of sequence, deliberately, the same shape TASK-039
already established** (see that task's own entry, above): the next free
number at the time this was drafted, placed physically here -- after
Stage 6's own task list closes, before Stage 7 (Rendering Annotations)
opens -- because that is where it belongs by reading order, not because
it depends on anything Stage 6 built. **Drafted on a separate branch
from TASK-044 (Stage 7's own substantive content) at the same time,
merged together 2026-09-01**: the two numbers turned out not to
collide, so this is the actual final placement, not a provisional one
awaiting a renumber.

**Status: Done, 2026-08-31.**

### Purpose

Running a golden demo requires typing the full path every time --
`pyflow run --config examples/golden-demos/lid_driven_cavity.yaml`.
Maintainer's own request: a shortcut, `pyflow run --demos
<name-or-number>`, with `pyflow run --demos` alone listing what is
available and an unresolvable name or number rejected outright.

### Dependencies

None. Pure CLI ergonomics over the existing `--config`/`bootstrap()`
path -- no engine, physics, or rendering change.

### Design decisions, recorded here

**Not simulation work, so `adr/ADR-007-executable-acceptance-criteria.md`
does not apply here, despite this task's own number being well past
Stage 4.** ADR-007's own Decision section scopes itself explicitly --
"Stage 4 onward... which is where physics begins and therefore where
'real simulation work' begins" -- to work with physical behaviour to
describe. Resolving a CLI flag to a config path has none, the same
"architecture, not behaviour" reasoning the ADR's own Stage 3 exemption
already uses for a different kind of non-physics task. Plain pytest
(`tests/unit/test_golden_demos.py`, `tests/unit/test_main.py`,
`tests/integration/test_cli.py`) is the same category `generate-config`
(TASK-039) already used -- TASK-039 predates the ADR by a day, but the
ADR's own scope, not the calendar, is why both stay this way.

**A curated, explicit registry (`src/pyflow/configuration/
golden_demos.py`'s `_GOLDEN_DEMOS`), not a sorted directory listing.** A
first draft derived both name and number from
`examples/golden-demos/*.yaml` directly (alphabetical sort, filename
stem as name) -- simpler, and self-updating, but it makes the number
unstable (a demo inserted alphabetically ahead of existing ones
reshuffles every later number) and ties the exposed name to whatever a
YAML file happens to be called. Revised after the maintainer asked for
both a stable number and a name that is deliberately short-but-
descriptive: `_GOLDEN_DEMOS` is instead an ordered, hand-maintained
`(name, filename)` list -- a demo's number is its fixed position
(appended, never inserted), and its name is chosen independently of the
underlying filename (`numerics_assembly.yaml` -> `numerics`,
`passive_scalar_transport.yaml` -> `passive_scalar`).

**That registry is a second source of truth, and the trade-off is
recorded, not hidden.** `test_registry_matches_golden_demos_directory`
(`tests/unit/test_golden_demos.py`) is the mechanical guard against it
drifting from `examples/golden-demos/` -- the same `check-manifest`/
`check-inventory` shape this repository already uses for every other
generated/derived-data pair, failing `make test` the moment a real
`.yaml` file and the registry disagree.

**`--config`/`--demos` are an `argparse` mutually exclusive group, not a
hand-written check.** Passing both is rejected by `argparse` itself
(`"not allowed with argument"`), the same "let the library express the
constraint" preference this project applies wherever it can.

### Artifacts Produced

- `src/pyflow/configuration/golden_demos.py` -- `_GOLDEN_DEMOS`,
  `list_golden_demos()`, `resolve_golden_demo(identifier, base_dir=...)`,
  `format_golden_demos_listing()`, `UnknownGoldenDemoError`.
- `src/pyflow/__main__.py` -- `run_parser` gains a mutually exclusive
  `--config`/`--demos` group; `--demos` bare (`nargs="?"`, sentinel
  `const`) lists demos and exits without calling `bootstrap()`; a
  resolved `--demos <value>` feeds `bootstrap()` exactly where
  `args.config` already did. Top-level and `run` subcommand `epilog`s
  updated with `--demos` examples, per `src/pyflow/CLAUDE.md`'s
  CLI-self-description rule.

### Acceptance Criteria

- `pyflow run --demos` (no value) lists every registered demo's number
  and name, and does not call `bootstrap()`.
- `pyflow run --demos <number>` and `pyflow run --demos <name>` each
  resolve to the same config `--config examples/golden-demos/<name>.yaml`
  would, checked by a real subprocess run of the resolved config, not
  only that the flag parses.
- An unresolvable number or name is rejected (non-zero exit, message
  naming the bad value) rather than silently falling through to the
  built-in default configuration.
- `pyflow run --config X --demos Y` together is rejected.
- Every real `*.yaml` under `examples/golden-demos/` is registered
  exactly once, and every registered filename exists --
  `test_registry_matches_golden_demos_directory`.

---

# Stage 7 — Rendering Annotations

Goal

Make a running simulation self-explanatory on screen -- what it is, what
the colour map means, how far it has progressed, and how large it is --
without a viewer having to read the config file.

Tasks include

- A HUD module in `src/pyflow/rendering/`: title, timestep and elapsed
  simulated time, cell size, domain size, all in the same world-space,
  camera-following style the existing legend strip already uses
- Numeric labels on the field legend (`value_range`'s endpoints, a
  field/quantity name) -- closing the deferral
  `docs/implementation/golden-demos.md`'s Field Display entry and this
  roadmap's own TASK-017 recorded when pygfx's text rendering had not yet
  been verified live
- An optional physical-unit conversion (a new `units:` config section:
  length/time scale factors and unit labels), so cell size, domain size
  and elapsed time can be shown in real-world units alongside simulation
  units

Golden Demo

The existing Field Display demo, annotated -- title, labelled legend,
timestep/time (once a live-stepping demo exercises it) and cell/domain
size all visible in one frame, run through the same public API every
other golden demo uses.

### Completion Criteria

**Written 2026-09-03, at this stage's exit audit, after its only task
had already closed -- not before its first task, as
`docs/practices.md`'s "A stage gets completion criteria before its first
task" requires.** Stated first because it is this stage's first
finding, not a footnote to it: the checklist that audit works from
(`docs/practices.md`, End-of-session consistency review, step 12) says
in as many words that a stage with no criteria to audit has already
produced its first result. Stages 2, 3, 4, 5 and 6 each had criteria
written before their first task started, which is what the rule asks
for. This stage had none at all --
no criteria, no discharge map, no status line -- which is why
`docs/planning/status.md` could only report it as "no pending tasks
recorded, but isn't marked complete".

**Stage 1 is the precedent, and it is not a reassuring one.** Its
criteria were also written after the fact, and that retrospective audit
found five of its eight unmet -- four of them inside code whose *task*
criteria were fully met. The rule exists because of that outcome. Writing
criteria after the work knows what the work built, and the only honest
defence is to draft them from the **Goal** above and from what a viewer
would observe, then check them against the repository rather than
against TASK-044's own Acceptance Criteria. That is what was done:
every criterion below was written from the Goal's four questions before
the audit read a line of `hud.py`, and three of the eight failed.

**The Goal is four questions a viewer should be able to answer from the
screen** -- what is this, what does the colour map mean, how far has it
got, how large is it -- so the criteria are about whether a frame
answers them, not about whether `hud.py` has the functions to. Every
qualifying clause is its own bullet (`docs/practices.md`, "The intent
lives in the qualifier").

**Stage 3's Gherkin exemption does not extend here, and TASK-044's own
judgement that it did is revisited below** (Criterion 2).
`adr/ADR-007-executable-acceptance-criteria.md`'s scope is "real
simulation work... where physics begins", and rendering annotations are
not physics -- which is why TASK-044 recorded no `.feature` file as a
deliberate, stated gap rather than an oversight, correctly, per that
ADR's own boundary. What the ADR's scope does not settle is the
separate question this stage's own **Golden Demo** entry raises: a
golden demo's criteria are executable regardless of ADR-007, because
every other demo in `tests/features/` already works that way, and this
stage names one.

1. **A viewer of any bundled demo can answer all four of the Goal's
   questions without opening its config file.** The Goal restated as
   the thing that would falsify it, and checked over every demo rather
   than the one that happened to be worked on.
   - **Every demo that renders anything states what it is** -- an
     explicit `rendering.title`, not the schema default `"PyFlow"`,
     which is the application's name and answers nothing about the run.
   - **Every demo that colour-maps a field names the quantity** --
     `field_display.field_label`, or `render_field`'s own name as the
     fallback `_add_hud` already implements. A gradient strip with
     numbers at its ends and no statement of what is being measured
     answers "what does the colour map mean" only for somebody who
     already knows.
   - **Every demo that draws arrows names what they are and how their
     length maps to magnitude** -- `field_display.vector_label`, which
     is what puts `arrow_scale` on screen as a stated conversion. This
     is the exact gap real user feedback named ("presumably velocity or
     something? Neither the direction nor magnitude is clear").
   - **Every demo that renders a mesh view labels both spatial axes** --
     P-019, and in practice `rendering.show_stats` left on, since the
     axis ticks share that gate.
   - **Checked by a sweep over `examples/golden-demos/*.yaml`, not
     demo by demo**, and this bullet is the one that does the work: all
     ten demos complied on the day P-019 was written *because the same
     change fixed all ten*, and nothing would have caught the eleventh.
     A standing rule enforced by memory is `docs/practices.md`'s "A
     checkable trigger still needs somebody to check it".
   - **The sweep itself must be checked for reaching anything**
     (`docs/practices.md`, "A rule that matches nothing reports
     nothing") -- a mis-globbed demo directory makes every check above
     pass by covering nothing.
2. **The annotations are rasterised inside the framed view, checked in
   a real rendered frame.** The stage's own **Golden Demo** entry, taken
   at its word: "all visible in one frame, run through the same public
   API every other golden demo uses."
   - **Checked in pixels, not in scene objects.** A `gfx.Text` present
     in `window.scene.children` with the right content is not the same
     claim as text a viewer can see: text placed outside the camera's
     own bounds satisfies the first and fails the second, and this
     stage widened the framed view four separate times, which is
     exactly the way that goes wrong.
   - **Not pixel-exact, and the reason is stated rather than assumed.**
     Font rasterisation is not reproducible the way this demo's
     flat-coloured cells are (`docs/implementation/golden-demos.md`
     already says so); the checkable claim is that a band of the frame
     which holds one annotation and nothing else is not entirely
     background.
   - **Each band must be shown to hold that annotation and nothing
     else**, by mutation rather than by reading the layout arithmetic:
     a band that also catches the mesh edge or the legend strip passes
     whether or not the text was drawn.
   - **Expressed as Gherkin scenarios**, because this is a golden demo
     and every other golden demo's criteria are
     (`tests/golden/CLAUDE.md`). TASK-044's own "no `.feature` file for
     this stage" note is correct about `adr/ADR-007`'s scope and does
     not settle this.
   - **The step/time readout is deliberately excluded from the pixel
     check, and the exclusion is named here rather than left to be
     noticed.** Field Display is static and has no step/time line at
     all; the aspect-pinned canvas that makes pixel prediction possible
     is unique to it, so no live demo can be checked this way without
     pinning a second one. The live claim -- a step/time line present,
     and different between frames -- stays checked at the rendered text
     in `tests/unit/test_bootstrap.py`, which is where it can be read
     back.
3. **The HUD never states something the frame does not support.** The
   falsifiable half of "self-explanatory", and the half a
   feature-by-feature reading misses entirely: an annotation that
   describes what is *configured* rather than what is *drawn* is worse
   than no annotation, because a viewer has no way to tell.
   - **A vector-scale line appears only where an arrow was actually
     drawn** -- not wherever `vector_pattern` or `velocity_solved` was
     configured. `build_vector_field_arrows` returns `None` for a field
     whose every cell vector is exactly zero, so the two are different
     questions.
   - **Checked in both directions**, which is the qualifier: a fix that
     never claims a scale passes the bullet above and destroys the
     feature. A run whose arrows appear once the flow develops must
     gain the line with them.
   - **Every other HUD element is held to the same standard** -- the
     stats block's step/time line appears only on a live-stepping run,
     the legend's labels only where a legend was drawn.
4. **Every number on screen is in the units the configuration asked
   for.** `units:` is this stage's one new configuration section, and a
   section that states an intention needs a check that something can
   act on it (`docs/practices.md`).
   - **Both halves**, length *and* time. Checked at the rendered text,
     not at the loaded config: a `_format_time` ignoring `time_scale`
     entirely is invisible to a configuration-boundary test.
   - **With distinct factors** (`docs/practices.md`, "Verify a
     conversion where its factors are distinct") -- a scale of 1, or a
     timestep of 1, lets a dropped multiplication pass.
   - **Left at their defaults, the numbers are unchanged from before
     this stage**, so an unconfigured run is not silently rescaled.
5. **The annotation layer is one mechanism, not one per annotation.**
   The architectural claim, and the one that decides whether Stage 8+
   can add an annotation cheaply.
   - **One module**, `rendering/hud.py`, holding plain-values-in,
     `pygfx.Text`-out and nothing else -- no camera, no render loop, no
     number formatting, the same split `mesh_visualization.py`/
     `field_visualization.py` already establish.
   - **One pair of gates**, `rendering.show_title`/`show_stats`, not one
     toggle per element. Axis labels reuse `show_stats` rather than
     adding a third.
   - **No new `adr/ADR-003` component, and no engine change at all.**
     This stage is rendering; a numerics interface that learns what a
     HUD is would be a Criterion 5 failure whatever it bought.
6. **Switching the annotations off restores the unannotated render
   exactly.** The escape hatch has to be real, or the stage has taken
   something away.
   - `show_title: false` with `show_stats: false` draws no HUD text at
     all, and `tests/features/empty_window.feature`'s "every pixel is
     the configured background colour" keeps holding for the one demo
     that asks for it.
   - **And the camera framing is unchanged**, not merely the text
     suppressed -- a HUD that still widens `bounds` when switched off
     would silently rescale every other demo.
7. **The rule this stage produced outlives it.** P-019 was written at a
   user's explicit request for "a standing rule for rendering", and a
   standing rule is a durable claim about every future rendering task,
   not a description of what this one did.
   - It exists as a numbered principle in
     `docs/engineering-principles.md`, with the mechanism recorded in
     `src/pyflow/rendering/CLAUDE.md` rather than restated there.
   - **And something checks it.** Criterion 1's sweep is that check;
     this bullet is here so the two cannot drift apart -- a principle
     whose only enforcement is that somebody remembers it is the shape
     `docs/practices.md` names twice ("A checkable trigger still needs
     somebody to check it", "A rule that matches nothing reports
     nothing").
8. **Documentation describes what now exists**, checked by grep rather
   than by diff review (`docs/practices.md`, "A stage's documentation
   sweep is a grep, not a diff review").
   - `docs/architecture/rendering.md` describes the package as built,
     including every module in it.
   - Any document that enumerates `src/pyflow/rendering/`'s modules
     agrees with the directory -- there is more than one, which is the
     point of grepping rather than reading the diff.
   - `docs/implementation/golden-demos.md`'s Field Display entry no
     longer records the legend-label deferral as open, since this stage
     closed it.
   - `docs/planning/status.md` reports this stage's real state.

### Discharge map

One task, so the map is short -- but it is written the way Stages 3, 4,
5 and 6 wrote theirs, and the second column is the honest half.

**TASK-044 discharges Criteria 1, 4, 5, 6 and 7 as built.** Criteria 2,
3 and 8 were discharged by this exit audit, on 2026-09-03, and each is
recorded as a failure in the table below rather than back-dated into
TASK-044's own entry.

| Criterion | Discharged by |
|-----------|---------------|
| 1. Four questions answerable from the screen | TASK-044 (the ten demo configs), plus this audit's sweep that checks it |
| 2. Annotations rasterised inside the framed view | **This audit** -- TASK-044 checked scene objects only |
| 3. The HUD states nothing the frame cannot support | **This audit** -- TASK-044 shipped a counter-example |
| 4. Numbers in the configured units | TASK-044 (length), **this audit** (time) |
| 5. One annotation mechanism | TASK-044 |
| 6. Switching it off restores the unannotated render | TASK-044 |
| 7. P-019 outlives the stage | TASK-044 (the principle), **this audit** (the check) |
| 8. Documentation describes what exists | **This audit** |

### Status as of 2026-09-03: Stage 7 complete, eight of eight criteria met after the audit's own fixes

**Six of the eight were not fully met when this audit opened, and one
of the six was a defect in shipped behaviour rather than in the checking
of it.** This paragraph said "three" in its first draft, counting only
the criteria whose *headline* failed and quietly rounding off four
qualifier bullets that had no check at all -- which is
`docs/practices.md`'s "At audit time: check the qualifier, not the
headline" being violated by the audit that quotes it. Corrected before
this branch merged, and left visible rather than silently rewritten
(root `CLAUDE.md`'s Integrity section).

**Two of those six failed only in the sense a retrospective criterion
can, and the distinction is worth keeping rather than flattening.**
Criteria 4 and 6 describe behaviour that was already correct -- verified
by running it, not assumed -- with nothing checking it. Criteria 1 and 7
name a mechanism (the P-019 sweep) that did not exist at all. Criteria 2
and 3 are the substantive failures: a golden demo nothing executable
discharged, and a defect in what a viewer actually sees. Writing
criteria at the audit rather than before the first task guarantees some
of this -- the audit writes the checks it then judges against -- which
is the strongest available argument for the rule this stage broke.

The shape of what went wrong is the one every stage audit here has
found: the criteria a task writes for itself describe what a component
does when used correctly, and nobody was asking what a *frame*
guaranteed.

| Criterion | Verdict |
|-----------|---------|
| 1. Four questions answerable from the screen | **Met in configuration, unenforced. Now both.** All ten demos already set an explicit `rendering.title`, a `field_label` (or `render_field`) wherever a field is colour-mapped, a `vector_label` wherever arrows are drawn, and left `show_stats` on -- verified demo by demo. But the criterion's own load-bearing bullet is "checked by a sweep... not demo by demo", and no sweep existed: all ten complied because the change that wrote P-019 fixed all ten, and nothing would have caught the eleventh. `tests/unit/test_golden_demo_annotations.py` is the sweep, each of its four assertions verified to fail under a real mutation of a real demo file, with the "does this sweep reach anything" guard the criterion also names. |
| 2. Annotations rasterised inside the framed view | **Not met. Now met.** The stage names a Golden Demo -- "all visible in one frame, run through the same public API every other golden demo uses" -- and nothing executable discharged it. `field_display.feature` had no annotation scenario and no golden test touched the HUD; coverage was object-presence in `tests/unit/test_bootstrap.py`, which is true whether or not the text is inside the camera's bounds, in a stage that widened that view four separate times. Four scenarios now check six bands of the rendered frame are not entirely background, each band shown to hold one annotation and nothing else **by mutation** -- `hud._build_text` patched to build every HUD object with empty content, nothing else changed, drops all six to zero. |
| 3. The HUD states nothing the frame cannot support | **Not met -- a defect in shipped behaviour. Now met.** See the account below; `show_vector_scale` was computed from configuration and never from whether an arrow was drawn. Reachable from `lid_driven_cavity.yaml`, which sets `vector_label` and starts from rest. Fixed and pinned in both directions. **The first fix was itself wrong, found by re-auditing it rather than by trusting it**: it had the live path's per-frame query *replace* the static path's answer, so a configuration setting both a static `vector_pattern` and `velocity_solved` went silent whenever the solved velocity was at rest -- with the pattern's arrows plainly on screen. The two are joined now, and the case has its own test. Recorded because a fix landing inside an audit is inside that audit's own scope, not outside it. |
| 4. Numbers in the configured units | **Behaviour correct, half of it unchecked. Now both checked.** `length_scale`/`length_unit` had a test at the rendered text; `time_scale`/`time_unit` had tests only at the configuration boundary, so a `_format_time` ignoring both would have left the suite green. Verified by running it that the live code is correct (three frames at `timestep: 0.01` under `time_scale: 1000.0` renders `30 ms`) -- a hole in the checking, not a defect. Closed with a test whose two factors are both distinct from 1. |
| 5. One annotation mechanism | **Met, and measured rather than asserted.** `git diff --stat 12e12ea b39ce07 -- src/pyflow/engine/ src/pyflow/physics/` returns nothing at all: Stage 7 changed **zero** lines of engine or physics code. `hud.py` imports nothing from `engine/`, owns no camera and formats no numbers; the axis labels added 2026-09-01 reused `show_stats` rather than inventing a third toggle; no `adr/ADR-003` component was touched. |
| 6. Switching it off restores the unannotated render | **Met; its second bullet unchecked. Now checked.** The text half is checked by `tests/features/empty_window.feature` and `test_bootstrap_show_title_and_show_stats_both_false_shows_nothing`. The camera half -- "and the camera framing is unchanged, not merely the text suppressed" -- was true (`_add_hud` returns its input bounds when both gates are off) with nothing asserting it, which is exactly the qualifier-without-a-check shape this table's Criterion 1 row describes. `test_bootstrap_hud_off_leaves_the_camera_framed_on_the_mesh_alone` compares against `fit_camera_to_bounds`' own arithmetic on the mesh bounds, so it survives a change to that margin. |
| 7. P-019 outlives the stage | **Met as a principle, not as a check. Now both.** P-019 exists in `docs/engineering-principles.md` with its mechanism in `src/pyflow/rendering/CLAUDE.md`, exactly as the criterion's first bullet asks. Its second bullet -- "and something checks it" -- is Criterion 1's sweep, and shares that row's verdict. A standing rule enforced by memory is `docs/practices.md`'s "A checkable trigger still needs somebody to check it", named twice in that document and instantiated here. |
| 8. Documentation describes what now exists | **Not met. Now met.** Three documents never learned `hud.py` exists, three days after it landed: `docs/architecture/rendering.md`'s scope sentence (still "the two visualisation modules", in a sentence carrying its own note that it had named only the first two until 2026-08-22), `docs/architecture/CLAUDE.md`'s restatement of the same list, and `docs/architecture/overview.md`'s system diagram. `docs/implementation/golden-demos.md` separately described the HUD's coverage as object-presence-only, true when written and stale once Criterion 2's scenarios landed. `docs/repository-manifest.md` was the one document that had it right. |

**Criterion 3 failed on real behaviour.** A configured
`field_display.vector_label` put "`<label>`: length = `<scale>` x
magnitude" in the stats block wherever `vector_pattern` or a
velocity-only solve was *configured*, without ever asking whether an
arrow had been drawn. `build_vector_field_arrows` returns `None` for a
field whose every cell vector is exactly zero, so a single-cell
`rotational` pattern renders that line over a frame with no arrow in it
-- measured directly, not reasoned about. Reachable from a shipped
demo, not only a constructed one: `lid_driven_cavity.yaml` sets
`vector_label` and starts from rest, so its first frame claimed a
length-per-magnitude conversion for arrows that did not exist yet.
TASK-044's own Acceptance Criteria had already written the correct rule
-- "when unset, **or when no arrows are drawn**, no such line appears"
-- and nothing checked the second clause. That is
`docs/practices.md`'s "At audit time: check the qualifier, not the
headline", found by doing exactly that. Fixed here rather than
recorded: `show_vector_scale` is now answered by the drawing paths
themselves, per frame on the live path, and pinned in both directions
(a run at rest claims nothing; the same run claims it again once the
lid drives the flow).

**Criterion 2 failed on coverage, and the gap was the stage's own
Golden Demo.** This stage names one -- the annotated Field Display,
"all visible in one frame, run through the same public API every other
golden demo uses" -- and nothing executable discharged it.
`field_display.feature` had no annotation scenario, no golden test
touched the HUD, and the only coverage was object-presence assertions
in `tests/unit/test_bootstrap.py`: a `gfx.Text` in the scene with the
right content, which is true whether or not the text is inside the
camera's bounds. This stage widened the framed view four times; that is
precisely the failure mode object presence cannot see. Four scenarios
now check that six bands of the rendered frame -- title, both axes'
ticks, the legend caption, the legend endpoints, the stats block -- are
not entirely background. Each band was shown to hold that annotation
and nothing else by mutation, not by reading the arithmetic: with
`hud._build_text` patched to build every HUD object with empty content
and nothing else changed, all six drop to zero non-background pixels.

**Criterion 8 failed the way it has now failed in six consecutive stage
audits.** `docs/architecture/rendering.md` still described
`src/pyflow/rendering/` as "the canvas seam and render loop plus **the
two** visualisation modules", three days after `hud.py` landed as the
third -- in a sentence carrying its own note that it had named only the
first two until 2026-08-22. The same list is restated in
`docs/architecture/CLAUDE.md`, which had drifted identically, and
`docs/architecture/overview.md`'s system diagram named two of the three
too (a diagram makes claims, `docs/architecture/CLAUDE.md`'s own rule).
Three documents, one fact, found by grepping a sibling module's name
rather than by re-reading the diff. `docs/repository-manifest.md` was
the one that had it right.

**Criterion 4 was met in half and unchecked in the other half.**
`units.length_scale`/`length_unit` had a test at the rendered text;
`time_scale`/`time_unit` had tests only at the configuration boundary,
so a `_format_time` ignoring both would have left the whole suite
green. Verified by running it that the live code is in fact correct
(`0.01 s` at three frames, `time_scale: 1000.0`, renders `30 ms`) --
this was a hole in the checking, not a defect in the behaviour, and the
distinction is worth keeping rather than rounding into "Criterion 4
failed". Closed with a test whose two factors are both distinct from 1.

**Criterion 1's sweep and Criterion 7's check are the same object, and
neither existed.** All ten demos satisfied P-019 on the day it was
written because the change that wrote it also fixed all ten. Nothing
would have caught the eleventh, which is what a standing rule is *for*.
The sweep now reads every demo config and fails if one colour-maps a
field without naming the quantity, draws arrows without naming them,
renders a mesh view with `show_stats` off, or leaves `rendering.title`
at the application default -- each verified to fail under a real
mutation of a real demo file before being trusted.

**What held, and held on its own terms.** Criterion 5's architectural
claim is intact: `hud.py` imports nothing from `engine/`, formats no
numbers, and owns no camera; the axis labels added on 2026-09-01 reused
`show_stats` rather than inventing a third toggle; no `adr/ADR-003`
component was touched and no engine file was modified by this stage at
all. Criterion 6 holds and is checked by
`tests/features/empty_window.feature` plus
`test_bootstrap_show_title_and_show_stats_both_false_shows_nothing` --
and the camera half holds too, since `_add_hud` returns its input
bounds unchanged when both gates are off. Criterion 1's configuration
half was already true in all ten demos before this audit; only its
enforcement was missing.

**One thing this audit deliberately did not do.** TASK-044 records a
fast-follow -- moving the HUD from world-space, camera-following text
to `screen_space=True`, verified to exist and work but not used -- and
this audit leaves it open rather than closing it. It is a change to
what the annotations look like at zoom, not to whether the stage's Goal
is met, and every criterion above is satisfied by the world-space
version. Recorded here so its absence reads as a decision rather than
an oversight; `docs/planning/backlog.md` carries it.

---

## TASK-044

Rendering HUD: Title, Legend Labels, Timestep/Time, Cell/Domain Size,
Physical Units

**Numbered out of sequence, the same shape TASK-039/TASK-043 already
established (see either entry): the next free number at the time this
was drafted, placed physically here because that is where it belongs by
reading order.** Two independent branches drafted work in the low-40s
at the same time (this one, and TASK-043's `pyflow run --demos`
shortcut) -- if both land, one is renumbered at merge time to avoid a
collision; this entry does not resolve which.

**Status: Done, 2026-08-31, for the scope below -- two real gaps
recorded honestly rather than silently, not "fully done".**

**Amended 2026-09-03 by the Stage 7 exit audit** (its verdict table is
above, under this stage's own Completion Criteria, which did not exist
when this entry was written). Three things this entry says are no
longer the current state, corrected here rather than left for a reader
to reconcile:

- **The "no Gherkin `.feature` file for this stage" gap is closed**, and
  the reasoning recorded below for it was half right. It is correct
  that `adr/ADR-007-executable-acceptance-criteria.md`'s own scope is
  physics and that rendering annotations are not physics. What that
  reasoning did not reach is the separate obligation this stage's own
  **Golden Demo** entry creates: a golden demo's criteria are executable
  because every other demo in `tests/features/` works that way
  (`tests/golden/CLAUDE.md`), regardless of ADR-007.
  `field_display.feature` now carries four annotation scenarios,
  checked in real rendered pixels.
- **A defect this entry's own Acceptance Criteria already forbade was
  shipped**, and its criterion below now reads as met because it was
  fixed, not because it always was: a `vector_label` stated a
  length-per-magnitude conversion wherever arrows were *configured*
  rather than wherever one was *drawn* -- see Criterion 3's row above
  for the measurement and the fix.
- **`docs/architecture/rendering.md` and two documents beside it never
  learned `hud.py` exists.** Not this entry's own claim to correct, but
  squarely inside its blast radius, and named here so the omission is
  attributed where it happened.

### Purpose

The stage's own Goal, made concrete: a viewer watching `pyflow run` had
no title, no labelled legend, no timestep/elapsed-time readout, and no
cell/domain-size readout -- nothing on screen said what was being
simulated or how the colour map should be read, without opening the
config file. This closes that gap, and incidentally the deliberate
TASK-017 deferral of numeric legend labels (held back specifically
because pygfx's text rendering had not been verified live, not because
labelling was unimportant).

### Dependencies

None functionally. Verified pygfx's `gfx.Text`/`TextMaterial` live
against the installed `pygfx==0.17.0` before building anything on it
(`src/pyflow/rendering/CLAUDE.md`'s own HUD entry has the measurements) --
not assumed from the fact that the classes exist.

### Design decisions, recorded here

**World-space, camera-following, not a fixed screen-space overlay --
maintainer's own choice, confirmed cheap to build (the legend strip's
existing bounds-extension pattern reuses directly) over the objectively
better UX of a fixed overlay, which would need new, unverified pygfx
API surface (`screen_space=True`, confirmed to exist and work during
this task's own research, but not used).** Revisit as a fast-follow now
that it is verified rather than speculative.

**The live-stepping path gained a legend it never had, not just the
static demo.** `_add_declared_field_transport` coloured a declared field
every frame with no legend beside it before this -- exactly backwards
from what watching a live run needs most. `bootstrap.py`'s new
`_add_legend` is the strip-drawing logic factored out and shared by both
paths; see `rendering/CLAUDE.md`'s own entry for the fuller reasoning.

**Physical units display as one labelled number, not a dual "raw
(converted)" pair.** `units.length_scale`/`time_scale` default to `1.0`
(unit labels default `"m"`/`"s"`), so an unconfigured run shows the bare
simulation number labelled in SI base units; a configured scale changes
what number is shown, not whether one is shown at all -- sidesteps the
"when do I show the parenthetical" question a dual display would raise.

**Layout is fixed-fraction margins against the mesh's own height, not
measured text extents** -- pygfx gives no cheap way to measure a `Text`
object's rendered size before adding it to a scene, so this follows
`_LEGEND_HEIGHT_FRACTION`'s own existing precedent (a documented guess,
generous rather than tight) rather than inventing a new approach.

**One real gap, recorded rather than smoothed over: no Gherkin
`.feature` file for this stage.** Coverage is plain pytest throughout
(`tests/unit/test_hud.py`, `tests/unit/test_bootstrap.py`) -- the same
"checked by construction" shape already used for the legend's
colour-sharing guarantee, but `adr/ADR-007-executable-acceptance-
criteria.md`'s own scope is "real simulation work... where physics
begins", and rendering annotations are not physics. Judged in scope at
the time this was written, per that ADR's own stated boundary -- but
named here explicitly rather than left for a reader to wonder whether it
was overlooked, per this project's own Integrity section. Revisit if a
future reader judges the existing plain-pytest coverage insufficient.

**Revised the same day, from real user feedback on the shipped
result -- three changes, not a second task:**

1. **The HUD's own gate was backwards.** It first shipped requiring
   `show_mesh`/`field_display`/a live simulation alongside
   `show_title`/`show_stats`, specifically to protect Empty Window's own
   "every pixel is the configured background colour" contract. A user
   running the bundled demos found this made every demo with nothing
   else configured to show (Numerics Assembly) render a genuinely blank
   window -- worse than the gap this task exists to close. Fixed by
   making `show_title`/`show_stats` the actual gate, independent of
   what else is configured; Empty Window now opts out explicitly instead
   of relying on the old condition to do it implicitly. See
   `rendering/CLAUDE.md`'s own HUD entry for the fuller account, and
   `src/pyflow/bootstrap.py`'s own comment at the reversed condition.
2. **No field/vector quantity naming, on the same user's own report**:
   "what is being simulated... should be explicit", "'Tracer' isn't
   sufficient", "[arrows --] neither the direction nor magnitude is
   clear." Every one of the ten bundled golden demos now sets an
   explicit `rendering.title`; every demo that colour-maps a field sets
   `field_display.field_label` (`"(model units)"` where the field isn't
   calibrated to a real physical unit, which is every demo so far --
   stated honestly rather than implying a precision that doesn't exist);
   every demo that draws arrows sets the new `field_display.vector_label`,
   which adds a HUD line stating the quantity and `arrow_scale` as a
   length-per-magnitude conversion. This closes what used to be listed
   here as a second, separate gap ("`field_label`'s on-screen placement
   is not verified against a real config that sets it") -- it now is,
   against nine real demo configs, visually checked, not merely
   object-presence-tested.
3. **A real, found-not-anticipated overflow bug, closed in the same
   pass**: a long `vector_label` line clipped clean off the edge of
   `field_display.yaml`'s own narrow, pixel-exact-testing canvas.
   `gfx.Text`'s `max_width` was verified live to word-wrap cleanly and is
   now set on every HUD text object to the mesh's own world-space width
   -- see `rendering/CLAUDE.md` for the measurement.

**Revised again the next day (2026-09-01), from a second round of real
user feedback -- two more changes, promoted to a standing rule
(`docs/engineering-principles.md` P-019) rather than left as this task's
own one-off fixes:**

4. **"Arrows" had no arrowhead.** A screenshot from the same user showed
   exactly what `roadmap.md`'s own TASK-017 entry had predicted and
   deferred: "no arrows at all... only lines which lengthen and rotate."
   A bare line segment has no visual asymmetry, so which end is the tip
   is not recoverable from the rendered pixels regardless of scale --
   confirmed the vectors themselves were genuinely present in the scene
   at every frame count checked (1 through 500) before concluding this,
   not assumed from the screenshot alone. `field_visualization.py`'s
   `build_vector_field_arrows` now appends two chevron segments at the
   tip, proportional to the shaft's own length (`_ARROWHEAD_LENGTH_
   FRACTION = 0.3`) so a near-zero vector still renders an honestly
   near-invisible head rather than a fixed-size decoration overstating
   it. Re-verified against real renders of Field Display and Lid-Driven
   Cavity before being trusted, the same discipline this task's own
   first cut used for the HUD's own layout.
5. **No labelled spatial axes, and the same report asked for a standing
   rule, not a one-off fix**: "make that a standing rule for rendering
   that all graphs and axes must be labelled." `hud.py`'s new
   `build_axis_labels` places min/mid/max world-coordinate tick labels
   along the mesh's top and left edges; `bootstrap.py`'s `_add_hud`
   reuses `show_stats` as the gate (the same mesh-geometry fact
   cell/domain size already describes, not a new toggle) and is the
   first HUD element to extend `bounds` leftward. `docs/engineering-
   principles.md`'s new **P-019** is the durable statement the user
   asked for; `rendering/CLAUDE.md`'s own entry is the mechanism.
   `field_display.yaml`'s canvas needed recalculating a second time as a
   direct consequence (`190x280`, `19:28`, and `285x430`/`57:86` once the exit audit widened the legend gap -- axis labels are the first
   HUD element to widen the frame horizontally).
6. **Immediate follow-up on item 4, same day**: "where the magnitude is
   small the arrowheads are also small. Too small to see easily...
   [make] direction clearer without distorting the impression of
   magnitude." A purely shaft-proportional head (item 4's own fix)
   shrinks below legibility for a genuinely small vector -- direction
   becomes unreadable even though the shaft itself is still visible, the
   exact case a Lid-Driven Cavity run starting from rest hits everywhere
   except right at the moving lid. `field_visualization.py` gained a
   second, independent floor, `_ARROWHEAD_MIN_LENGTH_FRACTION_OF_CELL =
   0.3` of that cell's own `sqrt(cell_volume)`, `max()`-combined with the
   existing proportional fraction -- the shaft itself, which is what
   actually conveys relative magnitude, is untouched, so this makes
   direction legible without changing what magnitude looks like. See
   `rendering/CLAUDE.md`'s own entry for the exact formula and the three
   tests (`..._head_has_a_minimum_length_for_tiny_vectors`,
   `..._head_floor_does_not_affect_large_shafts`, and the existing
   `..._head_length_scales_with_shaft_length` moved to scales `1.0`/
   `10.0`, both above the floor) that pin the two regimes apart.

### Artifacts Produced

- `src/pyflow/rendering/hud.py` -- `build_title_text`, `build_stats_text`,
  `build_legend_labels`, `build_axis_labels`, each taking a `max_width`
  (world units, `0` = unbounded) that word-wraps rather than lets text
  overflow.
- `src/pyflow/configuration/schema.py` -- `RenderingConfig.show_title`/
  `show_stats`, `FieldDisplayConfig.field_label`/`vector_label`, new
  `UnitsConfig` section (`PyFlowConfig.units`).
- `src/pyflow/bootstrap.py` -- `_add_legend` (factored out, shared by the
  static and live-stepping scalar-display paths), `_add_hud` (now also
  building axis tick labels), `_format_length`/`_format_time`/
  `_stats_lines`; `_add_field_display`/`_add_declared_field_transport`/
  `_add_solved_velocity_rendering` each widened to also return their own
  legend bounds (`None` where no legend is drawn); the top-level `if` in
  `bootstrap()` widened to include `show_title`/`show_stats`.
- `src/pyflow/rendering/field_visualization.py` -- `build_vector_field_
  arrows` now appends a real arrowhead (`_ARROWHEAD_ANGLE`/
  `_ARROWHEAD_LENGTH_FRACTION`) to every shaft it draws, with a second,
  independent floor (`_ARROWHEAD_MIN_LENGTH_FRACTION_OF_CELL`) keeping
  the head legible for a small-magnitude vector without changing the
  shaft that conveys its magnitude.
- `docs/engineering-principles.md` -- new **P-019** (every rendered
  chart/plot/mesh view labels its own axes and legends).
- `examples/golden-demos/*.yaml` -- all ten: an explicit `rendering.
  title`; `field_display.field_label` on every demo colour-mapping a
  field; `field_display.vector_label` on every demo drawing arrows;
  `empty_window.yaml`'s own explicit `show_title: false`/
  `show_stats: false` opt-out. `field_display.yaml`'s `rendering.width`/
  `height` recalculated three times (250x290 -> 250x395 -> 190x280 -> 285x430) as the HUD,
  then axis labels, widened the framed view -- not guessed either time.
- `docs/implementation/config-template.yaml` -- regenerated for the new/
  changed fields.

### Acceptance Criteria

- A configured title appears as HUD text matching `rendering.title`,
  suppressed entirely by `rendering.show_title: false`.
- The legend's min/max labels match `field_display.value_range` exactly;
  a `field_label`, if set, overrides the legend caption that otherwise
  falls back to `render_field`'s own name.
- Cell size and domain size HUD text reflects `config.mesh.spacing` and
  the mesh's own bounding box, suppressed entirely by
  `rendering.show_stats: false`.
- A live-stepping run's stats text includes a step/time line that
  differs between frames; a static (non-live-stepping) run's stats text
  never claims a step/time at all.
- `units.length_scale`/`time_scale`/`length_unit`/`time_unit`, when set,
  change the displayed cell-size/domain-size/elapsed-time numbers and
  labels; left at their defaults, the numbers are unchanged from before
  this task.
- A bare `pyflow run` with no mesh/fields/simulation configured still
  shows the HUD (title/stats), since `show_title`/`show_stats` default
  true and are the actual gate -- reversed from this task's own first
  cut; only a config setting both false explicitly (`empty_window.yaml`)
  shows nothing but its background colour, and `tests/features/
  empty_window.feature`'s own contract keeps holding for that one demo.
- A `vector_label`, when set, adds a HUD line stating the label and
  `arrow_scale` wherever arrows are actually drawn (static
  `vector_pattern` or live velocity-only rendering); when unset, or when
  no arrows are drawn, no such line appears.
- HUD text that would otherwise overflow the mesh's own world-space
  width wraps at word boundaries (`max_width`) instead of clipping or
  extending past the framed view.
- `tests/golden/test_field_display.py`'s existing per-cell/legend
  pixel-exact checks still pass at the recalculated canvas resolution.
- Every vector field arrow renders a real arrowhead whose two segments
  are symmetric about the shaft (equal angle, opposite sides) and scale
  with the shaft's own length, so direction is visually recoverable
  without a fixed-size decoration overstating near-zero vectors.
- A vector small enough that a purely proportional head would be
  illegible still gets a head at least `0.3 * sqrt(cell_volume)` long,
  without its shaft length changing -- direction stays readable at any
  magnitude, and relative magnitude still reads from the shaft alone.
- `rendering.show_stats: true` (the default) adds min/mid/max
  world-coordinate tick labels along both axes, formatted through
  `config.units` exactly as cell/domain size are; `show_stats: false`
  suppresses them along with the rest of the stats block, since they
  share that one gate rather than a toggle of their own.
- **Added 2026-09-03 by the exit audit, as the second half of the
  criterion three bullets above already stated:** a `vector_label` adds
  no scale line where no arrow was drawn, whatever the configuration
  asked for -- and the line returns as soon as arrows do, so a velocity
  starting from rest is silent on its first frame and labelled on the
  frame its flow develops.

### Discharges

Assigned at the exit audit rather than when this task closed, because
this stage had no criteria to assign against until then -- the exception
to Stages 3-6's own practice, and the reason it is an exception is
recorded in this stage's Completion Criteria above.

**Criteria 1, 4 (length), 5, 6 and 7 (the principle)**, as built.
Criteria 2, 3, 4 (time), 7 (the check) and 8 were discharged by the
audit itself; the discharge map above says which, and the verdict table
beside it says why.

---

# Stage 8 — Better Numerics

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

**Inherited from Stage 6, recorded here 2026-08-31 by that stage's exit
audit so it is not carried only in the documents that deferred it:
Rayleigh-Bénard's critical Rayleigh number.** Stage 6's design question
five (resolved 2026-08-30, maintainer's call) settled that the
qualitative onset check -- rolls form heated from below and do not
heated from above -- was that stage's bar, and that the quantitative
comparison against approximately 1708 for the rigid-rigid case is
**deferred to this stage at the earliest, not dropped**. The reason is
this stage's own subject: hitting a critical threshold on
first-order-upwind advection at MVP mesh resolutions is a bar the MVP's
documented numerics are not built to clear, and a criterion meetable
only by loosening its own number later is not a criterion. A less
diffusive scheme is what would make it meetable, which is what "Better
Numerics" means. `docs/planning/backlog.md`'s and
`docs/planning/implementation-plan.md`'s Rayleigh-Bénard entries both
say so; this is the third place, and the one a reader opening this stage
would actually reach. Whether it becomes a completion criterion here is
for whoever drafts them -- the point of this note is that they know it
is on the table.

---

# Stage 9 — Geometry

Goal

Support realistic domains.

Tasks include

- Internal obstacles
- Immersed boundaries
- Complex boundaries

Golden Demo

Flow around a cylinder.

---

# Stage 10 — Adaptive Resolution

Goal

Increase efficiency.

Tasks include

- Adaptive Mesh Refinement
- Error estimation
- Dynamic refinement

Golden Demo

Adaptive vortex refinement.

---

# Stage 11 — Additional Numerical Frameworks

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

# Stage 12 — Three Dimensions

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

# Stage 13 — Performance

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

# Stage 14 — Advanced Physics

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
