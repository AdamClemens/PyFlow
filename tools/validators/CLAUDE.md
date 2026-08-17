# CLAUDE

Repository-consistency checks that run outside `make lint` (which only
covers formatting/typing/import hygiene, per `.pre-commit-config.yaml`).

**`check_docs.py`, added 2026-08-17.** Scans every `*.md` file for
Markdown links (`[text](target)`) and flags any relative target that
doesn't resolve to a real file -- the mechanical half of the Blast
Radius rule's "grep for the thing's name" check (`docs/practices.md`),
scoped specifically to links rather than arbitrary renamed terms (that
part still needs a human, since it requires judgement about what
changed). Run via `make check-docs`, and as part of `make ci`. Only
checks that the target *exists*; it does not verify that a
`file.md#heading` fragment matches a real heading in that file -- that
would need parsing every target's heading slugs, a heavier check not
built yet. Add a matching mechanical check here if another
Blast-Radius-adjacent grep (e.g. stale backlog ID cross-references)
turns out to fire often enough to be worth automating -- don't add one
speculatively ahead of that.
