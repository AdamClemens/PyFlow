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

All four are `planned` per the KA spec and not yet written -- currently
empty besides this file.

---

# Maintenance

Reconciled against KA §17-18 on 2026-08-15. Write each file once its
listed dependencies (see the relevant KA-0xx entry) exist as real content,
not before -- writing them early risks empty scaffolding, the same reason
`docs/CHANGELOG-DESIGN.md`'s 15-08-2026 entry gives for deferring the
prompt generator itself.
