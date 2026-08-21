# Numerical Method Survey

Per `docs/planning/knowledge-architecture.md` KA-007.

This document surveys the principal numerical methods used in
Computational Fluid Dynamics. Its purpose is not to teach each method
exhaustively, but to provide sufficient understanding to evaluate each
method's suitability for PyFlow and to understand the trade-offs
involved. It describes the numerical-method territory, not PyFlow's
implementation of it.

For which methods can be combined, and in what sense, see
`compatibility.md` (KA-008). For the decision this survey supports, see
`adr/ADR-002-fvm-first.md`. For how the "Free surface" attribute rated
below is actually achieved -- FVM gains it through an added interface
field (VOF or level-set), not through a property of FVM itself -- see
`free-surface-methods.md`.

**Provenance:** this content was written before the handbook directory
existed and lived at `docs/planning/numerical-frameworks.md` until
2026-08-15, when it was moved here -- the KA-specified path -- and split
from its compatibility section. The per-method content and every rating
below are as originally written; the rating legend, the "Common
companions" convention and the coverage note below were added
2026-08-18. See `docs/CHANGELOG-DESIGN.md`.

**Status:** KA-007 `draft`, honestly so. Its Content Requirements list
sixteen properties per method family; this survey addresses eleven of
them, and unevenly across the eight families -- see "What This Survey
Does Not Yet Cover" below, which names the five it does not, before
relying on it for something it may not address.

---

## Reading the Ratings

Qualitative ratings use a five-star scale. **The polarity is not the same
for every attribute, and this is the single easiest thing to misread
here**, so it is stated explicitly rather than left to context:

For **capability** attributes -- scientific maturity, GPU suitability,
parallel scalability, atmospheric suitability, heat transport, scalar
transport, free surface, complex geometry -- more stars is better:

* ★★★★★ Excellent / industry-leading
* ★★★★☆ Very good
* ★★★☆☆ Good
* ★★☆☆☆ Limited
* ★☆☆☆☆ Poor

For **cost** attributes -- implementation complexity, compute
requirement, memory requirement -- more stars means *more of that cost*,
so **fewer stars is better**:

* ★★★★★ Very high cost
* ★★★★☆ High
* ★★★☆☆ Moderate
* ★★☆☆☆ Low
* ★☆☆☆☆ Very low

FDM's ★★☆☆☆ implementation complexity therefore means it is *easy* to
implement, not that it implements things badly; FEM's ★★★★★ on the same
row means the opposite. Reading the cost rows on the capability scale
inverts the survey's conclusions about exactly the trade-off
`adr/ADR-002-fvm-first.md` had to weigh, which is why this note exists.

A related wrinkle: the per-method **"Computational Characteristics"**
sections (present for FDM, FVM and FEM only) state CPU/GPU/Memory as
*performance*, where more stars is better, while the Summary tables state
the same underlying facts as *requirements*, where more stars is worse.
FDM's "CPU: ★★★★★" and its "Compute requirement: ★★☆☆☆" agree with each
other -- FDM is cheap -- despite looking opposed. The two conventions
were in the source material and are left as written rather than silently
harmonised; read the section heading before the stars.

---

# Finite Difference Method (FDM)

## Overview

The Finite Difference Method approximates derivatives by replacing them with differences between neighbouring grid points. It is one of the oldest and simplest numerical methods for solving partial differential equations.

FDM is conceptually straightforward, making it an excellent educational method and a popular choice in atmospheric science where structured grids are common.

> **On "Common companions" and "Compatibility" throughout this survey.**
> These fields name methods a given method is often *mentioned alongside*.
> They deliberately do **not** say what kind of relationship that is, and
> several of them are not couplings at all: FDM/FVM/Spectral are mutually
> exclusive as the primary discretisation of a region, spectral element
> methods are a hybrid rather than FEM coupled to a spectral solver, and
> MPM's FEM-like background grid is internal to MPM rather than a second
> solver alongside it. `compatibility.md` (KA-008) classifies every
> pairing by kind and is authoritative where the two documents differ;
> treat these fields as a pointer into it, not as a compatibility claim
> in their own right.

## Representation

* Structured Cartesian grid
* Variables stored at grid locations

## Governing Equations

Suitable for:

* Navier–Stokes
* Heat equation
* Advection–diffusion
* Poisson equation
* Wave equation

## Typical Applications

* Weather models
* Ocean models
* Heat conduction
* Academic CFD
* Numerical research

## Strengths

* Simple implementation
* Fast on structured grids
* Excellent cache locality
* High-order schemes available
* GPU-friendly

## Weaknesses

* Poor handling of complex geometry
* Difficult adaptive refinement
* Conservative formulations require care

## Compatibility

Commonly coupled with:

* Finite Volume
* Spectral methods
* Immersed boundary methods

Rarely coupled with particle methods.

## Computational Characteristics

CPU: ★★★★★

GPU: ★★★★★

Memory: ★★★★★

Parallel scaling: ★★★★☆

Implementation complexity: ★★☆☆☆

## Suitability for PyFlow

Excellent for early prototypes and educational implementations.

Less attractive as the long-term foundation if arbitrary geometry becomes important.

### Summary

| Attribute                 | Rating                                |
| ------------------------- | ------------------------------------- |
| Scientific maturity       | ★★★★★                                 |
| Implementation complexity | ★★☆☆☆                                 |
| Compute requirement       | ★★☆☆☆                                 |
| Memory requirement        | ★★☆☆☆                                 |
| GPU suitability           | ★★★★★                                 |
| Parallel scalability      | ★★★★☆                                 |
| Atmospheric suitability   | ★★★★★                                 |
| Heat transport            | ★★★★★                                 |
| Scalar transport          | ★★★★★                                 |
| Free surface              | ★★☆☆☆                                 |
| Complex geometry          | ★☆☆☆☆                                 |
| Typical role              | Excellent prototype / possible engine |
| Common companions         | FVM, Spectral                         |

---

# Finite Volume Method (FVM)

## Overview

Finite Volume divides the domain into control volumes and enforces conservation across each volume. It is the dominant approach in industrial CFD because conservation laws are naturally preserved.

## Representation

* Structured or unstructured control-volume mesh

## Governing Equations

Ideal for conservation laws:

* Navier–Stokes
* Energy
* Species transport
* Turbulence
* Combustion
* Multiphase transport

## Typical Applications

* Engineering CFD
* Aerospace
* Automotive
* Heat exchangers
* Weather and environmental transport
* Combustion

## Strengths

* Excellent conservation
* Handles arbitrary meshes
* Mature ecosystem
* Strong multiphysics support
* Natural treatment of transported fields

## Weaknesses

* More implementation complexity
* Mesh generation required
* Higher bookkeeping cost

## Compatibility

Commonly coupled with:

* FEM
* SPH
* LBM
* Radiation solvers

Widely used in multiphysics codes.

## Computational Characteristics

CPU: ★★★★☆

GPU: ★★★★☆

Memory: ★★★☆☆

Parallel scaling: ★★★★★

Implementation complexity: ★★★★☆

## Suitability for PyFlow

Currently appears to be the strongest candidate for the primary PyFlow framework due to its field-based formulation and support for transport equations.

### Summary

| Attribute                 | Rating                   |
| ------------------------- | ------------------------ |
| Scientific maturity       | ★★★★★                    |
| Implementation complexity | ★★★★☆                    |
| Compute requirement       | ★★★☆☆                    |
| Memory requirement        | ★★★☆☆                    |
| GPU suitability           | ★★★★☆                    |
| Parallel scalability      | ★★★★★                    |
| Atmospheric suitability   | ★★★★★                    |
| Heat transport            | ★★★★★                    |
| Scalar transport          | ★★★★★                    |
| Free surface              | ★★★☆☆                    |
| Complex geometry          | ★★★★★                    |
| Typical role              | Strong primary candidate |
| Common companions         | FEM, SPH, LBM            |

---

# Finite Element Method (FEM)

## Overview

FEM represents the solution using basis functions over mesh elements. It is the dominant numerical framework for structural mechanics and many multiphysics problems.

## Representation

* Unstructured mesh
* Basis functions over elements

## Governing Equations

General PDE framework including:

* Navier–Stokes
* Elasticity
* Heat transfer
* Electromagnetics

## Typical Applications

* Fluid-structure interaction
* Structural mechanics
* Biomedical simulation
* Multiphysics

## Strengths

* Arbitrary geometry
* Excellent mathematical foundation
* Adaptive refinement
* Strong multiphysics capability

## Weaknesses

* Higher mathematical complexity
* More difficult implementation
* Conservative transport often less natural than FVM

## Compatibility

Frequently coupled with:

* FVM
* Spectral methods
* Particle methods

## Computational Characteristics

CPU: ★★★☆☆

GPU: ★★★☆☆

Memory: ★★★☆☆

Parallel scaling: ★★★★☆

Implementation complexity: ★★★★★

### Summary

| Attribute                 | Rating                  |
| ------------------------- | ----------------------- |
| Scientific maturity       | ★★★★★                   |
| Implementation complexity | ★★★★★                   |
| Compute requirement       | ★★★★☆                   |
| Memory requirement        | ★★★☆☆                   |
| GPU suitability           | ★★★☆☆                   |
| Parallel scalability      | ★★★★☆                   |
| Atmospheric suitability   | ★★★☆☆                   |
| Heat transport            | ★★★★★                   |
| Scalar transport          | ★★★★☆                   |
| Free surface              | ★★☆☆☆                   |
| Complex geometry          | ★★★★★                   |
| Typical role              | Complementary framework |
| Common companions         | FVM                     |

---

# Spectral / Spectral Element Methods

## Overview

These methods approximate the solution using global or high-order basis functions, delivering exceptionally high accuracy for smooth solutions.

This entry covers two related but meaningfully different things, and the
ratings below are not the same for both. *Global* spectral methods use
basis functions spanning the whole domain, which is what delivers their
accuracy and what restricts them to smooth, simple, typically periodic
geometry. *Spectral element* methods decompose the domain into elements
first, as FEM does, and apply high-order bases within each -- which is
why the ★★★★☆ complex-geometry rating below is defensible at all, since a
purely global method would rate near the bottom of that row.
`compatibility.md`'s Spectral/SPH incompatibility is a statement about
the global variant specifically, for the same reason.

## Typical Applications

* Direct Numerical Simulation (DNS)
* Turbulence research
* High-performance computing

## Strengths

* Extremely high accuracy
* Low numerical diffusion

## Weaknesses

* Complex implementation
* Difficult local refinement
* Computationally intensive

### Summary

| Attribute                 | Rating         |
| ------------------------- | -------------- |
| Scientific maturity       | ★★★★☆          |
| Implementation complexity | ★★★★★          |
| Compute requirement       | ★★★★★          |
| Memory requirement        | ★★★★☆          |
| GPU suitability           | ★★★★☆          |
| Parallel scalability      | ★★★★★          |
| Atmospheric suitability   | ★★★★☆          |
| Heat transport            | ★★★★★          |
| Scalar transport          | ★★★★★          |
| Free surface              | ★☆☆☆☆          |
| Complex geometry          | ★★★★☆          |
| Typical role              | Specialist HPC |
| Common companions         | FEM            |

---

# Lattice Boltzmann Method (LBM)

## Overview

LBM models the evolution of particle distribution functions on a lattice rather than solving the Navier–Stokes equations directly.

## Typical Applications

* Porous media
* Microfluidics
* Low-Mach flows
* Complex boundaries

## Strengths

* Extremely parallel
* Elegant implementation
* Excellent GPU performance

## Weaknesses

* Less suitable for high-Mach compressible flow
* Different conceptual framework from classical CFD

### Summary

| Attribute                 | Rating            |
| ------------------------- | ----------------- |
| Scientific maturity       | ★★★★☆             |
| Implementation complexity | ★★★☆☆             |
| Compute requirement       | ★★★☆☆             |
| Memory requirement        | ★★★★☆             |
| GPU suitability           | ★★★★★             |
| Parallel scalability      | ★★★★★             |
| Atmospheric suitability   | ★★☆☆☆             |
| Heat transport            | ★★★☆☆             |
| Scalar transport          | ★★☆☆☆             |
| Free surface              | ★★★☆☆             |
| Complex geometry          | ★★★★☆             |
| Typical role              | Specialist solver |
| Common companions         | FVM               |

---

# Smoothed Particle Hydrodynamics (SPH)

## Overview

SPH is a mesh-free Lagrangian method in which fluids are represented by particles carrying physical properties.

## Typical Applications

* Breaking waves
* Flood simulation
* Astrophysics
* Splashing liquids

## Strengths

* Naturally handles free surfaces
* Large deformation
* Moving boundaries

## Weaknesses

* Boundary treatment
* Tensile instability
* High particle counts
* Diffusion of some quantities requires care

### Summary

| Attribute                 | Rating               |
| ------------------------- | -------------------- |
| Scientific maturity       | ★★★★☆                |
| Implementation complexity | ★★★★☆                |
| Compute requirement       | ★★★★☆                |
| Memory requirement        | ★★★★☆                |
| GPU suitability           | ★★★★★                |
| Parallel scalability      | ★★★★★                |
| Atmospheric suitability   | ★☆☆☆☆                |
| Heat transport            | ★★☆☆☆                |
| Scalar transport          | ★★☆☆☆                |
| Free surface              | ★★★★★                |
| Complex geometry          | ★★★★★                |
| Typical role              | Specialist extension |
| Common companions         | FVM, DEM             |

---

# Particle-In-Cell (PIC) / FLIP

## Overview

PIC and FLIP combine particles with a background grid. The grid solves the governing equations while particles transport material information.

## Typical Applications

* Computer graphics
* Splashing liquids
* Visual effects

## Strengths

* Stable free-surface simulation
* Reduced numerical diffusion (FLIP)
* Excellent animation quality

## Weaknesses

* Complex implementation
* Less common in engineering CFD

### Summary

| Attribute                 | Rating                          |
| ------------------------- | ------------------------------- |
| Scientific maturity       | ★★★☆☆                           |
| Implementation complexity | ★★★★★                           |
| Compute requirement       | ★★★★☆                           |
| Memory requirement        | ★★★★☆                           |
| GPU suitability           | ★★★★★                           |
| Parallel scalability      | ★★★★☆                           |
| Atmospheric suitability   | ★☆☆☆☆                           |
| Heat transport            | ★★☆☆☆                           |
| Scalar transport          | ★★☆☆☆                           |
| Free surface              | ★★★★★                           |
| Complex geometry          | ★★★★☆                           |
| Typical role              | Future visual-effects extension |
| Common companions         | Grid solvers                    |

---

# Material Point Method (MPM)

## Overview

MPM combines particles with a background computational grid and excels at problems involving very large deformations.

## Typical Applications

* Snow
* Sand
* Soil
* Soft materials
* Fluid-solid interaction

## Strengths

* Handles topology changes
* Excellent for deformable materials
* Naturally unifies solids and fluids

## Weaknesses

* High implementation complexity
* Specialist domain

### Summary

| Attribute                 | Rating                       |
| ------------------------- | ---------------------------- |
| Scientific maturity       | ★★★☆☆                        |
| Implementation complexity | ★★★★★                        |
| Compute requirement       | ★★★★☆                        |
| Memory requirement        | ★★★★☆                        |
| GPU suitability           | ★★★★☆                        |
| Parallel scalability      | ★★★★☆                        |
| Atmospheric suitability   | ★☆☆☆☆                        |
| Heat transport            | ★★☆☆☆                        |
| Scalar transport          | ★★☆☆☆                        |
| Free surface              | ★★★★☆                        |
| Complex geometry          | ★★★★★                        |
| Typical role              | Specialist future capability |
| Common companions         | FEM, SPH                     |

---

# What This Survey Does Not Yet Cover

KA-007's Content Requirements name sixteen properties per method family.
This survey addresses eleven: what equations each method addresses,
physical domains, field representation, strengths, weaknesses,
computational requirements, memory requirements, geometric flexibility,
multiphysics suitability, compatibility with other methods, and --
by way of `compatibility.md` -- whether methods are alternatives,
composable, nested or hybridisable.

**Five are not covered**, recorded here so a reader knows what the
survey's silence means and so KA-007's `draft` status has a concrete
meaning rather than a vague one:

- **Accuracy characteristics**, and separately **stability
  characteristics**, per method family. The per-method entries in this
  directory cover both for the schemes PyFlow actually uses
  (`advection.md`, `diffusion.md`, `time-integration.md`), but not
  comparatively across families.
- **Suitability for transient problems**, as an axis distinct from the
  ratings above -- currently implicit in "Typical applications" at best.
- **Suitability for different scales.** No entry addresses what happens
  across orders of magnitude in domain size or resolution.
- **Practical examples of established projects using them.** Named
  elsewhere for FVM only (`fvm.md` and `adr/ADR-002-fvm-first.md` cite
  OpenFOAM, ANSYS Fluent and SU2); absent for the other seven families.

A further issue is not a missing requirement but an unevenness in how the
eleven covered ones are delivered:

- **Structural consistency between entries.** FDM, FVM and FEM have
  "Representation", "Governing Equations", "Compatibility" and
  "Computational Characteristics" sections; Spectral, LBM, SPH, PIC/FLIP
  and MPM have some or none of these. Only FDM and FVM carry a
  "Suitability for PyFlow" verdict -- the field `adr/ADR-002` cites
  directly.

None of this blocks the decision the survey was written to support:
`adr/ADR-002-fvm-first.md` was reviewed line by line against this
document on 2026-08-17 and no claim in it depends on a gap above. The
gaps matter if a *future* decision needs to compare families on an axis
this survey does not rate -- at which point fill the gap rather than
inferring an answer from the ratings that are here.

## Maintenance

Reviewed 2026-08-18 as part of the Handbook scientific-accuracy pass. No
rating was changed and no per-method content was rewritten: the ratings
are unsourced qualitative judgements inherited from the pre-handbook
survey, and revising them would substitute one judgement for another --
the same reasoning that governed `compatibility.md`'s frequency
groupings, except that KA-007 genuinely *requires* computational and
memory ratings, so these stay and are made legible instead of removed.

What changed is everything around them: the rating legend now states that
cost attributes invert the scale (previously a single "Excellent → Poor"
legend covered rows where five stars means "very expensive"); the
"Common companions" fields are marked as pointers into `compatibility.md`
rather than compatibility claims, since several of them name
relationships that are not couplings; the Spectral entry distinguishes
global from spectral element methods, which its own complex-geometry
rating depends on; and KA-007's uncovered Content Requirements are listed
explicitly so the `draft` status means something specific.

If a rating is ever changed, check `adr/ADR-002-fvm-first.md` in the same
change -- it cites this survey's FVM ratings and "Suitability for PyFlow"
verdict directly as part of its rationale.

**2026-08-21:** added a pointer to the new `free-surface-methods.md`
entry, which closes the gap `docs/planning/backlog.md` recorded the same
day -- this survey rates every family's "Free surface" suitability but
never explained how any of them actually achieve it. No rating changed.
