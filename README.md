# PyFlow

> A modern, extensible fluid dynamics simulation engine focused on beautiful visualisation, scientific correctness, and maintainable engineering.

---

## Project Status

**Current Version:** 0.0.1 — no release has been made.

PyFlow has completed **Stage 2 (Representing Fields)** and is about to
begin Stage 3 (Numerical Engine). Stage 0 built the engineering
foundations; Stage 1 added the first real engine code -- a
`CoordinateSystem`, a `Mesh` with a structured Cartesian implementation,
and a mesh visualiser you can zoom and pan; Stage 2 added `Field` and
its scalar and vector implementations, plus the rendering that makes
them visible. There is still no *physics*: fields hold values, but
nothing is being simulated and nothing is being transported. See
`docs/planning/roadmap.md` for the per-task status and each stage's
exit audit, and `docs/implementation/golden-demos.md` for what each
stage's demonstration proves.

The project's primary objective is to build a reusable fluid simulation engine while documenting every significant engineering decision along the way.

---

## Vision

PyFlow aims to become a platform for exploring fluid dynamics through interactive simulation.

The project prioritises:

- scientific correctness where practical
- incremental development
- excellent visualisation
- maintainability
- enjoyable engineering

Every stage after Stage 0 produces a working, visible demonstration
(P-004, `docs/engineering-principles.md`). Not necessarily a
*simulation* -- Stage 1's demonstration draws an empty computational
mesh, which is exactly what "the domain is representable" looks like
when nothing is being transported through it yet. This line said
"working simulation" until 2026-08-21, overstating the principle it
was paraphrasing.

---

## Repository Philosophy

The repository is designed to explain itself.

Rather than relying on memory, project knowledge is captured explicitly through documentation, architectural decisions, and generated planning artefacts.

---

## Quick Start

Requires [`uv`](https://docs.astral.sh/uv/) and `make`. PyFlow tracks a
current Python version rather than an old floor -- see `.python-version`
and `docs/practices.md`'s Python version policy; `uv` provisions it
automatically, nothing to install separately.

In a clone of this repository:

```bash
make install   # creates .venv, installs dependencies, installs the git pre-commit hook
```

Then:

```bash
make demo      # opens the render window -- press Escape/Enter or close the window to exit (no simulation yet)
make test      # runs the test suite, with a coverage report
make lint      # formats and lints code and docs (see the Makefile's own comment for exactly what runs)
make ci        # the full sequence CI runs on every push and pull request -- lint, typecheck, test, and the documentation/graph/inventory/manifest checks; see CLAUDE.md for what each one covers
```

To remove everything `make install` set up:

```bash
make clean
```

`make clean` prints what it can't remove and why when it runs -- run it
to see the current, authoritative list rather than trusting a copy of it
here, which could drift.

This section must stay current as functionality is added -- see
`docs/practices.md`.

---

## Where to Start

If you're new to the project, read these documents in order:

1. `CLAUDE.md` — the project's operating rules
2. `docs/glossary.md` — terminology, including what Stage, Capability
   Level and Release each mean here
3. `docs/practices.md` — how work is conducted
4. `docs/planning/capability-map.md` — what PyFlow is meant to be able to do
5. `docs/planning/roadmap.md` — what is being built, and what is done
6. `docs/planning/backlog.md` — what is outstanding and what is undecided

`docs/repository-manifest.md` is the inventory of every maintained
artifact if you want to know what exists before reading any of it.
`docs/index.md` is the full, generated map of every documentation page
grouped by directory, for once you know what you're looking for and just
need to find it.

---

## Current Phase

Stage 3 — Numerical Engine.

Stages 0 through 2 are complete, each closed against its own written
completion criteria (`docs/planning/roadmap.md`):

- Stage 0 — planning system, capability map, repository structure,
  development tooling, CI. Deliberately no CFD functionality.
- Stage 1 — `CoordinateSystem` and `Mesh` interfaces with their first
  concrete implementations, and the Empty Mesh golden demo. Geometry,
  still no physics.
- Stage 2 — the `Field` abstraction and how a physical quantity is
  stored against a mesh (`ScalarField`, `VectorField`), rendered as a
  colour map and arrows, in the Field Display golden demo. Values, but
  nothing yet acting on them.

Stage 3 adds the numerical operator interfaces that will act on those
fields. Physics itself arrives from Stage 4.

Try the most recent demonstration:

```bash
uv run python -m pyflow run --config examples/golden-demos/field_display.yaml
```

---

## Roadmap

The project progresses through incremental stages
(`docs/planning/roadmap.md`), against a longer-range view of capability
levels (`docs/planning/implementation-plan.md`).

Each stage after Stage 0 must include:

- working software
- visible demonstrations
- updated documentation
- completed Definition of Done

---

## License

[BSD 3-Clause](LICENSE)
