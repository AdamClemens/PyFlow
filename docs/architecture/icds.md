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

**Mesh and Variables (`engine.md`'s other two layers) do not, yet.** Both
currently have exactly one implementation (structured Cartesian mesh,
collocated arrangement) with no second option anywhere in the codebase or
roadmap to choose between. An ICD for a choice that does not exist yet
would be speculative rather than a real contract -- write it when a
second mesh type or variable arrangement is actually being added
(`docs/implementation/upgrade-paths.md` "Mesh"/"Variables" describe where
that eventually goes), not ahead of it, per P-016 (prefer reversible
decisions until understanding justifies commitment).

---

## Contract Shape

Each ICD below follows KA-030's required structure: what it represents,
what choices exist, what configuration controls, compatibility
requirements, expected behaviour, and limitations.

**Configuration mechanism (proposed, not yet implemented):** every
existing configuration section (`LoggingConfig`, `RenderingConfig` in
`src/pyflow/configuration/schema.py`) follows the same shape -- a
dataclass field with a `Literal[...]` type listing the valid choices by
name, validated immediately and explicitly in `validate()` rather than
left to fail wherever the value is first used (see `rendering.backend`
for the working precedent). The six ICDs below assume a future
`numerics` configuration section following that same pattern -- e.g.
`numerics.advection: Literal["first_order_upwind"]` -- rather than
inventing a different mechanism. This is a naming proposal for whoever
implements TASK-018..022, not a commitment already made in code; treat
the exact section/field names as provisional until that implementation
lands, and update this document to match once it does.

---

## Advection

**Represents:** the scheme computing a field's advective flux
contribution at each mesh face, given the field and the velocity field
transporting it.

**Choices:** `first_order_upwind` (the only implementation; MVP,
`docs/implementation/mvp.md`). Future: central difference, QUICK, TVD,
WENO (`docs/implementation/upgrade-paths.md` "Advection").

**Configuration control:** proposed `numerics.advection`.

**Compatibility requirements:** none yet documented as a live constraint
-- with exactly one implementation, there is nothing to be incompatible
with. `adr/ADR-003`'s Negative consequences flag that advection/diffusion
combinations can have stability interactions in general; once a second
advection scheme exists, any real interaction found should be recorded
here, not left implicit.

**Expected behaviour:** first-order upwind is numerically diffusive but
unconditionally stable for the schemes it's typically paired with --
appropriate for MVP correctness validation, not for accuracy-sensitive
production use.

**Limitations:** first-order accuracy only; smooths sharp gradients more
than a user comparing against a higher-order reference might expect.

---

## Diffusion

**Represents:** the scheme computing a field's diffusive flux
contribution at each mesh face.

**Choices:** `central_difference` (the only implementation; MVP). Future:
improved geometric/non-orthogonal handling
(`upgrade-paths.md` "Diffusion").

**Configuration control:** proposed `numerics.diffusion`.

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

**Configuration control:** proposed `numerics.time_integration`.

**Compatibility requirements:** none yet documented; independent of
which advection/diffusion/pressure-coupling schemes are configured, by
construction (per `engine.md`'s core principle -- the integrator
consumes a time derivative, not the schemes that produced it).

**Expected behaviour:** fourth-order accurate in time, explicit --
requires a timestep small enough to satisfy the stability limit implied
by the configured advection/diffusion schemes and mesh spacing (not yet
computed automatically; a fixed timestep is configured directly for the
MVP).

**Limitations:** explicit integration bounds the usable timestep by
stability rather than accuracy, which can make it the binding cost for
fine meshes -- the motivation for the implicit-integration end of its
upgrade path.

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

**Configuration control:** proposed `numerics.pressure_coupling`.

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

**Configuration control:** proposed `numerics.linear_solver`.

**Compatibility requirements:** Conjugate Gradient requires a symmetric
positive-definite system -- true of the pressure-correction equation PISO
produces on the MVP's mesh, but a real constraint a future non-symmetric
system (from a different pressure-coupling strategy, or a different
governing equation) would violate. Record which linear solvers are valid
for which systems here once a second solver or system type exists.

**Expected behaviour:** converges reliably for the MVP's
well-conditioned, uniform-mesh pressure system.

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

**Configuration control:** proposed per-boundary-face selection (e.g.
`numerics.boundary_conditions: {north: dirichlet, south: neumann, ...}`)
rather than a single simulation-wide choice, since different edges of the
same domain typically need different condition types -- unlike the other
five ICDs, this one is not a single scalar choice.

**Compatibility requirements:** `periodic` requires the paired boundary
(e.g. east paired with west) to also be `periodic` -- a periodic
condition on only one side of a domain is not physically meaningful.

**Expected behaviour:** each condition type supplies the face value
(Dirichlet), face gradient (Neumann), or wrapped-neighbour reference
(periodic) the interior advection/diffusion schemes need at that face.

**Limitations:** limited to simple, axis-aligned domain edges -- internal
boundaries and arbitrary-geometry surfaces are explicitly future work,
not a current gap being worked around.

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
`src/pyflow/configuration/schema.py`'s existing pattern. The proposed
`numerics.*` configuration keys are **not yet implemented** -- update
this document, not just `schema.py`, the moment Stage 3
(TASK-018..022) actually adds them, since a stale "proposed" label left
in place after the real key exists is exactly the kind of drift
`docs/practices.md`'s Blast Radius rule exists to catch.
