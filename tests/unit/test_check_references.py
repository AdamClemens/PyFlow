"""Tests for `tools/validators/check_references.py`.

Structured the same way `test_check_manifest.py` is, and for the same
reason: one of these tests exists to pin a decision rather than a
behaviour. A path-existence rule was written once before, produced 44
essentially-false findings against `docs/repository-manifest.md`, and
was removed (`tools/validators/CLAUDE.md`). This script is that rule
returning in a narrower form, and
`test_documents_that_name_retired_things_are_excluded` is what stops the
exclusion quietly disappearing and the old problem coming back with it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "validators" / "check_references.py"


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_references_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FILES = {
    "docs/practices.md",
    "src/pyflow/engine/mesh.py",
    "src/pyflow/rendering/canvas.py",
    "examples/golden-demos/empty_window.yaml",
    "adr/ADR-003-modular-numerical-strategies.md",
    "planning/model/schema.yaml",
}
_DIRS = {"docs", "src", "src/pyflow", "src/pyflow/engine", "planning", "planning/model"}


@pytest.mark.parametrize(
    ("path", "containing", "why"),
    [
        ("docs/practices.md", "", "an ordinary root-relative path"),
        ("src/pyflow/engine/mesh.py", "", "a source file"),
        ("adr/ADR-003", "", "a prefix -- ADR ids are cited without the slug"),
        ("../model/schema.yaml", "planning/data", "a parent-relative path"),
        ("rendering/canvas.py", "src/pyflow/configuration", "a sibling package's module"),
        (
            "golden-demos/empty_window.yaml",
            "docs",
            "section-relative: named inside a passage about examples/",
        ),
    ],
)
def test_a_path_that_exists_resolves(path: str, containing: str, why: str) -> None:
    assert _module().resolves(path, containing, _FILES, _DIRS), why


def test_a_suffix_match_must_land_on_a_path_boundary() -> None:
    """`mesh.py` must not resolve against `structured_mesh.py`; without
    the leading slash it would, and the check would stop meaning much.
    """
    module = _module()
    assert not module.resolves("engine/other_mesh.py", "", _FILES, _DIRS)


def test_a_path_that_exists_nowhere_is_reported(tmp_path: Path) -> None:
    module = _module()
    doc = tmp_path / "doc.md"
    doc.write_text("See `docs/does-not-exist.md` for details.\n", encoding="utf-8")

    found = module.check_file(doc, "docs/doc.md", _FILES, _DIRS)

    assert found == [(1, "docs/does-not-exist.md")]


def test_each_missing_path_is_reported_once_per_file(tmp_path: Path) -> None:
    """A document naming the same dead path six times should produce one
    finding, not six -- an unreadable report is an ignored one.
    """
    module = _module()
    doc = tmp_path / "doc.md"
    doc.write_text("`a/gone.md`\n`a/gone.md`\n`a/gone.md`\n", encoding="utf-8")

    assert len(module.check_file(doc, "doc.md", _FILES, _DIRS)) == 1


def test_brace_shorthand_is_expanded(tmp_path: Path) -> None:
    """`src/pyflow/rendering/{canvas,window}.py` is prose this repository
    writes constantly; both halves must be checked, not the literal.
    """
    module = _module()
    assert module.expand_braces("a/{b,c}.py") == ["a/b.py", "a/c.py"]

    doc = tmp_path / "doc.md"
    doc.write_text("`src/pyflow/engine/{mesh,absent}.py`\n", encoding="utf-8")

    assert module.check_file(doc, "doc.md", _FILES, _DIRS) == [(1, "src/pyflow/engine/absent.py")]


def test_an_allowed_missing_path_is_not_reported(tmp_path: Path) -> None:
    """Prose that says "there is no `docs/handbook/README.md`" is correct
    prose, and rewording it to satisfy a checker would be the wrong fix.
    """
    module = _module()
    doc = tmp_path / "doc.md"
    doc.write_text("There is no `docs/handbook/README.md`.\n", encoding="utf-8")

    assert module.check_file(doc, "doc.md", _FILES, _DIRS) == []


def test_a_planned_artifact_is_not_reported_while_its_task_is_unbuilt(tmp_path: Path) -> None:
    """A fresh module instance (`_module()`) each call, not the shared
    import -- mutating `PLANNED` here can't leak into another test. Uses
    a synthetic entry rather than whatever `PLANNED` happens to hold in
    production: that dict is empty whenever every named artifact has
    actually landed (true as of TASK-021, Stage 3's last task), and a
    test asserting behaviour should not depend on production data being
    non-empty to have something to assert against.
    """
    module = _module()
    planned = "src/pyflow/engine/numerics/not_yet_built.py"
    module.PLANNED[planned] = "TASK-999"
    doc = tmp_path / "doc.md"
    doc.write_text(f"Artifacts Produced: `{planned}`\n", encoding="utf-8")

    assert module.check_file(doc, "doc.md", _FILES, _DIRS) == []


def test_every_planned_entry_names_a_task() -> None:
    """The task id is the trigger for deleting the entry. Without one an
    exemption has no expiry, which is how exemption lists stop meaning
    anything.
    """
    for path, task in _module().PLANNED.items():
        assert task.startswith("TASK-"), f"{path} has no task id"


def test_documents_that_name_retired_things_are_excluded() -> None:
    """Pins the decision, not the behaviour.

    `check_manifest.py` dropped an equivalent rule after it produced 44
    false findings against the manifest -- a document whose job includes
    naming what was retired. This script keeps the rule by excluding
    those documents rather than by growing an exemption list until it
    means nothing. If someone removes an entry here, the old problem
    comes straight back.
    """
    excluded = _module().EXCLUDED_FILES

    assert "docs/repository-manifest.md" in excluded
    assert "docs/planning/backlog.md" in excluded
    assert "docs/CHANGELOG-DESIGN.md" in excluded


def test_the_real_repository_has_no_dangling_path_references(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Checks the repository itself. A failure here means prose names a
    path that does not exist, not that a rule above is broken.
    """
    assert _module().main() == 0, capsys.readouterr().out
