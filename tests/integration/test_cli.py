"""Smoke test for the `python -m pyflow` entry point (backlog C1a).

Integration, not unit: this crosses the real process boundary the way a
user actually invokes the package, rather than calling `main()` directly.
"""

import subprocess
import sys

from pyflow import __version__


def test_entry_point_prints_version_and_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pyflow"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert __version__ in result.stdout
    assert "usage:" in result.stdout
    assert "-h, --help" in result.stdout
