"""The `.claude/` hooks actually run, invoked exactly as configured.

Regression test (2026-08-21 audit). `post_edit_format.py` had been dead
since the day it was added (2026-08-17) and nobody could tell: it used
PEP 758's unparenthesised `except A, B:` syntax, which only parses on
Python 3.14, while `.claude/settings.json` invoked it with a bare
`python` -- whatever happens to be on `PATH`, which on the maintainer's
own machine was 3.10. Claude Code reports nothing when a hook exits
non-zero, so a `SyntaxError` on every single edit was completely silent.

Nothing in `make ci` covered this: `mypy` only looked at `src` and
`tests`, and `ruff` parses with the project's *configured* target
version, so it read the file as valid and said nothing.

Two tests, because there are two independent failure modes and running
the hook only catches one of them reliably. `test_hook_scripts_parse_on_
older_interpreters` is the deterministic one: it compiles each hook at a
fixed `feature_version`, so it fails on this exact bug on any machine.
The end-to-end test below is environment-dependent by nature -- whichever
Python `PATH` happens to resolve is the one it exercises, and on a
machine where that is already 3.14 it would have passed while the hook
was broken for the shell next door. It is still worth having: it is the
only check that the configured command runs at all and does its job.
"""

from __future__ import annotations

import ast
import json
import shlex
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"

# The oldest interpreter a hook script must still parse under. Deliberately
# far below the project's own `requires-python` (3.14): these scripts are
# launched by the harness with whatever `python` resolves to, not by `uv`
# with the project's pinned interpreter, so the project floor is the wrong
# floor for them. 3.9 is chosen as the oldest version still widely present
# as a system Python; raise it only with a reason.
_OLDEST_SUPPORTED_HOOK_INTERPRETER = (3, 9)

_BADLY_FORMATTED = "import os,sys\ndef f( a,b ):\n  return  a+b\n"


def _configured_hook_commands() -> list[str]:
    """Every `command` string `.claude/settings.json` wires up, read from
    the settings file itself rather than restated here -- so a hook added
    later is covered by this test automatically, and a hook whose command
    is edited is tested as edited.
    """
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return [
        hook["command"]
        for matchers in settings.get("hooks", {}).values()
        for matcher in matchers
        for hook in matcher.get("hooks", [])
        if hook.get("type") == "command"
    ]


@pytest.mark.parametrize("script", sorted(HOOKS_DIR.glob("*.py")), ids=lambda path: path.name)
def test_hook_scripts_parse_on_older_interpreters(script: Path) -> None:
    """Every hook script parses at `_OLDEST_SUPPORTED_HOOK_INTERPRETER`.

    `ast.parse(..., feature_version=...)` rejects syntax newer than the
    given version even when running on a newer interpreter, which makes
    this check independent of whatever Python happens to be executing the
    test suite -- unlike actually running the hook.
    """
    source = script.read_text(encoding="utf-8")
    ast.parse(source, feature_version=_OLDEST_SUPPORTED_HOOK_INTERPRETER)


def test_settings_json_wires_up_at_least_one_hook() -> None:
    """Guards the test below from passing vacuously if the settings file
    is restructured and `_configured_hook_commands` silently finds none.
    """
    assert _configured_hook_commands()


@pytest.mark.parametrize("command", _configured_hook_commands())
def test_configured_hook_runs_and_formats_the_file_it_is_given(
    command: str, tmp_path: Path
) -> None:
    """The hook exits 0 *and* does its job.

    Exit code alone is not enough: the script returns 0 on every path it
    handles, including "payload didn't parse", so a broken hook that
    silently no-ops would still look green. The file is a real one under
    `tmp_path`, never a repository file -- the hook rewrites what it is
    pointed at.
    """
    target = tmp_path / "needs_formatting.py"
    target.write_text(_BADLY_FORMATTED, encoding="utf-8")
    payload = json.dumps({"tool_input": {"file_path": str(target)}})

    result = subprocess.run(
        shlex.split(command),
        input=payload,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, f"{command!r} failed: {result.stderr}"
    assert target.read_text(encoding="utf-8") != _BADLY_FORMATTED, (
        f"{command!r} exited 0 but left the file unformatted"
    )
