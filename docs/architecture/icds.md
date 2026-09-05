# Interface Contract Definitions (ICDs)

Checked-by: stage-boundary

Per `docs/planning/knowledge-architecture.md` KA-030. Defines the
user/configuration-facing contracts by which PyFlow's replaceable
numerical components are selected and described.

**Scope, per KA-030:** these are the interfaces exposed to a user through
configuration -- what you can choose, and what choosing it guarantees --
not every internal Python interface between engine modules. An internal
interface (e.g. exactly how an `AdvectionScheme` object is called by the
timestepper) belongs in code and its own module-level documentation, not
here, unless it's useful to a user trying to understand what a choice
does.

This document assumes `docs/architecture/engine.md`'s conceptual layers
and does not re-explain them. It exists to unblock Stage 3
(`docs/planning/roadmap.md` TASK-018..022, "Operator Interfaces") having
something concrete to implement against, per `docs/planning/backlog.md`.

---

## Which Layers Get an ICD

`adr/ADR-003-modular-numerical-strategies.md` names exactly six
components as independently replaceable and configuration-selected:
advection scheme, diffusion scheme, time integrator, pressure-velocity
coupling strategy, linear solver, and boundary condition type. Those six
get an ICD below.

**Mesh and Variables (`engine.md`'s other two layers) do not, yet --**
and wouldn't even once a second option exists, since `ADR-003` names
exactly the six components above, not these two. Both currently have
exactly one implementation *built* (structured Cartesian mesh, collocated
arrangement). TASK-011 (`docs/planning/roadmap.md`, 2026-08-19) is the
first departure from "no second option anywhere": its `CoordinateSystem`
interface is deliberately designed not to assume vertex placement, and
the task explicitly plans a second, cell-center-based implementation for
later -- not built yet, so still not a real choice to write a contract
for, but no longer purely speculative either, since it's now named
future work rather than an unconsidered possibility. Write an ICD if
and when this or any other layer actually joins `ADR-003`'s six -- not
before, per P-016 (prefer reversible decisions until understanding
justifies commitment).

**Source Term does not get one either, and that is a decision, not an
omission -- recorded 2026-08-31 by the Stage 6 exit audit, which found
this document silent about it.** `NumericsConfig.source_term`
(TASK-035, Stage 6, 2026-08-30) is a real, validated, user-facing
configuration key with two choices today -- `"none"` and
`"boussinesq_buoyancy"` -- resolved through `assembly.py`'s registry
exactly as the six below are, so a reader who found nothing about it
here would reasonably conclude it did not exist. It stays out of the
ICD set because `adr/ADR-003` deliberately keeps its six at six
(that stage's own design question two, and Criterion 2): a first
concrete implementation of an interface is not the same claim as a
component a user chooses *between*, which is what an ICD specifies.
`"none"` is not a rival scheme -- it is the permanent, supported
"no body force in this run" answer. **The trigger for writing one is
the same as for Mesh and Variables above: a second real source term,
where a user genuinely has to choose.** Until then the contract lives
in `src/pyflow/engine/numerics/source.py`'s own docstring and
`adr/ADR-010-source-term-state.md`, and `docs/architecture/engine.md`'s
Time Integration entry is where the `+ source` in the governing
equation is named.

---

## Contract Shape

Each ICD below follows KA-030's required structure: what it represents,
what choices exist, what configuration controls, compatibility
requirements, expected behaviour, and limitations.

**Configuration mechanism (implemented, Stage 3, done 2026-08-23):**
`NumericsConfig` (`src/pyflow/configuration/schema.py`) follows the same
shape every other configuration section does -- a dataclass field with a
`Literal[...]` type listing the valid choices by name, validated
immediately and explicitly in `validate()` rather than left to fail
wherever the value is first used (`rendering.backend`'s precedent).
`engine/numerics/assembly.py`'s `assemble_numerics` resolves each
configured name to a live instance
through a registry keyed by name, populated by `register_*` calls rather
than a chain `assemble_numerics` itself branches on -- adding a name
requires no edit to that function's body (Stage 3 Completion
Criterion 3). **Through Stage 3, no real numerical scheme registered
under any of these names** (Criterion 1): the registry's entries were
trivial, non-physical reference implementations that existed solely so
the mechanism itself had something to prove against. Stage 4 replaces
each in turn, `advection` first (TASK-023, 2026-08-27): `"first_order_upwind"`
now resolves to `FirstOrderUpwindAdvection`, a real scheme, with no
schema change required -- *replacing* that name's reference
registration rather than shadowing it, which `assembly.py`'s
`DuplicateSchemeError` enforces at import time. `diffusion` followed the
same day (TASK-024): `"central_difference"` now resolves to
`CentralDifferenceDiffusion`.

**All six resolve to a real scheme as of TASK-029 (Stage 4, closed
2026-08-28), and `assembly.py` holds zero `_Null*` reference classes.**
This paragraph ended "The other four names still resolve to their own
reference implementation until their own task lands" until 2026-08-31,
three days and a whole stage after that stopped being true -- the same
sentence, about the same four names, that the Stage 5 exit audit had
already found and fixed in `src/pyflow/configuration/schema.py`'s
`NumericsConfig` docstring on 2026-08-29. That sweep did not reach this
file. `adr/ADR-003-modular-numerical-strategies.md` tracks each
component's realisation task by task and is authoritative for which is
which; this section describes the *mechanism*, and a status sentence
inside it is exactly the kind of restated fact `docs/practices.md`
("Let a checked artifact carry status, not a tense") asks not to write
here.

---

## Advection

**Represents:** the scheme computing a field's advective flux
contribution at each mesh face, given the field and the velocity field
transporting it.

**Choices:** `first_order_upwind` (the only implementation; MVP,
`docs/implementation/mvp.md`). Future: central difference, QUICK, TVD,
WENO (`docs/implementation/upgrade-paths.md` "Advection").

**Configuration control:** `numerics.advection` (implemented, Stage 3).

**Compatibility requirements:** none yet documented as a live constraint
-- with exactly one implementation, there is nothing to be incompatible
with. `adr/ADR-003`'s Negative consequences flag that advection/diffusion
combinations can have stability interactions in general; once a second
advection scheme exists, any real interaction found should be recorded
here, not left implicit.

**Expected behaviour:** first-order upwind is numerically diffusive but
unconditionally *bounded* -- it cannot manufacture a value outside the
range of the neighbours it interpolates between. Boundedness is not
stability: the timestep must still satisfy the configured integrator's CFL
limit (`docs/handbook/numerical-methods/advection.md`,
`time-integration.md`). Appropriate for MVP correctness validation, not
for accuracy-sensitive production use.

**Limitations:** first-order accuracy only; smooths sharp gradients more
than a user comparing against a higher-order reference might expect. The
artificial diffusivity this amounts to is roughly $\rho |u| \Delta x / 2$
for mesh-aligned flow and larger for oblique flow, so the error is
mesh- and speed-dependent rather than a fixed offset.

---

## Diffusion

**Represents:** the scheme computing a field's diffusive flux
contribution at each mesh face.

**Choices:** `central_difference` (the only implementation; MVP,
`docs/implementation/mvp.md`). Future: improved geometric/non-orthogonal
handling (`upgrade-paths.md` "Diffusion").

**Configuration control:** `numerics.diffusion` (implemented, Stage 3);
`fluid.diffusion_coefficient` (implemented, Stage 4, TASK-024) -- Gamma,
the diffusion coefficient the central-difference formula multiplies by.
A plain positive number, not a scheme choice (the same shape as
`numerics.timestep`), since it is a physical property of what's being
transported, not a discretisation decision. **That reasoning is why it
does not live under `numerics` at all: it moved to `FluidConfig` in
TASK-041 (2026-08-28, Stage 5's design question four), and this entry
still said `numerics.diffusion_coefficient` until 2026-09-04** -- found
while drafting Stage 8's completion criteria, which is a stage that
reads this ICD for what its own "improved diffusion" work would have to
change. A config setting the old name is rejected at load with a named
error pointing at the new one, so the stale entry named a field no run
could have used. Per-field overrides are
`fields.<name>.diffusion_coefficient`, and momentum's own diffusivity is
`fluid.viscosity` (TASK-031b).

**Compatibility requirements:** none yet documented as a live constraint
-- with exactly one implementation, there is nothing to be incompatible
with; see Advection's note above, which applies here too.

**Expected behaviour:** second-order accurate on a uniform orthogonal
mesh (`docs/handbook/numerical-methods/diffusion.md`) -- the interior
face-normal gradient is a centred difference, exact at the face itself
because the face lies midway between the two centroids on PyFlow's MVP
mesh. Not in tension with boundedness the way advection's own central
differencing is: diffusion's physical effect is itself smoothing, so no
spurious oscillation results from the same discretisation advection
would need a limiter for.

**Limitations:** the boundary-face flux formula (a one-sided difference
against a prescribed Dirichlet value, or the prescribed Neumann gradient
read directly) is not claimed to be second-order accurate at the
boundary itself -- only the interior formula carries that claim, and
`tests/features/central_difference_diffusion.feature`'s own convergence
scenario measures accordingly, against interior cells only. Assumes an
orthogonal mesh throughout; no non-orthogonal correction exists yet
(`upgrade-paths.md` "Diffusion").

**Expected behaviour:** second-order accurate on orthogonal (Cartesian)
meshes, matching the MVP's mesh choice exactly.

**Limitations:** accuracy degrades on non-orthogonal or skewed meshes --
not a concern for the MVP's uniform Cartesian mesh, but a real limitation
once the Mesh layer's own upgrade path (structured → unstructured)
progresses ahead of this one.

---

## Time Integrator

**Represents:** advancing the full simulation state forward by one
timestep, given the state and a function that computes its time
derivative at any state -- re-evaluatable, not a single precomputed
value, per `adr/ADR-008-time-integrator-derivative-callable.md`
(TASK-025): a multi-stage scheme like RK4 needs the derivative at
intermediate states within the step, which a fixed value cannot supply.

**Choices:** `rk4` (the only implementation; MVP -- real,
`src/pyflow/engine/numerics/time_integrator.py`, TASK-025). Future:
Euler, RK2, adaptive RK, implicit integration (`upgrade-paths.md` "Time
Integration").

**Configuration control:** `numerics.time_integration`/`numerics.timestep` (implemented, Stage 3).

**Compatibility requirements:** none yet documented; independent of
which advection/diffusion/pressure-coupling schemes are configured, by
construction (per `engine.md`'s core principle -- the integrator
consumes a time derivative, not the schemes that produced it).

**Expected behaviour:** fourth-order accurate in time *for the ODE system
it is handed*, explicit -- requires a timestep small enough to satisfy the
stability limit implied by the configured advection/diffusion schemes and
mesh spacing (not yet computed automatically; a fixed timestep is
configured directly for the MVP).

**Limitations:** explicit integration bounds the usable timestep by
stability rather than accuracy, which can make it the binding cost for
fine meshes -- the motivation for the implicit-integration end of its
upgrade path. Separately, **the finished solver's observed temporal order
will be well below four**, capped by first-order upwind advection
spatially and by the operator splitting in the pressure-velocity coupling
temporally (`docs/handbook/numerical-methods/time-integration.md`) --
expected behaviour for a projection-type incompressible solver, not a
defect, and stated here so a measured convergence rate is not read as
one.

---

## Pressure–Velocity Coupling

**Represents:** enforcing the incompressibility constraint by relating a
provisional velocity field back to a divergence-free one and the
pressure field consistent with it.

**Choices:** `piso` (the only implementation; MVP -- real,
`src/pyflow/engine/numerics/pressure_coupling.py`, TASK-027). Future:
SIMPLE, SIMPLEC, or other strategies depending on whether the simulation
is transient or steady-state (`upgrade-paths.md`
"Pressure–Velocity Coupling" -- these are not strictly "more advanced"
than PISO, only suited to different regimes; a future configuration
should let a user pick deliberately, not assume one dominates).

**Configuration control:** `numerics.pressure_coupling` (implemented,
Stage 3); `numerics.pressure_correction_tolerance`/
`numerics.pressure_correction_max_iterations` (implemented, Stage 5
TASK-033 -- the outer corrector loop's own tunables, distinct from
`numerics.linear_solver_tolerance`/`numerics.linear_solver_max_iterations`,
which govern each pass's inner solve).

**Compatibility requirements:** requires a configured Linear Solver to
solve the pressure-correction equation it produces each timestep -- the
one real cross-layer dependency among the six (every other layer here is
independent of the others' choice).

**Expected behaviour:** PISO is well suited to transient (time-accurate)
simulation, which matches the MVP's own scope -- a real-time visualised
flow, not a steady-state result.

**Limitations:** PISO's transient suitability is also a limitation for a
future steady-state use case, which is exactly what the SIMPLE/SIMPLEC
alternatives on its upgrade path exist to address -- not a defect to fix
within PISO itself.

**Done, TASK-027, 2026-08-27, with a real limitation recorded rather
than papered over**: `PISO` performed a single, real, dt-scaled pressure
correction (`u_corrected = u* - dt * grad(p)`, `p` solving the compact
Poisson equation `CentralDifferenceDiffusion`'s own already-symmetric
Laplacian gives), verified to measurably and boundedly reduce a
manufactured provisional field's divergence. **At that point it was not,
and did not claim to be, the full multi-pass Issa algorithm**: PyFlow's
mesh is collocated, and driving cell-centred divergence to near-zero
under *repeated* correction needs Rhie-Chow interpolation, which needs
momentum-equation coefficients this task's own interface had no way to
obtain -- verified directly (composing this task's own `Gradient`/
`Divergence` into a Poisson matrix produces one that is provably not
symmetric, so `ConjugateGradientSolver` cannot even solve it; three
correction strategies were tried and measured before settling on the
single-pass, compact-Laplacian design actually shipped). That stronger,
fully-converged claim was left to Stage 5 TASK-033 (Pressure Correction
Loop), which has real momentum-coupled state to iterate against --
`docs/planning/roadmap.md` TASK-027's own Design decision Two records
the full investigation, and `docs/practices.md`'s "A criterion whose
strong reading depends on a later task must say so when drafted" is the
standing rule this finding produced.

**Done, TASK-033, 2026-08-29: `PISO` is now genuinely multi-pass, and
the limitation above is resolved, not superseded by a rename.** The
question the paragraph above leaves open -- what carries the
momentum-equation coefficients Rhie-Chow needs, given PyFlow's momentum
predictor is fully explicit (RK4, no implicit assembly to draw a
coefficient from) -- resolved to `a_P = V/dt`: the unsteady term is the
only contribution to `a_P` for this architecture, and PyFlow's uniform
cell volume makes `V/a_P = dt` one constant for the whole mesh, needing
no new momentum-coefficient machinery. Pairing that correction with the
*same* compact Laplacian the Poisson matrix already uses -- not the
composed `Gradient`/`Divergence` pair TASK-027 tried and measured
failing -- restores the discrete adjoint property exactly; verified
numerically (both a linear and a nonlinear manufactured provisional
field converge to floating-point-exact zero divergence) before any
implementation code was written, the same prototype-first sequence
TASK-026/027 both used. `correct` now loops: each pass measures the
maximum cell divergence, records it, and either returns (at or below
`numerics.pressure_correction_tolerance`) or solves another correction,
up to `numerics.pressure_correction_max_iterations` passes before
raising `DivergenceDidNotConvergeError` rather than returning a
best-effort result. No change to `PressureCoupling.correct`'s own
signature, and no new ADR -- the outer-loop tolerance/iteration-limit
state is bound at `PISO`'s own construction, the same "strategy owns its
own tunables" shape `ConjugateGradientSolver` already established, not a
widening of the shared interface. `docs/planning/roadmap.md` TASK-033's
own Design decisions record the full numerical investigation.

**Done, TASK-034, 2026-08-29: `PISO` gained periodic-boundary support,
and this stage's own timestep assembles the whole pipeline for real.**
Found while building Stage 5 Completion Criterion 4's own "uniform flow
on a fully periodic domain" null test: `PISO`'s pressure treatment had
no periodic case at all before this -- `GreenGaussGradient`/
`GreenGaussDivergence` raised `UnconfiguredBoundaryFaceError`
unconditionally for any periodic boundary face, which blocked even
*measuring* an already divergence-free field's divergence, let alone
correcting it. Both gained a `periodic_pairs` constructor parameter, the
same shape `CentralDifferenceDiffusion` already had since TASK-030;
`PISO` threads it to both plus its own `_rhie_chow_divergence` correction
loop, and to the Poisson matrix's own diffusion scheme, which had been
silently passed a hardcoded empty mapping regardless of what `PISO`
itself was told. Also new: `pyflow.engine.simulation.navier_stokes_step`,
the predictor/corrector/corrected-state assembly this ICD's own contract
implies but nothing before this task actually built -- momentum's own
components advance through the ordinary `step` path with no pressure
term (the predictor), the result is reassembled and handed to whichever
`PressureCoupling` was configured (the corrector), and the corrected
components replace the predictor's own. `docs/planning/roadmap.md`
TASK-034's own Design decisions record the full numerical investigation,
including the Poisson-matrix caching fix this task found needed while
measuring the Lid-Driven Cavity validation's own real runtime.

---

## Linear Solver

**Represents:** solving the linear system Pressure–Velocity Coupling (and
any other implicit step) produces.

**Choices:** `conjugate_gradient` (the only implementation; MVP -- real,
`src/pyflow/engine/numerics/linear_solver.py`, TASK-026). Future:
BiCGSTAB, GMRES, multigrid/preconditioned methods
(`upgrade-paths.md` "Linear Solvers").

**Configuration control:** `numerics.linear_solver`, `numerics.linear_solver_tolerance`, `numerics.linear_solver_max_iterations` (implemented, Stage 3).

**Compatibility requirements:** Conjugate Gradient requires a symmetric
positive-definite system -- true of the pressure-correction equation PISO
produces on the MVP's mesh, but a real constraint a future non-symmetric
system (from a different pressure-coupling strategy, or a different
governing equation) would violate. Record which linear solvers are valid
for which systems here once a second solver or system type exists.

A second, immediately live requirement: **when every boundary prescribes
velocity and none prescribes pressure -- the lid-driven cavity among the
MVP's own validation cases -- the pressure system is positive
*semi*-definite**, since pressure is fixed only up to an additive
constant. This implementation must remove that null space (pin a
reference cell, or project the constant mode out each iteration) and the
boundary values must satisfy global mass conservation; see
`docs/handbook/numerical-methods/pressure-velocity-coupling.md` and
`linear-solvers.md`. This is a precondition on the MVP configuration, not
a future concern.

**Done, TASK-026, 2026-08-27**: `ConjugateGradientSolver` detects this
case (the constant vector in `matrix`'s own null space) and projects it
out of the residual each iteration, gated on that detection rather than
applied unconditionally -- applying it unconditionally would silently
change the answer for a genuine full-rank system, verified directly
before this landed (`docs/planning/roadmap.md` TASK-026's own Design
decisions).

**Expected behaviour:** converges reliably for the MVP's
well-conditioned, uniform-mesh pressure system, once the null space above
is handled.

**Limitations:** convergence rate degrades as mesh resolution increases
without preconditioning -- the motivation for the
multigrid/preconditioned end of its upgrade path.

---

## Boundary Condition

**Represents:** how a field behaves at domain edges where no neighbouring
control volume supplies a flux.

**Choices:** `dirichlet`, `neumann`, `periodic` (where practical; MVP,
`docs/implementation/mvp.md`). Future: mixed conditions, internal
boundaries, arbitrary surfaces/geometries (`upgrade-paths.md` "Boundary
Conditions").

**Configuration control:** `numerics.boundary_conditions.{north,south,
east,west}.type` (implemented, Stage 3) -- a per-boundary-face selection
rather than a single simulation-wide choice, since different edges of the
same domain typically need different condition types; unlike the other
five ICDs, this one is not a single scalar choice. `assemble_numerics`
resolves `dirichlet`/`neumann` faces to a `BoundaryCondition` instance
through the same registry the other five components use, keyed by
`type`; a `periodic` face resolves no such instance --
`BoundaryCondition` (`src/pyflow/engine/numerics/boundary_condition.py`)
covers only the Dirichlet/Neumann shapes, per TASK-019's own scope, not
the "wrapped-neighbour reference" shape periodic's own Expected
behaviour below describes.

**Compatibility requirements:** `periodic` requires the paired boundary
(e.g. east paired with west) to also be `periodic` -- a periodic
condition on only one side of a domain is not physically meaningful.
Additionally, the set of boundary conditions must be jointly consistent,
not merely individually valid: velocity and pressure cannot both be
prescribed on the same boundary, and a configuration prescribing velocity
on every boundary must have those values sum to zero net flux, or the
pressure equation it produces has no solution at all
(`docs/handbook/numerical-methods/boundary-conditions.md`). This is a
whole-configuration constraint, which validation should check across
boundaries rather than per-face.

**A fourth requirement, added 2026-08-29 by the Stage 5 exit audit: a
`periodic` face may prescribe nothing.** It wraps to its pair and
resolves no `BoundaryCondition` instance at all (see the `Choices:` note
above), so `velocity`, `pressure`, `scalar_value`, `scalar_gradient`,
`field_values` and `field_gradients` are read by nobody on such a face.
Before this, setting one loaded cleanly and was then ignored outright --
a silently discarded instruction, which is the failure mode the other
three requirements here exist to prevent. Checked against *non-default*
values only, since `velocity` and both scalar fields default to `0.0`
rather than to a "not prescribed" sentinel, and a rule phrased as "is set
at all" would reject every periodic configuration this repository already
ships. This is Stage 5 Completion Criterion 6's second named rejection
surface, which no Stage 5 task discharged.

**Expected behaviour:** each condition type supplies the face value
(Dirichlet), face gradient (Neumann), or wrapped-neighbour reference
(periodic) the interior advection/diffusion schemes need at that face.

**Limitations:** limited to simple, axis-aligned domain edges -- internal
boundaries and arbitrary-geometry surfaces are explicitly future work,
not a current gap being worked around.

**Done, TASK-028, 2026-08-28, Dirichlet's own half**:
`DirichletBoundaryCondition` (`src/pyflow/engine/numerics/
boundary_condition.py`) is the first real implementation, replacing
`_NullValueBoundaryCondition` under the `"dirichlet"` name. Its own
prescribed value comes from `BoundaryFaceConfig.scalar_value`, a new
config field added by this task -- deliberately distinct from
`velocity`/`pressure` above, which stay reserved for the momentum/
pressure system's own Compatibility requirements (mutual exclusivity,
net flux); `scalar_value` carries neither.

**Done, TASK-029, 2026-08-28, Neumann's own half -- the same day**:
`NeumannBoundaryCondition` replaces `_NullGradientBoundaryCondition`
under the `"neumann"` name, reading `BoundaryFaceConfig.scalar_gradient`
(`scalar_value`'s exact mirror, same reasoning). **This closes Stage 3
Completion Criterion 1's carve-out for good**: all six `adr/ADR-003`
components now have a real concrete scheme, and zero `_Null*` reference
implementations remain in `assembly.py`.

**Done, TASK-030, 2026-08-28, periodic's own half -- Stage 4's last
task.** Not a `BoundaryCondition` implementation, as this document's own
"Expected behaviour" already anticipated (a "wrapped-neighbour reference"
is not a value or a gradient): `StructuredCartesianMesh.
wrapped_neighbour_cell(face) -> int` (`src/pyflow/engine/mesh.py`) is
the real mechanism, additive and off the abstract `Mesh` interface, since
"the opposite edge of the domain" has no meaning for a mesh with no
`(i, j)` structure. `assemble_numerics` still resolves no `Boundary
Condition` instance for a periodic face -- it now also builds a second,
separate mapping (`periodic_pairs`, `{face_name: opposite_face_name}`)
threaded into the advection/diffusion factories alongside
`boundary_conditions`, which is what a concrete scheme consults at a
periodic face instead. `mvp.md`'s "Periodic (where practical)" bullet is
now real, not aspirational.

---

## Not Yet Addressed: Plugin / Component Discovery

KA-030's **Enables** list names "future plugin/component discovery"
alongside implementation, configuration and UI labelling. This document
still does not address it, and that is deliberate rather than an
oversight: every choice below is a fixed `Literal[...]` of names known
at import time, validated against that closed set at `load_config`
time -- the mechanism `adr/ADR-003-modular-numerical-strategies.md`
explicitly preferred over "a full plugin/entry-point discovery system
from day one" (deferred there, not rejected).

**Stage 3 (`engine/numerics/assembly.py`) added an *internal*
extensibility mechanism that is easy to mistake for this one, and is
not it.** `assemble_numerics` resolves a configured name through a
registry a caller can add to (`register_advection_scheme` and its five
siblings) without editing `assemble_numerics`'s own body -- Stage 3
Completion Criterion 3. That registry is open; the configuration schema
is not. A user can still only *configure* one of the names each
`Literal[...]` above already lists -- registering a factory under a new
name makes that name resolvable in code, not choosable in YAML, since
`NumericsConfig.validate()` never consults the registry. Real
plugin/component discovery, in KA-030's sense, means a user-facing name
the schema didn't already enumerate becoming configurable, which still
does not exist.

What would change if discovery were added: the `Literal[...]` choice
lists become open sets validated against whatever is registered, and this
document's per-ICD "Choices" sections stop being exhaustive. Recorded
here so the gap between KA-030's Enables list and this document's scope
is visible, rather than reading as something forgotten.

---

## Definition of Done

Per KA-030's Intent: a user relying on this document should understand
the stable conceptual contract they're choosing among, without needing
to read the eventual implementation to find out what a choice does or
what it requires. This document is complete for Stage 0/3 purposes when
every ADR-003-named component has the six required sections above filled
in with real (even if currently single-choice) content -- not necessarily
when every future choice already exists.

## Maintenance

Written 2026-08-17 against `adr/ADR-003-modular-numerical-strategies.md`,
`docs/implementation/mvp.md`, `docs/implementation/upgrade-paths.md`, and
`src/pyflow/configuration/schema.py`'s existing pattern. The `numerics.*`
configuration keys were proposed then and **are implemented as of Stage
3 (2026-08-23, TASK-018..022)** with the exact names this document
already used -- updated in the same change, per `docs/practices.md`'s
Blast Radius rule, rather than left stale the way `engine.md`'s Variables
entry went a day unapplied during Stage 2. That failure recurred twice
more in Stage 3 and is now addressed structurally rather than by
diligence: `engine.md` states each layer's status by naming a module
path CI checks, not by a tense (`docs/practices.md`, "Let a checked
artifact carry status, not a tense").

Reviewed 2026-08-18 against the numerical-methods handbook, which was
written after this document and in places contradicts what it recorded.
Three ICDs changed: Advection's "unconditionally stable" became
"unconditionally bounded" (`docs/handbook/numerical-methods/fluxes.md`
explains why the distinction matters); Time Integrator's fourth-order
claim was scoped, since the finished solver's temporal order is capped by
upwind advection and by pressure-coupling splitting; and Linear Solver and
Boundary Condition gained the singular-pressure-system and
global-mass-conservation compatibility requirements, both of which apply
to the MVP's own validation cases rather than to a hypothetical future
configuration.
