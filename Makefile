.PHONY: install lint format typecheck test docs demo ci clean

install:
	uv sync
	uv run pre-commit install

lint:
	uv run pre-commit run --all-files

format:
	uv run ruff format .

typecheck:
	uv run mypy src

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
	uv run python -m pyflow
	@echo ""
	@echo "This is the Stage 0 placeholder entry point (TASK-000). The real"
	@echo "bootstrap -- configuration, logging, a rendering window, the"
	@echo "run loop -- is TASK-010 and does not exist yet."

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
