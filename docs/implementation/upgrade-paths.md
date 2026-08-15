# PyFlow Upgrade Paths

Per `docs/planning/knowledge-architecture.md` KA-032. Extracted from
`docs/planning/implementation-plan.md` on 2026-08-15 into its own
artifact, and expanded to KA-032's full category list -- the version
previously embedded in `implementation-plan.md` covered only five of the
twelve categories below.

## Intent

Make the MVP (`docs/implementation/mvp.md`) intentionally simple without
letting that simplicity become an architectural dead end. Each major MVP
component has an identifiable path to more sophisticated alternatives,
without requiring the redesign of unrelated components -- see
`adr/ADR-003-modular-numerical-strategies.md`.

## Mesh

Structured 2D → structured 3D → unstructured → arbitrary geometry →
adaptive refinement.

## Variables

Collocated → alternative placement schemes (e.g. staggered) where
required.

## Flux

Simple flux formulation → more sophisticated formulations.

## Advection

Upwind → central difference → QUICK → TVD → WENO.

(Elaborates KA-032's "simple upwind → central/higher-order → TVD/other
bounded schemes": QUICK and WENO are specific instances of
higher-order and bounded schemes respectively.)

## Diffusion

Simple central formulation → improved geometric/non-orthogonal handling.

## Time Integration

Euler → RK2 → RK4 → adaptive RK → implicit.

(Elaborates KA-032's "RK4 → alternative explicit schemes → implicit
integration": Euler and RK2 are simpler explicit predecessors to RK4;
adaptive RK is a further alternative explicit scheme.)

## Pressure–Velocity Coupling

PISO → SIMPLE / SIMPLEC / other appropriate strategies, depending on
whether the simulation is transient or steady-state.

**Note:** the version of this upgrade path previously embedded in
`implementation-plan.md` read "Projection → SIMPLE → PISO," implying PISO
was the most advanced target -- but the MVP (`docs/implementation/mvp.md`)
already targets PISO from the start. That ordering was internally
inconsistent with the project's own MVP definition. This entry follows
KA-032 instead, which correctly starts from PISO (the MVP's actual choice)
and treats SIMPLE/SIMPLEC as alternatives suited to different regimes,
not strictly "more advanced."

## Linear Solvers

Conjugate Gradient → BiCGSTAB → GMRES → multigrid / preconditioned
methods.

## Boundary Conditions

Basic edge boundaries (Dirichlet, Neumann, periodic) → mixed conditions →
internal boundaries → arbitrary surfaces/geometries.

## Physics

Velocity/flow → heat → density/buoyancy → humidity/species → cloud
formation → additional fields.

## Numerical Framework

FVM → future FEM-compatible architecture (see
`adr/ADR-002-fvm-first.md`).

## Physics Scope

CFD → broader multiphysics, potentially including electromagnetic
phenomena, without requiring the initial implementation to support them.

## Definition of Done

- Each major MVP component has an identifiable upgrade path.
- Upgrading one component does not require redesigning unrelated
  components.
- Upgrade boundaries correspond to interfaces (see
  `adr/ADR-003-modular-numerical-strategies.md`).
- Complexity and motivation are recorded where useful.
