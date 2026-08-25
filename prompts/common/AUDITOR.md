# The Auditor

Reusable review stance, referenced by `TEMPLATE.md`'s Review Cycle
section and by `docs/practices.md` wherever a prompt or a session needs
a second pass distinct from the persona that produced the work under
review. Extracted 2026-08-24 from `docs/practices.md`'s End-of-session
consistency review, once the same stance was needed in a second place
(the per-task review cycle in `docs/practices.md`'s "Audit code before
calling it done") rather than restated -- per `docs/engineering-principles.md`
P-011, a fact gets one authoritative source.

This file owns the *stance* only. What to check is owned elsewhere --
`docs/practices.md`'s End-of-session consistency review checklist for a
session or a merge, the Definition of Done of whichever task prompt is
under review for a single task. Read this file alongside whichever of
those applies, not instead of it.

---

## The Stance

Adopt the stance of a reviewer who did not write the artifact under
review and is trying to find the one place it is wrong -- not the stance
that just finished it. For every claim the artifact makes (a test name,
a docstring, a status line, a "done"), ask **"what would make this
false?"**, not "does this look right?" Continuing in the mode that
produced the work tends to confirm it; the question that actually finds
a defect is adversarial by construction.

This is not a stylistic preference. `docs/practices.md`'s End-of-session
consistency review records why: the 2026-08-24 Stage 3 exit audit found
three real defects behind a green `make ci` (473 tests, 19 scenarios,
99% coverage) -- a `logger.info` call standing in for the assertion its
own criterion required, a null solver claiming `converged=True` on a
zero solution that four other documents already called an unconverged
no-op, and a registry with no duplicate-name guard for a failure mode
already named in `icds.md`. Each was invisible to the persona that had
just written it, on a single pass, with every test green.

## When to Use It

- **Code-writing tasks.** Any prompt instantiated from `TEMPLATE.md`
  whose Output includes source under `src/` or `tests/` runs its Review
  Cycle under this stance after the Definition of Done's own tests pass
  -- see `TEMPLATE.md`'s Review Cycle section for the loop itself. In a
  Claude Code session, the `/code-review` skill (medium or high effort;
  `--fix` to apply) is one concrete way to run a pass; the requirement
  is the stance and the repeat-until-clean loop, not that specific tool
  -- a human contributor without it applies the same stance by hand.
- **Exit audits and merge-readiness checks.** Work `docs/practices.md`'s
  End-of-session consistency review checklist under this stance, not as
  a formality to clear.
- **Anywhere else a prompt needs a reviewer distinct from its author.**
  Reference this file rather than re-deriving the stance inline --
  that's the entire reason it was extracted.

## What This Is Not

Not a second, separately-defined persona alongside this one -- there is
one auditor stance, described once, here; nothing else in this project
should restate it. Not a substitute for the checklist it's applied to --
this file owns the stance, `docs/practices.md` and each task's
Definition of Done own what to check. Not a blanket gate on every piece
of prose in the repository -- it applies where a Blast Radius rule, an
exit audit, or a code-writing task's Review Cycle already calls for a
consistency pass, not by default everywhere.
