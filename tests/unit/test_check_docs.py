"""Unit tests for tools/validators/check_docs.py.

Not part of the `pyflow` package (it's a repo-consistency script, not
library code), so it's imported directly via `sys.path` rather than as
`pyflow.*` -- see tools/validators/CLAUDE.md.
"""

import sys
from pathlib import Path

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_docs import check_file  # noqa: E402


def test_flags_a_broken_relative_link(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("See [missing](does-not-exist.md) for details.\n")

    broken = check_file(md)

    assert len(broken) == 1
    lineno, target, _reason = broken[0]
    assert lineno == 1
    assert target == "does-not-exist.md"


def test_does_not_flag_a_link_that_resolves(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Target\n")
    md = tmp_path / "doc.md"
    md.write_text("See [target](target.md) for details.\n")

    assert check_file(md) == []


def test_does_not_flag_markdown_syntax_shown_as_a_code_example(tmp_path: Path) -> None:
    """Regression test: prose describing link syntax isn't a real link.

    Found while building this checker -- its own CLAUDE.md entry wrote
    "Markdown links (`[text](target)`)" as an inline-code example, and the
    checker flagged the literal word "target" as a broken link to a
    nonexistent file named "target". A real link is never wrapped in
    backticks, so stripping inline code spans before scanning distinguishes
    the two without needing a link-target allowlist.
    """
    md = tmp_path / "doc.md"
    md.write_text("Markdown links look like `[text](target)` in source.\n")

    assert check_file(md) == []
