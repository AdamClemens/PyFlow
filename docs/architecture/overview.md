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
                    │  Configuration       │   src/pyflow/configuration/
                    │  (YAML -> dataclass) │   selects implementations,
                    └──────────┬───────────┘   validates, never executes
                               │
                               │  constructs
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                        bootstrap()                               │  src/pyflow/bootstrap.py
│   orchestrates configuration + engine + rendering; owns none of  │  (package root, not inside
│   them -- see src/pyflow/CLAUDE.md's circular-import lesson      │  any subpackage -- see below)
└───────────┬───────────────────────────────────┬──────────────────┘
            │                                   │
            ▼                                   ▼
┌───────────────────────┐          ┌─────────────────────────────┐
│  Engine + Physics       │          │  Rendering                  │
│  src/pyflow/{engine,    │  fields  │  src/pyflow/rendering/       │
│  physics}/               │ ───────▶ │  canvas.py + window.py       │
│  nine numerical layers  │          │  RenderWindow's render loop  │
│  (engine.md), all       │          │  (rendering.md); presentation│
│  Stage 1+, not built    │          │  only, no numerics           │
└───────────────────────┘          └─────────────────────────────┘
```

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

- **`rendering.md` describes real, implemented code** --
  `src/pyflow/rendering/{canvas,window}.py`, built and tested (D3-D5).
- **`engine.md` and `icds.md` describe target architecture** -- the nine
  numerical layers, and the six configuration-facing contracts among
  them, exist as documentation only; `src/pyflow/engine/` and
  `src/pyflow/physics/` currently hold nothing beyond package
  initialisation (`docs/planning/roadmap.md` TASK-000). Both documents
  say so themselves, with an "Arrives via"/roadmap-task note per
  concept, precisely so a reader doesn't mistake the plan for the
  current state.

Configuration (`src/pyflow/configuration/`) sits in between: the
*mechanism* is real and tested (`PyFlowConfig`, YAML loading, validation
-- TASK-005), but the specific fields the numerical engine will need
(`icds.md`'s proposed `numerics.*` keys) are not yet added, because
nothing exists yet to configure.

## Why This Split

Configuration is deliberately upstream of and independent from both
engine and rendering -- it constructs, and is not itself part of, either
(`adr/ADR-003-modular-numerical-strategies.md`'s "construction versus
execution" principle, applied at the whole-system level here, not just
within the numerical layers `engine.md` covers). Engine and rendering are
deliberately independent of *each other* at this altitude: the render
loop has no dependency on numerical layers today (`rendering.md`'s "What
This Does Not Provide"/"Relation to the Timestep" sections), and nothing
about `engine.md`'s nine layers assumes a specific renderer. The only
place all three genuinely meet is `bootstrap()`, and that is exactly why
it is architecturally separate from all three subpackages it composes.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E2a), deliberately kept
short -- its only job is orientation and pointing at the right deeper
document, not restating any of them (`docs/documentation-guidelines.md`'s
"prefer links over duplicated information"). If a new top-level
architecture document is added alongside `engine.md`/`icds.md`/
`rendering.md`, add it to the list at the top of this file in the same
change.
