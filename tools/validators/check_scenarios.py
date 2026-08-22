"""Fail if any Gherkin scenario exists but never runs.

Feature files under ``tests/features/`` *are* this project's acceptance
criteria for the work they cover
(``adr/ADR-007-executable-acceptance-criteria.md``). That only means
anything if every scenario in them actually executes -- and pytest is
silent about the failure mode that matters: a ``.feature`` file no test
module binds is not an error, not a skip, and not a warning. It simply
never runs, while reading exactly like a criterion that passes.

Two ways a scenario becomes live, both accepted here:

* a module calls ``scenarios("<file>.feature")``, which binds every
  scenario in that file; or
* a module calls ``scenario("<file>.feature", "<Scenario name>")`` for
  that specific scenario.

So this script reports a feature file bound by neither, a named scenario
inside a partially-bound file that nothing binds, and a file bound more
than once (which silently runs every scenario twice and makes a failure
report twice as long as it should be).

It does **not** check that a scenario's steps are implemented -- pytest-bdd
already fails loudly for a missing step definition, which is exactly the
kind of check this script has no reason to duplicate.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = REPO_ROOT / "tests" / "features"
TESTS_DIR = REPO_ROOT / "tests"

# `Scenario:` and `Scenario Outline:` both declare a runnable scenario.
SCENARIO_PATTERN = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+?)\s*$", re.MULTILINE)
# `scenarios("a.feature", "b.feature")` -- binds every scenario in each.
SCENARIOS_CALL = re.compile(r"\bscenarios\(\s*((?:[\"'][^\"']+[\"']\s*,?\s*)+)\)")
# `scenario("a.feature", "Some name")` -- binds that one scenario.
SCENARIO_CALL = re.compile(r"\bscenario\(\s*[\"']([^\"']+)[\"']\s*,\s*[\"']([^\"']+)[\"']")
STRING_LITERAL = re.compile(r"[\"']([^\"']+)[\"']")


def _display(path: Path) -> str:
    """Repo-relative where possible, absolute otherwise -- the tests
    point the directory constants at a `tmp_path` outside the repository.
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def feature_files() -> list[Path]:
    return sorted(FEATURES_DIR.rglob("*.feature")) if FEATURES_DIR.is_dir() else []


def scenarios_in(feature: Path) -> list[str]:
    return SCENARIO_PATTERN.findall(feature.read_text(encoding="utf-8"))


def collect_bindings() -> tuple[dict[str, list[Path]], dict[str, set[str]]]:
    """Returns (feature name -> modules binding it wholesale, feature name
    -> individually bound scenario names).
    """
    whole: dict[str, list[Path]] = defaultdict(list)
    individual: dict[str, set[str]] = defaultdict(set)

    for module in sorted(TESTS_DIR.rglob("*.py")):
        text = module.read_text(encoding="utf-8")
        for group in SCENARIOS_CALL.findall(text):
            for name in STRING_LITERAL.findall(group):
                whole[Path(name).name].append(module)
        for name, scenario_name in SCENARIO_CALL.findall(text):
            individual[Path(name).name].add(scenario_name)

    return whole, individual


def main() -> int:
    features = feature_files()
    if not features:
        print("No feature files found; nothing to check.")
        return 0

    whole, individual = collect_bindings()
    problems: list[str] = []

    for feature in features:
        rel = _display(feature)
        name = feature.name
        bound_by = whole.get(name, [])

        if len(bound_by) > 1:
            where = ", ".join(_display(m) for m in bound_by)
            problems.append(f"{rel}: bound by more than one module ({where}) -- runs twice")

        if bound_by:
            continue

        declared = scenarios_in(feature)
        if not declared:
            problems.append(f"{rel}: contains no scenarios")
            continue

        unbound = [s for s in declared if s not in individual.get(name, set())]
        if len(unbound) == len(declared):
            problems.append(
                f"{rel}: no module binds it -- all {len(declared)} scenario(s) silently never run"
            )
        else:
            for s in unbound:
                problems.append(f"{rel}: scenario {s!r} is never bound and never runs")

    for problem in problems:
        print(problem)

    if problems:
        print(f"\n{len(problems)} unrun-scenario problem(s) found.")
        return 1

    total = sum(len(scenarios_in(f)) for f in features)
    print(f"All {total} scenario(s) across {len(features)} feature file(s) are bound and run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
