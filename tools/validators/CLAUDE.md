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

**`check_graph.py`** (added 2026-08-21,
`adr/ADR-006-knowledge-graph-scope.md`) validates `planning/data/*.yaml`
against `planning/model/*.yaml`.

**It gates, and `check_claims.py` does not -- the difference is worth
understanding before adding a third validator here.** `check_claims.py`
had to stay advisory because distinguishing a real stale claim from a
document legitimately quoting the rule needs judgement, and a checker
that needs judgement cannot block a commit without training people to
ignore it. Every `check_graph.py` rule is instead a definite structural
fact: does this id exist, is this edge type declared, does this path
resolve, is this graph acyclic. Nothing about them is arguable, so they
belong in `make ci`. **Ask which kind a new check is before deciding
where it runs**; getting that backwards produces either a gate people
route around or a warning nobody reads.

Its rules are declared in `planning/model/validation.yaml` rather than
only in the script (P-011), and `tests/unit/test_check_graph.py` has one
test per rule id. Adding a rule means touching all three. Those tests
build miniature graphs in `tmp_path` rather than asserting against the
real `planning/` tree -- a test reading the real graph fails whenever the
graph legitimately changes, for reasons unrelated to the rule it covers.
One test does check the real tree, deliberately separate and named so a
failure reads as "the graph is wrong", never as "a rule is broken".

**`check_manifest.py`** (added 2026-08-21) enforces the contract
`docs/repository-manifest.md` states about itself: "Every maintained
file should appear here exactly once, either as its own row or under an
explicitly stated collective rule." Nothing enforced that, and it failed
twice -- v0.1 described ~35 handbook files that never existed, and
`.claude/` sat unrecorded until a hand sweep found it on 2026-08-19.
Gating, for the same reason as `check_graph.py`.

**The rule it does *not* have is the instructive part.** "Every path the
manifest names exists" was written, run, and removed before shipping: 44
findings on the real manifest, essentially all false. The manifest names
retired things on purpose -- `tools/planner/`, `assets/textures/`,
`docs/planning/numerical-frameworks.md` -- because recording what went
and why is a large part of its value; it also writes section-relative
paths and at least one naming template (`ADR-00N-title.md`). Separating
those from a genuinely stale reference needs a reader.

That is the gate-versus-advisory question from the top of this file,
arriving in a new form: the rule was not wrong so much as *not
gate-shaped*. The options were to make the whole validator advisory
(losing the coverage check's teeth), add suppressions until the false
positives went quiet (which is how an exemption list stops meaning
anything -- see `check_claims.py` above for the same trap), or drop the
rule. Dropping it was right, and
`tests/unit/test_check_manifest.py::test_a_retired_path_the_manifest_still_names_is_not_reported`
pins the decision so it isn't re-added without someone seeing why it
went. **Prefer three rules that always mean something to four where one
needs interpreting.**
