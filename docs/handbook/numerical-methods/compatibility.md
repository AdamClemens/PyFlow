# Numerical Method Compatibility

Per `docs/planning/knowledge-architecture.md` KA-008.

Which numerical method families can be combined, and in what sense.
"Can be used together" means several different things -- interchangeable
implementations, methods coexisting at different layers, coupled methods,
hybrid approaches, and post-processing-only combinations are not the same
relationship, and this document should not collapse them into a single
compatibility label.

For the properties of each individual method, see `overview.md` (KA-007).

**Provenance:** split from the survey on 2026-08-15 when it moved from
`docs/planning/numerical-frameworks.md` into the handbook. Content is
unchanged apart from this header and the repair of an unbalanced code
fence around the classification tree below. See
`docs/CHANGELOG-DESIGN.md`.

**Status:** complete against KA-008's Definition of Done as of
2026-08-17 (`docs/planning/backlog.md` E5) -- the pairwise graph and
frequency grouping below record observed practice at a glance; "Kinds of
Compatibility" and "Incompatibilities" below satisfy the two
requirements that were previously outstanding.

---

The following graph summarises common combinations found in practice.

```text
                    CFD Numerical Methods

                              ┌──────────────┐
                              │     FDM      │
                              └──────┬───────┘
                                     │
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
         ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
         │     FVM     │──────│     FEM     │──────│  Spectral   │
         └───┬────┬────┘      └─────────────┘      └─────────────┘
             │    │
             │    │
      ┌──────▼┐  ┌▼─────────┐
      │  LBM  │  │   SPH    │
      └───────┘  └────┬─────┘
                      │
              ┌───────▼────────┐
              │ PIC / FLIP     │
              └───────┬────────┘
                      │
                ┌─────▼─────┐
                │    MPM    │
                └───────────┘
```

### Interpretation

**Very common**

- FVM ↔ FEM
- FVM ↔ SPH
- SPH ↔ DEM (future handbook entry)
- FEM ↔ Structural Mechanics

**Common**

- FDM ↔ FVM
- FVM ↔ LBM
- FEM ↔ Spectral

**Occasional**

- SPH ↔ PIC/FLIP
- MPM ↔ FEM
- MPM ↔ SPH

**Rare**

- FDM ↔ SPH
- FDM ↔ PIC
- Spectral ↔ SPH

### Classification

```text
Field-based
├── FDM
├── FVM
├── FEM
└── Spectral

Particle-based
├── SPH
├── PIC
├── FLIP
└── MPM

Distribution-based
└── LBM
```

---

## Kinds of Compatibility

"Can be used together" collapses at least seven distinct relationships.
The pairwise graph and frequency grouping above say *how often* two
methods appear together in practice; this section says *what kind of
relationship* that appearance actually is -- two methods can be "common"
for entirely different reasons; this document should not report a
frequency without also reporting a kind.

### Mutually exclusive alternatives

Methods solving the *same* governing equations over the *same* continuum
domain, at the same layer -- a project picks exactly one, not several.
**FDM, FVM, FEM, and Spectral methods are mutually exclusive as the
primary spatial discretisation of a single continuum region.** This is
the relationship `adr/ADR-002-fvm-first.md` actually decided between: it
did not combine FVM with FDM or FEM as PyFlow's core discretisation, it
chose FVM *instead of* them for that role. (This does not preclude a
*different* method later being used at a genuinely different layer or
subdomain -- see "Coexisting at different layers" and "Coupled methods"
below; it precludes two of them discretising the same equations over the
same region simultaneously.)

### Interchangeable implementations

Methods with entirely different underlying mechanisms that, within a
specific regime, produce equivalent macroscopic results -- genuinely
swappable for the same intent, not merely combinable. **FVM and LBM are
interchangeable for single-phase, low-Mach, roughly isothermal flow**:
LBM's kinetic formulation (evolving particle distribution functions,
`overview.md`'s LBM entry) recovers the same macroscopic Navier–Stokes
behaviour FVM solves for directly, in that regime -- a project could
choose either as "the flow solver" and expect comparable macroscopic
output. This equivalence is regime-limited, not general -- see
"Incompatibilities" below for where it breaks down.

### Methods coexisting at different layers

One method resolves the bulk/coarse solution while a second, different
method is embedded locally for a specific sub-feature needing finer
resolution or a different representation -- a *multi-resolution*
relationship, not a domain split (contrast with "Coupled methods"
below, where each method owns a full, separate physical subdomain). A
representative pattern from the broader field: an FVM bulk solve with a
locally embedded particle method (SPH or PIC/FLIP) resolving a specific
free-surface or splash feature the bulk mesh is too coarse to capture
directly. PyFlow does not do this today -- noted here as a real kind of
compatibility this territory contains, not as an implemented or planned
PyFlow capability.

### Coupled methods

Two methods, each owning a distinct physical subdomain or phase,
exchanging boundary data (forces, velocities, temperatures) across a
shared interface every timestep or sub-cycle -- both solves proceed
largely independently between exchanges. **FVM (fluid) coupled with FEM
(structure) is the standard Fluid-Structure Interaction (FSI)
pattern**: the fluid domain and the structural domain are physically
distinct regions, each solved by the method suited to it, exchanging
traction and displacement at their shared boundary. **FVM (continuous
carrier phase) coupled with SPH or a discrete-element method (dispersed
phase)** is the analogous pattern for particle-laden or multiphase flow.

### Hybrid approaches

Not two separate coupled solvers, but a *single* method that internally
blends mechanisms from two families into one unified algorithm. **PIC
and FLIP are themselves hybrids, not combinations of two separate
methods** (`overview.md`'s PIC/FLIP entry already describes this: "PIC
and FLIP combine particles with a background grid" as one integrated
scheme, not a coupling between an independent grid solver and an
independent particle solver) -- the grid solves the governing equations
each step, particles carry material information between steps, and
neither exists as a standalone solver in this scheme. This is a
structurally different relationship from "Coupled methods" above, even
though both involve two representations working together.

### Post-processing-only combinations

One method's output feeds a second, entirely one-directional process,
with zero feedback into the governing solve -- the second "method" is
not really solving anything, only consuming a result. The standard
example: advecting massless tracer particles through an already-computed
FVM (or any Eulerian method's) velocity field, purely for visualisation
or diagnostic purposes (streamlines, path lines). This costs nothing in
solver-coupling complexity, precisely because there is no coupling --
information flows one way, computed after the fact.

### Combinations needing separate engines

Two methods whose underlying data structures, timestep control, and
memory layout differ so fundamentally that hosting both as first-class
citizens of one shared internal architecture is impractical -- production
practice typically runs each as a genuinely separate program, exchanging
state only at coarse synchronisation points (co-simulation), rather than
sharing internal representations the way an FVM+FEM FSI code often does.
This is the general-field pattern for pairing a mesh-based method
(FDM/FVM/FEM/Spectral) with a mesh-free particle method (SPH, MPM) used
as the *primary* solver for a large sub-domain, not merely a locally
embedded feature (contrast with "Coexisting at different layers," where
the embedded method is small and local enough to still fit inside one
shared architecture). Recorded here as a real category this territory
contains; PyFlow has not evaluated a concrete instance of it.

---

## Incompatibilities

Not every pairing in the survey combines usefully, and this document
should say so rather than implying anything can be made to work with
enough effort.

- **FDM ↔ SPH, FDM ↔ PIC/FLIP (both "rare" above): a genuine structural
  mismatch, not merely an unusual choice.** FDM assumes a fixed,
  structured grid with values defined at grid points and no inherent
  concept of a control-volume boundary; SPH and PIC/FLIP are built around
  particles with no grid at all (SPH) or a grid used only as an auxiliary
  solve step, not FDM's own pointwise-derivative formulation (PIC/FLIP).
  Neither pairing has a shared data structure or shared concept (like
  FVM's face flux, `fvm.md`) to exchange information through -- any
  coupling would need a wholly separate interpolation/mapping layer
  bridging the two representations, which is why these pairings are rare
  in practice rather than simply less common.
- **Spectral ↔ SPH: opposing requirements, not just an unusual
  combination.** Spectral methods need smooth, typically simple/periodic
  domains to make their global basis functions well-defined
  (`overview.md`'s Spectral entry); SPH exists specifically to handle
  irregular, evolving, free-surface geometry that has no such smooth,
  fixed domain. Combining them offers little benefit in either direction:
  a spectral method cannot naturally represent the moving boundary an SPH
  simulation produces, and SPH gains nothing from global basis functions
  since it has no grid to define them over.
- **LBM ↔ FEM: no shared mathematical machinery.** FVM and FEM can share
  information relatively directly because both ultimately produce
  face/nodal values on a mesh (`fvm.md`'s "Compatibility with an FEM
  Extension"); LBM's kinetic, distribution-function formulation has no
  direct analogue to FEM's nodal basis functions or weak form. As with
  the FDM/particle-method pairings above, combining them would require an
  intermediate macroscopic-field mapping layer rather than any direct
  exchange.
- **The FVM ↔ LBM equivalence above is regime-limited, not general.**
  Outside single-phase, low-Mach, roughly isothermal flow -- high-Mach
  compressible flow in particular -- LBM's kinetic formulation and FVM's
  direct macroscopic discretisation diverge, and the "interchangeable"
  relationship above should not be assumed to hold; `overview.md`'s LBM
  entry already flags "less suitable for high-Mach compressible flow" as
  a weakness for exactly this reason.

## Maintenance

"Kinds of Compatibility" and "Incompatibilities" written 2026-08-17
(`docs/planning/backlog.md` E5), closing KA-008's previously-outstanding
Definition of Done items. Grounded in `overview.md`'s existing per-method
entries and `fvm.md`'s FVM/FEM compatibility note rather than introduced
independently -- update both together if a new method entry changes what
either section claims about it.
