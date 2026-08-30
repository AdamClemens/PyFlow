.PHONY: install lint format typecheck test check-docs check-docs-index check-graph \
        dependency-tree check-dependency-tree inventory check-inventory \
        check-manifest check-references check-scenarios check-claims status-report \
        check-status config-template check-config-template docs demo ci clean

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

# `-n auto` (pytest-xdist, added 2026-08-30): runs the suite across all
# available cores. No test's own content changes -- see pyproject.toml's
# own dev-dependency comment for the profiling behind this and what it
# does and doesn't fix.
test:
	uv run pytest -n auto

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

# Fails if planning/data/*.yaml is structurally inconsistent with
# planning/model/*.yaml -- a dangling edge, an undeclared relationship
# type, a reference to a file that doesn't exist, a dependency cycle
# (tools/validators/CLAUDE.md, adr/ADR-006-knowledge-graph-scope.md).
# Unlike check-claims this one GATES: every rule is a definite
# structural fact needing no judgement, which is the only reason
# check-claims had to stay advisory.
check-graph:
	uv run python tools/validators/check_graph.py

# Regenerates docs/planning/dependency-tree.md from the component graph.
# That document was hand-maintained until 2026-08-21 and disagreed with
# docs/architecture/engine.md about what the engine's subsystems are;
# it is now a view of planning/data/components.yaml, so the two cannot
# diverge again. Never hand-edit the output -- root CLAUDE.md's
# generated-documentation rule applies to it exactly as to docs/index.md.
dependency-tree:
	uv run python tools/generators/generate_dependency_tree.py

# Fails if the committed dependency-tree.md doesn't match what the
# current graph would generate. Part of `make ci`, same as
# check-docs-index, so drift can't merge silently.
check-dependency-tree:
	uv run python tools/generators/generate_dependency_tree.py --check

# What CI (docs/planning/roadmap.md TASK-004) runs. Kept here rather than
# duplicated in the CI workflow definition, per P-011 (single
# authoritative source) -- the workflow should invoke this target, not
# restate the command sequence.
# Regenerates docs/repository-inventory.md -- every tracked file, by
# directory, with empty files marked -- from `git ls-files`. The factual
# half of docs/repository-manifest.md, split out 2026-08-21 because a
# hand-restated file inventory goes stale (that document spent five days
# describing src/ as "docstring-only, no implementation" against 1,470
# lines of code). Never hand-edit the output.
inventory:
	uv run python tools/generators/generate_repository_inventory.py

# Fails if the committed inventory doesn't match what git tracks.
check-inventory:
	uv run python tools/generators/generate_repository_inventory.py --check

# Fails if any tracked file is neither named in
# docs/repository-manifest.md nor covered by one of the collective rules
# declared in that document. Deliberately does NOT check the reverse --
# recording what was retired is part of the manifest's job; see
# tools/validators/check_manifest.py for why that rule was removed.
check-manifest:
	uv run python tools/validators/check_manifest.py

ci: lint typecheck test check-docs check-docs-index check-graph check-dependency-tree check-inventory check-manifest check-references check-scenarios check-status check-config-template

# Fails if prose names a repository path that does not exist. Gating:
# every rule is a definite structural fact (does this path resolve),
# with the judgement-shaped cases excluded by document rather than by a
# growing exemption list -- see tools/validators/CLAUDE.md.
check-references:
	uv run python tools/validators/check_references.py

# Fails if a Gherkin scenario exists but nothing binds it, so it never
# runs while reading like a criterion that passes. Gating for the same
# reason: "is this scenario executed" is a fact, not a judgement.
check-scenarios:
	uv run python tools/validators/check_scenarios.py

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

# Regenerates docs/planning/status.md (a visual project status report,
# task/stage tables plus a Mermaid chart) and, alongside it, an HTML
# dashboard under build/ (gitignored, not committed, not checked by
# check-status). Reads docs/planning/roadmap.md's own status prose --
# `## TASK-NNN` headings, `**Status: Done, DATE.**` markers, each
# stage's Completion Criteria list and status line -- rather than adding
# a second, competing status field anywhere (root CLAUDE.md, ADR-006
# rule 2: the roadmap stays prose and stays authoritative).
#
# Before rendering anything it cross-checks a handful of structural
# facts the roadmap claims (a stage's criteria total, the CLAUDE.md
# count, the test count, the Gherkin scenario count) against the live
# repository, and refuses to generate either file if any disagree --
# see tools/generators/generate_status_report.py and
# docs/planning/status.md for what that caught the first time this ran.
status-report:
	uv run python tools/generators/generate_status_report.py

# Fails if docs/planning/status.md is stale, or if the drift check above
# finds roadmap.md disagreeing with the live repository. Gating, for the
# same reason check-graph and check-manifest are: every rule it applies
# -- does a claimed count match a counted fact -- is structural, not a
# judgement call. See tools/generators/generate_status_report.py's
# module docstring for why the "N of M criteria met" met-count itself
# stays unchecked while the total is gated.
check-status:
	uv run python tools/generators/generate_status_report.py --check

# Regenerates docs/implementation/config-template.yaml: every
# PyFlowConfig field, with a comment above each one stating what counts
# as a valid value and what does not. `pyflow generate-config` (TASK-039)
# already produces a loadable scaffold from the same schema, but
# PyYAML's safe_dump cannot emit comments, so it carries no explanation
# -- this generator is that explanation, kept next to its own source of
# truth instead of hand-typed once and left to drift (root CLAUDE.md,
# docs/CLAUDE.md: generate a document that restates a fact the
# repository already knows). See
# tools/generators/generate_config_template.py's own module docstring.
config-template:
	uv run python tools/generators/generate_config_template.py

# Fails if the committed template is stale relative to the live schema
# (a field's default or type changed) or this generator's own
# FIELD_COMMENTS/SECTION_COMMENTS (an explanation changed without
# regenerating). Part of `make ci`. The narrower, always-on companion
# check -- does every field have *a* comment at all, regardless of
# whether the committed file matches -- is
# tests/unit/test_generate_config_template.py::test_every_live_config_field_has_a_comment,
# which fails a plain `make test` the moment a field is added to
# schema.py with no matching entry, not only at `make ci` time.
check-config-template:
	uv run python tools/generators/generate_config_template.py --check

# Regenerates docs/index.md, the navigable map of every documentation
# page (tools/generators/CLAUDE.md). Not a hand-maintained file -- see
# root CLAUDE.md's "Generated documentation must never be edited
# manually" rule. Run this after adding, moving, deleting, or
# re-titling (changing the first `#` heading of) any page under
# docs/, docs/planning/, docs/architecture/, docs/handbook/{physics,
# numerical-methods}/, docs/implementation/, docs/references/,
# docs/tutorials/, or adr/.
#
# This is not the only generated document: `dependency-tree` (above)
# regenerates docs/planning/dependency-tree.md from the component graph.
# Deliberately a separate target -- it reads planning/, not the doc tree,
# and runs on a different trigger (a graph change, not a page being
# added or re-titled).
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
