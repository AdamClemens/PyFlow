"""`pyflow record` and `pyflow resume` (TASK-045, Stage 8, Recording &
Playback): real subprocesses, per this project's CLI-testing convention.
One module for both, not two -- a real `resume` test needs a real
`record` to resume from, and splitting them would either duplicate that
setup or force cross-file coordination for no reader's benefit.

Lives here, not under `tests/golden/`, deliberately: recording is a new
*mode of running an existing config*, not a new demo -- `tests/golden/
CLAUDE.md`'s own "one test module per demo" obligation attaches to a
demo identity, and none is being claimed here. The same category
`test_cli.py`'s own `generate-config` tests already occupy.
"""

import subprocess
import sys
from pathlib import Path

import torch


def test_record_writes_checkpoint_files_for_a_real_golden_demo_config(tmp_path: Path) -> None:
    output_dir = tmp_path / "checkpoints"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "record",
            "--config",
            "examples/golden-demos/heat_diffusion.yaml",
            "--max-frames",
            "5",
            "--output-dir",
            str(output_dir),
            "--checkpoint-interval",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "2" in result.stdout  # frames 0 and 5
    assert (output_dir / "checkpoint_00000000.pt").is_file()
    assert (output_dir / "checkpoint_00000005.pt").is_file()

    # A real, loadable checkpoint -- not just a file that happens to exist.
    payload = torch.load(output_dir / "checkpoint_00000005.pt", weights_only=True)
    assert payload["frame_count"] == 5
    assert set(payload["fields"]) == {"tracer"}  # heat_diffusion's own declared field name


def test_record_requires_config_and_max_frames() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "record"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--config" in result.stderr


def test_resume_continues_a_real_recording_with_no_config_flag(tmp_path: Path) -> None:
    output_dir = tmp_path / "checkpoints"
    record_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "record",
            "--config",
            "examples/golden-demos/heat_diffusion.yaml",
            "--max-frames",
            "5",
            "--output-dir",
            str(output_dir),
            "--checkpoint-interval",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert record_result.returncode == 0, record_result.stderr

    # `resume` gets only the checkpoint path -- no `--config` at all,
    # the property the checkpoint's own self-containment exists for.
    resume_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "resume",
            "--checkpoint",
            str(output_dir / "checkpoint_00000005.pt"),
            "--max-frames",
            "10",
            "--checkpoint-interval",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert resume_result.returncode == 0, resume_result.stderr
    assert "1" in resume_result.stdout  # one new checkpoint: frame 10
    assert (output_dir / "checkpoint_00000010.pt").is_file()

    payload = torch.load(output_dir / "checkpoint_00000010.pt", weights_only=True)
    assert payload["frame_count"] == 10
    assert set(payload["fields"]) == {"tracer"}


def test_resume_requires_checkpoint_and_max_frames() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "resume"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--checkpoint" in result.stderr
