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

**`check_claims.py`, added 2026-08-18.** The completeness-claim check the
2026-08-18 review identified as having earned the test above. It reports
documentation asserting that some file or directory is empty, unwritten,
or a stub when it actually has content -- `docs/practices.md`,
"Completeness claims belong only in the two documents that track
completeness". Run via `make check-claims`, and as step 10 of the
end-of-session consistency review.

**It verifies rather than pattern-matches.** It does not flag prose for
containing the word "empty": it resolves the paths named on the same line
(or the line above -- these documents hard-wrap, and both real drifts
wrapped that way) and reports only where the claim contradicts what is on
disk. A claim about a genuinely empty file, or a file that doesn't exist,
is never reported.

**Advisory, not a `ci` gate, on purpose.** It exits 0 even with findings,
because a document quoting the rule or describing its own directory is
indistinguishable from a violation without judgement. Two suppressions
keep the noise down -- a claim inside quotation marks, and one preceded by
a reporting verb ("`engine.md` still *described* the handbook as
unwritten") -- and both were derived from real false positives rather than
guessed at.

**One known false positive**, left deliberately:
`docs/planning/knowledge-architecture.md` line ~1858 reads "no file
tracked in `docs/repository-manifest.md` is empty", a rule about the
manifest's *contents*, not a claim about the manifest. A quantifier-based
suppression was built for it and then removed, because the real
`docs/glossary.md` drift read "no release process is defined,
`releases.md` is empty" -- suppressing on a nearby quantifier silently
discarded a true positive. One reported false positive beats a
silently-missed real one for an advisory tool.
`tests/unit/test_check_claims.py` pins this decision as a named test so a
future contributor doesn't re-add the suppression without seeing why it
went.

**The other earned candidate is now partly covered elsewhere, and partly
still open.** Stray control characters in Markdown are caught by the
`mixed-line-ending` pre-commit hook (added 2026-08-18, `--fix=no`), which
fires on the carriage return a mangled `\r` escape leaves behind. Not
covered: unbalanced inline maths (an odd number of unescaped `$` on a
line), which would catch a corrupted equation that left no control
character behind. Build that here if it ever fires for real -- the bar in
the paragraph above still applies.
