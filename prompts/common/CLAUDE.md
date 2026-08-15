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
  Constraints / Definition of Done / Output)
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
