"""Unit tests for tools/validators/check_duplicate_blocks.py.

Fixture repos in `tmp_path`, same reasoning as `test_check_manifest.py`:
the real repository is checked once, at the bottom, and everything else
builds a miniature repository so a rule's own test doesn't fail whenever
real prose legitimately changes.
"""

import subprocess
import sys
from pathlib import Path

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_duplicate_blocks import check_duplicate_blocks  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    """A miniature git repository holding the given tracked files.

    A real `git init`/`git add`, because this validator asks git which
    Markdown files are tracked rather than walking the disk.
    """
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    for command in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", *command], cwd=tmp_path, capture_output=True, check=True)
    return tmp_path


def _substantial_block(n: int, prefix: str) -> str:
    """`n` lines that are each long enough to count as "substantial"."""
    return "\n".join(f"{prefix} line number {i} carries real, specific prose" for i in range(n))


def test_a_large_duplicated_block_is_reported(tmp_path: Path) -> None:
    """The failure this exists for, at a testable scale: a botched sed or
    index-based reorder duplicated roughly 3,900 lines of a real planning
    document (Claude Code Insights, 2026-09-08 usage report) -- the same
    substantial block of prose appearing twice, verbatim, in one file.
    """
    block = _substantial_block(15, "content")
    text = "intro\n\n" + block + "\n\nan unrelated middle section\n\n" + block + "\n\noutro\n"
    root = _repo(tmp_path, {"docs/plan.md": text})

    findings = check_duplicate_blocks(root)
    assert len(findings) == 1
    assert "docs/plan.md" in findings[0]


def test_short_or_sparse_repeated_lines_are_not_reported(tmp_path: Path) -> None:
    """Table dividers, blank-line runs and short list markers repeat
    legitimately throughout real documents and must never fire this
    check -- only a run of genuinely substantial lines should count.
    """
    text = "\n".join(["| a | b |", "|---|---|"] * 20)
    root = _repo(tmp_path, {"docs/table.md": text})

    assert check_duplicate_blocks(root) == []


def test_a_file_with_no_duplication_is_not_reported(tmp_path: Path) -> None:
    block = _substantial_block(15, "content")
    root = _repo(tmp_path, {"docs/plan.md": "intro\n\n" + block + "\n\noutro\n"})

    assert check_duplicate_blocks(root) == []


def test_a_non_markdown_tracked_file_is_not_scanned(tmp_path: Path) -> None:
    """Scoped to `*.md` only (root CLAUDE.md's Blast Radius rule is about
    documentation specifically here) -- code and tests routinely repeat
    near-identical structure on purpose (parametrised tests, per-field
    config comments) and scanning them would reproduce the false-positive
    trap `check_manifest.py`'s own dropped "every path exists" rule
    warns about.
    """
    block = _substantial_block(15, "content")
    text = block + "\n\n" + block + "\n"
    root = _repo(tmp_path, {"src/generated.py": text})

    assert check_duplicate_blocks(root) == []


def test_the_real_repositorys_markdown_has_no_duplicated_blocks() -> None:
    """Proves the rule against real data before it gates anything -- the
    same discipline `check_manifest.py`'s `ka-name-matches-manifest` was
    verified with: run against the real repository and confirm zero
    findings before wiring it into `make ci`.
    """
    assert check_duplicate_blocks(REPO_ROOT) == []
