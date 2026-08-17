# CLAUDE

This file contains instructions specific to `prompts/features/`.

These rules extend the repository-level `CLAUDE.md`.

---

# Purpose

Per-artifact-kind prompt context: tells an agent what role a given kind of
document plays and what quality is expected of it, per
`docs/planning/knowledge-architecture.md` KA-040 through KA-043.

---

# Expected Files

- `handbook.md` -- KA-040, how Handbook entries should be written
- `adr.md` -- KA-041, how ADRs should be written
- `implementation-plan.md` -- KA-042, how implementation-plan tasks
  should be written
- `agents.md` -- KA-043, how `CLAUDE.md` files should be written --
  notably, this is the generated-prompt counterpart to the standing rule
  in the root `CLAUDE.md` ("Maintaining CLAUDE.md Files"), for use once a
  prompt generator exists

All four written 2026-08-17 (`docs/planning/backlog.md` E8), `draft` per
the KA spec. Each file's listed KA-0xx dependencies were already real
content at the time -- documentation guidelines, engineering principles,
practices, `adr/README.md`, and the Handbook's *structure* (not yet its
content: KA-040 depends on handbook structure, which the physics/
numerical-methods `README.md`/`CLAUDE.md` files already establish, not on
the handbook entries themselves being written).

---

# Maintenance

Reconciled against KA §17-18 on 2026-08-15; the four files written
2026-08-17. `implementation-plan.md` complements rather than duplicates
`prompts/common/TEMPLATE.md` -- it explains what belongs in the
template's `## Task` section when the source is a roadmap/
implementation-plan item; the template itself still owns the overall
prompt structure.
