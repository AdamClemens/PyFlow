# CLAUDE

Architecture documentation. `overview.md`, `rendering.md`, `repository.md`
have no basis in `docs/planning/knowledge-architecture.md` -- not
redundant, just not itemised there; KA doesn't have to enumerate every
architecture doc the project ends up wanting. All three were written
2026-08-17 (`docs/planning/backlog.md` E2a/E2b/E2c):

- `overview.md` -- the single top-level system map (configuration ->
  bootstrap() -> engine/physics + rendering), pointing at `engine.md`/
  `icds.md`/`rendering.md` for depth rather than duplicating them.
- `rendering.md` -- the architecture of the renderer actually adopted
  (wgpu/pygfx, `adr/ADR-005`), grounded in the real, already-implemented
  `src/pyflow/rendering/{canvas,window,mesh_visualization,field_visualization}.py`
  -- unlike `engine.md`/`icds.md` below, this describes code that
  exists, not target architecture. (The last two modules arrived with
  TASK-013 and TASK-017; this list named only `canvas`/`window` until
  2026-08-22.)
- `repository.md` -- why the repository's top-level directories are
  shaped the way they are, distinct from `docs/repository-manifest.md`
  (per-file completion status, not structural rationale).

`icds.md` (KA-030, Interface Contract Definitions -- the
user/configuration-facing interfaces PyFlow's components expose, *not*
every internal Python interface) and `engine.md` (KA-029, conceptual
engine architecture: mesh/variables/flux/advection/diffusion/time-
integration/pressure-velocity-coupling/linear-solvers/boundary-conditions
as replaceable layers behind contracts) were scaffolded (structure only)
2026-08-15 and **written 2026-08-17** (`docs/planning/backlog.md`
E1a/E1b), both per KA. `engine.md` is not the same document as
`overview.md` -- resolved as two separate files, not one renamed.

Both were written as target architecture for Stage 1-4 layers that did
not exist as code -- `engine.md`'s own "Arrives via" note per layer, and
`icds.md`'s `numerics.*` configuration keys, are explicitly marked
proposed/not-yet-implemented rather than described as current fact.

**Two of those layers are now real** (2026-08-22): Mesh (Stage 1) and
Variables (Stage 2), whose `engine.md` entries have been converted from
"Arrives via" to "Implemented in", with the modules that implement them
named. Forward-looking framing is correct for the remaining layers and
wrong for those two, so **check which half of this document you are in
before trusting a tense.** `engine.md`'s own Maintenance section carries
the rule -- "'Arrives via' should read as 'implemented in' once true" --
and the Stage 2 exit audit found it had gone a day unapplied to
Variables, which is exactly how long it takes for a reader to be
misled.
`icds.md` covers only the six components `adr/ADR-003` names as
independently configuration-selected (advection, diffusion, time
integrator, pressure-velocity coupling, linear solver, boundary
condition) -- Mesh and Variables are `engine.md` layers but not yet ICDs,
since each currently has exactly one implementation with nothing to
choose between.

`compute-and-rendering-stack.md` (added 2026-08-15) is not empty --
survey and compatibility matrix for the array-library/renderer decision,
with live-verified findings on top of a May-2026 knowledge snapshot.
**Both questions it exists to support are decided**: the class (A2b) as
`adr/ADR-004-compute-rendering-class.md`, and the instances (A2c,
PyTorch + wgpu/pygfx) as `adr/ADR-005-compute-rendering-instances.md`,
both 2026-08-15. It is now the record of *why* those decisions went the
way they did and what was not chosen -- not an open question. Extend it
with new findings or re-verification; revisiting either decision is a new
ADR, per the root `CLAUDE.md`. Read its own status banner, which says the
same thing, before assuming anything in it is still open.

This sentence previously read "it remains the live reference for A2c's
instance-level choice," and `docs/repository-manifest.md` said A2c was
"not yet decided" -- both stale from the day they were written, since
`ADR-005` landed the same day, and both corrected 2026-08-18. When a
document is decision *support*, say which decisions it has already fed;
that phrasing does not go stale the way "still open" does.

**Reviewed 2026-08-18** (maintainer's request, alongside the Handbook).
All five documents here changed; each one's Maintenance section records
what. Two patterns are worth knowing before editing anything in this
directory:

- **These documents were written before the Handbook and are now
  downstream of it.** `icds.md` recorded scheme behaviour ("first-order
  upwind is unconditionally stable") that
  `docs/handbook/numerical-methods/` later contradicted, and `engine.md`
  still described the handbook as unwritten a day after it was written.
  When a Handbook entry and an architecture document disagree about the
  domain, the Handbook is authoritative and this directory should point at
  it rather than restate it; when they disagree about PyFlow's own
  architecture, this directory is.
- **A diagram makes claims too, and it can be wrong in either
  direction.** In 2026-08-18 `overview.md`'s system diagram drew a data
  path between Engine and Rendering that the same document's prose
  denied existed; the arrow was removed. By 2026-08-21 TASK-013 and
  TASK-017 had built that path for real, and the diagram spent a day
  denying something true -- **the identical defect, inverted**, found by
  the 2026-08-22 consistency sweep and fixed by putting the arrow back.
  Check a diagram against the text beside it whenever either changes,
  and against the *code* at a stage boundary: a picture is not exempt
  from the tense discipline (`docs/practices.md`, "write prospective
  language as retrospective the moment it's true", and its converse) the
  prose is held to, and removing a claim is as much an assertion as
  making one.

`rendering.md`'s header also claimed KA §11 covered it and pointed at
`engine.md` for an explanation that was never there; the explanation is
in this file, above. If a future architecture document again has no KA
entry, record that here and have the document point here.
