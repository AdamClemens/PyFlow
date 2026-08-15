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
      **Chosen:** `uv` installed at user level; `uv python install 3.12`
      supplying the interpreter; `.venv/` holding project dependencies;
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

- [ ] **A1b. Stand up the environment.** Checked 2026-08-15 on the
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
      - [x] **Development Python version decided** (2026-08-15,
            maintainer's call): **track the current Python release**
            rather than holding a fixed floor. PyFlow has no external
            consumers, so there is nothing to stay compatible with, and
            the 3.12 previously configured was arbitrary rather than
            chosen. Applied at **3.14**: `requires-python = ">=3.14"`,
            the `Programming Language :: Python` classifier,
            `[tool.ruff] target-version = "py314"` and `[tool.mypy]
            python_version = "3.14"` all moved together, and
            `roadmap.md` TASK-001 no longer names 3.12. Both pinned tool
            versions were verified to accept 3.14 before the bump (`ruff
            0.16.3`, `mypy 2.3.1`) rather than assumed. Policy recorded
            in `docs/practices.md`, including the condition that flips
            it: the moment someone else depends on PyFlow, a
            conservative floor starts to earn its keep.
            **Still to follow through:** C2's CI matrix must match, and
            B2 should decide whether a `.python-version` file is wanted
            at all -- under a track-current policy, pinning one may work
            against the policy rather than for it.
      *Produces:* working `uv`, `make` and a current Python; setup
      instructions in `README.md`.
      *Verified by:* `uv --version`, `make --version` and
      `python --version` all succeed, with Python reporting 3.14 or
      later. All three binaries confirmed working 2026-08-15
      (`uv 0.12.5`, `GNU Make 4.4.1`, CPython 3.14.7). What remains is
      only the `README.md` instructions (E11) and a check that a *fresh*
      shell finds all three on `PATH` -- they were installed mid-session
      and were not visible to a shell started before the install.

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

- [ ] **A2a. Survey the combined compute-and-rendering stack, and build a
      compatibility matrix.** Produces
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
      - do both support the current Python release (see the
        track-current policy in `docs/practices.md` -- this is a live
        constraint, not a formality, since 3.14 is recent and both
        library families are exactly the kind that lag)
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

- [ ] **A2b. Choose the class, and record it as an ADR.** The class is
      the architectural commitment and the thing that is expensive to
      reverse; it constrains field storage layout (Stage 2), the operator
      implementations (Stages 3-4), the rendering subsystem's event loop
      (TASK-007), and whether Capability Level 9 is an upgrade or a
      rewrite. Record what it forecloses, not only what it enables, and
      state the reversibility honestly (P-016).
      *Verified by:* the ADR exists and is Accepted.

- [ ] **A2c. Choose the instances within the class.** The specific array
      library and the specific renderer. Cheaper to change than the class
      and should be recorded as such -- if the interface work in A2b's
      consequences is done properly, swapping an instance should not be
      an architectural event. One ADR or two, as suits.
      *Produces:* the ADR(s); runtime dependencies declared in
      `pyproject.toml`; rows in `docs/repository-manifest.md`; a KA entry
      if wanted.
      *Verified by:* TASK-011 has no unmade dependency decision in front
      of it, and D3 knows what it is building against.
      **Note on ADR numbering:** `adr/README.md` makes numbering
      sequential and permanent, so 004 goes to whichever ADR lands first
      across A2b, A2c and A4 -- do not pre-assign.

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

- [ ] **B1. TASK-000 — create the engine skeleton.** The repository
      contains **no Python files at all**. `src/pyflow/` and its four
      subpackages hold only `CLAUDE.md`. Create `__init__.py` for
      `pyflow` and for `engine/`, `physics/`, `rendering/`,
      `configuration/`, plus the placeholder modules that communicate the
      intended architecture, and an example entry point. Note that
      `pyproject.toml` (`packages = ["src/pyflow"]`) and MyPy
      (`packages = ["pyflow"]`) are both already configured against this
      package, so `make install` and `make typecheck` fail until it
      exists.
      *Produces:* an importable `pyflow` package.
      *Verified by:* TASK-000's four acceptance criteria -- imports
      successfully, no circular dependencies, structure matches the
      documented architecture, example entry point executes.
      **"No circular dependencies" needs a mechanism, not an assertion**
      (noted 2026-08-15): nothing currently checks it, and it is the one
      TASK-000 criterion that cannot be confirmed by looking. Either add
      an import-graph check to the test suite (C1) or to CI (C2), or
      record that it is verified by inspection and accept that it will
      silently rot. It matters more later than now -- the layered engine
      architecture in E1a is exactly the kind of design that acquires
      cycles quietly.

- [ ] **B2. TASK-001 — complete the development environment.**
      `pyproject.toml` and `.pre-commit-config.yaml` exist;
      `uv.lock` does not, and TASK-001 lists it as a required artifact.
      Runtime dependencies are no longer empty by the time this runs --
      A2c declares the array library and the renderer -- so the lock
      covers both dependency groups. Decide here whether a
      `.python-version` file is wanted at all: under the track-current
      policy, pinning one may work against the policy rather than for
      it.
      Consider `.python-version` (optional per TASK-001). Note that
      `uv.lock` is what actually makes the dev toolchain reproducible --
      the unpinned `ruff`/`mypy`/`pytest`/`pre-commit` entries in
      `[dependency-groups]` are acceptable once it exists, and the
      current mismatch between floating tool versions and the exactly
      pinned hook `rev`s in `.pre-commit-config.yaml` should be checked
      once both can actually run.
      *Produces:* `uv.lock`; a verified environment.
      *Verified by:* TASK-001's acceptance criterion literally -- a clean
      clone runs `make install` then `make test` with no manual
      configuration.

- [ ] **B3. TASK-002 — verify the build system.** The `Makefile` has all
      eight targets, but none has ever been executed and `docs` and
      `demo` are placeholder echoes. Run each target; replace the two
      placeholders once there is something to build and run (`demo`
      depends on D4).
      *Produces:* eight working targets.
      *Verified by:* TASK-002's acceptance criterion -- every documented
      command executes successfully.

- [ ] **B4. Run `pre-commit` against the whole repository for the first
      time.** *(Gap found 2026-08-15.)* `.pre-commit-config.yaml` was
      written on 2026-08-15 and has **never been executed** -- its own
      header says so. `make install` runs `pre-commit install`, which
      only wires up the hook; it does not run it. The first
      `pre-commit run --all-files` should be a deliberate step with its
      results inspected, not something discovered mid-commit, because
      `ruff --fix` and `ruff-format` will rewrite source on first
      contact and `mypy` runs under `strict = true` -- which the
      placeholder modules from B1 must satisfy, annotations included.
      Expect this to produce changes; that is the point of doing it
      deliberately.
      *Verified by:* `pre-commit run --all-files` passes cleanly, and C2
      configures CI to run the same checks so the two cannot drift.

---

## Group C — Testing and CI (TASK-003, TASK-004)

Depends on B.

- [ ] **C1. TASK-003 — automated testing.** `tests/` contains five
      `CLAUDE.md` files and nothing else. `pyproject.toml` configures
      `testpaths` but has **no coverage configuration**, which TASK-003
      lists as a required artifact. Add coverage config and smoke tests.
      This also removes the known `make test` failure (pytest exits 5 on
      zero collected tests).
      *Produces:* smoke tests, coverage configuration.
      *Verified by:* TASK-003's acceptance criterion -- tests execute
      locally and produce coverage reports; `make test` exits 0.

- [ ] **C2. TASK-004 — continuous integration.** `.github/workflows/`
      contains a `CLAUDE.md` and **no workflow file**. CI executing is a
      named condition in both `roadmap.md`'s Stage 0 criteria and
      KA-034's Definition of Done, so Stage 0 cannot be reached without
      it. Configure install, lint, format check, type check, and unit
      tests. Write `.github/CLAUDE.md` and `.github/workflows/CLAUDE.md`
      in the same change -- they are two of the placeholders E9 covers,
      and this is the moment their content becomes known.
      **Pin the OS and Python matrix explicitly** (noted 2026-08-15):
      neither `roadmap.md` nor this item says which. Development happens
      on Windows and CI runners default to Linux, and that split is
      precisely where `make` behaviour and headless rendering (D5)
      diverge -- so a green pipeline could coexist with a broken local
      setup, or the reverse. Decide whether CI is Linux-only, or a
      matrix, and say so. The Python side is now constrained by the
      track-current policy (A1b, `docs/practices.md`): CI tests the
      current release, and a version matrix would contradict the policy
      rather than support it -- so the real question here is the *OS*
      matrix. Note also that a track-current policy makes CI the thing
      most likely to catch a new release breaking a dependency, which is
      an argument for pinning the runner's Python explicitly rather than
      letting it drift silently.
      *Produces:* a CI workflow definition.
      *Verified by:* TASK-004's acceptance criterion -- the pipeline runs
      automatically and passes.

---

## Group D — Engine subsystems (TASK-005, 006, 007, 010)

D1-D3 depend on B1; D3 additionally on A2; D4 on B3, D1, D2, D3.

- [ ] **D1. TASK-005 — configuration framework.** Loading, validation,
      defaults. Deliberately simple. This is the mechanism
      `adr/ADR-003-modular-numerical-strategies.md` and
      `docs/implementation/golden-demos.md` both assume exists -- demos
      must select numerical components through configuration rather than
      hardcoding them.
      *Verified by:* the application can be started entirely from
      configuration.

- [ ] **D2. TASK-006 — logging framework.** Configurable levels,
      consistent formatting, centralised configuration.
      *Verified by:* every subsystem logs through the common framework.

- [ ] **D3. TASK-007 — rendering framework.** Window creation, render
      loop, clean shutdown, using the renderer chosen in A2c, within the
      class chosen in A2b.
      *Verified by:* a rendering window opens, updates and closes
      cleanly.

- [ ] **D4. TASK-010 — engine bootstrap.** A minimal application that
      loads configuration, initialises logging, opens the window, enters
      the loop and exits cleanly. No simulation functionality.
      *Verified by:* TASK-010's acceptance criteria -- `make demo` starts
      the application from a clean checkout, CI passes, and all Stage 0
      components integrate. This is also Stage 0 completion criterion 7.

- [ ] **D5. Deliver the "Empty Window" golden demo.** *(Gap found
      2026-08-15 while checking the queue for completeness -- no previous
      audit had caught it.)* D4 produces a bootstrap application; that is
      not the same artifact as a golden demo, and Stage 0 owes one.
      `implementation-plan.md` gives Capability Level 0 the golden demo
      "open a rendering window, display an empty simulation" and lists
      **Empty Window / Rendering** in its Golden Demos table.
      `docs/implementation/golden-demos.md` requires every demo in that
      table to have an entry defining what "working" means concretely
      enough to verify automatically, and sets a Definition of Done that
      is stricter than "the app starts": executable, deterministic or
      with controlled non-determinism, verifying meaningful behaviour
      rather than just not crashing, documented, and **included in
      regression testing**.
      Three artifacts, none of which exist:
      - [ ] an Empty Window entry in `docs/implementation/golden-demos.md`
      - [ ] runnable demo code in `examples/golden-demos/` -- currently
            an empty directory, and the one place the repository has
            promised demos will live
      - [ ] a regression test in `tests/golden/` -- currently an empty
            directory whose purpose is exactly this
      This is also what forces the **headless rendering** requirement in
      A2a to be real rather than theoretical: a golden demo that cannot
      run in CI is not included in regression testing, and therefore does
      not meet its own Definition of Done.
      *Verified by:* the demo runs in CI with no display and its
      regression test passes.

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

- [ ] **E1a. `docs/architecture/engine.md`** (KA-029) -- the conceptual
      map of the engine's replaceable layers: mesh, variables, flux,
      advection, diffusion, time integration, pressure-velocity coupling,
      linear solvers, boundary conditions. Must convey that each layer
      has a contract, implementations are replaceable, the timestepper
      depends on contracts rather than concrete schemes, construction
      selects implementations and execution operates through them.
- [ ] **E1b. `docs/architecture/icds.md`** (KA-030) -- the
      user/configuration-facing contracts, *not* every internal Python
      interface. Stage 3 (TASK-018..022) has nothing to implement against
      until this exists, so leaving it empty makes "a developer can begin
      Stage 1 immediately" true only in a narrow sense.

### E2 — Remaining architecture files (3 files)

- [ ] **E2a. Write or retire `docs/architecture/overview.md`.** Empty, no
      KA entry. If kept, it must be distinct from `engine.md`, which was
      already resolved as a separate document rather than a rename.
- [ ] **E2b. Write or retire `docs/architecture/repository.md`.** Empty,
      no KA entry. Note the overlap risk with
      `docs/repository-manifest.md` -- if kept, state clearly what job
      each one has, or fold it in.
- [ ] **E2c. Write `docs/architecture/rendering.md`.** Empty, no KA
      entry. Distinct from A2a's survey: the survey is decision-support
      comparing options, this is the architecture of the renderer
      actually adopted -- how it sits behind an interface (per
      `adr/ADR-003-modular-numerical-strategies.md`), how the render loop
      relates to the timestep, and how a second renderer would be added,
      which is the maintainer's stated ambition. **Follows A2b and A2c**;
      it cannot be written before the decisions it describes.

### E8 — Prompt feature contexts (4 files, KA-040..043)

None of these exist. KA §20's "Agent support" completion criteria name
them explicitly. **Worth doing before E3 and E4**, since `handbook.md` is
precisely the brief those sixteen handbook entries should be written
against.

- [ ] **E8a. `prompts/features/handbook.md`** (KA-040)
- [ ] **E8b. `prompts/features/adr.md`** (KA-041)
- [ ] **E8c. `prompts/features/implementation-plan.md`** (KA-042)
- [ ] **E8d. `prompts/features/agents.md`** (KA-043)

### E3 — Numerical-methods handbook (10 files, KA-016..025)

Real domain content with citations. Do not generate mechanically.
`docs/handbook/numerical-methods/overview.md` now supplies survey
material to draw on, and `docs/handbook/numerical-methods/CLAUDE.md`
carries the citation requirement.

- [ ] **E3a. `fvm.md`** (KA-016) -- **write first.** It is the one
      already-decided method, `ADR-002` points at it, and everything
      below depends on it conceptually.
- [ ] **E3b. `meshes.md`** (KA-017)
- [ ] **E3c. `variable-placement.md`** (KA-018)
- [ ] **E3d. `fluxes.md`** (KA-019)
- [ ] **E3e. `advection.md`** (KA-020)
- [ ] **E3f. `diffusion.md`** (KA-021)
- [ ] **E3g. `time-integration.md`** (KA-022)
- [ ] **E3h. `pressure-velocity-coupling.md`** (KA-023)
- [ ] **E3i. `linear-solvers.md`** (KA-024)
- [ ] **E3j. `boundary-conditions.md`** (KA-025)

### E4 — Physics handbook (6 files, KA-010..015)

Same citation requirement; see `docs/handbook/physics/README.md` for what
an entry must contain, and `physics/CLAUDE.md` for the caution.

- [ ] **E4a. `incompressible-flow.md`** (KA-010) -- **write first.** It
      is the MVP's physical model.
- [ ] **E4b. `heat-transfer.md`** (KA-011)
- [ ] **E4c. `density.md`** (KA-012)
- [ ] **E4d. `humidity.md`** (KA-013)
- [ ] **E4e. `buoyancy.md`** (KA-014)
- [ ] **E4f. `cloud-formation.md`** (KA-015)

The last four support Stage 6 rather than the MVP. They are still in
scope under A3 -- the criterion is "no empty tracked file", not "only
what the MVP needs" -- but they are the natural place to economise if
Stage 0 needs to be shortened, by retiring them from the manifest for now
rather than half-writing them.

### E5 — Handbook completeness

- [ ] **E5. Bring `docs/handbook/numerical-methods/compatibility.md` up
      to KA-008's Definition of Done.** It currently records the pairwise
      graph and a very-common/common/occasional/rare grouping. KA-008
      also requires the *kinds* of compatibility to be distinguished --
      mutually exclusive alternatives, interchangeable implementations,
      methods coexisting at different layers, coupled methods, hybrids,
      post-processing-only, and combinations needing separate engines are
      not the same relationship -- and requires incompatibilities to be
      stated. The file flags this gap itself. Not an empty-file item; it
      is 🟨 already, and this takes it to 🟩.

### E6 — References (3 files)

Populate from the sources E3 and E4 cite, not before -- the standing
deferral reason has always been that there is nothing to list until the
handbook cites something. Under A3 they cannot stay empty, so these
follow E3/E4 rather than being independent.

- [ ] **E6a. `docs/references/books.md`**
- [ ] **E6b. `docs/references/papers.md`**
- [ ] **E6c. `docs/references/websites.md`**

### E7 — Planning (1 file)

- [ ] **E7. Write or retire `docs/planning/releases.md`.** Empty, and the
      KA spec has no entry to build from. Release is now defined in the
      glossary, so the term is no longer undefined; what remains is
      whether a release process is wanted at all. Under A3 the file
      cannot stay empty -- write it, or remove it from the manifest and
      delete it.

### E9 — Agent guidance (TASK-009, KA-038)

- [ ] **E9. Fill the 29 placeholder `CLAUDE.md` files.** 45 exist; 29 are
      still the identical 121-byte generic text. Grouped by where the
      knowledge already exists, so none of these requires inventing
      anything:
      - [ ] `adr/` -- conventions are already in `adr/README.md`
      - [ ] `tests/` and `unit/`, `integration/`, `golden/`,
            `performance/` -- the four-way split is undocumented and what
            belongs where is not obvious; settle it alongside C1
      - [ ] `.github/` and `.github/workflows/` -- content becomes known
            with C2; write them in that change
      - [ ] `planning/`, `planning/model/`, `planning/data/` -- the
            deliberate knowledge-graph deferral and its unblock condition
      - [ ] `src/` and `src/pyflow/` -- src-layout, package boundaries;
            content becomes known with B1
      - [ ] `tools/` and `generators/`, `planner/`, `validators/`,
            `scripts/` -- depends on E10
      - [ ] `examples/` and `experiments/`, `tutorials/` --
            `golden-demos/` already has real content
      - [ ] `docs/references/`, `docs/tutorials/`
      - [ ] `assets/` and `colourmaps/`, `icons/`, `shaders/`,
            `textures/` -- content becomes known with D3
      *Verified by:* no `CLAUDE.md` in the repository still contains the
      generic placeholder text.

### E10-E12 — Loose ends

- [ ] **E10. Give `tools/` a documented purpose, or retire it.** Four
      empty subdirectories (`generators/`, `planner/`, `validators/`,
      `scripts/`), no mention in the KA spec or roadmap, and nothing
      anywhere stating what belongs in any of them. If the manifest is
      ever generated (Part II), `tools/generators/` is presumably where
      that lives -- which would settle this. Blocks the `tools/` part of
      E9.

- [ ] **E11. Add `README.md` development instructions.** KA-001 lists
      "development instructions when implementation begins" as a content
      requirement, and Stage 0's exit criterion is that a developer can
      clone and begin Stage 1 immediately. Currently the README has none.
      Follows A1b and B2, once there is a real setup to describe.

- [ ] **E13. Add the development commands to the root `CLAUDE.md`.**
      *(Gap found 2026-08-15.)* KA-037 requires the root file to give
      agents the minimum essential project-wide instructions, and Stage 0
      criterion 5 is that agents have contextual guidance throughout the
      repository. The root `CLAUDE.md` currently says nothing about how
      to build, test, lint or type-check -- because until B2/B3 none of
      those commands worked. Once they do, an agent entering the
      repository should learn them there rather than reverse-engineering
      the `Makefile`. Keep it compact, per KA-037's own Definition of
      Done. Follows B3.

- [ ] **E12. Review `adr/ADR-002-fvm-first.md` against the survey it now
      cites.** Its rationale was drafted from general CFD domain
      knowledge because no project-specific reasoning had been recorded;
      `docs/handbook/numerical-methods/overview.md` turned out to contain
      exactly that reasoning, with per-method PyFlow-suitability
      assessments. The ADR cites it as of 2026-08-15 but has not been
      checked against it. Until it is, it stays 🟨 in the manifest.
      Depends on nothing; do it early.

---

## Group F — Close out and verify

- [ ] **F1. Record the project's Git conventions.** `docs/practices.md`
      asserts Git is the primary historical record and step 7 of the
      session workflow is "commit changes", but nothing says anything
      about branch naming, commit granularity or message form. The
      repository's history begins on branch `master` while `main` is the
      more common default -- decide and record which this project uses.
      Not heavyweight process; one short section.

- [ ] **F2. Sweep the inventories for everything Stage 0 created.**
      *(Gap found 2026-08-15.)* Stage 0 adds a substantial number of
      artifacts that neither `docs/repository-manifest.md` nor
      `docs/planning/knowledge-architecture.md` currently knows about:
      the ADRs from A2b/A2c/A4,
      `docs/architecture/compute-and-rendering-stack.md` (A2a),
      `uv.lock` and possibly `.python-version` (B2), the CI workflow
      (C2), every Python module under `src/pyflow/` (B1), the test suite
      (C1), and the golden demo code and its regression test (D5). The
      manifest's `src/`, `tests/`, `examples/` and `.github/` sections
      are all currently ⬜ with explanatory notes that will become wrong.
      `docs/practices.md` now carries the standing rule to update both
      documents together whenever an artifact is added, moved or changes
      status -- this item is the backstop that catches whatever slipped
      through, not a substitute for following it as you go.
      The two inventories drifting is the failure mode this repository
      has already had once, and it is the reason the second audit was
      needed at all.
      *Verified by:* the link check and empty-file check both come back
      clean, and every ⬜ row corresponds to something genuinely not yet
      built.

- [ ] **F3. Run the Stage 0 exit audit.** Check each of the nine Stage 0
      Completion Criteria against evidence, and record the result. The
      criteria and where their evidence comes from:
      1. TASK-000..010 acceptance criteria — B1, B2, B3, C1, C2, D1-D4,
         plus TASK-008 (Group E) and TASK-009 (E9, E13)
      2. All engineering tooling operational — A1a, A1b, B2, B3, B4,
         C1, C2
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
      accurate; it did not answer this. *Unblock condition:* worth
      settling before it drifts a second time, and it interacts with E10
      (`tools/generators/`).

- [ ] **`planning/model/*.yaml` and `planning/data/*.yaml`** -- the
      machine-readable knowledge graph. Eleven empty files. Deferred
      because populating the graph is downstream of having real handbook
      and ADR content to populate it with. Explicitly exempt from A3's
      no-empty-files condition, as data rather than documentation.
      *Unblock condition:* Group E's handbook work landing.

- [ ] **`CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `SECURITY.md`** --
      none exist and none is referenced. A conscious deferral for a
      single-developer project, reaffirmed 2026-08-15, not an oversight.

- [ ] **File-structure pruning pass** -- a dedicated pass to remove
      files and directories that turn out not to be needed, once scope is
      clearer, rather than ad hoc deletion during other work.
      `prompts/common/task-prompts-subdir-agents-md.md` (superseded,
      never executed) is a first candidate; E2, E7 and E10 may produce
      more. Note that this repository has no general keep-don't-delete
      convention -- the only such rule is the narrow one in
      `prompts/common/CLAUDE.md` about completed `task-*.md` prompts.

- [ ] **Handbook README asymmetry.** `docs/handbook/physics/` has a
      structural `README.md` (KA-009); `docs/handbook/numerical-methods/`
      and `docs/handbook/` itself do not. No longer a divergence -- the
      manifest no longer claims otherwise -- just an open structural
      choice, and `overview.md` partly serves the role already.

- [ ] **`docs/planning/dependency-tree.md`: hand-maintained or derived?**
      It is currently hand-maintained. Whether it should instead be
      derived from Engine Architecture / ICDs is an open question that
      only becomes answerable once E1a exists. *Unblock condition:* E1a.

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
- [ ] Physics Handbook, content -- write the six entries. Real domain
      content requiring citations -- deliberately not attempted
      mechanically alongside the structural scaffolding above.
- [x] Numerical Component Handbook, structure decision (resolved
      2026-08-15): same situation as the Physics Handbook -- KA-016
      through KA-025 already specify
      `docs/handbook/numerical-methods/{fvm,meshes,variable-placement,
      fluxes,advection,diffusion,time-integration,
      pressure-velocity-coupling,linear-solvers,boundary-conditions}.md`.
      Scaffolded all ten.
- [ ] Numerical Component Handbook, content -- write the ten entries.
      `fvm.md` is the natural one to write first (KA status `draft`, not
      `planned`, and `adr/ADR-002-fvm-first.md` references it).
- [ ] `docs/architecture/overview.md`, `rendering.md`, `repository.md` --
      all still empty. No KA basis for any of the three (checked KA §11
      in full -- it only defines `engine.md` and `icds.md`) -- not
      redundant, just not itemised in the spec. Content still unwritten.
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
- [ ] `docs/references/books.md`, `websites.md`, `papers.md` -- all empty;
      still blocked on handbook content (checked 2026-08-15: still
      unwritten, see the Physics/Numerical Component Handbook content
      items above) -- populate alongside those, not before.
- [ ] `docs/planning/releases.md` -- empty. Checked 2026-08-15: MVP
      Definition and Upgrade Paths now exist
      (`docs/implementation/{mvp,upgrade-paths}.md`), so the original
      blocking condition is technically satisfied, but
      `knowledge-architecture.md` has no entry for a releases artifact
      at all (checked, no hits) -- there's no spec to follow, and this
      was already assessed low priority. Left deferred rather than
      inventing a release process/structure nobody asked for.
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
- [ ] **No branching/commit conventions are recorded anywhere.** Promoted
      to Part I, F1 -- `docs/practices.md` asserts Git is the primary
      historical record without saying anything about how it is used, and
      history now begins on `master` while `main` is the more common
      default.

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
- [ ] **Review `adr/ADR-002-fvm-first.md` against the survey it now
      cites.** The ADR's rationale was drafted from general CFD domain
      knowledge because no project-specific reasoning had been recorded;
      `docs/handbook/numerical-methods/overview.md` turned out to contain
      exactly that reasoning, with per-method PyFlow-suitability
      assessments. The ADR now cites it (2026-08-15) but has not been
      checked against it. Until then it stays 🟨 in the manifest, not 🟩.

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
- [ ] **`compatibility.md` does not yet meet KA-008's Definition of
      Done.** It records the pairwise graph and a very-common/common/
      occasional/rare grouping, which is observed practice. KA-008
      additionally requires the *kinds* of compatibility to be
      distinguished explicitly -- mutually exclusive alternatives,
      interchangeable implementations, methods coexisting at different
      layers, coupled methods, hybrids, post-processing-only, and
      combinations needing separate engines are not the same
      relationship -- and requires incompatibilities to be stated. The
      file flags this itself. Real content work, not a consistency fix.

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
- [ ] **`docs/planning/releases.md` is still empty.** The narrower part
      of this finding is closed -- Release is now defined in the glossary
      and the README no longer describes project status in release terms.
      Inventing a release *process* remains deferred on the original §3
      grounds: KA has no entry for one, and nobody has asked for it.
      Revisit when there is something to release.

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
- [ ] **Rename `knowledge-architecture.md`** (raised 2026-08-15).
      "architechture" is a typo in the filename of one of the project's
      two most-referenced planning documents; roughly 25 references point
      at it. Not a consistency defect -- everything referring to it spells
      it the same wrong way -- so it was left alone during the
      consistency pass. Worth doing *before* the first commit if it is
      going to be done at all, since a pre-history rename is free and a
      post-history one is not.
