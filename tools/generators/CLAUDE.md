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
