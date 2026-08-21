# Repository Architecture

Why PyFlow's top-level directories are laid out the way they are, and
what job each one has -- a map of the repository's *structure and
rationale*, read once to understand the shape of the codebase.

**Distinct from `docs/repository-manifest.md`, which this document does
not duplicate or replace.** The manifest tracks per-file *completion
status* (which files exist, whether each is empty/draft/complete) --
an inventory, updated constantly as files change state. This document
explains *why the directories exist and what belongs in each* -- a
structural map, which changes only when the structure itself changes.
Consult the manifest for "is X written yet?"; consult this document for
"where would X go, and why is it there rather than somewhere else?" Each
directory's own `CLAUDE.md` remains the authoritative, most detailed
source for that directory specifically -- this document is the map
between them, not a replacement for any of them.

---

## Top-Level Directories

```text
src/pyflow/     the installable package (src-layout)
tests/          automated tests, split by what they exercise
docs/           documentation -- planning, architecture, handbook,
                implementation, references
examples/       demo/tutorial/experiment scripts, not an importable
                package
adr/            Architecture Decision Records
prompts/        prompt material for briefing document-generation agents
tools/          standalone scripts supporting the repo, outside the
                pyflow package
assets/         non-code assets (colour maps only -- icons/shaders/
                textures retired 2026-08-19, no documented purpose)
planning/       machine-readable knowledge graph (schema + data)
.github/        GitHub-specific configuration (CI workflows)
.claude/        Claude Code configuration (settings + hooks), tracked
```

## Why src-layout

`src/pyflow/` rather than a bare `pyflow/` at the repository root --
the installable package is deliberately not importable by accident from
the repository root itself, which is what a flat layout allows and
src-layout prevents (a common source of "works on my machine because I'm
in the wrong directory" bugs, where tests import the working-tree copy
instead of the installed package). See `src/CLAUDE.md`.

## Why `examples/`, Not `demos/`

The roadmap originally specified `demos/`. Renamed during Stage 0
(`docs/planning/backlog.md`, 2026-08-15 decision) because the directory
holds more than demos -- `golden-demos/`, `tutorials/`, and
`experiments/` all live under it, and `examples/` is the accurate
umbrella term for all three, not just the first. `golden-demos/` itself
holds configuration files, not Python scripts, because a golden demo
must run through the public `pyflow run --config <file>` CLI rather than
demo-specific code (`docs/implementation/golden-demos.md`'s public-API
rule) -- see `examples/CLAUDE.md`.

## Why `tests/` Is Split Four Ways

`unit/`, `integration/`, `golden/`, `performance/` -- split by what each
kind of test actually exercises (isolated logic; a real process/I/O
boundary; a golden demo's regression behaviour; performance rather than
correctness), not by which part of the codebase they cover. This
distinction is what let `tests/integration/test_import_order.py` (a
regression test for the circular-import bug D4 found) live in
`integration/` rather than `unit/` -- it needs a fresh subprocess per
import, a real process boundary, even though the code under test is a
single-process import statement. See `tests/CLAUDE.md`.

## Why ADRs Live Outside `docs/`

`adr/` sits at the repository root, a sibling of `docs/` rather than a
subdirectory of it -- Architecture Decision Records are peers to code and
documentation both (they record decisions that constrain both), not
subordinate to the documentation tree specifically. `adr/README.md`
carries the full convention (naming, lifecycle, when to write one); this
document only explains the placement.

## Why `prompts/` Exists as Its Own Directory

Holds durable, project-wide context (`prompts/global/`) and
per-artifact-kind guidance (`prompts/features/`) meant to brief a
document-generation agent that has no memory of any prior session --
distinct from `docs/`, which is the documentation those agents produce,
and from `CLAUDE.md` files, which brief an agent working in a specific
directory rather than generating a specific kind of artifact. See
`prompts/CLAUDE.md`.

## Why `tools/`, Not Scripts Scattered by Convenience

Standalone scripts supporting the repository -- generating derived
documentation (`generators/`), checking repository consistency
(`validators/`) -- that are not part of the installable `pyflow`
package and should not be importable as if they were. Kept to exactly
the subdirectories that have earned real content: `planner/` and
`scripts/` existed here too until 2026-08-17, when both were retired for
having sat empty since the repository's first commit with nothing
anywhere stating what either was for (`docs/planning/backlog.md` E10) --
recreate either only once something concrete needs to live there. See
`tools/CLAUDE.md`.

## Why `planning/` at the Root Is Not `docs/planning/`

Two directories with similar names, deliberately different jobs: root
`planning/` is the machine-readable knowledge graph (`model/` schema,
`data/` content) that tooling reads; `docs/planning/` is the actual
planning *documentation* (the roadmap, the backlog, this document's own
home) a person or agent reads directly. See `planning/CLAUDE.md`.

The split is now load-bearing rather than merely tidy, and the rule
governing it is `adr/ADR-006-knowledge-graph-scope.md`: **the graph
holds entities and the relationships between them, `docs/planning/`
holds reasoning, and reasoning is never generated.** So a component's
dependencies live in `planning/data/components.yaml` and are validated
by `make check-graph`; *why* a layer exists lives in
`docs/architecture/engine.md` and is read by people.
`docs/planning/dependency-tree.md` is the one document generated across
the boundary so far (`make dependency-tree`).

This paragraph described both directories' `.yaml` files as "currently
empty by design" until 2026-08-21, which had been true since the
repository's first commit and stopped being true when the graph was
populated. Seven of the eleven now hold content; the remaining four are
empty with a stated trigger each in `planning/model/entities.yaml`.

## `.github/`

GitHub-specific configuration only -- currently just `workflows/ci.yml`.
No issue templates, PR templates, or `CODEOWNERS` exist yet, the same
deliberate deferral as `CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`/
`SECURITY.md` for a single-developer project
(`docs/planning/backlog.md`, Part II).

## `.claude/`

Claude Code's own configuration: `settings.json` and `hooks/`. It is
**tracked in git, not ignored**, which is the point worth recording --
the hook that runs after an edit is part of how the repository maintains
itself, so it belongs to the repository rather than to one contributor's
machine, in the same spirit as `.pre-commit-config.yaml`. Note the
distinction from `CLAUDE.md` files, which are instructions *to* an agent
working in a directory; `.claude/` is configuration of the *tool* the
agent runs inside.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E2b). Update this
document, not `docs/repository-manifest.md`, when a top-level
directory's *purpose* changes (added, removed, renamed, or its job
redefined) -- update the manifest instead when a *file within* one
changes completion status. The two documents drift apart exactly when
an edit meant for one lands in the other; keep the distinction in mind
before choosing where to write a change.

Reviewed 2026-08-18: `.claude/` was missing from the top-level directory
list and now has its own section. It is tracked in git and holds the
post-edit hook the repository runs on itself, so its absence from a
document whose whole job is "what is each top-level directory for" was a
real gap rather than a tidy omission.
