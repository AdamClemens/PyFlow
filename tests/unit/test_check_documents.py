"""Unit tests for tools/validators/check_documents.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.

Same split as `test_check_stages.py`: every rule is covered against a
fixture written into `tmp_path`, and one deliberately separate test reads
the real tree so a failure there says "a document is undeclared", never
"a rule is broken".
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

import check_documents  # noqa: E402
from check_documents import (  # noqa: E402
    MECHANISMS,
    declaration_of,
    find_problems,
    tracked_markdown,
)


@pytest.fixture
def doc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], Path]:
    """Write a document into a fake repo root and return its relative path.

    `declaration_of` resolves against `REPO_ROOT`, so the fixture points
    that at `tmp_path` rather than the real repository -- the same reason
    `test_check_graph.py` builds miniature graphs instead of asserting
    against `planning/`.
    """

    def write(body: str) -> Path:
        monkeypatch.setattr(check_documents, "REPO_ROOT", tmp_path)
        path = Path("docs/planning/example.md")
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text(body, encoding="utf-8")
        return path

    return write


def test_a_document_with_a_valid_declaration_reports_nothing(doc: Callable[[str], Path]) -> None:
    """The control. Without it every test below could pass because the
    checker reports nothing under any circumstances.
    """
    path = doc("# A Document\n\nChecked-by: stage-boundary\n\nBody.\n")
    assert find_problems([path]) == []


def test_a_document_with_no_declaration_is_reported(doc: Callable[[str], Path]) -> None:
    path = doc("# A Document\n\nBody, and nothing saying what keeps it true.\n")
    assert any("no 'Checked-by:' line" in p for p in find_problems([path]))


def test_an_unknown_mechanism_is_reported(doc: Callable[[str], Path]) -> None:
    """The three mechanisms are the three this repository actually has.
    A fourth would be a claim about machinery that does not exist.
    """
    path = doc("# A Document\n\nChecked-by: vibes\n")
    problems = find_problems([path])
    assert any("unknown mechanism 'vibes'" in p for p in problems), problems


@pytest.mark.parametrize("mechanism", ["generated", "gated"])
def test_a_mechanism_naming_nothing_responsible_is_reported(
    doc: Callable[[str], Path], mechanism: str
) -> None:
    """`generated` and `gated` are claims that some specific target keeps
    this document honest. A claim with no named owner cannot be verified
    to exist, which is precisely how a check goes inert
    (`docs/practices.md`, "A rule that matches nothing reports nothing").
    """
    path = doc(f"# A Document\n\nChecked-by: {mechanism}\n")
    problems = find_problems([path])
    assert any("names nothing responsible" in p for p in problems), problems


def test_stage_boundary_needs_no_named_owner(doc: Callable[[str], Path]) -> None:
    """The honest asymmetry: `stage-boundary` means *nothing* mechanical
    checks this, so there is nothing to name. Declaring it is a statement
    that the document is unprotected, which is the point of having the
    word at all.
    """
    path = doc("# A Document\n\nChecked-by: stage-boundary\n")
    assert find_problems([path]) == []


def test_a_declaration_below_the_first_40_lines_does_not_count(doc: Callable[[str], Path]) -> None:
    """A declaration belongs where a reader meets it. Scanning the whole
    file would let one hide in the middle of a 3,000-line document, which
    is the same as not having one.
    """
    body = "# A Document\n\n" + ("filler\n" * 60) + "Checked-by: stage-boundary\n"
    path = doc(body)
    assert any("no 'Checked-by:' line" in p for p in find_problems([path]))


def test_the_parenthetical_is_read_back(doc: Callable[[str], Path]) -> None:
    path = doc("# A Document\n\nChecked-by: gated (make check-status)\n")
    assert declaration_of(path) == ("gated", "make check-status")


def test_claude_md_files_are_not_covered() -> None:
    """Directory-local guidance is maintained by whoever works in that
    directory -- the root `CLAUDE.md`'s own standing rule -- and is not
    a description of the world that goes stale the same way.
    """
    assert not any(path.name == "CLAUDE.md" for path in tracked_markdown())


def test_adrs_are_not_covered() -> None:
    """An ADR records a decision as it was taken, on the evidence
    available then. `docs/practices.md` permits editing one only to fix a
    cross-reference, so "is this still true today" is the wrong question
    to ask of it.
    """
    assert not any("adr" in path.parts for path in tracked_markdown())


def test_every_real_document_declares_a_known_mechanism() -> None:
    """The one test that reads the real tree. A failure means a document
    is undeclared, not that a rule is broken.
    """
    paths = tracked_markdown()
    assert paths, "no documents found under the covered roots -- has the layout changed?"
    assert find_problems(paths) == []
    for path in paths:
        mechanism, _ = declaration_of(path)
        assert mechanism in MECHANISMS, (path, mechanism)
