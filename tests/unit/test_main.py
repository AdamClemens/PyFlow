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
from types import SimpleNamespace
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


def test_top_level_help_describes_current_capabilities(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The top-level help text must reflect what PyFlow can actually do
    (`src/pyflow/CLAUDE.md`'s "help text must stay current" rule) -- it
    previously described the CLI as a "Stage 0 skeleton -- no simulation
    functionality yet" long after real numerics and golden demos landed,
    and never mentioned `--config` or how to run one at all, since
    `--config` lives on the `run` subcommand's own help and argparse
    does not surface a subcommand's flags in the top-level listing.
    """
    main([])
    captured = capsys.readouterr()
    assert "Stage 0" not in captured.out
    assert "--config" in captured.out
    assert "examples/golden-demos" in captured.out
    assert "--demos" in captured.out
    assert "record" in captured.out
    assert "resume" in captured.out
    assert "play" in captured.out


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


def test_run_demos_bare_lists_demos_and_does_not_bootstrap(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(["run", "--demos"])

    mock_bootstrap.assert_not_called()
    captured = capsys.readouterr()
    assert "1  empty_window" in captured.out
    assert "lid_driven_cavity" in captured.out


def test_run_demos_by_number_dispatches_to_bootstrap_with_resolved_config() -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(["run", "--demos", "1"])

    mock_bootstrap.assert_called_once_with(
        Path("examples/golden-demos/empty_window.yaml"), max_frames=None, backend=None
    )


def test_run_demos_by_name_dispatches_to_bootstrap_with_resolved_config() -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        main(["run", "--demos", "lid_driven_cavity"])

    mock_bootstrap.assert_called_once_with(
        Path("examples/golden-demos/lid_driven_cavity.yaml"), max_frames=None, backend=None
    )


def test_run_demos_rejects_unknown_identifier(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("pyflow.__main__.bootstrap") as mock_bootstrap:
        with pytest.raises(SystemExit):
            main(["run", "--demos", "not_a_real_demo"])

    mock_bootstrap.assert_not_called()
    assert "not_a_real_demo" in capsys.readouterr().err


def test_run_rejects_config_and_demos_together(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["run", "--config", "some-config.yaml", "--demos", "1"])

    assert "not allowed with argument" in capsys.readouterr().err


def test_record_dispatches_to_record_with_parsed_args() -> None:
    with patch("pyflow.__main__.record") as mock_record:
        mock_record.return_value = SimpleNamespace(
            checkpoint_frames=[0, 5, 10], output_dir=Path("out")
        )
        main(
            [
                "record",
                "--config",
                "some-config.yaml",
                "--max-frames",
                "10",
                "--output-dir",
                "out",
                "--checkpoint-interval",
                "5",
                "--max-checkpoints-retained",
                "2",
            ]
        )

    mock_record.assert_called_once_with(
        Path("some-config.yaml"),
        max_frames=10,
        output_dir=Path("out"),
        checkpoint_interval=5,
        max_checkpoints_retained=2,
    )


def test_record_output_dir_and_checkpoint_interval_default_to_none(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with patch("pyflow.__main__.record") as mock_record:
        mock_record.return_value = SimpleNamespace(checkpoint_frames=[0, 3], output_dir=Path("c"))
        main(["record", "--config", "some-config.yaml", "--max-frames", "3"])

    mock_record.assert_called_once_with(
        Path("some-config.yaml"),
        max_frames=3,
        output_dir=None,
        checkpoint_interval=None,
        max_checkpoints_retained=None,
    )


def test_record_requires_config(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["record", "--max-frames", "5"])

    assert "--config" in capsys.readouterr().err


def test_record_requires_max_frames(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["record", "--config", "some-config.yaml"])

    assert "--max-frames" in capsys.readouterr().err


def test_record_prints_a_summary(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("pyflow.__main__.record") as mock_record:
        mock_record.return_value = SimpleNamespace(
            checkpoint_frames=[0, 5, 10], output_dir=Path("checkpoints")
        )
        main(["record", "--config", "some-config.yaml", "--max-frames", "10"])

    captured = capsys.readouterr()
    assert "3" in captured.out
    assert "checkpoints" in captured.out


def test_resume_dispatches_to_resume_with_parsed_args() -> None:
    with patch("pyflow.__main__.resume") as mock_resume:
        mock_resume.return_value = SimpleNamespace(
            checkpoint_frames=[9, 12], output_dir=Path("out")
        )
        main(
            [
                "resume",
                "--checkpoint",
                "checkpoints/checkpoint_00000006.pt",
                "--max-frames",
                "12",
                "--output-dir",
                "out",
                "--checkpoint-interval",
                "3",
                "--max-checkpoints-retained",
                "2",
            ]
        )

    mock_resume.assert_called_once_with(
        Path("checkpoints/checkpoint_00000006.pt"),
        config_path=None,
        max_frames=12,
        output_dir=Path("out"),
        checkpoint_interval=3,
        max_checkpoints_retained=2,
    )


def test_resume_output_dir_and_checkpoint_interval_default_to_none() -> None:
    with patch("pyflow.__main__.resume") as mock_resume:
        mock_resume.return_value = SimpleNamespace(checkpoint_frames=[9], output_dir=Path("c"))
        main(["resume", "--checkpoint", "checkpoints/checkpoint_00000006.pt", "--max-frames", "9"])

    mock_resume.assert_called_once_with(
        Path("checkpoints/checkpoint_00000006.pt"),
        config_path=None,
        max_frames=9,
        output_dir=None,
        checkpoint_interval=None,
        max_checkpoints_retained=None,
    )


def test_resume_dispatches_with_config_instead_of_checkpoint() -> None:
    """`--config`, added at a user's direct request for `pyflow resume`
    to be able to start a brand new recording at frame 0 -- a mutually
    exclusive alternative to `--checkpoint`, not a way to pass both.
    """
    with patch("pyflow.__main__.resume") as mock_resume:
        mock_resume.return_value = SimpleNamespace(checkpoint_frames=[0, 9], output_dir=Path("out"))
        main(["resume", "--config", "some-config.yaml", "--max-frames", "9", "--output-dir", "out"])

    mock_resume.assert_called_once_with(
        None,
        config_path=Path("some-config.yaml"),
        max_frames=9,
        output_dir=Path("out"),
        checkpoint_interval=None,
        max_checkpoints_retained=None,
    )


def test_resume_rejects_checkpoint_and_config_together(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "resume",
                "--checkpoint",
                "checkpoints/checkpoint_00000006.pt",
                "--config",
                "some-config.yaml",
                "--max-frames",
                "9",
            ]
        )

    assert "not allowed with argument" in capsys.readouterr().err


def test_resume_requires_checkpoint_or_config(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["resume", "--max-frames", "9"])

    assert "--checkpoint" in capsys.readouterr().err


def test_resume_requires_max_frames(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["resume", "--checkpoint", "checkpoints/checkpoint_00000006.pt"])

    assert "--max-frames" in capsys.readouterr().err


def test_resume_prints_a_summary(capsys: pytest.CaptureFixture[str]) -> None:
    with patch("pyflow.__main__.resume") as mock_resume:
        mock_resume.return_value = SimpleNamespace(
            checkpoint_frames=[9, 12], output_dir=Path("checkpoints")
        )
        main(["resume", "--checkpoint", "checkpoints/checkpoint_00000006.pt", "--max-frames", "12"])

    captured = capsys.readouterr()
    assert "2" in captured.out
    assert "checkpoints" in captured.out


def test_play_dispatches_to_play_with_parsed_args() -> None:
    with patch("pyflow.__main__.play") as mock_play:
        main(
            [
                "play",
                "--checkpoints-dir",
                "checkpoints",
                "--from-frame",
                "10",
                "--to-frame",
                "100",
                "--cache",
                "cache",
                "--backend",
                "offscreen",
                "--max-frames",
                "5",
            ]
        )

    mock_play.assert_called_once_with(
        Path("checkpoints"),
        from_frame=10,
        to_frame=100,
        cache_dir=Path("cache"),
        backend="offscreen",
        max_frames=5,
    )


def test_play_from_frame_defaults_to_zero() -> None:
    with patch("pyflow.__main__.play") as mock_play:
        main(["play", "--checkpoints-dir", "checkpoints", "--to-frame", "100"])

    mock_play.assert_called_once_with(
        Path("checkpoints"),
        from_frame=0,
        to_frame=100,
        cache_dir=None,
        backend=None,
        max_frames=None,
    )


def test_play_requires_checkpoints_dir(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["play", "--to-frame", "100"])

    assert "--checkpoints-dir" in capsys.readouterr().err


def test_play_requires_to_frame(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["play", "--checkpoints-dir", "checkpoints"])

    assert "--to-frame" in capsys.readouterr().err


def test_play_rejects_invalid_backend(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "play",
                "--checkpoints-dir",
                "checkpoints",
                "--to-frame",
                "100",
                "--backend",
                "not-a-backend",
            ]
        )

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
            "show_title": True,
            "show_stats": True,
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
            "field_label": None,
            "vector_label": None,
            "panels": [],
        },
        "fields": [],
        "simulation": {
            "velocity_pattern": None,
            "velocity": [1.0, 0.0],
            "velocity_solved": False,
        },
        "fluid": {
            "viscosity": 1.0,
            "diffusion_coefficient": 1.0,
            "gravity": [0.0, -9.81],
        },
        "numerics": {
            "advection": "first_order_upwind",
            "diffusion": "central_difference",
            "time_integration": "rk4",
            "timestep": 0.01,
            "linear_solver": "conjugate_gradient",
            "linear_solver_tolerance": 1e-6,
            "linear_solver_max_iterations": 1000,
            "pressure_coupling": "piso",
            "pressure_correction_tolerance": 1e-6,
            "pressure_correction_max_iterations": 50,
            "source_term": "none",
            "boundary_conditions": {
                "north": {
                    "type": "dirichlet",
                    "velocity": 0.0,
                    "pressure": None,
                    "scalar_value": 0.0,
                    "scalar_gradient": 0.0,
                    "field_values": {},
                    "field_gradients": {},
                },
                "south": {
                    "type": "dirichlet",
                    "velocity": 0.0,
                    "pressure": None,
                    "scalar_value": 0.0,
                    "scalar_gradient": 0.0,
                    "field_values": {},
                    "field_gradients": {},
                },
                "east": {
                    "type": "dirichlet",
                    "velocity": 0.0,
                    "pressure": None,
                    "scalar_value": 0.0,
                    "scalar_gradient": 0.0,
                    "field_values": {},
                    "field_gradients": {},
                },
                "west": {
                    "type": "dirichlet",
                    "velocity": 0.0,
                    "pressure": None,
                    "scalar_value": 0.0,
                    "scalar_gradient": 0.0,
                    "field_values": {},
                    "field_gradients": {},
                },
            },
        },
        "units": {
            "length_unit": "m",
            "length_scale": 1.0,
            "time_unit": "s",
            "time_scale": 1.0,
        },
        "recording": {
            "output_dir": "checkpoints",
            "checkpoint_interval": 100,
            "max_checkpoints_retained": None,
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
    assert list(written.keys()) == [
        "logging",
        "rendering",
        "mesh",
        "field_display",
        "fields",
        "simulation",
        "fluid",
        "numerics",
        "units",
        "recording",
    ]
    assert written["mesh"]["extent"] == list(PyFlowConfig().mesh.extent)
