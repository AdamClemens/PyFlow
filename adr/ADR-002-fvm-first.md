# ADR-002: Use the Finite Volume Method as the Initial Numerical Framework

**Status:** Accepted, partially implemented

# Implementation Status

**Added 2026-08-22, by a repository consistency sweep.** `adr/README.md`
requires this section of any accepted-but-unimplemented ADR ("Accepted
says the decision was made, not that it was carried out", added
2026-08-21). The rule was written for ADR-001's problem and applied
there; ADR-002 and ADR-003 needed it too and did not get it.

**What exists:** nothing of the finite volume method itself. The
decision has shaped what was built -- `Mesh` (Stage 1, TASK-011/012)
exposes cell volumes, face areas, outward normals and neighbour
connectivity because FVM integrates over control volumes and sums fluxes
over their faces, and its geometric-closure test
(`sum(face_area * outward_normal) == 0` per cell) is a precondition
FVM's conservation properties depend on. `Field` and its collocated
implementations (Stage 2, TASK-014..016) store one value per control
volume for the same reason.

**Updated 2026-08-27, TASK-023 (First-order Upwind Advection, Stage 4):
the first genuinely FVM-specific computation now exists.**
`src/pyflow/engine/numerics/advection.py`'s `FirstOrderUpwindAdvection`
computes a real per-face flux (the upstream cell's own value, times the
face-normal velocity); `src/pyflow/engine/simulation.py`'s
`accumulate_flux_to_cells` (TASK-040) is the discrete Gauss-theorem
face-to-cell reduction FVM's own conservation property depends on. The
conservation criterion this section used to anticipate is now checked
directly: `tests/features/first_order_upwind_advection.feature`'s own
"Conservation on a closed domain" scenario constructs a domain with zero
velocity at every boundary cell and confirms the transported quantity's
total is unchanged after many timesteps, to floating-point tolerance.

**What still does not exist:** a real Diffusion, Time Integration,
Pressure-Velocity Coupling, or Linear Solver implementation -- `docs/
architecture/engine.md`'s own entries for those four layers still name
`assembly.py`'s trivial, non-physical reference implementation, not a
real scheme. Stage 4 (`docs/planning/roadmap.md`, TASK-024..030) brings
each in turn; `first_order_upwind` is the first of the six `adr/ADR-003`
components to go real, not the last.

---

# Context

PyFlow needs an initial spatial discretisation framework for its CFD
engine. Several established approaches exist: the Finite Difference
Method (FDM), the Finite Element Method (FEM), the Finite Volume Method
(FVM), spectral methods, and particle/mesoscopic methods such as the
Lattice Boltzmann Method (LBM) and Smoothed Particle Hydrodynamics (SPH).

The MVP (`docs/implementation/mvp.md`) targets a 2D incompressible flow on
a structured Cartesian mesh, but the engine architecture should not
preclude the project's longer-range goals: complex geometry, unstructured
meshes, and additional transported physical fields (heat, density,
humidity, cloud formation).

The survey of these method families, their properties and their
trade-offs is `docs/handbook/numerical-methods/overview.md`; their
combination relationships are in
`docs/handbook/numerical-methods/compatibility.md`.

The project also wants to avoid re-deriving solved problems where
possible -- the initial framework should have well-documented, established
practice behind it.

**Reviewed against the survey it cites, 2026-08-17
(`docs/planning/backlog.md` E12).** This ADR's rationale was originally
drafted from general CFD domain knowledge, before `overview.md` existed
to supply project-specific reasoning. Checked line by line against it:
no factual claim here contradicts the survey (FVM's strengths/weaknesses,
and every alternative's rejection/deferral reasoning, match what
`overview.md` records for each method). The one real gap -- the survey's
own per-method "Suitability for PyFlow" verdicts and field-transport
ratings were available but not cited -- is closed below.

---

# Decision

PyFlow will use the Finite Volume Method (FVM) as its initial numerical
framework, as already reflected in `docs/implementation/mvp.md`.

---

# Consequences

## Positive

- Conservation of mass, momentum, and other transported quantities is
  guaranteed by construction, since FVM directly discretises the integral
  (conservation) form of the governing equations over control volumes --
  a property especially valuable for long-running, physically-meaningful
  simulations.
- Directly matches PyFlow's field-centric vision (`prompts/global/
  project.md`: "the engine transports arbitrary fields"), not just
  generic CFD suitability -- `docs/handbook/numerical-methods/
  overview.md` rates FVM ★★★★★ for both Heat transport and Scalar
  transport (the two ratings besides Atmospheric suitability where FVM
  scores the maximum), and its own "Suitability for PyFlow" verdict is
  that FVM "appears to be the strongest candidate for the primary PyFlow
  framework due to its field-based formulation and support for transport
  equations" -- the survey's project-specific assessment, not only its
  generic description of the method.
- Natural extensibility toward unstructured and complex-geometry meshes,
  giving a smooth path along the project's own "Mesh" upgrade path
  (structured → adaptive → unstructured).
- Boundary conditions are expressed as flux specifications at cell faces,
  which composes cleanly with the modular, replaceable-component
  architecture recorded in ADR-003.
- FVM is the dominant method in mature production and open-source CFD
  software (e.g. OpenFOAM, ANSYS Fluent, SU2), meaning established
  practice, well-documented pitfalls, and abundant reference material
  exist.

## Negative

- Achieving higher-order accuracy on complex or skewed meshes requires
  more careful gradient reconstruction than simpler finite-difference
  stencils.
- Some very high-order schemes (e.g. high-order WENO) are more naturally
  expressed in finite-difference or finite-element-adjacent formulations.
  If very high accuracy on smooth domains ever becomes a priority, the
  project may need to support an additional framework alongside FVM
  rather than solely extending it -- already anticipated as a possible
  future capability level ("Additional Numerical Frameworks") rather than
  treated as a gap in this decision.

---

# Alternatives Considered

## Finite Difference Method (FDM)

Rejected as the primary framework.

Conceptually the simplest approach -- direct discretisation of the
governing PDEs on a grid -- but does not enforce conservation directly,
and generalises poorly to unstructured or complex geometries, which the
project needs a credible path toward.

## Finite Element Method (FEM)

Deferred, not rejected.

FEM offers strong flexibility for complex geometry and higher-order
accuracy, with a solid mathematical foundation, but its weak-formulation
and basis-function machinery adds implementation complexity that isn't
justified for the MVP. FVM was chosen partly *because* it does not
preclude a future FEM-compatible architecture -- see the "Numerical
Framework" upgrade path (FVM → future FEM-compatible architecture).

## Spectral methods

Rejected as the primary framework.

Excellent accuracy for smooth problems on simple domains, but poor
flexibility for the complex, evolving geometries and boundary conditions
the project intends to eventually support.

## Lattice Boltzmann Method (LBM)

Rejected as the primary framework.

Effective for certain flow regimes and complex boundaries via simple
local update rules, but LBM is a mesoscopic/kinetic method operating on
particle distribution functions rather than directly on macroscopic
fields (pressure, velocity, temperature). This doesn't map cleanly onto
PyFlow's field-centric architecture, where the engine transports
arbitrary physical fields directly. Left open as a possible future
alternative numerical framework, not part of the core engine.

## Smoothed Particle Hydrodynamics (SPH)

Rejected as the primary framework.

Meshless and well-suited to free-surface and multiphase flows, but its
conservation and accuracy properties differ substantially from mesh-based
methods, and it doesn't fit the structured, incompressible-flow MVP as
currently scoped. Left open as a possible future alternative framework,
alongside LBM.

---

# Notes

This ADR records the decision and its rationale, not FVM's mechanics.
The conceptual, implementation-independent explanation of FVM is
`docs/handbook/numerical-methods/fvm.md` (KA-016), written 2026-08-17.
Read that for what FVM *is*; read this for why PyFlow chose it.

Standard reference: Versteeg, H.K. and Malalasekera, W., *An Introduction
to Computational Fluid Dynamics: The Finite Volume Method* -- a widely
used introductory text covering the tradeoffs summarised above in more
depth.
