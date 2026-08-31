"""Smoke test for the `python -m pyflow` entry point (backlog C1a).

Integration, not unit: this crosses the real process boundary the way a
user actually invokes the package, rather than calling `main()` directly.
"""

import subprocess
import sys
from pathlib import Path

import yaml

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


def test_entry_point_help_mentions_config_flag_and_golden_demos() -> None:
    """Real packaged-entry-point companion to
    `tests/unit/test_main.py::test_top_level_help_describes_current_capabilities`
    -- the same content, verified crossing the real subprocess boundary.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--config" in result.stdout
    assert "examples/golden-demos" in result.stdout
    assert "--demos" in result.stdout


def test_run_demos_bare_lists_available_demos() -> None:
    """`pyflow run --demos` (TASK-043), no value: a real subprocess,
    listing the bundled golden demos rather than running one.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "run", "--demos"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "1  empty_window" in result.stdout
    assert "lid_driven_cavity" in result.stdout


def test_run_demos_by_name_runs_the_real_demo() -> None:
    """`pyflow run --demos <name>` resolves to the same config
    `--config examples/golden-demos/<name>.yaml` already runs -- checked
    by actually running it headlessly, not just that the flag parses.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--demos",
            "empty_window",
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_run_demos_rejects_unknown_name() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "run", "--demos", "not_a_real_demo"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "not_a_real_demo" in result.stderr


def test_run_rejects_config_and_demos_together() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            "some-config.yaml",
            "--demos",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "not allowed with argument" in result.stderr


def test_generate_config_prints_valid_yaml_to_stdout() -> None:
    """`pyflow generate-config` with no arguments (TASK-039): a real
    subprocess, per this project's CLI-testing convention, checking
    stdout is actually valid, loadable `PyFlowConfig` YAML rather than
    just that the process exited 0.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pyflow", "generate-config"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    parsed = yaml.safe_load(result.stdout)
    assert list(parsed.keys()) == [
        "logging",
        "rendering",
        "mesh",
        "field_display",
        "fields",
        "simulation",
        "fluid",
        "numerics",
    ]


def test_generate_config_output_writes_file_and_round_trips_through_run(
    tmp_path: Path,
) -> None:
    """`pyflow generate-config --output <path>` (TASK-039): the written
    file must both contain the same content `generate-config` would print
    to stdout, print nothing itself, and actually work as a `pyflow run`
    config -- a real subprocess round-trip through the actual CLI a user
    would use, not `load_config` called in-process.
    """
    output_path = tmp_path / "generated.yaml"

    write_result = subprocess.run(
        [sys.executable, "-m", "pyflow", "generate-config", "--output", str(output_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert write_result.returncode == 0, write_result.stderr
    assert write_result.stdout == ""
    assert output_path.is_file()

    written_config = yaml.safe_load(output_path.read_text())
    assert list(written_config.keys()) == [
        "logging",
        "rendering",
        "mesh",
        "field_display",
        "fields",
        "simulation",
        "fluid",
        "numerics",
    ]

    run_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(output_path),
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, run_result.stderr


def test_generate_config_output_content_matches_stdout(tmp_path: Path) -> None:
    """The file `--output` writes must be the same YAML `generate-config`
    would print to stdout for the same (default) config -- not just
    "some valid YAML", but the actual generated scaffold.
    """
    output_path = tmp_path / "generated.yaml"
    subprocess.run(
        [sys.executable, "-m", "pyflow", "generate-config", "--output", str(output_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    stdout_result = subprocess.run(
        [sys.executable, "-m", "pyflow", "generate-config"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert output_path.read_text() == stdout_result.stdout
