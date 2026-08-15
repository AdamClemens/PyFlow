.PHONY: install lint format typecheck test docs demo clean

install:
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

test:
	uv run pytest

docs:
	@echo "No documentation build is configured yet (see docs/planning/backlog.md)."

demo:
	@echo "No demo entry point exists yet (see docs/planning/roadmap.md)."

clean:
	rm -rf .venv .mypy_cache .ruff_cache .pytest_cache dist build *.egg-info
