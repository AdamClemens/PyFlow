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
- `docs/architecture/sequences.md` -- the time-ordered runtime sequences
  (setup, timestep loop, data flow, rendering) that this document and the
  ones above do not cover: they describe the pieces and why each is
  shaped the way it is, not the order things happen in.

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
│ physics/ real as of Stage 6       │fields│ field_visualization.py         │
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
- **`engine.md` is part real and part target architecture**, and which
  part is which is stated per layer in that document -- by the module
  paths each layer's `Implementation:` line names, not by its tense
  (`docs/practices.md`, "Let a checked artifact carry status, not a
  tense"). Read it there rather than trusting a count restated here,
  which is how this bullet came to claim seven layers were unbuilt when
  only Flux was. `src/pyflow/physics/` held nothing beyond package
  initialisation through Stage 5; `buoyancy.py` (TASK-035, Stage 6,
  2026-08-30) is its first real module.
- **`icds.md` describes six implemented configuration contracts.**
  Stage 3 (TASK-018..022, done 2026-08-23) gave all six an interface
  and a real `numerics.*` configuration section; that document's
  per-contract "Configuration control" lines name the keys and say
  which stage implemented them. Stage 4 (TASK-040, TASK-023..030, done
  2026-08-28) put a real concrete scheme behind every one of the six --
  `FirstOrderUpwindAdvection`, `CentralDifferenceDiffusion`,
  `RK4Integrator`, `ConjugateGradientSolver`, `PISO`, and
  `DirichletBoundaryCondition`/`NeumannBoundaryCondition` -- and
  `assembly.py` holds zero reference implementations as a result. This
  bullet read "No concrete numerical *scheme* exists behind any of them
  yet -- that is Stage 4" until the 2026-08-28 Stage 4 exit audit, which
  is the **second** time this file has gone stale about a stage that
  had already closed (see the bullet above, and `docs/practices.md`, "A
  stage's documentation sweep is a grep, not a diff review").

Configuration (`src/pyflow/configuration/`) sits in between and has
grown with the engine rather than ahead of it: `PyFlowConfig`, YAML
loading and validation are TASK-005's, `MeshConfig` arrived with
TASK-012, `FieldDisplayConfig` with TASK-017, and a generator
(TASK-039) writes a valid file from the schema, and the `numerics.*`
section arrived across Stage 3 alongside the interfaces it selects among
(`NumericsConfig`, TASK-018..022) -- with `simulation.*`
(`SimulationConfig`, TASK-030) the most recent addition, the first
section to drive a live stepping run rather than a single rendered
frame. This sentence read "the part still missing, because the
interfaces it would select among do not exist yet" until the 2026-08-28
Stage 4 exit audit, while the bullet immediately above it already said
those six interfaces existed -- one file contradicting itself three
lines apart, which is what a status claim restated in prose costs.

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

The only place configuration, engine and rendering genuinely meet is
`bootstrap()`, and that is exactly why it is architecturally separate
from the subpackages it composes.

**That is now four subpackages, not three** -- `physics/` joined them in
Stage 6 (TASK-035, 2026-08-30), and `bootstrap()` is the only module
allowed to import a concrete phenomenon *and* the numerics registry it
registers into, since `engine/` must stay "independent of any specific
physics" (`src/pyflow/engine/CLAUDE.md`). This paragraph said "all three
subpackages it composes" until 2026-08-31, when the Stage 6 exit audit's
count grep reached it; the three-way argument above is unaffected, since
`physics/` sits on the engine side of it.

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
