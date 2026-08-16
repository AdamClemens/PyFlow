"""Integration test for `python -m pyflow run` (TASK-010, backlog D4).

Real subprocess, real CLI entry point -- same rationale as
`test_cli.py`: this is how a user actually invokes it, not how
`bootstrap()` behaves called in-process. Uses the offscreen render
backend via a config file so it runs headless, the same way CI does
(see docs/planning/backlog.md D3/D5) rather than opening a real window.
"""

import subprocess
import sys
from pathlib import Path


def test_run_bootstraps_and_exits_cleanly(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  width: 64\n  height: 64\n")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(config_file),
            "--max-frames",
            "2",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
