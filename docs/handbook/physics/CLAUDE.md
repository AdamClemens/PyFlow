# CLAUDE

Physics Handbook entries, per `docs/planning/knowledge-architecture.md`
KA-009 through KA-015. See `README.md` in this directory for what belongs
in an entry.

All six entries were written 2026-08-17 (`docs/planning/backlog.md` E4),
in KA's own dependency order: `incompressible-flow.md` first (the MVP's
physical model, and what every other entry here builds on), then
`heat-transfer.md`, `density.md`, `humidity.md`, `buoyancy.md`, and
`cloud-formation.md` last (the entry with the most dependencies -- it
draws on all four of the others). Every entry cites authoritative
sources, per the standing caution below -- this is exactly the kind of
domain content where a confident-sounding but wrong claim is costly.
When in doubt, cite a source or flag the uncertainty rather than
presenting an invented claim as settled.

**Reviewed for scientific accuracy 2026-08-18** (maintainer's request).
All six entries changed; each one's Maintenance section records what and
why. Two of the findings are worth carrying forward as guidance rather
than as one-off fixes:

- **`buoyancy.md` had the Boussinesq buoyancy term's sign inverted** for
  its own stated meaning of $\mathbf{g}$ -- warm fluid would have sunk.
  Both sides of the expression were flipped consistently, which is why it
  read as coherent and survived being written. Where a sign depends on a
  convention (a vector pointing down versus a positive magnitude with an
  upward unit vector), state the convention *and* sanity-check the result
  in words, the way that entry now does.
- **"Air holds moisture" is wrong and was in two entries.** Saturation
  vapour pressure is a property of the vapour-liquid equilibrium, not a
  capacity of air. The everyday framing gives the right answer for the
  wrong reason, which is fine in conversation and not fine in
  `cloud-formation.md`, whose whole subject is *why* condensation
  happens. Standard-but-loose domain phrasing is a real risk in this
  directory, distinct from the invented-claim risk the caution above
  covers.

Also record a model's validity limits, not only its content: `density.md`
now states both Boussinesq conditions, including the shallow-domain one
that genuinely bounds how far this approximation carries PyFlow toward
the atmospheric ambitions in `docs/planning/dreams.md`.
