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

`compute-and-rendering-stack.md` (added 2026-08-15) is not empty --
survey and compatibility matrix for the array-library/renderer decision,
with live-verified findings on top of a May-2026 knowledge snapshot. The
class-level question it existed to inform is decided
(`adr/ADR-004-compute-rendering-class.md`); it remains the live reference
for A2c's instance-level choice (`docs/planning/backlog.md`). Read its
own status banner before assuming anything in it is still open.

`engine.md`, `icds.md`, `overview.md`, `rendering.md` and `repository.md`
remain empty -- structure only.
