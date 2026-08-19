# CLAUDE

One workflow, `ci.yml` (TASK-004, `docs/planning/roadmap.md`). Runs on
every push to `main` and every pull request, on a Linux + Windows
matrix (maintainer's call, 2026-08-16 -- development happens on Windows,
runners default to Linux, and that split is exactly where `make`
behaviour and headless rendering diverge, so only one platform proves
nothing about the other).

**Invokes `make ci`; does not restate its steps.** The Makefile's `ci`
target is the single authoritative sequence (P-011, `docs/practices.md`).
If CI needs to run something different from local verification, change
the Makefile target, not this file, so the two can't drift apart.

Deliberately *not* listing that sequence here: this note used to say
`make ci` chains "`lint`, `typecheck`, `test`" and went stale on
2026-08-17 when `check-docs` and `check-docs-index` were added to it --
a restatement that contradicted the very target it called authoritative.
Read the Makefile for the current chain; the root `CLAUDE.md` carries a
description of each target for readers who need one.

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

Branch renamed `master` -> `main` 2026-08-19 (`docs/planning/backlog.md`
F1); `push.branches` above updated in the same change.

**Linux needs a software Vulkan driver, added 2026-08-16 (D3).**
`ubuntu-latest` has no GPU; once `tests/unit/test_rendering.py` started
creating a real `wgpu` device (even the offscreen backend needs one),
Linux CI needs LavaPipe to have anything to render with. Windows needs no
equivalent step -- it has a software D3D12 (WARP) adapter built into the
OS. The apt package set (`libegl1 libgl1 mesa-vulkan-drivers`) itself was
never wrong -- see below for what actually broke the first real run.

**First real run, 2026-08-19 (remote added same day).** Windows went
green in 2m23s including `choco install make` and all 64 tests. Linux
hung on the Vulkan-driver step, twice, across two attempts:

1. **First diagnosis, made without log access, wrong.** No permission to
   download the run's raw log (needs repo-admin auth), so the fix was a
   plausible guess from the symptom alone: `needrestart`'s interactive
   "which services should be restarted?" prompt, which `ubuntu-latest`
   images enable by default and which `apt-get install -y` does not
   suppress. Shipped `NEEDRESTART_MODE=a`/`DEBIAN_FRONTEND=noninteractive`
   -- harmless, kept as defence in depth, but the next run hung for
   *longer* (8+ minutes), proving it wasn't the actual cause.
2. **Real cause, found from the actual log** (maintainer pasted it
   directly, since I still couldn't download it): `apt-get update`
   itself was the slow step, not `install` -- stuck retrying
   `azure.archive.ubuntu.com` (GitHub's Azure-runner regional mirror,
   periodically flaky) four times before falling back to
   `archive.ubuntu.com` directly. A documented GitHub Actions gotcha,
   unrelated to this package set. Fixed by overwriting
   `/etc/apt/apt-mirrors.txt` (the mirror list Ubuntu 24.04's
   `mirror+file:` sources resolve through) with the direct archive URL
   before `apt-get update` runs, skipping the flaky mirror entirely
   rather than waiting out its retry/fallback cycle.

**The lesson, not just the fix:** a diagnosis made from symptoms and
general knowledge, without the actual log, is a hypothesis, not a
finding -- state it as one, and verify against a real subsequent run
before writing it up as settled. The first attempt here was reported
back to the maintainer as fixed before that verification happened, which
was premature; catch this by waiting for a real green run before closing
anything in `docs/planning/backlog.md` or `roadmap.md` on this account.
