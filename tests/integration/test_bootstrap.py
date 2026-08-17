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

from pyflow.bootstrap import bootstrap


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


def test_run_offscreen_produces_non_blank_output(tmp_path: Path) -> None:
    """The offscreen backend doesn't just exit 0 -- it actually renders
    and presents real pixel data, not an all-zero or never-presented
    buffer. Guards the same class of bug D5 found once already
    (`renderer.render()` called without `canvas.draw()` renders into a
    texture that's never presented, so the "rendered" image silently
    stays `None` forever, see `RenderWindow._draw`'s own comment) --
    checked here through `bootstrap()`, the public Python entry point
    `pyflow run` itself calls, since a subprocess boundary (as in
    `test_run_bootstraps_and_exits_cleanly` above) has no way to hand
    pixel data back for inspection.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n"
        "  backend: offscreen\n"
        "  width: 48\n"
        "  height: 48\n"
        '  background_color: "#3366cc"\n'
    )

    window = bootstrap(config_file, max_frames=2)

    assert window.last_image is not None
    assert window.last_image.any(), "rendered output is entirely blank/zero"
    assert (window.last_image[..., :3] == [0x33, 0x66, 0xCC]).all()
