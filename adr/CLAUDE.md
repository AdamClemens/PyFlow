# CLAUDE

Architecture Decision Records. Conventions (naming, lifecycle, structure,
when to write one) are already fully specified in `README.md` in this
directory -- read that before adding or editing an ADR; don't duplicate
it here.

Six exist: `ADR-001` (knowledge/capability graph), `ADR-002` (FVM-first),
`ADR-003` (modular numerical strategies), `ADR-004` (compute/rendering
class), `ADR-005` (compute/rendering instances), `ADR-006`
(knowledge-graph scope) -- all `Accepted`. The next number is `007`.
Numbering is sequential and permanent; never renumber or reuse a number,
even if an ADR is later superseded.

**Two pairs so far where a later ADR narrows an earlier one rather than
superseding it**: `ADR-004`/`ADR-005` (class, then instances) and
`ADR-001`/`ADR-006` (the graph, then its scope). Both earlier ADRs stay
`Accepted` and both pairs should be read together. Prefer this shape
over `Superseded` when the original decision still stands and only its
scope or its instances are being settled -- superseding would discard a
decision that is still in force, and lose the record of what was
deliberately left open at the time.

An ADR's status changes (e.g. to `Superseded`) are recorded in the ADR
itself, not by editing history elsewhere -- but if something else in the
repository was decided *because of* an ADR, check whether that decision
still holds before changing the ADR's status (Blast Radius,
`docs/practices.md`).
