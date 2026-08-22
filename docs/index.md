# Documentation Index

<!-- GENERATED FILE -- do not edit by hand.
     Regenerate with `make docs` (tools/generators/generate_docs_index.py).
     `make check-docs-index` fails CI if this file is stale. -->

Every documentation page in the repository, grouped by directory. Link text is each page's own heading.

For a curated first-read order instead of the full map, see [README.md](../README.md)'s "Where to Start" section. For completion status per file, see [repository-manifest.md](repository-manifest.md).

## Meta

- [Changelog Design](CHANGELOG-DESIGN.md)
- [Documentation Guidelines](documentation-guidelines.md)
- [Engineering Principles](engineering-principles.md)
- [Glossary](glossary.md)
- [Engineering Practices](practices.md)
- [Repository Inventory](repository-inventory.md)
- [Repository Manifest](repository-manifest.md)

## Planning

- [Backlog](planning/backlog.md)
- [Capability Map](planning/capability-map.md)
- [Dependency Tree](planning/dependency-tree.md)
- [Dreams](planning/dreams.md)
- [PyFlow Implementation Plan](planning/implementation-plan.md)
- [PyFlow Knowledge Architecture](planning/knowledge-architecture.md)
- [Releases](planning/releases.md)
- [PyFlow Execution Roadmap](planning/roadmap.md)

## Architecture

- [Compute-and-Rendering Stack](architecture/compute-and-rendering-stack.md)
- [Engine Architecture](architecture/engine.md)
- [Interface Contract Definitions (ICDs)](architecture/icds.md)
- [Architecture Overview](architecture/overview.md)
- [Rendering Architecture](architecture/rendering.md)
- [Repository Architecture](architecture/repository.md)

## Handbook — Numerical Methods

- [Advection](handbook/numerical-methods/advection.md)
- [Boundary Conditions](handbook/numerical-methods/boundary-conditions.md)
- [Numerical Method Compatibility](handbook/numerical-methods/compatibility.md)
- [Diffusion](handbook/numerical-methods/diffusion.md)
- [Fluxes](handbook/numerical-methods/fluxes.md)
- [Free-Surface Methods](handbook/numerical-methods/free-surface-methods.md)
- [The Finite Volume Method](handbook/numerical-methods/fvm.md)
- [Linear Solvers](handbook/numerical-methods/linear-solvers.md)
- [Meshes](handbook/numerical-methods/meshes.md)
- [Numerical Method Survey](handbook/numerical-methods/overview.md)
- [Pressure–Velocity Coupling](handbook/numerical-methods/pressure-velocity-coupling.md)
- [Time Integration](handbook/numerical-methods/time-integration.md)
- [Variable Placement: Collocated and Staggered Arrangements](handbook/numerical-methods/variable-placement.md)

## Handbook — Physics

- [Buoyancy](handbook/physics/buoyancy.md)
- [Cloud Formation](handbook/physics/cloud-formation.md)
- [Density](handbook/physics/density.md)
- [Heat Transfer](handbook/physics/heat-transfer.md)
- [Humidity and Species Transport](handbook/physics/humidity.md)
- [Incompressible Flow](handbook/physics/incompressible-flow.md)
- [Physics Handbook](handbook/physics/README.md)

## Implementation

- [PyFlow Golden Demo Specification](implementation/golden-demos.md)
- [PyFlow MVP Definition](implementation/mvp.md)
- [PyFlow Upgrade Paths](implementation/upgrade-paths.md)

## References

- [Book References](references/books.md)
- [Paper References](references/papers.md)
- [Website References](references/websites.md)

## Tutorials

*(no pages yet)*

## Architectural Decisions (ADRs)

- [ADR-001: Use a Typed Property Graph as the Planning Source of Truth](../adr/ADR-001-knowledge-graph.md)
- [ADR-002: Use the Finite Volume Method as the Initial Numerical Framework](../adr/ADR-002-fvm-first.md)
- [ADR-003: Numerical Components Are Modular, Independently Replaceable Strategies](../adr/ADR-003-modular-numerical-strategies.md)
- [ADR-004: Compute-and-Rendering Stack — Class Decision](../adr/ADR-004-compute-rendering-class.md)
- [ADR-005: Compute-and-Rendering Stack — Instance Decision](../adr/ADR-005-compute-rendering-instances.md)
- [ADR-006: Narrow the Knowledge Graph to Traceability and Validation](../adr/ADR-006-knowledge-graph-scope.md)
- [ADR-007: Acceptance Criteria for Simulation Work Are Executable Gherkin Scenarios](../adr/ADR-007-executable-acceptance-criteria.md)
- [Architecture Decision Records](../adr/README.md)
