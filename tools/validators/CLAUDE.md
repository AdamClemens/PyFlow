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

**It reads `git ls-files`, not the working tree** (changed 2026-08-31 by
the Stage 6 exit audit). It used to walk `REPO_ROOT.rglob("*.md")`
against a hardcoded `EXCLUDED_DIRS` of directory names to skip, which is
a list that has to keep up with every tool that writes into the working
tree -- and it had already fallen behind one. `.claude/worktrees/` holds
a full second checkout while a `git worktree` is open, so that audit's
run reported 14 completeness claims of which **12 were this repository's
own documents seen twice**, burying the 2 real candidates in a report
whose entire value is that a human reads every line of it. Reading
tracked files excludes every ignored directory structurally rather than
by name, is the same source `check_references.py`/`check_manifest.py`
already use, and narrows the check to the documents the repository
actually maintains -- which is what the rule is about. Pinned by
`tests/unit/test_check_claims.py::test_only_tracked_markdown_files_are_read`,
which asserts the *property* (tracked, not "not this one directory") and
was verified by reverting the old implementation and watching it fail.
`EXCLUDED_DIRS` survives for `directory_has_content` alone, which still
walks a directory named in prose to decide whether it holds anything.

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

**`check_references.py`** (added 2026-08-22) fails if prose names a
repository path that does not exist -- a typo in a filename, a module
renamed without its references, a path that was always wrong. Gating.

(This paragraph originally illustrated the point with a misspelled
`docs/practices.md` in backticks. The script flagged it, correctly, on
the first run after being wired in -- a validator's own documentation is
prose like any other. Illustrate a bad path by describing it, not by
writing one.)

**Read the `check_manifest.py` entry below before touching this one.**
This is the rule that entry describes as written, run, and *removed*:
"every path the manifest names exists", 44 findings, essentially all
false. It returns here in a narrower form, and the narrowing is the
whole design. Rather than growing an exemption list until it means
nothing -- the trap `check_claims.py` above already documents -- it
excludes the three documents that made the original unworkable
(`repository-manifest.md`, `backlog.md`, `CHANGELOG-DESIGN.md`), each of
which names retired things *as its job*. It also resolves
section-relative and sibling-relative paths, which is what most of the
original's false positives actually were.
`tests/unit/test_check_references.py::test_documents_that_name_retired_things_are_excluded`
pins that so the exclusion cannot quietly disappear and take the old
problem's place.

Its `PLANNED` table is the part worth copying elsewhere: an artifact a
roadmap task *names but has not built yet* is listed with its task id,
and the script fails once that path appears -- so the entry must be
deleted when the task lands, and if the implementation named the file
something else, that mismatch is a build failure rather than a
discrepancy nobody notices. An exemption with an expiry date, and a
promise that gets checked.

**That was not true of `.feature` paths until 2026-08-30, and the
failure is worth keeping rather than just fixing.** `.feature` was
never in this script's `EXTS` tuple, so no feature path in any document
was ever checked. Stage 5 nonetheless listed four of them in `PLANNED`
on 2026-08-28, under a comment describing them as checked promises;
none of those entries could have fired, and their silence was
indistinguishable from a pass. Found when Stage 6's criteria named five
feature files that do not exist and this gate said nothing.
`tests/unit/test_check_references.py::test_a_feature_file_is_a_checked_path`
is the regression, and it fails against the pre-fix tuple -- verified
by reverting the one line rather than assumed. The general shape is the
one the Stage 5 exit audit met in `generate_status_report.py`'s
scenario-count pattern (`docs/practices.md`): **a rule that matches
nothing reports nothing, which reads exactly like a clean pass.** When
adding a checked promise, check that the checker can see it.

**`check_scenarios.py`** (added 2026-08-22,
`adr/ADR-007-executable-acceptance-criteria.md`) fails if a Gherkin
scenario exists that nothing binds. Gating, and it has to be: pytest
does not error, skip, or warn for a `.feature` file no module runs -- it
silently never runs, while reading exactly like a criterion that passes.
Since those files *are* the acceptance criteria for Stage 4+ work, that
one silence would make the whole decision worthless. It deliberately
does not check that steps are implemented; pytest-bdd already fails
loudly for a missing step, and duplicating a check that already exists
is how a validator earns being ignored.

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
