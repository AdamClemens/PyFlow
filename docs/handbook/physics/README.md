# Physics Handbook

Per `docs/planning/knowledge-architecture.md` KA-009. Provides a stable
place for future developers to understand both the physical phenomena
PyFlow models and the equations governing them, independently of how
PyFlow happens to implement them.

## Structure

One file per phenomenon/process. Current entries (KA-010 through
KA-015, all `draft` -- written 2026-08-17,
`docs/planning/backlog.md` E4; all six reviewed for scientific accuracy
2026-08-18, with each entry's own Maintenance section recording what
changed and `CLAUDE.md` in this directory recording the guidance that
came out of it):

- `incompressible-flow.md` -- the physical model underlying the MVP
- `heat-transfer.md` -- temperature as a transported field
- `density.md` -- density as a field/property
- `humidity.md` -- humidity/species concentration transport
- `buoyancy.md` -- buoyancy's coupling to fluid motion
- `cloud-formation.md` -- physical processes behind cloud formation as a
  future capability

## What Belongs in an Entry

Each entry should generally cover:

- the phenomenon or process itself
- physical interpretation
- assumptions
- governing equations
- meaning of important terms
- relationship to other phenomena
- numerical implications
- references to more detailed authoritative texts

Derivations should be concise unless necessary for understanding. An
entry should clearly separate physical knowledge from implementation
choices, and should not become an exhaustive textbook -- link out to
authoritative sources for that.

## Maintenance

When an entry gets written, update this README's status note for it and
this directory's `CLAUDE.md`.
