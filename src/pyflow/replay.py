"""Windowed materialization (TASK-046, Stage 8, Recording & Playback):
given a checkpoint directory and a target frame range, re-simulate
forward and produce dense, in-memory per-frame field data for just that
range -- the mechanism `pyflow play` (`playback.py`, TASK-047) renders.

**No `rendering` import at all**, the same rule `recording.py` follows
and for the same reason: this module is a pure library, testable with
plain pytest, with no dependency on a window or a `pygfx` scene existing
at all.

Orchestrates `configuration` + `engine` only, the same package-root
placement `bootstrap.py`/`simulation_run.py`/`checkpoint.py`/
`recording.py` all use (`src/pyflow/CLAUDE.md`).

**Ephemeral by default, with an optional disk cache -- one `pyflow play`
command, not two.** `materialize_window` always re-simulates; there is
no way to ask for anything else from it. `materialize_or_load_window`
is the caller-facing function `pyflow play` actually uses: given a
`cache_dir`, it reads an exact-range match if one exists there and
writes one after materializing if not, so watching the same window twice
costs nothing the second time -- but the range must match exactly
(`from_frame`/`to_frame` both), a real, stated scope decision rather
than an oversight: partial-overlap reuse (asking for [10, 20] when a
[0, 30] cache exists) would need to know how to slice or extend a
cached window, a real design question with no shipped need for it yet.
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from pathlib import Path

import torch

from pyflow.checkpoint import field_tensors, read_checkpoint, restore_simulation_state
from pyflow.configuration import config_from_dict
from pyflow.configuration.schema import PyFlowConfig
from pyflow.simulation_run import advance_simulation_state

_WINDOW_SCHEMA_VERSION = 1

_CHECKPOINT_FILENAME = re.compile(r"^checkpoint_(\d{8})\.pt$")


class NoCheckpointBeforeFrameError(ValueError):
    """Raised by `find_checkpoint_at_or_before` when no checkpoint in the
    given directory has a frame count at or before the requested frame --
    there is nothing to re-simulate forward from.
    """


class UnsupportedWindowVersionError(ValueError):
    """Raised by `read_materialized_window` if a file's own
    `schema_version` isn't the one this module knows how to read -- the
    same named-rejection shape `checkpoint.UnsupportedCheckpointVersionError`
    already establishes.
    """


def find_checkpoint_at_or_before(checkpoints_dir: str | Path, frame: int) -> Path:
    """The newest checkpoint in `checkpoints_dir` whose own frame count is
    `<= frame`.

    Ranks candidates by the frame number in the *filename* first (cheap,
    no I/O for every candidate that isn't the winner), then reads only
    the selected file and cross-checks its real `Checkpoint.frame_count`
    against that filename -- `checkpoint.py`'s own "the filename is a
    convention, `frame_count` is authoritative" rule, applied to a lookup
    that would otherwise trust the filename outright. Raises
    `NoCheckpointBeforeFrameError` if the filename claims a mismatched
    frame count (someone renamed the file) or if nothing qualifies.
    """
    candidates: list[tuple[int, Path]] = []
    for path in Path(checkpoints_dir).glob("checkpoint_*.pt"):
        match = _CHECKPOINT_FILENAME.match(path.name)
        if match is None:
            continue
        candidates.append((int(match.group(1)), path))

    qualifying = [candidate for candidate in candidates if candidate[0] <= frame]
    if not qualifying:
        raise NoCheckpointBeforeFrameError(
            f"no checkpoint at or before frame {frame} in {checkpoints_dir}"
        )

    claimed_frame, path = max(qualifying, key=lambda candidate: candidate[0])
    checkpoint = read_checkpoint(path)
    if checkpoint.frame_count != claimed_frame:
        raise NoCheckpointBeforeFrameError(
            f"{path} claims frame {claimed_frame} in its own filename, but its real "
            f"frame_count is {checkpoint.frame_count} -- refusing to trust the filename"
        )
    return path


@dataclass(frozen=True)
class MaterializedWindow:
    """`materialize_window`'s own result -- `frames[i]` is the field
    values at frame `from_frame + i`, so `len(frames) == to_frame -
    from_frame + 1`. `config` is the checkpoint's own embedded config the
    window was materialized under, the same "structure/config travels
    with the data" shape `checkpoint.Checkpoint` already establishes.
    """

    config: PyFlowConfig
    from_frame: int
    to_frame: int
    frames: list[dict[str, torch.Tensor]]


def materialize_window(
    checkpoints_dir: str | Path, *, from_frame: int, to_frame: int
) -> MaterializedWindow:
    """Find the newest checkpoint at or before `from_frame`, restore it,
    fast-forward (advancing and discarding) to `from_frame`, then advance
    and collect every frame's field values through `to_frame` inclusive.

    Raises `ValueError` if `to_frame < from_frame`, and
    `NoCheckpointBeforeFrameError` (via `find_checkpoint_at_or_before`)
    if `checkpoints_dir` has nothing to start from.
    """
    if to_frame < from_frame:
        raise ValueError(f"to_frame ({to_frame}) must be >= from_frame ({from_frame})")

    checkpoint_path = find_checkpoint_at_or_before(checkpoints_dir, from_frame)
    checkpoint = read_checkpoint(checkpoint_path)
    _mesh, numerics, state = restore_simulation_state(checkpoint)
    dt = checkpoint.config.numerics.timestep

    for _ in range(from_frame - checkpoint.frame_count):
        state = advance_simulation_state(state, numerics, dt)

    frames = [field_tensors(state.fields)]
    for _ in range(to_frame - from_frame):
        state = advance_simulation_state(state, numerics, dt)
        frames.append(field_tensors(state.fields))

    return MaterializedWindow(
        config=checkpoint.config, from_frame=from_frame, to_frame=to_frame, frames=frames
    )


def write_materialized_window(window: MaterializedWindow, path: str | Path) -> None:
    """Write `window` to `path` -- one `torch.save`d file, the config
    embedded once (not once per frame, unlike a checkpoint, which is
    exactly one frame): `write_checkpoint`'s per-frame config duplication
    makes sense for a self-contained, independently-resumable snapshot;
    a materialized window's own frames are never resumed from
    individually, so there is nothing to gain by repeating the same
    config dict `len(frames)` times.
    """
    payload = {
        "schema_version": _WINDOW_SCHEMA_VERSION,
        "from_frame": window.from_frame,
        "to_frame": window.to_frame,
        "config": dataclasses.asdict(window.config),
        "frames": window.frames,
    }
    torch.save(payload, path)


def read_materialized_window(path: str | Path) -> MaterializedWindow:
    """Read a window written by `write_materialized_window`. Raises
    `UnsupportedWindowVersionError` if the file's own `schema_version`
    doesn't match this module's.
    """
    payload = torch.load(path, weights_only=True)
    schema_version = payload["schema_version"]
    if schema_version != _WINDOW_SCHEMA_VERSION:
        raise UnsupportedWindowVersionError(
            f"{path}: window schema version {schema_version!r} is not supported "
            f"(this build reads version {_WINDOW_SCHEMA_VERSION!r} only)"
        )
    return MaterializedWindow(
        config=config_from_dict(payload["config"]),
        from_frame=payload["from_frame"],
        to_frame=payload["to_frame"],
        frames=payload["frames"],
    )


def materialize_or_load_window(
    checkpoints_dir: str | Path,
    *,
    from_frame: int,
    to_frame: int,
    cache_dir: str | Path | None = None,
) -> MaterializedWindow:
    """`pyflow play`'s own entry point into this module: read an
    exact-range match from `cache_dir` if one exists there, otherwise
    materialize fresh -- and, if `cache_dir` was given, write the result
    there so a second call with the same range costs nothing.
    `cache_dir` omitted (the default) always materializes fresh, never
    writing or reading anything -- the ephemeral, no-artifact-left-behind
    behaviour this module's own docstring describes as the default.
    """
    cache_path = (
        Path(cache_dir) / f"window_{from_frame:08d}_{to_frame:08d}.pt"
        if cache_dir is not None
        else None
    )
    if cache_path is not None and cache_path.is_file():
        return read_materialized_window(cache_path)

    window = materialize_window(checkpoints_dir, from_frame=from_frame, to_frame=to_frame)

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        write_materialized_window(window, cache_path)

    return window
