# CLAUDE

This directory holds implementation-level artifacts per
`docs/planning/knowledge-architecture.md`:

- `mvp.md` (KA-031) -- the MVP definition (what "smallest complete
  PyFlow" means). Extracted from `docs/planning/implementation-plan.md`
  on 2026-08-15.
- `upgrade-paths.md` (KA-032) -- how each MVP numerical component can
  later be replaced or extended. Extracted the same day.
- `golden-demos.md` (KA-035) -- what each golden demo must do and how
  it's verified. Written 2026-08-15; the demos themselves (runnable code)
  live under `examples/golden-demos/`, not here.

Keep these in sync with `adr/ADR-002-fvm-first.md` and
`adr/ADR-003-modular-numerical-strategies.md`, which `mvp.md` and
`upgrade-paths.md` both reference. If the MVP's component choices change,
update `mvp.md` directly rather than letting `implementation-plan.md` or
`roadmap.md` silently diverge from it.
