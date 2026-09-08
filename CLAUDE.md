# CLAUDE.md

This file contains the global operating rules for contributors to the PyFlow repository.

These instructions apply to both human contributors and automated agents unless a more specific `CLAUDE.md` exists within a subdirectory.

Lower-level `CLAUDE.md` files may extend these rules but should not contradict them.

---

# Mission

Build a maintainable, understandable and enjoyable fluid dynamics simulation engine.

The repository should preserve project knowledge so that progress never depends on any individual's memory.

---

# Core Responsibilities

Contributors should:

- improve the repository
- preserve project knowledge
- leave the repository easier to understand than they found it
- follow the engineering principles
- follow the documentation guidelines
- record significant architectural decisions
- avoid unnecessary complexity
- keep `CLAUDE.md` files current as understanding grows (see "Maintaining
  CLAUDE.md Files" below)

---

# Integrity

Lying is never an option. Not to save time, not to smooth over an
inconsistency, not to avoid an awkward admission.

Report uncertainty, mistakes and bad news plainly and as soon as they are
known. A wrong answer that is honestly labelled uncertain is recoverable;
a confident fabrication is not, and the institutional-memory philosophy
this repository is built on assumes what is written down is true.

This is what "say so explicitly" means everywhere else in this file --
the Blast Radius rule and the Validation section below both ask for the
same honesty, in narrower situations. This section is the general
statement they follow from.

Added 2026-08-15, maintainer's instruction.

---

# Planning Philosophy

The planning system exists to accelerate PyFlow.

Avoid spending time improving the planning system unless it directly benefits development of PyFlow.

---

# Maintaining CLAUDE.md Files

`CLAUDE.md` files are living documents, not one-time scaffolding.

Whenever work in a directory surfaces something a future contributor
(human or agent) would need to know -- a convention, a decision, a purpose
that wasn't obvious, a pitfall hit and resolved -- amend the nearest
`CLAUDE.md` with that knowledge before moving on. Do not wait for a
directory's content to be "finished" first; update incrementally, as
understanding accumulates.

A generic placeholder (e.g. "This directory contains project files. Follow
the repository conventions...") is acceptable only until something specific
is known about that directory. Replace it as soon as that changes.

---

# Merge Gate

**A branch does not merge to `main` until the repository is entirely
self-consistent -- not merely until the pipeline is green.** Standing
rule, 2026-08-22.

"Ready to merge" means four things, and any one failing means not ready:

1. **Mechanically green** -- `make ci` in full, plus a real CI run on
   both platforms for anything touching code.
2. **Internally consistent** -- every restatement of every fact the
   branch changed, updated in the same branch (Blast Radius, below, run
   as a grep rather than remembered).
3. **The intent is met** -- every acceptance criterion the branch claims
   to discharge is checked by something that would *fail* if the intent
   were violated, not merely by something that passes.
4. **Said honestly** -- if any of the three is unverified, say which and
   why. Green CI is not a substitute for the sentence.

This exists because green CI has never once meant ready here: the pan
scale error, the unvalidated mesh accessors, the truncated mesh config,
the contract suite that proved less than it claimed, and an
architecture document that described the Stage 0 repository for two
stages all merged green. Full rule, and what applying it retroactively
turned up: `docs/practices.md`.

**Where the intent is not clear enough to write a failing check for,
stop and hold a design session** rather than picking the reading that is
easiest to implement -- also `docs/practices.md`.

---

# Feature Verification Before Reporting Done

Before reporting a user-facing feature as done, run the exact command a
user would run -- `pyflow run`, `make graph`, whatever the feature's own
entry point is -- and describe the real output or the actual rendered
window, not the expected one. Confirm every new CLI flag actually
appears in `--help`.

Then re-read the diff as a hostile auditor, not as its author: list
anything overstated, defaulted off, or unreachable before calling the
work finished.

Added 2026-09-08, maintainer's instruction, after a HUD that shipped
defaulted off and a `--demos` flag that was never wired into the CLI
both passed review because neither was ever actually run. This is the
concrete form Merge Gate criterion 3 ("the intent is met") takes for
anything a person looks at or types.

---

# Branch Discipline

**All coding work happens on a branch, never directly on `main`.**
Standing rule, 2026-09-08, maintainer's instruction.

Create a branch before the first edit, not after -- `docs/practices.md`
already names the branch-naming convention (`<kind>/<short-hyphenated-
subject>`) and the one-branch-per-task granularity; this rule is what
makes both apply every time rather than only when someone remembers to
branch first. `main` only receives commits by merge, once the Merge Gate
above is satisfied.

The one exception: a trivial single-file edit to a `CLAUDE.md` or other
process-rule file may be committed directly to `main` when the user
explicitly says so in the same turn -- it does not need its own
branch/PR. Everything else follows the full cycle: open a PR, watch CI
to green, merge, delete the branch, and return to `main` before starting
the next task. `make preflight` (Development Commands, below) must pass
locally before any commit made on a branch; it is a fast local gate, not
a substitute for `make ci` in full, which the Merge Gate above still
requires before merge.

Added 2026-09-08, later the same day as the standing rule above, after
noticing this section said "never directly on main" without saying what
to do once a branch exists.

---

# Acceptance Criteria for Simulation Work

**From Stage 4 (`docs/planning/roadmap.md` TASK-023) onward, a task's
acceptance criteria are a Gherkin `.feature` file under
`tests/features/`** -- the criteria themselves, not a restatement of
them. `adr/ADR-007-executable-acceptance-criteria.md` records the
decision, its scope, and the one real risk it carries.

Stage 3 is deliberately exempt: it defines interfaces and computes
nothing, so its criteria have no user-observable behaviour to describe.
Contract suites stay plain pytest.

---

# Blast Radius

Before making a change, work out what else it affects -- what references
it, restates it, tracks it in an inventory, or was decided because of it
-- and update all of it in the same change.

Searching for the name of the thing you are changing is usually enough to
find the radius.

If something in the radius cannot be updated now, say so explicitly where
the divergence is. A recorded inconsistency is a known problem; an
unrecorded one is a trap.

Full rule, with the specific cases most often missed: `docs/practices.md`.

---

# Session Handoff

The repository must always be left in a state internally consistent
enough that a fresh agent, with no memory of this session, could pick up
the next piece of work and trust what the documents say.

At the end of a session that touched multiple documents, or spanned
several rounds of work, verify this is actually true rather than
assuming it -- re-check status tables, counts and cross-references
against the current state directly, the same way a fresh agent would.
Where this finds a gap, add a rule that would have prevented it, not
just a one-off fix.

Checklist, with the specific things most often missed: `docs/practices.md`.

---

# Development Commands

Every command below is a `Makefile` target; run `make <target>` from the
repository root. Do not reverse-engineer the `Makefile` or reach for
tool-specific commands (`pytest`, `ruff` directly, etc.) when the
equivalent target already exists here -- that is exactly the drift
the `ci` target (below) exists to
prevent (P-011, single authoritative source).

- `make install` -- set up the development environment (`uv sync` plus
  the git pre-commit hook). Start here on a fresh clone.
- `make lint` -- run `pre-commit` across the repository (formatting and
  linting, code and docs).
- `make format` -- `ruff format .` alone. Deliberately narrower than
  `lint` (no `pre-commit`, no docs/YAML/whitespace/spelling checks): a
  fast standalone reformat, not a substitute for `lint`, which is the
  comprehensive one. **Missing from this list until 2026-08-22** even
  though the target has existed since TASK-002 -- which matters more
  here than elsewhere, because this section tells a contributor not to
  reverse-engineer the `Makefile` when the equivalent target is already
  listed. A list that claims to be authoritative has to be complete.
- `make typecheck` -- `mypy --strict` over `src` and `tests`.
- `make test` -- run the test suite with coverage.
- `make check-docs` -- fail if any relative Markdown link is broken.
- `make check-docs-index` -- fail if `docs/index.md` doesn't match what
  the current doc tree would generate.
- `make check-graph` -- fail if the planning knowledge graph
  (`planning/data/*.yaml`) is structurally inconsistent with its model
  (`planning/model/*.yaml`): a dangling edge, an undeclared relationship
  type, a path that doesn't resolve, a dependency cycle. Unlike
  `check-claims` this one **gates**, because every rule it applies is a
  definite structural fact rather than something needing judgement. See
  `adr/ADR-006-knowledge-graph-scope.md`.
- `make dependency-tree` -- regenerate
  `docs/planning/dependency-tree.md` from the component graph. Like
  `docs/index.md`, this is generated output and must never be hand-edited.
- `make check-dependency-tree` -- fail if that file is stale.
- `make inventory` -- regenerate `docs/repository-inventory.md`, the
  complete list of every tracked file, from `git ls-files`. Generated
  output; never hand-edit. It is the factual half of
  `docs/repository-manifest.md`, split out because a hand-restated file
  inventory goes stale.
- `make check-inventory` -- fail if that file is stale.
- `make check-manifest` -- fail if any tracked file is neither named in
  `docs/repository-manifest.md` nor covered by a collective rule
  declared in that document. Deliberately one-directional: it does not
  check that everything the manifest names still exists, because
  recording what was retired is part of that document's job.
- `make docs` -- regenerate `docs/index.md`. Run this, not a manual
  edit, after adding, moving, deleting, or re-titling a documentation
  page -- see `docs/CLAUDE.md`.
- `make check-references` -- fail if prose names a repository path that
  does not exist. Gating. The narrowed return of a rule
  `check_manifest.py` tried and dropped in 2026-08-21; it stays workable
  by excluding the three documents whose job includes naming what was
  retired, rather than by growing an exemption list
  (`tools/validators/CLAUDE.md`). Its `PLANNED` table is a *checked
  promise*: an artifact a roadmap task names but has not built yet,
  which must be deleted from the table when that task lands -- and if
  the implementation named the file something else, this fails.
- `make check-scenarios` -- fail if a Gherkin scenario exists but
  nothing binds it. Gating, because that is the one failure mode that
  would make `adr/ADR-007-executable-acceptance-criteria.md` worthless:
  pytest does not error, skip, or warn for a `.feature` file no module
  runs. It silently never runs, while reading exactly like a criterion
  that passes.
- `make check-stages` -- fail if a Stage in `docs/planning/roadmap.md`
  is missing part of the shape a well-defined stage has, at the point in
  its lifecycle each section becomes due: its Goal, the Capability Level
  it **Serves**, its **Use cases**, a Golden Demo, its Completion
  Criteria, a discharge map, a status section. Gating, and part of
  `make ci`. The shape is declared in `docs/planning/stage-shape.yaml`
  and explained in `docs/planning/stage-specification.md`, which are
  gated against each other -- a section declared in the first that the
  second never explains fails the build. **Exists because Stage 7
  reached its exit audit with no completion criteria at all and nothing
  noticed**: `docs/practices.md`'s "A stage gets completion criteria
  before its first task" had been a rule enforced by memory since
  2026-08-21, and memory had already failed once. It deliberately does
  not judge whether a criterion is any *good* -- that is not a
  structural fact, and a gate needing judgement trains people to route
  around it (`tools/validators/CLAUDE.md`).
- `make check-documents` -- fail if a document under `docs/planning/`,
  `docs/architecture/` or `docs/implementation/` does not declare, in
  its own first lines, what keeps it honest: `generated`, `gated`, or
  `stage-boundary` re-read. Gating, and part of `make ci`. It also
  prints the list of documents nothing checks mechanically, which is the
  reading list an exit audit needs -- derived from the documents' own
  declarations every run rather than restated anywhere, so it cannot go
  stale. **It also checks update obligations**: a document declaring
  `Updated-by: TASK-NNN -- <what>` must name a task that exists, whose
  own roadmap entry names the document back, and which is **not already
  Done** -- an obligation on a finished task is overdue by definition,
  and that is the case nothing could catch before (`sequences.md` asked
  to be updated when TASK-030 landed, then described a dead seam for six
  days). See `docs/documentation-guidelines.md` for what each mechanism
  means and why they are not equally strong.
- `make check-dates` -- fail if any tracked file records a date later
  than today. Gating, and part of `make ci`. **Exists because 23 tracked
  files -- this one included -- dated 2026-09-04's work as the day
  after**,
  written across two consecutive sessions with `make ci` green
  throughout, and found only because somebody compared a document
  against `git log`. This repository dates almost everything it records,
  and a wrong date corrupts the record in the one dimension nothing else
  can reconstruct. It gates despite "is this date right?" being an
  obvious judgement, because it does not ask that: only whether a date
  is in the future, which is a fact about the calendar. To name a
  genuinely planned point, write it as prose without the ISO form
  ("targeting December 2026") -- the check matches only `YYYY-MM-DD`,
  which this repository uses exclusively for things that have already
  happened.
- `make check-duplicate-blocks` -- fail if a tracked Markdown file
  contains the same large (12-line) block of prose twice, verbatim.
  Added 2026-09-08 (failure-mode audit), for the structural shape a
  botched `sed`/index-arithmetic edit leaves behind when it duplicates a
  section instead of moving it -- see
  `tools/validators/check_duplicate_blocks.py`'s own module docstring.
- `make check-claims` -- report documentation claiming some file or
  directory is empty, unwritten, or a stub when it actually has content
  (`docs/practices.md`). **Advisory and deliberately outside `make ci`**:
  it exits 0 even with findings, because telling a real drift from a
  document legitimately quoting the rule needs judgement. Run it as part
  of the end-of-session consistency review, not on every commit.
- `make status-report` -- regenerate `docs/planning/status.md` (a
  visual project status report: task/stage tables plus a Mermaid chart,
  read out of `docs/planning/roadmap.md`'s own status prose rather than
  a second status field anywhere) and an HTML dashboard under `build/`
  (gitignored, not committed). Refuses to write either file if the
  roadmap's claimed counts (a stage's criteria total, the CLAUDE.md
  count, the test count, the Gherkin scenario count) disagree with the
  live repository -- see `tools/generators/generate_status_report.py`.
- `make check-status` -- fail if `docs/planning/status.md` is stale, or
  if that drift check finds a disagreement. Added 2026-08-26, part of
  `make ci`.
- `make config-template` -- regenerate
  `docs/implementation/config-template.yaml`: every `PyFlowConfig` field
  from `src/pyflow/configuration/schema.py`, with a comment above each
  one stating what counts as a valid value and what does not.
  `pyflow generate-config` (TASK-039) already produces a loadable
  scaffold from the same schema, but `PyYAML`'s `safe_dump` cannot emit
  comments, so it carries no explanation -- this generator is that
  explanation, kept next to its own source of truth (its
  `FIELD_COMMENTS`/`SECTION_COMMENTS`) instead of hand-typed once into a
  committed file and left to drift, the same restated-fact failure mode
  this section's other generators exist to close. Added 2026-08-28 at a
  user's direct request, with the explicit condition that it stay
  current as the schema evolves -- see
  `src/pyflow/configuration/CLAUDE.md` for the rule that keeps it so.
- `make check-config-template` -- fail if the committed template is
  stale relative to the live schema or this generator's own comments.
  Part of `make ci`. `tests/unit/test_generate_config_template.py`'s own
  `test_every_live_config_field_has_a_comment` is the narrower,
  always-on companion: it fails a plain `make test` the moment a field
  is added to `schema.py` with no matching comment, not only at
  `make ci` time.
- `make ci` -- `lint typecheck test check-docs check-docs-index
  check-graph check-dependency-tree check-inventory check-manifest
  check-references check-scenarios check-stages check-documents
  check-status check-config-template check-dates check-duplicate-blocks
  check-benchmark-report`
  together (this list
  itself went stale by two targets, `check-references` and
  `check-scenarios`, before one correction, by a third,
  `check-benchmark-report`, added 2026-09-06 in the same change that
  added the target, and by a fourth, `check-duplicate-blocks`, added
  2026-09-08 in the same change that added it too -- restated facts
  drift even in the document that warns about restated facts, and
  keeps proving it every time a target is added here); this is what CI
  actually runs (`.github/workflows/ci.yml`), so it is also the one
  command that verifies a change is ready before committing. **For
  documentation it verifies structure, not content**
  (stated 2026-08-18): `check-docs` checks that relative links resolve,
  `check-docs-index` that the generated index matches the doc tree, and
  the `pre-commit` hooks cover whitespace, YAML syntax, spelling
  (`codespell`) and line endings (`mixed-line-ending`, which catches the
  stray control characters a mangled escape leaves behind). Beyond
  spelling, nothing in the chain reads the *meaning* of a Markdown file.
  A wrong
  equation, an inverted sign, a citation whose target does not support
  it, or a status claim that went stale weeks ago all pass `make ci`
  cleanly. The one exception, added 2026-08-21, is
  `check-graph`: relationships expressed as graph edges *are* checked
  for meaning, in the narrow sense that a dangling edge or a
  wrongly-typed one fails. That is precisely why
  `adr/ADR-006-knowledge-graph-scope.md` moved the relationships out of
  prose -- but it covers relationships between entities, nothing else,
  and no amount of it makes a wrong equation detectable. Every error the
  2026-08-18 documentation review found had
  been passing `make ci` for days, and a mangled LaTeX escape introduced during
  that review passed it too. **A second, narrower exception was added
  2026-08-26: `check-status` reads a handful of specific counts back out
  of `docs/planning/roadmap.md`'s prose** (a stage's claimed criteria
  total, the CLAUDE.md count, the test count, the Gherkin scenario
  count) **and fails if they disagree with the live repository** -- "a
  status claim that went stale weeks ago" is no longer quite true for
  those particular counts, which is exactly what the sentence above
  used to say `make ci` could never catch. It found two: the roadmap's
  own "tests at N% as of DATE" paragraph was already off by 136 real
  tests and 5 real Gherkin scenarios the first time this ran, fixed in
  the same change that added the check (`docs/planning/roadmap.md`,
  just above Stage 1). It is still narrow -- a count is a fact, not a
  reading, and everything genuinely judgement-shaped (whether a
  criterion is really *met*, whether an equation is right) is exactly as
  uncaught as before. Run it always; for prose in general, still treat
  `make ci` as a floor rather than a verification. The Blast Radius rule
  and the end-of-session consistency review (`docs/practices.md`) are
  what actually catch content errors, and both need a person or an
  agent reading.
- `make graph` -- render the knowledge graph
  (`planning/data/*.yaml`) as a browsable page under `build/`
  (gitignored, not committed). Every entity, and every edge in **both
  directions** -- an entity's YAML lists what it points at, and nothing
  anywhere lists what points back, which is the direction a reader
  asking "what depends on this?" needs. **Deliberately not in `make ci`
  and with no `--check` mode**, unlike every other generator here: it
  commits nothing, so there is no committed file to be stale against,
  and `adr/ADR-006-knowledge-graph-scope.md` rule 3's bar for generating
  a *document* does not apply to something that duplicates nothing.
  Added 2026-09-04, after the honest answer to "how do I view the
  graph?" turned out to be that you read the YAML: 102 entities and 257
  edges existed, of which 17 had any rendered form. Rendering it found
  the 33 untitled task headings within the hour.
- `make demo` -- run `python -m pyflow run`, the interactive engine
  entry point.
- `make benchmark` -- time a real `bootstrap()` demo run end to end,
  headlessly, a few repeats, reporting the minimum across them (less
  sensitive to one contaminated repeat than a mean would be), for the
  benchmark suite (`DEFAULT_CONFIGS`, override with `--config`). Added
  2026-09-06, at the end of a seven-fix vectorization arc
  (`docs/planning/roadmap.md` TASK-022/026/040/024/023/027 x2) whose
  every measured before/after number up to that point came from an ad
  hoc, hand-typed timing script rewritten from scratch each time -- one
  run was contaminated by a concurrent `make ci` and had to be caught
  and re-measured by hand. Only times the public `bootstrap()` API, not
  an isolated internal call: internals reshape with every fix like the
  seven above, `bootstrap()`'s own shape does not. **Not in `make ci`
  and no `--check` mode**, the same reasoning `make graph` above
  already gives -- a performance number is not a structural fact to
  gate on, and there is no committed file to compare against. See
  `tools/benchmarks/benchmark_demos.py`'s own docstring. Prints only --
  see `make record-benchmarks` below for the one that persists a result.
- `make benchmark-report` -- regenerate
  `docs/planning/benchmark-history.md` from
  `tools/benchmarks/benchmark_history.jsonl`. `make check-benchmark-report`
  fails if the committed copy is stale; part of `make ci`, since *that*
  is a structural fact (does the rendering match its committed source)
  even though the measurements the source holds are not. See
  `tools/generators/generate_benchmark_report.py`'s own docstring.
- `make record-benchmarks` -- run the full benchmark suite with
  `--record` (appends one entry per config to
  `tools/benchmarks/benchmark_history.jsonl`: git commit, `pyflow`
  version, hostname, timestamp, and the same phase-split statistics
  `--phases` prints) and regenerate the report in the same step. Added
  2026-09-06, at a user's direct request for a permanent, growing record
  rather than numbers that live only in a chat transcript or a
  hand-written `CLAUDE.md` paragraph, with two standing obligations that
  go with it (`tools/benchmarks/CLAUDE.md`): run this for any new
  benchmark config the day it's added, and at every version bump.
  **Deliberately never run automatically** -- a recorded number is only
  meaningful next to *what machine* produced it
  (`benchmark-history.md`'s own `hostname` column exists because of
  this), and CI's shared, variable-spec runners would silently pollute
  that record with numbers nothing else in it is comparable to. This is
  a by-hand action on one person's own machine, the same reasoning
  `make benchmark`/`make graph` already establish for why a performance
  number itself is never a `make ci` gate.
- `make clean` -- remove what `make install` created; states on its own
  output what it deliberately leaves alone (the `uv` binary, the shared
  interpreter, `uv`'s package cache) rather than restated here.
- `make preflight` -- a fast local pre-commit gate, added 2026-09-08:
  regenerates `docs/index.md` and `docs/repository-inventory.md`, then
  runs the link checker, the two cheapest structural-consistency checks
  (`check-manifest`, `check-references`), lint, typecheck, and the test
  suite, in that order, stopping at the first failure. Unlike `make ci`
  it regenerates before checking, so a merely-stale generated doc heals
  itself instead of failing outright. Deliberately narrower than `make
  ci` -- it skips `check-graph`, `check-scenarios`, `check-stages`,
  `check-documents`, `check-status`, `check-config-template`,
  `check-dates` and `check-benchmark-report`, none of which are cheap
  enough to justify running on every commit -- so a green `make
  preflight` is a reason to commit, not a reason to skip `make ci`
  before merge. See the Branch Discipline section above for when it's
  required.

Full detail, including what each target's acceptance criteria are and
why the project settled on `uv`+`make`: `README.md`'s Quick Start
section and `docs/planning/backlog.md` A1a/A1b/B2/B3.

---

# Tooling Gotchas

Environment-specific failure modes worth knowing before they cost a
retry cycle. Neither of these is a PyFlow behaviour -- both are the
local development environment fighting back -- but both have cost real
time more than once, which is the bar the rest of this file uses for
writing something down.

## Formatter Hook Interaction

The repository's `PostToolUse` hook (`.claude/hooks/post_edit_format.py`)
runs `ruff --fix`/`ruff format` on every file an Edit/Write call
touches, and `ruff --fix` removes an import it believes is unused. Add a
new import and its first usage in the *same* edit, never the import
alone -- an import added ahead of the code that uses it reads as unused
to the hook and gets silently stripped before the follow-up edit lands.
After any edit that touches imports, re-read the file to confirm the
import survived before running tests against it.

## Shell Usage (Git Bash)

Do not use heredocs for multi-line file content or commit messages on
this platform -- Git Bash's line-ending handling has mangled heredoc
writes into CRLF-corrupted or duplicated content before. Use the Write
tool for file content, and `git commit -F <file>` (a file written by the
Write tool) for a long commit message instead of `git commit -m` with an
inline heredoc. Never reorder sections of a file with `sed` or index
arithmetic -- a botched reorder has duplicated thousands of lines of a
planning document in a single command before; use targeted `Edit` calls
instead.

Added 2026-09-08, maintainer's instruction, after both failure modes had
each recurred across several sessions.

---

# Documentation

Documentation is treated as part of the implementation.

Documentation should evolve alongside code.

Generated documentation must never be edited manually.

Follow `docs/documentation-guidelines.md`.

## Documentation Blast Radius

Any change to behaviour, a CLI flag, or help text propagates in the same
commit to every place that restates it: `README.md`, the relevant
handbook or manifest entry, the roadmap/backlog status line, and every
`CLAUDE.md` that names the thing being changed. This is the Blast Radius
rule (above) applied specifically to documentation, because that is
where it has been missed most often -- run `make check-manifest`,
`make check-references` and `make check-docs` before committing (also
folded into `make preflight`, above), not only at full `make ci` time.

Never state a relative timeframe ("months ago", "recently", "a while
back"). Use a commit date, an explicit `YYYY-MM-DD`, or omit the claim
-- `git log` and a PR's actual merge time are the source of truth; a
session's own sense of elapsed time is not, and has been wrong before.

Added 2026-09-08, maintainer's instruction.

---

# Engineering Principles

Follow the principles defined in:

`docs/engineering-principles.md`

---

# Architectural Decisions

Significant architectural decisions should be recorded as ADRs.

Do not silently change established architecture.

---

# Validation

If you believe the repository violates one of these principles:

- report the issue
- explain why
- propose a solution
- do not silently ignore it

---

# Local Instructions

Always consult any more specific `CLAUDE.md` files in subdirectories before making changes.

Local instructions take precedence where they extend these rules.

When unsure, prefer improving the project's understanding over increasing the project's complexity.
