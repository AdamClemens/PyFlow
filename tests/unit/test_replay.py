"""Unit tests for pyflow.replay (TASK-046, Stage 8, Recording &
Playback) -- windowed materialization: given a checkpoint directory and
a target frame range, re-simulate forward and produce dense, in-memory
per-frame field data for just that range. No rendering import -- see
that module's own docstring.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from pyflow.checkpoint import read_checkpoint, restore_simulation_state
from pyflow.engine.collocated_field import CollocatedField
from pyflow.recording import record
from pyflow.replay import (
    MaterializedWindow,
    NoCheckpointBeforeFrameError,
    find_checkpoint_at_or_before,
    materialize_or_load_window,
    materialize_window,
    read_materialized_window,
    write_materialized_window,
)
from pyflow.simulation_run import advance_simulation_state

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


@pytest.fixture
def checkpoints_dir(tmp_path: Path) -> Path:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_DECLARED_FIELD_CONFIG)
    output_dir = tmp_path / "checkpoints"
    record(config_file, max_frames=20, output_dir=output_dir, checkpoint_interval=5)
    return output_dir


def test_find_checkpoint_at_or_before_picks_the_newest_qualifying_one(
    checkpoints_dir: Path,
) -> None:
    assert find_checkpoint_at_or_before(checkpoints_dir, 12).name == "checkpoint_00000010.pt"
    assert find_checkpoint_at_or_before(checkpoints_dir, 10).name == "checkpoint_00000010.pt"
    assert find_checkpoint_at_or_before(checkpoints_dir, 0).name == "checkpoint_00000000.pt"


def test_find_checkpoint_at_or_before_raises_when_none_qualify(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(NoCheckpointBeforeFrameError):
        find_checkpoint_at_or_before(empty_dir, 5)


def test_find_checkpoint_at_or_before_ignores_non_checkpoint_files(
    checkpoints_dir: Path,
) -> None:
    (checkpoints_dir / "notes.txt").write_text("not a checkpoint")

    assert find_checkpoint_at_or_before(checkpoints_dir, 20).name == "checkpoint_00000020.pt"


def test_materialize_window_produces_one_frame_per_step_in_range(
    checkpoints_dir: Path,
) -> None:
    window = materialize_window(checkpoints_dir, from_frame=6, to_frame=9)

    assert window.from_frame == 6
    assert window.to_frame == 9
    assert len(window.frames) == 4  # frames 6, 7, 8, 9
    assert set(window.frames[0]) == {"smoke"}


def test_materialize_window_starting_exactly_on_a_checkpoint(checkpoints_dir: Path) -> None:
    window = materialize_window(checkpoints_dir, from_frame=5, to_frame=5)

    assert len(window.frames) == 1


def test_materialize_window_rejects_a_non_positive_range(checkpoints_dir: Path) -> None:
    with pytest.raises(ValueError, match="from_frame"):
        materialize_window(checkpoints_dir, from_frame=9, to_frame=6)


def test_materialize_window_matches_a_directly_stepped_trajectory(
    checkpoints_dir: Path,
) -> None:
    """The determinism claim this mechanism depends on, checked directly
    against *every* materialized frame, not only the last one -- and from
    a `from_frame` (6) that is deliberately not itself a checkpoint frame
    (the nearest one is at 5), so the fast-forward/discard step actually
    runs. A first draft of this test checked only `window.frames[-1]`
    from a `from_frame` that already equalled a checkpoint's own frame
    count (10), which made the discard loop a no-op either way --
    confirmed blind by a deliberate off-by-one mutation there (`range(
    from_frame - checkpoint.frame_count - 1)`): every test in this file
    still passed, because none checked a specific materialized frame's
    *value* against an independently-computed one. This test's own
    from_frame/per-frame check is what catches that class of bug.
    """
    window = materialize_window(checkpoints_dir, from_frame=6, to_frame=9)
    control = read_checkpoint(checkpoints_dir / "checkpoint_00000000.pt")

    _mesh, numerics, state = restore_simulation_state(control)
    expected: list[torch.Tensor] = []
    for frame in range(1, 10):  # step to frame 9, recording frames 6, 7, 8, 9 as we pass them
        state = advance_simulation_state(state, numerics, control.config.numerics.timestep)
        if frame >= 6:
            smoke = state.fields["smoke"]
            assert isinstance(smoke, CollocatedField)
            expected.append(smoke.values.clone())

    assert len(expected) == len(window.frames) == 4
    for materialized, direct in zip(window.frames, expected, strict=True):
        torch.testing.assert_close(materialized["smoke"], direct, rtol=0, atol=0)


def test_write_and_read_materialized_window_round_trips(
    checkpoints_dir: Path, tmp_path: Path
) -> None:
    window = materialize_window(checkpoints_dir, from_frame=6, to_frame=8)
    path = tmp_path / "window.pt"

    write_materialized_window(window, path)
    read_back = read_materialized_window(path)

    assert read_back.from_frame == window.from_frame
    assert read_back.to_frame == window.to_frame
    assert len(read_back.frames) == len(window.frames)
    for original, restored in zip(window.frames, read_back.frames, strict=True):
        torch.testing.assert_close(restored["smoke"], original["smoke"], rtol=0, atol=0)


def test_materialize_or_load_window_writes_a_cache_when_given_a_cache_dir(
    checkpoints_dir: Path, tmp_path: Path
) -> None:
    cache_dir = tmp_path / "cache"

    materialize_or_load_window(checkpoints_dir, from_frame=6, to_frame=9, cache_dir=cache_dir)

    assert (cache_dir / "window_00000006_00000009.pt").is_file()


def test_materialize_or_load_window_reuses_an_existing_cache_without_recomputing(
    checkpoints_dir: Path, tmp_path: Path
) -> None:
    cache_dir = tmp_path / "cache"
    materialize_or_load_window(checkpoints_dir, from_frame=6, to_frame=9, cache_dir=cache_dir)

    # Deleting every checkpoint proves the second call could not have
    # recomputed anything -- it must have come from the cache.
    for checkpoint_file in checkpoints_dir.glob("checkpoint_*.pt"):
        checkpoint_file.unlink()

    window = materialize_or_load_window(
        checkpoints_dir, from_frame=6, to_frame=9, cache_dir=cache_dir
    )

    assert len(window.frames) == 4


def test_materialize_or_load_window_with_no_cache_dir_recomputes_every_time(
    checkpoints_dir: Path,
) -> None:
    window = materialize_or_load_window(checkpoints_dir, from_frame=6, to_frame=9)

    assert isinstance(window, MaterializedWindow)
    assert len(window.frames) == 4
