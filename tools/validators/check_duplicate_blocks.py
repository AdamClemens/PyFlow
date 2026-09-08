"""Fail if a tracked Markdown file contains the same large block of prose
twice, verbatim.

Mechanises the failure mode a 2026-09-08 audit of this repository's own
recurring mistakes found no other gate covered: a `sed`/index-arithmetic
edit that duplicates a section of a file instead of moving it, which
duplicated roughly 3,900 lines of a real planning document in one
incident (Claude Code Insights, 2026-09-08 usage report). That incident
never reached `git log` -- it was caught and reverted within the session
before being committed -- so there is no historical commit this script
can point at; it is built from the failure's shape, not a specific
commit, the same way `check_dates.py` was built from a class of mistake
rather than one instance of it.

**Detection: a sliding window of `WINDOW` consecutive lines, hashed as a
tuple.** If the same `WINDOW`-line block appears twice in one file, at
non-overlapping offsets, that is reported. A window is only compared once
at least `MIN_SUBSTANTIAL_LINES` of its `WINDOW` lines are "substantial"
(at least `MIN_LINE_LENGTH` characters after stripping) -- table
dividers, blank-line runs and short list markers repeat legitimately
throughout real prose and must not fire this on their own. Both
constants were chosen empirically against this repository's own tracked
Markdown (verified zero findings before landing, the same discipline
`tools/validators/CLAUDE.md`'s `ka-name-matches-manifest` entry
describes) -- widen `WINDOW` or lower `MIN_SUBSTANTIAL_LINES` only after
re-running against the real tree and confirming it still finds nothing.

**Scoped to `*.md` only.** Code and tests routinely repeat near-identical
structure on purpose (parametrised tests, per-field config comments,
boilerplate CLAUDE.md headers) -- scanning them would very likely
reproduce the false-positive trap `check_manifest.py`'s own dropped
"every path exists" rule warns about (`tools/validators/CLAUDE.md`).
Prose duplication is also the actual incident this exists for: a
structural copy-paste accident in a *document*, not a legitimate
repeated code pattern.

Run via `make check-duplicate-blocks`, part of `make ci`. Gates rather
than advises: whether a specific run of lines repeats verbatim elsewhere
in the same file is a structural fact, not a judgement call, the same
reasoning `check_graph.py`/`check_manifest.py` already use.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# See the module docstring for how these were chosen. WINDOW=12 with
# MIN_SUBSTANTIAL_LINES=10 is far below the ~3,900-line incident this
# check exists to catch, while producing zero findings against this
# repository's own tracked Markdown as of 2026-09-08.
WINDOW = 12
MIN_SUBSTANTIAL_LINES = 10
MIN_LINE_LENGTH = 20


def _tracked_markdown_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=root, capture_output=True, text=True, check=True
    )
    return [root / p for p in result.stdout.split()]


def _is_substantial(block: tuple[str, ...]) -> bool:
    substantial = sum(1 for line in block if len(line.strip()) >= MIN_LINE_LENGTH)
    return substantial >= MIN_SUBSTANTIAL_LINES


def _find_duplicate(lines: list[str]) -> tuple[int, int] | None:
    """First (earlier_index, later_index) pair of a duplicated, non-
    overlapping `WINDOW`-line block, or `None`.
    """
    seen: dict[tuple[str, ...], int] = {}
    for index in range(len(lines) - WINDOW + 1):
        block = tuple(lines[index : index + WINDOW])
        if not _is_substantial(block):
            continue
        first = seen.get(block)
        if first is None:
            seen[block] = index
        elif index >= first + WINDOW:
            return first, index
    return None


def check_duplicate_blocks(root: Path = REPO_ROOT) -> list[str]:
    """Every duplicated block found, as human-readable strings.

    `root` is a parameter so tests can build miniature repositories in
    `tmp_path` -- a test asserting only against real files would fail
    every time real prose legitimately changed near a false positive.
    """
    findings: list[str] = []
    for path in _tracked_markdown_files(root):
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        result = _find_duplicate(lines)
        if result is None:
            continue
        first, second = result
        rel = path.relative_to(root).as_posix()
        findings.append(
            f"duplicate-block: {rel} repeats the same {WINDOW}-line block at "
            f"line {first + 1} and line {second + 1} -- check for a botched "
            f"sed/index-based edit rather than an intentional move"
        )
    return findings


def main() -> int:
    findings = check_duplicate_blocks()
    if findings:
        for finding in findings:
            print(finding)
        print(f"\n{len(findings)} duplicate block(s) found.")
        return 1

    print("No duplicated content blocks found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
