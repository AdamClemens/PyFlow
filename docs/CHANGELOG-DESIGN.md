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
