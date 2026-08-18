# CLAUDE.md

This file contains the global operating rules for contributors to the PyFlow repository.

These instructions apply to both human contributors and automated agents unless a more specific `CLAUDE.md` exists within a subdirectory.

Lower-level `CLAUDE.md` files may extend these rules but should not contradict them.

---

# Mission

Build a maintainable, understandable and enjoyable fluid dynamics simulation engine.

The repository should preserve project knowledge so that progress never depends on any individual's memory.

---

# Core Responsibilities

Contributors should:

- improve the repository
- preserve project knowledge
- leave the repository easier to understand than they found it
- follow the engineering principles
- follow the documentation guidelines
- record significant architectural decisions
- avoid unnecessary complexity
- keep `CLAUDE.md` files current as understanding grows (see "Maintaining
  CLAUDE.md Files" below)

---

# Integrity

Lying is never an option. Not to save time, not to smooth over an
inconsistency, not to avoid an awkward admission.

Report uncertainty, mistakes and bad news plainly and as soon as they are
known. A wrong answer that is honestly labelled uncertain is recoverable;
a confident fabrication is not, and the institutional-memory philosophy
this repository is built on assumes what is written down is true.

This is what "say so explicitly" means everywhere else in this file --
the Blast Radius rule and the Validation section below both ask for the
same honesty, in narrower situations. This section is the general
statement they follow from.

Added 2026-08-15, maintainer's instruction.

---

# Planning Philosophy

The planning system exists to accelerate PyFlow.

Avoid spending time improving the planning system unless it directly benefits development of PyFlow.

---

# Maintaining CLAUDE.md Files

`CLAUDE.md` files are living documents, not one-time scaffolding.

Whenever work in a directory surfaces something a future contributor
(human or agent) would need to know -- a convention, a decision, a purpose
that wasn't obvious, a pitfall hit and resolved -- amend the nearest
`CLAUDE.md` with that knowledge before moving on. Do not wait for a
directory's content to be "finished" first; update incrementally, as
understanding accumulates.

A generic placeholder (e.g. "This directory contains project files. Follow
the repository conventions...") is acceptable only until something specific
is known about that directory. Replace it as soon as that changes.

---

# Blast Radius

Before making a change, work out what else it affects -- what references
it, restates it, tracks it in an inventory, or was decided because of it
-- and update all of it in the same change.

Searching for the name of the thing you are changing is usually enough to
find the radius.

If something in the radius cannot be updated now, say so explicitly where
the divergence is. A recorded inconsistency is a known problem; an
unrecorded one is a trap.

Full rule, with the specific cases most often missed: `docs/practices.md`.

---

# Session Handoff

The repository must always be left in a state internally consistent
enough that a fresh agent, with no memory of this session, could pick up
the next piece of work and trust what the documents say.

At the end of a session that touched multiple documents, or spanned
several rounds of work, verify this is actually true rather than
assuming it -- re-check status tables, counts and cross-references
against the current state directly, the same way a fresh agent would.
Where this finds a gap, add a rule that would have prevented it, not
just a one-off fix.

Checklist, with the specific things most often missed: `docs/practices.md`.

---

# Development Commands

Every command below is a `Makefile` target; run `make <target>` from the
repository root. Do not reverse-engineer the `Makefile` or reach for
tool-specific commands (`pytest`, `ruff` directly, etc.) when the
equivalent target already exists here -- that is exactly the drift
`ci: lint typecheck test check-docs check-docs-index` (below) exists to
prevent (P-011, single authoritative source).

- `make install` -- set up the development environment (`uv sync` plus
  the git pre-commit hook). Start here on a fresh clone.
- `make lint` -- run `pre-commit` across the repository (formatting and
  linting, code and docs).
- `make typecheck` -- `mypy --strict` over `src` and `tests`.
- `make test` -- run the test suite with coverage.
- `make check-docs` -- fail if any relative Markdown link is broken.
- `make check-docs-index` -- fail if `docs/index.md` doesn't match what
  the current doc tree would generate.
- `make docs` -- regenerate `docs/index.md`. Run this, not a manual
  edit, after adding, moving, deleting, or re-titling a documentation
  page -- see `docs/CLAUDE.md`.
- `make check-claims` -- report documentation claiming some file or
  directory is empty, unwritten, or a stub when it actually has content
  (`docs/practices.md`). **Advisory and deliberately outside `make ci`**:
  it exits 0 even with findings, because telling a real drift from a
  document legitimately quoting the rule needs judgement. Run it as part
  of the end-of-session consistency review, not on every commit.
- `make ci` -- `lint typecheck test check-docs check-docs-index`
  together; this is what CI actually runs (`.github/workflows/ci.yml`),
  so it is also the one command that verifies a change is ready before
  committing. **For documentation it verifies structure, not content**
  (stated 2026-08-18): `check-docs` checks that relative links resolve,
  `check-docs-index` that the generated index matches the doc tree, and
  the `pre-commit` hooks cover whitespace, YAML syntax, spelling
  (`codespell`) and line endings (`mixed-line-ending`, which catches the
  stray control characters a mangled escape leaves behind). Beyond
  spelling, nothing in the chain reads the *meaning* of a Markdown file.
  A wrong
  equation, an inverted sign, a citation whose target does not support
  it, or a status claim that went stale weeks ago all pass `make ci`
  cleanly -- every error the 2026-08-18 documentation review found had
  been passing it for days, and a mangled LaTeX escape introduced during
  that review passed it too. Run it always; for prose, treat it as a
  floor rather than a verification. The Blast Radius rule and the
  end-of-session consistency review (`docs/practices.md`) are what
  actually catch content errors, and both need a person or an agent
  reading.
- `make demo` -- run `python -m pyflow run`, the interactive engine
  entry point.
- `make clean` -- remove what `make install` created; states on its own
  output what it deliberately leaves alone (the `uv` binary, the shared
  interpreter, `uv`'s package cache) rather than restated here.

Full detail, including what each target's acceptance criteria are and
why the project settled on `uv`+`make`: `README.md`'s Quick Start
section and `docs/planning/backlog.md` A1a/A1b/B2/B3.

---

# Documentation

Documentation is treated as part of the implementation.

Documentation should evolve alongside code.

Generated documentation must never be edited manually.

Follow `docs/documentation-guidelines.md`.

---

# Engineering Principles

Follow the principles defined in:

`docs/engineering-principles.md`

---

# Architectural Decisions

Significant architectural decisions should be recorded as ADRs.

Do not silently change established architecture.

---

# Validation

If you believe the repository violates one of these principles:

- report the issue
- explain why
- propose a solution
- do not silently ignore it

---

# Local Instructions

Always consult any more specific `CLAUDE.md` files in subdirectories before making changes.

Local instructions take precedence where they extend these rules.

When unsure, prefer improving the project's understanding over increasing the project's complexity.
