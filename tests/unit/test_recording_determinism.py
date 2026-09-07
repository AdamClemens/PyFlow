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

import dataclasses
from pathlib import Path

import torch

from pyflow.checkpoint import read_checkpoint, restore_simulation_state
from pyflow.configuration import config_from_dict, load_config
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

# `_CONFIG_TEXT` above never sets `simulation.velocity_pattern`, so its
# prescribed velocity field -- the one thing `restore_simulation_state`
# reconstructs from the checkpoint's embedded config rather than reads
# from the checkpoint's own tensors -- is all zero. A reconstruction bug
# that always produced zero velocity regardless of config would still
# pass every test built on `_CONFIG_TEXT` alone, since zero happens to be
# the correct answer there too (`docs/practices.md`'s "distinct factors"
# rule: verify a conversion, or here a reconstruction, where its inputs
# are not degenerate). This fixture prescribes a real, nonzero velocity
# instead, so a wrong reconstruction changes the outcome rather than
# accidentally agreeing with it -- see the two tests below that use it.
_CONFIG_TEXT_WITH_PRESCRIBED_VELOCITY = (
    _CONFIG_TEXT
    + """
simulation:
  velocity_pattern: uniform
  velocity: [1.0, 0.5]
"""
)

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


def test_resuming_reproduces_trajectory_with_a_nonzero_prescribed_velocity(
    tmp_path: Path,
) -> None:
    """The same claim as the test above, on
    `_CONFIG_TEXT_WITH_PRESCRIBED_VELOCITY` -- see that constant's own
    comment for why a nonzero prescribed velocity is what actually pins
    `restore_simulation_state`'s reconstruction, rather than only
    exercising it.

    **Confirmed to have the teeth the test above lacks**: with
    `restore_simulation_state` mutated to overwrite its reconstructed
    `velocity_field` with an all-zero one after building it, the test
    above (zero-velocity fixture) stayed green while this one failed,
    20/20 mismatched elements -- reverted once confirmed, per this
    project's own mutation-testing discipline.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_CONFIG_TEXT_WITH_PRESCRIBED_VELOCITY)

    control = _control_trajectory(config_file)
    resumed = _resumed_trajectory(config_file, tmp_path / "checkpoints")

    torch.testing.assert_close(resumed, control, rtol=0, atol=0)


def test_config_round_trip_reconstructs_a_nonzero_prescribed_velocity_field_bit_identically(
    tmp_path: Path,
) -> None:
    """The mechanism the two tests above rely on, isolated: a "passive"
    mode `SimulationState.velocity_field` is never checkpointed at all
    (`checkpoint.py`'s own docstring) because it is a pure function of
    `config.simulation.velocity_pattern`/`velocity` and the mesh, not
    evolved state -- so round-tripping the config through the exact
    serialization a checkpoint uses (`dataclasses.asdict`/
    `config_from_dict`, not the file itself) and rebuilding from it must
    reproduce the *configured* velocity exactly, not a plausible
    approximation of it.

    **Checked against a hand-computed expected tensor, not against a
    second `build_simulation_state` call on the same config** -- a first
    draft compared the round-tripped reconstruction to a fresh build from
    `config` itself, and mutation testing found that blind: both calls
    share every line of `config_from_dict`/`_config_from_raw`
    (`configuration/loader.py`), so a mutation that made
    `simulation.velocity` silently fall back to its schema default
    (`(1.0, 0.0)`) broke both sides identically and the comparison still
    passed. Comparing against a value computed independently of any
    PyFlow parsing code is what makes a shared-code bug visible instead
    of invisible to a differential check.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_CONFIG_TEXT_WITH_PRESCRIBED_VELOCITY)
    config = load_config(config_file)
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    round_tripped_config = config_from_dict(dataclasses.asdict(config))
    reconstructed = build_simulation_state(mesh, round_tripped_config)
    assert reconstructed is not None
    assert reconstructed.velocity_field is not None

    # `_CONFIG_TEXT_WITH_PRESCRIBED_VELOCITY` sets `velocity: [1.0, 0.5]`
    # directly -- this is that literal value, not derived from any code
    # under test, broadcast across every cell (a uniform pattern's own
    # definition: the same vector everywhere).
    expected = torch.tensor([1.0, 0.5], dtype=torch.float64).repeat(mesh.num_cells, 1)
    torch.testing.assert_close(reconstructed.velocity_field.values, expected, rtol=0, atol=0)
