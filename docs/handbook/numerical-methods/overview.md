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
`adr/ADR-002-fvm-first.md`.

**Provenance:** this content was written before the handbook directory
existed and lived at `docs/planning/numerical-frameworks.md` until
2026-08-15, when it was moved here -- the KA-specified path -- and split
from its compatibility section. Content is unchanged apart from this
header and the split. See `docs/CHANGELOG-DESIGN.md`.

Qualitative ratings use the following scale:

* ★★★★★ Excellent / industry-leading
* ★★★★☆ Very good
* ★★★☆☆ Good
* ★★☆☆☆ Limited
* ★☆☆☆☆ Poor

---

# Finite Difference Method (FDM)

## Overview

The Finite Difference Method approximates derivatives by replacing them with differences between neighbouring grid points. It is one of the oldest and simplest numerical methods for solving partial differential equations.

FDM is conceptually straightforward, making it an excellent educational method and a popular choice in atmospheric science where structured grids are common.

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
