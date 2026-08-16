.PHONY: install lint format typecheck test docs demo ci clean

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
typecheck:
	uv run mypy src tests

test:
	uv run pytest

# What CI (docs/planning/roadmap.md TASK-004) runs. Kept here rather than
# duplicated in the CI workflow definition, per P-011 (single
# authoritative source) -- the workflow should invoke this target, not
# restate the command sequence.
ci: lint typecheck test

docs:
	@echo "No documentation build is configured yet (see docs/planning/backlog.md)."

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
