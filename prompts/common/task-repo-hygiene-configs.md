# Task: Repo Hygiene Config Files

Generated from TEMPLATE.md. Backlog reference: docs/planning/backlog.md §2.

---

## Context

PyFlow is a maintainable, understandable fluid dynamics simulation engine
built in Python. The repository preserves project knowledge so progress
never depends on any individual's memory (root CLAUDE.md).

Root CLAUDE.md (verbatim):
> Contributors should: improve the repository; preserve project knowledge;
> leave the repository easier to understand than they found it; follow the
> engineering principles; follow the documentation guidelines; record
> significant architectural decisions; avoid unnecessary complexity.
> When unsure, prefer improving the project's understanding over increasing
> the project's complexity.

No more specific CLAUDE.md governs the repository root itself.

Known project facts (from docs/planning/roadmap.md TASK-001, already decided
-- do not re-derive or second-guess these):
- Python 3.12
- uv for dependency management
- Ruff + Ruff Formatter for lint/format
- MyPy for static typing
- PyTest for testing
- pre-commit for hook automation

## Task

Target files: `.gitignore`, `.editorconfig`, `.gitattributes` (repo root,
all currently empty)

Purpose: standard repo hygiene so contributors and agents get consistent
line endings, editor behaviour, and don't accidentally commit build
artifacts or caches.

Scope:
- `.gitignore`: Python artifacts (`__pycache__/`, `*.pyc`, `.venv/`,
  `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `dist/`, `build/`,
  `*.egg-info/`), uv-specific artifacts, common OS/editor cruft
  (`.DS_Store`, `Thumbs.db`), and IDE folders if not otherwise tracked.
- `.editorconfig`: UTF-8, LF line endings, final newline, trim trailing
  whitespace, 4-space indent for `.py`, 2-space for `.yaml`/`.yml`/`.json`,
  reasonable default for `.md`.
- `.gitattributes`: normalize line endings (`* text=auto eol=lf`) — this
  repo currently has a CRLF/LF mix (e.g. `docs/CHANGELOG-DESIGN.md`,
  `adr/README.md` are CRLF) that this should prevent going forward. Do not
  rewrite the line endings of existing files as part of this task — that's
  a separate, larger change.
- Do NOT invent dependencies, tools, or conventions not already decided
  above or elsewhere in the repo.

Depends on: none

References: docs/planning/roadmap.md (TASK-001, for the tool stack above)

## Constraints

(as TEMPLATE.md)

## Definition of Done

- [ ] `.gitignore`, `.editorconfig`, `.gitattributes` are non-empty and valid
- [ ] Nothing in them contradicts the tool stack already decided in
      TASK-001 (no assuming poetry/pipenv/conda, no assuming black instead
      of Ruff, etc.)
- [ ] Root `CLAUDE.md` is NOT modified (these are generic config files, no
      new maintenance guidance needed beyond what already exists)
- [ ] docs/planning/backlog.md §2 items for these three files checked off

## Output

`.gitignore`, `.editorconfig`, `.gitattributes` at repo root.
