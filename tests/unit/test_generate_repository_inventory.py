"""Unit tests for tools/generators/generate_repository_inventory.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.
"""

import subprocess
import sys
from pathlib import Path

TOOLS_GENERATORS = Path(__file__).resolve().parents[2] / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_repository_inventory import (  # noqa: E402
    OUTPUT_PATH,
    group_by_directory,
    render,
    tracked_files,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_tracked_files_comes_from_git_not_a_directory_walk() -> None:
    """The inventory must list what the repository *contains*, which is
    what git tracks -- not what happens to be on this disk. A walk would
    include `.venv/`, build caches and untracked scratch files, and would
    differ between two clones of the same commit.
    """
    files = tracked_files(REPO_ROOT)
    expected = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.split()

    assert files == sorted(expected)


def test_grouping_puts_root_files_under_a_named_group() -> None:
    """Files with no directory would otherwise group under `.`, which
    reads as a bug in the output rather than as "the repository root".
    """
    groups = group_by_directory(["README.md", "src/pyflow/mesh.py"])

    assert "(root)" in groups
    assert groups["(root)"] == ["README.md"]
    assert groups["src/pyflow"] == ["src/pyflow/mesh.py"]


def test_groups_and_files_are_sorted_so_output_is_stable() -> None:
    """Two runs over the same commit must be byte-identical, or
    `make check-inventory` fails at random.
    """
    forward = group_by_directory(["b/z.md", "a/y.md", "b/a.md"])
    backward = group_by_directory(["b/a.md", "a/y.md", "b/z.md"])

    assert forward == backward
    assert list(forward) == ["a", "b"]
    assert forward["b"] == ["b/a.md", "b/z.md"]


def test_empty_files_are_marked(tmp_path: Path) -> None:
    """The manifest's own legend defines the "Not Started" state as
    "file does not exist, or exists and is empty", so emptiness is the
    one status a generator can determine without judgement. Everything
    else -- draft versus complete -- needs a reader, and this file does
    not guess at it.
    """
    (tmp_path / "empty.yaml").write_text("", encoding="utf-8")
    (tmp_path / "full.md").write_text("# Something\n", encoding="utf-8")

    output = render(["empty.yaml", "full.md"], root=tmp_path)

    empty_line = next(line for line in output.splitlines() if "empty.yaml" in line)
    full_line = next(line for line in output.splitlines() if "full.md" in line)
    assert "empty" in empty_line
    assert "empty" not in full_line


def test_output_says_it_is_generated_and_names_its_source(tmp_path: Path) -> None:
    """Root CLAUDE.md: generated documentation must never be edited
    manually. A generated file that doesn't say so invites exactly that,
    and this one looks hand-writable.
    """
    (tmp_path / "a.md").write_text("x\n", encoding="utf-8")

    output = render(["a.md"], root=tmp_path)

    assert "generated" in output.lower()
    assert "make inventory" in output


def test_output_reports_the_file_count(tmp_path: Path) -> None:
    """A count stated by the generator cannot go stale, which is the
    whole point: "42 tests, 87% coverage" sat wrong in the hand-written
    manifest for five days (2026-08-21 audit).
    """
    for name in ("a.md", "b.md", "c.md"):
        (tmp_path / name).write_text("x\n", encoding="utf-8")

    output = render(["a.md", "b.md", "c.md"], root=tmp_path)

    assert "3" in output


def test_the_committed_inventory_is_up_to_date() -> None:
    """The same assertion `make check-inventory` makes, run in the
    ordinary suite so a stale file fails fast rather than only at the end
    of `make ci`.
    """
    expected = render(tracked_files(REPO_ROOT), root=REPO_ROOT)

    assert OUTPUT_PATH.read_text(encoding="utf-8") == expected
