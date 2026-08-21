# CLAUDE.md

This file contains documentation-specific instructions.

These rules extend the repository-level `CLAUDE.md`.

---

# Purpose

Maintain documentation that is accurate, maintainable and easy to navigate.

---

# Responsibilities

When editing documentation:

- follow the documentation guidelines
- avoid duplication
- prefer improving existing documentation over creating new documents
- maintain cross references where appropriate

---

# Navigation

**Two documents under `docs/` are generated and must never be
hand-edited** (root `CLAUDE.md`): `docs/index.md`, via `make docs`, and
`docs/planning/dependency-tree.md`, via `make dependency-tree` (added
2026-08-21 -- it renders `planning/data/components.yaml`, see
`docs/planning/CLAUDE.md`). Both are checked in `make ci`, so a stale
copy fails rather than merges.

`docs/index.md` is the generated map of every documentation page,
grouped by directory (tools/generators/CLAUDE.md). It is **generated,
not hand-written** -- never edit it directly; run `make docs` after
adding, moving, deleting, or re-titling a doc, and `make check-docs-index`
(part of `make ci`) fails the build if it's stale. Its link text comes
from each page's own first `#` heading, so keep that heading accurate
and specific -- it's doing double duty as the page's title and its
entry in the index.

`README.md`'s "Where to Start" section is the separate, small,
hand-curated first-read order and stays that way; it is not meant to be
comprehensive, `docs/index.md` is.

---

# Preferred Behaviour

Capture decisions rather than discussions.

Document intent before implementation.

Prefer concise documents with clear responsibilities.

---

# Validation

If documentation appears inconsistent:

- identify the authoritative source
- update incorrect documentation
- avoid creating duplicate explanations

This is the reactive case -- finding an inconsistency someone else left.
The proactive case is the Blast Radius rule in `docs/practices.md`: work
out what a change affects *before* making it, and update all of it in the
same change, so this section has less to catch.
