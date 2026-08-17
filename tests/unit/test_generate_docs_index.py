"""Unit tests for tools/generators/generate_docs_index.py.

Not part of the `pyflow` package (it's a repo-consistency script, not
library code), so it's imported directly via `sys.path` rather than as
`pyflow.*` -- see tools/generators/CLAUDE.md, following the same pattern
as tests/unit/test_check_docs.py.
"""

import sys
from pathlib import Path

TOOLS_GENERATORS = Path(__file__).resolve().parents[2] / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_docs_index import entries_for, title_for  # noqa: E402


def test_title_uses_the_first_heading(tmp_path: Path) -> None:
    md = tmp_path / "some-file.md"
    md.write_text("# Real Title\n\nBody text.\n")

    assert title_for(md) == "Real Title"


def test_title_falls_back_to_filename_when_no_heading(tmp_path: Path) -> None:
    md = tmp_path / "no-heading-here.md"
    md.write_text("Body text with no heading.\n")

    assert title_for(md) == "No Heading Here"


def test_entries_for_skips_empty_files(tmp_path: Path) -> None:
    # An empty file is a reserved-but-unwritten page (e.g. docs/architecture/
    # overview.md) -- nothing to link to yet, so it's left out until it has
    # real content and a heading to derive a title from.
    (tmp_path / "written.md").write_text("# Written\n")
    (tmp_path / "reserved.md").write_text("")

    titles = [title for title, _path in entries_for(str(tmp_path))]

    assert titles == ["Written"]


def test_entries_for_excludes_claude_and_index_files(tmp_path: Path) -> None:
    (tmp_path / "real.md").write_text("# Real\n")
    (tmp_path / "CLAUDE.md").write_text("# Should Be Excluded\n")
    (tmp_path / "index.md").write_text("# Should Also Be Excluded\n")

    titles = [title for title, _path in entries_for(str(tmp_path))]

    assert titles == ["Real"]


def test_entries_for_returns_empty_for_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    assert entries_for(str(missing)) == []
