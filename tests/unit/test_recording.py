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


# -- retention (TASK-049, Stage 8 reopening, added 2026-09-09) -----------


def _checkpoint_frames_on_disk(output_dir: Path) -> set[int]:
    return {int(p.stem.removeprefix("checkpoint_")) for p in output_dir.glob("checkpoint_*.pt")}


def test_record_without_a_cap_keeps_every_checkpoint(tmp_path: Path) -> None:
    """Unset (the default) changes nothing for an existing config -- no
    pruning at all, exactly today's behaviour.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"

    record(config_file, max_frames=20, output_dir=output_dir, checkpoint_interval=5)

    assert _checkpoint_frames_on_disk(output_dir) == {0, 5, 10, 15, 20}


def test_record_prunes_checkpoints_beyond_the_retention_cap(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"

    record(
        config_file,
        max_frames=20,
        output_dir=output_dir,
        checkpoint_interval=5,
        max_checkpoints_retained=2,
    )

    # Frame 0 plus the newest two non-zero checkpoints (15, 20) -- 5 and
    # 10 pruned.
    assert _checkpoint_frames_on_disk(output_dir) == {0, 15, 20}


def test_record_retention_cap_never_prunes_frame_zero(tmp_path: Path) -> None:
    """Frame 0 is excluded from the retention *count* itself, not merely
    old enough to survive by coincidence: with five non-zero checkpoints
    and a cap of five, "keep the newest N files overall" (the wrong
    reading) would drop frame 0 -- the oldest of six -- while excluding
    it from the count keeps all six. Chosen so a broken implementation
    and the correct one disagree, not just so frame 0 happens to survive
    either way.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"

    record(
        config_file,
        max_frames=25,
        output_dir=output_dir,
        checkpoint_interval=5,
        max_checkpoints_retained=5,
    )

    assert _checkpoint_frames_on_disk(output_dir) == {0, 5, 10, 15, 20, 25}


def test_resume_prunes_across_the_whole_directory_not_only_what_it_wrote(
    tmp_path: Path,
) -> None:
    """The cap applies to everything on disk, including checkpoints an
    earlier `record` call wrote -- not only the frames this particular
    `resume` call writes.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=10, output_dir=output_dir, checkpoint_interval=5)

    resume(
        output_dir / "checkpoint_00000010.pt",
        max_frames=20,
        checkpoint_interval=5,
        max_checkpoints_retained=2,
    )

    assert _checkpoint_frames_on_disk(output_dir) == {0, 15, 20}


def test_load_config_max_checkpoints_retained_is_used_when_not_overridden(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG + "\nrecording:\n  max_checkpoints_retained: 1\n")
    output_dir = tmp_path / "checkpoints"

    record(config_file, max_frames=15, output_dir=output_dir, checkpoint_interval=5)

    assert _checkpoint_frames_on_disk(output_dir) == {0, 15}


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


def test_resume_needs_no_config_path_at_all_when_resuming_from_a_checkpoint(
    tmp_path: Path,
) -> None:
    """A checkpoint is self-contained (`checkpoint.py`'s own docstring),
    so resuming from one never needs a `config_path` -- checked here by
    calling `resume` with only a checkpoint path and confirming it works,
    not merely by `config_path` being optional in the signature.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=3, output_dir=output_dir, checkpoint_interval=3)
    config_file.unlink()  # the original config is gone; resume must not need it

    result = resume(output_dir / "checkpoint_00000003.pt", max_frames=6, checkpoint_interval=3)

    assert result.checkpoint_frames == [6]


def test_resume_from_a_config_path_behaves_exactly_like_record(tmp_path: Path) -> None:
    """`resume(config_path=...)` (added at a user's direct request: "do
    pyflow resume from a config file and have it start from the first
    frame") is a pure alternate entry point into the same recording --
    given a config instead of a checkpoint, there is nothing yet to
    resume *from*, so it starts at frame 0 exactly like `record` does.
    Checked by comparing against a real `record()` call on the same
    config, not merely asserting `resume` runs without raising -- the two
    must produce byte-identical output, not just superficially similar
    output.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    recorded_dir = tmp_path / "recorded"
    record(config_file, max_frames=6, output_dir=recorded_dir, checkpoint_interval=3)

    resumed_dir = tmp_path / "resumed"
    result = resume(
        config_path=config_file, max_frames=6, output_dir=resumed_dir, checkpoint_interval=3
    )

    assert result.checkpoint_frames == [0, 3, 6]
    assert result.output_dir == resumed_dir
    recorded = read_checkpoint(recorded_dir / "checkpoint_00000006.pt")
    resumed = read_checkpoint(resumed_dir / "checkpoint_00000006.pt")
    torch.testing.assert_close(resumed.fields["smoke"], recorded.fields["smoke"], rtol=0, atol=0)


def test_resume_rejects_neither_checkpoint_path_nor_config_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="checkpoint_path.*config_path"):
        resume(max_frames=6)


def test_resume_rejects_both_checkpoint_path_and_config_path(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=3, output_dir=output_dir, checkpoint_interval=3)

    with pytest.raises(ValueError, match="checkpoint_path.*config_path"):
        resume(output_dir / "checkpoint_00000003.pt", config_path=config_file, max_frames=6)
