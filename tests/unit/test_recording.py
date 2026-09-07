"""Unit tests for pyflow.recording (TASK-045, Stage 8, Recording &
Playback) -- the headless, no-`rendering`-import loop that writes
periodic checkpoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from pyflow.checkpoint import read_checkpoint
from pyflow.recording import NothingToRecordError, NothingToResumeError, record, resume

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


# -- resume (extends TASK-045's own recording -- not replay or playback) --


def test_resume_continues_from_a_checkpoint_and_writes_only_new_checkpoints(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=6, output_dir=output_dir, checkpoint_interval=3)

    result = resume(output_dir / "checkpoint_00000006.pt", max_frames=12, checkpoint_interval=3)

    # Not [0, 3, 6, 9, 12] -- frames up to and including 6 already exist
    # on disk from the `record()` call above; resuming must not re-write
    # them (`checkpoint_frames` is only what *this* call wrote).
    assert result.checkpoint_frames == [9, 12]
    assert result.final_frame_count == 12
    checkpoint = read_checkpoint(output_dir / "checkpoint_00000012.pt")
    assert checkpoint.frame_count == 12


def test_resume_produces_the_same_final_checkpoint_as_an_uninterrupted_record(
    tmp_path: Path,
) -> None:
    """The invariant a checkpoint-then-resume pipeline exists to
    guarantee: recording straight to frame 12 and recording to frame 6
    then resuming to frame 12 must agree exactly at frame 12 -- the same
    claim `tests/unit/test_recording_determinism.py` checks at the
    `SimulationState` level, pinned here at the level a CLI user actually
    observes (two checkpoint files).
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)

    uninterrupted_dir = tmp_path / "uninterrupted"
    record(config_file, max_frames=12, output_dir=uninterrupted_dir, checkpoint_interval=12)
    control = read_checkpoint(uninterrupted_dir / "checkpoint_00000012.pt")

    resumed_dir = tmp_path / "resumed"
    record(config_file, max_frames=6, output_dir=resumed_dir, checkpoint_interval=6)
    resume(resumed_dir / "checkpoint_00000006.pt", max_frames=12, checkpoint_interval=6)
    resumed = read_checkpoint(resumed_dir / "checkpoint_00000012.pt")

    torch.testing.assert_close(resumed.fields["smoke"], control.fields["smoke"], rtol=0, atol=0)


def test_resume_defaults_output_dir_to_the_checkpoints_own_directory(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=6, output_dir=output_dir, checkpoint_interval=6)

    result = resume(output_dir / "checkpoint_00000006.pt", max_frames=9, checkpoint_interval=9)

    assert result.output_dir == output_dir
    assert (output_dir / "checkpoint_00000009.pt").is_file()


def test_resume_falls_back_to_the_checkpoints_own_recording_config_for_interval(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG + "\nrecording:\n  checkpoint_interval: 4\n")
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=4, output_dir=output_dir)

    result = resume(output_dir / "checkpoint_00000004.pt", max_frames=12)

    assert result.checkpoint_frames == [8, 12]


def test_resume_rejects_max_frames_not_past_the_checkpoint(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=6, output_dir=output_dir, checkpoint_interval=6)

    with pytest.raises(NothingToResumeError):
        resume(output_dir / "checkpoint_00000006.pt", max_frames=6)

    with pytest.raises(NothingToResumeError):
        resume(output_dir / "checkpoint_00000006.pt", max_frames=3)


def test_resume_needs_no_config_path_at_all(tmp_path: Path) -> None:
    """The property `pyflow resume`'s own CLI leans on for having no
    `--config` flag: a checkpoint is self-contained
    (`checkpoint.py`'s own docstring), so `resume` never takes one --
    checked here by calling it with only a checkpoint path and confirming
    it works, not merely by the function signature lacking the parameter.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=3, output_dir=output_dir, checkpoint_interval=3)
    config_file.unlink()  # the original config is gone; resume must not need it

    result = resume(output_dir / "checkpoint_00000003.pt", max_frames=6, checkpoint_interval=3)

    assert result.checkpoint_frames == [6]
