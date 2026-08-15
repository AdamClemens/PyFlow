# Task: Pre-commit Configuration

Generated from TEMPLATE.md. Backlog reference: docs/planning/backlog.md §2.

---

## Context

(Same root CLAUDE.md excerpt as task-repo-hygiene-configs.md.)

Known project facts (from docs/planning/roadmap.md TASK-001, already decided):
- Python 3.12, managed via uv
- Ruff for linting, Ruff Formatter for formatting
- MyPy for static typing
- PyTest for testing
- `.pre-commit-config.yaml` is explicitly listed as a TASK-001 artifact

TASK-001's acceptance criteria: a clean clone can run `make install` then
`make test` with no manual configuration. This task only covers the
pre-commit config itself, not the Makefile (that's TASK-002 / a separate,
not-yet-unblocked item — `src/pyflow` has no code yet, so hooks will have
nothing to lint/typecheck until then. That's expected; configure the hooks
correctly regardless).

## Task

Target file: `.pre-commit-config.yaml` (repo root, currently empty)

Purpose: automate formatting/linting/type-checking before commit, per
TASK-001.

Scope:
- Ruff hook (lint, with `--fix`)
- Ruff Formatter hook
- MyPy hook
- Standard `pre-commit-hooks` repo: trailing-whitespace, end-of-file-fixer,
  check-yaml, check-added-large-files
- Do NOT add hooks for tools not already decided (no flake8, no black, no
  isort — Ruff supersedes these)
- Pin hook versions to recent stable releases; note in a comment that
  versions should be bumped periodically

Depends on: none for the config file itself, but note in your output that
this hasn't been runnable end-to-end yet since `pyproject.toml` (which
would normally hold Ruff/MyPy tool config sections) doesn't exist yet.
Flag this rather than silently also writing `pyproject.toml` — that's a
separate backlog item blocked on TASK-000 (engine skeleton) existing first.

References: docs/planning/roadmap.md (TASK-001)

## Constraints

(as TEMPLATE.md)

## Definition of Done

- [ ] `.pre-commit-config.yaml` is valid YAML and installable via
      `pre-commit install`
- [ ] Only the tools already decided in TASK-001 are referenced
- [ ] A comment or note flags that this hasn't been exercised against real
      source yet (no `src/pyflow` code exists), so it should be re-verified
      once TASK-000 lands
- [ ] docs/planning/backlog.md §2 item for `.pre-commit-config.yaml` checked off

## Output

`.pre-commit-config.yaml` at repo root.
