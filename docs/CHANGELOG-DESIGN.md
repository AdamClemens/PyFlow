## 15-08-2026

### Decisions
- Audited the full repository snapshot against `knowledge-architechture.md`;
  logged the results as `docs/planning/backlog.md` (structural
  inconsistencies, tooling gaps, content gaps, process items).
- Confirmed: the prompt generator (automated or manual) is downstream of
  having real handbook/ADR content -- building it now would only automate
  producing empty scaffolding. Deferred `planning/model/*.yaml` and
  `planning/data/*.yaml` accordingly.
- Standing rule adopted: whenever a document is created or substantially
  filled in, update its nearest `AGENTS.md` with concrete maintenance
  guidance. Still needs to be recorded in `docs/practices.md` itself.
- Created `prompts/common/TEMPLATE.md` (reusable task-prompt structure) and
  four ready-to-delegate prompts for backlog items with no open
  project-identity decisions: repo hygiene configs (`.gitignore`,
  `.editorconfig`, `.gitattributes`), `.pre-commit-config.yaml`, the
  `dependency-tree.md` formatting fix, and `AGENTS.md` for
  `prompts/code`/`prompts/docs`.
- Corrected an earlier miscall: the glossary merge is NOT delegatable as-is
  -- it depends on an unresolved decision (which file is canonical), so it
  moved from the "ready to delegate" set into the open-decisions set below.

### Open Questions (decisions needed before delegating further work)
- **Glossary**: keep `docs/planning/glossary.md` as canonical vs. move its
  content to `docs/glossary.md` (the path the manifest expects).
- **`docs/handbook.md`**: retire now (salvage anything useful first) vs.
  keep as a stub index until the Physics/Numerical Component Handbooks
  exist. Conflicts with `CHANGELOG-DESIGN.md` (12-07-2026 entry) calling
  the handbook "canonical memory."
- **`implementation-plan.md` vs `roadmap.md`**: overlapping planning docs
  (Capability Levels vs. Stages/TASK-XXX). `roadmap.md` is more recently
  touched; still needs an explicit reconcile-or-retire decision.
- **Physics Handbook granularity**: 3 stub files
  (`atmosphere.md`/`fluids.md`/`thermodynamics.md`) vs. 6 topics implied by
  the KA spec (incompressible flow, heat transport, density transport,
  humidity/species transport, buoyancy, cloud formation).
- **Numerical Component Handbook**: one file per component vs. a combined
  document; no path assigned yet.
- **ICDs**: no file location assigned yet.
- **MVP Definition vs Upgrade Paths**: need an explicit scope boundary so
  they don't duplicate the same material.
- **TASK-000 package mismatch**: roadmap specifies
  `engine/physics/rendering/configuration/demos/tests`; actual
  `src/pyflow/` has `engine/interaction/io/physics/rendering/simulation/util`.

### Next Session
- Work through the open questions above one at a time.
- Once each is resolved, either action it directly (if trivial) or
  instantiate a `prompts/common/task-*.md` prompt from `TEMPLATE.md` for it.
- See `docs/planning/backlog.md` for the full outstanding list, including
  lower-priority items not repeated here.

### Decisions (continued, same day)
- Added a standing rule to the top-level `AGENTS.md` ("Maintaining
  AGENTS.md Files"): these files are living documents and should be
  amended whenever work surfaces something a future contributor would
  need to know, not just when a document is first filled in. Generalizes
  the narrower rule noted in the 15-08-2026 entry above (which still needs
  recording in `docs/practices.md` -- not yet done).
- Before executing the `prompts/code`/`prompts/docs` AGENTS.md task
  prompt, checked its cited source (`knowledge-architechture.md` §17,
  KA-039..043) directly rather than trusting the prompt's own inference.
  Found the KA spec actually calls for `prompts/global/project.md` +
  `prompts/features/{handbook,adr,implementation-plan,agents}.md`, not a
  code/docs split -- logged as a new backlog §1 item ("Prompt directory
  layout mismatch") rather than resolved silently.
- Decision: follow the KA spec. Scaffolded `prompts/global/AGENTS.md`,
  `prompts/features/AGENTS.md`, and a new `prompts/AGENTS.md` index.
  `prompts/code/` and `prompts/docs/` left in place, untouched, marked
  legacy pending reconciliation. The KA-039..043 content files themselves
  (`project.md`, `handbook.md`, `adr.md`, `implementation-plan.md`,
  `agents.md`) were deliberately not written -- `project.md` in
  particular can't be written yet without resolving whether it supersedes
  `prompts/common/BRIEF`, whose "Current Direction" section conflicts
  with KA-039's content boundary (see `prompts/global/AGENTS.md`).
  Marked `prompts/common/task-prompts-subdir-agents-md.md` superseded in
  place rather than deleting it.

### Open Questions (added)
- **BRIEF vs. `prompts/global/project.md`**: does `project.md` supersede
  `BRIEF`? If so, where does `BRIEF`'s "Current Direction" content move,
  given KA-039 says the global file must not contain current numerical
  architecture?
- **`prompts/code/` and `prompts/docs/` fate**: rename into `features/`,
  merge, or retire now that the KA-conformant layout exists alongside them?

### Decisions (continued, same day -- AGENTS.md -> CLAUDE.md)
- A recommendation surfaced in a separate chat (different context window)
  that Claude Code reads `CLAUDE.md`, not `AGENTS.md`, and suggested either
  a root `CLAUDE.md` importing `@AGENTS.md`, or mirroring the tree with a
  one-line `CLAUDE.md` (`@AGENTS.md`) in every directory that already has
  an `AGENTS.md`.
- Verified this directly against the current official Claude Code docs
  (`code.claude.com/docs/en/memory`) rather than trusting the secondhand
  summary: confirmed Claude Code reads `CLAUDE.md` only, at every directory
  level, and never reads `AGENTS.md`. The repo's entire per-directory
  local-context design was invisible to it.
- Decision (maintainer's call, overriding the import suggestion): rename
  every `AGENTS.md` to `CLAUDE.md` rather than keep both. Simpler than an
  import layer, and Windows symlinks (the docs' other suggested option)
  need admin/dev mode. Trade-off noted and accepted: this repo now has no
  automatic recognition by other AGENTS.md-reading agent tools, if one is
  ever added to the workflow.
- Executed: renamed all 45 `AGENTS.md` files to `CLAUDE.md`. Also updated
  every textual reference to "AGENTS.md" across the living docs --
  `AGENTS.md` itself (now `CLAUDE.md`), `knowledge-architechture.md`
  (KA-038, KA-043, and several plain-prose mentions), `roadmap.md`
  (TASK-009), `repository-manifest.md`, `backlog.md`, and the
  `prompts/common/` templates and task prompts -- so the rename didn't
  leave the design docs describing a filename that no longer exists. This
  changelog was deliberately excluded from that pass: it's an append-only
  log, so entries above dated before today correctly still say
  "AGENTS.md" -- that was accurate when written. Logged as a resolved item
  in `docs/planning/backlog.md` §1.
- Correction, same conversation: earlier today's superseded-task
  annotation on `prompts/common/task-prompts-subdir-agents-md.md` claimed
  it was being kept "per repo convention." Challenged -- no such general
  convention exists. The only real rule is the narrower one in
  `prompts/common/CLAUDE.md`, scoped to completed `task-*.md` prompts,
  which doesn't cleanly cover a superseded/never-executed one. Corrected
  the annotation and logged a new backlog item (§4) for a deliberate
  file-structure pruning pass later, rather than deciding file-by-file
  whether to delete things while doing other work.

### Decisions (continued, same day -- backlog §2 tooling/plumbing)
- Identified that most of §2 was already mechanical (covered by the
  `repo-hygiene-configs` and `pre-commit-config` prompts, both grounded in
  `roadmap.md` TASK-001's already-decided tool stack: Python 3.12, uv,
  Ruff, Ruff Formatter, MyPy, PyTest, pre-commit), but `LICENSE` and parts
  of `pyproject.toml` had no real decision recorded anywhere.
- Asked the maintainer directly rather than guessing: **License ->
  BSD-3-Clause**; **pyproject.toml author metadata -> name + email**
  (`Adam Clemens <a.j.clemens@hotmail.com>`, already public via git commit
  authorship regardless).
- Build backend (not asked -- low-stakes, reversible, decided directly):
  **hatchling**, not `uv_build`. `uv` is the dependency manager either way;
  hatchling was chosen for its stable, well-documented src-layout config
  over `uv_build`'s faster-moving, less-verifiable-from-memory pinning
  conventions.
- Verified rather than guessed, since getting this wrong would silently
  break `make install`/`make test`: (1) the PEP 639 `license =
  "BSD-3-Clause"` + `license-files = ["LICENSE"]` string form is current
  and valid, superseding the old table form; (2) `uv` now uses
  `[dependency-groups]` (PEP 735) for dev dependencies, not
  `[tool.uv.dev-dependencies]` (legacy) -- `uv sync` includes the `dev`
  group by default, so `make install` doesn't need `--all-extras`;
  (3) current stable tags for the three pre-commit hook repos, checked
  against each repo's GitHub API directly rather than search-engine
  summaries (which disagreed with each other on the mypy mirror's tag).
- Executed all of §2 in one pass: `LICENSE`, `pyproject.toml`, `Makefile`,
  `.pre-commit-config.yaml`, `.gitignore`, `.editorconfig`,
  `.gitattributes`. Updated `README.md`'s License section (was "TBD") and
  `repository-manifest.md`'s status markers for the three tracked rows.
  `CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`/`SECURITY.md` remain deferred, per
  the existing backlog note -- not revisited.
- Two caveats surfaced rather than papered over: `uv` isn't installed in
  this environment, so `make install`/`make test` were never actually run
  -- TASK-001's acceptance criterion is unverified, not confirmed. And
  `make test` will likely fail right now (pytest exits 5 on zero collected
  tests) until TASK-003 adds smoke tests -- expected, not a defect in
  today's work. Both noted in `docs/planning/backlog.md` §2.

### Decisions (continued, same day -- backlog §1 remaining structural items)
- Asked the maintainer directly for the four items with genuine judgment
  calls (no existing spec settled them): `docs/handbook.md`'s fate,
  `implementation-plan.md` vs `roadmap.md` reconciliation, and the
  TASK-000 package-structure mismatch. A fourth candidate item, the
  glossary duplication, turned out not to need asking -- KA-005 already
  names `docs/glossary.md` as canonical, so it was executed directly like
  the earlier AGENTS.md/prompts findings.
- **Glossary**: moved `docs/planning/glossary.md`'s 475 lines to
  `docs/glossary.md`, first folding in three terms (Feature, Golden Demo,
  Thin Slice) that existed only in the stale 16-line stub there and
  nowhere in the larger file -- would have been silently lost otherwise.
- **Handbook -> retire** (maintainer's call): deleted `docs/handbook.md`.
  Every section was superseded elsewhere, and it collided in name with the
  KA spec's *different* future Handbook (Physics + Numerical Component
  reference). Updated `README.md`'s "Where to Start" list to point at
  `CLAUDE.md`, `docs/practices.md`, `docs/planning/capability-map.md`,
  `docs/planning/backlog.md` instead.
- **Plans -> roadmap is execution, plan is vision** (maintainer's call):
  removed `implementation-plan.md`'s Task Index table and unfilled
  `TASK-XXX` template (redundant with `roadmap.md`, which already covers
  this far more concretely); added a scope note at its top pointing to
  `roadmap.md` for execution detail. Kept MVP Definition, Capability
  Levels 0-10, Dependency Graph, Milestones, Golden Demos, Upgrade Paths,
  and the generic Definition of Done as-is -- those aren't duplicated by
  `roadmap.md`.
  While reconciling, found `roadmap.md` had its own internal bug: Stage 1
  onward's task IDs restart at `TASK-001` and collide with Stage 0's
  `TASK-001..010` (e.g. `TASK-001` = "Development Environment" in Stage 0
  *and* "Coordinate System" in Stage 1; `TASK-004` = "Continuous
  Integration" *and* "Field Interface"). Fixed by renumbering Stage 1
  onward to continue from `TASK-011`, done via a two-phase sed (temporary
  `TASKX-` marker prefix, to avoid a renumbered ID colliding with a
  not-yet-processed old one) rather than by hand, then verified no
  duplicate headings remain anywhere in the file. Mapping: Stage 1
  001-003 -> 011-013; Stage 2 004-007 -> 014-017; Stage 3 008-012 ->
  018-022; Stage 4 013-020 -> 023-030; Stage 5 021-024 -> 031-034; Stage 6
  025-028 -> 035-038. Stage 0 (000-010) and Stages 7-12 (no individual
  task IDs yet, just bullet lists) were untouched. Nothing outside
  `roadmap.md` referenced a Stage-1+ task number yet, so this was
  self-contained.
- **TASK-000 package structure -> actual should match roadmap**
  (maintainer's call): removed `src/pyflow/{interaction,io,simulation,
  util}/` -- all four were empty, undocumented stubs; grepped
  `knowledge-architechture.md` for any rationale and found none, including
  for what "simulation" was meant to mean as distinct from "engine".
  Added `src/pyflow/configuration/` per TASK-005. Folded the removed
  packages' presumed responsibilities into `engine/` (io, simulation,
  util) and `rendering/` (interaction), documenting this choice directly
  in each package's `CLAUDE.md` rather than leaving it implicit again.
  `demos/` was deliberately not created under `src/pyflow/` --
  `examples/` already fills that role at the repo root. That naming
  difference wasn't part of what was asked, so it's logged as a separate,
  non-blocking open item in `docs/planning/backlog.md` §1 rather than
  assumed.
- Checked off the related `docs/repository-manifest.md`
  `docs/handbook/`-vs-flat-file backlog item as moot, now that the flat
  file is gone -- the manifest's existing `docs/handbook/` section was
  already correct as a description of the future state.

### Decisions (continued, same day -- examples/demos naming, BRIEF, prompts/code+docs)
- **`examples/` vs. roadmap's `demos/`** (maintainer's call): kept
  `examples/` -- it's the better umbrella term (holds `golden-demos/`,
  `experiments/`, `tutorials/`, not just demos). Updated TASK-000's
  implementation text in `roadmap.md` to say `examples/`, and to make
  explicit which of its listed packages are `src/pyflow/` subpackages vs.
  top-level repository directories (previously conflated).
- **BRIEF vs. `prompts/global/project.md`** (maintainer's call: retire
  BRIEF into project.md): wrote `prompts/global/project.md` per KA-039.
  Deliberately dropped BRIEF's "Engineering Philosophy" bullet list too,
  not just "Current Direction" -- it turned out to duplicate
  `docs/engineering-principles.md`'s eighteen numbered principles (P-001
  through P-018), just as a shorter, looser paraphrase. Replaced with a
  pointer to that file instead, consistent with the same
  single-authoritative-source reasoning already applied to "Current
  Direction" and `implementation-plan.md`. Added the KA-039-required
  "institutional memory" content (knowledge should never depend on
  individual memory) and the explicit instruction to consult
  `roadmap.md`/`backlog.md`/`implementation-plan.md` for current state,
  neither of which BRIEF had. Deleted `prompts/common/BRIEF`.
- **`prompts/code/` and `prompts/docs/`** (maintainer's call: retire):
  deleted both. Updated `prompts/CLAUDE.md`, `prompts/common/CLAUDE.md`,
  and `prompts/global/CLAUDE.md` to stop describing them as pending and
  stop referencing BRIEF as current practice.
- This closes out the "Prompt directory layout mismatch" backlog item
  from earlier today completely -- both of its follow-on open questions
  are now resolved, not just logged.

### Decisions (continued, same day -- backlog §3 knowledge/content gaps)
- Went into this bucket expecting several open structural decisions
  (Physics Handbook granularity, Numerical Component Handbook structure,
  ICD location). Found that `knowledge-architechture.md` had already
  settled nearly all of them with exact filenames, same pattern as the
  glossary and AGENTS.md findings earlier today -- executed directly
  rather than asking, since there was nothing to decide:
  - Physics Handbook (KA-009..015): scaffolded
    `docs/handbook/physics/{README,incompressible-flow,heat-transfer,
    density,humidity,buoyancy,cloud-formation}.md`. Wrote a real
    `README.md` (organisational content). Removed the old, differently-
    named, entirely empty `docs/physics/{atmosphere,fluids,
    thermodynamics}.md`.
  - Numerical Component Handbook (KA-016..025): scaffolded
    `docs/handbook/numerical-methods/{fvm,meshes,variable-placement,
    fluxes,advection,diffusion,time-integration,
    pressure-velocity-coupling,linear-solvers,boundary-conditions}.md`.
  - ICDs (KA-030): scaffolded `docs/architecture/icds.md`. Noted but did
    not act on a related gap found in passing -- KA-029 also specifies
    `docs/architecture/engine.md`, which doesn't exist under that or an
    equivalent name; `overview.md` might be intended to serve that role,
    or might not. Left for `docs/architecture/CLAUDE.md` and the backlog
    to track, not guessed at.
  - None of the actual physics/numerics *content* was written -- that's
    real domain knowledge requiring citations, explicitly left as
    separate follow-on work, consistent with how the backlog already
    split "structure decision" from "content" as different line items.
- **ADR-002/ADR-003**: asked the maintainer how to source the "why" --
  chose to draft from standard, well-established CFD domain knowledge
  (citing Versteeg & Malalasekera) rather than wait for the maintainer's
  own reasoning, since none had been recorded anywhere. Wrote both at
  `adr/ADR-002-fvm-first.md` and
  `adr/ADR-003-modular-numerical-strategies.md`, following `adr/`'s real,
  already-in-use 3-digit convention (`adr/README.md`) rather than KA-027/
  028's unfollowed `docs/adr/ADR-000X-*.md` path -- same reasoning as
  every other "KA says X, reality already established Y" case today:
  `adr/ADR-001-knowledge-graph.md` is a real, accepted decision already
  referencing that path, so it wins over an unfollowed spec. Corrected
  `repository-manifest.md`'s ADR rows to match (they had inherited KA's
  4-digit/differently-slugged naming, and marked ADR-001 as merely
  "Draft" despite it being complete and Accepted -- fixed both).
- **MVP Definition / Upgrade Paths** (asked, maintainer's call: extract
  per KA): KA-031/032 specify these as their own files under
  `docs/implementation/`, not sections inside `implementation-plan.md` --
  which is where this morning's earlier roadmap/plan reconciliation had
  left them. Extracted to `docs/implementation/mvp.md` (using KA-031's
  structure, with the richer existing category breakdown folded in) and
  `docs/implementation/upgrade-paths.md` (expanded from the existing 5
  categories to KA-032's full 12). Found and fixed one real inconsistency
  while merging: the old Pressure-Velocity Coupling chain read
  "Projection -> SIMPLE -> PISO," implying PISO was the most-advanced
  target, but the MVP already starts at PISO -- corrected to follow
  KA-032's framing (PISO as the starting point, SIMPLE/SIMPLEC as
  situational alternatives) instead of silently keeping the
  self-contradictory version.
- Backlog's "Upgrade Paths -- not written anywhere yet" line turned out
  to be stale -- the content already existed inside
  `implementation-plan.md`, just not extracted or complete. Corrected
  rather than treated as still accurate.

### Decisions (continued, same day -- dependency-tree.md reformat)
- Executed the last queued prompt (`task-dependency-tree-reformat.md`) as
  written: converted `docs/planning/dependency-tree.md` from CRLF to LF,
  wrapped the ASCII tree in a fenced code block, and removed the blank
  line that had been pasted between every single tree line (an artifact,
  not intentional spacing) -- verified the full node set and connector
  characters are unchanged. Formatting only, per the prompt's explicit
  scope: did not decide whether this file should eventually be derived
  from Engine Architecture/ICDs instead of hand-maintained -- that's
  still open. Updated `docs/planning/CLAUDE.md` (previously a bare
  placeholder) to record the file's status and flag that open question
  for whoever touches it next.
- This clears the entire original four-item prompt queue from the
  2026-08-15 12-07 audit (`repo-hygiene-configs`, `pre-commit-config`,
  `dependency-tree-reformat` all executed; `prompts-subdir-agents-md`
  superseded, see earlier entry).

### Decisions (continued, same day -- remaining loose threads)
- **`docs/architecture/engine.md`**: KA-029 specifies it as its own file,
  distinct from the pre-existing (KA-less) `overview.md`. Scaffolded as
  an empty stub, resolving the ambiguity noted earlier today rather than
  leaving it open.
- **Golden Demo specification**: KA-035 specifies
  `docs/implementation/golden-demos.md`, not somewhere under
  `examples/golden-demos/` as originally assumed. Written with real
  content (KA-035's initial-demo requirements and Definition of Done,
  cross-referenced to `docs/implementation/mvp.md`) -- this is structural
  content directly sourced from already-decided specs, not invented
  domain knowledge, so it didn't need the same caution as physics/
  numerics content. `examples/golden-demos/CLAUDE.md` updated to point to
  it.
- **`docs/references/*.md`**: checked, still genuinely blocked on
  handbook content (unwritten) -- left deferred, no change.
- **`docs/planning/releases.md`**: its stated blocker (MVP/Upgrade Paths)
  is now cleared, but `knowledge-architechture.md` has no releases-related
  entry at all -- there's no spec to build from. Left deferred rather
  than inventing a release process nobody asked for; still low priority
  per the original audit.
- **CRLF cleanup**: asked to fix the two files flagged earlier
  (`CHANGELOG-DESIGN.md`, `adr/README.md`). A repo-wide check first,
  rather than trusting the original backlog's file list, found 10 more
  `.md` files also had CRLF endings that the original 2026-08-12 audit
  had missed entirely. Converted all 12 non-`dependency-tree.md` CRLF
  files found this session (content verified unchanged -- line-ending-
  only diffs). Zero CRLF `.md` files remain.
- **`CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`/`SECURITY.md`**: reviewed, no
  change -- the existing conscious-deferral note still holds and nothing
  today changed that assessment.
### Audit (continued, same day -- full repository review)
- Performed a second, full-repository audit covering everything, not only
  the 2026-08-12 checklist's scope. Findings logged as
  `docs/planning/backlog.md` §§5-12; the backlog's header was rewritten
  to distinguish the two audits. No decisions were taken and no other
  document was changed -- this pass was a review, and several findings
  turn on questions (generate-vs-hand-maintain the manifest, where the
  numerical survey belongs, Level 7's fate) that are the maintainer's to
  settle, not something to resolve silently mid-audit.
- Headline findings, recorded here so the shape of the result survives
  even if the backlog is later restructured:
  - **The repository has zero commits.** Everything is untracked. This
    contradicts KA-003 ("use Git as the primary historical record") and
    `docs/practices.md` step 7, and means the whole design phase --
    including this log -- exists only in one working tree. Highest
    priority item in the repository.
  - **Stage 0 is barely started, contrary to how §§1-4 read.** Zero `.py`
    files exist, so TASK-000's acceptance criteria cannot pass and both
    `pyproject.toml`'s hatchling target and MyPy's `packages = ["pyflow"]`
    already point at nothing. TASK-003/004/005/006/007/010 are untouched
    and TASK-004 (CI) was not tracked anywhere at all. §§1-4 were
    pre-Stage-0 hygiene, not Stage 0.
  - **Both self-declared authoritative inventories are wrong about the
    repository.** `docs/repository-manifest.md` has wrong paths, a
    handbook section describing ~35 files that don't exist, an `engine/`
    section for a directory that doesn't exist, and omits most of the
    repository. `knowledge-architechture.md` has six `Name:` paths the
    project never followed and at least nine stale `Status:` fields.
    Both failed the same way -- hand-maintained status duplicated across
    two places -- which is why the manifest item is framed as a
    generate-vs-maintain decision (P-002) rather than a rewrite.
  - **The Numerical Method Survey already exists.**
    `docs/planning/numerical-frameworks.md` is a complete 17 KB survey of
    eight method families plus a compatibility section -- effectively
    KA-007 and KA-008 delivered, but under a path no spec references, so
    both inventories still list them as missing and `ADR-002` cites none
    of it despite it being the survey that decision needed.
  - **Release / Stage / Capability Level are three live vocabularies**,
    none defined in the glossary, and roadmap Stages and plan Levels
    genuinely diverge (Level 7, alternative numerical frameworks, has no
    roadmap stage; the plan's "Dam Break" golden demo is unreachable from
    the roadmap). August's reconciliation settled authority between those
    two documents but not their content.
  - Smaller: 29 of 45 `CLAUDE.md` files are still the generic
    placeholder; `docs/practices.md` steps 1 and 5 still say "read/update
    the handbook" and were missed when `docs/handbook.md` was retired
    earlier the same day; documentation Definition of Done is defined
    three times; `numerical-frameworks.md` has an unbalanced code fence;
    this log's first entry cites a 12-07-2026 entry that is not in this
    file.

### Decisions (continued, same day -- self-consistency pass before first commit)

Goal: put the repository into a self-consistent state for its first
commit. Scope was deliberately narrow -- fix divergence and duplication
now; leave content-writing, code and open decisions on the backlog.
Everything below is a consistency repair, not a change of project
direction.

- **Numerical Method Survey moved into the handbook.**
  `docs/planning/numerical-frameworks.md` was KA-007 and KA-008
  effectively delivered, filed under a planning name no spec referenced.
  Split at its own "Numerical Method Compatibility" heading into
  `docs/handbook/numerical-methods/overview.md` (KA-007) and
  `compatibility.md` (KA-008) -- the KA-specified paths -- with the
  original file removed. Content unchanged apart from new headers and the
  repair of an unbalanced code fence that had left the trailing
  method-classification tree in an unterminated code block. `ADR-002` now
  cites the survey it always should have; `docs/planning/CLAUDE.md`
  records that scientific reference material belongs in the handbook, not
  in planning, so this does not recur.
- **`docs/repository-manifest.md` rewritten (v0.1 -> v0.2).** v0.1
  described ~35 handbook files that never existed, put four documents at
  the wrong paths, described a top-level `engine/` directory that does not
  exist, and omitted most of the repository -- while asserting itself the
  authoritative inventory. Rewritten against the actual tree. Two
  structural changes: the 45 `CLAUDE.md` files are now tracked by an
  explicit collective rule rather than 45 rows, and the duplicated
  documentation Definition of Done was removed in favour of a reference to
  `docs/documentation-guidelines.md` (P-011). The generate-vs-hand-maintain
  question is **not** settled -- it is recorded at the top of the file and
  in the backlog. Rewriting it stops it misleading readers; it does not
  answer whether it should exist in this form.
- **`knowledge-architechture.md` corrected.** Six `Name:` paths that named
  locations the project never used (KA-006, KA-026/027/028, KA-033,
  KA-036) now name actual paths; ten `Status:` fields were brought in line
  with reality. A maintenance note at the top makes the invariant explicit
  and pairs the file with the manifest, which is the pairing whose absence
  let both drift.
- **Progression vocabulary defined once.** Release, Stage and Capability
  Level were three live terms with no definitions and no stated
  relationship. All three are now in `docs/glossary.md`, and the
  Stage/Level correspondence table lives in `roadmap.md` (the execution
  document) with `implementation-plan.md` referencing rather than
  restating it. P-004 was reworded from "every release after Release 0" to
  "every stage after Stage 0" -- the intent was always Stages; the project
  has no release process. `README.md`, `practices.md` and
  `prompts/global/project.md` were aligned to match.
- **Capability Level 7 divergence made explicit, not resolved.** Level 7
  (SPH/FLIP/PIC) has no corresponding roadmap Stage, which makes the
  plan's "Dam Break / Free Surface" golden demo unreachable. Recorded in
  both documents and in the backlog. Adding a Stage or dropping the Level
  are both real scope changes and are the maintainer's call.
- **`docs/practices.md` Session Workflow fixed.** Steps 1 and 5 still said
  "read/update the handbook," meaning the project-meta `docs/handbook.md`
  retired earlier the same day; read literally they told every session to
  begin by opening sixteen empty scientific files. They now point at the
  current design state (`roadmap.md`, `backlog.md`, this log). `README.md`
  had been updated for that retirement; `practices.md` was missed.
  Relatedly, the glossary's "Project Specification" entry described a
  document that does not exist -- redefined as the set of documents that
  actually hold that role.
- **The standing CLAUDE.md-maintenance rule is now recorded in
  `docs/practices.md`**, closing a backlog §4 item. It previously existed
  only in the root `CLAUDE.md` and in this log.
- **Stage 0 status table added to `roadmap.md`.** The roadmap described
  Stage 0's tasks without ever stating where the project was against them,
  so "nearly done with the pre-Stage-0 checklist" read as "nearly done
  with Stage 0." It is not: TASK-000 has not started and there are no
  Python files at all.
- Stale cross-references repaired in `ADR-002`, `ADR-003`,
  `prompts/global/project.md` and `prompts/global/CLAUDE.md` -- all four
  still pointed at `implementation-plan.md` for the MVP definition and
  upgrade paths, which were extracted to `docs/implementation/` earlier
  the same day.

### Correction to this log's first entry

The 15-08-2026 "Open Questions" entry cites a "`CHANGELOG-DESIGN.md`
(12-07-2026 entry)" describing the handbook as "canonical memory." No
such entry exists in this file, which contains only 15-08-2026 sections.
That content most likely lived in the retired `docs/handbook.md` and was
not carried across when it was retired; it should be treated as lost. The
original entry is left as written -- this log is append-only, and
rewriting it would destroy the record of what was believed at the time.

### Decisions (continued, same day -- knowledge-architecture rename)
- Renamed `docs/planning/knowledge-architechture.md` to
  `knowledge-architecture.md`, correcting a typo in the filename of one of
  the project's two most-referenced planning documents, and updated all 35
  references across 22 files. Done deliberately before the first commit:
  a pre-history rename costs nothing, while a post-history one carries
  every reference through the log.
- `docs/CHANGELOG-DESIGN.md` was left untouched -- same treatment as the
  `AGENTS.md` -> `CLAUDE.md` rename earlier the same day. This log is
  append-only, and its eight existing references spelled the filename the
  way it was actually spelled at the time. Read them as referring to
  `docs/planning/knowledge-architecture.md`.

### Decisions (continued, same day -- first commit and backlog restructure)
- **Initial commit made.** 118 files, branch `master`. The repository's
  entire design phase had existed only as untracked files in one working
  tree, contradicting KA-003 and `docs/practices.md` step 7. This was the
  highest-priority finding of the second audit and it is now closed.
  `.gitattributes` normalisation verified immediately afterward via
  `git ls-files --eol`: 82 files `i/lf w/lf`, 36 `i/none w/none` (the
  empty ones), zero CRLF. Branch naming is unresolved -- history begins on
  `master` -- and is now Part I item F1.
- **`docs/planning/backlog.md` restructured from an audit log into an
  ordered work queue.** It had been organised by *when things were
  discovered*, which is the wrong axis for a document whose job is
  telling you what to do next. Now three parts: **Part I**, the ordered
  Stage 0 work queue (Groups A-F, dependency-ordered, each item stating
  what it produces and how completion is checked); **Part II**, work
  deliberately deferred past Stage 0, each with a reason and an unblock
  condition; **Part III**, the 2026-08-12 and 2026-08-15 audits preserved
  verbatim as the record of why things are the way they are. Everything
  outstanding in Part III was promoted into Part I or II, so Part III is
  now read-only history. `roadmap.md`'s Stage 0 Completion Criteria point
  at Part I as the route to satisfying them; Part I's final item (F2)
  maps each criterion back to the evidence that proves it.
- Three gaps surfaced while building the queue that no previous audit had
  found, all now Part I items:
  - **The development toolchain is not installed.** `uv` and `make` are
    absent from the machine and the Python on PATH is 3.10.5, against a
    `requires-python = ">=3.12"`. Every TASK-001/TASK-002 acceptance
    criterion is phrased as `make install` / `make test`, so none of them
    can be verified until this is fixed. This is why §2's tooling items
    were closed with an "unverified" caveat; the caveat now has an owner
    (A1).
  - **The rendering library choice is an unrecorded architectural
    decision.** TASK-007 says "select an initial rendering library" and
    never says which or on what basis, while fixing the rendering
    subsystem's dependencies, platform support and event-loop shape for
    the life of the project. It meets `adr/README.md`'s own criteria for
    requiring an ADR, so A2 makes it ADR-004 rather than something
    settled inline during implementation.
  - **"Documentation has a complete first draft" is not auditable as
    written.** 25 tracked `.md` files are empty and nothing says whether
    that fails the criterion. A3 proposes a mechanically checkable
    reading -- no file tracked in the manifest is empty at Stage 0 exit,
    each either drafted or explicitly retired -- with the eleven
    `planning/**.yaml` files carved out as data rather than
    documentation, keeping their existing deferral. Recommended, not
    imposed: it needs confirmation because it sets Group E's scope.

### Decisions (continued, same day -- Stage 0 queue decisions A1-A3)
- **A3 decided (maintainer's confirmation):** "documentation has a
  complete first draft" now means *no file tracked in
  `docs/repository-manifest.md` is empty at Stage 0 exit* -- each is
  either a genuine first draft or explicitly retired and removed from the
  manifest. Recorded beside the Stage 0 Completion Criteria in
  `roadmap.md`. The eleven `planning/**.yaml` files are carved out as
  data rather than documentation and keep their existing deferral. This
  fixes Group E's extent at exactly the 25 currently-empty files, so it
  was expanded from one unbounded checkbox into one item per file
  (E1a..E12), grouped by area, with the two entries worth writing first
  called out: `fvm.md` (the decided method, cited by ADR-002) and
  `incompressible-flow.md` (the MVP's physical model).
- **A1 reshaped after a correction (maintainer's direction: use a managed
  environment).** `uv` and `make` cannot live inside a Python virtual
  environment -- `uv` is a standalone binary that *creates* venvs, and
  `make` is a system tool -- so "managed environment" resolves to three
  real options, now written out in A1a: host `uv` plus a uv-managed venv
  (light and native, but `make` on Windows is the awkward part and
  reproducibility is documented rather than enforced); a dev container
  (reproducible by construction, and CI can reuse the image, but running
  a GUI from a container on Windows means WSLg or X forwarding and
  hardware-accelerated OpenGL is fiddly); or a hybrid. **A1a and A2
  constrain each other** -- a container without hardware OpenGL rules out
  some rendering options -- so they should not be decided independently.
  Split into A1a (decide) and A1b (stand it up, and document it in
  `README.md`).
- **A2 reshaped into survey-then-decide**, following the precedent that
  worked for the numerical framework (KA-007 survey -> ADR-002). A2a
  writes the survey into `docs/architecture/rendering.md` -- an empty
  file with no KA entry, which this gives a purpose and removes from
  Group E -- and A2b records the decision as ADR-004.
  - **Correction recorded:** OpenFOAM, raised as a candidate, is a C++
    finite volume CFD *solver*, not a renderer; it is already cited in
    ADR-002 as evidence for the FVM decision, which is its right role.
    Its visualisation is ParaView, built on **VTK** -- so that instinct
    points at the VTK/PyVista lineage, which is a serious candidate.
  - Candidate families recorded for the survey: scientific visualisation
    toolkits (VTK/PyVista); GPU-accelerated scientific visualisation
    (VisPy, wgpu-py/pygfx); thin graphics layers (ModernGL, pyglet,
    glfw+PyOpenGL); GUI frameworks (PySide6/Qt); and matplotlib, which is
    too slow for a real-time loop but likely wanted alongside the winner
    for validation plots and golden-demo regression images.
  - Assessment axes recorded, including one that constrains the field
    more than any other and had not been noticed before:
    **offscreen/headless rendering**. `docs/implementation/
    golden-demos.md` requires demos to produce visual output *and* be
    included in regression testing, which means the renderer must work in
    CI with no display.
- Two further gaps found while expanding Group E, both now items:
  `README.md` has no development instructions although KA-001 requires
  them and Stage 0's exit criterion assumes them (E11); and
  `docs/architecture/repository.md` overlaps `docs/repository-manifest.md`
  closely enough that keeping both needs a stated division of labour
  (E2b).

### Decisions (continued, same day -- A1a development environment)
- **A1a decided (maintainer's call): host `uv` + uv-managed venv, with CI
  enforcing reproducibility.** `uv` at user level, `uv python install
  3.12` supplying the interpreter, `.venv/` for project dependencies,
  `make` installed on the host.
- **Why not a dev container**, despite it being reproducible by
  construction and shareable with CI: Stage 0 *ends* by opening a
  rendering window (TASK-007; TASK-010's acceptance criterion is `make
  demo` starting the application). Running a GUI from a container on
  Windows means WSLg or X forwarding, with hardware-accelerated OpenGL
  fiddly at best. Paying that for the whole of Stage 0 to solve a problem
  the CI pipeline (TASK-004) already solves is the wrong trade.
- **Consequence for A2:** this decision *removes* a constraint rather than
  adding one. A container without hardware OpenGL would have ruled out
  some rendering candidates; none are excluded on that basis now, so the
  survey keeps every family on the table. Headless rendering remains a
  hard requirement, but for CI and golden-demo-regression reasons rather
  than local-development ones.
- Noted in A1b: Git for Windows does not ship `make`, so it needs an
  explicit install (scoop/winget/choco/MSYS2). If `make` proves more
  trouble on Windows than it is worth, that is a change to `roadmap.md`
  TASK-002 -- which names a `Makefile` and phrases every acceptance
  criterion in terms of it -- and should be recorded as such rather than
  worked around locally.
