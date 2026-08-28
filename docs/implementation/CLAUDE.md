# CLAUDE

This directory holds implementation-level artifacts per
`docs/planning/knowledge-architecture.md`:

- `mvp.md` (KA-031) -- the MVP definition (what "smallest complete
  PyFlow" means). Extracted from `docs/planning/implementation-plan.md`
  on 2026-08-15.
- `upgrade-paths.md` (KA-032) -- how each MVP numerical component can
  later be replaced or extended. Extracted the same day.
- `golden-demos.md` (KA-035) -- what each golden demo must do and how
  it's verified. Written 2026-08-15; the demos themselves live under
  `examples/golden-demos/`, not here. Note that a demo is a **YAML
  configuration file**, not runnable code: the public-API rule
  (2026-08-16) requires every golden demo to run through
  `pyflow run --config <file>`, so there is no demo-specific script.
  This line said "runnable code" until 2026-08-18, describing the shape
  the rule had already replaced -- see `examples/golden-demos/CLAUDE.md`,
  which is authoritative for what lives there.
- `config-template.yaml`, added 2026-08-28 at a user's direct request.
  **Not itemised in `docs/planning/knowledge-architecture.md`** -- same
  as `.claude/` and `tools/`, the KA spec does not enumerate every
  directory or file the project ends up wanting; recorded in
  `docs/repository-manifest.md` instead. **Generated, never hand-edited**
  (`tools/generators/generate_config_template.py`, from
  `src/pyflow/configuration/schema.py`): every `PyFlowConfig` field, with
  a comment above each one stating what counts as a valid value and what
  does not. Regenerate with `make config-template`; `make
  check-config-template` (part of `make ci`) fails if it's stale. See
  `src/pyflow/configuration/CLAUDE.md` for the rule keeping it current as
  the schema evolves.

Keep these in sync with `adr/ADR-002-fvm-first.md` and
`adr/ADR-003-modular-numerical-strategies.md`, which `mvp.md` and
`upgrade-paths.md` both reference. If the MVP's component choices change,
update `mvp.md` directly rather than letting `implementation-plan.md` or
`roadmap.md` silently diverge from it.
