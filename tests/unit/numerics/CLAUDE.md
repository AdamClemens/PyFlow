# CLAUDE

Contract test suites for TASK-018's five operator interfaces
(`src/pyflow/engine/numerics/`) -- one file per interface, each
parametrised over two test-only implementations plus a deliberately
inert third one, per Stage 3 Completion Criterion 2
(`docs/planning/roadmap.md`). Isolated logic, no process boundary --
same scope as the rest of `tests/unit/`, see `tests/unit/CLAUDE.md`.

**`test_advection_contract.py` gained a real fourth fixture,
`FirstOrderUpwindAdvection` (TASK-023, 2026-08-27), alongside its two
test-only ones and the deliberately inert third** -- Stage 4 Completion
Criterion 3, joined by adding one factory (`_first_order_upwind_advection`,
wired with a uniform zero-gradient `BoundaryCondition` on all four edges
so the suite's own generic velocity/field fixtures never hit an
unconfigured inflow boundary) with no edit to any existing test body in
the file. Its own physical-correctness claims -- this suite only checks
shape, "varies with input", and the incompatible-velocity rejection, per
Stage 4 Completion Criterion 3's "passing that suite is necessary and
explicitly not sufficient" -- are `tests/features/
first_order_upwind_advection.feature`, bound by
`tests/unit/test_first_order_upwind_advection.py`.

**`test_diffusion_contract.py` gained a real third fixture,
`CentralDifferenceDiffusion` (TASK-024, 2026-08-27), the same way
`test_advection_contract.py` gained its own real fourth one** -- Stage 4
Completion Criterion 3, joined by adding one factory
(`_central_difference_diffusion`, wired with a uniform zero-gradient
`BoundaryCondition` on all four edges, the identical reasoning
advection's own join used) with no edit to any existing test body in the
file. Its own physical-correctness claims are `tests/features/
central_difference_diffusion.feature`, bound by `tests/unit/
test_central_difference_diffusion.py`.

`test_boundary_condition_contract.py` (TASK-019, done 2026-08-23) joins
them, minus the "inert implementation" teeth-check the other five use:
a real Dirichlet condition is *supposed* to return the same prescribed
value regardless of the field it's handed, so "varies with input" isn't
a property this interface has to prove -- its own two test-only
implementations (one value-shaped, one gradient-shaped) already
demonstrate two genuinely different behaviours without it.

`test_time_integrator_contract.py` (TASK-020, done 2026-08-23) also
skips that third class, for a different reason than boundary condition's:
this interface's own acceptance criteria already supply both halves the
inert-implementation pattern exists to prove -- the zero-derivative case
is the boundary an inert (ignores-its-input) implementation would also
pass, and the nonzero "same values, same result regardless of source"
case is the one it would fail. Its own two test-only implementations
(`_EulerIntegrator`, `_DoubleStepIntegrator`) have genuinely different
arithmetic rather than genuinely different shapes.

**`test_time_integrator_contract.py` gained a real third fixture,
`RK4Integrator` (TASK-025, 2026-08-27) -- unlike every other join in this
file, it did not arrive by adding a factory alone.** `TimeIntegrator.
advance`'s second parameter was widened from a precomputed
`Mapping[str, torch.Tensor]` to a re-evaluatable
`Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]`
(`adr/ADR-008-time-integrator-derivative-callable.md`), so every test
already in this file needed its call site adapted (`_EulerIntegrator`/
`_DoubleStepIntegrator` now call `derivative(fields)` instead of indexing
a dict; every test building a fixed derivative wraps it with a small
local `_constant_derivative` helper) before `_rk4_integrator` could be
added to `_FACTORIES` alongside them. Recorded here as a genuinely
different shape of change from `test_advection_contract.py`'s/
`test_diffusion_contract.py`'s own joins (both "add a factory, edit
nothing existing") rather than presented as the same pattern.

`test_linear_solver_contract.py` (TASK-022, done 2026-08-23) follows the
same no-third-class reasoning as time integrator's: "returns the known
solution within tolerance" and "reports non-convergence" together
already prove both halves, since an exact direct solve structurally
cannot fail to converge and so cannot stand in for the inert case
either way. Its two test-only implementations (`_ExactSolver`,
`_JacobiSolver`) are genuinely different strategies (direct vs.
iterative), the same shape of difference `TimeIntegrator`'s two
implementations use (different arithmetic) rather than
`BoundaryCondition`'s (different shapes).

`test_pressure_coupling_contract.py` (TASK-021, done 2026-08-23, Stage
3's last task) also has no third class -- its own Acceptance Criteria
name no "varies with input" case at all, unlike `TimeIntegrator`'s or
`LinearSolver`'s, so there is nothing for a teeth-check to prove. Its two
test-only strategies (`_PassthroughCoupling`, `_ScaledCoupling`) are
genuinely different arithmetic, the same shape of difference
`TimeIntegrator`'s use, each constructed with a local test-only
`LinearSolver` -- Stage 3 Completion Criterion 6 made structural.

`test_assembly.py` (TASK-021) is not a contract suite for an interface --
it's the in-process unit suite for `assemble_numerics` and the six
registries `engine/numerics/assembly.py` builds, covering Stage 3
Completion Criteria 3 (registering a name no `src/` module knows
resolves with no edit to `assemble_numerics`'s body) and 4 (mutating a
`NumericsConfig` after assembly changes nothing already assembled), plus
dedicated tests for each reference ("null") implementation's own claimed
behaviour -- `assemble_numerics` only proves these construct, not that
they do what their docstrings say. It also covers registration itself:
registering a different factory under a name already taken raises
`DuplicateSchemeError`, while re-registering the identical factory does
not, which is the Stage 4 hand-over guard (see
`src/pyflow/engine/CLAUDE.md`'s `assembly.py` entry).

Every interface in this package has a contract suite; Stage 3's own
`tests/golden/test_numerics_assembly.py` (binding
`tests/features/numerics_assembly.feature`) is the end-to-end
counterpart, run through the real CLI rather than in-process.

**`test_assembly.py`'s `_TestOnlyAdvection`/`_OtherTestOnlyAdvection`
gained a `boundary_conditions` constructor parameter (ignored) in
TASK-040**, matching `register_advection_scheme`'s new factory shape
(`src/pyflow/engine/CLAUDE.md`'s `assembly.py` entry) -- registering
either class as a zero-arg factory would now fail the moment
`assemble_numerics` calls it with one argument. Two rejection-path tests
were added in the same change (`test_unknown_diffusion_name_raises_named`,
`test_unknown_time_integration_name_raises_named`): advection and
diffusion used to share `_resolve`'s own `UnknownSchemeError` line, so
one test covered all three by line-coverage accident; splitting
diffusion into its own inline resolution (boundary-conditions-first
reordering) left that line genuinely untested until this suite's own
Blast Radius check caught it. A third,
`test_unknown_linear_solver_name_raises_named`, was added afterward for
symmetry -- linear_solver shares `_resolve`'s line with time_integration
and had never had a test of its own either, a pre-existing gap this
change's own review cycle happened to surface rather than create.

**`_CapturingAdvection` and two more tests were added in TASK-040's own
review cycle, not its first pass.** Every other test-only advection
scheme in this module discards its `boundary_conditions` constructor
argument, so none of them would fail if `assemble_numerics` silently
passed an empty or stale mapping instead of the one it just resolved --
`_CapturingAdvection` records what it actually received, and
`test_advection_and_diffusion_factories_receive_the_resolved_boundary_conditions`
checks it against `assembled.boundary_conditions` directly.
`test_boundary_conditions_is_immutable` checks the same mapping is a
genuine `MappingProxyType`, not a plain `dict` a caller (or a future
scheme) could mutate out from under the other holder -- see
`src/pyflow/engine/CLAUDE.md`'s `assembly.py` entry for why that mattered.

**`_CapturingDiffusion` and its own test (TASK-024, 2026-08-27) are the
diffusion analogue, one argument wider.** `register_diffusion_scheme`'s
factory gained a second parameter, `diffusion_coefficient`
(`NumericsConfig.diffusion_coefficient`, Gamma), threaded the same
"constructed with it" way `boundary_conditions` was -- every other
test-only `DiffusionScheme` double in this module discards its
constructor arguments, so `_CapturingDiffusion` records both the
boundary-conditions mapping *and* the coefficient it received;
`test_diffusion_factory_receives_the_resolved_boundary_conditions_and_coefficient`
checks both against the assembled config's own values. `_NullDiffusionScheme`
was deleted in the same task rather than updated to accept the new
parameter, since TASK-024 replaced it wholesale
(`src/pyflow/engine/CLAUDE.md`'s `assembly.py` entry).

**`test_null_time_integrator_returns_unchanged_copies` was replaced by
`test_default_config_resolves_a_real_time_integrator` (TASK-025,
2026-08-27)**, the same shape the diffusion/advection real-scheme
resolution tests already established immediately above it in this file
-- `_NullTimeIntegrator` no longer exists to have its own behaviour
checked; `assemble_numerics(NumericsConfig())` now resolves `"rk4"` to a
real `RK4Integrator` instance, checked by `isinstance`.

**`test_linear_solver_contract.py` gained a real third fixture,
`ConjugateGradientSolver` (TASK-026, 2026-08-27) -- unlike
`test_time_integrator_contract.py`'s own join, this one is a real
"add a factory, edit nothing existing" join**, since `LinearSolver.
solve`'s signature needed no change. A new generic test,
`test_a_zero_right_hand_side_solves_to_the_zero_vector_immediately`
(parametrised over all three factories, `exact`/`jacobi`/
`conjugate_gradient`), was added alongside the join -- not a
TASK-026-specific check smuggled into the shared suite, but a claim true
for any `LinearSolver`, found worth adding while confirming
`ConjugateGradientSolver`'s own early-convergence branch was genuinely
exercised rather than dead code (100% coverage was reachable this way
without inventing an implementation-specific test file the way
`Mesh`/`StructuredCartesianMesh` split into contract-suite-plus-own-file
-- no Stage 4 concrete scheme has needed that second file so far).

**`test_null_linear_solver_reports_unconverged_zero_solution` was
replaced by `test_default_config_resolves_a_real_linear_solver`
(TASK-026, 2026-08-27)**, the same shape the three real-scheme resolution
tests above it already established -- `_NullLinearSolver` no longer
exists to have its own behaviour checked; `assemble_numerics(
NumericsConfig())` now resolves `"conjugate_gradient"` to a real
`ConjugateGradientSolver` instance, checked by `isinstance`.

**`test_pressure_coupling_contract.py` gained a real third fixture,
`PISO` (TASK-027, 2026-08-27) -- unlike `test_time_integrator_contract.py`'s
own join, `correct`'s widened signature (`adr/ADR-009-pressure-coupling-dt.md`)
was already paid for by that ADR's own migration, so this suite's join
only needed a factory and a `dt` argument at each existing call site, not
a rewrite of either test-only strategy's own arithmetic.** `_piso`
constructs `PISO` with a local test-only `_ZeroNormalVelocity`
`BoundaryCondition` alongside the suite's own `_StubLinearSolver`, since
`PISO`'s own constructor needs both.

**`test_gradient_contract.py`/`test_divergence_contract.py` each gained a
real third fixture, `GreenGaussGradient`/`GreenGaussDivergence`
(TASK-027, 2026-08-27) -- the same "add a factory, wire a uniform
zero-gradient `BoundaryCondition`" join `test_advection_contract.py`'s
own `FirstOrderUpwindAdvection` join established.** Each suite also
gained two dedicated tests neither existing test-only fixture has the
logic to exercise generically: an exact-for-a-linear-field check (the
Green-Gauss reconstruction's own physical-correctness claim, verified
against a real non-trivial linear field, `docs/practices.md`'s "distinct
factors" rule) and an `UnconfiguredBoundaryFaceError` check (the periodic
case). `test_divergence_contract.py` gained a third,
`IncompatibleVectorFieldError`, for a field whose `component_shape`
doesn't match the mesh's spatial dimensionality -- `GreenGaussGradient`
has no analogous check, since a scalar gradient's input has no
"incompatible shape" to reject the way a vector-only divergence does.

**`test_null_pressure_coupling_returns_unchanged_velocity_and_zero_pressure`
was replaced by `test_default_config_resolves_a_real_pressure_coupling`
(TASK-027, 2026-08-27)**, the same shape the four real-scheme resolution
tests above it already established -- `_NullPressureCoupling` no longer
exists to have its own behaviour checked; `assemble_numerics(
NumericsConfig())` now resolves `"piso"` to a real `PISO` instance,
checked by `isinstance`. **A new capture test,
`test_pressure_coupling_factory_receives_the_resolved_boundary_conditions`,
was added alongside it** -- the pressure-coupling analogue of
`test_diffusion_factory_receives_the_resolved_boundary_conditions_and_coefficient`
above, proving `assemble_numerics` actually threads the resolved mapping
into the pressure-coupling factory too, not just advection/diffusion,
via a local `_CapturingPressureCoupling` test double.

**`test_boundary_condition_contract.py` gained a real third fixture,
`DirichletBoundaryCondition` (TASK-028, 2026-08-28) -- a real "add a
factory, edit nothing existing" join, the same shape
`test_linear_solver_contract.py`'s own `ConjugateGradientSolver` join
used**, since this interface's `evaluate`/`kind` needed no change. A new
dedicated test, `test_dirichlet_boundary_condition_reports_its_kind_and_value`,
covers its own specific claim (kind `"value"`, the exact prescribed
number), the same shape `_FixedValueCondition`'s own dedicated test
already established for the test-only double it replaces as the real
third fixture.

**`test_null_boundary_conditions_evaluate_the_configured_value` was
renamed `test_boundary_conditions_evaluate_the_configured_value` and its
own fixture rewritten (TASK-028, 2026-08-28)** -- its Dirichlet-typed
faces now read `scalar_value`, not `velocity`/`pressure`
(`BoundaryFaceConfig`'s new field, `src/pyflow/configuration/CLAUDE.md`'s
own entry); the previous version was asserting the pre-TASK-028
semantics, which TASK-028's own Design decision found to be a live gap,
not merely stale test data. **`test_default_config_resolves_a_real_
dirichlet_boundary_condition` was added alongside it**, the same shape
the five real-scheme resolution tests above it already established --
every default-config boundary face is `"dirichlet"`
(`BoundaryFaceConfig`'s own default), so all four now resolve to the real
`DirichletBoundaryCondition`, checked by `isinstance`.

**`test_boundary_condition_contract.py` gained a real fourth fixture,
`NeumannBoundaryCondition` (TASK-029, 2026-08-28) -- the same "add a
factory, edit nothing existing" join Dirichlet's own used**, since this
interface's `evaluate`/`kind` needed no change either time. A new
dedicated test, `test_neumann_boundary_condition_reports_its_kind_and_gradient`,
covers its own specific claim (kind `"gradient"`, the exact prescribed
number), the same shape the value-side dedicated test already
established.

**`test_boundary_conditions_evaluate_the_configured_value`'s own Neumann
fixture was rewritten again (TASK-029, 2026-08-28)** -- reads
`scalar_gradient`, not `velocity`/`pressure`/`0.0`
(`BoundaryFaceConfig`'s new field). **Given a `velocity` deliberately
distinct from `scalar_gradient`, found necessary by mutation testing, not
assumed sufficient by inspection**: the fixture used previously
(`scalar_gradient=0.0`, `velocity=None`) happened to equal
`_null_boundary_value`'s own old fallback for an unset `velocity`, so a
deliberate mutation (`assembly.py`'s Neumann adapter reading `velocity`
instead of `scalar_gradient`) passed this test unnoticed; re-verified
against the same mutation after the fix, now caught
(`docs/practices.md`'s "distinct factors" rule).
**`test_a_neumann_typed_config_resolves_a_real_neumann_boundary_condition`
was added alongside it**, the same shape the six real-scheme resolution
tests above it already established -- built against an explicit
`"neumann"`-typed config, not the default one, since every default face
is `"dirichlet"` (`BoundaryFaceConfig`'s own default has no Neumann face
to check by default).
