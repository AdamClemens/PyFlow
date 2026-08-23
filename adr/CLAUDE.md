# CLAUDE

Architecture Decision Records. Conventions (naming, lifecycle, structure,
when to write one) are already fully specified in `README.md` in this
directory -- read that before adding or editing an ADR; don't duplicate
it here.

**For what exists, read `docs/index.md`'s ADR section** -- it is
generated from the tree by `make docs` and checked by `make ci`, so it
cannot be wrong. **The next number is one past the highest that exists
there.**

That is deliberately a rule rather than a value. This paragraph read
"Six exist: ADR-001 ... ADR-006 -- all `Accepted`. The next number is
`007`" until 2026-08-22, and was already wrong when it was read that
day: `ADR-007` had landed hours earlier, in the same change that
introduced the merge gate requiring exactly this kind of restatement to
be updated. **Nothing mechanical caught it** -- `make check-references`
only sees paths that do not resolve, and a count is not a path -- and
nothing will catch the next one either, which is why the count is gone
rather than corrected. Same reasoning as `docs/CLAUDE.md`'s: where a
document restates a fact the repository already knows, point at the
generated version instead of keeping a copy.

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
