# CLAUDE

TASK-018's five operator interfaces: `advection.py`, `diffusion.py`,
`gradient.py`, `divergence.py`, `source.py` -- one `ABC` each, no
concrete implementation under `src/` through Stage 3 (Stage 3 Completion
Criterion 1, `docs/planning/roadmap.md`). `boundary_condition.py`
(TASK-019, done 2026-08-23), `time_integrator.py` (TASK-020, done
2026-08-23) and `linear_solver.py` (TASK-022, done 2026-08-23, built
before TASK-021 despite the number) join them the same way.
`pressure_coupling.py` (TASK-021, done 2026-08-23, Stage 3's last task)
completes the set. **`advection.py` stopped being interface-only on
2026-08-27 (TASK-023, Stage 4)**: `FirstOrderUpwindAdvection` is the
first real concrete scheme anywhere in this subpackage -- see
`src/pyflow/engine/CLAUDE.md`'s own entry for it, and its own
`boundary_face_name` addition to `mesh.py`, for the full design
rationale. **`diffusion.py` followed the same day (TASK-024)**:
`CentralDifferenceDiffusion` is the second real concrete scheme -- see
that same `CLAUDE.md`'s own entry for it, and its own
`Mesh.face_centroid_distance` addition (concrete on the abstract `Mesh`
itself, unlike `boundary_face_name`), for the full design rationale.
**`time_integrator.py` followed the next day (TASK-025)**:
`RK4Integrator` is the third real concrete scheme -- see that same
`CLAUDE.md`'s own entry for it. **This one is different in kind from the
two before it: landing it required revising the interface itself, not
just adding an implementation.** `TimeIntegrator.advance`'s `derivatives`
parameter (a single precomputed snapshot) could not supply what RK4's
own multi-stage evaluation needs -- widened to a re-evaluatable
`Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]`, recorded
as `adr/ADR-008-time-integrator-derivative-callable.md`. Every existing
`TimeIntegrator` implementation (including test-only doubles in
`tests/unit/numerics/test_time_integrator_contract.py` and
`tests/unit/test_simulation.py`) needed its call site adapted as a
result -- the first time landing a Stage 4 MVP scheme has required
touching a Stage 3 interface's own signature, not only its registry
entry.

**`linear_solver.py` followed the next day (TASK-026)**:
`ConjugateGradientSolver` is the fourth real concrete scheme, and lands
the same way advection/diffusion did -- no interface change needed this
time, only `register_linear_solver`'s factory type widening from
zero-arg to `Callable[[float, int], LinearSolver]` (mirrors
`register_diffusion_scheme`'s own `diffusion_coefficient` precedent).
See that same `CLAUDE.md`'s own entry for the real content: a genuine
correctness trap in the handbook's own "project the constant mode out
each iteration" guidance (unconditional projection silently solves a
different problem for a well-conditioned system), caught by a numerical
prototype before any code was written, and an honest mutation-testing
finding that the projection's own necessity could not be demonstrated at
any fixture size this repository can realistically test -- recorded as
such rather than presented as verified when it was not.

**`pressure_coupling.py` followed the next day (TASK-027), and this time
took `gradient.py`/`divergence.py` with it.** `PISO` is the fifth real
concrete scheme, and `GreenGaussGradient`/`GreenGaussDivergence` are the
first real concrete implementations of `GradientScheme`/
`DivergenceScheme` -- built and owned by `PISO` directly rather than
resolved through `assembly.py`'s registry, since neither interface is
one of `adr/ADR-003`'s six configuration-selected components. **A real
interface change again, the second since `time_integrator.py`'s**:
`PressureCoupling.correct` gained a second parameter, `dt`, recorded as
`adr/ADR-009-pressure-coupling-dt.md`. See `src/pyflow/engine/CLAUDE.md`'s
own entries for the real content: `PISO` performs a single, real
correction pass rather than the full multi-pass Issa algorithm, an
honestly-scoped limitation found and resolved by numerical investigation
before any implementation code was written -- PyFlow's collocated mesh
needs Rhie-Chow interpolation (and momentum-equation coefficients this
task's own interface has no way to obtain) to suppress pressure-velocity
decoupling under repeated correction, which composing this task's own
`Gradient`/`Divergence` into a Poisson matrix cannot substitute for
(proven not symmetric, both algebraically and numerically). That
stronger claim belongs to Stage 5 TASK-033, not this task --
`docs/practices.md`'s "A criterion whose strong reading depends on a
later task must say so when drafted" is the standing rule this finding
produced.

**`boundary_condition.py` followed the next day (TASK-028), and this
time only Dirichlet's own half.** `DirichletBoundaryCondition` is the
sixth real concrete scheme, sharing the module with the interface the
same way every other Stage 4 concrete scheme does. No interface change
(unlike `time_integrator.py`'s/`pressure_coupling.py`'s own widenings),
only a small registry-adapter swap (`assembly.py`'s
`_dirichlet_boundary_condition`). See `src/pyflow/engine/CLAUDE.md`'s own
entry for the real content: a genuine config-surface gap (found and
closed in the same task, not left implicit) where the reference
implementation this task retires had been reading `velocity` regardless
of which field asked -- correct by accident for Stage 3's own golden
demo, which advects nothing, but a plausible-looking wrong answer waiting
for the first real scalar-transport Dirichlet boundary. Neumann's own
half is still `_NullGradientBoundaryCondition`, not yet reached
(TASK-029) -- that task's own drafting inherits a narrower version of the
same gap (no scalar-gradient field yet either), named explicitly rather
than left to be rediscovered (`docs/planning/roadmap.md` TASK-029's own
Intent).

**`boundary_condition.py` finished the same day (TASK-029), Neumann's own
half.** `NeumannBoundaryCondition` is the seventh real concrete scheme --
and the last of the six `adr/ADR-003` components to go real, closing
Stage 3 Completion Criterion 1's carve-out for good, zero `_Null*`
reference implementations remaining anywhere in `assembly.py`. Same
shape as Dirichlet's own join: no interface change, one adapter swap
(`_neumann_boundary_condition`), `BoundaryFaceConfig.scalar_gradient`
resolving the inherited gap named above. See
`src/pyflow/engine/CLAUDE.md`'s own entry for the real content, including
a mutation-caught test-quality finding in `test_assembly.py`'s own
fixture (a coincidentally-shared `0.0` had let a wrong-field regression
pass unnoticed, fixed per `docs/practices.md`'s "distinct factors" rule).

**`assembly.py`** (TASK-021) is different in kind from the interfaces above:
not an interface, but the registry (`register_advection_scheme` and five
siblings) and `assemble_numerics(NumericsConfig) -> AssembledNumerics`
that resolve a configured name to a live instance of one. It was also
this subpackage's **one exception to "no concrete implementation under
`src/`", through Stage 3 and the first eight days of Stage 4** -- a small
set of trivial, non-physical reference classes, registered by default
under the exact MVP names, existed solely so a real `pyflow run`
subprocess had something to assemble into for Stage 3's golden demo.
Named and documented as reference implementations throughout, never as
real ones, and **retired one by one by the Stage 4 task that replaced
each** -- `DuplicateSchemeError` makes shadowing one instead of deleting
it an import-time error. **The last two retired the same day (TASK-028,
TASK-029, 2026-08-28): zero `_Null*` reference implementations remain.**
See the module's own docstring and `src/pyflow/engine/CLAUDE.md`'s
`numerics/` entry for the full retirement history and the exception's own
now-closed record against Stage 3 Completion Criterion 1.

Full design rationale -- why a subpackage, why every operator takes
`Field` rather than a concrete subclass, why the return shapes split
face-valued (Advection/Diffusion) from cell-valued
(Gradient/Divergence/Source), the `_check_velocity`/`_check_boundary_face`
rejection pattern, `BoundaryCondition`'s `kind`-property design, why
`TimeIntegrator.advance` takes a `Mapping[str, Field]` with no analogous
`_check_...` helper, why `LinearSolver.solve` takes a plain dense
`matrix`/`rhs` pair rather than a dedicated "system" type, and
`PressureCoupling`'s real `isinstance` guard on its constructor argument
-- lives in the parent `src/pyflow/engine/CLAUDE.md`'s `numerics/` entry,
not repeated here.
