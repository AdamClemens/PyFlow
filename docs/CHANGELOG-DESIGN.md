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

### Decisions (continued, same day -- completeness check on the Stage 0 queue)
Checked Part I against the Stage 0 Completion Criteria and KA-034's
Definition of Done rather than assuming the queue was complete. Five gaps
found, all now items. Recorded here because the largest of them is a
requirement the project had written down twice and still not scheduled.

- **D5 -- the "Empty Window" golden demo was never scheduled.** D4
  produces a bootstrap application; that is not the same artifact.
  `implementation-plan.md` gives Capability Level 0 the golden demo "open
  a rendering window, display an empty simulation" and lists
  Empty Window / Rendering in its Golden Demos table, and
  `docs/implementation/golden-demos.md` requires every demo in that table
  to have an entry, runnable code, and inclusion in **regression
  testing** -- a Definition of Done materially stricter than "the app
  starts". Three artifacts were missing: the entry, code in
  `examples/golden-demos/`, and a test in `tests/golden/` (both
  directories empty, and both existing precisely for this). This is also
  what makes A2a's headless-rendering axis a hard requirement rather than
  a nice-to-have: a demo that cannot run in CI is not in regression
  testing and so fails its own Definition of Done.
- **B4 -- `pre-commit` has never been run.** `make install` runs
  `pre-commit install`, which wires up the hook without executing it. The
  first `pre-commit run --all-files` will rewrite source (`ruff --fix`,
  `ruff-format`) and put `mypy strict = true` against B1's placeholder
  modules. Made a deliberate step so the result is inspected rather than
  discovered mid-commit.
- **F2 -- nothing swept the inventories for what Stage 0 itself creates.**
  ADR-004, `docs/architecture/rendering.md`, `uv.lock`, the CI workflow,
  every module under `src/pyflow/`, the test suite, the golden demo and
  its test are all new artifacts, and the manifest's `src/`, `tests/`,
  `examples/` and `.github/` sections carry notes that will become wrong.
  `practices.md` already carries the standing rule to update the manifest
  and the KA spec together; F2 is the backstop, not a substitute for it.
  The two inventories drifting apart is the failure this repository has
  already had once.
- **E13 -- the root `CLAUDE.md` has no development commands.** KA-037
  requires it to carry the minimum essential project-wide instructions,
  and Stage 0 criterion 5 is that agents have contextual guidance; it
  currently says nothing about building, testing, linting or type
  checking, because until B2/B3 none of those worked.
- **A2a is to be run interactively** (maintainer's preference). The
  rendering comparison's weightings -- turnkey glyphs and legends against
  dependency weight, how seriously to take Level 9's GPU ambitions now,
  how much interactive UI is actually wanted -- are project-specific and
  live with the maintainer rather than in any document. A knowledge
  snapshot to May 2026 is accepted as the basis, so it does not block on
  live version checking; the snapshot date goes in the document so a
  later reader can tell a stale claim from a wrong one.

### Decisions (continued, same day -- runtime dependency moved into Stage 0)
- **A5: the runtime array/numerics dependency moves from Part II into
  Group A** (maintainer's call). The deciding argument is Stage 0
  criterion 6 -- *a developer can clone the repository and begin Stage 1
  immediately.* Stage 1 opens with TASK-011 (coordinate system) and
  TASK-012 (structured Cartesian mesh), neither of which can be written
  without an array library, so deferring the choice would have meant
  Stage 1 beginning with an unmade architectural decision and criterion 6
  being true only in a narrow sense.
- It is ADR-worthy on `adr/README.md`'s own test: the choice constrains
  field storage layout (Stage 2), the operator implementations
  (Stages 3-4), and above all Capability Level 9, where whether the array
  type has a GPU-backed counterpart with a compatible interface decides
  whether GPU execution is an upgrade or a rewrite.
- Noted that A2b and A5 both produce ADRs and `adr/README.md` makes
  numbering sequential and permanent, so 004 goes to whichever lands
  first rather than being pre-assigned to the rendering decision. Also
  noted for A2b: if the rendering choice lands on a GPU-buffer-sharing
  stack, the two decisions stop being independent.

### Decisions (continued, same day -- Blast Radius rule, toolchain installed)
- **New practice adopted: Blast Radius** (maintainer's proposal). Before
  making a change, work out what else references, restates, tracks or
  depends on the thing being changed, and update all of it in the same
  change; where something in the radius cannot be updated now, record the
  divergence explicitly rather than leaving it silent.
  **Where this sat before:** roughly 60% latent, but scattered and
  narrow. Root `CLAUDE.md` said documentation evolves alongside code;
  `docs/CLAUDE.md` had the *reactive* version (fix inconsistencies you
  find); `docs/practices.md` had two *specific* instances (update the
  nearest `CLAUDE.md`; update the manifest and KA spec together);
  P-006 and P-011 carry the underlying philosophy. What was missing was
  the general, proactive form -- enumerate the radius *before* changing,
  as a discipline rather than as cleanup. So: a genuine expansion, not a
  restatement.
  **Justified by this repository's own history** -- four documented
  instances, each caught only by a later audit: `practices.md` missed
  when `docs/handbook.md` was retired; four documents left pointing at
  `implementation-plan.md` after the MVP and upgrade paths moved out; the
  manifest describing ~35 files that never existed; and the numerical
  survey filed where both inventories reported it missing. The
  `AGENTS.md` -> `CLAUDE.md` rename is the counterexample where the
  discipline was applied and nothing broke.
  **Placed in `docs/practices.md`** (KA-003 -- how work is conducted),
  not in `engineering-principles.md`, since the philosophy is already
  covered by P-006/P-011 and what was missing is the action. The two
  pre-existing specific rules are folded underneath it as instances.
  Propagated in the same change -- deliberately demonstrating the rule --
  to root `CLAUDE.md` (compact statement, since agents read it),
  `docs/CLAUDE.md` (its Validation section now names itself the reactive
  case), and KA-003's content requirements.
- **Toolchain installed** (maintainer, 2026-08-15): `uv 0.12.5`,
  `GNU Make 4.4.1`, CPython 3.14.7. A1b's first three steps are closed.
- **New question raised by the install, now the remainder of A1b:** the
  repository is configured for Python 3.12 in three places
  (`requires-python`, `ruff target-version`, `mypy python_version`) and
  3.14.7 is what is installed. Developing on 3.14 against a 3.12 floor is
  a legitimate configuration but must be deliberate, and the alternative
  is pinning to 3.12 or raising the floor. **This is not independent of
  A2a and A5:** rendering and array libraries are exactly the kind of
  dependency that lags a recent Python release, so wheel availability on
  the chosen version constrains both, and C2's CI matrix must agree with
  whatever is chosen.

### Decisions (continued, same day -- Python policy, stack decision restructured)
- **Python version policy decided (maintainer's call): track the current
  release.** The previous 3.12 was arbitrary rather than chosen. PyFlow
  has no external consumers, so there is nothing to stay compatible with,
  and the cost of moving forward only grows the longer it is deferred.
  **The condition that flips this is recorded with it**: the moment
  someone else depends on PyFlow, a conservative floor starts to earn its
  keep and the policy should become deliberate stability.
  Applied at 3.14 across all four places that must move together --
  `requires-python`, the `Programming Language :: Python` classifier,
  `[tool.ruff] target-version`, `[tool.mypy] python_version` -- plus
  `roadmap.md` TASK-001, which no longer names 3.12. Policy written up in
  `docs/practices.md`.
  Both pinned tool versions were **verified** to accept 3.14 before the
  bump (`ruff 0.16.3` with `--target-version py314`, `mypy 2.3.1` with
  `--python-version 3.14 --strict`) rather than assumed -- the same
  discipline applied to the hook versions themselves.
  Consequence noted in C2: under a track-current policy a *version*
  matrix in CI would contradict the policy, so the open CI question is
  the OS matrix; and CI becomes the thing most likely to catch a new
  Python release breaking a dependency, which argues for pinning the
  runner's Python explicitly rather than letting it drift.
- **A2 and A5 merged into a single three-step stack decision
  (maintainer's insight).** They were never independent: the array
  library determines what a renderer can read without a copy, and the
  renderer determines what memory layout and device the array library
  must produce. Assessed separately, each would have been chosen against
  assumptions about the other.
  Now: **A2a** surveys the *combinations* and builds a compatibility
  matrix; **A2b** chooses the *class* of solution (the architectural
  commitment -- e.g. CPU arrays with a scientific-viz toolkit, versus GPU
  arrays sharing buffers with a GPU renderer); **A2c** chooses the
  *instances* within that class, which should be comparatively cheap to
  change if A2b's interface work is done properly. A5 is folded in and no
  longer stands alone.
  The maintainer's ambition to support **more than one renderer**, or
  different renderers per domain, is recorded as an assessment axis in
  its own right: which classes keep a second renderer cheap, and which
  quietly assume there is only one? A class that couples the array type
  to a single renderer's buffers is buying performance with that
  flexibility, and that trade should be explicit rather than discovered.
  This is consistent with ADR-003 -- rendering behind a stable interface,
  selected at construction.
- Blast radius of that restructure, handled in the same change:
  `docs/architecture/rendering.md` is **no longer** claimed by A2a (the
  survey goes to a new `compute-and-rendering-stack.md`, since it covers
  both axes and `rendering.md` would be the wrong name). It returns to
  Group E as **E2c** with its original job -- the architecture of the
  renderer actually adopted, written *after* A2b/A2c. Group E's header
  and E2's heading corrected, F2's artifact list updated, and both
  documents added to `docs/repository-manifest.md`.

### Decisions (continued, same day -- KA-034 superseded)
- **A4 decided (maintainer's call): retire KA-034.** The maintainer's
  framing was better than the one offered -- the artifact's *purpose*
  ("define repository and development infrastructure required before
  simulation implementation") is already satisfied, just realised as two
  documents rather than one file: `docs/planning/roadmap.md`'s Stage 0
  section is the specification, and `docs/planning/backlog.md` Part I is
  the ordered queue that executes it. Writing a separate `stage-0.md`
  would duplicate the first (P-011) and set up a `stages/` directory
  competing with the roadmap as Stages 1-12 arrive.
- **Marked `superseded`, not `complete`.** `complete` would send a reader
  after a file that does not exist. That required a fourth value in the
  KA status vocabulary, which the maintainer approved conditional on it
  making long-term sense -- it does: over twelve stages artifacts will be
  replaced; `adr/README.md` already uses "Superseded" in the ADR
  lifecycle so the term is not novel here; and the alternatives were
  deleting the entry (losing the record, against P-001) or misreporting
  it. `superseded` is now defined in the KA Artifact Record Schema as
  "purpose served elsewhere, the named file will not be written, entry
  kept so the record survives, must say what replaced it".
- **Nothing was dropped, and this was checked rather than assumed.**
  KA-034's Definition of Done was compared item by item against
  `roadmap.md`'s Stage 0 Completion Criteria *before* retiring it. Five
  were already covered. Two were stated in KA-034 but only *implied* in
  the roadmap -- "CI executes" and "Stage 0 infrastructure is
  reproducible" -- and are now criteria 8 and 9 there, at the
  maintainer's explicit instruction to formalise the implied
  requirements. A pipeline that exists but never runs satisfies the
  looser reading of criterion 2 and fails criterion 8, which is the point
  of stating it.
- Worth recording for future readers, since it inverts the natural
  assumption: KA-034's DoD was the **weaker** of the two. It required
  only that "documentation structure exists" (satisfied today) where the
  roadmap requires a complete first draft (A3: no empty tracked file),
  and it was silent on rendering where the roadmap requires a working
  window. Had KA-034 been treated as authoritative, Stage 0 would have
  looked roughly 70% done instead of roughly 15%.
- Blast radius handled in the same change: KA §5 status vocabulary,
  KA-034's `Name:` and `Status:` and resolution note, `roadmap.md`'s
  criteria (now nine) and a pointer recording that this section *is* the
  Stage 0 specification, the manifest's `docs/implementation/` note,
  backlog A4, the Part I preamble, F3's evidence mapping, C2's reference
  to CI as a named criterion, and two Part III entries.

### Correction (2026-08-15, later the same day -- Python policy phrasing)
The Python version policy entries above, and the corresponding text in
`docs/practices.md`, `pyproject.toml`, `roadmap.md` and
`docs/planning/backlog.md`, described the decision as "track the current
Python release" / "track-current policy". That overstated what was
decided. The maintainer's actual instruction: PyFlow does not have to
stay on the latest release continuously -- periodically check whether
upgrading would *benefit* the project, and upgrade when it does. All five
documents were corrected in place to this phrasing (not appended
separately, since none of them are append-only logs); only this entry is
handled as a correction, because this log is. The Python version chosen
(3.14) is unchanged -- only the description of the ongoing policy was
wrong, not the decision reached under it.

### Decisions (continued, same day -- Integrity rule added to root CLAUDE.md)
- **Added an explicit "Lying is never an option" rule to the root
  `CLAUDE.md`** (maintainer's instruction, prompted by discomfort at
  phrasing used earlier in this session -- see the correction above and
  the KA-034 discussion, where "misreporting it" was used to describe
  mislabelling a superseded artifact as `complete`. That was about label
  accuracy, not a considered choice between honesty and convenience, but
  it read as though deception were a live option being weighed, which it
  is not and should never be presented as being).
  New "Integrity" section, placed early (after Core Responsibilities,
  before Planning Philosophy): report uncertainty, mistakes and bad news
  plainly and as soon as they are known; a wrong answer honestly labelled
  uncertain is recoverable, a confident fabrication is not. Framed as the
  general statement that the existing "say so explicitly" instances (the
  Blast Radius rule, the Validation section) already follow from, rather
  than a new and separate concern.

### Decisions (continued, same day -- A2a first draft)
- **First draft of `docs/architecture/compute-and-rendering-stack.md`
  written** (A2a). Surveys seven array/numerics libraries (NumPy, CuPy,
  PyTorch, JAX, Numba, Taichi, NVIDIA Warp, plus PyOpenCL and Dask Array
  noted for completeness) against six renderer candidates, builds a
  coupling matrix, and groups the results into three candidate classes.
  Explicitly marked DRAFT and not yet reviewed against the maintainer's
  priorities -- written to open the interactive discussion the item
  calls for, not to close it.
  **Headline finding:** almost every GPU-array-library × general-purpose-
  renderer pairing in the matrix is unproven at this snapshot (marked 🟡
  or ❔) -- host round-trips are the reliable fallback, and true
  zero-copy GPU sharing (DLPack into wgpu, CUDA-GL interop) is real
  engineering risk that has not been spiked. The only fully-native path
  found is **Taichi**, whose GGUI renderer reads Taichi fields directly
  because compute and render share one runtime -- at the cost of locking
  the numerical-operator implementation into Taichi's DSL rather than
  NumPy-shaped code, and of making a second, different renderer for the
  same data path expensive rather than cheap.
  Confidence flagged per claim throughout rather than presented
  uniformly, per the knowledge-snapshot caveat this item carries and the
  root `CLAUDE.md` Integrity rule -- lowest confidence on: current
  headless/offscreen support for VisPy, wgpu/pygfx and Taichi GGUI
  specifically (§7.1, potentially disqualifying for D5 rather than
  merely inconvenient); actual DLPack-to-wgpu maturity (§7.2); NVIDIA
  Warp's ecosystem maturity relative to Taichi, which is why Warp was
  surveyed but not built into the class list (§7.3); and Array API
  standard conformance across the NumPy-shaped libraries (§7.4).
  Added to `docs/repository-manifest.md` at 🟨.

### Decisions (continued, same day -- Taichi verified live, correction issued)
- **Correction issued (per the Integrity rule adopted earlier today):**
  the maintainer stated Python 3.10 as "the latest supported version",
  apparently referring to Taichi's Python ceiling. This was checked
  directly rather than accepted -- 3.10 is not correct even as a Taichi
  ceiling. Live verification (see below) found the actual ceiling is
  3.13.
- **Taichi verified live** (PyPI JSON API, GitHub API, official docs --
  not the May-2026 knowledge snapshot the rest of the survey relies on,
  because this is now a live decision candidate rather than a background
  survey entry):
  - Wheels exist for cp39 through **cp313**. No cp314 wheel.
    `taichi-nightly` on PyPI is a dead, unrelated legacy package (0.5.11,
    Python 3.6-era classifiers) and not an escape hatch.
  - Latest release **v1.7.4, published 2025-07-31** -- confirmed via the
    raw GitHub releases API (not a model paraphrase; an earlier fetch had
    given a conflicting 2024 date from a summarized page and was not
    trusted). Over a year old as of 2026-08-15. Release gaps before it
    were widening: ~4 months, then ~7 months, then 13+ months and
    counting -- a genuine maintenance-slowdown signal, not just one gap.
  - GGUI headless rendering **confirmed working**, resolving the survey's
    open ❔: `ti.ui.Window(..., show_window=False)`, then
    `window.save_image()` in place of `window.show()`. Documented,
    official behaviour.
  - `docs/architecture/compute-and-rendering-stack.md` updated in place
    with all of the above, each item marked as a live verification rather
    than a snapshot claim, distinguishing it from the rest of the
    document's May-2026-snapshot basis.
- **New tension surfaced, not resolved here:** Taichi's version ceiling
  (3.13) conflicts with the Python version chosen earlier today (3.14).
  Framed in the survey as exactly the situation the periodic-review
  policy (`docs/practices.md`) exists to handle -- a real dependency
  constraint is a legitimate reason to revisit -- but left as an open
  decision for the maintainer rather than resolved unilaterally, alongside
  whether the slowing release cadence changes the "least engineering
  risk" read of Class 3 from the first survey pass.

### Decisions (continued, same day -- NVIDIA Warp verified live, Class 4 added)
- **NVIDIA Warp checked with the same rigour as Taichi**, at the
  maintainer's request, after the Taichi Python-ceiling/maintenance
  findings raised the question of whether it was actually the best
  native-GPU option available. All findings below are live checks
  (PyPI JSON API, GitHub releases API, NVIDIA's own docs), not the
  survey's May-2026 background snapshot.
  - **Maintenance is the inverse of Taichi's:** latest release v1.16.0,
    published 2026-08-03 -- 12 days before this check -- with roughly
    monthly releases for months before that (Apr through Aug 2026).
  - **Apache-2.0** licensed; compatible with BSD-3-Clause.
  - **Wheels confirmed for cp310 through cp314** -- supports the Python
    version already chosen. Unlike Taichi, choosing Warp does not force
    reopening the Python decision.
  - **CFD is an explicitly demonstrated use case** (2D incompressible
    turbulence, Navier-Stokes examples in Warp's own examples), not
    merely adjacent to its robotics/ML focus.
  - **CUDA-only** -- no ROCm, no Metal. CPU fallback exists
    (x86-64/ARMv8/Apple Silicon) but that is CPU execution, not
    GPU on non-NVIDIA hardware. Narrower than Taichi's stated
    multi-backend claim.
  - **The rendering story is architecturally different from Taichi's,
    not merely less mature -- this is the most important finding.** A
    first WebFetch summary claimed Warp "lacks built-in rendering"; a
    follow-up search found this was incomplete, and a third, more
    targeted fetch confirmed: Warp ships `warp.render.OpenGLRenderer`
    (built on **pyglet**, already an axis-2 candidate in this survey),
    with genuine headless support via EGL on Linux. But NVIDIA's own
    docs describe it as intended for *debugging and interactive
    playback*; the documented production path is `UsdRenderer`, an
    **offline USD export** for external tools (Omniverse/Blender/
    usdview), not an in-process real-time loop. Whether the debug
    renderer can consume Warp arrays without a host round-trip is
    **undocumented**, flagged as genuinely unconfirmed rather than
    assumed either way.
  - Catching the first fetch's incompleteness via a second, independent
    check (rather than passing along "no built-in rendering" as fact)
    is exactly the discipline the Integrity rule added earlier today
    calls for, applied to a tool result rather than to the maintainer's
    own claim this time.
- **Class 4 added** to the survey: Warp compute + a general-purpose or
  bridged renderer. Characterised precisely rather than favourably --
  Warp's kernel-DSL operator model carries the same cost against
  `ADR-003`'s replaceable-interface principle as Taichi's Class 3,
  *without* fully inheriting Class 3's native-rendering payoff, since
  Warp's own renderer is debug-grade. The trade is materially better
  maintenance and no Python conflict, against CUDA-only hardware scope
  and an operator layer that is still a DSL rather than NumPy-shaped
  code. Coupling matrix (§4) extended with a Warp row/column on the same
  basis as the other candidates, marked with the same confidence
  flagging.
- Explicitly **not decided here**: which class or instance wins. This
  entry records verification, not a recommendation -- A2b/A2c remain the
  maintainer's decision, to be taken with this and the Taichi findings
  both in view.

### Decisions (continued, same day -- versatility/performance deep dive on Class 2 vs Class 4)
- **Requested by the maintainer** after the Taichi/Warp comparison: which
  combination gives the most versatility/flexibility and best
  performance, with Class 2 (CuPy/PyTorch/JAX + general renderer) raised
  as a live contender now that Taichi's staleness makes Class 3 look
  weaker. All findings below verified live (GitHub/PyPI APIs, official
  docs, web search), not recalled from the survey's May-2026 snapshot.
- **CuPy, PyTorch and JAX are all independently healthy** -- none has
  Taichi's problem. Verified release dates: CuPy v14.1.1 (2026-06-01),
  PyTorch v2.13.0 (2026-07-08, ~4-6 week cadence, Meta-backed), JAX
  v0.11.0 (2026-07-16, almost exactly monthly for five months -- the most
  regular of any array library checked).
- **Hardware portability differs meaningfully within Class 2, corrected
  from treating it as monolithic.** CuPy has mature, official ROCm
  wheels (cupy-rocm-7-0). PyTorch has **official first-class ROCm
  support as of 2.7** (not a preview) plus auto-detected Apple MPS. JAX's
  ROCm story exists via a separate plugin but was **not verified this
  session and should not be assumed at parity** -- flagged rather than
  guessed. This is real versatility neither Class 3 (Taichi, multi-vendor
  but stale) nor Class 4 (Warp, CUDA-only) offers in the same verified
  form.
- **Quantified the host-round-trip fallback cost (survey doc section
  4.1)** rather than leaving it an unquantified risk. Using measured PCIe
  bandwidths (approx 12.5-32 GB/s) against the MVP's actual scope (2D,
  structured, uniform grid per docs/implementation/mvp.md): a generous
  2048x2048x4-field frame is approx 67 MB, costing single-digit
  milliseconds even on older PCIe generations -- well inside a 60fps
  budget, and effectively free at more realistic MVP grid sizes (512x512,
  sub-millisecond). Explicitly flagged as back-of-envelope reasoning, not
  a verified benchmark of actual PyFlow code, with a real profiling spike
  still recommended once code exists. **This changes Class 2's risk
  profile from the first survey pass**, where the round-trip was
  described as "defeating much of the point of a GPU array library" --
  that framing was true in principle but overstated for this project's
  near/medium-term scale; revised in the document. Noted explicitly where
  it stops holding: 3D at Stage 10 scales as N cubed, and the same
  fallback becomes disqualifying there, not merely slow -- future work,
  not a Stage 0-5 concern, and the reason the Array API standard is
  worth keeping the operator layer written against.
- **Domain-specific validation checked for both classes, with an
  in-progress self-correction worth recording.** Found and initially
  nearly cited **JAX-CFD** (Google's CFD-in-JAX project) as evidence for
  Class 2 -- then found, before using it, that its own commit history
  contains an explicit "no longer maintained" notice from Google
  (2026-02-24). Excluded as evidence; recorded as an example of the
  Integrity rule adopted earlier today applied to a near-miss rather than
  an actual mistake. The sources actually cited: **JAX-Fluids**
  (differentiable compressible/two-phase CFD, CPU/GPU/TPU) and
  **PhiFlow** (multi-backend differentiable PDE/fluid framework --
  literally "the exact same code runs a 2D NumPy sim or a 3D GPU
  PyTorch/JAX sim"), both real and both validating the swappable-backend
  *compute* pattern for fluid simulation specifically. Caveated
  honestly: both are themselves stale as a dependency would be judged
  here (JAX-Fluids' latest release 2025-03-21, PhiFlow's 2025-08-02) --
  though this matters less than Taichi's staleness would, since PyFlow
  would not depend on either, only take them as evidence the pattern
  works. **More important caveat: neither resolves the native-rendering
  question.** PhiFlow's own visualization answer is a web-based
  interactive UI, architecturally different from the native window/
  render-loop roadmap.md TASK-007 specifies -- these projects validate
  the compute side and sidestep the rendering question rather than
  answering it.
  For Class 4/Warp: found that Warp is the compute layer under NVIDIA's
  own **Newton** physics engine (via Isaac Lab), which explicitly
  includes MPM fluid/granular-material simulation -- real production
  validation from the vendor's own flagship stack, a different and
  arguably stronger kind of evidence than a research-community project.
- No clean head-to-head performance benchmark between the array
  libraries and Warp/Taichi was found for grid-based simulation
  specifically; not fabricated. Reported only what is documented: Warp's
  kernel model gives explicit per-thread control, most valuable for
  irregular/sparse/conditional workloads (later capability levels --
  AMR, immersed boundaries, unstructured meshes) rather than the MVP's
  uniform structured grid, where vectorised array operations are
  typically well-matched to the problem shape. Flagged as reasoning from
  general numerical-computing knowledge, not a verified PyFlow-specific
  result; a real micro-benchmark spike would be needed to settle this
  with numbers.
- docs/architecture/compute-and-rendering-stack.md updated throughout
  with all of the above: axis-1 rows for CuPy/PyTorch/JAX, a new section
  4.1, Class 2 and Class 4 both revised (not merely appended to) to
  reflect the round-trip finding, and a new "Proven for this domain
  specifically" row. No decision was taken -- A2b/A2c remain open.

### Decisions (continued, same day -- A2b decided, ADR-004 recorded)
- **Class decided: Class 2** (GPU-capable, NumPy-shaped array library --
  CuPy/PyTorch/JAX, instance not yet chosen -- paired with a
  general-purpose renderer, host round-trip accepted as the default
  coupling). Recorded as `adr/ADR-004-compute-rendering-class.md`,
  following the same Context/Decision/Consequences/Alternatives structure
  as ADR-002 and ADR-003.
- The path to this decision is worth recording precisely, since it did
  not land where the discussion started: the maintainer's initial lean
  was toward Taichi (Class 3) for native compute-and-render performance.
  Live verification found Taichi's release cadence had stalled (13+
  months, widening gaps beforehand) and its Python ceiling (3.13)
  conflicted with the 3.14 chosen earlier the same day. A parallel check
  of NVIDIA Warp (Class 4) found it well-maintained and validated at
  production scale via NVIDIA's own Newton physics engine, but its own
  renderer is documented by NVIDIA as debug-grade rather than
  production -- so Class 4 inherits Class 3's kernel-DSL cost against
  `ADR-003` without Class 3's native-rendering payoff. With both native
  compute+render options weakened on inspection, Class 2 was revisited
  and found to have a stronger independent case than the first survey
  pass credited it with: verified official multi-vendor GPU support
  (CuPy and PyTorch both have mature ROCm; PyTorch adds Apple MPS) that
  neither Taichi nor Warp match; all three candidate instances
  independently well-maintained; and, most importantly, the host
  round-trip's cost -- initially treated as an unquantified but
  significant risk -- turned out on quantification
  (`docs/architecture/compute-and-rendering-stack.md` §4.1) to be a
  near/medium-term non-issue at the MVP's actual 2D scale. The decision
  changed as the evidence came in, not before it.
- Blast radius handled in the same change: `docs/repository-manifest.md`
  gains the ADR-004 row; `docs/planning/backlog.md` A2b marked done with
  the reasoning trail, A2c sharpened now that the class is fixed
  (pointing at the survey's per-instance material and flagging that
  VisPy/wgpu headless status -- unlike Taichi's and Warp's -- was never
  checked, since those weren't the classes under live discussion); F2's
  artifact list corrected to reference the real ADR-004 rather than a
  future placeholder; the survey document's own status banner and §8
  rewritten to state plainly that the class question is settled and the
  instance question is not, so a future reader does not mistake open
  A2c items for an unmade A2b decision; `docs/architecture/CLAUDE.md`
  updated to describe the one non-empty file in its directory.
- Not decided here and not implied by this decision: which specific
  array library, which specific renderer, or whether `.python-version`
  should be added (B2). A2c remains open.

### Decisions (continued, same day -- Python version policy corrected; A2c narrowed)

**Python version policy corrected (maintainer's insight).** The version
should be the *intersection* of what the actual dependencies support,
derived once the dependency-defining choices (chiefly A2c) are made --
not asserted independently ahead of them. This is not hypothetical: it
is exactly what went wrong earlier the same day, when 3.14 was set as
A1b's chosen version before A2 existed, and Taichi's 3.13 ceiling then
had to be framed as "reopening" a decision that was never actually
fixed. `docs/practices.md` gained a new subsection stating this
precisely, including that the dev tooling (uv/ruff/mypy/pytest/
pre-commit) is unlikely to ever be the binding constraint -- the heavier
compiled dependencies (array library, renderer) almost always are, which
is why the version should stay provisional until those are chosen.
`pyproject.toml`'s comment, `roadmap.md` TASK-001, and
`docs/planning/backlog.md` A1b were all corrected to describe 3.14 as
*derived*, not *chosen first* -- re-verified live the same day against
CuPy (`cupy-cuda12x`), PyTorch, and jaxlib, all of which confirmed cp314
wheels. The number did not change; the recorded reasoning for it did,
which matters for a future reader trying to understand why 3.14 is
correct.

**A2c: headless rendering checked live for the two candidates left
open.** wgpu/pygfx has the strongest confirmed headless story of any
general-purpose renderer surveyed in this document -- not merely
documented as possible, but the project's own CI runs on LavaPipe
(software rendering) as standard practice, and offscreen rendering needs
no canvas, GUI toolkit, or event loop at all. VisPy's headless path is
real (a genuine EGL backend, real engineering investment) but rougher: a
headless-rendering-without-sudo issue has sat open and unaddressed on
its own issue tracker since 2023, and other EGL-related issues recur
through its history; release cadence is also the least regular of the
renderer candidates checked live this session. VTK and ModernGL/glfw
were deliberately **not** re-checked -- flagged explicitly as still
resting on the original May-2026 snapshot rather than silently treated
as equally verified.

**A2c: array-library instance narrowed to CuPy vs. PyTorch.** JAX was
set aside -- not for maintenance or Python support, both confirmed fine
live (jaxlib 0.11.0 ships cp312-cp314; its *floor* moved up to 3.12 in
this release series, irrelevant to us but a sign of fast Python
tracking) -- but for its immutable-array model being real, ongoing
friction against a mutable per-timestep FVM loop, and its ROCm story
being unverified rather than confirmed at parity with CuPy/PyTorch.
The maintainer's stated lean toward PyTorch ("wide use and vibes") was
examined rather than accepted on trust or waved off: it holds up on
real, substantive grounds -- the broadest verified hardware reach of the
three (official first-class ROCm plus Apple MPS, both confirmed live),
the best-resourced project by a wide margin (Meta-backed), and latent
optionality toward differentiable-simulation work that is a live
direction in CFD research and fits `docs/planning/dreams.md`'s remit.
The honest counter-case for CuPy was written up with equal care: it is
the more literal expression of the NumPy-shape argument that won Class 2
the A2b decision over Class 3/4 in the first place, and PyTorch's
breadth is bought partly by trading that property away. Not resolved --
laid out for the maintainer's decision in
`docs/architecture/compute-and-rendering-stack.md` §6a.

**Correction to earlier CuPy findings.** The bare `cupy` package checked
earlier in the session is sdist-only on PyPI; the real install targets
are variant packages (`cupy-cuda12x`, `cupy-cuda13x`, `cupy-rocm-7-0`).
Re-checked `cupy-cuda12x` directly and confirmed cp310-cp314. The
ROCm-maturity finding from the earlier session stands; only the specific
package checked for Python-wheel support was wrong and has been
corrected in the survey document.

`docs/repository-manifest.md` and `docs/planning/backlog.md` A2c updated
to reflect the narrowed state. Neither array-library nor renderer
instance is decided as of this entry.

### Decisions (continued, same day -- A2c decided, ADR-005 recorded)
- **Instances decided: PyTorch (array library) and wgpu/pygfx
  (renderer).** Recorded as
  `adr/ADR-005-compute-rendering-instances.md`, following the same
  Context/Decision/Consequences/Alternatives structure as ADR-002
  through ADR-004.
- PyTorch chosen over CuPy: broader verified hardware reach (official
  ROCm and Apple MPS), the best-resourced and most durable project of
  the three array candidates, and latent differentiable-simulation
  optionality relevant to future capability levels and
  `docs/planning/dreams.md`. The trade-off recorded explicitly rather
  than glossed over: CuPy is the more literal expression of the
  NumPy-shape argument that won Class 2 the A2b decision in the first
  place, and PyTorch's `torch.Tensor` API differing from NumPy's in
  places is a real, if modest, cost against that same reasoning.
- wgpu/pygfx chosen over VisPy on the headless findings verified live
  earlier the same session -- own CI runs on LavaPipe as standard
  practice, the strongest confirmed story of any renderer surveyed.
  VTK/PyVista and ModernGL/glfw were explicitly **not** ruled out on
  evidence -- they were simply not re-verified live and so not preferred
  over the two candidates that were. Recorded honestly as an absence of
  comparison, not a rejection.
- `pyproject.toml` now declares `torch` and `pygfx` as runtime
  dependencies (unpinned -- pinning is B2's job once `uv.lock` can be
  generated against real code from B1). This closes the "runtime
  dependencies declared" artifact A2c's backlog entry specified.
- Blast radius handled in the same change: `docs/repository-manifest.md`
  gains the ADR-005 row and notes the new dependencies;
  `docs/planning/backlog.md` A2c marked done with the reasoning trail;
  `roadmap.md` TASK-007's status and implementation text updated to name
  the chosen library and instruct against re-litigating it during
  implementation (consistent with the root `CLAUDE.md`'s instruction not
  to silently change established architecture); E2c
  (`docs/architecture/rendering.md`) marked unblocked, since it was
  explicitly waiting on both A2b and A2c; the survey document's status
  banner, §6a closing paragraph, §7 item 6, and §8 all rewritten to state
  plainly that both the class and instance questions are now decided,
  distinguishing "resolved as part of this decision" from "still
  genuinely open" (VTK/ModernGL's unverified headless status; the
  DLPack zero-copy path, deferred by both ADRs rather than settled).

### Decisions (continued, same day -- B1/TASK-000: engine skeleton created)
- **First Python code in the repository.** Six files:
  `src/pyflow/__init__.py`, `__main__.py`, and `__init__.py` for
  `engine/`, `physics/`, `rendering/`, `configuration/`. All
  docstring-only, no implementation beyond package initialisation, per
  TASK-000's own scope. Docstrings drawn from each package's existing
  `CLAUDE.md` rather than inventing new scope decisions.
- **Deliberately no internal submodules** (no `engine/mesh.py`,
  `engine/operators.py`, etc.). Creating those now would pre-empt
  Stage 1-3's own task-by-task design work (TASK-011 coordinate system
  onward, TASK-018 operator interfaces onward) against P-016 (prefer
  reversible decisions until understanding justifies commitment) and the
  KA spec's "stop descending the capability tree when the next level
  would introduce implementation decisions." `__init__.py` per package
  is both the "placeholder package" and the "placeholder module" TASK-000
  asks for -- no separate file was needed to satisfy that literally.
- **All four TASK-000 acceptance criteria verified by actually running
  them, not assumed:**
  - Import check: `python -c "import pyflow, pyflow.engine,
    pyflow.physics, pyflow.rendering, pyflow.configuration"` -- succeeded.
  - Entry point: `python -m pyflow` -- executed, printed version.
  - Both run against the real installed CPython 3.14.7 via `PYTHONPATH`,
    without needing `uv sync` (B2, not yet done) -- possible because the
    placeholder modules have no third-party imports.
  - `ruff check --target-version py314` (0.16.3) and `mypy --strict
    --python-version 3.14` (2.3.1) both run clean, via isolated `uv tool
    run` rather than the project's own venv (which doesn't exist yet).
  - No circular dependencies: verified **by inspection only** -- none of
    the six files import another `pyflow` subpackage. The mechanical-check
    gap flagged before B1 started (add an import-graph check to C1 or C2)
    is explicitly **not** closed by this work and remains open.
  - Structure matches the documented architecture: matches TASK-000's own
    package list and the `CLAUDE.md` files; there is no
    `docs/architecture/engine.md` yet (E1a) to check against more
    formally.
  - `__version__ = "0.0.1"` in `pyflow/__init__.py` is a plain hardcoded
    string, deliberately not sourced via `importlib.metadata` -- that
    would require the package to be installed, breaking the
    PYTHONPATH-only verification path used here before B2 exists.
    Commented to note it must track `pyproject.toml`'s `version` field.
- `roadmap.md`'s Stage 0 status table, its `make typecheck` expectation
  note, and `docs/repository-manifest.md`'s `src/` section all updated to
  reflect TASK-000 done -- describing what actually exists now, rather
  than left saying "no Python files at all."

### Decisions (continued, same day -- entry point spec, Makefile rebuilt, B2/B3/B4/C1a closed)
- **Maintainer confirmed `uv run python -m pyflow` works**, and `uv.lock`
  now exists as a result. Committed -- a lockfile only does its job
  tracked in version control. 62 packages resolved, including `torch`
  and `pygfx` and their transitive dependencies, matching exactly what
  `ADR-004`/`ADR-005` specified.
- **New, explicit acceptance criteria for the entry point** (maintainer's
  request, deliberately scoped as its own item "to avoid things falling
  through the gaps" rather than folded silently into a larger task):
  `python -m pyflow`, called with no arguments, must print version and
  help info by default, and an automated test must verify it. This is
  new scope, beyond TASK-000's original written criteria (which only
  required "example entry point executes," already satisfied). Recorded
  as an addition, not a retroactive rewrite of what B1 already closed.
  `__main__.py` extended to use `argparse`, printing the version line
  then `parser.print_help()` on every invocation -- verified directly,
  not assumed: `pyflow 0.0.1` plus full usage/options text, exit 0;
  `--help` still works via argparse's own handling.
- **The repository's first automated test:**
  `tests/integration/test_cli.py`, invoking `python -m pyflow` as a real
  subprocess (deliberately not calling `main()` in-process, which
  wouldn't catch packaging/entry-point issues) and asserting exit 0,
  the version string, and help text in stdout. `make test` now exits 0
  -- the first green test run in the project's history, replacing the
  known `pytest` exit-5 failure.
  Settled a real open question in passing: is this unit or integration?
  Called integration, since it crosses the real process boundary the way
  a user invokes the package. `tests/CLAUDE.md` and
  `tests/integration/CLAUDE.md` rewritten from generic placeholders to
  record this as the concrete precedent E9 had flagged as missing --
  `unit/` and `golden/` are left as placeholders deliberately, to get
  the same treatment once their own first real test exists, rather than
  inventing their conventions speculatively ahead of one.
- **Makefile rebuilt to the maintainer's spec** (`install`, `clean`,
  `test`, `lint` named explicitly, plus "any more that seem useful"):
  - `lint` now runs `pre-commit run --all-files` instead of bare `ruff
    check` -- covers formatting *and* linting, for docs and code both,
    using tooling already configured in `.pre-commit-config.yaml` rather
    than adding anything new. This makes `make lint` the literal
    execution of backlog item B4 ("run pre-commit against the whole
    repository for the first time"), rather than two separate concepts.
  - `clean` now genuinely undoes what `install` did (removes `.venv`,
    uninstalls the git pre-commit hook via `uv run pre-commit uninstall`
    before the venv it depends on is removed) **and explicitly states
    what it leaves alone and why**, per the maintainer's instruction:
    `uv` itself (installed at user level, not by `make install`), the
    Python interpreter `uv` downloaded (shared across other `uv`
    projects on the machine -- removing it here could break them), and
    `uv`'s global package cache (also shared).
  - `demo` now actually runs `python -m pyflow` instead of echoing a
    placeholder, with a note that the real bootstrap is still TASK-010.
  - New **`ci` target** added (`lint typecheck test`, chained) -- stated
    explicitly as what C2's future CI workflow should invoke rather than
    duplicate, per P-011 (single authoritative source), so the workflow
    definition and local pre-push verification cannot drift apart from
    each other.
  - `install`, `format`, `typecheck`, `docs` unchanged in substance.
- **Every target verified by actually running it, not by reading the
  file:** `install` (idempotent, resolves the real dependency set),
  `typecheck` (clean, 6 files), `test` (now passes), `demo` (prints
  version+help, correct placeholder note), `lint` (fixed two files on
  first run -- `docs/handbook/numerical-methods/overview.md` and
  `docs/planning/implementation-plan.md`, both missing a trailing
  newline -- clean on second run; diff inspected, confirmed as exactly
  the expected fix and nothing else), `ci` (chains correctly, stops at
  the same known `test` gap it did before C1a landed, then passes once
  C1a existed), and the full `install` → `clean` → `install` round trip
  (venv and hook both removed, then both fully restored).
- **`.python-version` added, containing `3.14`.** Consistent with the
  Python version policy (`docs/practices.md`): the deliberately-chosen
  version should be pinned so the choice is reproducible until the next
  periodic review, rather than left as an explicitly-flagged open
  question (as it was in B2's text before this session).
- Backlog closed: **B2, B3, B4 done**; **C1 split into C1a (done) and
  C1b (remaining: coverage configuration)** -- the split itself is new,
  reflecting that "automated testing" turned out to have a natural first
  slice (the entry-point smoke test) worth tracking separately from the
  rest of TASK-003's scope. `roadmap.md`'s Stage 0 status table and
  `docs/repository-manifest.md` updated throughout to match -- including
  two small accuracy fixes found while sweeping: `.gitattributes` and
  `.pre-commit-config.yaml` were still marked "unverified"/"never run"
  despite both having been verified days -- rather, hours -- earlier in
  this same session.

### Decisions (continued, same day -- backlog review pass)
- **Full re-read of Part I, top to bottom, rather than trusting memory of
  what was written at different points in a long session** (maintainer's
  request). Found real coherence bugs, not just staleness:
  - **A1b and A2a were both fully complete but still showed `[ ]`.** A1b
    had every sub-step checked (`uv`, `make`, Python, the version
    decision) with nothing left but the outer checkbox; A2a had produced
    and been used to make two ADRs. Both marked `[x]`. This is exactly
    the kind of drift the backlog's own design (checkbox state should
    answer "is this done?" without judgement calls) exists to prevent --
    finding it here rather than leaving it for a future reader to
    puzzle over is the point of doing this pass.
  - **A1a still said `uv python install 3.12`**, a leftover from before
    the Python version was corrected to 3.14 later the same session.
    Corrected with a pointer to A1b rather than just swapping the number,
    so the "why" stays attached.
  - **C2 (the CI task) still described restating the
    install/lint/typecheck/test sequence in the workflow YAML** --
    written before `make ci` existed. Updated to say the workflow should
    invoke `make ci`, matching the reason that target was added in the
    first place (P-011, so the two definitions can't drift apart).
  - **Group D's dependency line never mentioned D5 at all.** D5's
    relationship to D4 was only implied in its own prose ("D4 produces a
    bootstrap application; that is not the same artifact as a golden
    demo"). Made explicit in the dependency line, matching how every
    other item in the group states its dependency.
  - **Three items were quietly unblocked by today's work and still read
    as blocked:** E9's `src/` sub-item (waiting on B1, done), E11 (waiting
    on A1b and B2, both done), E13 (waiting on B3, done). All three
    flagged as unblocked rather than left implying they still can't be
    started.
  - **F2's artifact list was written prospectively** ("uv.lock and
    possibly `.python-version`," "the test suite (C1)") for things that
    have since actually landed. Rewritten to distinguish what's already
    been added (as it landed, following the standing rule in
    `docs/practices.md` rather than deferring to this sweep) from what
    genuinely remains for when C2/D5/E11/E13 land -- the item's real
    remaining job has narrowed from "a backlog of unrecorded artifacts"
    to "a final confirmation pass," which is recorded as the point of a
    backstop working as intended.
  - **F3's evidence-mapping still cited undivided `C1`** in two places,
    stale since C1 split into C1a/C1b. Both corrected.
  - Swept for other `3.12` references left over from the version
    correction -- the remaining ones are all legitimate historical
    mentions (describing what used to be configured, or general policy
    discussion), not stale current-state claims. No further changes
    needed there.
- **Checkbox count confirmed mechanically after the pass**, not assumed:
  Group A (6/6) and Group B (4/4) fully closed, C1a closed, everything
  else in Groups C-F still open and correctly so.
- No item's *position* in the ordered queue changed -- the review found
  content and state bugs, not sequencing bugs. Group D's internal order
  (D1-D3 parallel, D4 needs all three, D5 needs D4) and Group E's stated
  order (E8 before E3/E4, etc.) both held up under re-reading.

### Decisions (continued, same day -- README Quick Start, lint scope, two new standing rules)
- **New standing rule: keep `README.md`'s Quick Start current as
  functionality is added, in the same change** (maintainer's
  instruction). Recorded in `docs/practices.md`'s Documentation Rules,
  with the reasoning stated rather than just the rule: a Quick Start that
  lags behind what the project does actively misleads the person it
  exists to help. Also records a design choice meant to stop this rule
  needing to fight entropy on its own -- don't duplicate detail that
  would drift (e.g. `make clean`'s own explanation of what it can't
  remove); point at running the command instead of restating its output.
  README's Quick Start section written to this standard: `make install`,
  then `demo`/`test`/`lint`/`ci`, `clean` explained by reference rather
  than by copy. The Project Status section's "no Python source" claim
  (stale since B1 landed) was fixed in the same change, found while
  touching the file rather than deferred. `make ci` run clean immediately
  after, confirming the documented commands actually work. Closes E11.
- **`make lint`'s scope clarified, not changed in substance** (maintainer
  clarification: the intent was always for `lint` to cover format, lint
  and typecheck together). It already did, structurally -- `pre-commit
  run --all-files` includes the `mypy` hook -- but having `typecheck` as
  a separate top-level target made this easy to miss without reading
  `.pre-commit-config.yaml`. Fixed by making it explicit rather than
  restructuring: a comment above `lint` in the `Makefile` now enumerates
  every hook it runs, hook-by-hook, with an explicit instruction to keep
  it in sync if `.pre-commit-config.yaml` changes (an instance of the
  Blast Radius rule, named as such). `typecheck` kept as its own target
  (required by `roadmap.md` TASK-002's own command list) but now
  documented as the narrower, faster alternative, not a sign `lint`
  excludes typechecking.
- **`make typecheck` extended to cover `tests/`, not only `src/`**
  (maintainer instruction: formatting and linting should apply to every
  folder containing Python code). `mypy src` silently excluded `tests/`
  even though pre-commit's `mypy` hook already covered it (hooks receive
  explicit file arguments, unlike the bare `mypy src` invocation, which
  only sees what `[tool.mypy] packages = ["pyflow"]` scopes it to) --
  `make lint` and `make typecheck` could therefore disagree about whether
  a test file type-checks, depending on which one caught a problem first.
  Changed to `mypy src tests`; verified live (7 files now, up from 6).
  `format` (`ruff format .`) and `lint` (`pre-commit run --all-files`)
  already covered the whole repository via a bare `.`/`--all-files`, so
  neither needed a change -- only `typecheck`'s narrower, explicit `src`
  argument was the actual gap. Noted in the Makefile that `examples/`
  should be added to `typecheck` once it holds real Python code, rather
  than pointed at now while empty.
  `.pre-commit-config.yaml`'s header comment, which still said "these
  hooks have had nothing to lint/typecheck" from before B4 ran them for
  real, was also fixed in the same change -- found while touching the
  file for the hook-list comment's sake, not sought out separately.
- **New standing rule: closing a backlog item is a Blast Radius event**
  (maintainer's instruction, directly in response to the coherence bugs
  the backlog review pass found earlier this session). Recorded in
  `docs/practices.md` as its own named section, with a checklist derived
  directly from the specific bugs found rather than written in the
  abstract: mark `[x]` in the same change, not a later pass; grep the
  file for the item's own ID and update every other item that named it
  as a blocker; if an item was split or renumbered, grep for the *old*
  ID everywhere; propagate any specific fact the item changed (a version,
  a tool name) to everywhere else that restates it; if the item added a
  new capability, point other places at it instead of leaving them to
  duplicate what it replaced; convert prospective language ("will
  produce X") to retrospective ("produced X") the moment it becomes true.
  States explicitly why this matters more here than a generic
  documentation-hygiene rule would: an agent picking up the next piece of
  work reads the backlog as ground truth, and a wrong backlog is more
  dangerous than an incomplete one because it doesn't look wrong.
  Applied immediately to itself: closing E11 in this same session
  triggered a grep for "E11" across the backlog, which found and fixed
  two other items (A1b, F2) that still described it as outstanding.

## 16-08-2026

### Decisions (Group C closed out: C1b coverage config, C2 CI workflow)
- Confirmed Group A/B were genuinely done, not just claimed done, before
  starting Group C: checked `.venv` exists, `uv`/`make` both on `PATH`,
  `git status` clean, no coverage config, no `.github/workflows/` file --
  matched what the backlog already said, so Group C was the correct next
  work rather than something drifted since 2026-08-15.
- **C1b (TASK-003, closed).** Added `pytest-cov` to the `dev` dependency
  group via `uv add` (so `pyproject.toml` and `uv.lock` moved together,
  not hand-edited separately). Configured `--cov=pyflow
  --cov-report=term-missing` in `[tool.pytest.ini_options]` and added
  `[tool.coverage.run]`/`[tool.coverage.report]`, deliberately with no
  `fail_under` threshold yet -- one real test and almost no
  implementation makes any number either meaningless or trivially gamed.
  Verified by running `make test` directly: coverage table prints,
  `1 passed`. Found and recorded a real gap while verifying rather than
  glossing over it: `__main__.py` shows 0% because
  `tests/integration/test_cli.py` deliberately invokes it as a real
  subprocess (the whole point of that test, per
  `tests/integration/CLAUDE.md`), and `pytest-cov` only instruments the
  in-process interpreter. Documented as a comment directly above
  `[tool.coverage.report]` rather than left for a future reader to
  discover by confusion; the real fix
  (`COVERAGE_PROCESS_START`/`sitecustomize.py`) is named and deliberately
  deferred until more than one subprocess-boundary test exists to justify
  it. `make ci` re-run clean afterward to confirm nothing else broke.
- **C2 (TASK-004, written but not CI-verified).** Maintainer's call on
  the open matrix question C2 itself had flagged: **both Windows and
  Linux**, not Linux-only, since development happens on Windows and
  that's exactly where `make` behaviour and headless rendering are most
  likely to diverge from a Linux-only signal. Wrote
  `.github/workflows/ci.yml`: matrix `[ubuntu-latest, windows-latest]`,
  triggers on push to `master` and every pull request, Python from
  `.python-version` via `astral-sh/setup-uv`'s `python-version-file`
  input (not a second hardcoded version), and invokes `make ci` rather
  than restating install/lint/typecheck/test in YAML (P-011). Windows
  needs one extra step -- `choco install make -y`, conditional on
  `runner.os == 'Windows'` -- because `windows-latest` doesn't ship GNU
  Make, the same gap A1b found and fixed the same way on the local dev
  machine; Linux needs nothing extra since `ubuntu-latest` ships Make
  already. Wrote `.github/CLAUDE.md` and `.github/workflows/CLAUDE.md` in
  the same change, closing that pair in E9's list too.
  **Honestly incomplete in one specific way, recorded rather than
  smoothed over:** the repository has no git remote, so `ci.yml` has
  never actually run on a GitHub Actions runner. What was verified
  directly: the YAML parses (`python -c "import yaml;
  yaml.safe_load(open('.github/workflows/ci.yml'))"`), `make lint`'s
  `check-yaml` pre-commit hook passes over it, and the sequence it
  invokes (`make ci`) was itself re-run clean locally moments before.
  TASK-004's actual acceptance criterion -- pull requests execute the
  pipeline automatically -- stays open until a remote exists and a real
  PR proves it green. Recorded as such in `roadmap.md`'s status table
  (not marked plain "Done"), in the backlog's C2 entry, and in
  `docs/repository-manifest.md` (🟨, not 🟩) -- per the Integrity section
  of the root `CLAUDE.md`, a green checkbox that hasn't actually been
  demonstrated is exactly the kind of thing that must be said plainly,
  not assumed.
- Blast Radius sweep for both closures, per the standing rule added
  2026-08-15: grepped the backlog for `C1b` and `C2` and updated every
  place that named them as a dependency or open thread, not just the
  items' own checkboxes -- `roadmap.md`'s Stage 0 status table, the
  `tests/` and `.github/` sections of `docs/repository-manifest.md`, the
  `.github`/`.github/workflows` line in E9's placeholder-`CLAUDE.md`
  list, F2's "still to add" list (moved C2 into "already added"), and
  A1b's own "still to follow through: C2's CI matrix must match" note
  (now closed, since `ci.yml` reads `.python-version` directly). README's
  Quick Start section updated in the same change (E11's standing rule)
  since `make test`'s behaviour changed (now reports coverage) and
  `make ci`'s description gained the "on every push and pull request"
  detail now that it's true.

### Decisions (continued, same day -- Group D: D1-D4, TASK-005/006/007/010)
- Confirmed Group D was actually unblocked before starting, not just
  assumed to be: A2b/A2c decided, B1's package skeleton real,
  `.venv`/`uv`/`make` all working. D1-D3 have no ordering dependency on
  each other per the roadmap; built D1 -> D2 -> D3 -> D4 anyway, since D1
  needed to exist before D3 could couple the render backend to
  configuration (see next point), and D2 was small enough to slot in
  between them.
- **Two decisions made with the maintainer before writing code, not
  after:** config file format, and the interactive rendering window's
  backend. On format: **YAML via PyYAML**, over stdlib TOML (zero new
  dependency, but the maintainer preferred YAML's more familiar
  sim/ML-tooling syntax) and JSON (no comments, worse for a hand-edited
  file). On the render backend, the maintainer's answer reframed the
  question rather than picking an option: not "which library forever" but
  "build for long-term flexibility." Resolved by recognising
  `adr/ADR-003-modular-numerical-strategies.md` already commits PyFlow to
  swappable implementations behind a stable interface, selected at
  construction -- applied one layer down, to the windowing library
  instead of the whole renderer. **glfw** implemented now (TASK-007's own
  acceptance criterion needs a real interactive window); **Qt** left
  undone but documented as the next backend behind the same seam
  (`src/pyflow/rendering/canvas.py`), so adding it later is additive, not
  a rewrite.
- **D1 (TASK-005).** `configuration/schema.py`: nested dataclasses
  (`PyFlowConfig`/`LoggingConfig`/`RenderingConfig`), every field
  defaulted so `PyFlowConfig()` alone is complete and valid.
  `configuration/loader.py`: `load_config(path)` reads YAML, rejects
  unknown sections/fields and out-of-range values immediately rather than
  silently accepting a typo. `RenderingConfig.backend` is the field that
  couples D1 to D3 (below). `pytest-cov` (already added, C1b) reported
  100% on both modules; 11 tests in `tests/unit/test_configuration.py`,
  the repository's first real unit test -- `tests/unit/CLAUDE.md` written
  against it (E9).
- **D2 (TASK-006).** stdlib `logging`, not a third-party library --
  nothing about Stage 0 argues for more. `engine/logging_setup.py`:
  `configure_logging` sets up the `pyflow` logger once (level +
  formatting, handlers cleared before re-adding so repeated calls, e.g.
  across tests, don't accumulate duplicate handlers); `get_logger(name)`
  is the one documented factory every subsystem calls, conventionally
  with `__name__`, getting hierarchy-based inheritance for free. 4 tests,
  100% coverage.
- **D3 (TASK-007).** `rendering/canvas.py`'s `create_canvas(config)`
  builds a `rendercanvas.glfw.GlfwRenderCanvas` or `rendercanvas.
  offscreen.OffscreenRenderCanvas` depending on `config.backend`;
  `rendering/window.py`'s `RenderWindow` is written against the shared
  `rendercanvas.base.BaseRenderCanvas` protocol both satisfy, so it never
  branches on which backend it has. `RenderWindow.run(max_frames=...)`:
  interactive backends self-reschedule each draw via `request_draw` until
  closed (by the user, or automatically once `max_frames` is hit);
  offscreen draws `max_frames` (default 1) frames directly, since
  `rendercanvas.offscreen` has no event loop at all (its own docstring:
  "No scheduling"). Added `glfw` as a runtime dependency; added a scoped
  `[[tool.mypy.overrides]]` for `pygfx.*`/`rendercanvas.*` (neither ships
  a py.typed marker, same category of gap `types-pyyaml` fixed
  differently for a stubs-available package).
  **Real API drift caught by trying the import, not by re-reading the
  survey:** the 2026-08-15 A2a survey described `wgpu.gui.offscreen`/
  `wgpu.gui.auto`; the actually-installed `wgpu` 0.32.0 has no `wgpu.gui`
  submodule -- canvas support had moved to a separate `rendercanvas`
  package (2.7.2), already resolved as a transitive dependency in
  `uv.lock`. The survey's own conclusions (offscreen canvas works
  headless, returns a NumPy array, no GUI toolkit needed) held up fine;
  only the import path had moved.
  **Verified both backends by actually running them, not one and
  assuming the other:** `tests/unit/test_rendering.py` (5 tests) exercises
  canvas creation, the full render loop, and clean shutdown on the
  offscreen backend -- the one that works headless, which is also the
  only one the automated suite touches (CI has no display). The
  interactive glfw path was run manually and separately: a real 400x300
  window opened, drew 5 frames, and closed cleanly
  (`frame_count=5, closed=True`) -- confirmed before D3 was called done,
  not assumed from the offscreen tests passing.
- **D4 (TASK-010).** `bootstrap()` (loads config, initialises logging,
  opens the window, runs the loop) wired to a new `pyflow run` subcommand
  in `__main__.py`, kept off the bare-invocation path so C1a's existing
  no-args contract (version + help, still what `test_cli.py` checks)
  didn't change underneath it. `Makefile`'s `demo` target now runs
  `python -m pyflow run` for real.
  **A genuine circular import, found by running the import, not by
  inspection.** First write: `bootstrap.py` inside `engine/` (TASK-010's
  own name says "engine bootstrap"). That created a real cycle -- `engine`
  needing `rendering` (for the window), `rendering.window` needing
  `engine.logging_setup` (for its logger) -- so whichever package a
  program imported first would find the other only partially initialised.
  First attempted fix: reorder the two imports inside `engine/__init__.py`
  so `logging_setup` bound its names before `bootstrap` ran. Worked, once
  -- until the very next `make lint`, when `ruff`'s isort hook silently
  sorted the imports back to alphabetical order (`bootstrap` before
  `logging_setup`) and reintroduced the exact bug it had just fixed. A
  fix that only survives until the linter runs isn't a fix. **The real
  fix was structural, not textual:** moved `bootstrap.py` out of `engine/`
  entirely, to the `pyflow` package root, since it composes
  `configuration`, `engine`, and `rendering` together and so belongs
  above all three in the dependency graph, not nested inside one of them.
  Verified clean afterward from every import order in a fresh
  interpreter -- `pyflow.rendering` first, `pyflow.engine` first,
  `pyflow.bootstrap` first, all pass -- not just the one order that
  happened to work before. Recorded as a standing rule in the newly
  written `src/pyflow/CLAUDE.md`: a module that orchestrates two or more
  subpackages belongs at the package root, not inside whichever
  subpackage its task name happens to suggest.
  *Verified by running:* `tests/integration/test_bootstrap.py` runs
  `python -m pyflow run --config <offscreen config> --max-frames 2` as a
  real subprocess, exit 0. The interactive path was also run end-to-end
  through the actual CLI (`python -m pyflow run --max-frames 5`): real
  window, 5 frames, clean exit, logging output legible throughout. The
  bare no-args form was re-checked afterward to confirm it still prints
  version + help, unchanged.
  **What's still honestly open, not swept under D4's own "done":**
  TASK-010's acceptance criterion "the CI pipeline passes" inherits C2's
  own unresolved caveat (`ci.yml` has never run on a real GitHub Actions
  runner, no remote configured) -- and D3 raised the stakes of that gap
  specifically, since Linux CI now needs a software Vulkan driver
  (LavaPipe) just to construct a `wgpu` device for the rendering tests.
  Added a best-effort `apt-get install libegl1 libgl1 mesa-vulkan-drivers`
  step to `ci.yml` for the Linux leg, explicitly flagged in both `ci.yml`
  and `.github/workflows/CLAUDE.md` as an unverified guess -- standard
  practice for wgpu/pygfx's own CI per the 2026-08-15 survey, but not
  re-checked against today's `ubuntu-latest` image or a real run. If
  Linux CI is ever green everywhere except the rendering tests, that step
  is where to look first.
- Blast Radius sweep for D1-D4: `roadmap.md`'s Stage 0 status table
  (TASK-005/006/007/010 all moved to Done, with TASK-010's entry noting
  C2's still-open CI-verification caveat rather than hiding it inside a
  plain "Done"); `docs/repository-manifest.md`'s `pyproject.toml` row
  (new runtime deps `pyyaml`/`glfw` named); every touched package's
  `CLAUDE.md` (`configuration/`, `engine/`, `rendering/`, and the newly
  written `src/pyflow/CLAUDE.md` and `tests/unit/CLAUDE.md`); README's
  Quick Start (`make demo` no longer described as a placeholder); F2's
  "already added" list; E9's placeholder-`CLAUDE.md` list (`unit/` and
  `src/`/`src/pyflow/` both moved from outstanding to done).

### Decisions (continued, same day -- D5: Empty Window golden demo)
- Three artifacts built: an entry in `docs/implementation/
  golden-demos.md` (placed before the existing "Initial Golden Demo"
  section, since Capability Level 0 precedes Level 1); `examples/
  golden-demos/empty_window.py`, a `run(config, *, max_frames)` function
  plus an `if __name__ == "__main__":` block so the same code is both the
  interactive demo and what the regression test calls headlessly; and
  `tests/golden/test_empty_window.py`, which loads the demo module by
  file path (`importlib.util.spec_from_file_location`) rather than by
  import statement, since `examples/` is deliberately not an importable
  package and `golden-demos` has a hyphen in it regardless.
- Deliberately gave the demo a solid, declared background colour
  (`#1a1a2e`) rather than leaving `pygfx`'s default (transparent black).
  Reasoning: golden-demos.md's own Definition of Done requires
  "verifies meaningful behaviour... not just it ran without crashing" --
  a transparent frame would satisfy "it ran" trivially and give the
  regression test nothing real to assert against. A declared, exact
  colour makes both the demo and its test meaningful: the test checks
  every pixel equals that colour, and a second run is checked
  byte-identical to the first, covering both "verifies meaningful
  behaviour" and "deterministic" from the Definition of Done, not just
  one of them.
- **A real bug in D3 found while building this, not before.**
  `RenderWindow`'s offscreen path (`window.py`) called `renderer.render()`
  directly every frame, but never called `canvas.draw()` -- and it turns
  out `canvas.draw()` is the only thing that actually triggers
  presentation and captures the frame in `rendercanvas.offscreen`;
  `renderer.render()` alone renders into a texture nothing then reads.
  Confirmed empirically, not assumed, with a short interactive check
  before touching any code: `renderer.render()` left
  `canvas._last_image` at `None`; calling `canvas.draw()` afterward
  populated it as a real NxMx4 array. D3's own test suite had never
  caught this, because none of its tests had ever inspected the
  rendered pixels -- only that `renderer.render()` didn't raise and
  `frame_count` incremented, which stayed true whether or not a frame
  was ever actually presented. Fixed in `window.py`: offscreen mode now
  registers `self._draw` via `request_draw()` once, then calls
  `canvas.draw()` each frame and stores the result on a new
  `RenderWindow.last_image` attribute. Added
  `test_render_window_captures_pixel_data` to D3's own
  `tests/unit/test_rendering.py` so this specific regression can't
  reappear silently. Exactly the class of bug "verified by running, not
  assumed" (root `CLAUDE.md`) exists to catch -- and here it caught
  something a previous verification pass had missed, which is the whole
  point of re-running real checks rather than trusting that a thing
  already marked "done" stays correct.
  `Makefile`'s `typecheck` target extended to `mypy src tests examples`
  -- an open note left in B3 ("add `examples/` once it holds real Python
  code") closed here rather than carried further.
  *Verified by running:* `make ci` -- 25 tests (up from 22) all passing;
  the interactive demo script also launched manually and opened a real
  window (killed after ~3s deliberately, since it has no `max_frames`
  and a human demo should wait for a human to close it, not auto-exit).
- Blast Radius sweep for D5: `docs/repository-manifest.md` (`golden-demos.md`
  row to 🟩, `tests/` and `examples/` sections rewritten for the new
  real content); `tests/golden/CLAUDE.md`, `examples/golden-demos/
  CLAUDE.md` (corrected a stale claim that the first demo would be the
  2D air-current simulation "once the MVP exists" -- Empty Window turned
  out not to need the MVP at all), and `examples/CLAUDE.md`, all written
  for the first time; the backlog's own D5 entry, F2's "already added"
  list, and E9's placeholder-`CLAUDE.md` list (`examples/` and
  `golden-demos/` moved from outstanding to done, `experiments/`/
  `tutorials/` correctly left generic -- still nothing specific known
  about either).

### Decisions (continued, same day -- 0% coverage gap closed by request)
- Maintainer asked, directly: could the `__main__.py`/`bootstrap.py` 0%
  coverage gap (recorded as deliberately deferred in C1b, same day) be
  closed by duplicating the existing subprocess test, "unless there's
  some other way... without nasty hacks." There was: `main()` gained an
  optional `argv: list[str] | None = None` parameter -- the exact
  convention `argparse.ArgumentParser.parse_args` already uses -- so
  `tests/unit/test_main.py` and a new `tests/unit/test_bootstrap.py`
  could call `main()`/`bootstrap()` directly, in-process, rather than via
  subprocess. Not a duplicate of the subprocess tests: those still verify
  the real packaged entry point (the thing they exist to prove);
  `test_main.py` mocks `bootstrap` entirely to check argument
  parsing/dispatch in isolation, `test_bootstrap.py` runs the real
  offscreen render path to actually exercise `bootstrap.py`. Coverage
  moved from 73% to 90% overall; `__main__.py` 91% (only the
  `if __name__ == "__main__":` guard stays unreachable, correctly),
  `bootstrap.py` 100%.
  Surfaced a second, independent bug while doing this: `tests/unit/
  test_bootstrap.py` collided with `tests/integration/test_bootstrap.py`
  -- pytest and mypy both identify test modules by bare basename without
  an `__init__.py`, and neither tool had one anywhere under `tests/`
  before now. `mypy` failed outright ("Duplicate module named
  'test_bootstrap'"); `pytest` failed the same way with an `import file
  mismatch` error, and would have failed for *any* two subdirectories
  that happened to test the same module under its natural name, not just
  this one. Fixed with a one-line `__init__.py` in all four `tests/`
  subdirectories (`unit/`, `integration/`, `golden/`, `performance/`),
  not only the two that collided today -- per the same "new regression
  test on discovery" instinct, fixing the general case rather than the
  specific instance.
  *Verified by running:* `make ci` -- 29 tests (up from 25), mypy clean
  across `src tests examples`, coverage table showing 90%.

### Decisions (continued, same day -- CI scope set explicitly; interactive close-on-key; import-order regression test)
- **CI scope, asked and answered directly.** Maintainer, on C2's
  unresolved-on-a-real-runner caveat: "that's a fair concern but I think
  we'll do that after we have one of the 2D demos... consider 'pipeline'
  to mean the test suite and makefile targets until then." Recorded as an
  explicit scope decision everywhere the gap had previously been flagged
  as an open worry -- `roadmap.md`'s TASK-004/TASK-010 rows,
  `docs/repository-manifest.md`'s `.github/` section,
  `.github/workflows/CLAUDE.md`, and the backlog's own C2/D4 entries --
  reframed from "unverified, should be closed soon" to "deliberately
  deferred until a 2D demo exists, and `make ci` is the accepted
  definition of 'the pipeline' until then." Nothing about the actual risk
  changed (Linux CI still needs the unverified LavaPipe apt step); what
  changed is that it's now a stated decision instead of an implicit gap
  restated with mounting urgency every time this area gets touched.
- **New standing instruction, given directly:** always add a regression
  test with measurable pass/fail criteria when a bug is found mid-task,
  not just fix it silently. Saved as a durable memory (not just a
  same-session note) since it's a general working preference, not
  PyFlow-specific. Applied immediately, retroactively, to the D4
  circular-import bug found and fixed earlier the same day: added
  `tests/integration/test_import_order.py`, which imports every `pyflow`
  subpackage/module first, each in a fresh subprocess (the same technique
  that surfaced the original bug -- `sys.modules` caching means
  re-importing an already-imported module in the same process never
  re-exercises import *order*). Not re-verified against a deliberately
  re-broken tree -- the technique's effectiveness was already
  demonstrated live, hours earlier in this same session, catching the
  real bug with this exact command shape; re-breaking the real,
  now-committed source tree to re-derive that would have risked the
  uncommitted work sitting on top of it for no added confidence.
- **Golden demos need an interactive, humanly-usable mode, not just a
  passing regression test.** Maintainer wanted to actually look at Empty
  Window to manually verify it, and found the existing interactive path
  either closed too fast (`max_frames` set) or required hunting for the
  OS window's close button -- neither is "an option to run directly" in
  any useful sense. `empty_window.py`'s `run()` gained `close_on_key`:
  registers a `key_down` handler (`window.canvas.add_event_handler`)
  that closes the window on Escape or Enter, skipped entirely for the
  offscreen backend (no keyboard events to listen for); the `__main__`
  block now prints what to press before opening the window, and no
  longer sets `max_frames` at all when run this way -- it waits. Verified
  for real: injected a simulated `key_down`/`Escape` event via
  `canvas.submit_event()` while the interactive loop was actually
  running (`loop.call_later` scheduled the injection, `loop.run()` was
  genuinely blocking at the time), and confirmed the window closed in
  response, drawing 2 frames first. Documented as the standing pattern
  for every future golden demo in `examples/golden-demos/CLAUDE.md`, not
  left as a one-off fix to this single file.

### Correction (2026-08-16, later the same day -- close-on-key was never wired into the real `pyflow run` path)
- Maintainer actually ran `uv run python -m pyflow run`: the window
  opened, rendered, and then was unresponsive to keyboard input -- had to
  Ctrl+C, which "closed cleanly apparently" (an uncaught KeyboardInterrupt
  unwinding cleanly, not a real `canvas.close()` path). Root cause: the
  close-on-key handler added earlier the same day lived only in
  `examples/golden-demos/empty_window.py`'s own `run()` wrapper, never in
  `RenderWindow` or `bootstrap.py` -- so it never reached the actual
  product entry point, only the demo script. Every verification of the
  interactive path recorded earlier today (D3, D4, and the close-on-key
  addition itself) used `max_frames` to bound the run, so the real "no
  bound, a person has to close this" scenario had genuinely never been
  exercised.
  **Fixed structurally, not by patching the demo again:** moved the
  close-key handler into `RenderWindow.run()` itself as a default
  parameter (`close_keys=("Escape", "Enter")`, on unless explicitly
  disabled) -- the only place shared by every current and future caller,
  including `pyflow run`. `bootstrap.py` needed zero changes: it already
  calls `window.run(max_frames=max_frames)` without touching
  `close_keys`, so the fix reaches the real CLI for free.
  `empty_window.py` simplified in the same change -- its own duplicate
  handler and `close_on_key` parameter removed now that `RenderWindow`
  handles this for every interactive window, not just this one demo.
  **Verified with exactly the reproduction the maintainer suggested**
  ("a test that waits a few seconds before injecting a keypress"):
  `loop.call_later(6.0, ...)` injected a simulated Escape `key_down`
  event into a genuinely-running `window.run()`. Confirmed the window
  was actively repainting the entire six seconds (164 frames -- not
  frozen, contrary to what "unresponsive" might have suggested) and
  closed the instant the event arrived. Re-ran the real CLI
  (`python -m pyflow run --max-frames 3`) afterward and confirmed the log
  line now states the close keys explicitly, so a user isn't left
  guessing. Not captured as an automated pytest test -- a real
  `GlfwRenderCanvas` needs an actual display/window system, which
  headless Linux CI doesn't have, the same reason D3's interactive path
  was never automated either; the exact verification command is recorded
  in `src/pyflow/rendering/CLAUDE.md` to re-run locally instead.
- Also answered, in passing: whether a `make pyflow` alias was worth
  adding for `uv run python -m pyflow run`. It already exists --
  `make demo` has done exactly this since D4. No new target added;
  README's Quick Start line for `make demo` updated to mention the close
  keys explicitly instead.

### Decisions (continued, same day -- new rule: golden demos must run via the public API)
- **New standing rule, maintainer's instruction:** a golden demo must be
  reproducible by a user "exactly and simply" -- the relevant `pyflow`
  command, plus whatever configuration it needs, nothing bespoke. In
  concrete terms: a demo's identity lives in a plain config file under
  `examples/golden-demos/`, run via `pyflow run --config <file>` (the
  same public CLI, the same public `bootstrap()` underneath it, that any
  user has). If a demo needs something configuration doesn't yet expose,
  that capability gets added to the schema, not worked around with
  demo-specific code. At least one regression test per demo must invoke
  it exactly that way -- the real CLI, as a subprocess -- not only
  through an internal shortcut. Recorded in `docs/implementation/
  golden-demos.md`'s Definition of Done.
- Applied immediately to Empty Window, which had been violating this
  since D5 landed hours earlier: `examples/golden-demos/empty_window.py`
  (a script calling `RenderWindow`/`pygfx` directly) deleted outright,
  replaced by `empty_window.yaml` -- one line,
  `rendering.background_color: "#1a1a2e"`. That required promoting the
  demo's one distinctive feature, its background colour, from
  demo-script code into the public configuration schema:
  `RenderingConfig.background_color` (validated `#RRGGBB` hex, `None`
  default -- changes nothing for anyone not using it), wired into
  `RenderWindow.__init__`.
- Needed one more piece to keep a single config file usable both
  interactively and headlessly: `pyflow run --backend` and a matching
  `backend` keyword on `bootstrap()`, overriding whatever the config
  file says. Same config, same command, one flag turns "the demo a human
  watches" into "the demo CI verifies" -- exactly the kind of override a
  real user might reach for too (a screenshot, a scripted check), not a
  test-only escape hatch. `bootstrap()` also now returns the
  `RenderWindow` it built (was `None`), since a caller -- tests
  especially -- has no other way to see what was actually rendered.
- `tests/golden/test_empty_window.py` rewritten around all of this:
  `test_empty_window_runs_via_the_public_cli` is a genuine subprocess
  running the exact command the spec documents; two further tests use
  `bootstrap()` directly (the public Python entry point, not a shortcut)
  for pixel-exact and determinism checks, since that's the only way to
  reach `last_image`. The earlier version's `importlib.util.
  spec_from_file_location` trick (needed to load a demo script that no
  longer exists) is gone along with the script.
- **A real, immediate consequence, caught by running the build rather
  than predicted:** deleting the only `.py` file under `examples/` left
  it with zero Python files, and `make typecheck` (extended to `mypy src
  tests examples` earlier the same day, for exactly the opposite
  situation) started failing outright -- mypy exits nonzero on a
  directory with no Python to check at all. Reverted to `mypy src
  tests`, with a comment recording that `examples/` is now expected to
  stay config-only, not a temporary state.
- Found and fixed in passing, unrelated to the main change but noticed
  while touching this area: `tests/golden/test_empty_window.py` has
  always imported `numpy` directly, resolved only because `torch`/`pygfx`
  happen to depend on it transitively -- never declared. Added explicitly
  to the `dev` dependency group rather than left as a latent fragility.
- Two ideas raised in the same conversation -- selecting among demos
  without knowing a file path, and a GUI for "run a demo, watch it
  happen" (extending later to tests) -- deliberately not built now.
  Recorded in `docs/planning/backlog.md` Part II with the maintainer's
  own stated trigger: a second golden demo existing, which is also when
  there's something real to design the choice against rather than a
  guess.
- *Verified by running, not assumed:* the actual CLI command, run
  directly, both with `--backend offscreen --max-frames 1` and with the
  interactive default (a real window, confirmed opening), before the
  rewritten test suite existed to check either automatically. `make ci`
  afterward: 42 tests (up from 35), 87% coverage, mypy clean.

### Decisions (continued, same day -- end-of-session consistency review made a standing practice)
- The 2026-08-16 review pass found four real drifts across `roadmap.md`,
  `backlog.md`, and `docs/repository-manifest.md` -- a stale `TASK-003`
  status line claiming `unit/`/`golden/` were still empty, a stale
  `CLAUDE.md` placeholder count (29, actually 20) repeated in three
  places, a stale `E9` file-by-file breakdown, and D5's own top summary
  still describing a deleted file as current fact 90 lines above its own
  correction. Fixed directly (commit `887fd4f`).
- **Maintainer's instruction:** this shouldn't be a one-off cleanup --
  the repository must always be left in a state a fresh agent could pick
  up and trust, and whenever a gap like this is found, a rule should be
  added to prevent the same class of drift recurring. Recorded two
  places, mirroring how the Blast Radius rule itself is recorded: a
  short principle statement in the root `CLAUDE.md` (new "Session
  Handoff" section, between "Blast Radius" and "Documentation"), and the
  actual checklist in `docs/practices.md`'s "Session Workflow" section
  (a new step 7, "run the end-of-session consistency review," inserted
  before "commit changes").
  The checklist itself is explicitly designed to grow: its last item is
  "add a new item here whenever a review finds a drift this list
  wouldn't have caught," the same self-extending shape as
  `docs/practices.md`'s existing "Closing a backlog item is a Blast
  Radius event" checklist. Verified `make ci` stays clean after both
  additions (doc-only change).

## 17-08-2026

### Decisions
- Prompted by a Claude Code usage-insights report analyzing prior
  sessions: two of its four suggestions (an end-of-session checklist, a
  "verify through the real entry point" rule) turned out to already be
  covered, more precisely, by the 16-08-2026 additions above and by
  `src/pyflow/rendering/CLAUDE.md`'s documented manual-verification
  convention for the interactive `close_keys` path -- not re-done, to
  avoid duplicating or contradicting standing rules. The other two were
  genuinely missing and built:
- **`tools/validators/check_docs.py`**, run via `make check-docs` and
  now part of `make ci` (`ci: lint typecheck test check-docs`).
  Mechanizes one specific instance of the Blast Radius rule's "grep for
  the thing's name" check (`docs/practices.md`): every Markdown link in
  the repository is resolved relative to its own file and flagged if the
  target doesn't exist. Deliberately narrow -- it does not verify that a
  `file.md#heading` fragment matches a real heading, and it is not a
  substitute for the rest of Blast Radius (renamed terms, stale numbers),
  which still needs a human. See `tools/validators/CLAUDE.md`.
  - **Two real bugs found while building it, fixed in the same change
    with regression tests** (`tests/unit/test_check_docs.py`), per the
    "Regression tests on discovery" rule: (1) prose describing Markdown
    link syntax itself (this very entry's own CLAUDE.md text, `` `[text]
    (target)` `` written as an example) was flagged as a broken link to a
    literal file named "target" -- fixed by stripping inline code spans
    before scanning a line; (2) a broken link resolving outside the repo
    root (enough `../` segments, or -- what actually surfaced it --
    `tmp_path` test fixtures living outside `REPO_ROOT`) crashed
    `Path.relative_to` with `ValueError` instead of reporting cleanly --
    fixed with a fallback to the absolute path.
  - `[tool.mypy] mypy_path` in `pyproject.toml` extended from `"src"` to
    `["src", "tools/validators"]` so the regression test's `from
    check_docs import check_file` resolves under `--strict`, mirroring
    the existing `tests.*` mypy-override pattern for the same
    no-`__init__.py` reason.
- **A `PostToolUse` hook** (`.claude/settings.json`,
  `.claude/hooks/post_edit_format.py`) runs `uv run ruff check --fix` +
  `uv run ruff format` on the single `.py` file an `Edit`/`Write` tool
  call just touched -- scoped to that one file, not `--all-files`, since
  the repo-wide sweep already happens at commit time via
  `.pre-commit-config.yaml`/`make lint`. Not itself part of `make ci`
  (nothing outside `.claude/` depends on it); exists purely to shrink the
  gap between "edited" and "would pass lint" during a session. Verified
  by piping a synthetic hook payload at a scratch file with real lint
  violations before wiring it in -- **not yet proven to fire inside a
  live session**, since `.claude/` didn't exist when this session
  started and the settings watcher only watches directories that existed
  at session start; needs `/hooks` or a restart to activate, same as any
  fresh `.claude/settings.json`.
- `make ci` re-verified clean end to end after all of the above: 45
  tests (up from 42), mypy clean, `check-docs` clean.

### Correction (2026-08-17, later the same day -- the interactive `close_keys` path turned out to be automatable after all)

The "Decisions" entry above states that the interactive `close_keys`
path stays manually verified, per `src/pyflow/rendering/CLAUDE.md`'s
"documented manual-verification convention," and treats that as settled
enough not to redo. Hours later, asked to build a real acceptance suite
covering the interactive window, the close key, and the offscreen
render path through the actual public entrypoints, that convention
turned out to rest on an unexamined generalisation: "CI runners have no
display" (true) had quietly become "this can't be automated" (false).
A real display is checkable at runtime -- `GlfwRenderCanvas(size=(2,
2))` either succeeds or raises -- so a test can probe for one and skip
itself cleanly when it's absent, same shape as any other
environment-dependent test, rather than being excluded from automation
entirely.

- **`tests/integration/test_interactive_window.py`**, new: three tests,
  module-scoped `pytest.mark.skipif` on that display probe. (1) `python
  -m pyflow run` through the real CLI, default (`glfw`) backend,
  `--max-frames` standing in for a user closing the window -- the same
  subprocess-boundary pattern `test_bootstrap.py`/`test_cli.py` already
  use, just without the `--backend offscreen` override every other
  integration test reaches for. (2) The close-key path itself,
  automating the exact manual recipe `src/pyflow/rendering/CLAUDE.md`
  had documented since D4: `window.canvas.submit_event({"event_type":
  "key_down", "key": "Escape"})` scheduled via `loop.call_later(0.5,
  ...)` while `window.run()` genuinely blocks (no `max_frames`) --
  passes only if `run()` actually returns, the canvas reports closed,
  and `frame_count` is high enough to prove the window was live and
  repainting throughout, not frozen until the key arrived. (3) That a
  real window redrawn several times presents genuinely different pixel
  content frame to frame, not just an incrementing `frame_count` --
  verified empirically first that Stage 0's own empty/static scene
  produces bit-identical `renderer.snapshot()` output on every one of 5
  successive frames, so the test adds a small mesh via `self.scene`
  (the extension point `RenderWindow`'s own docstring already sanctions)
  and mutates its colour each frame.
- **`RenderWindow.run(on_frame=...)`**, new, added to make (3) above
  possible: called once per frame, right after it's rendered. Not a
  test-only seam -- a future real-time simulation loop needs exactly
  this shape (advance state once per frame), the same way
  `request_draw` already advances drawing once per frame. `None`
  default, so every existing caller is unaffected.
- **`tests/integration/test_bootstrap.py`** gained
  `test_run_offscreen_produces_non_blank_output`: `bootstrap()` with a
  configured background colour, asserting the returned `last_image` is
  both non-`None` *and* `.any()` (not all-zero) *and* pixel-exact
  against the configured colour -- closing the actual gap in the
  existing offscreen coverage, which checked the CLI's exit code but
  never the rendered pixels themselves through the real entrypoint
  (`tests/unit/test_rendering.py` checks pixels, but through
  `RenderWindow` directly, not `bootstrap()`/`pyflow run`).
- **No product bug found in the interactive window, close-key, or
  offscreen-presentation code itself** -- all three new tests, and the
  extended `test_bootstrap.py` test, passed the first time they were
  run, and stayed green across three consecutive full-suite runs
  (`pytest -x`) plus `mypy src tests` and `ruff check`/`ruff format
  --check`, all clean. The bug this session actually found was
  documentary, not code: the standing claim that the interactive path
  "isn't part of `make test`" and "needs a real display, which CI
  runners don't have" (true) had been written, and then read back
  hours later in this very file, as "not an automated test" (false, or
  at least no longer necessarily true) without anyone re-checking
  whether a display was actually available before repeating the
  claim.
- `src/pyflow/rendering/CLAUDE.md`, `tests/unit/CLAUDE.md` and
  `tests/integration/CLAUDE.md` updated in the same change (dated
  append notes, not rewrites of the 2026-08-16 history, per the Blast
  Radius rule) to point at the new tests and correct the "not
  automated" claims each had been carrying.
- *Verified by running, not assumed:* `pytest -x` three consecutive
  full green runs (49 tests, up from 45), `mypy src tests` clean,
  `ruff check`/`ruff format --check` clean on `src`/`tests`.

### Backlog sanity check, then E8 (2026-08-17)

- Session opened with a consistency pass over `docs/planning/backlog.md`
  before starting new work, per `docs/practices.md`'s session workflow
  step 1. Checked, against the repository directly rather than trusting
  the file: the "19 remaining generic `CLAUDE.md`" count under E9 (exact
  match -- 20 files match the placeholder string, one of them the root
  `CLAUDE.md` itself quoting the placeholder text as an example, not
  carrying it), and the empty/non-empty state of every file E1/E2/E8
  describe. Both matched what the backlog claimed; no drift found, so no
  correction was needed before proceeding.
- **E8 done**: all four `prompts/features/*.md` files (KA-040..043)
  written -- `handbook.md`, `adr.md`, `implementation-plan.md`,
  `agents.md`. Each adds generation-specific guidance on top of an
  existing authoritative source rather than restating it (P-011):
  `handbook.md` points at `docs/handbook/{physics,numerical-methods}/`'s
  own structural docs; `adr.md` points at `adr/README.md` and adds a
  caution -- grounded in `ADR-002`'s known gap (backlog E12) -- to prefer
  project-specific reasoning over generic domain knowledge when drafting
  an ADR; `implementation-plan.md` points at `roadmap.md`'s existing
  TASK-000-onward structure as the precedent to match, and explains how
  it maps onto `prompts/common/TEMPLATE.md`'s `## Task` section rather
  than replacing that template; `agents.md` is the generated-prompt
  counterpart to the root `CLAUDE.md`'s own "Maintaining CLAUDE.md
  Files" section.
- Confirmed this was correctly sequenced: KA-040's stated dependency is
  Handbook *structure*, not Handbook *content* -- the physics/
  numerical-methods `README.md`/`CLAUDE.md` files already establish that
  structure, so writing `handbook.md` did not need to wait for E3/E4's
  still-unwritten entries. This is what the backlog's own stated E8
  ordering ("worth doing before E3 and E4, since `handbook.md` is the
  brief those entries should be written against") depends on.
- Blast Radius: `docs/repository-manifest.md` (four `features/*.md` rows
  ⬜->🟨), the four `Status: planned`->`draft` fields in
  `docs/planning/knowledge-architecture.md` KA-040..043, and
  `prompts/features/CLAUDE.md` (no longer describes the four files as
  unwritten) all updated in the same change, along with
  `docs/planning/backlog.md` E8's own checkboxes and heading text.
  Deliberately left alone: `knowledge-architecture.md` §20's "Agent
  support" completion-gate checkboxes (`- [ ] Feature prompt contexts
  exist.`) -- that whole checklist is unchecked wholesale, including
  items long since true (a README, engineering principles, practices),
  so it reads as a planning-gate concept-check evaluated holistically at
  the gate (§21) rather than a running tracker any single item should
  update in isolation; flagging this as a possible inconsistency worth a
  maintainer decision, not fixing it unilaterally here.
- *Verified by:* re-read each new file against its own KA Definition of
  Done; grepped the repository for every other place naming these four
  files (`docs/repository-manifest.md`, the KA spec, `prompts/features/
  CLAUDE.md`, `docs/planning/backlog.md`) and updated every hit found.

### E12: ADR-002 review (2026-08-17)

- Checked `adr/ADR-002-fvm-first.md` line by line against
  `docs/handbook/numerical-methods/overview.md`, the survey it cites:
  every strength/weakness claimed for FVM, and every alternative's
  rejection or deferral reasoning, matches what the survey records for
  that method. No factual contradiction found.
- **The real gap:** the survey carries per-method "Suitability for
  PyFlow" verdicts and project-specific ratings (FVM rated ★★★★★ for
  both Heat and Scalar transport -- the traits that matter most for
  PyFlow's stated field-centric vision, `prompts/global/project.md`:
  "the engine transports arbitrary fields" -- and explicitly named "the
  strongest candidate for the primary PyFlow framework"), and the ADR
  never cited any of it. Its existing field-related argument was about
  composability with `ADR-003` instead -- a real point, but not the more
  direct one already sitting in the survey. Closed by adding a
  Positive-consequence bullet that quotes the survey's verdict directly,
  plus a dated review note in the ADR's own Context section recording
  that this check happened and what it found -- so the ADR carries its
  own review history rather than only the backlog carrying it.
- `docs/repository-manifest.md` (ADR-002: 🟨->🟩, with its note rewritten
  to describe the review's outcome instead of flagging it as
  outstanding) and `docs/planning/knowledge-architecture.md` KA-027
  (`Status: draft`->`complete`) updated in the same change, per Blast
  Radius. Two backlog entries described the same open item under
  different names (Part I's E12, and an unpromoted duplicate surviving
  in Part III's §7 audit history) -- both closed together, the Part III
  one now pointing at E12 rather than repeating the finding.
- *Verified by:* `make ci` clean (49 tests, mypy clean, no broken doc
  links) after all edits.

### E1: engine architecture and ICDs (2026-08-17)

- **`docs/architecture/engine.md`** (KA-029): the conceptual map of the
  engine's nine replaceable layers (mesh, variables, flux, advection,
  diffusion, time integration, pressure-velocity coupling, linear
  solvers, boundary conditions), each with what it represents, its
  contract, its MVP implementation, which roadmap Stage/task it arrives
  via, and its upgrade path. Grounded in `adr/ADR-002`, `adr/ADR-003`,
  `docs/implementation/{mvp,upgrade-paths}.md` and `docs/glossary.md`'s
  existing "Layer" entry -- confirmed all three already use the same
  nine-layer taxonomy before writing, rather than inventing a tenth
  framing. Explicit that this describes target architecture: Stage 1-4
  layers don't exist as code yet, and each layer's entry says which
  roadmap task it arrives via so that note can be flipped to
  retrospective the moment it lands.
- **`docs/architecture/icds.md`** (KA-030): the user/configuration-facing
  contracts for the six components `adr/ADR-003` names as independently
  replaceable. Deliberately excludes Mesh and Variables -- both are
  `engine.md` layers, but each has exactly one implementation today with
  nothing to choose between, so writing an ICD for a non-existent choice
  would be speculative rather than a real contract (P-016). Proposes
  `numerics.*` configuration keys following the exact pattern
  `RenderingConfig`/`LoggingConfig` already establish in
  `src/pyflow/configuration/schema.py`, explicitly labelled proposed/
  not-yet-implemented rather than presented as current fact.
- **A real structural mismatch found while writing `engine.md`, not
  before:** `docs/planning/dependency-tree.md` groups Gradient/
  Divergence/Sources under "Numerical Operators" and has no separate
  Flux, Variables, or Boundary Conditions node -- a different shape from
  the nine-layer taxonomy `engine.md`, `docs/glossary.md` and
  `upgrade-paths.md` all already agreed on independently. Not resolved
  silently: `engine.md` names the mismatch explicitly in its own
  "Relationship to Other Architecture Documents" section, and the
  backlog's existing "hand-maintained or derived?" open question for the
  dependency tree (Part II) is updated to note it's now unblocked, not
  answered -- picking one shape is a decision for the maintainer, not
  something to fold into writing the document the question depends on.
- Blast Radius: `docs/repository-manifest.md` (⬜->🟨 for both new files),
  KA-029/030 `Status` (`planned`->`draft`), `docs/architecture/CLAUDE.md`,
  `docs/planning/dependency-tree.md`'s header note, and `docs/planning/
  CLAUDE.md`'s own mention of the same open question all updated in the
  same change.
- *Verified by:* `make ci` clean (49 tests, mypy clean,
  `tools/validators/check_docs.py` confirms every relative link in both
  new files resolves) after all edits.

### E3/E4/E6: the Handbook content pass (2026-08-17)

- **Sixteen Handbook entries written**, real domain content with
  citations, not generated mechanically: ten numerical-methods entries
  (`fvm.md`, `meshes.md`, `variable-placement.md`, `fluxes.md`,
  `advection.md`, `diffusion.md`, `time-integration.md`,
  `pressure-velocity-coupling.md`, `linear-solvers.md`,
  `boundary-conditions.md` -- KA-016..025) and six physics entries
  (`incompressible-flow.md`, `heat-transfer.md`, `density.md`,
  `humidity.md`, `buoyancy.md`, `cloud-formation.md` -- KA-010..015).
  Written in each area's own stated dependency order -- `fvm.md` and
  `incompressible-flow.md` first in their respective directories, since
  later entries build on them conceptually (confirmed against each KA
  entry's own "Depends On" list before writing, not assumed from the
  backlog's ordering alone) -- with entries in one area forward-
  referencing not-yet-written entries in the other where KA's own
  dependency graph crosses between them (e.g.
  `pressure-velocity-coupling.md` on `incompressible-flow.md`), resolved
  by the time this session's commit landed.
- Every entry cites real, standard, well-established references (fifteen
  books, nine papers) rather than inventing sourcing -- see `docs/
  references/{books,papers}.md` for the full list, each entry annotated
  with which Handbook file(s) actually cite it.
- **E6, following immediately per the backlog's stated order:**
  `docs/references/{books,papers,websites}.md` populated by transcribing
  every citation the sixteen entries actually made. `websites.md` has no
  entries -- every citation across all sixteen files turned out to be a
  book or journal paper, not a web reference -- recorded explicitly
  (per A3, the file still can't be left empty) rather than inventing one
  to fill it.
- Blast Radius, done as one consolidated pass rather than per-file (16
  files sharing the same few downstream documents made a per-file pass
  wasteful): `docs/repository-manifest.md` (⬜->🟨 for all 19 files across
  `docs/handbook/{numerical-methods,physics}/` and `docs/references/`),
  KA-010..025's sixteen `Status` fields (`planned`->`draft`, each edited
  individually since `replace_all` would have hit unrelated `planned`
  entries elsewhere in the KA spec), `docs/handbook/{CLAUDE,
  physics/{README,CLAUDE},numerical-methods/CLAUDE}.md`, and
  `docs/references/CLAUDE.md` (rewritten from the generic placeholder --
  closes that item under E9 too) all updated in the same change.
- *Verified by:* `make ci` clean (49 tests, mypy clean,
  `tools/validators/check_docs.py` confirms every relative link across
  all 19 new/changed files resolves) after every edit in this pass.

### Generated documentation navigation index (2026-08-17)

- **Decision:** the repository had many documentation pages but no
  single navigable route through them -- three overlapping partial
  indexes existed (`README.md`'s "Where to Start" list,
  `docs/repository-manifest.md`'s status table,
  `docs/planning/knowledge-architecture.md`'s KA spec), none cross-linked,
  and almost no doc used real `[text](path)` Markdown link syntax
  (cross-references were overwhelmingly bare backtick-quoted paths, e.g.
  `` `docs/practices.md` ``). Rather than hand-writing a fourth index
  (the same failure mode that made `docs/repository-manifest.md` v0.1
  describe ~35 files that never existed), a generator was added:
  `tools/generators/generate_docs_index.py` walks the doc-bearing
  directories and writes `docs/index.md`, grouped by directory, using
  each page's own first `#` heading as link text.
- **Alternatives considered:** (1) hand-write `docs/index.md` once and
  rely on the Blast Radius rule to keep it current -- rejected, since
  that rule already applies to `docs/repository-manifest.md` and it
  still drifted badly enough to need a full rewrite; (2) fold navigation
  into `docs/repository-manifest.md` itself -- rejected, that document's
  purpose is completion *status*, not a reading route, and conflating
  them would violate `docs/documentation-guidelines.md`'s "single
  primary purpose per doc" rule.
- **Mechanism:** `make docs` regenerates `docs/index.md`;
  `make check-docs-index` (added to `make ci`) fails the build if the
  committed file doesn't match what the current doc tree would generate
  -- the same enforcement pattern `check_docs.py`/`make check-docs`
  already established for broken relative links (added earlier the same
  day, commit `12b9cb9`). `docs/index.md` carries the standard
  "generated, do not hand-edit" banner.
- Kept deliberately separate from the curated path: `README.md`'s
  "Where to Start" section stays hand-written and short; `docs/index.md`
  is the comprehensive generated map behind it. The two now cross-link.
- Blast Radius: `docs/CLAUDE.md` (new Navigation section),
  `tools/generators/CLAUDE.md` (rewritten from the generic placeholder),
  `README.md` (points at the new index), `docs/repository-manifest.md`
  (new `index.md` row, `Makefile` row updated -- `docs` is no longer a
  placeholder, eleven targets not ten, `tools/` section updated now that
  `generators/` has real content, Maintenance Rules' "link it from any
  appropriate index" step now notes this is satisfied by `make docs` for
  documentation pages specifically), `Makefile` (`docs` target rewritten,
  `check-docs-index` added to `.PHONY` and `ci`).
- *Verified by:* `make ci` clean (54 tests including 5 new for the
  generator; `tools/validators/check_docs.py` confirms every link in the
  generated index resolves; `make check-docs-index` confirms the
  committed `docs/index.md` matches freshly generated output) after
  every edit in this pass.

### Closing out Group E: E5, E7, E13 (2026-08-17)

- **E5:** `docs/handbook/numerical-methods/compatibility.md` brought to
  KA-008's full Definition of Done. Added "Kinds of Compatibility" (all
  seven relationships KA-008 names, each grounded in `overview.md`'s
  existing content rather than invented -- FDM/FVM/FEM/Spectral as
  mutually exclusive alternatives is literally the choice
  `adr/ADR-002-fvm-first.md` made; PIC/FLIP reclassified as a hybrid *in
  itself*, correcting the implicit framing of the old graph, which
  listed it only by frequency) and "Incompatibilities" (four pairings,
  each with the specific structural reason -- no shared data structure,
  opposing domain requirements, or no shared mathematical machinery --
  rather than "rare" left unexplained). `docs/repository-manifest.md`
  and KA-008's `Status` (`draft`->`complete`) updated in the same
  change.
- **E7:** `docs/planning/releases.md` written. Decided write over retire
  after checking `docs/glossary.md`'s "Release" entry -- it is one of
  three named progression concepts, so deleting the file would leave a
  defined term with nothing behind it. Records three concrete trigger
  conditions (external consumer, MVP reached, maintainer decision)
  rather than an open-ended deferral, following the same pattern already
  used for `CONTRIBUTING.md`/`CODE_OF_CONDUCT.md`/`SECURITY.md`.
  `docs/planning/CLAUDE.md`'s own listing (previously "`releases.md`
  (empty)") updated in the same change.
- **E13:** root `CLAUDE.md` gained a "Development Commands" section --
  all eleven `Makefile` targets, one line each, explicitly instructing
  agents to use them rather than reverse-engineer the `Makefile`.
  KA-037's `Status` moved `draft`->`complete`, its Definition of Done
  (compact, actionable, doesn't duplicate the documentation system,
  directs to authoritative sources) now genuinely satisfied.
- Two stale Part III audit-history duplicates found and closed while
  making these changes, following the same pattern as earlier sessions'
  ADR-002/dependency-tree duplicates: a `compatibility.md`-DoD finding
  and a `releases.md`-empty finding had each been promoted into Part I
  (as E5 and E7 respectively) without the original Part III entry being
  marked `[x]` and pointed at its replacement.
- *Verified by:* `make docs` (index regenerated), then `make ci` clean
  -- 54 tests, mypy clean, no broken links, `docs/index.md` confirmed
  current via `make check-docs-index`.

### E10: retiring tools/planner/ and tools/scripts/ (2026-08-17)

- **Decision (maintainer's, asked directly since the initial attempt was
  blocked by the permission classifier):** `tools/planner/` and
  `tools/scripts/` retired -- `git rm -r` both, taking their placeholder
  `CLAUDE.md` files with them. Both had sat empty since the repository's
  first commit, with no mention in the KA spec or roadmap and no
  document anywhere stating what either was for, unlike their siblings
  `generators/` and `validators/`, which both earned real content the
  same day (docs-index generation, broken-link checking respectively).
  Retiring rather than inventing a speculative purpose for either.
- This closes E10 fully and, in the same change, closes the
  `planner/`/`scripts/` line item under E9 -- they are simply no longer
  part of that count. Placeholder `CLAUDE.md` count moved from 45 to 43
  files; the still-generic count moved from 12 to 10.
- Blast Radius: `tools/CLAUDE.md` rewritten to describe two
  subdirectories instead of four; `docs/repository-manifest.md`'s
  `tools/` section (🟨->🟩, now describing a fully-resolved directory);
  `docs/planning/backlog.md`'s Part II "File-structure pruning pass"
  entry updated to record that E10 resolved its own candidate directly
  rather than deferring it there.
- *Verified by:* `make docs`/`make ci` clean (54 tests, no broken
  links, `docs/index.md` unaffected -- neither retired file was part of
  the generated documentation index).

### E2: the last three architecture files (2026-08-17)

- **`docs/architecture/overview.md`, `rendering.md`, `repository.md`**
  written -- the three architecture stubs with no KA basis (checked
  KA §11 in full before writing; it only defines `engine.md`/`icds.md`).
  All three decided "write," not "retire": each had real, distinct
  content once actually drafted.
  - `overview.md`: a single top-level system map
    (configuration -> `bootstrap()` -> engine/physics + rendering),
    deliberately staying one altitude above every other architecture
    document and pointing at them rather than restating them.
  - `rendering.md`: the architecture of wgpu/pygfx as actually
    implemented, read directly from `src/pyflow/rendering/
    {canvas,window}.py` rather than only its `CLAUDE.md` summary --
    the canvas seam, the offscreen/interactive render-loop split,
    `close_keys`/`on_frame`, and an honest note that a second-*renderer*
    seam (distinct from the existing second-*canvas* seam) hasn't
    actually been built. Unlike `engine.md`/`icds.md`, this document
    describes real, already-implemented code, not target architecture --
    stated explicitly so a reader doesn't conflate the two documents'
    tenses.
  - `repository.md`: why the repository's top-level directories are
    shaped the way they are, with the overlap risk against
    `docs/repository-manifest.md` the backlog item itself flagged
    resolved by stating the split directly in both documents --
    structural rationale here, per-file completion status there.
- Three more stale Part III audit-history duplicates found and closed in
  the same pass as this and the E5/E7 duplicates found earlier the same
  day: Physics Handbook content, Numerical Component Handbook content,
  and the `docs/architecture/{overview,rendering,repository}.md` finding
  had all been promoted into Part I (E4, E3, E2 respectively) without
  their original entries being marked `[x]`.
- `docs/repository-manifest.md` (⬜->🟩 for all three -- 🟩 rather than
  🟨 since, unlike `engine.md`/`icds.md`, all three describe things that
  already exist) and `docs/architecture/CLAUDE.md` updated in the same
  change.
- *Verified by:* `make docs`/`make ci` clean.

### Two new practices, from gaps found while closing Group E (2026-08-17)

Maintainer asked directly whether the gaps found while closing Group E
were preventable with a rule -- per the root `CLAUDE.md`'s own Session
Handoff instruction ("where this finds a gap, add a rule that would have
prevented it, not just a one-off fix"), both were.

- **Stale Part III duplicates**, `docs/practices.md`'s "Closing a
  backlog item is a Blast Radius event": a new bullet -- when a Part I
  item was promoted from a Part III finding, closing the Part I item
  doesn't automatically close the Part III original, and nothing before
  today's rule said to check. Found seven instances of exactly this
  drift this session alone (ADR-002, `compatibility.md`, `releases.md`,
  `dependency-tree.md`, both Handbook content findings, and the
  `docs/architecture/{overview,rendering,repository}.md` finding) --
  each correctly promoted and correctly closed in Part I, only the
  Part III original left stale every time.
- **Missing E2 on the first pass**, `docs/practices.md`'s Session
  Workflow step 1: a new note -- resuming a previously-scoped group
  ("close out the E block") from a remembered "what's left" summary
  instead of re-grepping the source document's actual current headers is
  exactly how an entire subsection (E2, three files) went unaddressed
  until a completeness sweep happened to catch it afterward, not because
  one was planned. Also added as item 9 of the End-of-session
  consistency review checklist, since the same check matters whether run
  at the start of resuming work or the end of a session.
- *Verified by:* `make ci` clean; both new practices re-read against the
  backlog history that prompted them for accuracy.

## 18-08-2026

### Scientific-accuracy review of the Handbook and architecture documents (2026-08-18)

Maintainer's request: read the repository, then review the sixteen
Handbook entries plus `compatibility.md` and the five
`docs/architecture/` documents for scientific accuracy, relevance and
readability, improving them where necessary. Twenty-two documents
changed; each one's own Maintenance section records what and why, and
this entry records only the findings that were errors rather than
improvements.

**Errors corrected.** Every one of these was a confident, plausible
sentence -- none read as shaky before being checked, which is the point
worth remembering.

- **`buoyancy.md`: the Boussinesq buoyancy term's sign was inverted.**
  It read $-(\rho - \rho_0)\mathbf{g} \approx \rho_0\beta(T-T_0)\mathbf{g}$
  with $\mathbf{g}$ described as the gravitational acceleration vector.
  With $\mathbf{g}$ pointing down, that expression sinks warm fluid. Both
  sides were flipped consistently, which is exactly why it read as
  coherent. Now correct for the stated convention, with the
  scalar-$g$/upward-unit-vector alternative shown alongside and a
  sanity-check in words.
- **`fvm.md` and `fluxes.md` disagreed about $\rho$.** `fvm.md`'s general
  conservation equation omitted it where `fluxes.md`'s face-flux
  expression included it, leaving the latter dimensionally inconsistent
  unless $\Gamma$ meant something the documents never said. `fvm.md` now
  fixes one convention for the whole area and `fluxes.md` and
  `diffusion.md` are anchored to it.
- **`advection.md` attributed a WENO claim to `overview.md`, which does
  not mention WENO at all.** The point (very-high-order schemes being
  more naturally expressed in finite-difference-adjacent formulations)
  comes from `adr/ADR-002-fvm-first.md`'s Negative consequences, and is
  now cited there.
- **"Upwind is unconditionally stable" was wrong in `fluxes.md` and in
  `docs/architecture/icds.md`.** Upwind is unconditionally *bounded*;
  stability is a joint property of the spatial scheme and the time
  integrator, and explicit upwind still diverges above its CFL limit.
- **`diffusion.md` treated non-uniform structured spacing as a cause of
  non-orthogonality.** A graded Cartesian mesh is still orthogonal; what
  it loses is the centredness that makes the difference quotient
  second-order. `meshes.md` gained a taxonomy separating
  non-orthogonality, skewness and non-uniformity, which are fixed by
  different means.
- **`variable-placement.md` explained the checkerboard problem via the
  wrong mode.** It described the pressure field as producing no net
  velocity divergence, which is the dual (velocity) manifestation. The
  mechanism that lets a checkerboard *pressure* field survive is the
  $2\Delta x$ central-difference stencil returning exactly zero gradient
  for it; both modes are now stated.
- **`humidity.md` and `cloud-formation.md` used "air holds water
  vapour".** Saturation vapour pressure is a property of the
  vapour-liquid equilibrium, essentially independent of the air.
  Harmless phrasing in general; not harmless in the entry whose subject
  is why condensation happens.
- **`docs/architecture/engine.md` described the numerical-methods
  handbook as unwritten** and `advection.md` as an empty stub -- true
  when written on 2026-08-17 and false by the end of that same day.
- **`docs/architecture/rendering.md`'s header claimed KA §11 covered it**
  and pointed at `engine.md` for an explanation of why neither had a KA
  entry. `engine.md` is KA-029 and its header says nothing of the kind;
  the reasoning is in `docs/architecture/CLAUDE.md`, which the header now
  points at.
- **`docs/architecture/overview.md`'s diagram contradicted its own
  prose**, drawing a "fields" arrow from Engine to Rendering that the
  document's "Why This Split" section says does not exist yet. Its box
  borders also did not line up with their contents. Redrawn, arrow
  removed, with a note saying why.

**Gaps closed, as distinct from errors.**

- `linear-solvers.md` gained **GMRES**, which
  `docs/implementation/upgrade-paths.md`, `engine.md` and `icds.md` all
  named on the Linear Solvers upgrade path while the handbook entry
  explaining those candidates did not cover it.
  `docs/references/papers.md` (Saad & Schultz 1986) and
  `docs/repository-manifest.md` updated in the same change.
- **The singular pressure system** a closed, all-velocity-boundary domain
  produces -- the MVP's own lid-driven cavity validation case -- was not
  mentioned anywhere. Now covered in `pressure-velocity-coupling.md`
  (authoritative), with the consequences recorded in `linear-solvers.md`
  (CG needs positive-*definite*), `boundary-conditions.md` (the
  compatibility condition on boundary data) and `icds.md` (both as real
  ICD compatibility requirements, not future concerns).
- **The forward-Euler/central-difference pairing is unstable at every
  timestep**, which matters because `upgrade-paths.md` lists Euler below
  RK4 and central difference above upwind. `time-integration.md` now says
  so, as the concrete instance of the advection/time-integration
  interaction `adr/ADR-003` flags in the abstract.
- **RK4's fourth-order accuracy is not the finished solver's temporal
  order**, being capped by first-order upwind spatially and by
  pressure-coupling splitting temporally. Recorded in
  `time-integration.md` and `icds.md` so a measured convergence rate is
  read as expected rather than as a bug.
- `docs/architecture/repository.md` was missing **`.claude/`** from its
  top-level directory list; it is tracked in git and holds the repo's own
  post-edit hook.
- `density.md` gained the **Boussinesq validity conditions** (including
  the shallow-domain one relative to the atmospheric scale height, a real
  ceiling on the approximation for `docs/planning/dreams.md`'s
  atmospheric ambitions) and the ideal gas law that makes its density
  determinants quantitative.
- `cloud-formation.md` gained the **cloud-condensation-nuclei** argument
  for why a saturation-threshold rule is a defensible model -- and what
  aerosol assumption it quietly makes.
- `boundary-conditions.md` gained **velocity/pressure BC pairing** and the
  global mass-conservation condition, both of which decide whether a case
  is solvable at all.

**`compatibility.md`'s frequency groupings -- first caveated, then
removed.** The initial pass left them in place with a
provenance-and-caution note, reasoning that rewriting unsourced labels
would substitute one judgement for another. That was the wrong call, and
re-reading KA-008 on the maintainer's prompt showed why: its Content
Requirements ask the document to distinguish seven kinds of
compatibility and state that it "should not collapse these into one
compatibility label." A "very common / common / occasional / rare" band
is exactly one such label, so the groupings were against the spec
regardless of whether any individual entry was accurate -- and two were
not (FVM/SPH banded alongside FVM/FEM; "FEM ↔ Structural Mechanics"
pairing a numerical method with an application domain). See the
follow-up entry below.

**Guidance added**, per the Session Handoff rule's "add a rule that would
have prevented it": `docs/handbook/numerical-methods/CLAUDE.md` (one
notation convention; boundedness/stability/accuracy are three properties;
verify a cross-reference's target actually makes the claim),
`docs/handbook/physics/CLAUDE.md` (state and sanity-check sign
conventions; standard-but-loose domain phrasing is a distinct risk from
invented claims), `docs/architecture/CLAUDE.md` (this directory is
downstream of the Handbook on domain questions; a diagram makes claims
and is held to the same tense discipline as prose).

- *Verified by:* `make ci` clean.

### compatibility.md restructured: frequency groupings removed (2026-08-18)

Follow-up to the review above, on the maintainer's prompt that the
`compatibility.md` issue still needed fixing rather than annotating.

**What changed.** The inherited "very common / common / occasional /
rare" frequency groupings and the ASCII combination diagram were removed
and replaced by a **Pairwise Relationships** table that gives each
pairing its *kind* -- the seven relationships KA-008 names -- rather than
a frequency. The classification tree was promoted ahead of the table
(it establishes the families the table indexes) and aligned with
`overview.md`'s eight families, which treat PIC and FLIP as one entry.
The "Hybrid approaches" section was extended to back two classifications
the new table asserts: spectral element methods and MPM are single
hybrid methods, not couplings, and are routinely misread as the latter.

**Why removal rather than correction.** KA-008's Content Requirements
already answered this and had not been re-read: they ask the document to
distinguish the seven kinds and say explicitly that it "should not
collapse these into one compatibility label." A frequency band is one
label, and two pairings sharing a band can be a coupling and an
equivalence -- architecturally nothing alike. The groupings were
therefore against the spec independently of accuracy. Two were also
wrong on their own terms: FVM/SPH shared the top band with FVM/FEM
despite the latter being routine industrial practice and the former a
narrow research area, and "FEM ↔ Structural Mechanics" was not a method
pairing at all. The diagram separately drew FDM as the root of a
hierarchy the classification tree contradicts.

**Recorded, not rewritten.** `docs/planning/backlog.md` E5 explicitly
recorded the opposite decision on 2026-08-17 ("the existing pairwise
graph and frequency grouping were kept as observed-practice-at-a-glance,
not replaced"). That item now carries a "Superseded in part" note rather
than being edited to match, so the change of mind stays visible.

**Rule added**, `docs/handbook/numerical-methods/CLAUDE.md`: when content
is doubtful, re-read the KA entry's Content Requirements before deciding
what to do with it. An honest caution beats a silent error but is not the
ceiling -- here the specification already settled the question, and
attaching a caveat postponed a fix that was available all along.

- *Verified by:* `make ci` clean.

### Review of the remaining documentation (2026-08-18)

Maintainer's prompt: check the rest of the documentation the same way the
Handbook and architecture documents were checked. Worked in priority
order -- domain-content documents first, where scientific accuracy
applies, then process and planning documents for staleness and internal
consistency.

**`docs/handbook/numerical-methods/overview.md` (the survey).** The
significant finding, because `adr/ADR-002-fvm-first.md` cites these
ratings as part of its rationale: **the five-star scale silently inverts
for three attributes.** The legend said ★★★★★ means "Excellent /
industry-leading" and ★☆☆☆☆ "Poor", but implementation complexity,
compute requirement and memory requirement are *cost* rows where five
stars means very expensive. FDM's ★★☆☆☆ implementation complexity reads
as "Limited" on the stated scale and means "easy to implement"; FEM's
★★★★★ on the same row means the opposite of "excellent". Reading the cost
rows on the capability scale inverts the survey's conclusions about
exactly the trade-off ADR-002 had to weigh. The legend now states both
polarities. A related wrinkle is also now explained rather than left to
be noticed: the per-method "Computational Characteristics" sections state
CPU/GPU/memory as *performance* (more is better) while the Summary tables
state the same facts as *requirements* (more is worse), so FDM's
"CPU: ★★★★★" and "Compute requirement: ★★☆☆☆" agree despite looking
opposed.

No rating was changed and no per-method content rewritten -- they are
unsourced qualitative judgements, and revising them would substitute one
judgement for another. Unlike `compatibility.md`'s frequency groupings,
KA-007 genuinely *requires* computational and memory ratings, so these
stay and were made legible instead of removed.

Also in the survey: the "Common companions" and "Compatibility" fields
were marked as pointers into `compatibility.md` rather than compatibility
claims, since several name relationships that are not couplings at all
(FDM/FVM/Spectral are mutually exclusive; spectral element methods are a
hybrid; MPM's FEM-like grid is internal) -- a direct contradiction with
the restructured `compatibility.md`, and blast radius from that change.
The Spectral entry now distinguishes global from spectral element
methods, which its own complex-geometry rating depends on. KA-007's five
uncovered Content Requirements are listed explicitly so its `draft`
status means something specific.

**Stale status claims, five of them, in documents that do not track
status.** `prompts/global/project.md` called the Handbook "largely
unwritten" -- in a document whose opening paragraph says it excludes
current status; `docs/glossary.md` said `releases.md` "is empty" after E7
wrote it; and both `docs/repository-manifest.md` and
`docs/architecture/CLAUDE.md` described the A2c instance decision as
still open on the same day `ADR-005` decided it. Each status claim was
deleted rather than updated.

**Stale counts from a deletion.** E10 retired `tools/planner/` and
`tools/scripts/`, taking two `CLAUDE.md` files with them.
`docs/planning/backlog.md` E9 correctly says 43 files, 10 placeholders;
`docs/planning/roadmap.md`'s TASK-009 row and
`docs/repository-manifest.md` both still said 45 and 19. Corrected, with
the backlog named as the authoritative count so the next update has one
place to start from. `roadmap.md` also still described `make docs` as
"a placeholder correctly, nothing exists yet to build" while the manifest
correctly described it regenerating `docs/index.md`; and it said ten
Makefile targets where there are eleven.

**Cross-reference corrections.** `adr/ADR-002` described `fvm.md` as
"to be written separately"; `adr/ADR-003` described the ICDs as future
and attributed "future plugin/component discovery" to the ICDs when the
phrase is in KA-030's Enables list, not in `icds.md` -- which does not
address plugin discovery at all. `icds.md` now records that gap
deliberately. ADR-003's cross-layer-interaction consequence also now
names the two concrete instances the Handbook has since documented, one
of which crosses advection/time-integration rather than the
advection/diffusion pair the ADR anticipated.

**`docs/glossary.md`** gained **Boundedness** and **Numerical Stability**
entries. The distinction between them is now load-bearing in four
documents, and the glossary's stated job is terms "whose meaning has been
explicitly clarified for PyFlow."

**Rules added**, `docs/practices.md`: completeness claims belong only in
the manifest and the backlog, and are deleted rather than updated when
found elsewhere; and a deletion changes counts stated elsewhere, which is
the case most easily missed because nothing in the change mentions the
number that just became wrong.

**Checked and found sound**, no changes needed: `docs/practices.md`
itself, `docs/engineering-principles.md`,
`docs/documentation-guidelines.md`, `docs/implementation/golden-demos.md`,
`docs/implementation/{mvp,upgrade-paths}.md`,
`docs/planning/{implementation-plan,dependency-tree,dreams,releases}.md`,
`docs/references/websites.md`, `README.md`, `adr/{README,ADR-001,ADR-004,
ADR-005}.md`, and `docs/architecture/compute-and-rendering-stack.md`
(whose own status banner was already correct -- it was the two documents
describing it that were stale).

- *Verified by:* `make ci` clean.

### Review of the CLAUDE.md files and prompts (2026-08-18)

Maintainer's prompt: check these the same way as the documentation. All
43 `CLAUDE.md` files and all 14 files under `prompts/` were read.

**Four `CLAUDE.md` files carried stale claims about how complete
something else was** -- the same failure the previous review found across
`docs/`, here concentrated in files whose job is explaining a directory,
not tracking its progress:

- `tests/CLAUDE.md` described `unit/` and `golden/` as empty placeholders
  awaiting their first real test. Both got real tests on 2026-08-16;
  `unit/` now holds seven modules and `golden/` its own written
  `CLAUDE.md`. Only `performance/` is still genuinely empty.
- `.github/workflows/CLAUDE.md` said `make ci` "chains `lint`,
  `typecheck`, `test`" in the same paragraph as calling the Makefile the
  single authoritative sequence. `check-docs` and `check-docs-index` were
  added to that target on 2026-08-17, so the file contradicted the
  authority it was pointing at. The step list is now deleted rather than
  corrected -- restating it is what made it wrong.
- `docs/implementation/CLAUDE.md` described golden demos as "runnable
  code" under `examples/golden-demos/`. The public-API rule (2026-08-16)
  replaced the demo script with a YAML config file, which
  `examples/golden-demos/CLAUDE.md` and `examples/CLAUDE.md` both state
  correctly.
- `docs/architecture/CLAUDE.md`'s A2c claim, corrected in the previous
  session's commit.

**Backlog phrasing.** Two open items (E9, F2) carried a *Verified by:*
line, which is this backlog's convention for recording what was actually
run on a **completed** item. On an open item it reads as a claim the
criterion already holds -- E9's said no `CLAUDE.md` still contains the
placeholder text, while its own body correctly says ten do. Both
relabelled *Done when:*. F2's artifact list also still named
`examples/golden-demos/empty_window.py`, deleted the same day it was
added.

**Prompts.** `prompts/global/project.md` was corrected in the previous
commit. Two briefs were strengthened with what this review actually
found, since they are where a future generating agent gets its standard
from:

- `prompts/features/handbook.md` gained "Four Failure Modes the Existing
  Entries Actually Hit" -- inconsistent notation between entries,
  unchecked sign conventions, cross-references to claims the target does
  not make, and standard-but-loose domain phrasing. Its existing "What to
  Avoid" covered inventing a claim, which none of these were: every one
  read as confident and correct.
- `prompts/features/agents.md` gained the completeness-claim bullet, with
  the four instances above named. Its existing warning about guidance
  that drifts was close but framed around test counts and file lists, not
  around describing another directory's state.

**Read and found sound**, no changes: the remaining 39 `CLAUDE.md` files
-- notably `src/pyflow/CLAUDE.md` (the circular-import lesson),
`src/pyflow/rendering/CLAUDE.md` (the fullest file in the repository, and
accurate against the code), `tools/generators/CLAUDE.md` (its listed scan
directories match the script's own `SECTIONS`), `tools/validators/`,
`tests/integration/`, `tests/golden/`, `examples/`, `planning/` and its
two children (the eleven-empty-`.yaml` count is right), `docs/references/`,
`adr/`, and the four `prompts/*/CLAUDE.md` files. Also sound:
`prompts/common/TEMPLATE.md`, the four `task-*.md` prompts (historical
records of what was asked for, correctly preserved rather than updated),
`prompts/features/adr.md` and `implementation-plan.md`.

The ten remaining generic placeholders are not counted as findings: they
are tracked in `docs/planning/backlog.md` E9, each with a stated reason
for waiting, and the root `CLAUDE.md` permits the placeholder until
something specific is known. Checked each against that test --
`assets/` and its four children wait on D3-class content, `docs/tutorials/`
and `examples/{tutorials,experiments}/` on any content at all,
`src/pyflow/physics/` on physics existing, `tests/performance/` on a first
benchmark. None has something specific known and unwritten.

- *Verified by:* `make ci` clean.

### `make ci` does not verify documentation content (2026-08-18)

Found while answering the maintainer's question of whether anything
should be added to the `CLAUDE.md` files after the documentation review.

**The finding.** The root `CLAUDE.md` called `make ci` "the one command
that verifies a change is ready before committing." For code that is
true. For this repository, which is overwhelmingly prose, it is
substantially not: `pre-commit` covers whitespace, YAML syntax and
Python; `check_docs.py` checks only that relative link *targets exist*
(its own docstring says so); `generate_docs_index.py --check` compares
paths and H1 titles; pytest covers Python. **Nothing in the chain reads
the body of a Markdown file.**

Every error the day's documentation review found had been passing
`make ci` for days -- the inverted Boussinesq sign, the dimensional
inconsistency between `fvm.md` and `fluxes.md`, the misattributed WENO
citation, nine stale status claims. So did a corruption introduced
*during* the review: a shell heredoc turned `$\rho$` into `$ho$` with an
embedded carriage return in `prompts/features/handbook.md`, and
`make check-docs` passed with the control character still in the file.

**Recorded in three places, each at the altitude that needs it:**

- Root `CLAUDE.md`, Development Commands: `make ci` verifies structure,
  not content, for documentation; run it always, but treat it as a floor
  for prose rather than a verification. Blast Radius and the
  end-of-session review are what actually catch content errors, and both
  need someone reading.
- `docs/handbook/CLAUDE.md`: a new "Maths Notation" section. The
  sixteen entries use `$...$` and `$$...$$`, nothing renders or
  validates them, and backslash-heavy LaTeX is exactly what a shell
  heredoc mangles -- so an equation is only as correct as the last
  person to read it, and bulk-editing these files through a script is
  where that goes wrong.
- `tools/validators/CLAUDE.md`: two greps recorded as having *earned*
  the test that file already sets ("add a check if a Blast-Radius-
  adjacent grep fires often enough to be worth automating"). Stale
  completeness claims outside the manifest and backlog would have caught
  all nine instances but needs a review-and-confirm shape given false
  positives; stray control characters and unbalanced inline `$` is
  cheap, deterministic and a genuine CI failure, making it the better
  first candidate. Neither is built -- they are candidates with
  evidence, which is what that file asks for.

**On the process point**, since it cost a round trip: the proposed root
`CLAUDE.md` edit was initially held back as touching "the repo's
constitution." The maintainer challenged that, correctly. The file is a
genuine inheritance root -- global operating rules, which lower
`CLAUDE.md` files may extend but not contradict -- but the edit lands in
Development Commands, the one section that is factual description of
tooling rather than rule, and it does not change what anyone is obliged
to do. The reasoning also inverts: because everything inherits from that
file, a wrong factual claim there propagates *further* than one in a
leaf, which argues for fixing it promptly rather than pausing. Judge an
edit by its nature, not by the standing of the file it lands in.

- *Verified by:* `make ci` clean; every tracked Markdown file scanned for
  stray carriage returns (clean apart from the generated `docs/index.md`,
  unchanged).

### Markdown validation tooling (2026-08-18)

Maintainer asked what tooling could validate Markdown, after the previous
entry established that `make ci` does not read Markdown bodies. Four
things landed; two of them found real defects on their first run.

**`mixed-line-ending`, `--fix=no`** (`pre-commit/pre-commit-hooks`, the
hook repo already pinned here, so no new dependency). Verified against
the actual corruption before adopting: a stray carriage return mid-line
registers as a CR-terminated line among LF ones, so the hook fires. It
passes on all 106 tracked Markdown files as they stand. `--fix=no` is
deliberate -- auto-fixing turns the stray CR into a real line break,
replacing one silent corruption with another and reporting success.

**`codespell`.** Found a genuine defect on its first run:
`docs/planning/backlog.md` still carried "Rename
`knowledge-architecture.md`" as an **open** `[ ]` item, three days after
the rename was done (2026-08-15, all 35 references across 22 files
updated in the same change). The misspelling in the item's own body was
the only trace left outside the append-only changelog. Exactly the "items
fully complete but still showing `[ ]`" drift `docs/practices.md` records
under "Closing a backlog item is a Blast Radius event" -- and not
something any structural check would have found. Item closed.

The ignore list in `pyproject.toml` holds only what the first run
actually flagged and justified: `yau` (Rogers & Yau, cited by two physics
entries), `pre-empt`/`pre-emptively`/`re-using` (British hyphenated
forms, consistent with this repository's spelling), and `architechture`
(a former filename preserved in the append-only changelog). Nothing
speculative -- an entry added "just in case" is one that will eventually
hide a real typo.

**`tools/validators/check_claims.py` and `make check-claims`.** The
completeness-claim check the previous entry recorded as an earned
candidate. It **verifies rather than pattern-matches**: it resolves the
paths a claim names and reports only where the claim contradicts what is
on disk, so it never flags prose merely for containing the word "empty".
Advisory and deliberately outside `make ci` -- it exits 0 either way,
because telling a real drift from a document quoting the rule needs
judgement. Wired into the end-of-session consistency review as step 10.

Building it was itself instructive, in three ways worth recording:

- **The same escape-mangling struck again, in Python this time.** A `\b`
  written through a shell heredoc became a literal backspace byte
  (`\x08`) inside the regex, so the quantifier suppression silently never
  matched. `make lint` does not catch a control character inside a string
  literal. This is the second instance in two days of the hazard
  `docs/handbook/CLAUDE.md` now documents, and the reason the rest of
  this work was done with editing tools rather than heredocs.
- **A heuristic was built, tested, and removed.** Suppressing findings
  near a quantifier ("no file tracked in `X` is empty") looked sensible
  and would have silently discarded a true positive: the real
  `docs/glossary.md` drift read "no release process is defined,
  `releases.md` is empty". Reporting one known false positive beats
  missing a real one, so the suppression went and the decision is pinned
  as a named test in `tests/unit/test_check_claims.py` -- a future
  contributor who re-adds it will see why it went first.
- **The tests are the only evidence it works.** The checker reports
  nothing against today's repository, because every instance it was built
  for had already been fixed by hand. The ten unit tests reconstruct the
  real historical drifts as fixtures.

**`generate_docs_index.py` writes with `newline="\n"`.** It used text
mode, so on Windows it emitted CRLF, making `docs/index.md` the one file
in the repository with carriage returns on disk -- invisible in diffs
because git's `eol=lf` normalised it on commit, but contradicting
`.editorconfig`. Regenerated; the file is now LF everywhere.

**Considered and not adopted**, with reasons, so this is not re-litigated
from scratch: `mdformat` would reflow all ~18k lines and destroy the
hand-wrapped style for no correctness gain; Node-based `markdownlint-cli2`
has the better rule set but drags a Node toolchain into a Python-only
repository and its CI; external link checkers have nothing to do here
(`websites.md` is empty by design). `pymarkdownlnt` (pure-Python
markdownlint) and Vale (prose/terminology rules, which could mechanise
the "air holds moisture" class this week's review found by hand) were
left as separate decisions -- Vale is the better fit for this project's
actual failure modes and also the heaviest, being a Go binary with a rule
set to curate.

**The honest limit is unchanged.** None of this would have caught the
inverted buoyancy sign, the dimensionally inconsistent equation, or the
citation whose target did not support it. Even the corrupted `$ho$` was
only machine-detectable via the stray control character; had the escape
collapsed to plain text, nothing would have flagged it.

- *Verified by:* `make ci` clean (64 tests, up from 54);
  `uv run pre-commit run --all-files` clean across all nine hooks;
  `make check-claims` reporting only its one documented false positive.

## 19-08-2026

### Closed E9: revised its Done-when, retired three placeholder directories

Read the repository and `docs/planning/backlog.md` to find the next
Stage 0 item. E9 (fill the placeholder `CLAUDE.md` files) was next, but
its own per-directory notes were already refusing to invent content for
directories that are still genuinely empty -- `performance/`,
`experiments/`/`tutorials/`, `physics/` all say some form of "still
generic, nothing specific to write against yet." The item's own *Done
when* ("no `CLAUDE.md` still contains the generic placeholder text")
contradicted that: satisfying it literally would mean inventing
speculative documentation for empty scaffolding, which is exactly what
the per-directory notes were declining to do one at a time.

**Maintainer's call:** revise the *Done when* to "no placeholder remains
in a directory that has content," and retire any directory that has no
near-to-medium-term purpose rather than write speculative guidance for
it.

Checked every one of the 10 remaining placeholders against the ADRs,
roadmap and manifest before deciding which:

- `assets/icons/`, `assets/shaders/`, `assets/textures/` -- no document
  anywhere (KA, roadmap, ADR, manifest) ever stated what any of the
  three was for. Same test that retired `tools/planner/`/`tools/scripts/`
  (E10, 2026-08-17): nothing to write against and no record of intent
  either. **Retired.** `assets/colourmaps/` is different and stays --
  `adr/ADR-005-compute-rendering-instances.md` and roadmap TASK-017
  (Field Rendering) concretely tie colour maps to upcoming work, so its
  placeholder is deferred, not purposeless.
- `docs/tutorials/`, `examples/tutorials/`, `examples/experiments/` --
  have a stated purpose (the manifest's own text) and are named in
  TASK-000's already-closed acceptance criteria ("package structure
  matches the documented architecture"). Retiring these would mean
  reopening a closed Stage 0 item and reversing recorded architecture,
  not clearing undocumented cruft -- a materially different, riskier
  call than the assets three. Maintainer's decision: **kept**, distant
  timing is not the same test as "nothing states what this is for."
- `src/pyflow/physics/`, `tests/performance/` -- core, imminent
  architecture (Stage 1 physics work; benchmarking once there is
  something to benchmark). Never in question.

**Result:** `assets/icons/`, `assets/shaders/`, `assets/textures/`
deleted (three directories, three placeholder `CLAUDE.md` files).
`docs/architecture/repository.md` and `docs/repository-manifest.md`'s
`assets/` section updated to match. The seven remaining placeholders
(`assets/`, `assets/colourmaps/`, `docs/tutorials/`,
`examples/experiments/`, `examples/tutorials/`, `src/pyflow/physics/`,
`tests/performance/`) were checked directly, not assumed, to confirm
each is genuinely content-free (empty, or a bare docstring-only
`__init__.py`) before closing E9 under the revised criterion.
`docs/planning/backlog.md` E9, `docs/planning/roadmap.md`'s TASK-009 row
and `docs/repository-manifest.md`'s CLAUDE.md-files section all updated
together (40 files, 7 placeholders, down from 43/10).

**Two stale claims found in the same table, fixed in the same change**
(found while reading the roadmap for this item, not a separate pass):
TASK-008's row still said "the Handbook is largely empty," stale since
2026-08-17 when all sixteen entries were written (E3/E4); and the note
below the table still said `make install`/`make test` were "still
expected to fail," stale since B2/C1a/C1b landed 2026-08-15/16 --
`uv.lock` is committed and `make test` runs 64 tests. Both corrected,
both re-verified against the current repository state rather than
trusted from the old text.

- *Verified by:* `make ci` clean (64 tests, unchanged -- no test files
  touched); `docs/index.md` confirmed current
  (`generate_docs_index.py --check`); no broken relative links
  (`check_docs.py`); every count restated across
  `backlog.md`/`roadmap.md`/`repository-manifest.md` cross-checked
  against a direct `find . -name CLAUDE.md` byte-size scan, not carried
  forward from the stale text.

### Closed F1: Git conventions, widened to cover commit gating, branching/review and dependency updates (2026-08-19)

Maintainer flagged, immediately after E9 closed, that F1's original
narrow scope (branch naming, commit granularity, message form) was
missing something: general software-engineering rules/best practices.
Checked first whether that already had a home before writing anything --
it didn't. `docs/engineering-principles.md` is stable, high-level
philosophy (P-001..018), not concrete rules. `docs/practices.md` covered
only session workflow for an agent (Blast Radius, the consistency
review), nothing about what gates a commit or how branching/review
works. `.pre-commit-config.yaml`'s git hook runs lint/format/mypy only --
not the test suite, not the docs checks. Confirmed via
`AskUserQuestion`, multi-select, all four accepted: Git conventions,
commit gate policy, branching/review workflow, dependency update policy.

**Branch renamed `master` -> `main`.** The rename itself (`git branch -m`)
was blocked by the permission classifier on first attempt -- a
repository-state-changing action outside plain file edits, correctly
routed back for explicit confirmation rather than worked around.
Maintainer approved via a direct question. Reasoning recorded in
`docs/practices.md`'s new Version Control section: free to do with no
remote and no collaborators yet; the same rename after a remote's
default branch and any collaborator tooling already pointed at `master`
would cost real friction for an identical result. Every reference
updated in the same change -- `.github/workflows/ci.yml`
(`push.branches`, plus the inline comment that had explicitly deferred
to this exact decision), `.github/workflows/CLAUDE.md` (two mentions),
`docs/repository-manifest.md`'s `.github/` section. `docs/CHANGELOG-
DESIGN.md`'s own earlier entries recording the original `master` commit
were left untouched, per this file's append-only convention -- they were
correct as of when written.

**Commit gate made explicit, not changed.** The git hook stays scoped to
lint/typecheck (deliberate -- a hook that runs the full suite on every
commit adds friction most commits don't need); `make ci` being required
before any commit was already this project's actual practice, just
unstated as a rule anywhere before now.

**Branching and review deliberately left minimal**, per KA-003's own
content requirement to avoid multi-person process before there are
multiple people -- the same reasoning already used to defer
`CONTRIBUTING.md` (Part II). Recorded as single-branch, direct-commit,
no PRs, with an explicit trigger to revisit (a second contributor or a
remote, whichever comes first) rather than left as a silent default that
looks like an oversight.

**Tooling dependency update policy** added as a direct generalisation of
the existing Python version policy -- periodic review, update when it
benefits the project, verify Python-version compatibility before
bumping -- extended to `.pre-commit-config.yaml` hook revisions and
`uv.lock`.

`docs/repository-manifest.md` (practices.md: 🟨->🟩) and KA-003's
`Status` (`draft`->`complete`) updated in the same change -- practices.md
remains a living document by design (new practices get added as gaps
are found, same as before), `complete` records that it currently
satisfies its own Definition of Done, not that nothing will be added to
it again.

- *Verified by:* `make ci` clean after the branch rename and every
  document edit; `git branch -a` confirmed only `main` exists locally,
  no stray `master` left behind.

### Closed F2: inventory sweep, both directions (2026-08-19)

Maintainer asked for F2 (sweep the inventories for anything Stage 0
created but never recorded) plus its inverse: things recorded that no
longer exist. Ran both directions against all 159 tracked files rather
than sampling.

**Forward direction found one real gap:** `.claude/settings.json` and
`.claude/hooks/post_edit_format.py` had real content since early Stage 0
but were in neither `docs/repository-manifest.md` nor `docs/planning/
knowledge-architecture.md`, and neither directory had a `CLAUDE.md` at
all -- a genuine hole in KA-038's collective "every directory" rule that
nothing had ever caught, because no backlog item created `.claude/`; it
came from Claude Code tooling setup, outside the Blast Radius habit that
catches everything routed through a tracked task. Fixed: two new
`CLAUDE.md` files, a new manifest section, CLAUDE.md-file counts updated
everywhere they're restated (42 files now, up from 40; 35 real content,
7 still placeholder).

**Inverse direction found zero false claims of file existence** -- every
apparent hit from an automated path-extraction pass turned out to be a
naming-pattern placeholder, a relative-path fragment, or a claim already
correctly phrased as absence. It did surface a different kind of
mismatch the "does this path exist" check can't see: KA `Status:` fields
disagreeing with the manifest's status symbol for the same document.
Three found (`README.md`/KA-001, `golden-demos.md`/KA-035 -- whose own
"Initial golden demo" text may itself be stale, still describing a full
2D simulation rather than Empty Window -- and `compatibility.md`/KA-008,
the reverse direction). Deliberately not resolved here: syncing a status
label without reading the document against its own Definition of Done
risks manufacturing a second inaccuracy on top of the first, the same
reasoning E12 applied to `ADR-002`. Recorded as a new Part II item
instead of guessed at.

- *Verified by:* `make ci` clean; `find . -name CLAUDE.md` count matches
  the manifest's restated 42; the eleven `planning/**.yaml` files
  confirmed as the only zero-byte tracked files (A3's carve-out); every
  full path named in either inventory checked against disk directly.

### Closed F3: Stage 0 exit audit (2026-08-19)

Checked all nine Stage 0 Completion Criteria against direct evidence
immediately after F2, not against carried-over status from earlier in
Stage 0. **Result: eight of nine fully met.** The ninth -- CI executing,
demonstrated by a green run on a real runner -- was already known to be
open, with the same reason and trigger condition recorded since
2026-08-16 (no remote exists yet; deferred until a 2D demo exists). This
audit did not discover a new gap; it confirmed the existing accounting
was accurate.

**Two criteria got materially stronger evidence than they had before.**
B2's original "clean environment" verification was a `make clean` ->
`make install` cycle run in place, never an actual fresh clone. Ran one
for real this session: `git clone` into an empty directory, then `make
install`, `make ci` (64 tests passing), and `pyflow run` opening a real
render window from that clone -- all succeeded end to end. This is
directly what criteria 6 and 9 ask for and had not, until now, actually
been tested that way.

**One criterion needed an explicit decision, not just a check.**
`assets/`'s manifest row is still ⬜ against criterion 3's literal
check ("every ⬜ row has become 🟨/🟩 or been removed, except the eleven
`planning/**.yaml` files"). Writing placeholder colourmap content to
force a status change would have been exactly the kind of speculation
E9's revised *Done when* already refuses to manufacture for empty
directories elsewhere. Extended A3's existing carve-out to cover it
instead, on the same terms as the yaml graph: content gated on Stage 1+
field-rendering work (TASK-017), not an oversight. Recorded in three
places together -- the A3 note in `docs/planning/backlog.md`,
`docs/repository-manifest.md`'s `assets/` section, and `docs/planning/
roadmap.md`'s Completion Criteria bullet 3.

The full per-criterion record was written directly into `roadmap.md`'s
Stage 0 Completion Criteria section (a new "Exit audit" subsection)
rather than duplicated in the backlog, per P-011 -- that document already
states what each criterion means, so the audit result belongs next to
it, not in a second copy. The stale "Stage 0 is in progress and
substantially incomplete" status paragraph immediately above it (dated
2026-08-15, the day the engineering environment did not exist yet) was
also corrected in the same change -- found while updating the section
directly above it, not a separate pass.

- *Verified by:* the fresh-clone test itself (`make install`, `make ci`,
  `pyflow run`, all succeeding from a clone with zero prior state);
  `make ci` clean in the main working tree after every document edit;
  every one of the nine criteria checked against something concrete --
  a passing command, a file on disk, a dated decision already on
  record -- not asserted from memory of earlier sessions.

### CI's last criterion closed: three real bugs, three real fixes, three real verifications (2026-08-19)

A few hours after F3 closed with criterion 8 (CI executing on a real
runner) deliberately open, the maintainer created a GitHub remote and
pushed. This is the record of what closing that criterion actually took
-- worth keeping in full, not just as "done", because the process is the
part worth remembering.

**First push: Windows green, Ubuntu hung.** `.github/workflows/ci.yml`
had never run before this. Windows finished in 2m23s. Ubuntu sat on
"Install software Vulkan driver (Linux)" for 5+ minutes with no sign of
progress.

**First diagnosis, made without log access, wrong.** GitHub's log
download API needs repo-admin auth, which wasn't available. From the
symptom alone, a plausible guess: `needrestart`'s interactive
"which services should be restarted?" prompt, a well-known GitHub
Actions gotcha that `apt-get install -y` doesn't suppress. Fixed with
`NEEDRESTART_MODE=a`/`DEBIAN_FRONTEND=noninteractive`, reported back as
resolved, and merged. **The very next run hung for even longer (8+
minutes) on the same step** -- proof the diagnosis was wrong, not just
incomplete. The maintainer's response, verbatim: "Let's not guess at
things in the future." Saved to memory as a standing rule, not just
applied once.

**Second diagnosis, from a real log the maintainer pasted, correct.**
`apt-get update` itself -- not `install` -- was stuck retrying
`azure.archive.ubuntu.com` (GitHub's Azure-runner regional mirror,
periodically unreachable) four times before falling back to
`archive.ubuntu.com` directly. A documented GitHub Actions gotcha,
unrelated to the package set. Fixed by overwriting
`/etc/apt/apt-mirrors.txt` with the direct archive URL before
`apt-get update` runs. Opened as a fresh PR (the merged branch from the
wrong fix was deleted) rather than pushed straight to `main`, specifically
so the fix could be watched through to a real green run before being
reported as fixed -- the discipline the first attempt skipped.

**That PR's own first run found a second real bug**, this time from the
Vulkan step succeeding for the first time (18s) and `make ci` failing
instead, 25 seconds in -- too fast to have gotten far. The maintainer
pasted that log too, unprompted this time. `Fatal Python error: Aborted`,
a genuine SIGABRT inside `glfwSetFramebufferSizeCallback`, during
`tests/integration/test_interactive_window.py`'s module-level display
probe. `_display_available()` called straight into `GlfwRenderCanvas`
inside `try/except Exception`, assuming a headless machine raises a
catchable exception. `ubuntu-latest` has no `DISPLAY`/`WAYLAND_DISPLAY`
at all, and GLFW's native code aborts the whole process there instead --
a signal no Python `except` clause can intercept. Never reproducible
locally; the dev machine always has a display. Fixed by checking
`DISPLAY`/`WAYLAND_DISPLAY` before `GlfwRenderCanvas` is ever
constructed, restructuring the module's tests to use a per-function
`@_needs_a_real_display` marker instead of a blanket `pytestmark` (so a
new regression test can run precisely where there is *no* display,
which is the case it exists to cover), and adding that regression test:
it monkeypatches `GlfwRenderCanvas` to raise a bare `BaseException` --
standing in for the real SIGABRT without actually crashing the test
runner -- and asserts the guard never reaches it.

**A third real bug, found the same way, one push later.** The display
fix worked (`test_interactive_window.py` went from an instant crash to
`.sss`: one pass, three correctly skipped). `make ci` still failed, this
time in `check-docs-index`: "docs/index.md is stale." Locally impossible
to reproduce -- `check-docs-index` had passed on every local run all
session. Rather than guess at a mechanism, wrote a small script
comparing `sorted()` on bare `Path` objects against an explicit
lowercased-string sort for every `docs/index.md` section, run locally:
one directory differed. `docs/handbook/physics/README.md` is the only
file in any scanned section starting with an uppercase letter --
`Path.__lt__` is case-insensitive on Windows, case-sensitive on POSIX,
so Windows sorts it last (alongside where it alphabetises
case-insensitively) and Ubuntu sorts it first. `check-docs-index` was
correctly catching its own generator being non-deterministic across
platforms, something no amount of Windows-only local verification could
ever have found. Fixed with an explicit `key=lambda p: p.name.lower()`,
chosen to match Windows's existing output exactly so `docs/index.md`
itself needed no changes. Added a regression test reproducing the exact
mixed-case scenario.

**Fourth push: green on both platforms**, watched directly via the
GitHub API rather than assumed from the PR merging, before reporting
anything back. The maintainer merged; the push that merged it (`9c66e25`)
was checked again, independently, both jobs individually `success`.
Criterion 8 closed for real at that point, not before.

**What this actually demonstrates, beyond the three fixes themselves:**
every bug found here was invisible to `make ci` run locally, all
session, right up until a real remote and a real Linux runner existed --
which is the entire reason criterion 8 was written as its own, separate
Stage 0 criterion rather than folded into "engineering tooling is
operational." The first attempt at fixing the Ubuntu hang broke that
discipline (reported fixed without verification, from a guess); every
attempt after it held to watching a real run before saying anything was
resolved, per the maintainer's direct correction.

- *Verified by:* run `9c66e25` on GitHub Actions, checked directly via
  the API -- both `ci (ubuntu-latest)` and `ci (windows-latest)`
  individually `success`, not inferred from the PR merging cleanly;
  `make ci` clean locally after every fix, throughout.
