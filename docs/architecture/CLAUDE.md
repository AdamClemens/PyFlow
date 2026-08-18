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
  `src/pyflow/rendering/{canvas,window}.py` -- unlike `engine.md`/
  `icds.md` below, this describes code that exists, not target
  architecture.
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

Both describe target architecture for Stage 1-4 layers that don't exist
as code yet -- `engine.md`'s own "Arrives via" note per layer, and
`icds.md`'s `numerics.*` configuration keys, are explicitly marked
proposed/not-yet-implemented rather than described as current fact.
`icds.md` covers only the six components `adr/ADR-003` names as
independently configuration-selected (advection, diffusion, time
integrator, pressure-velocity coupling, linear solver, boundary
condition) -- Mesh and Variables are `engine.md` layers but not yet ICDs,
since each currently has exactly one implementation with nothing to
choose between.

`compute-and-rendering-stack.md` (added 2026-08-15) is not empty --
survey and compatibility matrix for the array-library/renderer decision,
with live-verified findings on top of a May-2026 knowledge snapshot. The
class-level question it existed to inform is decided
(`adr/ADR-004-compute-rendering-class.md`); it remains the live reference
for A2c's instance-level choice (`docs/planning/backlog.md`). Read its
own status banner before assuming anything in it is still open.

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
- **A diagram makes claims too.** `overview.md`'s system diagram drew a
  data path between Engine and Rendering that the same document's prose
  explicitly denies exists yet. Check a diagram against the text beside it
  when either changes -- a picture is not exempt from the tense
  discipline (`docs/practices.md`, "write prospective language as
  retrospective the moment it's true", and its converse) the prose is held
  to.

`rendering.md`'s header also claimed KA §11 covered it and pointed at
`engine.md` for an explanation that was never there; the explanation is
in this file, above. If a future architecture document again has no KA
entry, record that here and have the document point here.
