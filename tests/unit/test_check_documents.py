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


# --- update obligations ---------------------------------------------------
#
# Added 2026-09-05, at the maintainer's direction: "if something is
# asking for a task to update it then that *needs* to make its way into
# the relevant task specification."
#
# A natural-language detector was considered and rejected. Almost every
# mention of a task beside the word "update" in this repository is
# *historical* ("TASK-034 landed and deliberately did not build it"), and
# telling those from a live obligation is judgement -- which
# `tools/validators/CLAUDE.md` says must not gate. A declared marker is a
# structural fact instead, the same choice `Checked-by:` made.


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str, str], Path]:
    """A fake repository root with a roadmap and one document in it."""

    def build(roadmap: str, document: str) -> Path:
        monkeypatch.setattr(check_documents, "REPO_ROOT", tmp_path)
        (tmp_path / "docs" / "planning").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "planning" / "roadmap.md").write_text(roadmap, encoding="utf-8")
        (tmp_path / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
        path = Path("docs/architecture/example.md")
        (tmp_path / path).write_text(document, encoding="utf-8")
        return path

    return build


_OPEN_TASK = "## TASK-099\n\nMentions docs/architecture/example.md.\n"
_DONE_TASK = (
    "## TASK-099\n\n**Status: Done, 2026-09-05.**\n\nMentions docs/architecture/example.md.\n"
)


def test_an_obligation_on_a_finished_task_is_reported(repo: Callable[[str, str], Path]) -> None:
    """**The rule with teeth, and the one the request was about.**

    `docs/architecture/sequences.md` asked in prose to be updated "once
    TASK-030 wires a live timestep loop through it". TASK-030 landed on
    2026-08-28 and that note went on describing a seam nothing used for
    six days, on the same page as two live paths through it. An
    obligation on a finished task is overdue by definition, and nothing
    else in this repository can notice: nobody touches a closed task, so
    "re-read it when that task is touched" never fires.

    Verified against the real case before being trusted -- replacing
    `sequences.md`'s own declaration with `TASK-030` reproduces the
    failure exactly.
    """
    path = repo(
        _DONE_TASK, "# Doc\n\nChecked-by: stage-boundary\n\nUpdated-by: TASK-099 -- a note\n"
    )
    problems = check_documents.find_obligation_problems([path])
    assert any("already" in p and "Done" in p for p in problems), problems


def test_an_obligation_the_task_never_names_is_reported(repo: Callable[[str, str], Path]) -> None:
    """The maintainer's rule stated exactly: an obligation only the
    document records is one the task will not honour, because whoever
    works the task reads the task.
    """
    path = repo(
        "## TASK-099\n\nSays nothing about any document.\n",
        "# Doc\n\nChecked-by: stage-boundary\n\nUpdated-by: TASK-099 -- a note\n",
    )
    problems = check_documents.find_obligation_problems([path])
    assert any("never names this document" in p for p in problems), problems


def test_an_obligation_on_a_task_that_does_not_exist_is_reported(
    repo: Callable[[str, str], Path],
) -> None:
    path = repo(
        _OPEN_TASK, "# Doc\n\nChecked-by: stage-boundary\n\nUpdated-by: TASK-404 -- a note\n"
    )
    problems = check_documents.find_obligation_problems([path])
    assert any("no entry in" in p for p in problems), problems


def test_a_well_formed_obligation_on_an_open_task_is_accepted(
    repo: Callable[[str, str], Path],
) -> None:
    """The control: a task that exists, is unfinished, and names the
    document back. Without this every test above could pass because the
    checker reports something under all circumstances.
    """
    path = repo(
        _OPEN_TASK, "# Doc\n\nChecked-by: stage-boundary\n\nUpdated-by: TASK-099 -- a note\n"
    )
    assert check_documents.find_obligation_problems([path]) == []


def test_an_unassigned_obligation_is_allowed_but_must_say_what_it_owes(
    repo: Callable[[str, str], Path],
) -> None:
    """A real obligation with no task yet is worth recording -- better in
    an inventory than buried in prose where nothing reaches it. It still
    has to say what it owes, or it is a marker rather than a statement.
    """
    good = repo(
        _OPEN_TASK,
        "# Doc\n\nChecked-by: stage-boundary\n\nUpdated-by: unassigned -- this section\n",
    )
    assert check_documents.find_obligation_problems([good]) == []

    bare = repo(_OPEN_TASK, "# Doc\n\nChecked-by: stage-boundary\n\nUpdated-by: unassigned\n")
    assert any(
        "must say what it owes" in p for p in check_documents.find_obligation_problems([bare])
    )


def test_obligations_are_read_from_the_whole_document(repo: Callable[[str, str], Path]) -> None:
    """Deliberately unlike `Checked-by:`, which must sit in the first 40
    lines. A document has one honesty mechanism but may owe several
    updates, each belonging beside the paragraph that owes it.
    """
    body = "# Doc\n\nChecked-by: stage-boundary\n" + ("filler\n" * 60)
    body += "\nUpdated-by: unassigned -- a late section\n"
    path = repo(_OPEN_TASK, body)
    assert check_documents.obligations_of(path) == [("unassigned", "a late section")]


def test_the_real_tree_has_no_overdue_obligation() -> None:
    """The one obligation test that reads the real repository. A failure
    means an update is genuinely overdue, not that a rule is broken.
    """
    assert check_documents.find_obligation_problems(tracked_markdown()) == []


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
