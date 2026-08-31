"""Unit tests for tools/validators/check_claims.py.

Not part of the `pyflow` package (it's a repo-consistency script, not library
code), so it's imported directly via `sys.path` -- same pattern as
`test_check_docs.py`, see tools/validators/CLAUDE.md.

The cases below are the real historical drifts the 2026-08-18 documentation
review found, reduced to fixtures. They matter because the checker reports
nothing against the repository as it stands today -- every instance it was
built for had already been fixed by hand before it existed -- so these tests
are the only evidence that it fires at all.
"""

import sys
from pathlib import Path

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_claims import findings_for, iter_markdown_files  # noqa: E402


def test_flags_a_claim_that_a_written_file_is_empty(tmp_path: Path) -> None:
    """The docs/glossary.md -> releases.md drift, reduced."""
    (tmp_path / "releases.md").write_text("# Releases\n\nReal content here.\n")
    doc = tmp_path / "glossary.md"
    doc.write_text("No release process is defined and `releases.md` is empty.\n")

    findings = findings_for(doc)

    assert len(findings) == 1
    lineno, token, _line = findings[0]
    assert lineno == 1
    assert token == "releases.md"


def test_flags_a_stub_claim_about_a_written_file(tmp_path: Path) -> None:
    """The engine.md -> advection.md drift, reduced."""
    (tmp_path / "advection.md").write_text("# Advection\n\nUpwind, central...\n")
    doc = tmp_path / "engine.md"
    doc.write_text(
        "What upwind advection is belongs in `advection.md`\n(currently an empty stub).\n"
    )

    findings = findings_for(doc)

    assert [token for _n, token, _l in findings] == ["advection.md"]


def test_flags_a_placeholder_claim_about_a_populated_directory(tmp_path: Path) -> None:
    """The tests/CLAUDE.md -> unit/ drift, reduced."""
    (tmp_path / "unit").mkdir()
    (tmp_path / "unit" / "test_thing.py").write_text("def test_thing(): pass\n")
    doc = tmp_path / "CLAUDE.md"
    doc.write_text("`unit/` and `golden/` remain placeholders.\n")

    findings = findings_for(doc)

    assert [token for _n, token, _l in findings] == ["unit/"]


def test_does_not_flag_a_claim_that_is_actually_true(tmp_path: Path) -> None:
    (tmp_path / "releases.md").write_text("")
    doc = tmp_path / "glossary.md"
    doc.write_text("`releases.md` is empty.\n")

    assert findings_for(doc) == []


def test_does_not_flag_a_directory_of_deliberately_empty_files(tmp_path: Path) -> None:
    """planning/data/ holds seven empty .yaml files by design -- the directory
    exists and is populated, but holds no content, so the claim stands."""
    (tmp_path / "data").mkdir()
    for name in ("capabilities.yaml", "concepts.yaml"):
        (tmp_path / "data" / name).write_text("")
    doc = tmp_path / "CLAUDE.md"
    doc.write_text("All the files in `data/` are currently empty by design.\n")

    assert findings_for(doc) == []


def test_does_not_flag_a_quoted_claim(tmp_path: Path) -> None:
    """A document recording that some other file used to say this is not
    itself making the claim -- the correction note in docs/glossary.md."""
    (tmp_path / "releases.md").write_text("# Releases\n\nReal content.\n")
    doc = tmp_path / "glossary.md"
    doc.write_text('This entry said `releases.md` "is empty" until it was corrected.\n')

    assert findings_for(doc) == []


def test_finds_a_path_named_on_the_previous_line(tmp_path: Path) -> None:
    """These documents hard-wrap, so the path a claim is about is often a line
    above the claim itself. Both real drifts wrapped exactly this way."""
    (tmp_path / "releases.md").write_text("# Releases\n\nReal content.\n")
    doc = tmp_path / "glossary.md"
    doc.write_text("See `releases.md` for the deferral,\nthough that file is empty.\n")

    assert [token for _n, token, _l in findings_for(doc)] == ["releases.md"]


def test_known_limitation_quantified_statements_are_reported(tmp_path: Path) -> None:
    """ "no file tracked in `X` is empty" is a rule about X's *contents*, not a
    claim that X is empty -- but the checker reports it anyway.

    A quantifier-based suppression was tried and removed: the real
    docs/glossary.md drift read "no release process is defined,
    `releases.md` is empty", so suppressing on a nearby quantifier silently
    discarded a true positive. Reporting one known false positive is the
    better trade for an advisory tool. `docs/planning/knowledge-architecture.md`
    is the one line in the repository that trips this; see
    tools/validators/CLAUDE.md.
    """
    (tmp_path / "manifest.md").write_text("# Manifest\n\nRows.\n")
    doc = tmp_path / "ka.md"
    doc.write_text("The A3 decision means: no file tracked in `manifest.md` is empty.\n")

    assert [token for _n, token, _l in findings_for(doc)] == ["manifest.md"]


def test_ignores_a_claim_about_a_file_that_does_not_exist(tmp_path: Path) -> None:
    """Nothing to contradict -- the checker never guesses about absent files."""
    doc = tmp_path / "doc.md"
    doc.write_text("`never-existed.md` is empty.\n")

    assert findings_for(doc) == []


def test_does_not_flag_a_reported_claim(tmp_path: Path) -> None:
    """A maintenance note narrating a past drift is describing a claim, not
    making one -- docs/architecture/CLAUDE.md's record of engine.md's error."""
    (tmp_path / "handbook").mkdir()
    (tmp_path / "handbook" / "advection.md").write_text("# Advection\n\nReal.\n")
    doc = tmp_path / "CLAUDE.md"
    doc.write_text("`engine.md` still described `handbook/` as unwritten a day later.\n")

    assert findings_for(doc) == []


def test_only_tracked_markdown_files_are_read() -> None:
    """The Stage 6 exit audit's own finding, as a regression test.

    `iter_markdown_files` used to walk the working tree with `rglob`
    against a hardcoded list of directory names to skip, and
    `.claude/worktrees/` -- where a `git worktree` checkout of this same
    repository lives -- was not on it. The run that found this reported
    14 completeness claims, 12 of them the repository's own documents
    seen a second time through that copy, which is a report nobody can
    usefully read. Asserting *tracked* here rather than asserting the
    absence of one particular directory is the point: it is the property
    that does not have to be revisited when some future tool writes
    somewhere new.
    """
    import subprocess

    repo_root = Path(__file__).resolve().parents[2]
    tracked = {
        (repo_root / line).resolve()
        for line in subprocess.run(
            ["git", "ls-files", "*.md"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    }

    read = {path.resolve() for path in iter_markdown_files()}

    assert read == tracked
    assert not any(".venv" in path.parts or "worktrees" in path.parts for path in read)
