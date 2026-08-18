# Releases

Per `docs/planning/backlog.md` E7. There is no KA entry for this
document -- the knowledge-architecture spec never specified one -- so
this file's content is set by that backlog item and by
`docs/glossary.md`'s existing "Release" definition, not by a KA content
requirement.

## Current State

PyFlow has made **no release**. It is at version 0.0.1
(`pyproject.toml`), and no release process -- what triggers one, how it
is versioned in practice, what gets published where -- is defined
anywhere in the repository.

This is a **deliberate deferral, not an oversight**, for the same reason
`docs/planning/backlog.md` Part II gives for deferring
`CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`/`SECURITY.md`: PyFlow is a
single-developer project with no external consumers yet, and a release
process exists to serve exactly the concerns (external consumers'
expectations of stability, a distribution channel, a support/versioning
contract) that do not yet apply.

## Why Not Now

`docs/glossary.md`'s "Release" entry already states the core reason
plainly: releases are "the least developed of the project's three
progression concepts" (alongside Stage and Capability Level), and the
project's actual working rhythm is Stage-based, not release-based --
`docs/engineering-principles.md` P-004 was deliberately reworded from
"every release after Release 0" to "every stage after Stage 0" on
2026-08-15 specifically because "release" was never the unit PyFlow
plans or works in. Defining a release process now, ahead of any reason
to actually cut one, would be exactly the kind of premature structure
`docs/engineering-principles.md` P-016 (prefer reversible decisions
until understanding justifies commitment) and P-018 (implement the
simplest valid version of each layer) both argue against.

## What Would Trigger Defining One

Not an open-ended "eventually" -- concrete conditions, so this section
is checkable rather than aspirational:

- **A first external consumer** -- anyone depending on PyFlow who isn't
  actively developing it needs a stable, versioned thing to depend on,
  which is exactly what a release process exists to provide. This is
  also `docs/practices.md`'s Python-version-policy trigger for moving
  from "periodic review" to "deliberate stability" -- the same event
  changes both policies for the same underlying reason.
- **Reaching the MVP** (`docs/implementation/mvp.md`) -- the first point
  at which PyFlow is a genuinely usable simulation someone outside active
  development might want to run, rather than an in-progress engine.
- **A maintainer decision to publish** -- independent of either
  condition above, the maintainer may simply decide a release is wanted
  (e.g. to mark a milestone) before either triggers.

When any of these happens, this document should be rewritten with an
actual process (versioning scheme, what artifact gets published, where,
and what "released" means for a Python package specifically -- most
likely PyPI, given the project's BSD-3-Clause licence and
scientific-Python-ecosystem alignment, `LICENSE`) -- not just its
trigger condition restated. Until then, this file's job is to make the
deferral explicit and checkable, per A3's requirement that no tracked
file stay empty.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E7). Update this
document, not just `docs/glossary.md`'s "Release" entry, the moment any
trigger condition above is met -- the glossary defines the term: this
document is where the actual process, once one exists, belongs.
