# CLAUDE

Isolated logic, no process boundary, no I/O beyond what `tmp_path`
fixtures give a test for free -- if it needs to cross a real boundary
(subprocess, the packaged CLI, multiple subsystems together), it belongs
in `tests/integration/` instead.

`test_configuration.py` is the first example: pure in-process calls
against `pyflow.configuration`, using `tmp_path` for YAML fixture files
rather than real filesystem state outside the test. Covers defaults,
partial overrides, and every rejection path (missing file, non-mapping
YAML, unknown section, unknown field, each specific validation failure)
-- one test per failure mode rather than one large test asserting several
things, so a broken assertion says exactly what broke.

`test_rendering.py` (D3) only exercises the `offscreen` render backend,
never `glfw` -- it needs no I/O beyond `tmp_path`-style isolation and no
real OS resource, which is exactly what keeps it a *unit* test per this
directory's own scope. Follow this split for any future test that
touches rendering purely in-process, with no real window.

**A test that does need a real window belongs in `tests/integration/`,
not here** (revised 2026-08-17) -- it's crossing a real boundary (an
actual OS window system), the defining trait of that directory per
`tests/CLAUDE.md`, not "isolated logic." `tests/integration/
test_interactive_window.py` is that test: a real `glfw` window, skipped
cleanly (not failed) when no display is available. Previously this
section said interactive-backend behaviour "doesn't belong in the
automated suite" at all and was verified by hand instead (see
`src/pyflow/rendering/CLAUDE.md`) -- that blanket claim turned out to be
wrong, not just outdated: a real display is checkable at runtime and,
where present, a real window can be driven, closed, and its frames
inspected entirely automatically. "No display, no CI" was true; "no
display, ever" was an unexamined generalisation from it.

**`test_simulation.py` (TASK-040, added 2026-08-27) is the first
`pytest-bdd` module in this directory, not only in `tests/golden/`.**
`adr/ADR-007-executable-acceptance-criteria.md`'s scope is "simulation
work", not "golden demos" -- `tests/features/simulation_orchestrator.feature`
is Stage 4's first feature file and the first with no config file under
`examples/golden-demos/` and no CLI subprocess run, since it exercises
the orchestration mechanism (`src/pyflow/engine/simulation.py`) directly
rather than a runnable demo. It binds its scenarios and supplies its own
step definitions and test-only doubles locally (a `_Context` dataclass
mutated in place by each step, the same pattern `tests/golden/_demo.py`'s
`DemoRun` establishes) rather than drawing on `tests/golden/conftest.py`'s
vocabulary, which is phrased entirely in terms of running and rendering a
demo and has nothing this module needs. A future non-golden-demo feature
file follows this module's shape, not `tests/golden/`'s.

**`test_first_order_upwind_advection.py` (TASK-023, added 2026-08-27)
is the second**, binding `tests/features/first_order_upwind_advection.feature`
-- Stage 4's first real numerical scheme's own physical-correctness
claims (bounded, conservative on a closed domain, not the same as
stable). Same shape as `test_simulation.py`: its own `_Context`
dataclass, its own local test-only `BoundaryCondition` doubles, no
golden-demo config file or CLI run. **A second conservation scenario, on
a fully periodic domain, was added 2026-08-28 by the Stage 4 exit audit
because the closed-domain one turned out to pass for any flux array
whatsoever** -- see `src/pyflow/engine/CLAUDE.md`'s
`FirstOrderUpwindAdvection` entry for why, and for the general rule it
produced about what a conservation scenario can and cannot test.

**`test_central_difference_diffusion.py` (TASK-024, added 2026-08-27)
is the third**, binding `tests/features/central_difference_diffusion.feature`
-- Stage 4's second real numerical scheme's own physical-correctness
claims (the interior and boundary flux formulas, second-order accuracy
under mesh refinement, conservation under zero-flux boundaries). Same
shape again: its own `_Context` dataclass, its own local test-only
`BoundaryCondition` doubles (not imported from
`test_first_order_upwind_advection.py`, per this directory's own "each
binding test supplies its own local steps" convention), no golden-demo
config file or CLI run. Its own convergence-order scenario is measured
against strictly interior cells only, since only the interior
central-difference formula carries the handbook's second-order claim --
`docs/planning/roadmap.md` TASK-024's own Design Decision Four records
the full reasoning.

**`test_rk4_time_integration.py` (TASK-025, added 2026-08-27) is the
fourth**, binding `tests/features/rk4_time_integration.feature` -- Stage
4's fourth real numerical scheme's own physical-correctness claims
(fourth-order accuracy in time, and genuine four-stage evaluation at four
distinct states). Same shape again: its own `_Context` dataclass, no
golden-demo config file or CLI run. **Its own manufactured-derivative
approach is the temporal mirror of `test_central_difference_diffusion.py`'s
spatial one** -- that file measures spatial order with no time-stepping;
this one measures temporal order with a hand-written `dy/dt = -k*y`
closure, never touching the real mesh or `AdvectionScheme`/
`DiffusionScheme` machinery, so spatial error cannot contaminate the
measured temporal order. The four-evaluations scenario exists because
the accuracy scenario alone cannot distinguish genuine multi-stage
evaluation from a scheme that degenerates to fewer evaluations or reuses
a stale intermediate state -- verified to actually catch that distinction
by deliberate mutation, not assumed (`docs/planning/roadmap.md`
TASK-025's own Design decisions record the full mutation-testing
history, including a first draft of this scenario's own assertion that
was found too weak and tightened).

**`test_conjugate_gradient_solver.py` (TASK-026, added 2026-08-27) is
the fifth**, binding `tests/features/conjugate_gradient_solver.feature`
-- Stage 4's fifth real numerical scheme's own physical-correctness
claims (converges on a positive-semi-definite system with the null space
handled, non-convergence distinguishable from a converged answer). Same
shape again: its own `_Context` dataclass, its own local
`_ZeroGradientCondition` boundary-condition double, no golden-demo config
file or CLI run. **Its own semi-definite fixture is built from the real
`CentralDifferenceDiffusion`/`accumulate_flux_to_cells` on a
zero-gradient-everywhere mesh, not a hand-typed matrix** -- verified
directly (symmetric, one ~0 eigenvalue via `torch.linalg.eigvalsh`, the
rest strictly positive) before being written into the test, the closest
available approximation to "the system PISO actually produces" at the
time this was written, since PISO itself did not exist yet (TASK-027,
which landed the next day and turned out to build its own Poisson matrix
this exact same way -- `CentralDifferenceDiffusion`-based, not a
hand-typed one either, closing this forward-reference for real rather
than by coincidence). Mutation testing here found something worth
recording honestly rather than smoothing over: the solver's own
null-space *projection* could not be shown to matter at any fixture size
this repository can realistically test (only the *gate* deciding whether
to apply it could be) -- `docs/planning/roadmap.md` TASK-026's own Design
decisions record the full finding.

**`test_piso_pressure_coupling.py` (TASK-027, added 2026-08-27) is the
sixth**, binding `tests/features/piso_pressure_coupling.feature` --
Stage 4's sixth real numerical scheme's own physical-correctness claims,
honestly scoped (`docs/planning/roadmap.md` TASK-027's own Design
decision Two, `docs/practices.md`'s "A criterion whose strong reading
depends on a later task must say so when drafted"): a single correction
pass measurably and boundedly reduces a manufactured provisional
velocity field's divergence, checked in isolation, not the fully-
converged claim Stage 5 TASK-033 owns. Same shape again: its own
`_Context` dataclass, its own local `_ZeroNormalVelocity`
`BoundaryCondition` double and `_NeverConvergesSolver` `LinearSolver`
double, no golden-demo config file or CLI run. **Its own provisional
velocity fixture is neither axis-aligned nor uniform**
(`docs/practices.md`'s "distinct factors" rule) so a wrong implementation
(unchanged output, or a uniform correction regardless of local
divergence) cannot pass by coincidence; the 70% bound in the feature
file's own first scenario is the actual measured reduction on this
fixture (roughly 46-54% depending on the cell) with real margin, not a
value chosen to make a marginal result pass.

**`test_dirichlet_boundary.py` (TASK-028, added 2026-08-28) is the
seventh**, binding `tests/features/dirichlet_boundary.feature` -- Stage
4's seventh real numerical scheme's own physical-correctness claim, per
this task's own Intent: correctness is checked in what a real interior
scheme (`FirstOrderUpwindAdvection`, `CentralDifferenceDiffusion`)
computes at a boundary face using a real `DirichletBoundaryCondition`,
not only in what `evaluate()` returns in isolation -- a condition object
can return the right value and still be wired into the flux computation
wrongly. Same shape again: its own `_Context` dataclass, its own local
`_FixedGradientCondition` double for the three boundary faces neither
scenario exercises (never the class under test), no golden-demo config
file or CLI run. **Both scenarios build the real scheme and the real
condition together** -- unlike every prior binding module in this
directory, which constructs its interior scheme under test against
hand-written `BoundaryCondition` doubles, this is the first task whose
own claim is specifically that the *real* condition class is correctly
wired, so a hand-written double standing in for it would prove nothing
this task needed proven.

**`test_neumann_boundary.py` (TASK-029, added 2026-08-28) is the
eighth**, binding `tests/features/neumann_boundary.feature` -- Stage 4's
eighth and, for boundary conditions, last real numerical scheme's own
physical-correctness claim, per this task's own Intent: as Dirichlet's
own, for a prescribed gradient, with a *nonzero* gradient required
throughout -- a zero-gradient result is also what a boundary wired to
nothing at all would silently produce. Same shape again: its own
`_Context` dataclass, its own local `_FixedGradientCondition` double for
the three boundary faces the diffusion scenario doesn't exercise (never
the class under test), no golden-demo config file or CLI run. Both
scenarios build the real scheme and the real
`NeumannBoundaryCondition` together, the same "no hand-written double
standing in for the class under test" shape `test_dirichlet_boundary.py`
established. **Diffusion's own scenario proves the gradient's numeric
value is read directly into the flux formula; advection's own proves the
opposite** -- the value is never read, only zero-order extrapolation
from the owner -- confirmed by mutation: forcing
`NeumannBoundaryCondition.evaluate` to always return `0.0` fails the
diffusion scenario and the contract suite's own dedicated test, but
leaves the advection scenario passing unchanged, exactly the asymmetry
`src/pyflow/engine/CLAUDE.md`'s own `FirstOrderUpwindAdvection`/
`CentralDifferenceDiffusion` entries record.

**`test_periodic_boundary.py` (TASK-030, added 2026-08-28) is the ninth
and, for this pytest-bdd lineage, last of Stage 4's numerical-scheme
modules**, binding `tests/features/periodic_boundary.feature` -- Stage
4's ninth and last task's own physical-correctness claim. **A genuinely
different shape from every prior binding module in this list**: there is
no condition class under test at all -- periodic bypasses
`BoundaryCondition` entirely (`docs/planning/roadmap.md` TASK-030's own
Design decision), so the only real mechanism is the mesh's own
`wrapped_neighbour_cell` (tested directly in
`test_structured_cartesian_mesh.py`, not here) and the two real interior
schemes' own wiring to it. Own `_Context` dataclass, own local
`_FixedGradientCondition` double for the non-periodic boundary faces the
round-trip scenario's own mesh still needs something configured for
(diffusion has no inflow/outflow carve-out), no golden-demo config file
or CLI run. **The round-trip scenario is checked as convergence under
mesh refinement, not exact equality at one resolution** -- a genuine
numerical finding, not assumed: first-order upwind's own O(dx) numerical
diffusion smooths any field over the distance it travels regardless of
whether the wrap is correct, verified directly (near-identical results
at `num_steps` 10-160 on a fixed mesh, since refining the timestep alone
does not shrink a spatial-truncation-dominated error). A real wrap's own
round-trip error drops by roughly 62% over a 4x mesh refinement; a
mirrored/clamped one (a throwaway mutation, built and run specifically
to check this) drops by only roughly 16% and stays several times larger
throughout -- the scenario's own two-thirds bound was chosen to separate
those two measured outcomes, not guessed, and confirmed to actually fail
under that same mutation before being trusted.

**`test_velocity_field_support.py` (TASK-031, added 2026-08-29) is the
tenth, and the first Stage 5 module in this lineage** -- Stage 5's
second task, all four subtasks in one binding module (the roadmap's own
"share a branch, a test module and a review cycle"), binding
`tests/features/velocity_field_support.feature`'s thirteen scenarios,
grouped by subtask in both files. Same shape as the Stage 4 modules
before it: its own `_Context` dataclass, its own local `_EulerIntegrator`/
`_ZeroDiffusion`/`_InertLinearSolver`/`_InertPressureCoupling` doubles
(the same hand-derivable-arithmetic shape `test_simulation.py`'s own
identically-named doubles use), no golden-demo config file or CLI run.
Reuses `_numerics.py`'s `default_mesh`/`zero_gradient_everywhere` rather
than re-deriving either, per this task's own whole-task obligation.
**Its self-advection scenario ("Velocity advected by itself reproduces a
hand-derived result") uses its own smaller 2-cell mesh, not the shared
`default_mesh()`** -- purely horizontal, non-uniform initial velocity,
so the diffusion-free, Euler-integrated derivative is tractable to
derive by hand while still exercising the one real nonlinearity
self-advection introduces; the boundary condition it needs (a *specific*
west-wall value per velocity component, not the generic one every other
`step`-driving scenario in this module uses) is threaded through a
`ctx.advection` override rather than hardcoded into the shared `When`
step, since two scenarios share that step's exact wording but need
different boundary conditions to be correct. Verified directly before
being trusted, the same discipline every other hand-derived scenario in
this repository uses -- see this module's own commit message for the
full per-face derivation.

**`test_pressure_field.py` (TASK-032, added 2026-08-29) is the
eleventh, and Stage 5's second module in this lineage** -- Stage 5's
third task, binding `tests/features/pressure_field.feature`'s five
scenarios against the real `PISO` (TASK-027, Stage 4) directly, not a
new pressure-solving mechanism: this task's own job was proving
properties Stage 4's own criteria never had cause to check. Same shape
as every module before it: its own `_Context` dataclass, its own local
`_ZeroNormalVelocity` double (the same fixture shape
`test_piso_pressure_coupling.py`'s own identically-named double uses),
no golden-demo config file or CLI run. **Its divergence-free fixture is
a uniform velocity field with zero-gradient boundaries, not a
hand-crafted Dirichlet one** -- a uniform field's own divergence is
exactly zero by the discrete Gauss theorem's closure identity (the sum
of a closed cell's own face-area-weighted outward normals is the zero
vector) regardless of the field's value, and zero-gradient boundaries
extrapolate the interior's own uniform value back at every wall with no
artificial jump, unlike a Dirichlet condition that would have to
happen to match it exactly. The null-space scenario shifts the real
solved pressure by a nonzero constant and recomputes the correction
directly through `GreenGaussGradient`, rather than re-running `PISO`
end to end, since the claim is specifically about the gradient of a
shifted field, not about the solve that produced it.

**`test_pressure_correction_loop.py` (TASK-033, added 2026-08-29) is the
twelfth, and Stage 5's third module in this lineage** -- Stage 5's
fourth task, binding `tests/features/pressure_correction_loop.feature`'s
three scenarios against the real `PISO` directly, now genuinely
multi-pass (see `src/pyflow/engine/CLAUDE.md`'s own `PISO` entry for
design question three's resolution). Same shape as every module before
it: its own `_Context` dataclass, its own local `_ZeroNormalVelocity`
double (the same fixture shape `test_piso_pressure_coupling.py`'s/
`test_pressure_field.py`'s own identically-named doubles use), no
golden-demo config file or CLI run. **Two `LinearSolver` doubles do the
real work no real solver could demonstrate on this mesh**: a real
`ConjugateGradientSolver` converges the divergent fixture in one or two
passes, too fast to prove genuine multi-pass behaviour, so
`_HalvingSolver` (always returns exactly half of the true least-squares
correction, verified beforehand to produce an exact geometric halving of
the recorded divergence every pass) forces and proves several strictly-
decreasing passes; `_NoOpSolver` (reports `converged=True` but always
returns the zero vector) exercises the iteration-limit exhaustion path,
distinct from `test_piso_pressure_coupling.py`'s own
`_NeverConvergesSolver` (`converged=False`), since this scenario is
about the *outer* loop giving up, not the *inner* solve failing.

**The convention is "local by default, shared where genuinely
identical" -- amended 2026-08-28 by the Stage 4 exit audit, which found
the older blanket form ("each binding test supplies its own local
steps") in unresolved conflict with Stage 4 Completion Criterion 6.**

The conflict turned out not to be a real disagreement. That criterion
asked for a shared vocabulary in `tests/golden/conftest.py`, which
**cannot** serve this directory: a `conftest.py` applies only to its own
subtree, so a `tests/unit/` scenario using a step defined there fails
with `StepDefinitionNotFoundError` -- verified directly, not reasoned
about. The criterion named an unreachable venue; this convention grew
into the vacuum, and then hardened into a principle nobody re-examined
while the duplication it licensed accumulated: the mesh constants
byte-identical in eight modules, `_FixedGradientCondition` in four,
`_face_normal_velocity` in four, `_west_face` in four. Eight copies of
one fixture is one fixture with eight places to fix.

**What this means concretely.** `tests/unit/_numerics.py` holds the
shared building blocks -- `default_mesh`, `FixedValueCondition`,
`FixedGradientCondition`, `zero_gradient_everywhere`, `west_face`,
`face_normal_velocity`/`face_normal_velocity_toward` -- the counterpart
to `tests/golden/_demo.py`, and the same underscore-prefixed
"machinery, not a test module" naming. Import from it rather than
copying.

**Still local, and this is the load-bearing half:** each module keeps
its own `_Context` dataclass, its own `@given`/`@when`/`@then` bodies,
and any double only it needs (`test_piso_pressure_coupling.py`'s
`_ZeroNormalVelocity`, `test_periodic_boundary.py`'s
`_InertLinearSolver`/`_InertPressureCoupling`,
`test_simulation.py`'s `_EchoAdvection`). Sharing a *step definition*
would mean sharing the context it populates, coupling nine tasks'
fixture objects into one type -- which is exactly the risk the older
blanket convention was right about, and the reason the shared thing is a
helper module rather than a `tests/unit/conftest.py`. **When a fixture
detail genuinely differs, copy it rather than adding a parameter to the
shared one**: `test_periodic_boundary.py` needs
`face_normal_velocity_toward`'s explicit `neighbour` because a periodic
face has no mesh-reported neighbour, and that difference is visible at
the call site precisely because it was not hidden behind a default.
