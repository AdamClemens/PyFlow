"""One simulation state, written to and read from disk (TASK-045, Stage 8,
Recording & Playback) -- what `recording.py`'s headless loop writes
periodically, and what a future windowed-replay path (TASK-046) reads
back to resume deterministic stepping from.

Orchestrates `configuration` + `engine` only, the same "lives at the
package root, no `rendering` import" rule `simulation_run.py` and
`bootstrap.py` both follow (`src/pyflow/CLAUDE.md`).

**One `torch.save`d file per checkpoint, fully self-contained.** Embeds
its own config (`dataclasses.asdict`, not a pickled `PyFlowConfig`
instance and not a YAML round-trip through a temp file): a pickled
instance would force `torch.load(weights_only=False)`, a real code-exec
surface, and tie the format to Python's pickle protocol version and this
project's exact class layout; a YAML round-trip is needless indirection
through a text format when the in-memory dict shape is already exactly
what `pyflow.configuration.loader`'s own "raw dict -> validated
`PyFlowConfig`" machinery consumes (`config_from_dict`). `asdict()` is
already how `generator.py`'s `generate_config_yaml` gets its data
(`configuration/CLAUDE.md`'s own "reuses `dataclasses.asdict()`"), it
preserves tuples exactly, and `torch.load`'s default `weights_only=True`
safe-globals allowlist already covers plain dict/list/tuple/str/int/
float/bool -- no custom class ever crosses the pickle boundary.

**No per-field type tag, and no RNG/device metadata.** Every entry
`recording.py` checkpoints comes from `simulation_run.SimulationState.
fields`, which -- verified directly, not assumed -- only ever holds
plain single-component scalar tensors: `PressureField` never appears
there (`navier_stokes_step`'s own pressure output is a separate return
value, never fed back into the stepped state), and nothing anywhere in
this codebase uses randomness or a non-CPU device (grepped for
`torch.rand`/`random.`/`device=`/`.cuda(`, found none). Determinism
after reload is therefore purely mesh + field tensors + config,
reproduced exactly -- there is nothing else to capture.
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import torch

from pyflow.configuration import config_from_dict
from pyflow.configuration.schema import PyFlowConfig
from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.engine.scalar_field import ScalarField
from pyflow.simulation_run import SimulationState, assembled_numerics_for, build_simulation_state

_SCHEMA_VERSION = 1

# `checkpoint_00000010.pt` -- the one filename convention every
# checkpoint on disk follows. Factored out here (TASK-049, Stage 8
# reopening, 2026-09-09) so `list_checkpoints` below and `replay.py`'s
# own `find_checkpoint_at_or_before` read one implementation of "what
# checkpoints exist in this directory", not two that could drift apart
# -- this project's own P-011. The filename is a convention; a
# checkpoint's real `frame_count` (read from the file itself) is
# authoritative, per `read_checkpoint`'s own docstring -- callers that
# need to trust a frame number still read the file, the same way
# `find_checkpoint_at_or_before` already does.
CHECKPOINT_FILENAME = re.compile(r"^checkpoint_(\d{8})\.pt$")


class UnsupportedCheckpointVersionError(ValueError):
    """Raised by `read_checkpoint` if a file's own `schema_version` isn't
    the one this module knows how to read -- a named rejection rather
    than a confusing tensor-shape mismatch several calls deep, and a
    clean extension point the day this format's own shape ever changes.
    """


@dataclass(frozen=True)
class Checkpoint:
    """One `read_checkpoint` result: `frame_count` (0 = the run's own
    initial state, N = after N advances -- the same convention
    `RenderWindow.frame_count`/`bootstrap.py`'s `_stats_lines` already
    use, so `elapsed = frame_count * config.numerics.timestep` agrees
    with every other place in the codebase that computes it), the
    reconstructed `config` this checkpoint was recorded under, and
    `fields` (name -> `(mesh.num_cells,)` float64 tensor, exactly
    `simulation_run.SimulationState.fields`' own shape once each `Field`
    is reduced to its raw values).
    """

    frame_count: int
    config: PyFlowConfig
    fields: dict[str, torch.Tensor]


def list_checkpoints(directory: str | Path) -> list[tuple[int, Path]]:
    """Every checkpoint file in `directory`, as `(frame_number, path)`
    pairs read from each filename -- unsorted, in whatever order
    `Path.glob` yields them. A non-checkpoint file (no match against
    `CHECKPOINT_FILENAME`) is silently skipped, the same tolerance
    `find_checkpoint_at_or_before` already had before this was factored
    out of it. Cheap: reads filenames only, opens no file.
    """
    checkpoints: list[tuple[int, Path]] = []
    for path in Path(directory).glob("checkpoint_*.pt"):
        match = CHECKPOINT_FILENAME.match(path.name)
        if match is not None:
            checkpoints.append((int(match.group(1)), path))
    return checkpoints


def field_tensors(fields: Mapping[str, Field]) -> dict[str, torch.Tensor]:
    """A `dict[str, Field]` reduced to plain, cloned `(num_cells,)`
    tensors -- the shape `write_checkpoint` saves and `replay.py`'s own
    per-frame materialization collects, factored out so both go through
    one implementation (P-011) rather than two copies that could drift.
    Cloned because a caller (`recording.py`/`replay.py`) keeps stepping
    the same `SimulationState.fields` tensors after this returns, and a
    snapshot -- a checkpoint frame, or a materialized window frame -- is
    a snapshot at this moment, not a live view into state that will keep
    changing underneath it.
    """
    tensors: dict[str, torch.Tensor] = {}
    for name, field_value in fields.items():
        # `Field` itself declares no `.values` -- only `CollocatedField`
        # does (`docs/engine/CLAUDE.md`'s own "carries only what's true
        # regardless of arrangement"). Every entry a caller passes here
        # is one in practice, so this narrows rather than widens the
        # accepted type.
        assert isinstance(field_value, CollocatedField)
        tensors[name] = field_value.values.clone()
    return tensors


def write_checkpoint(
    path: str | Path,
    *,
    frame_count: int,
    config: PyFlowConfig,
    fields: Mapping[str, Field],
) -> None:
    """Write one checkpoint to `path`."""
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "frame_count": frame_count,
        "config": dataclasses.asdict(config),
        "fields": field_tensors(fields),
    }
    torch.save(payload, path)


def read_checkpoint(path: str | Path) -> Checkpoint:
    """Read one checkpoint written by `write_checkpoint`. Raises
    `UnsupportedCheckpointVersionError` if the file's own `schema_version`
    doesn't match this module's.
    """
    payload = torch.load(path, weights_only=True)
    schema_version = payload["schema_version"]
    if schema_version != _SCHEMA_VERSION:
        raise UnsupportedCheckpointVersionError(
            f"{path}: checkpoint schema version {schema_version!r} is not supported "
            f"(this build reads version {_SCHEMA_VERSION!r} only)"
        )
    return Checkpoint(
        frame_count=payload["frame_count"],
        config=config_from_dict(payload["config"]),
        fields=payload["fields"],
    )


def restore_simulation_state(
    checkpoint: Checkpoint,
) -> tuple[Mesh, AssembledNumerics, SimulationState]:
    """The mesh, assembled numerics, and resumable `SimulationState` a
    `record()` run had at `checkpoint.frame_count` -- ready to pass
    straight to `simulation_run.advance_simulation_state`.

    `checkpoint.fields`' own raw tensors are the state that actually
    changed; everything else needed to resume (mesh geometry, which mode
    to advance in, and -- for a `"passive"`-mode run -- the constant,
    never-checkpointed prescribed velocity field declared fields self-
    advect against) is deterministically re-derivable from `checkpoint.
    config` alone, via the exact same `simulation_run.
    build_simulation_state` a live or headless run already used to build
    its *own* initial state. Reusing it here gets the structure right
    (mode, prescribed velocity) but the field *values* wrong (freshly
    re-initialized from the config's own initial condition, not the
    checkpoint's evolved state) -- this function's own job is replacing
    those values with `checkpoint.fields`' real ones.
    """
    mesh = StructuredCartesianMesh.from_config(checkpoint.config.mesh)
    numerics = assembled_numerics_for(checkpoint.config)
    initial_state = build_simulation_state(mesh, checkpoint.config)
    # A checkpoint can only have been recorded for a config `recording.
    # record` accepted, and that function itself raises `NothingToRecord
    # Error` for exactly the config shape that would make this `None`.
    assert initial_state is not None
    initial_state.fields = {
        name: ScalarField(mesh, name, initial_value=tensor)
        for name, tensor in checkpoint.fields.items()
    }
    return mesh, numerics, initial_state
