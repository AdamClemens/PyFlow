"""Unit tests for pyflow.recording (TASK-045, Stage 8, Recording &
Playback) -- the headless, no-`rendering`-import loop that writes
periodic checkpoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pyflow.checkpoint import read_checkpoint
from pyflow.recording import NothingToRecordError, record

_DECLARED_FIELD_CONFIG = """\
mesh:
  extent: [4, 4]
  spacing: [0.25, 0.25]

numerics:
  timestep: 0.01
  boundary_conditions:
    north:
      type: periodic
    south:
      type: periodic
    east:
      type: periodic
    west:
      type: periodic

fields:
  - name: smoke
    initial_condition: sinusoidal_mode
"""

_VELOCITY_ONLY_CONFIG = """\
mesh:
  extent: [4, 4]
  spacing: [0.25, 0.25]

numerics:
  timestep: 0.01
  boundary_conditions:
    north:
      type: dirichlet
      field_values:
        velocity.0: 1.0
        velocity.1: 0.0
    south:
      type: dirichlet
    east:
      type: dirichlet
    west:
      type: dirichlet

simulation:
  velocity_solved: true

fluid:
  viscosity: 0.01
"""

_STATIC_CONFIG = """\
mesh:
  extent: [4, 4]
  spacing: [0.25, 0.25]
"""


def test_record_writes_checkpoints_at_expected_frames_for_a_declared_field(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"

    result = record(config_file, max_frames=10, output_dir=output_dir, checkpoint_interval=5)

    assert result.checkpoint_frames == [0, 5, 10]
    assert result.final_frame_count == 10
    assert result.output_dir == output_dir
    checkpoint = read_checkpoint(output_dir / "checkpoint_00000010.pt")
    assert checkpoint.frame_count == 10
    assert checkpoint.fields["smoke"].shape == (16,)  # 4x4 mesh


def test_record_writes_checkpoints_for_a_velocity_only_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_VELOCITY_ONLY_CONFIG)
    output_dir = tmp_path / "checkpoints"

    result = record(config_file, max_frames=6, output_dir=output_dir, checkpoint_interval=3)

    assert result.checkpoint_frames == [0, 3, 6]
    checkpoint = read_checkpoint(output_dir / "checkpoint_00000000.pt")
    assert set(checkpoint.fields) == {"velocity.0", "velocity.1"}


def test_record_raises_for_a_config_with_nothing_to_step(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_STATIC_CONFIG)

    with pytest.raises(NothingToRecordError):
        record(config_file, max_frames=5, output_dir=tmp_path / "checkpoints")


def test_record_always_writes_a_final_checkpoint_even_off_interval(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"

    result = record(config_file, max_frames=7, output_dir=output_dir, checkpoint_interval=5)

    assert result.checkpoint_frames == [0, 5, 7]


def test_record_falls_back_to_config_recording_section_when_not_overridden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # `output_dir` isn't overridden here, so it resolves relative to the
    # current working directory (the same relative-path convention every
    # other path-like config value in this schema already follows) --
    # `monkeypatch.chdir` keeps that resolution inside `tmp_path` rather
    # than writing into the real repository while this test runs.
    monkeypatch.chdir(tmp_path)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        _DECLARED_FIELD_CONFIG + "\nrecording:\n  output_dir: from_config\n"
        "  checkpoint_interval: 4\n"
    )

    result = record(config_file, max_frames=8)

    assert result.output_dir == Path("from_config")
    assert result.checkpoint_frames == [0, 4, 8]
