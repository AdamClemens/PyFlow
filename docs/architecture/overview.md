# Architecture Overview

A single top-level map of PyFlow's system architecture -- what the major
pieces are and how they compose -- for a reader who hasn't yet read
`engine.md`, `icds.md`, or `rendering.md` individually and needs to know
which one to open first.

**Distinct from those documents, not a summary that duplicates them.**
Each of the documents below covers its own piece in depth; this one
covers only how the pieces fit together, and should be read first, not
instead of them.

- `docs/architecture/engine.md` (KA-029) -- the numerical engine's nine
  replaceable layers (mesh through boundary conditions).
- `docs/architecture/icds.md` (KA-030) -- the user/configuration-facing
  contracts for six of those layers.
- `docs/architecture/rendering.md` -- the rendering subsystem as actually
  built (wgpu/pygfx).
- `docs/architecture/repository.md` -- why the repository's top-level
  directories are laid out the way they are (a different kind of
  "architecture" -- organisational, not runtime).

---

## The Whole System, One Level Up

```text
                           ┌─────────────────────┐
                           │ Configuration       │  src/pyflow/configuration/
                           │ (YAML -> dataclass) │  selects implementations,
                           └──────────┬──────────┘  validates, never executes
                                      │ constructs
                                      ▼
            ┌──────────────────────────────────────────────────┐
            │ bootstrap()                                      │   src/pyflow/bootstrap.py
            │ orchestrates configuration + engine + rendering; │   (package root, not inside
            │ owns none of them                                │   any subpackage -- see below)
            └─────┬─────────────────────────────────────┬──────┘
                  │                                     │
                  ▼                                     ▼
┌───────────────────────────────────┐      ┌────────────────────────────────┐
│ Engine + Physics                  │      │ Rendering                      │
│ src/pyflow/{engine,physics}/      │      │ src/pyflow/rendering/          │
│ nine numerical layers (engine.md) │      │ canvas.py + window.py          │
│ Mesh + Variables built (Stage 1-2)│─────▶│ RenderWindow's render loop,    │
│ the rest arrive Stage 3+          │mesh, │ mesh_visualization.py,         │
│ physics/ still empty (Stage 6)    │fields│ field_visualization.py         │
└───────────────────────────────────┘      │ (rendering.md)                 │
                                           └────────────────────────────────┘
```

**The arrow between the bottom two boxes is real, and it points one
way.** `rendering/mesh_visualization.py` imports `engine.mesh`, and
`rendering/field_visualization.py` imports `engine.mesh`,
`engine.scalar_field` and `engine.vector_field` -- rendering turns
engine types into pygfx geometry, so it depends on them. Nothing in
`engine/` imports `rendering/`, and that direction is the one worth
protecting.

**This arrow was deliberately absent until 2026-08-22, and the history
is worth keeping.** An early version drew it, labelled "fields", when no
such path existed; it was removed on 2026-08-18 for asserting in the
picture what the prose denied. TASK-013 (Stage 1) and TASK-017 (Stage 2)
then built the path for real, and the diagram spent a day denying
something true instead -- the same defect, inverted. Redraw this arrow
out only if the dependency actually goes away.

`bootstrap()` is the one module that knows about all three of
configuration, engine, and rendering -- and deliberately lives at the
`pyflow` package root rather than inside any of them, because a module
that orchestrates several subpackages belongs above them, not inside
whichever one its task name happens to suggest
(`src/pyflow/CLAUDE.md`'s circular-import lesson, found the hard way in
D4). It is also PyFlow's actual public API (`bootstrap()`, not `pyflow
run` the CLI, is what golden demos and tests call directly) -- see
`src/pyflow/CLAUDE.md`.

## What Exists Today vs. What's Architected Ahead of Time

This distinction matters enough to state explicitly, since it differs
between the two content documents above:

**This section is dated, because it is the one that rots fastest**
(rewritten 2026-08-22; it had described the Stage 0 repository, which
stopped being true when TASK-011 landed on 2026-08-20).

- **`rendering.md` describes real, implemented code** --
  `src/pyflow/rendering/{canvas,window,mesh_visualization,field_visualization}.py`,
  built and tested (D3-D5, TASK-013, TASK-017).
- **`engine.md` is now half real and half target architecture**, and
  which half is which is stated per layer in that document. Mesh
  (TASK-011/012, Stage 1) and Variables (TASK-014/015/016, Stage 2) are
  built -- their entries read "Implemented in" and name the modules.
  The remaining seven layers read "Arrives via" and are documentation
  only. `src/pyflow/physics/` still holds nothing beyond package
  initialisation and is not due until Stage 6.
- **`icds.md` is still entirely target architecture.** None of its six
  configuration-facing contracts has an interface yet; they arrive in
  Stage 3 (TASK-018..022), and that document marks its `numerics.*`
  keys as proposed rather than implemented.

Configuration (`src/pyflow/configuration/`) sits in between and has
grown with the engine rather than ahead of it: `PyFlowConfig`, YAML
loading and validation are TASK-005's, `MeshConfig` arrived with
TASK-012, `FieldDisplayConfig` with TASK-017, and a generator
(TASK-039) writes a valid file from the schema. The `numerics.*`
section `icds.md` proposes is the part still missing, because the
interfaces it would select among do not exist yet.

## Why This Split

Configuration is deliberately upstream of and independent from both
engine and rendering -- it constructs, and is not itself part of, either
(`adr/ADR-003-modular-numerical-strategies.md`'s "construction versus
execution" principle, applied at the whole-system level here, not just
within the numerical layers `engine.md` covers).

**Engine and rendering are not independent of each other, and the
precise shape of the dependency is what matters** (corrected 2026-08-22;
this section claimed "the render loop has no dependency on numerical
layers today", which stopped being true at TASK-013 and was thoroughly
false by TASK-017):

- **`rendering/` depends on `engine/`, one way.** The two visualisation
  modules import `Mesh`, `ScalarField` and `VectorField` in order to
  turn them into geometry. Nothing in `engine/` imports `rendering/`,
  and nothing should -- that is the direction that would make the engine
  unusable headless.
- **`RenderWindow` itself still depends on nothing numerical.** It
  imports `engine.get_logger` and no more; scene contents are handed to
  it. So `rendering.md`'s "Relation to the Timestep" claim -- nothing
  here computes or schedules a timestep -- holds, and is a different
  claim from "rendering does not depend on the engine", which no longer
  does.
- **Nothing about `engine.md`'s nine layers assumes a specific
  renderer.**

The only place all three genuinely meet is `bootstrap()`, and that is
exactly why it is architecturally separate from all three subpackages it
composes.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E2a), deliberately kept
short -- its only job is orientation and pointing at the right deeper
document, not restating any of them (`docs/documentation-guidelines.md`'s
"prefer links over duplicated information"). If a new top-level
architecture document is added alongside `engine.md`/`icds.md`/
`rendering.md`, add it to the list at the top of this file in the same
change.

Reviewed 2026-08-18: the system diagram was redrawn. Its box borders did
not line up with their contents, and it carried a "fields" arrow from
Engine to Rendering depicting a path that did not exist then -- asserting
in the picture what the "Why This Split" section denied in prose. The
arrow was removed, with a note saying why.

**Reviewed again 2026-08-22, and the arrow is back.** TASK-013 and
TASK-017 built the path; between TASK-017 landing (2026-08-21) and this
review, the diagram denied something true, which is the 2026-08-18
defect inverted rather than a new one. Four further claims in this
document had gone stale the same way -- `engine/` "holds nothing beyond
package initialisation", "nothing exists yet to configure", "the render
loop has no dependency on numerical layers today", and a citation of a
`rendering.md` section titled "What This Does Not Provide" (the actual
heading is "What wgpu/pygfx Does Not Provide", and it is about library
gaps, not dependencies). **This document is the first one a new reader
is told to open, and it described the Stage 0 repository for two
stages.** Re-read it at every stage boundary; it has no generated
content and nothing in `make ci` can tell when it stops being true.
