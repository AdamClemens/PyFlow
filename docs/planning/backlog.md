# Backlog

Update in place as items close; don't delete completed items outright --
mark them done, so this stays a record of what happened, not just what's
left.

Two audits are recorded here:

- **§§1-4** -- pre-Stage-0 checklist, snapshot taken 2026-08-12 and worked
  through on 2026-08-15. Mostly closed.
- **§§5-12** -- full repository review, 2026-08-15, taken after that work
  landed. Covers execution status, inventory accuracy and cross-document
  consistency, not only the first audit's scope.

A self-consistency pass was run over §§7-12 later the same day, ahead of
the repository's first commit: **every finding that was a divergence
between documents, or the same thing defined in two places, has been
fixed**; everything requiring new content, new code, or a scope decision
is left open below. `docs/CHANGELOG-DESIGN.md` records what was changed
and why.

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

- [ ] **The repository has zero commits.** Every file in the project is
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
- [ ] **`.gitattributes` normalisation is untested.** `* text=auto eol=lf`
      only takes effect on commit/checkout. The CRLF cleanup recorded in
      §2 was done by rewriting files directly, so the rule itself has
      never actually run. Verify after the first commit
      (`git ls-files --eol`) rather than assuming it works.
- [ ] **No branching/commit conventions are recorded anywhere.** Not
      urgent for a solo project, but `docs/practices.md` asserts Git is
      the primary historical record without saying anything about how it
      is used. Either write it down or note the deliberate absence.

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
      criteria and KA-034's Definition of Done both require CI to
      execute. This gap appeared in neither the first audit nor the
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
generated? what happens to KA-034? does ADR-002 survive review?) listed
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
- [ ] **Decide KA-034's fate**: formally retire it in favour of
      `roadmap.md`'s Stage 0 section, or write the separate stage
      specification. Its Definition of Done (CI executes, test suite
      executes, fresh checkout is developable) is still the definition of
      Stage 0 being finished either way.
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
