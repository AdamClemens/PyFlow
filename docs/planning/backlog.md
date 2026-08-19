# Backlog

## How to use this file

**Part I** is the ordered work queue for reaching Stage 0. Executing it
top to bottom, respecting the stated dependencies, should leave the
repository in a state where an audit against `docs/planning/roadmap.md`'s
Stage 0 Completion Criteria passes. Nothing needed for Stage 0 should be
absent from Part I; if something is found missing, add it there rather
than working around it.

**Part II** is work deliberately deferred past Stage 0. It is not
abandoned, and it is not blocking.

**Part III** is the audit history: the 2026-08-12 pre-Stage-0 checklist
and the 2026-08-15 full repository review, preserved as the record of
what was found and what was done about it. Items there are closed or have
been promoted into Parts I and II. Do not work from Part III -- read it
to understand why something is the way it is.

Update in place as items close; don't delete completed items outright --
mark them done, so this stays a record of what happened, not just what's
left.

Each Part I item states what it produces and how completion is checked,
so that "is this done?" is answerable without judgement calls.

---

# Part I — Stage 0 Work Queue

Stage 0 is complete when, per `roadmap.md`:

1. Every Stage 0 task (TASK-000..010) satisfies its acceptance criteria.
2. All engineering tooling is operational.
3. Documentation has a complete first draft.
4. Repository structure reflects the intended architecture.
5. Coding agents have contextual guidance throughout the repository.
6. A developer can clone the repository and begin Stage 1 immediately.
7. The engine successfully bootstraps into an empty rendering window.
8. CI executes.
9. Stage 0 infrastructure is reproducible.

Criteria 8 and 9 came from KA-034's Definition of Done when that entry
was superseded (A4). They were previously implied by criterion 2 and are
now stated, because a pipeline that exists but never runs satisfies the
looser reading and not this one.

Criterion 3 was ambiguous. It was fixed on 2026-08-15 (A3 below) to mean:
*no file tracked in `docs/repository-manifest.md` is empty* -- each is
either a genuine first draft or explicitly retired. That is what puts
Group E in scope in full.

**Extended 2026-08-19 (F3 exit audit, maintainer's call), same reasoning
as the original carve-out:** `assets/`'s manifest row is ⬜ -- not a file
sitting empty, but a collective row for colourmap files that were never
created, gated on Stage 1+ field-rendering work (`adr/ADR-005`, roadmap
TASK-017) the same way the `planning/**.yaml` graph is gated on handbook
content. Writing placeholder colourmap content now to force a 🟨 would be
exactly the kind of speculation E9's revised *Done when* already refuses
to manufacture elsewhere. Carved out on the same terms: content becomes
known when TASK-017 needs it, not before.

---

## Group A — Decisions and unblocking (do first; everything else waits on these)

- [x] **A1a. Decide the development environment strategy** (decided
      2026-08-15, maintainer's call: **host `uv` + uv-managed venv, with
      CI enforcing reproducibility**).
      One clarification shaped this: `uv` and `make` cannot live *inside*
      a Python virtual environment. `uv` is a standalone binary that
      *creates* venvs, and `make` is a system tool. So the real options
      were a host `uv` plus a uv-managed venv, a dev container, or a
      hybrid of the two.
      **Chosen:** `uv` installed at user level; `uv` supplying the
      interpreter (3.14, per A1b below -- 3.12 was this decision's
      placeholder, not its outcome); `.venv/` holding project dependencies;
      `make` installed on the host. Reproducibility is enforced by CI
      (C2/TASK-004) rather than by a container image -- the pipeline is
      what actually proves a clean checkout builds, which is Stage 0's
      "infrastructure is reproducible" criterion.
      **Why not a dev container:** it is reproducible by construction and
      CI could reuse the image, but Stage 0 *ends* by opening a rendering
      window (TASK-007, and TASK-010's acceptance criterion is `make
      demo` starting the application). Running a GUI from a container on
      Windows means WSLg or X forwarding, with hardware-accelerated
      OpenGL fiddly at best. Paying that cost for the whole of Stage 0,
      to solve a problem CI already solves, is the wrong trade.
      **Consequence for A2:** the rendering survey is *not* constrained by
      container display limitations, so every candidate family stays on
      the table. Headless rendering is still a hard requirement, but for
      CI/golden-demo reasons rather than local-development ones.

- [x] **A1b. Stand up the environment** (done 2026-08-15). Checked on the
      development machine: `uv` is **not installed**, `make` is **not
      installed** (Git for Windows does not ship it), and the Python on
      `PATH` is **3.10.5** against `requires-python = ">=3.12"`. Every
      acceptance criterion in TASK-001 and TASK-002 is phrased as
      `make install` / `make test`, so none of them can be verified -- or
      honestly claimed -- until this is fixed. This is also why §2's
      tooling items were closed with an explicit "unverified" caveat
      rather than as confirmed working.
      Steps:
      - [x] Install `uv` at user level -- done 2026-08-15, `uv 0.12.5` at
            `%USERPROFILE%\.local\bin\uv.exe`.
      - [x] Install `make` -- done 2026-08-15 via Chocolatey,
            `GNU Make 4.4.1`. (Not bundled with Git for Windows.) If
            `make` later proves more trouble on Windows than it is worth,
            that is a change to `roadmap.md` TASK-002 -- which names a
            `Makefile` and phrases every acceptance criterion in terms of
            it -- and should be recorded as such rather than worked
            around locally.
      - [x] A Python newer than 3.10.5 is available -- done 2026-08-15,
            CPython 3.14.7 installed.
      - [x] **Development Python version decided, then corrected to be
            derived rather than asserted** (2026-08-15). First pass
            (same day): periodic review, upgrade when it benefits
            PyFlow, applied at 3.14 -- the 3.12 previously configured was
            arbitrary rather than chosen. This was itself corrected later
            the same day (maintainer's insight, recorded in
            `docs/practices.md`): the version should not be picked
            independently at all -- it is the **intersection of what the
            dependencies A2c chooses actually support**, computed once
            those choices are made, not fixed ahead of them. The gap
            between these two framings was not academic: it is exactly
            what turned Taichi's 3.13 ceiling into something that had to
            be argued around as "reopening" a decision, when nothing was
            actually blocking anything -- a number had just been
            committed to too early.
            **Re-derived, not merely re-asserted:** checked live the same
            day against A2c's actual candidates -- CuPy (`cupy-cuda12x`),
            PyTorch, and jaxlib all confirmed shipping **cp314** wheels.
            3.14 is the correct answer under the corrected method too;
            only the reasoning changed, not the number.
            `requires-python = ">=3.14"`, the `Programming Language ::
            Python` classifier, `[tool.ruff] target-version = "py314"`
            and `[tool.mypy] python_version = "3.14"` all moved together,
            and `roadmap.md` TASK-001 no longer names 3.12. Both pinned
            tool versions were verified to accept 3.14 before the bump
            (`ruff 0.16.3`, `mypy 2.3.1`) rather than assumed.
            **Followed through** (2026-08-16, C2): `.github/workflows/ci.yml`
            reads `.python-version` via `astral-sh/setup-uv`'s
            `python-version-file` input rather than a second hardcoded
            `3.14`, so the two can't drift apart. Nothing left open here.
      *Produces:* working `uv`, `make` and a current Python; setup
      instructions in `README.md`.
      *Verified by:* `uv --version`, `make --version` and
      `python --version` all succeed, with Python reporting 3.14 or
      later. All three binaries confirmed working 2026-08-15
      (`uv 0.12.5`, `GNU Make 4.4.1`, CPython 3.14.7), **including in a
      fresh shell** -- confirmed later the same session (the original
      check was mid-session and could have been finding binaries only
      visible to that one shell). `README.md` instructions written (E11,
      done). Nothing remains open in this item.

> **Restructured 2026-08-15 (maintainer's call).** A2 (rendering) and A5
> (array/numerics) were originally independent items. They are not
> independent decisions: the array library determines what a renderer can
> read without a copy, and the renderer determines what memory layout and
> device the array library needs to produce. Assessed separately, each
> would be chosen against assumptions about the other.
>
> They are now one three-step decision: survey the **combinations**,
> choose a **class** of solution, then choose the **instances** within
> that class. A5 is folded in below and no longer stands alone.

- [x] **A2a. Survey the combined compute-and-rendering stack, and build a
      compatibility matrix** (done 2026-08-15, run interactively as
      requested -- see the extensive live-verification trail in
      `docs/CHANGELOG-DESIGN.md`). Produces
      `docs/architecture/compute-and-rendering-stack.md` (new; no KA
      entry, which is fine -- E2 already establishes that the KA spec
      need not enumerate every architecture document the project wants).
      Follows the precedent that worked for the numerical framework:
      survey (KA-007), then compatibility view (KA-008), then decision
      (ADR-002). Here the survey and compatibility view are one document
      because the whole point is that the axes interact.

      **Run this interactively** (maintainer's preference). The weightings
      are project-specific -- how much a turnkey glyph/legend
      implementation is worth against dependency weight, how seriously to
      take Capability Level 9's GPU ambitions now, how much interactive
      UI is really wanted. Draft the comparison, then settle the axes
      together rather than handing over a finished recommendation. A
      knowledge snapshot to **May 2026** is accepted as the basis, so this
      does not block on live version checking; record the snapshot date
      in the document so a later reader can tell a stale claim from a
      wrong one.

      **Axis 1 -- array/numerics libraries.** What holds field data and
      executes the operators. Candidates span CPU-only, GPU-capable with
      a NumPy-compatible interface, and compiled/kernel-oriented
      approaches. The property that matters most long-term is whether the
      array type has a GPU-backed counterpart with a compatible
      interface, because that decides whether Capability Level 9 is an
      upgrade or a rewrite.

      **Axis 2 -- rendering libraries.** Assessed in the earlier
      single-axis pass; families are scientific visualisation toolkits
      (VTK/PyVista -- the OpenFOAM/ParaView lineage), GPU-accelerated
      scientific visualisation (VisPy, wgpu-py/pygfx), thin graphics
      layers (ModernGL, pyglet, glfw+PyOpenGL), GUI frameworks
      (PySide6/Qt), and matplotlib -- too slow for a real-time loop but
      likely wanted alongside the winner for validation plots and
      golden-demo regression images.

      **The matrix.** For each viable pairing, record what actually
      couples them:
      - can the renderer consume the array type directly, or is a
        conversion needed every frame?
      - if both are GPU-capable, can they share a buffer, or does each
        frame round-trip through host memory?
      - do they agree on memory layout and dtype, or is there a hidden
        copy?
      - do both support Python 3.14 (the chosen version -- see
        `docs/practices.md`'s Python version policy)? This is a live
        constraint, not a formality: 3.14 is recent and both library
        families are exactly the kind that lag a new release, which is
        itself an input to the periodic version review the policy calls
        for -- a stack that only supports 3.12 is a reason to hold there.
      - both licences compatible with BSD-3-Clause?
      - do both work headless, for D5's golden-demo regression testing?

      **Classes of solution.** Group the pairings into classes that
      represent genuinely different architectures rather than different
      brands -- for example "CPU arrays with a scientific-viz toolkit",
      "GPU arrays sharing buffers with a GPU renderer", "CPU arrays with
      a thin custom renderer". The class is the architectural commitment;
      the instances within it are comparatively replaceable. Say for each
      class what it makes easy, what it forecloses, and what it costs to
      leave later.

      **Multiple renderers.** The maintainer's stated ambition is to
      support more than one renderer, or different renderers for
      different domains, if the numerics allow. This is consistent with
      `adr/ADR-003-modular-numerical-strategies.md` -- rendering behind a
      stable interface, selected at construction. Treat it as an
      assessment axis in its own right: **which classes keep a second
      renderer cheap, and which quietly assume there is only one?** A
      class that couples the array type to one renderer's buffers is
      buying performance with that flexibility, and that trade should be
      explicit rather than discovered.

- [x] **A2b. Choose the class, and record it as an ADR** (decided
      2026-08-15, maintainer's call: **Class 2** -- GPU-capable,
      NumPy-shaped array library, general-purpose renderer, host
      round-trip accepted as the default coupling). Recorded as
      `adr/ADR-004-compute-rendering-class.md`.
      Reached after `docs/architecture/compute-and-rendering-stack.md`'s
      first-pass survey (A2a) was followed by live verification of
      Taichi and Warp specifically, prompted by the class's own
      maintainer-facing lean toward native compute+render: Taichi's
      release cadence turned out to have stalled (13+ months, widening
      gaps beforehand) and its Python ceiling (3.13) conflicted with the
      3.14 already chosen; Warp is well-maintained and production-proven
      (NVIDIA's own Newton engine) but its renderer is documented as
      debug-grade, so it inherits Class 3's kernel-DSL cost against
      `ADR-003` without Class 3's native-rendering payoff. With Class 3
      effectively ruled out, Class 2's own case strengthened under
      scrutiny rather than winning by default: CuPy and PyTorch both have
      verified, official multi-vendor GPU support (ROCm; PyTorch also
      Apple MPS) that neither Taichi nor Warp match; all three candidate
      instances (CuPy/PyTorch/JAX) are independently well-maintained; and
      the host round-trip's cost, quantified against the MVP's actual 2D
      scope, turned out to be a near/medium-term non-issue rather than
      the assumed-costly fallback the first survey pass treated it as.
      See `docs/CHANGELOG-DESIGN.md` for the full trail.
      *Verified by:* the ADR exists and is Accepted -- done.

- [x] **A2c. Choose the instances within the class** (decided 2026-08-15,
      maintainer's call: **PyTorch** for the array library, **wgpu/pygfx**
      for the renderer). Recorded as
      `adr/ADR-005-compute-rendering-instances.md`.
      PyTorch chosen over CuPy for its broader verified hardware reach
      (official ROCm and Apple MPS), its ecosystem depth and maintenance
      backing, and latent differentiable-simulation optionality --
      accepting in exchange a less literal fit to the NumPy-shape
      argument that won Class 2 the A2b decision, and the heaviest
      install of the three candidates. wgpu/pygfx chosen over VisPy on
      its confirmed-live headless story (own CI runs on LavaPipe as
      standard practice); VTK/PyVista and ModernGL/glfw were not
      re-verified live and were not preferred over the two that were --
      not ruled out on evidence, simply not chosen without it.
      `pyproject.toml` now declares `torch` and `pygfx` as runtime
      dependencies (unpinned pending B2), `roadmap.md` TASK-007 records
      the choice and instructs against re-litigating it during
      implementation, and `docs/repository-manifest.md` carries both
      ADRs. See `docs/CHANGELOG-DESIGN.md` for the full trail.
      *Verified by:* TASK-011 has no unmade dependency decision in front
      of it, and D3 knows what it is building against -- done.

- [x] **A4. Decide KA-034's fate** (decided 2026-08-15, maintainer's
      call: **retire it**). KA-034 specified
      `docs/implementation/stages/stage-0.md`, which was never written,
      while `roadmap.md`'s Stage 0 section came to cover the same ground
      in more detail. Its purpose is now served by `roadmap.md` (the
      specification) plus Part I of this file (the ordered queue that
      executes it), so writing a separate file would duplicate the first
      and set up a `stages/` directory competing with the roadmap as
      Stages 1-12 arrive.
      Marked `superseded` rather than `complete` -- `complete` would send
      a reader after a file that does not exist. That required a fourth
      value in the KA status vocabulary (`planned`/`draft`/`complete`),
      added with a long-term view: over twelve stages artifacts will be
      replaced, the ADR lifecycle in `adr/README.md` already uses the
      term, and the alternatives were deleting the entry (losing the
      record, against P-001) or misreporting it.
      **Nothing was dropped.** KA-034's Definition of Done was compared
      against `roadmap.md`'s criteria first: five items were already
      covered, and the two stated there but only *implied* in the roadmap
      -- "CI executes" and "Stage 0 infrastructure is reproducible" --
      were added to the Stage 0 Completion Criteria explicitly, as
      criteria 8 and 9. The criteria list is now **nine**, not seven.

---

## Group B — Package and environment (TASK-000, TASK-001, TASK-002)

Depends on A1b.

- [x] **B1. TASK-000 — create the engine skeleton** (done 2026-08-15).
      Created `src/pyflow/__init__.py` and `__main__.py`, plus
      `__init__.py` for `engine/`, `physics/`, `rendering/`,
      `configuration/` -- six files, docstring-only, no implementation
      beyond package initialisation, matching each package's existing
      `CLAUDE.md` description rather than inventing new scope. No
      internal submodules created (e.g. no `engine/mesh.py`) --
      prescribing that structure now would pre-empt Stage 1-3's own
      task-by-task design (TASK-011 onward) against P-016 (prefer
      reversible decisions until understanding justifies commitment).
      *Verified by running, not assumed:* `python -c "import pyflow,
      pyflow.engine, pyflow.physics, pyflow.rendering,
      pyflow.configuration"` succeeds; `python -m pyflow` executes and
      prints its version; `ruff check` (0.16.3, target-version py314) and
      `mypy --strict` (2.3.1, python-version 3.14) both pass clean, via
      isolated `uv tool run` since no project venv exists yet (B2).
      "No circular dependencies" verified by inspection only -- none of
      the six files import from another `pyflow` subpackage. The gap
      flagged before B1 started still stands and is **not** closed by
      this: nothing *mechanically* checks this claim, and it is the one
      TASK-000 criterion that will silently rot as real imports appear.
      Add an import-graph check in C1 or C2 before the package grows
      past this trivially-acyclic starting point.
      "Package structure matches the documented architecture" -- matches
      TASK-000's own package list and each package's `CLAUDE.md`; no
      broader `docs/architecture/engine.md` exists yet to match against
      (E1a).

- [x] **B2. TASK-001 — complete the development environment** (done
      2026-08-15). `uv.lock` generated (62 packages resolved, including
      `torch`, `pygfx` and their transitive dependencies per
      `ADR-004`/`ADR-005`) and committed -- a lockfile only does its job
      tracked in version control. `.python-version` added, containing
      `3.14`: consistent with the Python version policy
      (`docs/practices.md`) to pin the deliberately-chosen version so
      that choice is reproducible until the next periodic review, not an
      open question left for later.
      *Verified by running the actual acceptance criterion, not
      inspection:* `make install` → `make clean` → `make install` cycle
      run for real -- `.venv` and the git pre-commit hook both removed by
      `clean` and fully restored by `install`, `uv sync` resolving
      `torch==2.13.0`, `pygfx==0.17.0`, `wgpu==0.32.0` exactly as A2c's
      live checks found. `make test` now exits 0 (C1a landed alongside
      this); the remaining tool-version-vs-hook-`rev` mismatch check
      noted here originally is folded into B4 below, now also done.

- [x] **B3. TASK-002 — verify the build system** (done 2026-08-15).
      Every target run for real: `install`, `lint`, `typecheck`, `test`,
      `demo`, `clean` all verified directly (see B2, B4, C1a). `format`
      not separately re-verified beyond what `lint` already covers (it
      calls the same `ruff format`). `docs` remains a placeholder --
      correctly, nothing exists yet for it to build.
      **Makefile reshaped in the same change** (maintainer's request):
      `lint` now runs `pre-commit run --all-files` instead of bare `ruff
      check` -- covers formatting *and* linting, for docs and code both,
      using tooling already configured rather than adding anything new.
      `clean` now explicitly undoes what `install` did (removes `.venv`,
      uninstalls the git hook) **and states what it deliberately leaves
      alone and why** -- `uv` itself, the shared uv-managed Python
      interpreter, uv's global package cache -- rather than silently
      doing a partial job. `demo` now actually runs `python -m pyflow`
      instead of echoing a placeholder, with a note that the real
      bootstrap is still TASK-010. A new **`ci` target** was added,
      chaining `lint`, `typecheck`, `test` -- stated as the thing C2's CI
      workflow should invoke rather than duplicate (P-011), so the
      workflow definition and local verification can't drift apart.
      *Verified by:* every target's actual output inspected, not just
      its exit code -- see the full record in
      `docs/CHANGELOG-DESIGN.md`.

- [x] **B4. Run `pre-commit` against the whole repository for the first
      time** (done 2026-08-15, via the new `make lint`). First run:
      `end-of-file-fixer` fixed two files
      (`docs/handbook/numerical-methods/overview.md`,
      `docs/planning/implementation-plan.md` -- both missing a trailing
      newline, one line removed each). Every other hook, including
      `mypy` under `strict = true` against B1's real modules, passed
      clean on the first attempt. Second run: fully clean, confirming the
      fix was genuinely sufficient rather than papering over something
      that would recur. Diff inspected before accepting -- both changes
      were exactly the expected trailing-newline removal, nothing
      unexpected.

---

## Group C — Testing and CI (TASK-003, TASK-004)

Depends on B.

- [x] **C1a. Entry-point smoke test** (done 2026-08-15, maintainer's
      request -- specified as its own explicit item rather than folded
      silently into C1, "to avoid things falling through the gaps").
      Acceptance criteria as given: `python -m pyflow`, called with no
      arguments, must print version and help info by default, and a test
      must verify this. This was **new scope**, not part of TASK-000's
      original written acceptance criteria (which only required "example
      entry point executes," already satisfied by B1) -- recorded as
      such rather than silently rewriting B1's history.
      **Two things landed together:** `src/pyflow/__main__.py` extended
      to use `argparse` and print the version line followed by
      `parser.print_help()` on every invocation (verified directly:
      `pyflow 0.0.1` plus full usage/options text, exit 0; `--help`
      still works via argparse's built-in handling). And
      `tests/integration/test_cli.py`, the repository's **first
      automated test** -- invokes `python -m pyflow` as a real
      subprocess (not calling `main()` in-process) and asserts exit 0,
      the version string, and help text all present in stdout.
      **Settles a real open question in passing:** is this a unit or
      integration test? Called integration -- it crosses the real
      process boundary the way a user invokes the package, which a
      direct in-process call to `main()` would not exercise. Written up
      in `tests/CLAUDE.md` and `tests/integration/CLAUDE.md` (both
      previously generic placeholders) as the first concrete precedent
      for the unit/integration split E9 had flagged as undocumented.
      *Verified by:* `make test` -- 1 passed, exit 0. First green test
      run in the repository's history.

- [x] **C1b. TASK-003 — the rest of automated testing** (done 2026-08-16).
      `pytest-cov` added to the `dev` dependency group (`uv add`, so
      `pyproject.toml` and `uv.lock` both moved together). `[tool.pytest]`
      now runs with `--cov=pyflow --cov-report=term-missing`; a new
      `[tool.coverage.run]`/`[tool.coverage.report]` scopes coverage to
      `src/pyflow`, turns on branch coverage, and deliberately sets no
      `fail_under` yet -- there's one real test and almost no
      implementation, so a threshold now would be either meaningless or
      gamed. No further smoke tests added -- still nothing beyond the
      entry point worth testing, same as when this item was opened.
      **Known gap, found and closed the same day, not left standing:**
      `test_cli.py` invokes `python -m pyflow` as a real subprocess (by
      design, see `tests/integration/CLAUDE.md`), and `pytest-cov` only
      instruments the in-process interpreter -- so `__main__.py` reported
      0% coverage despite genuinely being exercised. Originally recorded
      as a deliberately-deferred gap (real fix: `COVERAGE_PROCESS_START` +
      `sitecustomize.py`, not worth the setup for one module). **Closed
      differently, later the same day, on the maintainer's request:**
      rather than the heavier subprocess-coverage machinery, `main()`
      gained an optional `argv` parameter (the same convention
      `argparse.parse_args` itself uses) so `tests/unit/test_main.py` and
      `test_bootstrap.py` could call `main()`/`bootstrap()` directly,
      in-process -- complementary to the subprocess tests, not a
      replacement for them; the subprocess tests still verify the real
      packaged entry point, the new unit tests exist purely so
      coverage.py has something to measure. `__main__.py` now 91% covered
      (only the `if __name__ == "__main__":` guard line stays
      unreachable under import, correctly), `bootstrap.py` 100%. Overall
      coverage moved from 73% to 90%. `pyproject.toml`'s
      `[tool.coverage.report]` comment rewritten to describe the
      resolution and name this as the preferred pattern for any future
      subprocess-only module, ahead of reaching for
      `COVERAGE_PROCESS_START`.
      **A second, unrelated gap surfaced while adding the new unit
      test:** `tests/unit/test_bootstrap.py` collided with the
      already-existing `tests/integration/test_bootstrap.py` -- both
      pytest and mypy identify test modules by bare basename without an
      `__init__.py`, and two same-named files in different `tests/`
      subdirectories broke both tools' collection. Fixed by adding a
      one-line `__init__.py` to `tests/unit/`, `integration/`, `golden/`,
      `performance/` -- not just the two directories that collided today,
      since the same collision is exactly as likely the next time two
      subdirectories independently test the same module by its natural
      name.
      *Verified by running, not assumed:* `make ci` -- 29 tests (up from
      25), coverage table showing the real 90%, mypy clean across `src
      tests examples`, pre-commit clean.

- [x] **C2. TASK-004 — continuous integration** (written 2026-08-16,
      maintainer's call on the matrix: **both Windows and Linux**, not
      Linux-only -- development happens on Windows and that's exactly
      where `make` behaviour and headless rendering (D5) are most likely
      to diverge from a Linux-only pipeline, so both need to stay green,
      not just one). `.github/workflows/ci.yml` runs on push to `main`
      (renamed from `master` 2026-08-19, F1) and on every pull request,
      matrixed over `ubuntu-latest` and
      `windows-latest`. **Invokes `make ci`** (added 2026-08-15, B3)
      rather than restating install/lint/typecheck/test in the workflow
      YAML, so the two can't drift apart (P-011). Python comes from
      `.python-version` (currently 3.14) via `astral-sh/setup-uv`'s
      `python-version-file` input, not a second hardcoded version number
      -- closes the loop A1b left open (see A1b's entry above, updated in
      this same change).
      **Windows needs an explicit `make` install step** -- `windows-latest`
      doesn't ship GNU Make, the same gap A1b found on the local dev
      machine, fixed the same way (Chocolatey, which the runner image
      preinstalls), conditional on `runner.os == 'Windows'`. `ubuntu-latest`
      already ships Make and needs no equivalent step.
      `.github/CLAUDE.md` and `.github/workflows/CLAUDE.md` written in
      the same change (also closes that pair in E9's list below).
      **Not yet verified the way this backlog's own standard demands, and
      that's now a deliberate scope decision, not an open worry.** Every
      other closed item in this file was verified by actually running the
      thing; this one hasn't been, because the repository has no git
      remote, so the workflow has never executed on a real GitHub Actions
      runner. What *has* been checked directly: the YAML parses (`python
      -c "import yaml; yaml.safe_load(...)"`), `make lint`'s `check-yaml`
      pre-commit hook passes over it, and the sequence it invokes (`make
      ci`) was itself just re-run clean locally.
      **Maintainer's call, 2026-08-16, when asked directly about this
      gap:** real GitHub Actions verification is deferred until a 2D demo
      exists -- development stays local until then regardless, so
      "the CI pipeline" is understood to mean `make ci` / the local test
      suite for now. This isn't the gap closing; it's the gap's scope
      being set on purpose rather than left as an ambient worry re-raised
      every time this item is touched. TASK-004's literal acceptance
      criterion -- "every pull request executes the validation pipeline
      automatically" -- still stays open until a remote exists and a real
      PR runs it; F3's exit audit must check this against the state at
      the time, not against this note.
      *Verified by:* locally, as above.

---

## Group D — Engine subsystems (TASK-005, 006, 007, 010)

D1-D3 depend on B1 (done) and, for D3, on A2 (done) -- all three are
unblocked. D4 depends on B3 (done), D1, D2, D3. D5 depends on D4 --
stated explicitly here since it was previously only implied by its own
text ("D4 produces a bootstrap application; that is not the same
artifact as a golden demo").

- [x] **D1. TASK-005 — configuration framework** (done 2026-08-16,
      maintainer's call on format: **YAML via PyYAML**, over stdlib TOML
      or JSON -- common in sim/ML tooling and the more flexible syntax,
      accepted over adding zero new dependencies). `src/pyflow/
      configuration/schema.py` defines nested dataclasses
      (`PyFlowConfig`/`LoggingConfig`/`RenderingConfig`), every field
      defaulted so `PyFlowConfig()` alone is complete and valid --
      that's what makes "the application can be started entirely from
      configuration" true even with zero config file. `loader.py`'s
      `load_config(path)` reads YAML and rejects unknown sections/fields
      and out-of-range values immediately (`ValueError`), rather than
      silently ignoring a typo. This is the mechanism
      `adr/ADR-003-modular-numerical-strategies.md` and
      `docs/implementation/golden-demos.md` both assume exists -- demos
      must select numerical components through configuration rather than
      hardcoding them; not built yet, since there are no numerical
      components to select.
      **Design coupling with D3, decided upfront rather than
      retrofitted:** `RenderingConfig.backend` selects the render canvas
      (`"glfw"` interactive / `"offscreen"` headless) -- D5's golden demo
      must run headless in CI regardless of anything else, so D3 needed
      two canvas modes from the start, and D1's schema needed the field
      to select between them.
      *Verified by running:* `tests/unit/test_configuration.py` (11
      tests, 100% coverage on `schema.py`/`loader.py`) -- defaults,
      partial overrides, and every rejection path. First real
      `tests/unit/` test; `tests/unit/CLAUDE.md` written against it
      (closes that half of E9's list below).

- [x] **D2. TASK-006 — logging framework** (done 2026-08-16). stdlib
      `logging`, not a third-party structured-logging library -- nothing
      about Stage 0 argues for more than that. `src/pyflow/engine/
      logging_setup.py`: `configure_logging(LoggingConfig)` sets up the
      `pyflow` logger once (level + formatting), and `get_logger(name)`
      is the one documented entry point every subsystem uses
      (conventionally `get_logger(__name__)`) -- a child of `pyflow` that
      inherits level and handler through the normal logging hierarchy,
      so "every subsystem logs through the common framework" is a naming
      convention, not a mechanism each module opts into.
      *Verified by running:* `tests/unit/test_logging.py` (4 tests, 100%
      coverage) -- level configuration, no handler accumulation across
      repeated calls, child-logger inheritance.

- [x] **D3. TASK-007 — rendering framework** (done 2026-08-16,
      maintainer's call on the windowing backend: **build a
      canvas-selection seam, not a single hardcoded library** -- glfw
      implemented now for the interactive case, Qt left as a documented
      future backend behind the same seam, rather than picking one
      forever. This extends `adr/ADR-003-modular-numerical-strategies.md`'s
      already-accepted pattern -- implementations swappable behind a
      stable interface, selected at construction -- one layer down, to
      the windowing library rather than the whole renderer).
      `src/pyflow/rendering/canvas.py`'s `create_canvas(config)` builds
      either a `rendercanvas.glfw.GlfwRenderCanvas` or a
      `rendercanvas.offscreen.OffscreenRenderCanvas`; `window.py`'s
      `RenderWindow` doesn't know or care which one it got, since both
      implement the same `rendercanvas.base.BaseRenderCanvas` protocol
      that `pygfx.WgpuRenderer` depends on. Added `glfw` and kept
      `pygfx`/`wgpu` as runtime dependencies (already declared, A2c);
      added a scoped `[[tool.mypy.overrides]]` for `pygfx.*`/
      `rendercanvas.*` since neither ships a py.typed marker.
      **Real API drift found and worked around, not assumed away:** the
      A2a survey (2026-08-15) described `wgpu.gui.offscreen`/
      `wgpu.gui.auto`; the actually-installed `wgpu` 0.32.0 has no
      `wgpu.gui` submodule at all -- canvas support moved to a separate
      `rendercanvas` package (2.7.2), a dependency of `wgpu`/`pygfx`
      already resolved into `uv.lock`. Found by trying the import, not by
      re-reading the survey harder.
      *Verified by running, both backends:* `tests/unit/test_rendering.py`
      (5 tests, offscreen only -- CI has no display) exercises canvas
      creation, the full render loop, and clean shutdown headlessly.
      **The interactive glfw backend was also actually run**, manually, on
      the dev machine: a real window opened at 400x300, drew 5 frames, and
      closed cleanly (`frame_count=5, closed=True`) -- not just
      constructed and assumed to work.

- [x] **D4. TASK-010 — engine bootstrap** (done 2026-08-16).
      `src/pyflow/bootstrap.py`'s `bootstrap(config_path, *, max_frames)`
      loads configuration (D1), initialises logging (D2), opens the
      render window and runs the loop (D3), exits cleanly. Wired to `pyflow
      run` in `__main__.py` as a subcommand, not the bare-invocation
      default -- keeps C1a's existing no-args contract (prints version +
      help, still what `tests/integration/test_cli.py` checks) unchanged
      underneath it. `Makefile`'s `demo` target now runs `python -m
      pyflow run` for real instead of the Stage 0 placeholder note it
      carried since B3.
      **A real circular import, found by running the import, not by
      inspection:** `bootstrap.py` was first written inside `engine/`
      (TASK-010's own name says "engine bootstrap"). That created a
      genuine cycle -- `engine` needing `rendering` (for the window),
      while `rendering.window` needs `engine.logging_setup` (for its
      logger) -- so whichever package a program imported first would find
      the other only partially initialised. Reordering the imports inside
      `engine/__init__.py` "fixed" it locally, but `ruff`'s isort hook
      silently reordered them straight back on the next `make lint`,
      reintroducing the bug -- a fragile fix, not a real one. **The actual
      fix was structural:** moved `bootstrap.py` out of `engine/` to the
      `pyflow` package root, since it orchestrates `configuration`,
      `engine` and `rendering` together and so belongs above all three,
      not inside one of them. Verified clean from every import order
      afterward (`import pyflow.rendering` first, `pyflow.engine` first,
      `pyflow.bootstrap` first, all fresh interpreters). Recorded as a
      standing rule in `src/pyflow/CLAUDE.md`: a module that orchestrates
      two or more subpackages belongs at the package root, not inside
      whichever subpackage its task name happens to suggest.
      **A permanent regression test added afterward, on the maintainer's
      standing instruction** (2026-08-16: always add one with measurable
      pass/fail criteria when a bug like this is found, not just fix it):
      `tests/integration/test_import_order.py` imports every `pyflow`
      subpackage/module first, each in its own fresh subprocess (`sys.
      modules` caching means re-importing in the same process would never
      re-exercise the ordering that actually broke) -- exactly the
      technique that found this bug in the first place, kept around so it
      can't reappear silently.
      *Verified by running, not assumed:* `tests/integration/
      test_bootstrap.py` runs `python -m pyflow run --config <offscreen
      config> --max-frames 2` as a real subprocess, exit 0. The
      interactive path was also run manually end-to-end via the actual
      CLI (`python -m pyflow run --max-frames 5`, real glfw window, 5
      frames, clean exit) and the bare no-args form re-checked to confirm
      it still prints version + help unchanged. `make ci` re-run clean
      after every step in this item, not just at the end.
      **What TASK-010's own acceptance criteria still owe, honestly:**
      "the CI pipeline passes" inherits C2's scope decision -- `ci.yml`
      has never executed on a real GitHub Actions runner (no remote), and
      per the maintainer's 2026-08-16 call (C2 above), verifying that is
      deliberately deferred until a 2D demo exists; until then "the CI
      pipeline" means `make ci` locally, which does pass. D3 raised the
      stakes of the deferred part specifically: Linux CI would need a
      software Vulkan driver for the rendering tests to even construct a
      `wgpu` device, and the apt package set already added to `ci.yml` for
      that is itself unverified (see `.github/workflows/CLAUDE.md`) --
      something to check when GitHub Actions verification actually
      happens, not before. "All Stage 0 components integrate" is true for
      D1-D4 specifically, run for real; it is not yet true of Stage 0 as a
      whole while TASK-008/009 (Group E) remain partial.
      **A real usability bug found by the maintainer actually running
      `pyflow run`, not by any verification pass recorded above -- worth
      being honest about why it was missed.** The window opened, rendered,
      and then had no way to be closed short of killing the process
      (Ctrl+C). Root cause: `close_keys`-style handling had only ever
      been implemented in the Empty Window demo script (D5's follow-up
      entry above), never in `RenderWindow`/`bootstrap.py` itself -- and
      every verification of the interactive path recorded in this file,
      here and in D3, used `max_frames` to bound the run
      (`--max-frames 5`, etc.), so the actual "no bound, a real person has
      to close this" scenario was never once exercised before now. Fixed
      by moving the close-key handler into `RenderWindow.run()` itself,
      on by default (`close_keys=("Escape", "Enter")`) for every
      interactive window -- `bootstrap.py` needed no change at all, since
      it already calls `window.run(max_frames=max_frames)` without
      touching `close_keys`, so the fix reaches `pyflow run` for free.
      Verified with the reproduction the maintainer themselves suggested:
      inject a simulated keypress after a real multi-second delay, not
      immediately. `loop.call_later(6.0, ...)` submitted a `key_down`
      Escape event into a genuinely-running `window.run()`; confirmed the
      window was still actively repainting the whole time (164 frames
      over 6 real seconds -- not frozen) and closed cleanly the instant
      the event arrived. Re-ran the actual CLI too (`python -m pyflow run
      --max-frames 3`) to confirm the log line now states the close keys
      explicitly. **Not captured as an automated test**: a real
      `GlfwRenderCanvas` needs an actual display/window system, which
      headless Linux CI doesn't have -- same reason the offscreen-only
      test convention exists for D3. Documented in
      `src/pyflow/rendering/CLAUDE.md` with the exact verification command
      to re-run locally after touching this code.

- [x] **D5. Deliver the "Empty Window" golden demo** (done 2026-08-16).
      **Superseded later the same day -- read the "Second follow-up"
      paragraph below before trusting the specifics here.** The three
      artifacts as first built are described below for the record, but
      `empty_window.py` no longer exists: it was deleted and replaced by
      `empty_window.yaml` once the public-API rule (also below) required
      it. Treat this top section as "what D5 originally did," not as
      current fact.
      Three artifacts, all built:
      - [x] an Empty Window entry in `docs/implementation/golden-demos.md`
            -- what "working" means (window opens through the real
            configuration/rendering frameworks, a frame actually renders
            and presents, closes cleanly, runs both headless and
            interactive), placed before the Initial Golden Demo section
            since Capability Level 0 precedes Level 1.
      - [x] runnable demo code: `examples/golden-demos/empty_window.py`
            -- a `run(config, *, max_frames)` function plus an
            `if __name__ == "__main__":` block, so the same code is both
            the interactive demo (`uv run python
            examples/golden-demos/empty_window.py`, real glfw window) and
            what the regression test calls headlessly.
      - [x] a regression test: `tests/golden/test_empty_window.py` --
            loads the demo module by file path (`importlib.util.
            spec_from_file_location`, not an import statement:
            `examples/` isn't an importable package and `golden-demos`
            has a hyphen in it regardless), runs it with the offscreen
            backend, and asserts the rendered frame is *exactly* the
            demo's declared background colour (`#1a1a2e`) at every
            pixel, plus that two separate runs produce byte-identical
            output -- "verifies meaningful behaviour" and "deterministic"
            from golden-demos.md's Definition of Done, both checked for
            real rather than assumed from "it didn't crash."
      **A real bug in D3 found and fixed while building this, not
      before:** `RenderWindow`'s offscreen path called `renderer.render()`
      directly every frame but never called `canvas.draw()` -- which
      turns out to be the only thing that actually triggers presentation
      and captures the frame in `rendercanvas.offscreen`. Every existing
      D3 test still passed throughout, because none of them had ever
      inspected the rendered pixels, only that `renderer.render()` didn't
      raise and `frame_count` incremented. Confirmed empirically before
      fixing: `renderer.render()` alone left `canvas._last_image` at
      `None`; `canvas.draw()` (which invokes whatever was registered via
      `request_draw()`, then presents) is what actually populates it.
      Fixed in `window.py`: offscreen mode now registers `self._draw`
      via `request_draw()` once, then calls `canvas.draw()` each frame
      and stores the result on a new `RenderWindow.last_image` attribute.
      Added `test_render_window_captures_pixel_data` to
      `tests/unit/test_rendering.py` (D3's own suite) so this doesn't
      regress silently again. This is exactly the class of bug the root
      `CLAUDE.md`'s "verified by running, not assumed" standard exists to
      catch -- and here it caught something the earlier verification
      pass had missed, not just re-confirmed something already known.
      `Makefile`'s `typecheck` target extended to `mypy src tests
      examples` now that `examples/` holds real Python code (an already
      open note from B3, closed here rather than left for later).
      *Verified by running:* `make ci` -- 25 tests (up from 22), all
      passing, including both new golden-demo tests; the interactive
      demo script launched manually and opened a real window (killed
      after 3s since it has no auto-close, by design -- a human demo
      should wait for the human).
      This also makes A2a's **headless rendering** requirement real
      rather than theoretical: a golden demo that couldn't run in CI
      wouldn't be included in regression testing, and would fail its own
      Definition of Done. `tests/golden/test_empty_window.py` runs
      exactly like every other test in `make test` -- headlessly, via the
      offscreen backend -- so it's covered by whatever `make ci` proves,
      for whatever that's currently worth (see C2's still-open
      CI-verification caveat above).
      *Verified by:* the demo runs in CI with no display and its
      regression test passes.
      **Follow-up, same day (maintainer's request):** manual verification
      of a golden demo means actually looking at it, and the original
      interactive run either closed too fast to see (`max_frames` set) or
      relied on hunting for the OS window's close button. `run()` gained
      a `close_on_key` option -- Escape or Enter closes the window via a
      `key_down` event handler (`window.canvas.add_event_handler`),
      guarded to skip the offscreen backend, which has no keyboard events
      -- and the `__main__` block now prints what to press before opening
      the window. Verified for real, not assumed: injected a simulated
      `key_down`/`Escape` event into a running interactive canvas via
      `canvas.submit_event()` while `loop.run()` was actually blocking,
      and confirmed the window closed in response
      (`frame_count=2, closed=True`) -- the same mechanism a real
      keypress produces, per `rendercanvas.glfw`'s own key-handling code.
      Documented as the standing pattern for future golden demos in
      `examples/golden-demos/CLAUDE.md`, not just applied to this one.
      (Historical note, corrected later the same session: `close_on_key`
      here describes the demo script's *first* implementation. It was
      superseded almost immediately, in the very next round of work
      recorded under D4 above, by moving the handler into
      `RenderWindow.run()` itself as `close_keys` -- the demo script's
      own copy is gone, along with the script.)

      **Second follow-up, same day (maintainer's new standing rule for
      golden demos): they must run entirely through the public API.** A
      user must be able to replicate a golden demo exactly and simply --
      which means "the relevant command, plus the specific configuration
      it needs," not a script that happens to call internal classes
      directly. Recorded in `docs/implementation/golden-demos.md`'s
      Definition of Done. Applied immediately, retroactively, to Empty
      Window, which had been violating it since it was written:
      - `examples/golden-demos/empty_window.py` (the script) **deleted**.
        `examples/golden-demos/empty_window.yaml` (the config) is the
        demo now -- one line, `rendering.background_color: "#1a1a2e"`.
      - `RenderingConfig.background_color` (`str | None`, validated
        `#RRGGBB`) added to the public configuration schema
        (`src/pyflow/configuration/schema.py`) and wired into
        `RenderWindow.__init__` -- what makes Empty Window "Empty Window"
        is now a documented configuration option anyone can use, not
        demo-only code. `None` (the default) changes nothing for
        anything not using it -- still pygfx's own default transparent
        background.
      - `pyflow run` gained `--backend`, and `bootstrap()` gained a
        matching `backend` keyword, overriding whatever the config file
        says. This is what lets *one* config file be both "the
        interactive demo" (its own default, `glfw`) and "the
        headlessly-verified version" (`--backend offscreen`) without a
        second, duplicate file -- a user could type the same override
        themselves for the same reason (a screenshot, a CI job).
      - `bootstrap()` now **returns the `RenderWindow`** (was `None`),
        so a caller -- notably a test -- can inspect what was actually
        rendered without needing demo-specific wrapper code to expose it.
      - `tests/golden/test_empty_window.py` rewritten around this:
        `test_empty_window_runs_via_the_public_cli` is a real subprocess
        running the literal command `docs/implementation/
        golden-demos.md` documents (`pyflow run --config
        examples/golden-demos/empty_window.yaml --backend offscreen
        --max-frames 1`) -- the specific, new requirement ("at least one
        test... must run it successfully as a user"). Two further tests
        use `bootstrap()` directly (still the public API, just the
        Python entry point, needed to reach `last_image` for pixel
        checks) for the deeper "renders the exact configured colour" and
        "deterministic across two runs" assertions. No more
        `importlib.util.spec_from_file_location` loading trick -- there
        is no script left to load.
      **A real, immediate consequence caught by running the build, not
      predicted in advance:** deleting the only `.py` file under
      `examples/` left it with zero Python files, and `make typecheck`
      (which had been extended to `mypy src tests examples` earlier the
      same day) started failing outright -- mypy exits nonzero on a
      directory with no Python to check. Reverted to `mypy src tests`,
      with a comment explaining why `examples/` is expected to stay
      Python-free going forward, not just today.
      Also found and fixed in passing: `tests/golden/test_empty_window.py`
      has always imported `numpy` directly, resolved only transitively
      (via `torch`/`pygfx`) and never declared -- added explicitly to the
      `dev` dependency group while touching this area, rather than left
      as a latent fragility for whenever that transitive path changes.
      *Verified by running, not assumed:* the exact CLI command a user
      would type, run directly (`uv run python -m pyflow run --config
      examples/golden-demos/empty_window.yaml --backend offscreen
      --max-frames 1`, and again with the interactive default), before
      the test suite existed to check it automatically. `make ci` -- 42
      tests (up from 35), 87% coverage, mypy clean.
      Two related ideas the maintainer raised in the same message --
      selecting among demos without knowing a file path, and a GUI for
      "run a demo, watch it happen" -- were deliberately **not** built
      now; both are explicitly deferred to when a second golden demo
      exists, recorded in Part II below.

---

## Group E — Documentation first draft (TASK-008) and agent guidance (TASK-009)

Scope is set by A3: at Stage 0 exit, **no file tracked in
`docs/repository-manifest.md` is empty**. That makes this group's extent
exact -- 25 empty files today, each of which must end up drafted or
explicitly retired. Expanded below into one item per file so progress is
trackable rather than being a single unbounded checkbox.

Independent of Groups B-D and can run in parallel with them.

Order within the group: **E8 first** -- the prompt feature contexts are
the brief the sixteen handbook entries should be written against, so
writing them afterwards wastes the leverage. Then E12 and E1, both of
which depend on nothing and unblock other work (E1b gates Stage 3). The
handbook bulk (E3, E4) next, with E6 following it since the references
come from what those entries cite.

`docs/architecture/rendering.md` **is** still in this group. A2a's
survey goes into a new `docs/architecture/compute-and-rendering-stack.md`
instead, because it covers the array library too and `rendering.md`
would be the wrong name for it. `rendering.md` therefore keeps its
original job: the rendering architecture actually adopted, written after
A2b/A2c decide.

### E1 — Architecture (2 files)

- [x] **E1a. `docs/architecture/engine.md`** (KA-029, done 2026-08-17).
      The conceptual map of the engine's nine replaceable layers (mesh,
      variables, flux, advection, diffusion, time integration,
      pressure-velocity coupling, linear solvers, boundary conditions),
      each with what it represents, its contract, its MVP implementation,
      which roadmap Stage/task it arrives via, and its upgrade path.
      States the four things that hold for every layer (contract,
      replaceable implementations, timestepper depends on contracts,
      construction selects/execution operates through them), grounded in
      `adr/ADR-002`, `adr/ADR-003`, `docs/implementation/{mvp,
      upgrade-paths}.md` and `docs/glossary.md`'s existing "Layer"
      definition rather than invented independently. Explicitly framed as
      target architecture -- Stage 1-4 layers don't exist as code yet --
      with an "Arrives via" note per layer to keep that honest as each
      one lands. Flags, without resolving, that `docs/planning/
      dependency-tree.md`'s structure doesn't match this document's nine
      layers, and that its own hand-maintained-vs-derived question is now
      unblocked (Part II).
- [x] **E1b. `docs/architecture/icds.md`** (KA-030, done 2026-08-17). The
      user/configuration-facing contracts for the six components
      `adr/ADR-003` names as independently replaceable (advection,
      diffusion, time integrator, pressure-velocity coupling, linear
      solver, boundary condition) -- each with what it represents, its
      choices (MVP's single implementation plus the upgrade path's future
      ones), a proposed `numerics.*` configuration key following
      `RenderingConfig`'s existing pattern, compatibility requirements,
      expected behaviour, and limitations. Deliberately does not cover
      Mesh or Variables -- both are `engine.md` layers but have exactly
      one implementation each with nothing yet to choose between, so an
      ICD for them would be speculative (P-016). Unblocks Stage 3
      (TASK-018..022) having something concrete to implement against, so
      "a developer can begin Stage 1 immediately" is no longer true only
      in the narrow sense this item flagged.
      *Both verified by:* re-read against their own KA Content
      Requirements/Definition of Done; `make ci` clean after writing
      (`tools/validators/check_docs.py` confirms every relative link in
      both files resolves). `docs/repository-manifest.md` (⬜->🟨 for
      both), KA-029/030 `Status` (`planned`->`draft`), `docs/architecture/
      CLAUDE.md`, and `docs/planning/dependency-tree.md`'s header note
      updated in the same change.

### E2 — Remaining architecture files (3 files)

**Done 2026-08-17.** All three decided "write," not "retire" -- each
found to have real, distinct content once actually drafted, not just a
name with nothing to say.

- [x] **E2a. `docs/architecture/overview.md`** (decided: write). The
      single top-level system map (configuration -> `bootstrap()` ->
      engine/physics + rendering), distinct from `engine.md` by staying
      one altitude above every other architecture document and pointing
      at them rather than duplicating them.
- [x] **E2b. `docs/architecture/repository.md`** (decided: write). Why
      the repository's top-level directories are shaped the way they
      are -- explicitly distinguished from
      `docs/repository-manifest.md`'s overlap risk by stating the split
      directly in both documents: this one is structural rationale
      (why a directory exists, what belongs in it), the manifest is
      per-file completion status.
- [x] **E2c. `docs/architecture/rendering.md`** (write, as already
      unblocked). The architecture of wgpu/pygfx as actually adopted and
      already implemented (`src/pyflow/rendering/{canvas,window}.py`,
      D3-D5) -- the canvas seam, the render loop's offscreen/interactive
      split, `close_keys`/`on_frame`, and an honest note that a
      second-renderer seam (as opposed to the existing second-*canvas*
      seam) has not actually been built yet, distinct from `A2a`'s
      decision-support survey.
      *All three verified by:* re-read against their own stated purpose
      and cross-checked for overlap with neighbouring documents;
      `rendering.md` specifically checked against the real
      `canvas.py`/`window.py` source, not written from the `CLAUDE.md`
      summary alone. `docs/repository-manifest.md` (⬜->🟩 for all
      three, since each describes something that already exists, unlike
      `engine.md`/`icds.md`'s necessarily forward-looking content) and
      `docs/architecture/CLAUDE.md` updated in the same change. `make
      docs`/`make ci` clean after.

### E8 — Prompt feature contexts (4 files, KA-040..043)

**Done 2026-08-17**, before E3 and E4 as planned -- `handbook.md` is
precisely the brief those sixteen handbook entries should be written
against. KA §20's "Agent support" completion criteria named these four
explicitly.

- [x] **E8a. `prompts/features/handbook.md`** (KA-040, done 2026-08-17).
      Writing guidance for Handbook entries: what the entry is for, what
      good coverage looks like, what to avoid (invented claims,
      restating project state), grounded in `docs/handbook/physics/
      README.md` and `docs/handbook/numerical-methods/CLAUDE.md` rather
      than duplicating them.
- [x] **E8b. `prompts/features/adr.md`** (KA-041, done 2026-08-17).
      Adds generation-specific guidance on top of `adr/README.md`'s
      structure -- notably, a caution to prefer project-specific
      reasoning over generic domain knowledge, citing `ADR-002`'s known
      gap (E12) as the concrete example of what goes wrong otherwise.
- [x] **E8c. `prompts/features/implementation-plan.md`** (KA-042, done
      2026-08-17). Explains what a task description needs (purpose,
      place in the project, dependencies, artifacts, implementation
      approach, verification, Definition of Done, upgrade implications)
      to be executable without conversation history, using
      `roadmap.md`'s existing TASK-000-onward structure as the working
      precedent. Complements rather than replaces
      `prompts/common/TEMPLATE.md`.
- [x] **E8d. `prompts/features/agents.md`** (KA-043, done 2026-08-17).
      The generated-prompt counterpart to the root `CLAUDE.md`'s
      "Maintaining CLAUDE.md Files" section: what a `CLAUDE.md` should
      contain, when to write real content instead of the generic
      placeholder, and what to avoid duplicating.
      *All four verified by:* re-read against their own Definition of
      Done and cross-checked for internal consistency; each references
      its authoritative source rather than restating it (P-011).
      `docs/repository-manifest.md` (⬜->🟨), the four KA-040..043
      `Status` fields (`planned`->`draft`), and `prompts/features/
      CLAUDE.md` updated in the same change.

### E3 — Numerical-methods handbook (10 files, KA-016..025)

**Done 2026-08-17.** Real domain content with citations, written against
`docs/handbook/numerical-methods/overview.md` (survey material) and each
other in the dependency order below -- not generated mechanically.

- [x] **E3a. `fvm.md`** (KA-016) -- written first, as planned. The
      already-decided method (`ADR-002`), and everything below depends on
      it conceptually.
- [x] **E3b. `meshes.md`** (KA-017)
- [x] **E3c. `variable-placement.md`** (KA-018)
- [x] **E3d. `fluxes.md`** (KA-019)
- [x] **E3e. `advection.md`** (KA-020)
- [x] **E3f. `diffusion.md`** (KA-021)
- [x] **E3g. `time-integration.md`** (KA-022)
- [x] **E3h. `pressure-velocity-coupling.md`** (KA-023)
- [x] **E3i. `linear-solvers.md`** (KA-024)
- [x] **E3j. `boundary-conditions.md`** (KA-025)
      *Verified by:* re-read each against its own KA Content Requirements
      and Definition of Done; `make ci` clean
      (`tools/validators/check_docs.py` confirms every relative link
      resolves). `docs/repository-manifest.md` (⬜->🟨 for all ten),
      KA-016..025 `Status` (`planned`->`draft`), and
      `docs/handbook/numerical-methods/CLAUDE.md` updated in the same
      change.

### E4 — Physics handbook (6 files, KA-010..015)

**Done 2026-08-17.** Same citation requirement, written against
`docs/handbook/physics/README.md` and each other in KA's own dependency
order.

- [x] **E4a. `incompressible-flow.md`** (KA-010) -- written first, as
      planned. The MVP's physical model.
- [x] **E4b. `heat-transfer.md`** (KA-011)
- [x] **E4c. `density.md`** (KA-012)
- [x] **E4d. `humidity.md`** (KA-013)
- [x] **E4e. `buoyancy.md`** (KA-014)
- [x] **E4f. `cloud-formation.md`** (KA-015) -- written last, per KA-015's
      own dependency list (depends on all four of the others).
      *Verified by:* re-read each against its own KA content and the
      `physics/README.md` "What Belongs in an Entry" checklist; `make ci`
      clean. `docs/repository-manifest.md` (⬜->🟨 for all six),
      KA-010..015 `Status` (`planned`->`draft`), `docs/handbook/
      physics/{README,CLAUDE}.md` updated in the same change.

These last four support Stage 6 rather than the MVP, but were written in
full rather than economised on -- Stage 0 did not need shortening.

### E5 — Handbook completeness

- [x] **E5. Bring `docs/handbook/numerical-methods/compatibility.md` up
      to KA-008's Definition of Done** (done 2026-08-17). Added "Kinds of
      Compatibility" (all seven relationships KA-008 names, each with a
      concrete example grounded in `overview.md`'s existing per-method
      entries -- e.g. FDM/FVM/FEM/Spectral as mutually exclusive
      alternatives, matching what `adr/ADR-002-fvm-first.md` actually
      decided between; PIC/FLIP as a hybrid *in itself* rather than a
      coupling of two solvers) and "Incompatibilities" (FDM↔SPH,
      FDM↔PIC/FLIP, Spectral↔SPH, LBM↔FEM -- each with the specific
      structural reason two methods don't share machinery to exchange
      information through, not just "rare" left unexplained).
      `docs/repository-manifest.md` (🟨->🟩) and KA-008's `Status`
      (`draft`->`complete`) updated in the same change.

      **Superseded in part, 2026-08-18.** This item originally recorded
      that "the existing pairwise graph and frequency grouping were kept
      as observed-practice-at-a-glance, not replaced." Both were removed
      on 2026-08-18 during the Handbook scientific-accuracy review. The
      reason is KA-008's own Content Requirements, which ask the document
      to distinguish seven relationships and say it "should not collapse
      these into one compatibility label" -- a frequency band is one such
      label, so keeping them was against the spec, independently of two
      of the entries also being wrong (FVM/SPH banded with FVM/FEM;
      "FEM ↔ Structural Mechanics" pairing a method with an application
      domain). They are replaced by a "Pairwise Relationships" table
      keyed to the seven kinds. Left recorded rather than rewritten, so
      the change of mind is visible.

### E6 — References (3 files)

**Done 2026-08-17.** Populated from what E3/E4's sixteen entries actually
cite, immediately after they were written.

- [x] **E6a. `docs/references/books.md`** -- fifteen books/monographs
      transcribed from every book citation across E3/E4.
- [x] **E6b. `docs/references/papers.md`** -- nine journal articles
      transcribed from E3's citations. No physics-entry paper citations
      yet (every physics citation is a book) -- recorded explicitly
      rather than left implicit.
- [x] **E6c. `docs/references/websites.md`** -- no web references were
      cited by any of the sixteen entries; the file records that
      explicitly (per A3, it cannot simply stay empty) rather than
      inventing one.
      *Verified by:* every citation cross-checked against the entry that
      cites it. `docs/repository-manifest.md` (⬜->🟨 for all three) and
      `docs/references/CLAUDE.md` (no longer the generic placeholder --
      also closes that item under E9 below) updated in the same change.

### E7 — Planning (1 file)

- [x] **E7. Write `docs/planning/releases.md`** (done 2026-08-17, decided
      write over retire). Records the current state (no release, version
      0.0.1, no process defined) as a deliberate deferral -- the same
      pattern already used for `CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`/
      `SECURITY.md` in Part II -- with three concrete trigger conditions
      (a first external consumer, reaching the MVP, or a maintainer
      decision to publish) rather than an open-ended "eventually".
      Retiring was considered and rejected: `docs/glossary.md` treats
      "Release" as one of three real progression concepts (alongside
      Stage and Capability Level), so deleting the file would leave a
      defined term with no supporting document -- an artificial gap, not
      a genuine simplification.
      `docs/repository-manifest.md` (⬜->🟨) and `docs/planning/CLAUDE.md`
      (no longer describes the file as empty) updated in the same
      change.

### E9 — Agent guidance (TASK-009, KA-038)

- [x] **E9. Fill the placeholder `CLAUDE.md` files** (closed 2026-08-19,
      under a revised *Done when* -- see below). 40 exist as of
      2026-08-19 (down from 43: `assets/icons/`, `assets/shaders/`,
      `assets/textures/` retired the same day, this item, on the same
      "nothing anywhere states what this is for" test that retired
      `tools/planner/`/`tools/scripts/`, E10; 43 itself down from 45 for
      that earlier retirement); **7 remain** the identical 121-byte
      generic text (down from 10, for the same reason; down from 29 as
      of 2026-08-15 -- Group C/D's work filled several in passing, as
      each one's own subject matter became known, not as a dedicated
      pass; most recently `adr/`, `planning/`, `planning/model/`,
      `planning/data/`, `tools/` and `tools/generators/`, all
      2026-08-17).
      Grouped by where the knowledge already exists, so none of these
      requires inventing anything:
      - [x] `adr/` -- **done 2026-08-17**, points at `adr/README.md`'s
            already-complete conventions rather than restating them
      - [x] `tests/` and `integration/` -- **done 2026-08-15 (C1a)**,
            with a real precedent (`test_cli.py`) to write the split
            against rather than a speculative rule.
      - [x] `unit/` -- **done 2026-08-16 (D1)**, written against
            `test_configuration.py`, the first real unit test.
      - [x] `golden/` -- **done 2026-08-16 (D5)**, written against
            `test_empty_window.py`; revised the same day once the
            public-API rule changed what the file describes.
      - [x] `performance/` -- still generic, and that's now correct
            under the revised *Done when* (below): the directory holds
            nothing but a bare `__init__.py`, so there is no content for
            the placeholder to fall short of. Write real guidance once
            its own first real test (a benchmark) sets a concrete
            precedent, not ahead of it -- but that is no longer what
            closing E9 waits on.
      - [x] `.github/` and `.github/workflows/` -- **done 2026-08-16
            (C2)**, written in the same change as `ci.yml`.
      - [x] `planning/`, `planning/model/`, `planning/data/` -- **done
            2026-08-17**, documenting the deliberate knowledge-graph
            deferral and that its unblock condition (Group E's handbook
            work) is now satisfied, pending a maintainer decision to
            start populating it
      - [x] `src/` and `src/pyflow/` -- **done 2026-08-16 (D4)**, written
            once there was real package-boundary content to document:
            the four subpackages plus `bootstrap.py`'s deliberate
            placement at the package root (the circular-import lesson).
      - [x] `tools/` and `generators/` -- **done 2026-08-17 (E10)**,
            alongside the docs-index generator: `generators/` documents
            `generate_docs_index.py`, and `tools/` itself now summarises
            both subdirectories' status instead of the generic text
            (later the same day, once `planner/`/`scripts/` were
            retired, rewritten again to describe two rather than four).
      - [x] `planner/`, `scripts/` -- **retired 2026-08-17 (E10)**, not
            filled -- no longer exist, so no longer part of this count
      - [x] `validators/` -- **done 2026-08-17**, written against
            `check_docs.py`; narrowed out of E10, see that item
      - [x] `examples/` and `golden-demos/` -- **done 2026-08-16 (D5)**,
            written against the demo directory's actual, final shape --
            `empty_window.yaml` (config), not the `empty_window.py`
            script D5 first landed with and the public-API rule later
            removed.
      - [x] `experiments/`, `tutorials/` (`examples/`) -- still generic,
            still nothing specific to write against, still correct under
            the revised criterion: both are named in TASK-000's closed
            acceptance criteria (documented architecture, not
            undocumented cruft), just not populated yet. Kept, not
            retired -- 2026-08-19 maintainer's call: distant timing is
            not the same test as "nothing states what this is for."
      - [x] `docs/references/` -- **done 2026-08-17 (E6)**, written
            against the three now-populated reference files.
      - [x] `docs/tutorials/` -- still generic, still correct: paired
            with `examples/tutorials/` above, same reasoning, kept.
      - [x] `assets/` and `assets/colourmaps/` -- still generic, still
            correct: content becomes known once field rendering needs
            colour maps (TASK-017), not yet. `assets/icons/`,
            `assets/shaders/`, `assets/textures/` **retired 2026-08-19**
            rather than filled -- unlike `colourmaps/`, no document
            anywhere (KA, roadmap, ADR, manifest) ever stated what any of
            the three was for; `docs/architecture/repository.md` and
            `docs/repository-manifest.md` updated in the same change.
      - [x] `physics/` (`src/pyflow/physics/`) -- still generic, still
            correct: nothing physics-specific exists yet beyond a
            docstring-only `__init__.py` to write against.
      *Done when* (revised 2026-08-19, maintainer's call): no
      `CLAUDE.md` remains generic **in a directory that has content** --
      not no placeholder anywhere in the repository. The original
      phrasing required inventing directory-specific documentation for
      directories that are still genuinely empty scaffolding, which
      produces speculation, not knowledge, and is exactly what this
      item's own per-directory notes above were already refusing to do
      one at a time (`performance/`, `experiments/`/`tutorials/`,
      `physics/`). The seven remaining placeholders all sit in
      directories with no real content -- verified directly, not
      assumed: each holds either nothing or a bare docstring-only
      `__init__.py` -- so E9 is closed under the revised criterion.
      Reopen it, for a specific directory only, the day that directory
      gets real content and its `CLAUDE.md` is still the generic text.
      (Phrased as *Verified by* until 2026-08-18, which is this
      backlog's convention for something already checked on a completed
      item -- misleading while the item was open. Use *Done when* for an
      acceptance criterion and *Verified by* only for what was actually
      run.)
      *Verified by:* `find . -name CLAUDE.md` cross-checked byte size
      against the known 121-byte placeholder text, for every tracked
      `CLAUDE.md` in the repository, 2026-08-19 -- 40 files, 7 generic,
      all 7 confirmed content-free by directory listing the same pass.

### E10-E12 — Loose ends

- [x] **E10. Give `tools/` a documented purpose, or retire it** (done
      2026-08-17). Originally four empty subdirectories (`generators/`,
      `planner/`, `validators/`, `scripts/`), no mention in the KA spec
      or roadmap, and nothing anywhere stating what belongs in any of
      them.
      **`validators/` narrowed out of this item 2026-08-17**: it now holds
      real content (`check_docs.py`, a broken-relative-link checker run
      via `make check-docs`/`make ci`) and its own documented `CLAUDE.md`
      -- see `docs/CHANGELOG-DESIGN.md`, 17-08-2026.
      **`generators/` also narrowed out, same day**: it now holds
      `generate_docs_index.py` (writes `docs/index.md`, the generated
      documentation navigation index) and its own documented `CLAUDE.md`.
      That settles what the earlier note here only speculated about --
      the generator turned out to produce the doc-navigation index, *not*
      `docs/repository-manifest.md` itself, so the separate Part II
      question ("should the manifest be generated?") is not resolved by
      this and remains genuinely open, now with a real precedent in
      `tools/generators/` to extend if it's ever decided yes.
      **`planner/` and `scripts/` retired, same day, maintainer's
      decision** -- both had sat empty since the repository's first
      commit with nothing anywhere stating what either was for, unlike
      `generators/`/`validators/`, which both earned real content the
      same day this was decided. Retiring rather than inventing a
      speculative purpose closes E10 fully and, in the same change,
      closes the `planner/`/`scripts/` line item under E9 (they're no
      longer part of that count -- see E9 above). `tools/CLAUDE.md`
      rewritten to describe two subdirectories, not four.

- [x] **E11. Add `README.md` development instructions** (done 2026-08-15,
      maintainer's request). A new Quick Start section: `make install`,
      then `demo`/`test`/`lint`/`ci`, and `clean` -- deliberately not
      duplicating what `clean` prints about what it can't remove, since
      that's exactly the kind of restated fact that drifts (points at
      running it instead). The stale "no Python source" claim in Project
      Status (left over from before B1) was also fixed in the same
      change -- found while touching the file, not a separate item.
      **New standing rule adopted alongside this** (maintainer's
      instruction): keep the Quick Start section current as functionality
      is added, in the same change that adds it -- recorded in
      `docs/practices.md`.
      *Verified by:* `make ci` run clean immediately after, confirming
      nothing in the change broke the thing it documents.

- [x] **E13. Add the development commands to the root `CLAUDE.md`**
      (done 2026-08-17). A new "Development Commands" section lists all
      eleven `Makefile` targets as one-line entries, explicitly
      instructing agents to use them rather than reverse-engineer the
      `Makefile` or call tools directly -- kept compact per KA-037's own
      Definition of Done, pointing at `README.md`/`backlog.md` for detail
      rather than restating it. `docs/repository-manifest.md` (🟨->🟩)
      and KA-037's `Status` (`draft`->`complete`) updated in the same
      change.

- [x] **E12. Review `adr/ADR-002-fvm-first.md` against the survey it now
      cites** (done 2026-08-17). Checked line by line against
      `docs/handbook/numerical-methods/overview.md`: no factual claim in
      the ADR -- FVM's strengths/weaknesses, or any alternative's
      rejection/deferral reasoning -- contradicts the survey. The one
      real gap was that the survey's own per-method "Suitability for
      PyFlow" verdicts and field-transport ratings (FVM rated ★★★★★ for
      both Heat and Scalar transport, and explicitly called "the
      strongest candidate for the primary PyFlow framework") were
      available but never cited -- the ADR's field-related rationale
      argued from ADR-003 composability instead of this more direct,
      project-specific evidence. Closed by adding a Positive-consequence
      bullet quoting that verdict directly, and a dated review note in
      the ADR's own Context section so the ADR carries its own review
      history rather than only the backlog carrying it.
      `docs/repository-manifest.md` (🟨->🟩) and KA-027's `Status`
      (`draft`->`complete`) updated in the same change. The matching
      Part III entry (§7, "KA `Status:` fields are stale across the
      board") is now fully resolved -- see that item.

---

## Group F — Close out and verify

- [x] **F1. Record the project's Git conventions** (closed 2026-08-19).
      Started as: `docs/practices.md` asserts Git is the primary
      historical record and step 7 of the session workflow is "commit
      changes", but nothing said anything about branch naming, commit
      granularity or message form. **Scope grew before execution**,
      maintainer's call: the same gap extends to what must pass before a
      commit, how branching/review will work as the project grows past
      one contributor, and tooling-dependency update cadence -- checked
      first that none of these already had a home (`docs/engineering-
      principles.md` is philosophy, not concrete rules; `.pre-commit-
      config.yaml` gates lint/typecheck only, not tests; neither said
      anything about branching or review), then covered all four in one
      change rather than only the narrowest original reading.
      - **Branch naming.** `master` -> `main`, renamed 2026-08-19. Free
        to do now (no remote, no collaborators, one branch); would cost
        real friction after a remote's default branch and any
        collaborator tooling already pointed at `master`. Every
        reference updated in the same change: `.github/workflows/ci.yml`
        (`push.branches`), `.github/workflows/CLAUDE.md`,
        `docs/repository-manifest.md`'s `.github/` section.
      - **Commit granularity and message form.** Recorded: one logical
        change per commit, imperative-mood summary line, body explains
        *why* not what.
      - **Commit gate.** Recorded and made explicit rather than an
        unstated habit: the git hook (`make install` -> `pre-commit
        install`) covers lint/typecheck/whitespace only, deliberately not
        the full suite (friction on small commits); `make ci` must be
        run and pass before any commit regardless, which was already
        this project's actual practice.
      - **Branching and review.** Recorded as deliberately not decided
        beyond "single branch, direct commit, no PRs" while single-
        developer, per KA-003's own content requirement to avoid
        multi-person process before there are multiple people -- same
        reasoning the `CONTRIBUTING.md` deferral (Part II) already uses.
        Trigger to revisit: a second contributor or a remote, whichever
        comes first.
      - **Tooling dependency update policy.** Recorded, generalising the
        existing Python version policy (periodic review, update when it
        benefits the project, verify Python-version compatibility before
        bumping) to `.pre-commit-config.yaml` hook revisions and
        `uv.lock`.
      All four written into `docs/practices.md`'s new "Version Control"
      section and a new "Tooling dependency update policy" subsection.
      `docs/repository-manifest.md` (🟨->🟩) and KA-003's `Status`
      (`draft`->`complete`) updated in the same change.
      *Verified by:* `make ci` clean after the branch rename and every
      doc edit.

- [x] **F2. Sweep the inventories for everything Stage 0 created --
      and, per maintainer's request 2026-08-19, the inverse: things the
      inventories record that no longer exist** (closed 2026-08-19).
      *(Gap found 2026-08-15.)* Stage 0 adds a substantial number of
      artifacts that neither `docs/repository-manifest.md` nor
      `docs/planning/knowledge-architecture.md` currently knows about.
      **Already added, as they landed rather than deferred to this
      sweep:** `ADR-004` and `ADR-005` (A2b/A2c),
      `docs/architecture/compute-and-rendering-stack.md` (A2a), `uv.lock`
      and `.python-version` (B2), the Makefile rewrite (B3), every Python
      module under `src/pyflow/` (B1), `tests/integration/test_cli.py`
      and the updated `tests/CLAUDE.md`/`tests/integration/CLAUDE.md`
      (C1a), the README Quick Start section (E11), the coverage
      configuration in `pyproject.toml` (C1b), and `.github/workflows/ci.yml`
      with its now-written `CLAUDE.md` files (C2), and D1-D4's real
      implementation -- `configuration/{schema,loader}.py`,
      `engine/logging_setup.py`, `rendering/{canvas,window}.py`,
      `bootstrap.py`, their tests, the `pyyaml`/`glfw` dependencies, and
      the `pygfx`/`rendercanvas` mypy override -- with `docs/repository-manifest.md`
      and every touched package's `CLAUDE.md` updated in the same
      changes, not deferred here. Also `examples/golden-demos/` and
      `tests/golden/test_empty_window.py` (D5),
      with `docs/repository-manifest.md`'s `examples/`/`tests/` sections
      and the `golden-demos/`/`tests/golden/`/`examples/` `CLAUDE.md`
      files updated the same way. Root `CLAUDE.md`'s development
      commands (E13) landed 2026-08-17 -- nothing left outstanding from
      this list. This item's real remaining job has narrowed to a final
      confirmation pass, not a backlog of unrecorded artifacts -- the
      standing rule in `docs/practices.md` (update both inventories
      together as artifacts land) has been followed throughout rather
      than deferred to here, which is what a working backstop should look
      like: mostly nothing left to catch by the time it's run.
      *Done when:* the link check and empty-file check both come back
      clean, and every ⬜ row corresponds to something genuinely not yet
      built. (Also relabelled from *Verified by* 2026-08-18 -- see E9.)

      **2026-08-19 sweep, both directions, method and results:**

      *Forward (disk -> inventories, F2's original scope).* Cross-checked
      all 159 tracked files against `docs/repository-manifest.md` and
      `docs/planning/knowledge-architecture.md`: every KA `Name:` path
      (43 entries) exists on disk except the one already struck through
      as never-created (KA-034); every `docs/`/`adr/`/`prompts/`
      Markdown file is named in the manifest (directly or via its
      `task-*.md` glob row); every root config file is covered.
      **One real gap found:** `.claude/settings.json` and
      `.claude/hooks/post_edit_format.py` existed with real content
      (present since early Stage 0 -- `.claude/settings.json` predates
      most of Group D) but were in neither inventory, and neither
      directory had a `CLAUDE.md` at all, despite the root `CLAUDE.md`'s
      collective rule (KA-038) requiring one everywhere. Nothing ever
      prompted a Blast Radius check on it because no backlog item ever
      created it -- it came from Claude Code tooling setup, not a
      tracked task, which is exactly the blind spot a sweep like this
      exists to catch. Fixed: `.claude/CLAUDE.md` and
      `.claude/hooks/CLAUDE.md` written, both real content; a new
      `# .claude/` section added to `docs/repository-manifest.md`,
      🟩. Not itemised in `docs/planning/knowledge-architecture.md`,
      same treatment as `tools/`/`assets/` (KA doesn't enumerate every
      directory the project ends up wanting). CLAUDE.md-file counts
      updated everywhere they're restated (42 files, up from 40; 35 real
      content, up from 33; 7 placeholder, unchanged) --
      `docs/repository-manifest.md`'s CLAUDE.md-files section and
      `docs/planning/roadmap.md`'s TASK-009 row.

      *Inverse (inventories -> disk, added to scope 2026-08-19,
      maintainer's request).* Checked every path either inventory names
      for existence on disk: **zero false claims of existence found** --
      every full-path mention in the manifest that looked missing on a
      first automated pass turned out to be either a genuine naming
      pattern (`adr/ADR-00N-title.md`), a relative-path fragment matched
      out of context (`golden-demos/empty_window.yaml`, correctly meaning
      `examples/golden-demos/empty_window.yaml`), or a claim already
      correctly phrased as *absence* (`docs/handbook/README.md` and
      `numerical-methods/README.md` -- the manifest already says "There
      is no..." for both).

      **A different kind of inverse mismatch was found, not covered by
      "does the file exist": KA `Status:` fields disagreeing with the
      manifest's own status symbol for the same file.** Both inventories
      track the same artifacts from different angles (Blast Radius,
      `docs/practices.md`), so this is a real instance of the failure
      mode that section warns about, just not a missing-file one. Found
      by cross-referencing every KA entry's `Status:` against the
      manifest row for the same path:
      - **`README.md`** -- manifest 🟩, KA-001 `draft`.
      - **`docs/implementation/golden-demos.md`** -- manifest 🟩, KA-035
        `draft`. Worth a closer look before resolving either way: KA-035's
        own "Initial golden demo" text still describes "a 2D air-current
        simulation... produces measurable velocity fields" -- the
        ambition that predates Stage 0's actual first golden demo, Empty
        Window (D5), which does neither. The KA entry's *content*, not
        just its `Status:` label, may be stale relative to what Stage 0
        actually chose to build first.
      - **`docs/handbook/numerical-methods/compatibility.md`** -- KA-008
        `complete`, manifest 🟨 (the reverse direction: KA ahead of the
        manifest here).
      Most of the remaining 36 KA entries at `draft` are genuinely
      consistent with a manifest 🟨 on the same row (both mean the same
      thing: real content, not yet reviewed as satisfying its own
      Definition of Done) -- not touched, not a finding. **Not resolved
      here, deliberately:** flipping any of the three above requires
      reading the specific document against its own KA Definition of
      Done and making a content judgement, the same kind of work E12 did
      for `ADR-002`/KA-027 -- mechanically syncing the label to make the
      two inventories agree would risk manufacturing a second layer of
      inaccuracy on top of the first. Left as a **new candidate for Part
      II** (added below) rather than guessed at under F2's sweep.

      *Empty-file check:* clean -- the eleven `planning/**.yaml` files
      are the only tracked files with zero bytes, exactly A3's carve-out.
      *Link check:* clean (`make check-docs`).
      *Verified by:* `make ci` clean after every change in this sweep;
      `find . -name CLAUDE.md` cross-checked against
      `docs/repository-manifest.md`'s restated count.

- [x] **F3. Run the Stage 0 exit audit** (closed 2026-08-19). **Result:
      eight of nine criteria fully met; criterion 8 (CI executing on a
      real runner) deliberately open, same reason and trigger condition
      recorded since 2026-08-16 -- not a gap this audit discovered, a
      confirmation the existing accounting was accurate.** Full
      per-criterion record written directly into `docs/planning/roadmap.md`'s
      Stage 0 Completion Criteria section (a new "Exit audit" subsection)
      rather than duplicated here, per P-011 -- that document already
      states what each criterion means, so the audit result belongs next
      to it. Two things verified for real rather than re-asserted from
      old evidence: a genuinely fresh `git clone` (not the in-place
      `make clean`/`make install` cycle B2 originally ran) succeeded
      through `make install`, `make ci` (64 tests), and `pyflow run`
      opening a real window -- criteria 6 and 9's strongest evidence to
      date. `assets/`'s manifest row was found still ⬜ against
      criterion 3's literal check and explicitly carved out (same terms
      as the `planning/**.yaml` graph) rather than either ignored or
      papered over with speculative content -- see the A3 note above and
      `docs/repository-manifest.md`'s `assets/` section.
      Original per-criterion evidence mapping follows, preserved as the
      record of where each criterion's evidence came from at the time
      this item was written:
      1. TASK-000..010 acceptance criteria — B1, B2, B3, C1a, C1b, C2,
      criteria and where their evidence comes from:
      1. TASK-000..010 acceptance criteria — B1, B2, B3, C1a, C1b, C2,
         D1-D4, plus TASK-008 (Group E) and TASK-009 (E9, E13)
      2. All engineering tooling operational — A1a, A1b, B2, B3, B4,
         C1a, C1b, C2
      3. Documentation has a complete first draft — A3's condition, now
         settled: no file tracked in the manifest is empty. Group E
         exists to satisfy this and its items map one-to-one onto the
         files, so the check is: every ⬜ row in
         `docs/repository-manifest.md` has become 🟨/🟩 or has been
         removed, and the eleven `planning/**.yaml` files are the only
         empty tracked files remaining (carved out by A3).
      4. Repository structure reflects the intended architecture — B1,
         E1a, E1b, E2, E10
      5. Coding agents have contextual guidance throughout — E9, E13
      6. A developer can clone and begin Stage 1 immediately — B2's clean
         clone check, plus A2c (TASK-011 cannot start without an array
         library) and E1b (Stage 3 has nothing to build against without
         ICDs)
      7. The engine bootstraps into an empty rendering window — D4,
         and D5 delivers the Capability Level 0 golden demo that proves
         it in regression testing
      8. CI executes — C2, demonstrated by a green run, not merely by a
         workflow file existing
      9. Stage 0 infrastructure is reproducible — B2's `uv.lock` and the
         clean-clone check, with A1b's setup documented in `README.md`
         (E11)
      Update `roadmap.md`'s Stage 0 status table and
      `docs/repository-manifest.md` as part of this, and record the
      outcome in `docs/CHANGELOG-DESIGN.md`.

---

# Part II — Deferred beyond Stage 0

Not blocking, not forgotten. Each has a stated reason and, where it
exists, an unblock condition.

- [ ] **Decide Capability Level 7's fate.** Level 7 (Additional Numerical
      Frameworks -- SPH/FLIP/PIC) has no corresponding roadmap Stage, so
      the implementation plan's "Dam Break / Free Surface" golden demo is
      unreachable from the roadmap. Both documents record this explicitly
      and mark it unscheduled, so nothing is misleading in the meantime.
      Resolving it means adding a Stage or dropping the Level -- both
      real scope changes, and neither is needed to reach Stage 0.

- [ ] **Decide whether `docs/repository-manifest.md` should be generated
      rather than hand-maintained.** Under P-002 a file inventory with
      statuses is an obvious generation candidate, and hand-maintenance
      has already failed once -- v0.1 drifted far enough to describe ~35
      handbook files that never existed. The 2026-08-15 rewrite made it
      accurate; it did not answer this. Still open after 2026-08-17: that
      date added `tools/generators/generate_docs_index.py` and
      `docs/index.md`, a generated *navigation* index, but the decision
      made alongside it was explicitly to keep navigation separate from
      the manifest's *status-table* purpose (single primary purpose per
      doc, `docs/documentation-guidelines.md`) rather than fold one into
      the other -- see `docs/CHANGELOG-DESIGN.md`, 2026-08-17. So this
      question is unchanged in substance, but no longer blocked on
      whether `tools/generators/` is a workable place for a generator to
      live -- it demonstrably is now. *Unblock condition:* worth settling
      before the manifest drifts a second time; the pattern to follow, if
      the answer is yes, already exists in `tools/generators/`.

- [ ] **`planning/model/*.yaml` and `planning/data/*.yaml`** -- the
      machine-readable knowledge graph. Eleven empty files. Deferred
      because populating the graph is downstream of having real handbook
      and ADR content to populate it with. Explicitly exempt from A3's
      no-empty-files condition, as data rather than documentation.
      *Unblock condition:* Group E's handbook work landing -- **now
      satisfied**: E3 (numerical-methods handbook, 10 files) and E4
      (physics handbook, 6 files) both landed 2026-08-17. Populating the
      graph is no longer blocked on missing source content; starting it
      is a maintainer scheduling decision, not a technical one.

- [ ] **`CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `SECURITY.md`** --
      none exist and none is referenced. A conscious deferral for a
      single-developer project, reaffirmed 2026-08-15, not an oversight.

- [ ] **File-structure pruning pass** -- a dedicated pass to remove
      files and directories that turn out not to be needed, once scope is
      clearer, rather than ad hoc deletion during other work.
      `prompts/common/task-prompts-subdir-agents-md.md` (superseded,
      never executed) is a first candidate; E2 may produce more. E7 did
      not produce one -- `releases.md` was kept, written rather than
      retired. E10 resolved its own candidate directly (`tools/planner/`,
      `tools/scripts/`, retired 2026-08-17) rather than deferring it
      here, since E10 already asked exactly that question for those two
      directories specifically. Note that this repository has no general
      keep-don't-delete convention -- the only such rule is the narrow
      one in `prompts/common/CLAUDE.md` about completed `task-*.md`
      prompts.

- [ ] **Handbook README asymmetry.** `docs/handbook/physics/` has a
      structural `README.md` (KA-009); `docs/handbook/numerical-methods/`
      and `docs/handbook/` itself do not. No longer a divergence -- the
      manifest no longer claims otherwise -- just an open structural
      choice, and `overview.md` partly serves the role already.

- [ ] **`docs/planning/dependency-tree.md`: hand-maintained or derived?**
      It is currently hand-maintained. Whether it should instead be
      derived from Engine Architecture / ICDs is now answerable -- E1a/E1b
      landed 2026-08-17 -- but not answered here; it's the maintainer's
      call, not something to resolve by fiat while writing the document
      the question depends on. Worth noting when it is decided: the two
      documents' structures currently disagree (see `engine.md`'s
      "Relationship to Other Architecture Documents"), so "derive" would
      mean picking one shape, not just automating the existing one.

- [ ] **Demo selection, and a "run and watch" GUI for demos (and maybe
      tests).** Two related ideas from the maintainer, 2026-08-16, both
      explicitly deferred to the same trigger point. (1) A way to select
      among golden demos without needing to know a config file's path --
      something like `pyflow run --demo empty-window` resolving to the
      right config under `examples/golden-demos/`, rather than always
      spelling out `--config examples/golden-demos/empty_window.yaml`.
      (2) A GUI for the "issue a command, wait, see the result" pattern
      demos already are, and tests possibly later -- pick a demo from a
      dropdown, run it, watch it. Maintainer's own framing: "when we have
      a second Golden Demo we could add a dropdown to select between
      them." *Unblock condition:* a second golden demo existing -- with
      only one, there is nothing to select between, and both ideas would
      be built against a guess at the real shape of the choice rather
      than the choice itself.

- [ ] **KA `Status:` field reconciliation pass.** *(Gap found 2026-08-19,
      F2.)* Three concrete mismatches between `docs/planning/
      knowledge-architecture.md`'s per-entry `Status:` and
      `docs/repository-manifest.md`'s status symbol for the same file:
      `README.md` (manifest 🟩, KA-001 `draft`), `docs/implementation/
      golden-demos.md` (manifest 🟩, KA-035 `draft` -- and KA-035's own
      "Initial golden demo" text may itself be stale, still describing a
      full 2D air-current simulation rather than Empty Window, Stage 0's
      actual first golden demo), and `docs/handbook/numerical-methods/
      compatibility.md` (KA-008 `complete`, manifest 🟨, the reverse
      direction). Not resolved by F2 -- each needs the document read
      against its own KA Definition of Done, the same judgement E12
      applied to `ADR-002`/KA-027, not a mechanical label sync that risks
      papering over which side is actually right. The other ~33 `draft`
      KA entries were checked too and are genuinely consistent with a 🟨
      manifest row on the same document -- not part of this item.

---

# Part III — Audit history

Preserved as the record of what was found and what was done about it.
Everything still outstanding here has been promoted into Part I or
Part II; work from those, not from this section.

- **§§1-4** -- pre-Stage-0 checklist, snapshot taken 2026-08-12 and
  worked through on 2026-08-15.
- **§§5-12** -- full repository review, 2026-08-15, taken after that work
  landed. Covers execution status, inventory accuracy and cross-document
  consistency.

A self-consistency pass was run over §§7-12 later the same day, ahead of
the repository's first commit: every finding that was a divergence
between documents, or the same thing defined in two places, was fixed;
everything requiring new content, new code, or a scope decision was
carried into Parts I and II above. `docs/CHANGELOG-DESIGN.md` records
what was changed and why.

## 1. Resolve structural inconsistencies (blocking -- do first)

- [x] **Duplicate glossary** (resolved 2026-08-15): `knowledge-architecture.md`
      KA-005 already settles the canonical path as `docs/glossary.md` --
      not actually an open question, just not followed yet. Moved the
      475-line `docs/planning/glossary.md` content there (overwriting the
      16-line stale stub), first folding in three terms that existed only
      in the stub and nowhere in the 475-line version (Feature, Golden
      Demo, Thin Slice) so nothing was lost. `docs/planning/glossary.md`
      no longer exists.
- [x] **Stale `docs/handbook.md`** (resolved 2026-08-15, maintainer
      decision): retired. Every section (Vision, Engineering Principles,
      Planning Philosophy, Release Strategy, Accepted ADRs, Open
      Questions) was superseded elsewhere (root `CLAUDE.md`,
      `docs/practices.md`, `roadmap.md`, `adr/`, this backlog) and it also
      collided in name with the KA spec's *different* planned Handbook
      (Physics + Numerical Component reference, not project meta --
      `docs/repository-manifest.md`'s existing `docs/handbook/` section
      already correctly describes that future structure, so no manifest
      fix was needed there). `README.md`'s "Where to Start" list updated
      to point at current docs instead.
- [x] **Two competing implementation plans** (resolved 2026-08-15,
      maintainer decision: "roadmap = execution, plan = vision"):
      `roadmap.md` is now authoritative for concrete task execution
      (Purpose/Dependencies/Artifacts/Acceptance-Criteria per task);
      `implementation-plan.md` is the long-range vision reference (MVP
      Definition, Capability Levels, Upgrade Paths) and had its redundant,
      mostly-unfilled Task Index/template section removed, replaced with a
      scope note pointing to `roadmap.md`. While reconciling, found and
      fixed a real bug: `roadmap.md`'s Stage 1+ task IDs collided with
      Stage 0's (e.g. `TASK-001` meant both "Development Environment" and
      "Coordinate System") -- renumbered Stage 1 onward to continue from
      `TASK-011`, globally unique now. See `docs/CHANGELOG-DESIGN.md` for
      the full mapping.
- [x] **`docs/repository-manifest.md`** `docs/handbook/` vs flat
      `docs/handbook.md` (resolved 2026-08-15): moot now that
      `docs/handbook.md` is retired (see above) -- the manifest's
      `docs/handbook/` section was already correct as the future-state
      description, nothing to change.
- [x] **`docs/planning/backlog.md`** (this file) wasn't described anywhere in
      the manifest or knowledge-architecture doc before now -- add it to the
      manifest as a tracked artifact. (Done 2026-08-15 in the manifest
      v0.2 rewrite; it has a row under `docs/planning/`. It still has no
      KA entry -- the KA spec predates this file -- which is acceptable:
      KA specifies planned knowledge artifacts, and the backlog is a
      working record rather than one of them.)
- [x] **TASK-000 package structure mismatch** (resolved 2026-08-15,
      maintainer decision: actual should match roadmap): removed
      `interaction/`, `io/`, `simulation/`, `util/` from `src/pyflow/` --
      all four were undocumented stubs with zero content and zero
      explanation anywhere for why they existed or how "simulation"
      differed from "engine". Added `configuration/` per TASK-005. Folded
      the removed packages' presumed responsibilities into the packages
      that already existed: `io`/`simulation`/`util` -> `engine/`
      (state I/O, the run-loop, shared utilities all sit with the core
      engine for now); `interaction` -> `rendering/` (input/camera control
      belongs with the interactive visualisation it drives). Documented
      this in both packages' `CLAUDE.md` so it isn't silently forgotten
      again. `demos/` was not created under `src/pyflow/` -- `examples/`
      already serves that role at the repo root, just under a different
      name. That naming difference (`examples/` vs. roadmap's `demos/`)
      was not part of the decision asked and is left open below.
- [x] **`examples/` vs. roadmap's `demos/` naming** (resolved 2026-08-15,
      maintainer's call): kept `examples/` -- it's the better umbrella
      term, since it holds `golden-demos/`, `experiments/`, and
      `tutorials/`, not only demos. Updated TASK-000's implementation text
      in `roadmap.md` to say `examples/` instead of `demos/`, and to
      clarify which packages are `src/pyflow/` subpackages vs. top-level
      repository directories (that distinction wasn't explicit before).
- [x] **Prompt directory layout mismatch** (found 2026-08-15, fully
      resolved same day): `knowledge-architecture.md` §17 (KA-039..043)
      specifies `prompts/global/project.md` (durable project-wide context)
      and `prompts/features/{handbook,adr,implementation-plan,agents}.md`
      (per-artifact-kind context). The actual repo instead had
      `prompts/code/` and `prompts/docs/` (empty, no KA basis -- an earlier
      task prompt had inferred a code/docs split from the directory names
      alone, not from the spec text). Decision: follow the KA spec.
      Scaffolded `prompts/global/` and `prompts/features/` with `CLAUDE.md`
      files plus a new `prompts/CLAUDE.md` index.
      Two follow-on decisions closed this out fully: (1) **BRIEF vs.
      project.md** (maintainer's call: retire BRIEF into project.md) --
      wrote `prompts/global/project.md` per KA-039, cutting BRIEF's
      "Current Direction" section entirely rather than carrying it over
      (it nearly duplicated `implementation-plan.md`'s MVP Numerical
      Framework section almost verbatim -- one authoritative home is
      enough). Deleted `prompts/common/BRIEF`. (2) **`prompts/code/` and
      `prompts/docs/` fate** (maintainer's call: retire) -- deleted both;
      neither ever held content and neither corresponds to anything in
      the KA spec. `prompts/features/{handbook,adr,implementation-plan,
      agents}.md` themselves still remain unwritten -- that's a separate,
      lower-priority gap (§3), not blocked on anything above.
- [x] **`AGENTS.md` not read by Claude Code** (found and resolved
      2026-08-15): confirmed via the official Claude Code docs that it
      reads `CLAUDE.md` only, never `AGENTS.md`, at any directory level --
      the entire per-directory local-context design (every directory
      having its own instructions file) was invisible to it. Resolved by
      renaming all 45 `AGENTS.md` files to `CLAUDE.md` repo-wide (plain
      rename chosen over the `@AGENTS.md`-import pattern Claude's own docs
      suggest for repos that already use `AGENTS.md`, since this repo has
      no other AGENTS.md-reading tool in its workflow) and updating every
      textual reference across the living docs (KA spec, roadmap,
      manifest, this backlog, prompt templates). `docs/CHANGELOG-DESIGN.md`
      is an append-only log and was deliberately left untouched -- entries
      dated before 2026-08-15 still say "AGENTS.md" because that was
      accurate at the time. See that file for the full decision record.

## 2. Tooling / plumbing (empty despite being assumed by Stage 0 / TASK-001)

- [x] `LICENSE` -- BSD-3-Clause, chosen 2026-08-15 (maintainer decision;
      matches the scientific-Python ecosystem norm -- NumPy/SciPy/
      Matplotlib all use this family)
- [x] `pyproject.toml` -- written 2026-08-15. Python >=3.12, hatchling
      build backend (src-layout, `packages = ["src/pyflow"]`), `uv`
      dependency groups (`[dependency-groups] dev = [...]`, PEP 735 --
      verified this is uv's current convention, not the older
      `[tool.uv.dev-dependencies]`), Ruff + MyPy + PyTest config sections
      per `roadmap.md` TASK-001. No runtime dependencies yet (Stage 0 has
      none). **Caveat**: `uv` is not installed in this environment, so
      `make install`/`make test` could not actually be run end-to-end --
      TASK-001's acceptance criterion is unverified, not confirmed.
- [x] `Makefile` -- written 2026-08-15, all TASK-002 targets (install,
      lint, format, typecheck, test, docs, demo, clean). `docs`/`demo`
      are no-op placeholders (nothing to build/run yet). **Known gap**:
      `make test` will likely exit non-zero right now (pytest exits 5 on
      zero collected tests, and `tests/` has none yet) -- expected to
      resolve once TASK-003 (smoke tests) lands, not a mistake in this
      file, but flagging so it doesn't look like silent success.
- [x] `.pre-commit-config.yaml` -- written 2026-08-15. Hook versions
      verified directly against each repo's GitHub tags via the API
      (not guessed from training-data memory): `pre-commit-hooks` v6.0.0,
      `ruff-pre-commit` v0.16.3, `mirrors-mypy` v2.3.1. Not yet exercised
      against real source (none exists).
- [x] `.editorconfig` -- written 2026-08-15
- [x] `.gitignore` -- written 2026-08-15
- [x] `.gitattributes` -- written 2026-08-15, normalizes line endings
      going forward (`* text=auto eol=lf`). Did not itself rewrite the
      existing CRLF files -- `docs/planning/dependency-tree.md` was
      converted the same day (see §3). When asked to fix the remaining
      two flagged files (`CHANGELOG-DESIGN.md`, `adr/README.md`), a
      repo-wide check found the original audit had significantly
      undercounted: 10 more `.md` files also had CRLF endings
      (`adr/ADR-001-knowledge-graph.md`,
      `docs/documentation-guidelines.md`, `docs/engineering-principles.md`,
      `docs/glossary.md`, `docs/planning/capability-map.md`,
      `docs/planning/dreams.md`, `docs/planning/implementation-plan.md`,
      `docs/planning/numerical-frameworks.md`, `docs/practices.md`,
      `README.md`). Converted all of them (content verified unchanged,
      line-ending-only diffs). Repo-wide check after conversion found
      zero remaining CRLF `.md` files.
- [ ] `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `SECURITY.md` -- none exist,
      not referenced anywhere. Not urgent solo pre-Stage-0, but noted as a
      conscious deferral rather than an oversight

## 3. Knowledge/content gaps (dependency order per knowledge-architecture.md S19)

- [x] ADR-002 -- FVM-first (resolved 2026-08-15): written at
      `adr/ADR-002-fvm-first.md`, following the real `adr/` convention
      (3-digit, per `adr/README.md`) rather than KA-027's unfollowed
      `docs/adr/ADR-0002-*.md` path -- same precedent as ADR-001. Content
      -- alternatives (FDM/FEM/spectral/LBM/SPH), rationale, consequences
      -- drafted from standard, well-established CFD domain knowledge
      (maintainer's call, citing Versteeg & Malalasekera), not from
      project-specific reasoning that was never recorded anywhere. Review
      before treating the rationale as authoritative.
- [x] ADR-003 -- Modular numerical strategies (resolved 2026-08-15):
      written at `adr/ADR-003-modular-numerical-strategies.md`, grounded
      in the project's own already-stated "Replaceable Components"
      principle rather than invented reasoning.
- [x] Physics Handbook, structure decision (resolved 2026-08-15): not
      actually an open decision -- `knowledge-architecture.md` KA-009
      through KA-015 already specify exact filenames
      (`docs/handbook/physics/{README,incompressible-flow,heat-transfer,
      density,humidity,buoyancy,cloud-formation}.md`), just never
      followed. Scaffolded all seven at the correct path; wrote a real
      `README.md` (structural/organisational, not physics domain
      content); removed the old `docs/physics/{atmosphere,fluids,
      thermodynamics}.md` (all three were 0 bytes, nothing lost, and
      didn't match KA's topic list anyway).
- [x] Physics Handbook, content -- promoted into Part I as E4; written
      there 2026-08-17. See E4.
- [x] Numerical Component Handbook, structure decision (resolved
      2026-08-15): same situation as the Physics Handbook -- KA-016
      through KA-025 already specify
      `docs/handbook/numerical-methods/{fvm,meshes,variable-placement,
      fluxes,advection,diffusion,time-integration,
      pressure-velocity-coupling,linear-solvers,boundary-conditions}.md`.
      Scaffolded all ten.
- [x] Numerical Component Handbook, content -- promoted into Part I as
      E3; written there 2026-08-17, `fvm.md` first as planned. See E3.
- [x] `docs/architecture/overview.md`, `rendering.md`, `repository.md` --
      promoted into Part I as E2; written there 2026-08-17. See E2.
- [x] `docs/architecture/engine.md` gap (resolved 2026-08-15): KA-029
      specifies this as its own file, distinct from `overview.md` --
      scaffolded as an empty stub. See `docs/architecture/CLAUDE.md`.
- [x] `docs/planning/dependency-tree.md` formatting (resolved 2026-08-15):
      converted to LF, wrapped in a fenced code block, removed the
      pasting-artifact blank line between every tree line (kept every
      actual node and connector character unchanged -- verified same
      node set: Mesh, Field Storage, Numerical Operators, Advection,
      Diffusion, Gradient, Divergence, Sources, Pressure Coupling, Linear
      Solver, Time Integration, Rendering). Formatting only -- whether
      this should stay hand-maintained or become derived from Engine
      Architecture/ICDs is still open, noted in `docs/planning/CLAUDE.md`
      rather than decided here.
- [x] Interface Contract Definitions (ICDs) (resolved 2026-08-15): KA-030
      specifies `docs/architecture/icds.md` -- scaffolded (empty stub;
      content not written, depends on Engine Architecture which doesn't
      exist yet either).
- [x] MVP Definition (resolved 2026-08-15, maintainer's call: extract per
      KA): `docs/planning/knowledge-architecture.md` KA-031 specifies
      `docs/implementation/mvp.md` as its own artifact, not a section
      inside `implementation-plan.md` (which is where this morning's
      earlier reconciliation had briefly left it). Extracted, using
      KA-031's structure with the richer existing category breakdown
      folded in.
- [x] Upgrade Paths (resolved 2026-08-15, same call): this item's own
      premise was stale -- Upgrade Paths already existed, inside
      `implementation-plan.md`, just not as a standalone artifact and
      covering only 5 of KA-032's 12 categories. Extracted to
      `docs/implementation/upgrade-paths.md` per KA-032, expanded to all
      12 categories, and one internal inconsistency fixed in the
      process: the old Pressure-Velocity Coupling chain ("Projection ->
      SIMPLE -> PISO") implied PISO was the most-advanced target, but the
      MVP already starts at PISO -- corrected to follow KA-032's framing
      instead.
- [x] Golden Demo specification (resolved 2026-08-15): KA-035 specifies
      `docs/implementation/golden-demos.md`, not somewhere under
      `examples/golden-demos/` as the original note assumed. Written,
      using KA-035's own content (initial demo requirements, Definition
      of Done) plus a cross-reference to `docs/implementation/mvp.md`.
      `examples/golden-demos/CLAUDE.md` updated to point to it and
      clarify the spec/implementation split. Runnable demo code still
      doesn't exist -- that's separate, later work, blocked on the MVP
      itself existing.
- [x] `docs/references/books.md`, `websites.md`, `papers.md` -- promoted
      into Part I as E6; populated there 2026-08-17 once the Handbook
      content (E3/E4) it was blocked on existed. See E6 for the outcome.
- [x] `docs/planning/releases.md` -- promoted into Part I as E7; written
      there 2026-08-17. See E7 for the outcome.
- [x] `prompts/code/` and `prompts/docs/` (resolved 2026-08-15): retired --
      see the "Prompt directory layout mismatch" item in §1. Both
      directories are deleted. `prompts/common/task-prompts-subdir-agents-md.md`
      (the task prompt that would have added CLAUDE.md here) remains,
      marked superseded rather than deleted -- see that file, and the
      §4 file-structure pruning pass item.

## 4. Process

- [ ] Whenever a document above is filled in, update its nearest `CLAUDE.md`
      with concrete guidance on how/when to maintain that file (standing
      rule as of 2026-08-12)
- [ ] Record that rule itself in `docs/practices.md`
- [ ] Add a fresh entry to `docs/CHANGELOG-DESIGN.md` once this cleanup pass lands
- [ ] `planning/model/*.yaml` and `planning/data/*.yaml` -- intentionally
      deferred, not a current gap. Revisit only once enough handbook/ADR
      content exists to populate the graph meaningfully.
- [ ] **File-structure pruning pass** (raised 2026-08-15): a dedicated
      pass to remove files/directories that turn out not to be needed,
      once scope is clearer -- not ad hoc deletion in the middle of other
      work. `prompts/common/task-prompts-subdir-agents-md.md` (superseded,
      never executed -- see that file) is a first candidate. Raised in
      response to a mistaken claim, corrected the same day, that this repo
      has a general keep-don't-delete convention; it doesn't -- the only
      actual rule is the narrower one in `prompts/common/CLAUDE.md` about
      completed `task-*.md` prompts specifically.

---

# Second Audit -- 2026-08-15 (full repository review)

Sections 1-4 above are the 2026-08-12 pre-Stage-0 checklist, worked
through on 2026-08-15. This section is a *fresh* full-repository review
taken after that work landed, covering everything -- not only the items
the first audit had listed. Several findings below are things the first
audit did not look for, so they are new rather than regressions.

Headline: the repository's *planning* layer is in good shape and the
documents written on 2026-08-15 are genuinely coherent. Its *execution*
layer is further behind than the closed checkboxes above suggest, and the
two documents that declare themselves authoritative inventories are the
two most out of date with reality.

## 5. Version control (blocking, highest priority)

- [x] **The repository has zero commits** (resolved 2026-08-15: initial
      commit made after the self-consistency pass, 118 files, on branch
      `master`). Original finding follows. Every file in the project was
      untracked (`git log` is empty, `git status` shows the entire tree as
      `??`). This is the single largest risk in the repository and it
      contradicts the project's own stated foundations:
      `knowledge-architecture.md` KA-003 requires "use Git as the primary
      historical record"; `docs/practices.md` Session Workflow step 7 is
      "Commit changes"; P-001 says knowledge should never depend on
      individual memory. Right now the entire design phase -- including
      the whole 2026-08-15 reconciliation and its decision record --
      exists only as working-tree files on one machine, and
      `docs/CHANGELOG-DESIGN.md` is doing the job Git was supposed to do.
      Make an initial commit before any further work. Everything else in
      this section is secondary to it.
- [x] **`.gitattributes` normalisation is untested** (verified
      2026-08-15 immediately after the initial commit). `git ls-files
      --eol` reports 82 files `i/lf w/lf` and 36 `i/none w/none` (the
      empty files); zero CRLF anywhere in the index or working tree. The
      rule works.
- [x] **No branching/commit conventions are recorded anywhere.** Promoted
      to Part I, F1, and closed there 2026-08-19 -- `docs/practices.md`
      now has a Version Control section covering branch naming (renamed
      `master` -> `main`), commit granularity, message form, the commit
      gate and branching/review, plus a tooling dependency update
      policy. See F1's own entry for the full record.

## 6. Stage 0 execution status (the checkboxes above overstate it)

Sections 1-4 read as "nearly ready to begin Stage 0." Measured against
`roadmap.md`'s own Stage 0 acceptance criteria, most of Stage 0 has not
been started, and its *first* task is unmet despite §1 marking a
TASK-000-related item resolved. The §1 item was accurate for what it
claimed (it reconciled the *directory* layout); it did not create the
package, and nothing since has.

- [ ] **TASK-000 (Engine Skeleton) is not met.** There are **zero `.py`
      files in the repository** -- no `__init__.py` anywhere,
      `src/pyflow/` and its four subpackages contain nothing but
      `CLAUDE.md`. TASK-000's acceptance criteria ("the package imports
      successfully", "example application entry point executes") cannot
      pass. Two configured tools already depend on the package existing:
      `pyproject.toml` `[tool.hatch.build.targets.wheel] packages =
      ["src/pyflow"]` and `[tool.mypy] packages = ["pyflow"]`. So
      `make install` and `make typecheck` are both expected to fail
      today, in addition to `make test` (already flagged in §2).
- [ ] **TASK-003 (Automated Testing) not started.** `tests/` holds five
      `CLAUDE.md` files and nothing else -- no smoke tests, and no
      coverage configuration in `pyproject.toml` despite TASK-003 listing
      it as a produced artifact. This is the known cause of the `make
      test` exit-5 gap noted in §2; recording it here as its own task
      rather than a footnote.
- [ ] **TASK-004 (Continuous Integration) not started, and was not
      tracked anywhere.** `.github/workflows/` contains only a
      `CLAUDE.md` -- there is no workflow file. Stage 0's completion
      criteria require CI to execute -- criterion 8, which came from
      KA-034's Definition of Done when that entry was superseded (A4).
      It is a named criterion rather than an implied one precisely so
      that a workflow file which never runs cannot pass for it. This gap appeared in neither the first audit nor the
      manifest; the manifest and `roadmap.md`'s Stage 0 status table both
      record it as of 2026-08-15.
- [ ] **TASK-005 (Configuration), TASK-006 (Logging), TASK-007
      (Rendering), TASK-010 (Engine Bootstrap) not started and not
      tracked.** TASK-007 also carries an undecided question the roadmap
      states but never answers -- "select an initial rendering library" --
      which is an ADR-worthy choice (it determines the rendering
      subsystem's dependencies for the life of the project) and should
      not be settled inline during implementation.
- [ ] **TASK-008's Handbook artifact is unmet.** TASK-008 lists "Handbook"
      among its required first drafts and its acceptance criterion is
      "every core document exists and provides sufficient information."
      All 16 handbook entries are 0 bytes (§3 tracks the content gap; the
      point here is that Stage 0 *completion* is blocked on it, which the
      roadmap does not currently make visible).
- [ ] **Consequence:** the roadmap's Stage 0 Completion Criteria
      ("documentation has a complete first draft", "the engine
      successfully bootstraps into an empty rendering window") are a long
      way off. A per-task Stage 0 status table was added to `roadmap.md`
      on 2026-08-15 so this is legible without re-deriving it; keep it
      current. Treat §§1-4 above as "pre-Stage-0 hygiene", which is what
      they actually were, rather than as Stage 0 itself.

## 7. The two "authoritative inventory" documents disagree with the repo

**Resolved 2026-08-15** -- both documents now describe the repository
that exists, and each points at the other as the thing to update
alongside it. The findings are retained below as the record of what was
wrong, with the remaining open decisions (should the manifest be
generated? does ADR-002 survive review?) listed
as their own items.

Original assessment: both of these documents assert authority over the
repository's contents in their own text, and both are substantially wrong
about it. Under P-011 (single authoritative source) this is the most
damaging class of error in the repo: a reader who trusts either document
is misled.

- [x] **`docs/repository-manifest.md` is substantially stale** (rewritten
      2026-08-15 as v0.2 -- see the follow-up item below for the part that
      is *not* resolved). Every defect listed here was corrected against
      the actual tree; the 45 `CLAUDE.md` files are now covered by an
      explicit collective rule rather than being absent; the duplicated
      documentation Definition of Done was replaced by a reference to
      `docs/documentation-guidelines.md`. Original finding retained below
      as the record of what was wrong. It stated
      "every maintained file should appear here exactly once" and "this
      document is the authoritative inventory of repository knowledge."
      Actual state:
      - *Wrong paths*: `CHANGELOG-DESIGN.md` is listed at the root (it is
        in `docs/`); `implementation-plan.md`, `capability-map.md` and
        `dreams.md` are listed under `docs/` core (all three are in
        `docs/planning/`).
      - *Handbook section describes a structure that does not exist*: it
        lists `handbook/README.md`, `fem.md`, `fdm.md`, `spectral.md`,
        `lbm.md`, `sph.md`, and per-scheme files under Meshes / Variables
        / Operators / Time Integration / Pressure Coupling / Linear
        Solvers / Boundary Conditions / Physics subdirectories -- roughly
        35 files, none of which exist. The actual handbook (scaffolded
        2026-08-15 per KA-009..025) is flat: ten files in
        `numerical-methods/`, six plus a README in `physics/`. `fvm.md`
        is marked 🟨 Draft but is 0 bytes.
      - *Planning section*: lists `dependency-graph.md`,
        `milestone-roadmap.md` and `golden-demos.md`; the real files are
        `dependency-tree.md`, `roadmap.md`, and
        `docs/implementation/golden-demos.md` (written, but shown ⬜).
      - *Stale statuses*: `prompts/global/project.md` shown ⬜ though it
        was written 2026-08-15.
      - *Prompt features list* includes `documentation.md`, which is not
        one of KA-040..043's four (`handbook`, `adr`,
        `implementation-plan`, `agents`).
      - *An `engine/` section* describes a top-level directory that does
        not exist; the package is `src/pyflow/engine/`.
      - *Missing entirely*: `backlog.md` (already noted in §1),
        `roadmap.md`, `knowledge-architecture.md`,
        `numerical-frameworks.md`, `releases.md`, everything under
        `docs/architecture/`, `docs/implementation/`, `docs/references/`,
        `docs/handbook/physics/`, `adr/README.md`, and all of
        `planning/`, `src/`, `tests/`, `tools/`, `assets/`, `examples/`,
        the 45 `CLAUDE.md` files, and the four dotfile configs written on
        2026-08-15.
- [ ] **Follow-up (open): should the manifest be hand-maintained at
      all?** Under P-002 ("everything that can reasonably be generated
      should be generated") a file inventory with statuses is an obvious
      generation candidate, and hand-maintenance has already failed once.
      The 2026-08-15 rewrite made it accurate; it did not answer this.
      Decide before it drifts a second time. If the answer is "generate
      it," `tools/generators/` is presumably where that lives -- which
      would also give that directory the purpose it currently lacks
      (§10).
- [x] **`docs/planning/knowledge-architecture.md` Name fields point at
      paths the project does not use** (fixed 2026-08-15). All six
      corrected: KA-006 -> `docs/planning/capability-map.md`, KA-026/027/
      028 -> `adr/ADR-00N-*.md`, KA-033 ->
      `docs/planning/implementation-plan.md`, KA-036 ->
      `docs/planning/dreams.md`. A maintenance note at the top of the KA
      spec now states the invariant (Name and Status describe the actual
      repository) and pairs it with the manifest, since updating one
      without the other is how both drifted.
- [x] **KA `Status:` fields are stale across the board** (fixed
      2026-08-15). Ten corrected: KA-009/031/032/035/038/039 `planned` ->
      `draft`; KA-026/028 -> `complete`; KA-027 -> `draft` (ADR-002 still
      needs review, see below); KA-016 `draft` -> `planned`, since
      `fvm.md` is empty.
- [x] **KA-034 (`docs/implementation/stages/stage-0.md`) was never
      created and is superseded in practice** -- divergence recorded
      2026-08-15, decision still open (below). KA-034 now carries a note
      saying the file does not exist, that `roadmap.md`'s Stage 0 section
      covers the ground, and that supersession is undecided.
- [x] **Decide KA-034's fate** -- decided 2026-08-15: retired as
      `superseded`, with its two otherwise-implied Definition of Done
      items promoted into `roadmap.md`'s Stage 0 Completion Criteria. See
      Part I, A4.
- [x] **Review `adr/ADR-002-fvm-first.md` against the survey it now
      cites.** Promoted into Part I as E12; done there 2026-08-17. See
      E12 for the outcome -- not repeated here.

## 8. Finished work filed where nothing can find it

- [x] **`docs/planning/numerical-frameworks.md` is the Numerical Method
      Survey, under a name no spec references** (resolved 2026-08-15:
      moved into the handbook and split at its own compatibility heading
      into `docs/handbook/numerical-methods/overview.md` (KA-007) and
      `compatibility.md` (KA-008), the paths the KA spec already
      specified; the old file no longer exists; `ADR-002` now cites it;
      `docs/planning/CLAUDE.md` records that scientific reference
      material belongs in the handbook, not in planning). Original
      finding follows. This was a substantial,
      genuinely complete 17 KB document -- eight method families (FDM,
      FVM, FEM, spectral, LBM, SPH, PIC/FLIP, MPM), each with
      representation, governing equations, applications, strengths,
      weaknesses, compatibility, computational characteristics and a
      PyFlow-suitability summary, plus a dedicated compatibility section
      at the end. That is KA-007 (`docs/handbook/numerical-methods/
      overview.md`) and KA-008 (`.../compatibility.md`) essentially
      delivered. Because it sits at a different path under a different
      name, both KA and the manifest still treat those two artifacts as
      missing, the handbook looks entirely empty, and
      `adr/ADR-002-fvm-first.md` -- whose §3 entry warns its rationale
      was "drafted from standard CFD domain knowledge, not from
      project-specific reasoning that was never recorded anywhere" --
      cites nothing from it. The survey underpinning the FVM decision was
      in the repository the whole time. Decide: move/split it to the two
      KA paths, or keep it where it is and correct KA-007/008 to match.
      Either way `ADR-002` should then cite it.
- [x] **`docs/handbook/numerical-methods/{overview,compatibility}.md` are
      the only two KA-specified handbook files that were never
      scaffolded** (resolved 2026-08-15 by the move above -- they exist
      with real content, not as stubs).
- [x] **`compatibility.md` does not yet meet KA-008's Definition of
      Done.** Promoted into Part I as E5; closed there 2026-08-17. See
      E5 for the outcome.

## 9. Competing vocabularies for project progression

- [x] **Three parallel progression schemes are in use, and two of them
      disagree on content** (vocabulary resolved 2026-08-15; the content
      divergence is a scope decision and stays open immediately below).
      Release, Stage and Capability Level are now defined in
      `docs/glossary.md`; the Stage/Level correspondence table lives in
      `roadmap.md` (the execution document) and `implementation-plan.md`
      references rather than restates it; P-004 was reworded from "every
      release after Release 0" to "every stage after Stage 0", since
      Stages were always the intent and no release process exists;
      `README.md`, `practices.md` and `prompts/global/project.md` were
      aligned. Original finding follows.
- [ ] **Decide Capability Level 7's fate.** Level 7 (Additional Numerical
      Frameworks -- SPH/FLIP/PIC) has no corresponding roadmap Stage, so
      the implementation plan's "Dam Break / Free Surface" golden demo is
      unreachable from the roadmap. Both documents now say so explicitly
      and mark it unscheduled. Resolving it means either adding a Stage
      or dropping the Level -- both real scope changes, deliberately not
      taken during a consistency pass.

Original finding:

- **Three parallel progression schemes were in use.** `README.md`, `docs/practices.md` and
      `engineering-principles.md` P-004 speak in **Releases** ("every
      release after Release 0"); `roadmap.md` uses **Stages 0-12**;
      `implementation-plan.md` uses **Capability Levels 0-10**. None of
      the three is defined in `docs/glossary.md`, and no document maps
      them onto each other. They are not merely different names for the
      same ladder: `implementation-plan.md` Level 7 (Alternative
      Numerical Frameworks -- SPH/FLIP/PIC, golden demo "free-surface
      flow") has **no corresponding roadmap stage at all**, and the
      plan's Golden Demos table lists a "Dam Break / Free Surface" demo
      the roadmap never produces. The 2026-08-15 reconciliation settled
      *authority* between these two documents ("roadmap = execution, plan
      = vision") but not their *content*, so the divergence survived.
      Add Release/Stage/Level to the glossary with an explicit mapping,
      and reconcile Level 7 in one direction or the other.
- [x] **`docs/planning/releases.md` is still empty.** Promoted into
      Part I as E7; written there 2026-08-17, recording the deferral
      explicitly rather than leaving the file empty. See E7.

## 10. `CLAUDE.md` hierarchy: present but mostly unwritten

- [ ] **29 of the 45 `CLAUDE.md` files are still the identical 121-byte
      placeholder** ("This directory contains project files. Follow the
      repository conventions..."). TASK-009's acceptance criterion
      ("every actively developed subtree contains a CLAUDE.md") is
      formally met and KA-038's ("local instructions where those
      instructions materially improve correctness") is not. The root
      `CLAUDE.md` permits the placeholder "only until something specific
      is known about that directory" -- for several of these, something
      specific has been known for a while and is already written down
      elsewhere. Highest-value ones to write, because the knowledge
      already exists and is currently only findable by reading other
      files: `adr/` (conventions live in `adr/README.md`); `tests/` and
      its four subdirectories (the unit/integration/golden/performance
      split is undocumented -- what belongs where is not obvious);
      `.github/` and `.github/workflows/` (what CI must run, per
      TASK-004); `planning/` and `planning/{model,data}/` (the deliberate
      deferral of the YAML knowledge graph, currently recorded only in
      §4 of this file and the changelog); `src/` and `src/pyflow/` (the
      src-layout and package boundaries); `tools/` and its four
      subdirectories (all four are empty with no stated purpose --
      `generators/`, `planner/`, `validators/`, `scripts/` -- and nothing
      anywhere explains what is meant to go in them).
- [ ] **`tools/` has no documented purpose at all.** Four empty
      subdirectories, four placeholder `CLAUDE.md` files, no mention in
      the manifest, KA spec, or roadmap. Either document the intent or
      add it to the §4 pruning-pass candidate list.

## 11. Smaller defects found during this pass

- [x] **Unbalanced code fence in the numerical survey** (fixed
      2026-08-15 during the move to
      `docs/handbook/numerical-methods/compatibility.md`): the stray
      fence after the "Rare" list now properly opens the
      method-classification tree's block and is closed. Trailing newline
      added.
- [x] **`docs/practices.md` Session Workflow still refers to the retired
      handbook** (fixed 2026-08-15). Steps 1 and 5 now point at
      `roadmap.md` and `backlog.md` -- the current design state -- rather
      than at sixteen empty scientific files. The same pass found and
      fixed a related case: `docs/glossary.md`'s "Project Specification"
      entry described a single durable document by that name, which does
      not exist; it now names the three documents that actually hold that
      role.
- [x] **Documentation "Definition of Done" is defined three times**
      (fixed 2026-08-15). `docs/documentation-guidelines.md` is the
      single authoritative home; `docs/repository-manifest.md` now
      references it instead of restating Completion Rules, and
      `docs/practices.md` says so explicitly. KA-004 is left as written:
      it is the *specification* of what the guidelines document must
      contain, not a competing copy of it.
- [x] **`docs/CHANGELOG-DESIGN.md` contains a dangling self-reference**
      (handled 2026-08-15): a correction was appended noting the
      12-07-2026 entry does not exist in the file, most likely lived in
      the retired `docs/handbook.md`, and should be treated as lost. The
      original entry was deliberately not rewritten -- the log is
      append-only.
- [ ] **Handbook subdirectory asymmetry.** `docs/handbook/physics/` has a
      real `README.md` (KA-009); `docs/handbook/numerical-methods/` has
      none, and `docs/handbook/` itself has no README either. The
      manifest no longer claims one exists, so this is no longer a
      divergence -- just an open structural choice: does
      numerical-methods get its own README, or does `overview.md` serve
      that role? (It partly does already.)
- [ ] **`pyproject.toml` dev dependencies are unpinned.** `ruff`, `mypy`,
      `pytest`, `pre-commit` all float. `.pre-commit-config.yaml` pins its
      hook versions exactly, so lint results from `make lint` and from
      `pre-commit` can already diverge. Also: no `uv.lock` exists, which
      TASK-001 lists as a required artifact -- it cannot be generated
      until `uv` is available (§2 caveat) and TASK-000 lands.
- [ ] **`examples/` has no runnable content and `make demo` is a
      placeholder echo.** Expected at this stage, but the roadmap's
      TASK-010 acceptance criterion is literally `make demo` starting the
      application, so this is the concrete marker for Stage 0 being done.

## 12. Process items carried forward from §4

- [x] §4's "record the CLAUDE.md-maintenance rule in `docs/practices.md`"
      -- done 2026-08-15. `docs/practices.md` now has a Documentation
      Rules section carrying that rule, plus the manifest/KA-spec pairing
      rule and a pointer to the single documentation DoD.
- [x] §4's "add a fresh entry to `docs/CHANGELOG-DESIGN.md` once this
      cleanup pass lands" -- done 2026-08-15; the self-consistency pass
      is recorded there.
- [x] **Rename `knowledge-architecture.md`** (raised 2026-08-15, **done the
      same day**). "architechture" was a typo in the filename of one of the
      project's two most-referenced planning documents. Corrected before the
      first commit, with all 35 references across 22 files updated in the same
      change -- a pre-history rename costs nothing, while a post-history one
      carries every reference through the log. See `docs/CHANGELOG-DESIGN.md`,
      15-08-2026, "Decisions (continued, same day -- knowledge-architecture
      rename)".

      **Found still open 2026-08-18**, three days after it was done, by the
      `codespell` hook flagging the misspelling in this item's own body -- the
      only trace left anywhere outside the append-only changelog. Exactly the
      "items fully complete but still showing `[ ]`" drift
      `docs/practices.md` records under "Closing a backlog item is a Blast
      Radius event".
