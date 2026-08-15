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
