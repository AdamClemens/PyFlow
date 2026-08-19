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
hung indefinitely on the Vulkan-driver step -- not the package set, not
the rendering tests the previous version of this note predicted, but
`needrestart`'s interactive "which services should be restarted?"
prompt, which `ubuntu-latest` images enable by default and which
`apt-get install -y` does not suppress. With no TTY attached it blocks
until the job's own timeout kills it, potentially hours later. Fixed by
setting `NEEDRESTART_MODE=a` (forces automatic restart, no prompt) and
`DEBIAN_FRONTEND=noninteractive` (belt and braces for any other debconf
prompt) as step-scoped `env`, not workflow-wide -- no other step touches
`apt`. If Linux ever hangs again on a *different* step, this is the
pattern to reach for, not a package-set problem by default.
