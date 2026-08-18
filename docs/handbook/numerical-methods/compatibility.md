# Numerical Method Compatibility

Per `docs/planning/knowledge-architecture.md` KA-008.

Which numerical method families can be combined, and in what sense.
"Can be used together" means several different things. Mutually exclusive
alternatives, interchangeable implementations, methods coexisting at
different layers, coupled methods, hybrid approaches,
post-processing-only combinations, and combinations needing separate
engines are seven different relationships, and this document should not
collapse them into a single compatibility label (KA-008's own
instruction).

For the properties of each individual method, see `overview.md` (KA-007).

**Provenance:** split from the survey on 2026-08-15 when it moved from
`docs/planning/numerical-frameworks.md` into the handbook, and
substantially restructured 2026-08-18 -- the inherited combination
diagram and "very common / common / occasional / rare" frequency
groupings were removed rather than annotated, for the reason the next
section gives. See `docs/CHANGELOG-DESIGN.md`.

**Status:** complete against KA-008's Definition of Done. "Kinds of
Compatibility" is the spine of the document; "Pairwise Relationships"
below indexes into it, and "Incompatibilities" states where a pairing
does not work and why.

---

## Classification of the Method Families

The survey's eight method families (`overview.md`, which treats PIC and
FLIP as one entry) group by what they fundamentally represent, and most
of the relationships below follow from that grouping:

```text
Field-based
├── FDM
├── FVM
├── FEM
└── Spectral

Particle-based
├── SPH
├── PIC / FLIP
└── MPM

Distribution-based
└── LBM
```

## Pairwise Relationships

Every pairing is listed with **which kind of relationship it is**, not how
often it is met. That is a deliberate structural choice, and KA-008 is the
reason for it: its Content Requirements ask this document to distinguish
the seven relationships below and say explicitly that it "should not
collapse these into one compatibility label." A frequency band is exactly
one such label. Two pairings sharing a band can be a coupling and an
equivalence -- architecturally nothing alike -- and the band hides
precisely the distinction the document exists to draw.

Earlier versions of this file carried an inherited frequency grouping and
a combination diagram alongside the kinds. Both were removed on
2026-08-18: the groupings were unsourced and, in at least two places,
wrong. FVM/SPH shared the "very common" band with FVM/FEM, though
FVM/FEM coupling is routine industrial practice and FVM/SPH coupling a
far narrower research area. And "FEM ↔ Structural Mechanics" was not a
method pairing at all -- structural mechanics is an application domain,
not a numerical method. The diagram drew FDM
as the root of a hierarchy the "Classification" tree below contradicts.
Neither is required by KA-008, and neither could be corrected without
substituting one unsourced judgement for another -- whereas the *kind* of
each relationship follows from the methods' own structure, which
`overview.md` already documents.

| Pairing | Kind | What that means for a project |
| ------- | ---- | ----------------------------- |
| FDM / FVM / FEM / Spectral, any two of them | Mutually exclusive alternatives | Pick one as the primary discretisation of a continuum region. This is the choice `adr/ADR-002-fvm-first.md` actually made. |
| SPH / MPM, and the particle family generally | Mutually exclusive alternatives | The same relationship one family over -- competing primary solvers for a given problem, not components to combine. |
| FVM ↔ LBM | Interchangeable implementations | Either can be "the flow solver" for single-phase, low-Mach, roughly isothermal flow, with comparable macroscopic results. Regime-limited -- see "Incompatibilities". |
| FVM (fluid) ↔ FEM (structure) | Coupled methods | Fluid-structure interaction: two physical subdomains, each solved by the method suited to it, exchanging traction and displacement at their shared boundary. The best-established cross-family pairing in this table. |
| FVM (carrier phase) ↔ SPH or DEM (dispersed phase) | Coupled methods | Particle-laden, granular and free-surface flow. Note that DEM has no `overview.md` entry -- it is named here because the coupling is real, not because this handbook covers the method. |
| FVM bulk solve ↔ locally embedded SPH or PIC/FLIP | Coexisting at different layers | Multi-resolution: one method resolves the bulk, another a local feature the bulk mesh is too coarse to capture. Distinct from a coupling, where each method owns a full subdomain. |
| Spectral element methods (element decomposition + high-order bases) | Hybrid approaches | **One** method blending FEM's and spectral methods' mechanisms, not FEM coupled to a spectral solver. `overview.md` covers both under a single entry for this reason. |
| PIC / FLIP (particles + background grid) | Hybrid approaches | Likewise one integrated scheme. Neither the grid solve nor the particle representation exists as a standalone solver within it. |
| MPM (descended from PIC/FLIP, FEM-style background grid) | Hybrid approaches | Also one method. "MPM plus FEM" describes MPM's internals, not two solvers being combined. |
| Any Eulerian solver ↔ massless tracer particles | Post-processing only | Streamlines and path lines advected through an already-computed velocity field. Zero feedback, therefore zero coupling cost. |
| Mesh-based ↔ particle-based, each primary over a large subdomain | Needing separate engines | Data structures, timestep control and memory layout differ enough that production practice runs them as separate programs exchanging state at coarse synchronisation points. |
| FDM ↔ SPH; FDM ↔ PIC/FLIP; global Spectral ↔ SPH; LBM ↔ FEM | Incompatible | Structural mismatch rather than unusual choice -- see "Incompatibilities" for the specific reason in each case. |

Each kind is defined in its own subsection below, with the reasoning
behind the classification and a worked example.

---

## Kinds of Compatibility

"Can be used together" collapses at least seven distinct relationships.
The table above says which one each pairing is; this section defines each
kind and gives the reasoning. Two methods can appear together for
entirely different structural reasons, and the difference decides what an
architecture has to accommodate -- a coupling needs an interface between
two solvers, an equivalence needs neither, and a hybrid is not two
solvers at all.

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

The same relationship holds *within* the particle family, which is why
the table above groups SPH and MPM this way rather than as a combination:
they are competing primary solvers for overlapping problem classes, and a
project chooses between them for a given subdomain.

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

Two further entries in the table above are classified here for the same
reason, and both are commonly misread as combinations:

- **Spectral element methods** decompose the domain into elements, as FEM
  does, and apply high-order polynomial bases within each, as a spectral
  method does -- one algorithm, not FEM coupled to a spectral solver.
  `overview.md` covers the family under a single "Spectral / Spectral
  Element Methods" entry precisely because the two are not separable
  there. This also explains that entry's comparatively strong complex-
  geometry rating, which a purely global spectral method would not
  deserve (see "Incompatibilities").
- **MPM** descends from PIC/FLIP and carries the same structure: material
  points holding history-dependent state, with a background grid used for
  the governing solve each step in a manner closely related to FEM's.
  "MPM plus FEM" therefore describes MPM's internals rather than two
  solvers being combined.

The practical consequence is the same in all three cases: there is no
interface to design, because there are not two solvers to put one
between. A project adopts a hybrid whole or not at all.

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

- **FDM ↔ SPH, FDM ↔ PIC/FLIP: a genuine structural mismatch, not merely
  an unusual choice.** FDM assumes a fixed,
  structured grid with values defined at grid points and no inherent
  concept of a control-volume boundary; SPH and PIC/FLIP are built around
  particles with no grid at all (SPH) or a grid used only as an auxiliary
  solve step, not FDM's own pointwise-derivative formulation (PIC/FLIP).
  Neither pairing has a shared data structure or shared concept (like
  FVM's face flux, `fvm.md`) to exchange information through -- any
  coupling would need a wholly separate interpolation/mapping layer
  bridging the two representations. That missing shared concept, not any
  observed scarcity, is the reason to avoid the pairing.
- **Spectral ↔ SPH: opposing requirements, not just an unusual
  combination.** This is a statement about *global* spectral methods,
  which need smooth, typically simple or periodic domains to make their
  basis functions well-defined; SPH exists specifically to handle
  irregular, evolving, free-surface geometry that has no such smooth,
  fixed domain. Combining them offers little benefit in either direction:
  a global spectral method cannot naturally represent the moving boundary
  an SPH simulation produces, and SPH gains nothing from global basis
  functions since it has no grid to define them over.

  The distinction matters because `overview.md` covers "Spectral /
  Spectral Element Methods" as one entry, and *spectral element* methods
  are the reason it rates the family ★★★★☆ for complex geometry: they
  decompose the domain into elements and apply high-order bases within
  each, which is what makes complex geometry tractable and is closer in
  spirit to FEM than to a global spectral method. Read the incompatibility
  above as applying to the global variant; a spectral element method's
  relationship to the other families is essentially FEM's.
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

Restructured 2026-08-18. The inherited frequency groupings ("very common"
through "rare") and the combination diagram were **removed**, not
annotated, and replaced by the "Pairwise Relationships" table keyed to the
seven kinds. The deciding argument was KA-008's own Content Requirements,
which ask this document to distinguish the seven relationships and say it
"should not collapse these into one compatibility label" -- a frequency
band is one label, so the groupings were against the spec regardless of
whether any individual entry was accurate. Two were not: FVM/SPH shared a
band with FVM/FEM, and "FEM ↔ Structural Mechanics" paired a method with
an application domain. The diagram separately drew FDM as the root of a
hierarchy the classification tree contradicts.

`docs/planning/backlog.md` E5 recorded the opposite decision on
2026-08-17 ("the existing pairwise graph and frequency grouping were kept
as observed-practice-at-a-glance, not replaced") and was updated in the
same change as this one.

If a future contributor wants frequency information back, it needs a
citation, and it belongs beside the kind rather than instead of it. The
Spectral/SPH incompatibility was also scoped to *global* spectral methods
in the same pass, resolving an apparent contradiction with `overview.md`
rating the Spectral / Spectral Element family highly for complex
geometry -- spectral *element* methods are why it does, and their
relationship to the other families is essentially FEM's.
