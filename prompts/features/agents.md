# Agent (CLAUDE.md) Prompt Context

Per `docs/planning/knowledge-architecture.md` KA-043. Tells an agent how
to write or update a `CLAUDE.md` file -- the generated-prompt counterpart
to the root `CLAUDE.md`'s own "Maintaining CLAUDE.md Files" section, for
use once a prompt generator exists. Until then, this is the standard a
human or agent should already be writing `CLAUDE.md` files against by
hand.

Read alongside, not instead of:

- root `CLAUDE.md`'s "Maintaining CLAUDE.md Files" section -- the
  standing rule that these are living documents, updated incrementally
  as understanding accumulates, not one-time scaffolding.
- `docs/practices.md`'s Blast Radius section, "Specific instances of the
  rule" -- whenever a document is created or substantially filled in,
  its nearest `CLAUDE.md` must be updated in the same change.
- `docs/engineering-principles.md` -- what a `CLAUDE.md` should be
  compact enough to inherit from without restating.

---

## What a CLAUDE.md Is For

Compact, actionable guidance for an agent working in that directory --
not a duplicate of the documentation system. If a fact already has an
authoritative home elsewhere (`docs/engineering-principles.md`,
`docs/practices.md`, an ADR), point at it; don't copy it in.

## What to Include

- **Inherited instructions** -- a one-line acknowledgement that
  repository-level (and any intermediate) `CLAUDE.md` rules apply here
  too, without restating them.
- **Local scope** -- what this directory/package is *for*, in terms
  specific enough that a reader who has never seen it before understands
  its job in the architecture. Generic filler ("this directory contains
  project files") is never sufficient once anything specific is known.
- **Important commands/files** -- what a developer needs to build, test,
  or run something in this specific directory, if it differs from the
  project-wide commands already in the root `CLAUDE.md`.
- **Local validation** -- how to check that a change here is actually
  correct: a specific test file, a command, a manual verification step
  (see `src/pyflow/rendering/CLAUDE.md`'s `close_keys` entry for the
  pattern when something can't be automated).
- **Violations to report** -- conventions specific to this directory that
  an agent should flag rather than silently work around if it finds them
  broken.

## When to Write One

Write real content the moment something specific is known about the
directory -- don't wait for it to be "finished." A generic placeholder is
acceptable only until then, per the root `CLAUDE.md`. Prefer writing
against a real, concrete precedent already in the directory (an actual
test file, an actual module) over describing hypothetical future
content -- `docs/planning/backlog.md`'s E9 item followed this
consistently: each `CLAUDE.md` was filled in once its directory held
something real to write against, not speculatively ahead of it.

## What to Avoid

- Restating engineering principles, practices, or documentation
  guidelines instead of referencing them (`docs/engineering-principles.md`
  P-011: information should have a single authoritative source).
- Writing guidance that will drift the moment the directory's content
  changes -- prefer describing the *pattern* a future file should follow
  over restating specifics that will need updating every time (e.g. a
  test count, a file list) unless that specific inventory is the file's
  actual job.
- Leaving the generic placeholder text in place once real content exists
  to write against instead.

## Definition of Done

The file is compact, specific to its directory, and does not duplicate
what the documentation system already states elsewhere -- an agent
reading only this file and its parents should know how to work correctly
in this directory without reconstructing that from other documents.
