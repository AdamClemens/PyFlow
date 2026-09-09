"""Unit tests for pyflow.checkpoint (TASK-045, Stage 8, Recording &
Playback) -- the write/read round trip a checkpoint's own file format
must preserve exactly, since `recording.py`'s deterministic replay
depends on it being lossless.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
import torch

from pyflow.checkpoint import (
    UnsupportedCheckpointVersionError,
    list_checkpoints,
    read_checkpoint,
    write_checkpoint,
)
from pyflow.configuration import PyFlowConfig
from pyflow.configuration.schema import FieldConfig, MeshConfig
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField


def _non_default_config() -> PyFlowConfig:
    # Tuple-typed fields, a nested list section -- a config a naive
    # round trip (e.g. losing tuple-ness) would visibly corrupt.
    config = PyFlowConfig(
        mesh=MeshConfig(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(4, 3)),
        fields=[FieldConfig(name="smoke", initial_condition="gaussian_blob")],
    )
    config.validate()
    return config


def test_write_read_round_trips_config_and_fields(tmp_path: Path) -> None:
    config = _non_default_config()
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    field_a = ScalarField(mesh, "smoke", initial_value=lambda x, y: x + y)
    field_b = ScalarField(mesh, "velocity.0", initial_value=lambda x, y: x * 2)
    path = tmp_path / "checkpoint_00000010.pt"

    write_checkpoint(
        path, frame_count=10, config=config, fields={"smoke": field_a, "velocity.0": field_b}
    )
    loaded = read_checkpoint(path)

    assert loaded.frame_count == 10
    assert dataclasses.asdict(loaded.config) == dataclasses.asdict(config)
    torch.testing.assert_close(loaded.fields["smoke"], field_a.values, rtol=0, atol=0)
    torch.testing.assert_close(loaded.fields["velocity.0"], field_b.values, rtol=0, atol=0)


def test_write_checkpoint_stores_a_clone_not_a_reference(tmp_path: Path) -> None:
    """If a field's own tensor mutates after `write_checkpoint` returns,
    the checkpoint's own stored data must not change with it -- the
    whole point of persisting state at a moment in time.
    """
    config = _non_default_config()
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    field = ScalarField(mesh, "smoke", initial_value=lambda x, y: 1.0)
    path = tmp_path / "checkpoint_00000000.pt"

    write_checkpoint(path, frame_count=0, config=config, fields={"smoke": field})
    field.values[:] = 999.0
    loaded = read_checkpoint(path)

    assert not torch.allclose(loaded.fields["smoke"], field.values)


def test_read_checkpoint_rejects_unknown_schema_version(tmp_path: Path) -> None:
    path = tmp_path / "bad.pt"
    torch.save({"schema_version": 999, "frame_count": 0, "config": {}, "fields": {}}, path)

    with pytest.raises(UnsupportedCheckpointVersionError):
        read_checkpoint(path)


def test_list_checkpoints_finds_every_checkpoint_file_by_frame_number(tmp_path: Path) -> None:
    """Factored out of `replay.py`'s own private glob/regex (TASK-046)
    so `recording.py`'s new retention pruning (TASK-049) and
    `replay.find_checkpoint_at_or_before` read one implementation of
    "what checkpoints exist here", not two that could drift apart.
    """
    config = _non_default_config()
    for frame in (0, 5, 10):
        mesh = StructuredCartesianMesh.from_config(config.mesh)
        field = ScalarField(mesh, "smoke", initial_value=lambda x, y: 1.0)
        write_checkpoint(
            tmp_path / f"checkpoint_{frame:08d}.pt",
            frame_count=frame,
            config=config,
            fields={"smoke": field},
        )
    (tmp_path / "not_a_checkpoint.pt").write_text("ignore me")

    found = list_checkpoints(tmp_path)

    assert sorted(found) == [
        (0, tmp_path / "checkpoint_00000000.pt"),
        (5, tmp_path / "checkpoint_00000005.pt"),
        (10, tmp_path / "checkpoint_00000010.pt"),
    ]


def test_list_checkpoints_is_empty_for_a_directory_with_none(tmp_path: Path) -> None:
    assert list_checkpoints(tmp_path) == []


def test_restore_simulation_state_reconstructs_a_resumable_state_for_a_passive_config(
    tmp_path: Path,
) -> None:
    """`Checkpoint.fields` alone is not enough to resume from for a
    `"passive"`-mode run: `SimulationState.velocity_field` (the
    prescribed, never-checkpointed velocity a declared field self-
    advects against) has to be re-derived from the checkpoint's own
    embedded config, not read back from disk -- there is nothing on disk
    to read it from.
    """
    from pyflow.checkpoint import restore_simulation_state

    config = PyFlowConfig(
        mesh=MeshConfig(extent=(3, 2)),
        fields=[FieldConfig(name="smoke", initial_condition="gaussian_blob")],
    )
    config.validate()
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    field = ScalarField(mesh, "smoke", initial_value=lambda x, y: x + y)
    path = tmp_path / "checkpoint_00000005.pt"
    write_checkpoint(path, frame_count=5, config=config, fields={"smoke": field})

    checkpoint = read_checkpoint(path)
    restored_mesh, restored_numerics, restored_state = restore_simulation_state(checkpoint)

    assert restored_state.mode == "passive"
    assert restored_state.velocity_field is not None
    assert restored_state.velocity_field.mesh is restored_mesh
    restored_smoke = restored_state.fields["smoke"]
    assert isinstance(restored_smoke, ScalarField)
    torch.testing.assert_close(restored_smoke.values, field.values, rtol=0, atol=0)
    assert restored_numerics.names  # a real assembled numerics, not a stub


def test_restore_simulation_state_reconstructs_solved_mode_with_no_prescribed_velocity(
    tmp_path: Path,
) -> None:
    from pyflow.checkpoint import restore_simulation_state
    from pyflow.configuration.schema import SimulationConfig
    from pyflow.engine.vector_field import VectorField

    config = PyFlowConfig(
        mesh=MeshConfig(extent=(3, 2)), simulation=SimulationConfig(velocity_solved=True)
    )
    config.validate()
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    velocity_field = VectorField(
        mesh, "velocity", num_components=2, initial_value=lambda x, y: (x, y)
    )
    components = {c.name: c for c in velocity_field.decompose()}
    path = tmp_path / "checkpoint_00000003.pt"
    write_checkpoint(path, frame_count=3, config=config, fields=components)

    checkpoint = read_checkpoint(path)
    _mesh, _numerics, restored_state = restore_simulation_state(checkpoint)

    assert restored_state.mode == "solved"
    assert restored_state.velocity_field is None
    assert set(restored_state.fields) == {"velocity.0", "velocity.1"}
