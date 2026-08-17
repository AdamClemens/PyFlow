"""PostToolUse hook: ruff --fix + ruff format on the single file just edited.

Reads the hook payload from stdin, extracts the touched file path, and -- only
if it's a .py file -- runs `uv run ruff check --fix` and `uv run ruff format`
scoped to that one file (not --all-files; pre-commit/`make lint` already does
the repo-wide sweep at commit time, see .pre-commit-config.yaml).
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError, ValueError:
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
        subprocess.run(
            ["uv", "run", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
