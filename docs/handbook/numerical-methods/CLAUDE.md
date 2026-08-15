# CLAUDE

Numerical Component Handbook entries, per
`docs/planning/knowledge-architecture.md` KA-016 through KA-025. These
explain numerical concepts independently of their eventual PyFlow
implementation -- `fvm.md` is the one exception worth writing first, since
`adr/ADR-002-fvm-first.md` references it and FVM is already decided
(`Status: draft` in the KA spec, versus `planned` for the rest).

`overview.md` (KA-007, the numerical method survey) and
`compatibility.md` (KA-008) hold real content -- they lived at
`docs/planning/numerical-frameworks.md` until 2026-08-15, when they were
moved to the KA-specified paths and split. They are the two entries here
that are *not* stubs, and they are the natural source for the per-method
entries below them.

The ten KA-016..025 entries are currently empty stubs (structure only,
per KA's specified filenames). Do not write numerical-methods content
without citing authoritative sources -- same caution as
`docs/handbook/physics/`.
