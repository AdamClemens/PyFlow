# CLAUDE

This file contains instructions specific to `prompts/common/`.

These rules extend the repository-level `CLAUDE.md`.

---

# Purpose

Holds reusable material shared across every generated prompt: the
task-prompt TEMPLATE, and fully-instantiated task prompts generated from
it that are ready to hand to an agent.

Global project context used to live here as `BRIEF`; it was retired
2026-08-15 in favour of `prompts/global/project.md` (KA-039's actual
canonical name and location) once that file existed to replace it. New
prompts should reference `prompts/global/project.md`, not this directory,
for global context.

---

# Contents

- `TEMPLATE.md` — the reusable task-prompt structure (Context / Task /
  Constraints / Definition of Done / Review Cycle / Output), plus a
  condensed Worked Example instantiated against the real, closed
  TASK-021 (added 2026-08-24, per `agents.md`'s own "real precedent over
  hypothetical" rule, which the template hadn't been following against
  itself). The Review Cycle section (added 2026-08-24) requires a
  code-writing task's diff to be reviewed under `AUDITOR.md`'s stance,
  fixed, and re-reviewed until a pass finds nothing, before its
  Definition of Done counts as met.
- `AUDITOR.md` — the reusable adversarial-review stance (added
  2026-08-24), extracted from `docs/practices.md`'s End-of-session
  consistency review once `TEMPLATE.md`'s Review Cycle needed the same
  stance a second place. Owns the stance only; what to check stays in
  `docs/practices.md` and each task's own Definition of Done.
- `task-*.md` — instantiated, ready-to-run prompts generated from the
  template for specific backlog items (see `docs/planning/backlog.md`)

---

# Maintenance

When a `task-*.md` prompt has been executed and its Definition of Done is
met, mark the corresponding backlog item done in `docs/planning/backlog.md`
rather than deleting the prompt file — it's a record of what was asked for.

If the TEMPLATE structure changes, existing `task-*.md` files do not need
to be retroactively rewritten, but new ones should follow the current version.

Note: `prompts/code/` and `prompts/docs/` were retired 2026-08-15 -- they
never matched the KA spec's layout (no code/docs axis exists in it) and
never held any content. See `docs/planning/backlog.md` §1 "Prompt
directory layout mismatch" for the decision record.
