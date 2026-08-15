# CLAUDE

Architecture documentation. `overview.md`, `rendering.md`, `repository.md`
are pre-existing empty stubs with no basis in
`docs/planning/knowledge-architecture.md` -- not redundant, just not
itemised there; treat as legitimate, KA doesn't have to enumerate every
architecture doc the project ends up wanting.

`icds.md` (KA-030, Interface Contract Definitions -- the
user/configuration-facing interfaces PyFlow's components expose, *not*
every internal Python interface) and `engine.md` (KA-029, conceptual
engine architecture: mesh/variables/flux/advection/diffusion/time-
integration/pressure-velocity-coupling/linear-solvers/boundary-conditions
as replaceable layers behind contracts) were added 2026-08-15, both per
KA. `engine.md` is not the same document as `overview.md` -- resolved as
two separate files, not one renamed.

All files in this directory are currently empty -- structure only.
