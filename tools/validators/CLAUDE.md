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

**Two greps have now earned that test** (2026-08-18 documentation
review; recorded as candidates with evidence, not as work committed to).
Neither is built yet, and the bar in the paragraph above still applies --
build one when it would have saved a real review, not because it is
listed here:

- **Completeness claims outside the two documents that track
  completeness.** `docs/practices.md` now states this as a rule with no
  mechanical enforcement behind it. A case-insensitive grep for
  `is empty|not yet written|unwritten|still a placeholder|not yet
  decided`, excluding `docs/repository-manifest.md`,
  `docs/planning/backlog.md` and the append-only
  `docs/CHANGELOG-DESIGN.md`, would have caught all nine instances the
  review found across `docs/`, `prompts/` and four `CLAUDE.md` files.
  Expect false positives where a document legitimately quotes the rule
  itself, so this wants a review-and-confirm shape rather than a hard CI
  failure.
- **Stray control characters and unbalanced inline maths in Markdown.**
  A carriage return anywhere but a line ending, or an odd number of
  unescaped `$` on a line. Motivated by a real corruption during that
  review: `$\rho$` became `$ho$` with an embedded CR, and `make
  check-docs` passed -- see `docs/handbook/CLAUDE.md`'s notation section.
  This one is cheap, deterministic, and a genuine CI failure rather than
  a judgement call, which makes it the better first candidate of the
  two.
