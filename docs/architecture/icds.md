# Interface Contract Definitions (ICDs)

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
`engine/numerics/assembly.py`'s `assemble_numerics(NumericsConfig) ->
AssembledNumerics` resolves each configured name to a live instance
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
`DuplicateSchemeError` enforces at import time. The other five names
still resolve to their own reference implementation until their own
task lands.

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

**Choices:** `central_difference` (the only implementation; MVP). Future:
improved geometric/non-orthogonal handling
(`upgrade-paths.md` "Diffusion").

**Configuration control:** `numerics.diffusion` (implemented, Stage 3).

**Compatibility requirements:** none yet documented; see Advection's note
above -- the same applies here.

**Expected behaviour:** second-order accurate on orthogonal (Cartesian)
meshes, matching the MVP's mesh choice exactly.

**Limitations:** accuracy degrades on non-orthogonal or skewed meshes --
not a concern for the MVP's uniform Cartesian mesh, but a real limitation
once the Mesh layer's own upgrade path (structured → unstructured)
progresses ahead of this one.

---

## Time Integrator

**Represents:** advancing the full simulation state forward by one
timestep, given the state and its time derivative from the other layers.

**Choices:** `rk4` (the only implementation; MVP). Future: Euler, RK2,
adaptive RK, implicit integration (`upgrade-paths.md` "Time
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

**Choices:** `piso` (the only implementation; MVP). Future: SIMPLE,
SIMPLEC, or other strategies depending on whether the simulation is
transient or steady-state (`upgrade-paths.md`
"Pressure–Velocity Coupling" -- these are not strictly "more advanced"
than PISO, only suited to different regimes; a future configuration
should let a user pick deliberately, not assume one dominates).

**Configuration control:** `numerics.pressure_coupling` (implemented, Stage 3).

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

---

## Linear Solver

**Represents:** solving the linear system Pressure–Velocity Coupling (and
any other implicit step) produces.

**Choices:** `conjugate_gradient` (the only implementation; MVP). Future:
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

**Expected behaviour:** each condition type supplies the face value
(Dirichlet), face gradient (Neumann), or wrapped-neighbour reference
(periodic) the interior advection/diffusion schemes need at that face.

**Limitations:** limited to simple, axis-aligned domain edges -- internal
boundaries and arbitrary-geometry surfaces are explicitly future work,
not a current gap being worked around.

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
