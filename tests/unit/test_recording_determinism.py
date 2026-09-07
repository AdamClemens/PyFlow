"""The one genuinely new physical/numerical claim TASK-045 makes (Stage 8,
Recording & Playback): resuming from a checkpoint reproduces the same
trajectory as an uninterrupted run, bit-identically. Mirrors `tests/
features/navier_stokes_timestep.feature`'s own determinism scenario style
(`torch.testing.assert_close(..., rtol=0, atol=0)`), extended across a
real serialize/deserialize/resume round trip -- new ground nothing before
this task verified (that scenario only proves two in-process,
never-serialized runs agree).

Deliberately plain pytest, not a `.feature` file -- see `recording.py`'s
own module docstring and TASK-045's own roadmap entry for why: this is a
serialization-fidelity/mechanism claim, not a new physical prediction,
the same category Stage 7's rendering-plumbing work was exempted for.
"""

from __future__ import annotations

from pathlib import Path

import torch

from pyflow.checkpoint import read_checkpoint, restore_simulation_state
from pyflow.configuration import load_config
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.recording import record
from pyflow.simulation_run import (
    SimulationState,
    advance_simulation_state,
    assembled_numerics_for,
    build_simulation_state,
)

_CONFIG_TEXT = """\
mesh:
  origin: [0.5, -1.0]
  extent: [5, 4]
  spacing: [0.2, 0.3]

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

_CHECKPOINT_FRAME = 12
_FINAL_FRAME = 20


def _smoke_values(state: SimulationState) -> torch.Tensor:
    smoke = state.fields["smoke"]
    assert isinstance(smoke, ScalarField)
    return smoke.values.clone()


def _control_trajectory(config_file: Path) -> torch.Tensor:
    """An uninterrupted run to `_FINAL_FRAME`, no recording at all."""
    config = load_config(config_file)
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    numerics = assembled_numerics_for(config)

    built_state = build_simulation_state(mesh, config)
    assert built_state is not None
    state: SimulationState = built_state
    for _ in range(_FINAL_FRAME):
        state = advance_simulation_state(state, numerics, config.numerics.timestep)
    return _smoke_values(state)


def _resumed_trajectory(config_file: Path, output_dir: Path) -> torch.Tensor:
    """A checkpointed run: record to `_CHECKPOINT_FRAME`, reload, resume
    stepping to `_FINAL_FRAME`.
    """
    record(
        config_file,
        max_frames=_CHECKPOINT_FRAME,
        output_dir=output_dir,
        checkpoint_interval=_CHECKPOINT_FRAME,
    )
    checkpoint = read_checkpoint(output_dir / f"checkpoint_{_CHECKPOINT_FRAME:08d}.pt")
    _mesh, numerics, state = restore_simulation_state(checkpoint)
    for _ in range(_FINAL_FRAME - _CHECKPOINT_FRAME):
        state = advance_simulation_state(state, numerics, checkpoint.config.numerics.timestep)
    return _smoke_values(state)


def test_resuming_from_a_checkpoint_reproduces_an_uninterrupted_runs_trajectory(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_CONFIG_TEXT)

    control = _control_trajectory(config_file)
    resumed = _resumed_trajectory(config_file, tmp_path / "checkpoints")

    torch.testing.assert_close(resumed, control, rtol=0, atol=0)
