# PyFlow Golden Demo Specification

Per `docs/planning/knowledge-architecture.md` KA-035.

## Intent

A golden demo is both a useful demonstration and a functional regression
test of a meaningful vertical slice. Every Golden Demo listed in
`docs/planning/implementation-plan.md` ("Golden Demos" table) should
eventually have an entry here defining what "working" means for it
concretely enough to verify automatically.

## Definition of Done (applies to every golden demo)

- Executable.
- Deterministic, or its non-determinism is appropriately controlled
  (e.g. a fixed random seed).
- Verifies meaningful behaviour, not just "it ran without crashing."
- Produces useful visual output where applicable.
- Documented.
- Included in regression testing.

## Initial Golden Demo

A 2D air-current simulation, corresponding to the MVP
(`docs/implementation/mvp.md`). It must:

- construct the domain (structured 2D Cartesian mesh);
- configure the numerical components (via `src/pyflow/configuration/`,
  not hardcoded -- see `adr/ADR-003-modular-numerical-strategies.md`);
- execute timesteps;
- produce measurable velocity fields;
- render the result.

This is the demo the MVP's own Definition of Done refers to as "golden
demo exists."

## Future Demos

Add an entry here when a new capability is implemented, per
`docs/planning/implementation-plan.md`'s Golden Demos table (Scalar
Transport, Heat Diffusion, Lid-Driven Cavity, Flow Around Cylinder,
Vortex, Dam Break, 3D Cavity). Do not add a demo entry for a capability
that doesn't exist yet -- these get written when the corresponding
capability level is reached, not speculatively ahead of it.

## Relationship to `examples/golden-demos/`

This file defines *what* each golden demo must do and how it's verified.
`examples/golden-demos/` holds the actual runnable demo code once
written. Neither exists yet for the initial demo above -- this is the
specification, not the implementation.
