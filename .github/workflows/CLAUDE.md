# CLAUDE

One workflow, `ci.yml` (TASK-004, `docs/planning/roadmap.md`). Runs on
every push to `master` and every pull request, on a Linux + Windows
matrix (maintainer's call, 2026-08-16 -- development happens on Windows,
runners default to Linux, and that split is exactly where `make`
behaviour and headless rendering diverge, so only one platform proves
nothing about the other).

**Invokes `make ci`; does not restate its steps.** `make ci` (the
Makefile) chains `lint`, `typecheck`, `test` -- that's the single
authoritative sequence (P-011, `docs/practices.md`). If CI needs to run
something different from local verification, change the Makefile target,
not this file, so the two can't drift apart.

**Windows needs an explicit `make` install step.** `windows-latest`
doesn't ship GNU Make -- neither does Git for Windows, which is why the
local dev machine needed Chocolatey too (`docs/planning/backlog.md` A1b).
The workflow installs it the same way, conditionally, before `make
install` runs. Linux needs no equivalent step; `ubuntu-latest` ships Make
already.

Python version comes from `.python-version` (currently 3.14) via
`astral-sh/setup-uv`'s `python-version-file` input -- keep that in step
with the repository's Python version policy (`docs/practices.md`) rather
than pinning a version here directly, so there is one place that decides
the version and CI just reads it.

Branch name (`master`) tracks `docs/planning/backlog.md` F1, which is
still open. Update the `push.branches` filter here the moment that's
decided, if it changes.
