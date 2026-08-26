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

**Four documents under `docs/` are generated and must never be
hand-edited** (root `CLAUDE.md`): `docs/index.md` via `make docs`,
`docs/planning/dependency-tree.md` via `make dependency-tree` (it
renders `planning/data/components.yaml`, see `docs/planning/CLAUDE.md`),
`docs/repository-inventory.md` via `make inventory` (every tracked
file, from `git ls-files`), and `docs/planning/status.md` via
`make status-report` (task/stage status, from `roadmap.md`'s own prose
plus live repository counts -- `docs/planning/CLAUDE.md`). All four are
checked in `make ci` (`check-docs-index`, `check-dependency-tree`,
`check-inventory`, `check-status`), so a stale copy fails rather than
merges.

The pattern behind all four is worth stating once: **where a document
restates a fact the repository already knows, generate it.** The index
restates the doc tree, the dependency tree restates the component graph,
the inventory restates `git ls-files`, and the status report restates
`roadmap.md`'s own task/stage markers. What stays hand-written is the
part no generator can produce -- why a thing exists, what it is for,
what was deliberately left out. `docs/repository-manifest.md` is the
clearest case of the split: its file inventory was generatable and had
gone stale twice; its per-artifact reasoning is the reason to keep the
document at all. `status.md` is the same split applied to
`roadmap.md`'s own "where does the project actually stand" paragraph,
which had gone stale the same way (`docs/planning/CLAUDE.md`).

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
