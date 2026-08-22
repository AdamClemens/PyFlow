"""Tests for `tools/validators/check_scenarios.py`.

One test per failure mode the script exists to catch, plus one that runs
it against the real tree. The real-tree test is deliberately separate and
named so a failure reads as "a scenario is not being run", never as "a
rule is broken" -- the same split `tests/unit/test_check_graph.py`
already uses, and for the same reason.

These build miniature feature/test trees in `tmp_path` rather than
asserting against `tests/features/`, because a test reading the real
features fails whenever the demos legitimately change, for reasons
unrelated to the rule it covers.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "validators" / "check_scenarios.py"


def _load(features_dir: Path, tests_dir: Path) -> ModuleType:
    """Import the validator with its two directory constants redirected."""
    spec = importlib.util.spec_from_file_location(f"check_scenarios_{id(features_dir)}", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # `setattr` rather than attribute assignment: mypy types a
    # dynamically loaded module as bare `ModuleType`, which has no
    # declared `FEATURES_DIR`. Redirecting the two constants is the
    # whole point of loading it this way.
    setattr(module, "FEATURES_DIR", features_dir)  # noqa: B010
    setattr(module, "TESTS_DIR", tests_dir)  # noqa: B010
    return module


@pytest.fixture
def tree(tmp_path: Path) -> tuple[Path, Path]:
    features = tmp_path / "features"
    tests = tmp_path / "tests"
    features.mkdir()
    tests.mkdir()
    return features, tests


_FEATURE = """Feature: Example
  Scenario: The first thing
    Given something
  Scenario: The second thing
    Given something else
"""


def test_a_feature_no_module_binds_is_reported(
    tree: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """The failure mode the script exists for: pytest is entirely silent
    about a `.feature` file nothing runs -- not an error, not a skip.
    """
    features, tests = tree
    (features / "example.feature").write_text(_FEATURE, encoding="utf-8")
    (tests / "test_other.py").write_text("# binds nothing\n", encoding="utf-8")

    assert _load(features, tests).main() == 1
    assert "no module binds it" in capsys.readouterr().out


def test_a_fully_bound_feature_passes(
    tree: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    features, tests = tree
    (features / "example.feature").write_text(_FEATURE, encoding="utf-8")
    (tests / "test_example.py").write_text('scenarios("example.feature")\n', encoding="utf-8")

    assert _load(features, tests).main() == 0
    assert "are bound and run" in capsys.readouterr().out


def test_an_individually_bound_scenario_leaves_its_siblings_reported(
    tree: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """`scenario()` binds one scenario, so the others in that file
    silently never run -- the same defect as an unbound file, but harder
    to see because the file clearly is referenced.
    """
    features, tests = tree
    (features / "example.feature").write_text(_FEATURE, encoding="utf-8")
    (tests / "test_example.py").write_text(
        'scenario("example.feature", "The first thing")\n', encoding="utf-8"
    )

    assert _load(features, tests).main() == 1
    out = capsys.readouterr().out
    assert "'The second thing' is never bound" in out
    assert "The first thing" not in out


def test_a_feature_bound_twice_is_reported(
    tree: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    """Two bindings run every scenario twice, which passes cheerfully and
    doubles the length of any failure report.
    """
    features, tests = tree
    (features / "example.feature").write_text(_FEATURE, encoding="utf-8")
    (tests / "test_a.py").write_text('scenarios("example.feature")\n', encoding="utf-8")
    (tests / "test_b.py").write_text('scenarios("example.feature")\n', encoding="utf-8")

    assert _load(features, tests).main() == 1
    assert "bound by more than one module" in capsys.readouterr().out


def test_scenario_outlines_count_as_scenarios(tree: tuple[Path, Path]) -> None:
    """`Scenario Outline:` runs once per Examples row; an unbound one is
    exactly as invisible as an unbound `Scenario:`.
    """
    features, tests = tree
    (features / "example.feature").write_text(
        "Feature: Example\n  Scenario Outline: A templated thing\n    Given <x>\n",
        encoding="utf-8",
    )
    (tests / "test_other.py").write_text("# binds nothing\n", encoding="utf-8")

    assert _load(features, tests).main() == 1


def test_an_empty_features_directory_is_not_a_failure(tree: tuple[Path, Path]) -> None:
    """Before Stage 4 writes its first physics feature, a branch that
    touches no scenarios must not fail this gate.
    """
    features, tests = tree
    assert _load(features, tests).main() == 0


def test_the_real_feature_tree_has_no_unrun_scenarios(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Checks the repository itself. A failure here means a real scenario
    is not being run, not that a rule above is broken.
    """
    spec = importlib.util.spec_from_file_location("check_scenarios_real", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert module.main() == 0, capsys.readouterr().out
