# CLAUDE

Numerical Component Handbook entries, per
`docs/planning/knowledge-architecture.md` KA-016 through KA-025. These
explain numerical concepts independently of their eventual PyFlow
implementation.

`overview.md` (KA-007, the numerical method survey) and
`compatibility.md` (KA-008) hold real content -- they lived at
`docs/planning/numerical-frameworks.md` until 2026-08-15, when they were
moved to the KA-specified paths and split, and remain the natural source
the per-method entries draw from.

All ten KA-016..025 entries were written 2026-08-17
(`docs/planning/backlog.md` E3), in the dependency order the backlog
laid out: `fvm.md` first (since `adr/ADR-002-fvm-first.md` already
referenced it), then `meshes.md`, `variable-placement.md`, `fluxes.md`,
`advection.md`, `diffusion.md`, `time-integration.md`,
`pressure-velocity-coupling.md`, `linear-solvers.md`, and
`boundary-conditions.md` last. Every entry cites authoritative sources,
per the standing caution below -- same caution as
`docs/handbook/physics/`. Do not write numerical-methods content without
citing authoritative sources; this is exactly the kind of domain content
where a confident-sounding but wrong claim is costly.
