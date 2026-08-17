# CLAUDE

Architecture Decision Records. Conventions (naming, lifecycle, structure,
when to write one) are already fully specified in `README.md` in this
directory -- read that before adding or editing an ADR; don't duplicate
it here.

Five exist: `ADR-001` (knowledge/capability graph), `ADR-002` (FVM-first),
`ADR-003` (modular numerical strategies), `ADR-004` (compute/rendering
class), `ADR-005` (compute/rendering instances) -- all `Accepted`. The
next number is `006`. Numbering is sequential and permanent; never
renumber or reuse a number, even if an ADR is later superseded.

An ADR's status changes (e.g. to `Superseded`) are recorded in the ADR
itself, not by editing history elsewhere -- but if something else in the
repository was decided *because of* an ADR, check whether that decision
still holds before changing the ADR's status (Blast Radius,
`docs/practices.md`).
