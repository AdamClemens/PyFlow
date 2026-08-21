"""Unit tests for tools/validators/check_manifest.py.

One test per rule id in the script's own `RULES` docstring block. Not
part of the `pyflow` package -- imported via `sys.path`, see
tools/validators/CLAUDE.md.

Each test builds a miniature repository in `tmp_path` rather than
asserting against the real manifest: a test reading the real one fails
whenever the manifest legitimately changes, for reasons unrelated to the
rule under test. The real manifest is checked once, at the bottom.
"""

import subprocess
import sys
from pathlib import Path

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_manifest import check_manifest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo(tmp_path: Path, manifest: str, files: dict[str, str]) -> Path:
    """A miniature git repository with a manifest and some tracked files.

    A real `git init` and `git add`, because `check_manifest` asks git
    what the repository contains rather than walking the disk -- so a
    fixture that only writes files would exercise nothing.
    """
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    # The manifest is itself a tracked file and must cover itself, or
    # every fixture below would trip `manifest-covers-every-file` on the
    # manifest rather than on what the test is actually about.
    (docs / "repository-manifest.md").write_text(
        manifest + "\n- `repository-manifest.md` -- this document.\n",
        encoding="utf-8",
    )

    for command in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", *command], cwd=tmp_path, capture_output=True, check=True)
    return tmp_path


def _findings(root: Path) -> str:
    return "\n".join(check_manifest(root))


def test_a_file_the_manifest_never_mentions_is_reported(tmp_path: Path) -> None:
    """The drift this validator exists for: something lands in the
    repository and the inventory never hears about it. `.claude/` sat
    unrecorded in two inventories from early in Stage 0 until the
    2026-08-19 F2 sweep found it by hand.
    """
    root = _repo(
        tmp_path,
        manifest="# Repository Manifest\n\n- `README.md` is the entry point.\n",
        files={"README.md": "hi\n", "src/orphan.py": "x = 1\n"},
    )

    findings = _findings(root)
    assert "manifest-covers-every-file" in findings
    assert "src/orphan.py" in findings


def test_a_file_named_only_by_basename_counts_as_covered(tmp_path: Path) -> None:
    """The manifest's tables list bare filenames in a `File` column
    (`index.md`, not `docs/index.md`). That is a deliberate style, not an
    omission, so requiring full paths would report most of the document.
    """
    root = _repo(
        tmp_path,
        manifest="# Repository Manifest\n\n| File | Status |\n|---|---|\n| deep.md | ok |\n",
        files={"docs/nested/deep.md": "x\n"},
    )

    assert check_manifest(root) == []


def test_a_collective_rule_covers_the_files_it_globs(tmp_path: Path) -> None:
    """The manifest states that every file appears "either as its own row
    or under an explicitly stated collective rule". The rules are declared
    in the manifest itself, in a fenced `collective-coverage` block, so
    the statement and the check cannot drift apart (P-011).
    """
    manifest = (
        "# Repository Manifest\n\n```text collective-coverage\nprompts/common/task-*.md\n```\n"
    )
    root = _repo(
        tmp_path,
        manifest=manifest,
        files={"prompts/common/task-one.md": "a\n", "prompts/common/task-two.md": "b\n"},
    )

    assert check_manifest(root) == []


def test_a_collective_rule_that_globs_nothing_is_reported(tmp_path: Path) -> None:
    """A rule matching no file is either a typo or a leftover from files
    that have since been deleted. Either way it is silently widening the
    exemption list, which is the one thing an exemption list must not do.
    """
    manifest = (
        "# Repository Manifest\n\n"
        "- `README.md`\n\n"
        "```text collective-coverage\n"
        "prompts/common/task-*.md\n"
        "```\n"
    )
    root = _repo(tmp_path, manifest=manifest, files={"README.md": "hi\n"})

    findings = _findings(root)
    assert "collective-rule-matches-something" in findings
    assert "task-*.md" in findings


def test_a_retired_path_the_manifest_still_names_is_not_reported(tmp_path: Path) -> None:
    """There is deliberately no "every path exists" rule.

    It was built on 2026-08-21 and removed before shipping: it produced
    44 findings on the real manifest and essentially all were false. This
    document's job includes recording what was *retired* and why --
    `tools/planner/`, `assets/textures/`,
    `docs/planning/numerical-frameworks.md` -- so naming something that
    no longer exists is often the point. It also writes paths relative to
    the section they sit under. Separating those from a genuinely stale
    reference needs a reader, and this validator gates.

    Pinned as a test so the rule doesn't get re-added without someone
    first seeing why it went -- the same reason
    `tests/unit/test_check_claims.py` pins its own removed suppression.
    """
    root = _repo(
        tmp_path,
        manifest="# Repository Manifest\n\n"
        "- `tools/planner/` was retired 2026-08-17; nothing lives there now.\n"
        "- `README.md`\n",
        files={"README.md": "hi\n"},
    )

    assert check_manifest(root) == []


def test_a_not_started_row_naming_a_file_with_content_is_reported(tmp_path: Path) -> None:
    """The manifest's legend defines "Not Started" as "file does not
    exist, or exists and is empty". A file with content marked that way
    is a stale status -- the exact failure `check_claims.py` covers for
    prose, applied here to the status column instead.
    """
    root = _repo(
        tmp_path,
        manifest="# Repository Manifest\n\n| File | Status |\n|---|---|\n"
        "| README.md | ⬜ | not started |\n",
        files={"README.md": "actually has content\n"},
    )

    findings = _findings(root)
    assert "not-started-is-empty" in findings
    assert "README.md" in findings


def test_a_not_started_row_naming_a_genuinely_empty_file_is_accepted(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        manifest="# Repository Manifest\n\n| File | Status |\n|---|---|\n"
        "| blank.yaml | ⬜ | not started |\n",
        files={"blank.yaml": ""},
    )

    assert check_manifest(root) == []


def test_the_repositorys_own_manifest_passes() -> None:
    """A different assertion from every test above: those prove the rules
    fire, this proves the real manifest satisfies them. Named so a
    failure reads as "the manifest is wrong", never as "a rule is broken".
    """
    assert check_manifest(REPO_ROOT) == []
