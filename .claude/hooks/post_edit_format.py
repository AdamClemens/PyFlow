"""PostToolUse hook: ruff --fix + ruff format on the single file just edited.

Reads the hook payload from stdin, extracts the touched file path, and -- only
if it's a .py file -- runs `uv run ruff check --fix` and `uv run ruff format`
scoped to that one file (not --all-files; pre-commit/`make lint` already does
the repo-wide sweep at commit time, see .pre-commit-config.yaml).

**This file must parse on interpreters older than the project's own.** It is
run by whichever Python the harness invokes, which is not necessarily the
project's 3.14 -- see CLAUDE.md in this directory, and the regression test at
tests/integration/test_claude_hooks.py, which pins the floor.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        # `json.JSONDecodeError` subclasses `ValueError`, so one type
        # catches both. This read `except json.JSONDecodeError, ValueError:`
        # until 2026-08-21 -- PEP 758 syntax, which only parses on 3.14,
        # while settings.json ran this script under whatever `python` PATH
        # offered. See this directory's CLAUDE.md; ruff.toml beside it is
        # what stops `ruff format` reintroducing that syntax.
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or (payload.get("tool_response") or {}).get("filePath")
    if not file_path or not str(file_path).endswith(".py"):
        return 0

    target = Path(file_path)
    if not target.is_absolute():
        target = REPO_ROOT / target
    if not target.exists():
        return 0

    for args in (["ruff", "check", "--fix", str(target)], ["ruff", "format", str(target)]):
        result = subprocess.run(
            ["uv", "run", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            # Still `return 0` below -- a formatting convenience must never
            # fail the tool call it is attached to. But it should not fail
            # *invisibly* either: the whole reason this file's own breakage
            # went unnoticed for four days is that nothing it did was ever
            # reported. Ruff exits non-zero for unfixable lint findings too,
            # which is worth seeing.
            sys.stderr.write(
                "post_edit_format: {} exited {}\n{}".format(
                    " ".join(args), result.returncode, result.stderr or result.stdout
                )
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
