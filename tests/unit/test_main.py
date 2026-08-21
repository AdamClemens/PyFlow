"""Unit tests for pyflow.__main__ (in-process).

Complements, not replaces, the subprocess-based integration tests
(`tests/integration/test_cli.py`, `test_bootstrap.py`), which verify the
real packaged entry point. Those run as real subprocesses, deliberately,
so coverage.py -- which only instruments the in-process interpreter --
can't see into them; `__main__.py` showed 0% coverage despite genuinely
being exercised. These tests call `main()` directly instead, giving real
coverage without weakening the subprocess tests' own purpose.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from pyflow import __version__
from pyflow.__main__ import main
from pyflow.configuration import PyFlowConfig


def test_no_args_prints_version_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    captured = capsys.readouterr()
    assert __version__ in captured.out
    assert "usage:" in captured.out
    assert "-h, --help" in captured.out


def test_run_dispatches_to_bootstrap_with_parsed_args() -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(
            [
                "run",
                "--config",
                "some-config.yaml",
                "--max-frames",
                "3",
                "--backend",
                "offscreen",
            ]
        )

    mock_bootstrap.assert_called_once_with(
        Path("some-config.yaml"), max_frames=3, backend="offscreen"
    )


def test_run_defaults_to_no_config_no_max_frames_no_backend_override() -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(["run"])

    mock_bootstrap.assert_called_once_with(None, max_frames=None, backend=None)


def test_run_rejects_invalid_backend(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["run", "--backend", "not-a-backend"])

    assert "invalid choice" in capsys.readouterr().err


def test_generate_config_with_no_output_prints_to_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    main(["generate-config"])

    captured = capsys.readouterr()
    assert yaml.safe_load(captured.out) == {
        "logging": {"level": "INFO"},
        "rendering": {
            "backend": "glfw",
            "width": 1280,
            "height": 720,
            "title": "PyFlow",
            "background_color": None,
            "show_mesh": False,
            "grid_color": "#4477aa",
            "zoom": 1.0,
            "pan": [0.0, 0.0],
            "zoom_min": 0.1,
            "zoom_max": 10.0,
        },
        "mesh": {
            "origin": [0.0, 0.0],
            "spacing": [1.0, 1.0],
            "extent": [10, 10],
        },
        "field_display": {
            "scalar_pattern": None,
            "vector_pattern": None,
            "low_color": "#0000ff",
            "high_color": "#ff0000",
            "value_range": [0.0, 1.0],
            "arrow_color": "#ffffff",
            "arrow_scale": 0.3,
            "show_legend": True,
        },
    }


def test_generate_config_with_output_writes_file_and_prints_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_path = tmp_path / "generated.yaml"

    main(["generate-config", "--output", str(output_path)])

    captured = capsys.readouterr()
    assert captured.out == ""
    written = yaml.safe_load(output_path.read_text())
    assert list(written.keys()) == ["logging", "rendering", "mesh", "field_display"]
    assert written["mesh"]["extent"] == list(PyFlowConfig().mesh.extent)
