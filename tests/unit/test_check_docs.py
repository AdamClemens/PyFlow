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

from check_docs import check_file, heading_slugs, slugify  # noqa: E402


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


# --- heading fragments ----------------------------------------------------
#
# Added 2026-09-04. `check_docs.py` resolved a link's *path* and stopped
# there, which both that script's docstring and `tools/validators/
# CLAUDE.md` recorded as a known gap: "verifying a heading exists would
# need parsing every target file's heading slugs, which is a different,
# heavier check". It became worth building the moment prose started
# linking *into generated documents*, whose headings a generator can
# change without anyone noticing -- a cross-reference into a generated
# document is only safe if something checks the anchor.


def test_flags_a_fragment_that_names_no_heading(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Target\n\n## Real Heading\n")
    md = tmp_path / "doc.md"
    md.write_text("See [there](target.md#no-such-heading).\n")

    broken = check_file(md)

    assert len(broken) == 1
    _lineno, target, reason = broken[0]
    assert target == "target.md#no-such-heading"
    assert "no such heading" in reason


def test_does_not_flag_a_fragment_that_names_a_real_heading(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Target\n\n## Real Heading\n")
    md = tmp_path / "doc.md"
    md.write_text("See [there](target.md#real-heading).\n")

    assert check_file(md) == []


def test_a_same_file_fragment_is_checked_against_its_own_headings(tmp_path: Path) -> None:
    """`(#anchor)` names a heading in the linking file itself. It was
    skipped entirely before -- `is_local_target` returned False for a
    bare fragment -- so a self-link to a renamed section was invisible.
    """
    md = tmp_path / "doc.md"
    md.write_text("# Doc\n\n## A Section\n\nBack to [the section](#a-section).\n")
    assert check_file(md) == []

    md.write_text("# Doc\n\n## A Section\n\nJump to [nowhere](#not-here).\n")
    broken = check_file(md)
    assert len(broken) == 1
    assert "no such heading" in broken[0][2]


def test_a_link_with_no_fragment_is_unaffected(tmp_path: Path) -> None:
    """The existing behaviour, pinned: a path-only link must not start
    demanding headings of its target.
    """
    (tmp_path / "target.md").write_text("no headings at all\n")
    md = tmp_path / "doc.md"
    md.write_text("See [there](target.md).\n")

    assert check_file(md) == []


def test_a_fragment_on_a_non_markdown_target_is_not_checked(tmp_path: Path) -> None:
    """Only Markdown has headings this script can resolve. A fragment on
    anything else is somebody else's addressing scheme -- a line number,
    a YAML path -- and not a claim this check can verify.
    """
    (tmp_path / "data.yaml").write_text("key: value\n")
    md = tmp_path / "doc.md"
    md.write_text("See [there](data.yaml#L3).\n")

    assert check_file(md) == []


def test_slugify_matches_the_headings_this_repository_actually_writes() -> None:
    """Checked against real headings from the generated documents these
    cross-references point at, rather than taken from a specification.

    The four-hyphen case is the one worth pinning: `status.md`'s stage
    headings are written `Stage 7 -- Rendering Annotations`, and the
    surrounding spaces plus the literal double hyphen produce an anchor
    that looks like a typo and is not.
    """
    assert slugify("Stage 7 -- Rendering Annotations") == "stage-7----rendering-annotations"
    assert slugify("## Dependency order") == "dependency-order"
    assert slugify("`tools/` (root)") == "tools-root"
    assert slugify("Why This Split") == "why-this-split"


def test_heading_slugs_disambiguates_repeated_headings(tmp_path: Path) -> None:
    """Repeated heading text gets `-1`, `-2` suffixes, which is what
    GitHub does and therefore what a link to the second occurrence has to
    say.
    """
    target = tmp_path / "target.md"
    target.write_text("## Notes\n\n## Notes\n\n## Notes\n")

    slugs = heading_slugs(target)

    assert "notes" in slugs
    assert "notes-1" in slugs
    assert "notes-2" in slugs


def test_headings_inside_fenced_code_are_not_headings(tmp_path: Path) -> None:
    """A `#` inside a fence is a comment or a shell prompt. Treating one
    as a heading would let a link resolve against an anchor no reader can
    navigate to -- the check passing for the wrong reason.
    """
    target = tmp_path / "target.md"
    target.write_text("# Real\n\n```bash\n# Not A Heading\n```\n")

    slugs = heading_slugs(target)

    assert "real" in slugs
    assert "not-a-heading" not in slugs
