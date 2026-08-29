# CLAUDE

Scripts that generate a file from the current state of the repository,
rather than expressing knowledge by being hand-written themselves.

**`generate_docs_index.py`, added 2026-08-17.** Walks the documentation
directories (`docs/`, `docs/planning/`, `docs/architecture/`,
`docs/handbook/{numerical-methods,physics}/`, `docs/implementation/`,
`docs/references/`, `docs/tutorials/`, `adr/`) and writes `docs/index.md`:
a page listing every non-empty doc in each directory, linked by its own
first `#` heading. This is the comprehensive, generated map; `README.md`'s
"Where to Start" section stays the hand-written curated first-read path,
and the two are cross-linked rather than merged (docs/documentation-
guidelines.md: single primary purpose per doc).

Run via `make docs` to (re)write `docs/index.md`, or `make check-docs-index`
(also part of `make ci`) to fail if the committed file is stale relative
to the current doc tree. Regenerate and commit after adding, moving,
deleting, or re-titling (changing the first heading of) any file in the
directories above -- this is the mechanical half of the Blast Radius
rule's "what tracks this in an inventory" check (docs/practices.md) for
documentation pages specifically, same relationship `check_docs.py`
(tools/validators/CLAUDE.md) has to broken links.

`docs/index.md` itself carries a "do not edit by hand" banner per root
CLAUDE.md's "Generated documentation must never be edited manually" rule.
If a page needs a better title in the index, fix that page's own H1
heading and regenerate -- don't edit the index directly, since the next
regeneration would silently discard the edit.

Deliberately excluded from the scan: `prompts/` (agent-briefing material,
not documentation a project reader would navigate to -- see docs/
repository-manifest.md's separate `prompts/` section) and `planning/`
(machine-readable knowledge-graph data, not prose). Add a directory to
`SECTIONS` in the script only when it holds actual human-readable
documentation pages, not just because it contains `.md` files.

**Sort within a section is an explicit `key=lambda p: p.name.lower()`,
not bare `Path` comparison -- found the hard way, 2026-08-19, on the
first real Ubuntu CI run.** `Path.__lt__` is case-insensitive on
Windows but case-sensitive on POSIX; `docs/handbook/physics/README.md`
is the one file in any scanned section that starts with an uppercase
letter, so every locally-generated (Windows) `docs/index.md` had put it
last, alongside where it alphabetises case-insensitively, while Ubuntu's
case-sensitive sort put it first instead. `check-docs-index` did exactly
its job -- caught its own generator being non-deterministic across
platforms, something no amount of local (Windows-only) verification
could have found before a real Linux run existed. If a future section
ever needs a different ordering, change the `key=`, not back to bare
comparison.

**`generate_dependency_tree.py`** (added 2026-08-21) renders
`docs/planning/dependency-tree.md` from `planning/data/components.yaml`.
Same shape as `generate_docs_index.py` -- a `--check` mode wired into
`make ci`, `newline="\n"` so output is byte-identical across platforms,
and output that must never be hand-edited -- but a different trigger: it
reads `planning/`, not the doc tree, so it regenerates when the graph
changes, not when a page is added or re-titled. That is why `make docs`
and `make dependency-tree` are separate targets rather than one.

**`generate_status_report.py`** (added 2026-08-26) renders
`docs/planning/status.md` (task/stage tables, a Mermaid chart) and an
HTML dashboard under `build/` (gitignored, not committed, not
`--check`-gated) from `docs/planning/roadmap.md`'s own status prose --
`## TASK-NNN` headings, `**Status: Done, DATE.**` markers, the Stage 0
status table, each stage's Completion Criteria list and status line.
Same shape as the other three generators otherwise: `--check` wired into
`make ci` as `check-status`, `newline="\n"`, output that must never be
hand-edited.

**It is also a validator, which the other three generators in this file
are not.** Before rendering anything, it cross-checks a small set of
structural facts the roadmap claims -- a stage's claimed criteria total
against how many it actually lists, the CLAUDE.md count, the test count
(`pytest --collect-only`), the Gherkin scenario count -- against the
live repository, and refuses to render *at all* while any disagree,
regardless of `--check`. Ordinary generators fail only when their
*output* is stale relative to their *input*; this one additionally
refuses when the input itself has drifted from reality, because
rendering a status page from a source that disagrees with the repository
would just launder the staleness into a nicer format. It found real
drift the first time it ran: `docs/planning/roadmap.md`'s own test/
scenario-count paragraph was off by 136 tests and 5 scenarios, fixed in
the same change that added the check.

**It gained one non-roadmap check 2026-08-29 (Stage 5 exit audit):
`README.md`'s own "Current Phase" section.** The drift check now fails
when the stage README names there is not the roadmap's first stage not
marked complete (`_frontier_stage`). That section had gone a full stage
stale twice -- the Stage 2 audit found it claiming the project "is
beginning Stage 2"; the Stage 5 audit found it claiming Stage 5 was "not
yet started" on the day Stage 5 closed -- and both passed `make ci`,
because nothing read the sentence. **It adds no second source of
truth**: the roadmap still decides which stage is current, and README is
checked against it, never consulted for it. This is the same structural-
fact discipline as every other rule here (a stage number parsed out of a
named section, compared to a stage number parsed out of the roadmap), not
a judgement about whether README's prose is otherwise accurate. It lives
here rather than in a new `tools/validators/` script for the reason the
module docstring gives: the fact it needs -- which stage is current --
is already computed here, and a second script would have to recompute
it.

**Deliberately does not verify everything the roadmap claims.** Which
criteria within a stage are *met* (as opposed to how many total exist)
is exactly the kind of per-item reading `check_claims.py`
(`tools/validators/CLAUDE.md`) stays advisory over -- the verdict tables
backing it are shaped differently stage to stage, with no structural
invariant to check. Coverage percentage is skipped too, on purpose:
`pyproject.toml`'s `[tool.coverage.report]` has no fail-under threshold
yet, so gating on a coverage number would be gating on a figure the
project has already decided isn't meaningful. Both are rendered as
stated, neither is cross-checked -- see the module's own docstring for
the full reasoning, which is the same gate-vs-advisory judgement
`tools/validators/CLAUDE.md` asks every new check to make explicitly.

Why it exists is worth keeping: `dependency-tree.md` was hand-maintained
and disagreed with `docs/architecture/engine.md` about what the engine's
subsystems are. Both documents recorded the divergence and neither could
fix it, because fixing it by editing one is just picking a winner by
hand. Generating one from the other makes the agreement structural.

**Two things it does that the docs-index generator does not**, both
worth copying in any future generator here:

- **Sorts every level before emitting it.** Without that, output depends
  on dictionary ordering and `--check` fails at random.
- **Raises on a cyclic graph rather than emitting a partial view.**
  `make check-graph` catches cycles first and with a better message, so
  this is a backstop -- but a generator that silently drops every
  component caught in a cycle produces a document that looks complete
  and is not, which is the worst available outcome.

**`generate_repository_inventory.py`** (added 2026-08-21) writes
`docs/repository-inventory.md`: every tracked file, grouped by
directory, with empty files marked. `make inventory` /
`make check-inventory`.

**It reads `git ls-files`, not the disk**, and that is the load-bearing
choice. A directory walk describes the machine it runs on -- `.venv/`,
tool caches, untracked scratch files -- so two clones of the same commit
could produce different output and `--check` would fail for reasons
having nothing to do with the repository. Copy this if any future
generator needs to know "what is in the repository".

**It reports exactly one status: empty.** The manifest's own legend
defines "Not Started" as "file does not exist, or exists and is empty",
which is the only status derivable without a reader; Draft versus
Complete is judged against a Definition of Done and stays in the
hand-written manifest. Resist widening this -- a generator that guesses
at completeness produces confident wrong statuses, which is worse than
the stale ones it replaced.

**What it deliberately cannot fix**: test counts and coverage. Those
come from running the suite, not from listing files, and the "42 tests,
87% coverage" drift that motivated the split is therefore *not* solved
by this script. Those claims stay prose, now with a date attached, and
step 11 of the end-of-session review (`docs/practices.md`) is what
covers them.

**`generate_config_template.py`** (added 2026-08-28, at a user's direct
request) renders `docs/implementation/config-template.yaml`: every
`PyFlowConfig` field (`src/pyflow/configuration/schema.py`), with a
comment above each one stating what counts as a valid value and what
does not. Same shape as the other generators here -- a `--check` mode
wired into `make ci` as `check-config-template`, `newline="\n"`, output
that must never be hand-edited. Different trigger from the other three:
it regenerates when `schema.py`'s fields, defaults, or valid ranges
change, not when a doc page is added or the component graph changes.

**Why a generator rather than a hand-written example file.**
`pyflow generate-config` (TASK-039,
`src/pyflow/configuration/generator.py`) already turns `PyFlowConfig()`
into loadable YAML, straight from `dataclasses.asdict()` -- but
`PyYAML`'s `safe_dump` cannot emit comments, so that output carries no
explanation of *why* a value is accepted or rejected, only what the
default happens to be. Hand-writing that explanation directly into a
committed YAML file would relocate exactly the restated-fact problem
`generate_dependency_tree.py`/`generate_status_report.py` above were
each built to close, one field at a time instead of one document at a
time: the explanation would drift the moment `schema.py`'s `validate()`
changed and nobody remembered the YAML file existed. This script is that
fix applied to configuration documentation -- `FIELD_COMMENTS`/
`SECTION_COMMENTS` are the one place a field's valid/invalid explanation
is written, kept in the generator next to the schema it describes.

**It is also a structural completeness check, the same shape
`generate_status_report.py`'s drift check is, but narrower.**
`missing_comment_paths()` walks the live `PyFlowConfig` dataclass tree
(via `dataclasses.fields()`, `typing.get_type_hints()` to resolve
`from __future__ import annotations` string annotations) and returns
every leaf field with no entry in `FIELD_COMMENTS`, and every top-level
section with none in `SECTION_COMMENTS` -- `render()` refuses to
produce output at all while either list is non-empty, the same
refuse-rather-than-launder-staleness posture `generate_status_report.py`
takes. **Deliberately narrower than that check**: it verifies a comment
*exists* for a field, not that its *wording* is still an accurate
description of that field's real constraint -- the same
judgement-versus-structure line `check_claims.py`
(`tools/validators/CLAUDE.md`) draws, and for the same reason: telling a
stale explanation from a correct one needs a reader, and a check that
needs a reader cannot gate. `docs/practices.md`'s Blast Radius rule
covers that half instead, and `src/pyflow/configuration/CLAUDE.md`
states the concrete obligation ("update `FIELD_COMMENTS` in the same
change that changes the field it describes").

**Every value shown is `PyFlowConfig()`'s own default, never a
hand-picked "more illustrative" example.** A value that isn't the
schema's own default would be a second place that default could drift
from -- the same reasoning `generate_config_yaml` (TASK-039) already
uses for the plain scaffold, applied here to the annotated one. The four
boundary faces (`numerics.boundary_conditions.north/south/east/west`)
share one `BoundaryFaceConfig` shape and one comment set per field
(`FIELD_COMMENTS`'s `<face>` placeholder keys); the rendered file
explains each field's rules once, under `north`, and shows the other
three faces' values with no repeated prose -- verified directly by
`tests/unit/test_generate_config_template.py`'s own
`test_boundary_face_comments_are_explained_once_not_four_times`, after
an earlier draft of the renderer repeated the full explanation on all
four faces despite its own banner comment claiming otherwise.
