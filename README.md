# PyFlow

> A modern, extensible fluid dynamics simulation engine focused on beautiful visualisation, scientific correctness, and maintainable engineering.

---

## Project Status

**Current Version:** 0.0.1 — no release has been made.

PyFlow is in Stage 0 (Engineering Infrastructure): the engineering
foundations, not yet any CFD functionality. The package skeleton exists
and the development tooling works end-to-end (see Quick Start below),
but no simulation code has been written. See `docs/planning/roadmap.md`
for the per-task status.

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

Every stage after Stage 0 will produce a working simulation with a visible demonstration.

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
make demo      # runs the current entry point (Stage 0 placeholder -- no simulation yet)
make test      # runs the test suite, with a coverage report
make lint      # formats and lints code and docs (see the Makefile's own comment for exactly what runs)
make ci        # lint + typecheck + test -- the same sequence CI runs, on every push and pull request
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

---

## Current Phase

Stage 0 — Engineering Infrastructure.

Building the engineering foundations:

- planning system
- capability map
- repository structure
- development tooling

Stage 0 deliberately contains no CFD functionality.

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
