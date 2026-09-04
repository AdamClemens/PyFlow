# Capability Map

Checked-by: stage-boundary

The Capability Map describes **what PyFlow is capable of**, independent of implementation.

Capabilities describe abilities rather than algorithms, data structures or software architecture.

The hierarchy is intentionally conceptual and is expected to evolve as our understanding of the problem domain improves.

---

# Top-Level Capabilities

## Phenomena

The physical phenomena that PyFlow is capable of simulating.

Initial areas of interest include:

- Fluid Flow
- Heat Transport
- Diffusion
- Density Transport
- Humidity Transport
- Buoyancy
- Convection
- Cloud Formation

---

## Physics

The physical models that describe the behaviour of simulated phenomena.

Examples include:

- Fluid Mechanics
- Thermodynamics
- Mass Transport
- Phase Change

These describe the governing equations and assumptions rather than their numerical implementation.

---

## Numerics

The numerical methods available for approximating the governing equations.

This document identifies candidate numerical approaches rather than selecting between them -- capabilities are described independently of the algorithms that provide them. The selection itself is a decision record, not a capability: `adr/ADR-002-fvm-first.md` chose the Finite Volume Method as PyFlow's initial framework on 2026-08-15, and `docs/handbook/numerical-methods/overview.md` is the survey it was chosen from.

Candidate areas include:

- Grid-based methods
- Particle-based methods
- Hybrid methods
- Time integration methods

---

## Rendering

Methods for visualising the state of the simulation.

Examples include:

- Scalar field visualisation
- Vector field visualisation
- Annotation and labelling
- Particle rendering
- Volume rendering
- Animation

---

## Analysis

Ways of understanding and validating simulation results.

Examples include:

- Measurements
- Diagnostics
- Validation
- Export
- Comparison
