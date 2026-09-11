.PHONY: install lint format typecheck test check-docs check-docs-index check-graph \
        dependency-tree check-dependency-tree inventory check-inventory \
        check-manifest check-references check-scenarios check-stages check-documents \
        check-claims check-dates check-duplicate-blocks status-report \
        check-status config-template check-config-template docs graph demo benchmark \
        benchmark-report check-benchmark-report record-benchmarks ci preflight clean

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

# pytest-xdist (added 2026-08-30). No test's own content changes -- see
# pyproject.toml's own dev-dependency comment for the profiling behind
# this and what it does and doesn't fix.
#
# `PYTEST_WORKERS` defaults to 4 for a local run; CI (`.github/workflows/
# ci.yml`) sets it higher via the job's own environment before calling
# this same target, rather than this file hardcoding two different
# commands for the two contexts (added 2026-09-06). `?=` means an
# environment variable set by the caller wins over this default, and a
# `make test PYTEST_WORKERS=N` override on the command line wins over
# both -- see `.github/workflows/CLAUDE.md` for why this is the one
# place `make ci` is allowed to behave differently between CI and local,
# despite that file's own general "change the Makefile target, not the
# workflow" rule.
PYTEST_WORKERS ?= 4

# `--dist loadgroup` (added 2026-09-11) distributes exactly like the
# default `load` for ordinary tests, and additionally keeps every test
# sharing an `xdist_group` mark on **one** worker. The only group here is
# `display` (`tests/integration/CLAUDE.md`): the tests that open a real
# GLFW window. Added after Linux CI crashed a worker outright -- no
# Python traceback, the hard process abort GLFW produces rather than an
# exception -- on one run and passed the identical test code on the run
# before it, with 8 workers all creating software-GL contexts against one
# Xvfb display at once. Serialising them removes that contention without
# slowing anything else down, since the group is 10 tests out of 1209.
test:
	uv run pytest -n $(PYTEST_WORKERS) --dist loadgroup

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

ci: lint typecheck test check-docs check-docs-index check-graph check-dependency-tree check-inventory check-manifest check-references check-scenarios check-stages check-documents check-status check-config-template check-dates check-duplicate-blocks check-benchmark-report

# Fast local pre-commit gate (root CLAUDE.md, Branch Discipline section;
# added 2026-09-08). Not a substitute for `make ci` above -- it skips
# check-graph, check-scenarios, check-stages, check-documents,
# check-status, check-config-template, check-dates and
# check-benchmark-report, none of which are cheap enough to run on every
# commit -- but it catches the failures that show up most often before
# they reach CI: a stale generated doc, a broken relative link, a
# tracked file missing from the manifest, a path named in prose that
# doesn't resolve, a lint/type error, or a broken test.
#
# `docs`/`inventory` regenerate rather than check -- unlike `ci`, a
# merely-stale generated doc heals itself here instead of failing
# outright, since the point of a local gate is to fix what it can before
# a human looks at the diff.
#
# No single script in this repository is named "the self-consistency
# validator" -- `check-manifest` (every tracked file is named somewhere)
# and `check-references` (every path named in prose resolves) are the
# two structural-consistency checks fast enough to belong in a local
# gate; `check-graph` covers a third kind (the planning knowledge graph)
# and stays in full `make ci` only, since ordinary commits don't usually
# touch it.
#
# Runs in the order listed, stopping at the first failure, same as `ci`
# above.
preflight: docs inventory check-docs check-manifest check-references lint typecheck test

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

# Fails if a Stage in docs/planning/roadmap.md is missing part of the shape
# a well-defined stage has -- its Goal, the Capability Level it serves, its
# use cases, a Golden Demo, its Completion Criteria, a discharge map, a
# status section -- at the point in its lifecycle each becomes due. The
# shape is declared in docs/planning/stage-shape.yaml and explained in
# docs/planning/stage-specification.md. Gating: every rule is a structural
# fact about the document, never a judgement about whether a criterion is
# any good. Exists because Stage 7 reached its exit audit with no criteria
# at all and nothing noticed -- there was no declared shape to be missing
# from.
check-stages:
	uv run python tools/validators/check_stages.py

# Fails if a maintained document under docs/{planning,architecture,
# implementation}/ does not declare, in its own first 40 lines, what keeps
# it honest: generated, gated, or stage-boundary re-read. Also prints the
# list of documents nothing checks mechanically, which is the reading list
# an exit audit needs. Exists because two documents went stale for days in
# Stage 7 for the same reason -- nobody knew they were in the blast radius.
check-documents:
	uv run python tools/validators/check_documents.py

# Advisory, and deliberately NOT part of `ci`. Reports documentation that
# claims some file or directory is empty/unwritten/a stub when it actually
# has content (docs/practices.md, "Completeness claims belong only in the
# two documents that track completeness"). It exits 0 even with findings,
# because distinguishing a real drift from a document legitimately quoting
# the rule needs judgement -- see tools/validators/CLAUDE.md for the one
# known false positive. Run it as step 10 of the end-of-session
# consistency review, not on every commit.
# Fails if any tracked file records a date later than today. Gating,
# and part of `make ci`: whether a date is in the future is a fact about
# the calendar, not a judgement, and a record of something that has not
# happened is wrong under every reading. Only the full YYYY-MM-DD form
# is checked -- a genuinely planned point is written as prose
# ("targeting December 2026"), which is the escape hatch that lets this
# gate without ever needing a reader. See the script's own docstring for
# the 23-file drift it exists for.
check-dates:
	uv run python tools/validators/check_dates.py

# Fails if a tracked Markdown file contains the same large (12-line)
# block of prose twice, verbatim -- the structural shape a botched
# sed/index-based reorder leaves behind (a real ~3,900-line incident,
# never itself committed since it was caught and reverted within a
# session -- see tools/validators/check_duplicate_blocks.py's own module
# docstring). Gating, added 2026-09-08 (failure-mode audit): whether a
# specific run of lines repeats verbatim elsewhere in the same file is a
# structural fact, not a judgement call.
check-duplicate-blocks:
	uv run python tools/validators/check_duplicate_blocks.py

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

# Renders the knowledge graph as a browsable page under build/ --
# every entity, and every edge in BOTH directions, which the YAML cannot
# show (an entity's file lists what it points at; nothing lists what
# points back). Not committed, so deliberately NOT in `make ci` and with
# no --check mode: there is no committed file for it to be stale
# against. ADR-006 rule 3's bar for generating a *document* does not
# apply, because this duplicates nothing. See the script's own docstring.
graph:
	uv run python tools/generators/generate_graph_view.py

demo:
	uv run python -m pyflow run

# Times bootstrap() end to end for the benchmark suite (DEFAULT_CONFIGS,
# override with --config, repeatable), reporting the minimum across
# repeated runs -- less sensitive to a single contaminated run than a
# mean would be. Prints only; does not touch benchmark_history.jsonl --
# use `record-benchmarks` for that. Not a structural fact itself, so
# deliberately NOT in `make ci` and with no --check mode, the same
# reasoning `graph` above already gives. See
# tools/benchmarks/benchmark_demos.py's own docstring, and run this in
# isolation (nothing else CPU-heavy) for a clean number.
benchmark:
	uv run python tools/benchmarks/benchmark_demos.py

# Renders docs/planning/benchmark-history.md from
# tools/benchmarks/benchmark_history.jsonl. `check-benchmark-report`
# (part of `make ci`) fails if the committed copy is stale -- same shape
# as every other generator/checker pair here, since the *rendering* is a
# structural fact about the (committed) JSONL even though the
# measurements the JSONL holds are not. See
# tools/generators/generate_benchmark_report.py's own docstring.
benchmark-report:
	uv run python tools/generators/generate_benchmark_report.py

check-benchmark-report:
	uv run python tools/generators/generate_benchmark_report.py --check

# Runs the full benchmark suite with --record (appends to
# benchmark_history.jsonl) and regenerates the report in one step -- the
# one-command version of "add a benchmark result to the permanent
# record" tools/benchmarks/CLAUDE.md's own standing rule asks for after
# adding a new benchmark config or at a version bump. Deliberately a
# separate target from `benchmark`/`ci`, never run automatically: a
# recorded number is only meaningful next to *what machine* it came from
# (`benchmark-history.md`'s own hostname column), so this stays a
# deliberate, by-hand action on one person's own machine, not something
# CI's shared, variable-spec runners should ever do silently.
record-benchmarks:
	uv run python tools/benchmarks/benchmark_demos.py --record
	uv run python tools/generators/generate_benchmark_report.py

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
