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
OS. **The exact apt package set (`libegl1 libgl1 mesa-vulkan-drivers`) is
a best-effort guess, not verified against a real run.**

**This workflow has never executed on GitHub Actions -- deliberately,
for now, not just because no remote exists.** The repository has no git
remote, so it couldn't have run regardless; but the maintainer's
2026-08-16 call (`docs/planning/backlog.md` C2) is to defer actually
verifying it until a 2D demo exists, since development stays local until
then anyway. Until that happens, "the CI pipeline" means `make ci` run
locally, which does pass -- treat that as the accepted definition, not as
a gap silently substituting for the real one. When GitHub Actions
verification does happen, this apt package step is the first thing to
check if Linux is green everywhere except the rendering tests.
