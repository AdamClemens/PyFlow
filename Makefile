.PHONY: install lint format typecheck test check-docs check-docs-index check-claims docs demo ci clean

install:
	uv sync
	uv run pre-commit install

# Runs every pre-commit hook in .pre-commit-config.yaml, repo-wide,
# covering format + lint + typecheck for every folder containing Python
# code (src/, tests/, and anywhere else Python code lives, since
# --all-files applies to the whole repository, not just src/):
#   trailing-whitespace     -- pre-commit/pre-commit-hooks
#   end-of-file-fixer       -- pre-commit/pre-commit-hooks
#   check-yaml              -- pre-commit/pre-commit-hooks
#   check-added-large-files -- pre-commit/pre-commit-hooks
#   mixed-line-ending       -- pre-commit/pre-commit-hooks (--fix=no)
#   codespell               -- codespell-project/codespell
#   ruff (lint, --fix)      -- astral-sh/ruff-pre-commit
#   ruff-format             -- astral-sh/ruff-pre-commit
#   mypy (--strict)         -- pre-commit/mirrors-mypy
# KEEP THIS LIST IN SYNC WITH .pre-commit-config.yaml -- if a hook is
# added, removed or reordered there, update this comment in the same
# change (see the Blast Radius rule, docs/practices.md).
lint:
	uv run pre-commit run --all-files

format:
	uv run ruff format .

# Narrower than `lint` (no pre-commit, no docs/YAML/whitespace checks) --
# useful for a fast standalone check, but `lint` is the comprehensive one.
# Covers every folder with Python code, not just src/. `examples/` was
# added here briefly (2026-08-16, D5) and removed again the same day:
# golden demos must run via the public API/CLI with their configuration
# in a plain file, not demo-specific Python
# (docs/implementation/golden-demos.md) -- so examples/ is expected to
# hold config files, not .py files, going forward. mypy errors outright
# on a directory with zero Python files, which is exactly what caught
# this. Extend this list again if some future folder starts holding real
# Python.
#
# `.claude/hooks` added 2026-08-21: it held Python that nothing in
# `make ci` had ever looked at, and a broken hook there reports nothing
# when it fails, so it is the worst possible place for an unchecked
# script (see .claude/hooks/CLAUDE.md). ruff (via `lint`) did already
# reach it -- verified, not assumed -- but neither ruff nor mypy could
# have caught what was actually wrong there, since both read the file
# with the project's *own* target version and it was valid under that.
# `tests/integration/test_claude_hooks.py` is what covers that gap.
typecheck:
	uv run mypy src tests .claude/hooks

test:
	uv run pytest

# Broken relative Markdown links (tools/validators/CLAUDE.md). Mechanizes
# one specific instance of the Blast Radius "grep for the thing's name"
# check (docs/practices.md) -- not a substitute for the rest of it.
check-docs:
	uv run python tools/validators/check_docs.py

# Fails if docs/index.md doesn't match what the current doc tree would
# generate -- catches a doc page added, removed, renamed, or re-titled
# without regenerating the index (tools/generators/CLAUDE.md). Part of
# `make ci` so that drift can't merge silently.
check-docs-index:
	uv run python tools/generators/generate_docs_index.py --check

# What CI (docs/planning/roadmap.md TASK-004) runs. Kept here rather than
# duplicated in the CI workflow definition, per P-011 (single
# authoritative source) -- the workflow should invoke this target, not
# restate the command sequence.
ci: lint typecheck test check-docs check-docs-index

# Advisory, and deliberately NOT part of `ci`. Reports documentation that
# claims some file or directory is empty/unwritten/a stub when it actually
# has content (docs/practices.md, "Completeness claims belong only in the
# two documents that track completeness"). It exits 0 even with findings,
# because distinguishing a real drift from a document legitimately quoting
# the rule needs judgement -- see tools/validators/CLAUDE.md for the one
# known false positive. Run it as step 10 of the end-of-session
# consistency review, not on every commit.
check-claims:
	uv run python tools/validators/check_claims.py

# Regenerates docs/index.md, the navigable map of every documentation
# page (tools/generators/CLAUDE.md). Not a hand-maintained file -- see
# root CLAUDE.md's "Generated documentation must never be edited
# manually" rule. Run this after adding, moving, deleting, or
# re-titling (changing the first `#` heading of) any page under
# docs/, docs/planning/, docs/architecture/, docs/handbook/{physics,
# numerical-methods}/, docs/implementation/, docs/references/,
# docs/tutorials/, or adr/.
docs:
	uv run python tools/generators/generate_docs_index.py

demo:
	uv run python -m pyflow run

clean:
	@echo "Removing local build/tool caches and the virtual environment..."
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage dist build *.egg-info
	@if [ -d .venv ]; then \
		uv run pre-commit uninstall 2>/dev/null || true; \
	fi
	rm -rf .venv
	@echo ""
	@echo "NOT removed by this target, and why:"
	@echo "  - uv itself -- installed at the user/system level, not by 'make install'."
	@echo "  - the Python interpreter uv downloaded -- shared across other uv"
	@echo "    projects on this machine; removing it here could break them."
	@echo "    Run 'uv python uninstall <version>' yourself if you want it gone."
	@echo "  - uv's global package cache -- shared across projects."
	@echo "    Run 'uv cache clean' yourself if you want it gone."
