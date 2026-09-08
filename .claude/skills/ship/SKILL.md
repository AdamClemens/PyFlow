---
name: ship
description: Branch, implement TDD-first, propagate documentation, run the local gate, open a PR, watch CI, and merge -- the standard PyFlow delivery loop from root CLAUDE.md.
---

# Ship

This skill is a checklist, not new policy -- every step below restates a
rule that already lives in root `CLAUDE.md` or `docs/practices.md`. It
exists so the same sequence doesn't have to be re-described by hand each
time. If this file and one of those disagree, the other document wins;
fix this file in the same change.

1. **Branch before the first edit** (CLAUDE.md, Branch Discipline).
   `git checkout main && git pull`, then create
   `<kind>/<short-hyphenated-subject>` (`docs/practices.md`): `feat/` for
   a roadmap task, `fix/` for a defect, `docs/` for documentation/
   planning/process only. One branch per task -- don't fold an unrelated
   second task onto a branch already in flight.

2. **Write the failing test first, then implement** (root CLAUDE.md,
   Acceptance Criteria section; `docs/practices.md`'s TDD examples
   throughout the roadmap). The test must assert intent -- the physical
   or behavioural meaning a reader would check -- not an implementation
   detail that would still pass under a wrong implementation.

3. **Implement until it's green**, re-reading any file where an import
   was added before running tests against it -- the post-edit format
   hook strips an import that has no usage yet in the same edit
   (CLAUDE.md, Tooling Gotchas / Formatter Hook Interaction).

4. **Propagate the Blast Radius in the same change** (CLAUDE.md, Blast
   Radius; Documentation Blast Radius). Grep for the name of whatever
   changed and update every restatement: `README.md`, the relevant
   handbook/manifest entry, the roadmap/backlog status line, the
   `CHANGELOG`/`docs/CHANGELOG-DESIGN.md` where a decision was made, and
   every `CLAUDE.md` that names the thing. If something in the radius
   can't be updated now, say so explicitly in the PR description rather
   than leaving an unrecorded gap.

5. **Before calling a user-facing feature done, run it** (CLAUDE.md,
   Feature Verification Before Reporting Done). The exact command a user
   would run, not the test suite standing in for it -- `pyflow run`,
   `make graph`, whatever the feature's own entry point is. Confirm any
   new CLI flag actually appears in `--help`. Then re-read the diff as a
   hostile auditor and list anything overstated, defaulted off, or
   unreachable.

6. **Run `make preflight`** (CLAUDE.md, Branch Discipline / Development
   Commands) before the first commit on the branch, and again before
   opening the PR. It regenerates the generated docs, then runs the link
   checker, the fast structural-consistency checks, lint, typecheck, and
   the test suite, failing at the first error.

7. **Commit.** No heredocs for the message -- write it with the Write
   tool to a scratch file and use `git commit -F <file>` (CLAUDE.md,
   Tooling Gotchas / Shell Usage). State what changed and why, not what
   the diff already shows.

8. **Run `make ci` in full before merge** (CLAUDE.md, Merge Gate
   criterion 1) -- `make preflight` is not a substitute. Push, open the
   PR (`gh pr create`), and watch the real CI run on both platforms
   (`gh pr checks --watch`) rather than assuming local green transfers.

9. **Before merging, re-check Merge Gate criteria 2-4**: every
   restatement of every changed fact is updated in this branch, every
   acceptance criterion is checked by something that would fail if the
   intent were violated, and anything left unverified is said so
   explicitly rather than implied by silence.

10. **Merge, delete the branch, return to `main`** before starting the
    next task (CLAUDE.md, Branch Discipline).

**Exception**: a trivial single-file edit to a `CLAUDE.md` or other
process-rule file may skip straight to a direct commit on `main`, but
only when the user explicitly says so in that turn (CLAUDE.md, Branch
Discipline). Everything else follows the full sequence above.
