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
