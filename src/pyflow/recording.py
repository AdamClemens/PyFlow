"""Headless checkpoint recording (TASK-045, Stage 8, Recording & Playback):
step a simulation forward with no rendering window at all, writing
periodic checkpoints to disk -- the write half of `docs/planning/
backlog.md`'s "decouple simulation from rendering" item. `resume`
(added the same task) is the natural extension of that same half, not
the read/playback half: it continues a headless recording from an
existing checkpoint, writing further checkpoints -- still no rendering,
still not the dense, renderer-ready windowed replay Stage 8's own
Completion Criterion 5 (playback half) still waits on TASK-046/047 for.

**Never imports `rendering`, `pygfx`, or `rendercanvas` at all.** This is
the structural enforcement of "headless by default when recording" (the
backlog item's own stated requirement): `bootstrap()`/`RenderWindow`
never read `config.recording` (`schema.py`'s own `RecordingConfig`
docstring), so the same config file behaves identically under `pyflow
run` whether or not a `recording:` section is set -- recording is
enabled by *which command runs* (`pyflow record`/`pyflow resume`, this
module), not a config switch that could accidentally turn a live
interactive run into one that also writes checkpoints. `RenderWindow.
__init__` unconditionally builds a real `wgpu` renderer
(`rendering/window.py`), so this is not merely a convenience: there is
no way to get a genuinely headless run out of `bootstrap()` itself, even
with rendering "turned off," which is why this is a separate entry point
rather than a `bootstrap()` keyword argument.

Orchestrates `configuration` + `engine` only, the same package-root
placement `bootstrap.py`/`simulation_run.py` both use
(`src/pyflow/CLAUDE.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyflow.checkpoint import read_checkpoint, restore_simulation_state, write_checkpoint
from pyflow.configuration import load_config
from pyflow.configuration.schema import PyFlowConfig
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.simulation_run import (
    SimulationState,
    advance_simulation_state,
    assembled_numerics_for,
    build_simulation_state,
)

logger = get_logger(__name__)


class NothingToRecordError(ValueError):
    """Raised when `config` declares no `fields` and no
    `simulation.velocity_solved` -- there is no changing state to
    checkpoint, and silently writing `checkpoint_interval`-many identical
    files of a static initial condition would be a plausible-looking
    waste, not a useful recording.
    """


class NothingToResumeError(ValueError):
    """Raised by `resume` when `max_frames` is not strictly greater than
    the checkpoint's own `frame_count` -- there is nothing to advance to,
    and silently returning an empty result would look like a successful
    resume rather than a likely mistake in `--max-frames`.
    """


@dataclass(frozen=True)
class RecordingResult:
    """`record`/`resume`'s own return value -- `checkpoint_frames` is
    every frame number a checkpoint was written *by this call*, in order.
    For `record`, always starts with `0` and ends with `final_frame_count`
    (per `record`'s own docstring). For `resume`, never includes the
    frame resumed from (that checkpoint already exists -- it's the file
    `resume` read) and ends with `final_frame_count`.
    """

    output_dir: Path
    checkpoint_frames: list[int]
    final_frame_count: int


def _advance_and_checkpoint(
    state: SimulationState,
    numerics: AssembledNumerics,
    config: PyFlowConfig,
    *,
    start_frame: int,
    max_frames: int,
    output_dir: Path,
    interval: int,
) -> list[int]:
    """Advance `state` in place from `start_frame` to `max_frames`,
    writing a checkpoint every `interval` frames and at `max_frames`
    (even off interval). Never checkpoints `start_frame` itself -- shared
    by `record` (`start_frame=0`, checkpointed by its own caller before
    this runs) and `resume` (`start_frame=checkpoint.frame_count`,
    already on disk as the file being resumed from), so the two can never
    drift apart on what "every `interval` frames" means.
    """
    checkpoint_frames: list[int] = []
    for frame_count in range(start_frame + 1, max_frames + 1):
        state = advance_simulation_state(state, numerics, config.numerics.timestep)
        if frame_count % interval == 0 or frame_count == max_frames:
            path = output_dir / f"checkpoint_{frame_count:08d}.pt"
            write_checkpoint(path, frame_count=frame_count, config=config, fields=state.fields)
            checkpoint_frames.append(frame_count)
    return checkpoint_frames


def record(
    config_path: str | Path | None = None,
    *,
    max_frames: int,
    output_dir: str | Path | None = None,
    checkpoint_interval: int | None = None,
) -> RecordingResult:
    """Load `config_path`, step it forward `max_frames` timesteps with no
    rendering at all, writing a checkpoint at frame 0, every
    `checkpoint_interval` frames, and at `max_frames` (always, even if
    `max_frames` doesn't fall on the interval) -- the sparse seek index
    Stage 8's own Goal describes.

    `output_dir`/`checkpoint_interval`, given, override `config.
    recording`'s own fields, the same CLI-overrides-config shape
    `bootstrap()`'s own `backend` parameter already establishes.

    `max_frames` is required, not optional -- unlike `bootstrap()`, there
    is no window and no user to stop this run any other way; an
    unbounded headless loop has no natural end.

    Raises `NothingToRecordError` if the loaded config declares nothing
    that changes frame to frame.
    """
    config = load_config(config_path)
    configure_logging(config.logging)

    resolved_output_dir = Path(
        output_dir if output_dir is not None else config.recording.output_dir
    )
    interval = (
        checkpoint_interval
        if checkpoint_interval is not None
        else config.recording.checkpoint_interval
    )

    mesh = StructuredCartesianMesh.from_config(config.mesh)
    numerics = assembled_numerics_for(config)
    built_state = build_simulation_state(mesh, config)
    if built_state is None:
        raise NothingToRecordError(
            "config declares no `fields` and no `simulation.velocity_solved` -- "
            "nothing changes frame to frame, so there is nothing to record"
        )
    state: SimulationState = built_state

    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    write_checkpoint(
        resolved_output_dir / "checkpoint_00000000.pt",
        frame_count=0,
        config=config,
        fields=state.fields,
    )
    rest = _advance_and_checkpoint(
        state,
        numerics,
        config,
        start_frame=0,
        max_frames=max_frames,
        output_dir=resolved_output_dir,
        interval=interval,
    )
    checkpoint_frames = [0, *rest]

    logger.info(
        "recorded %d checkpoint(s) to %s, frames %s",
        len(checkpoint_frames),
        resolved_output_dir,
        checkpoint_frames,
    )
    return RecordingResult(
        output_dir=resolved_output_dir,
        checkpoint_frames=checkpoint_frames,
        final_frame_count=max_frames,
    )


def resume(
    checkpoint_path: str | Path | None = None,
    *,
    config_path: str | Path | None = None,
    max_frames: int,
    output_dir: str | Path | None = None,
    checkpoint_interval: int | None = None,
) -> RecordingResult:
    """Read the checkpoint at `checkpoint_path`, restore the
    `SimulationState` it holds, and continue stepping headlessly from its
    own `frame_count` up to `max_frames` -- the same checkpoint policy
    `record` uses (every `checkpoint_interval` frames, and at
    `max_frames`), so `record(..., max_frames=6)` followed by
    `resume(..., max_frames=12)` writes exactly the checkpoint files an
    uninterrupted `record(..., max_frames=12)` would have written after
    frame 6.

    `output_dir`, given, overrides where further checkpoints are written;
    omitted, defaults to `checkpoint_path`'s own parent directory -- not
    the checkpoint's embedded `config.recording.output_dir`, which is the
    *original* run's configured default and may not be where this
    particular file actually lives if that run itself overrode it.

    `checkpoint_interval`, given, overrides the checkpoint's own embedded
    `config.recording.checkpoint_interval`; omitted, that value applies --
    the same CLI-overrides-config shape `record` already establishes.

    Raises `NothingToResumeError` if `max_frames` is not strictly greater
    than the checkpoint's own `frame_count`.

    **`config_path` (added at a user's direct request: "do pyflow resume
    from a config file and have it start from the first frame") is a
    second, mutually exclusive way to call this function -- pass exactly
    one of `checkpoint_path`/`config_path`, never both, never neither.**
    Given a config instead of a checkpoint, there is nothing yet to
    resume *from*, so this is a pure alternate entry point into `record`
    itself (`return record(config_path, ...)`, not a second copy of its
    logic) -- what lets a caller use `resume` as the one command for an
    entire recording's lifecycle (`pyflow resume --config X` the first
    time, `pyflow resume --checkpoint <latest>` every time after) without
    having to remember which of two command names applies yet. This is
    a different case from the "mismatch between the config a checkpoint
    carries and a config a user might pass" concern the original
    `--checkpoint`-only design recorded, above and in `src/pyflow/
    CLAUDE.md`: that risk is specifically about combining both at once,
    which is exactly the combination this still rejects.
    """
    if (checkpoint_path is None) == (config_path is None):
        raise ValueError(
            "resume: exactly one of checkpoint_path or config_path must be given, got "
            f"checkpoint_path={checkpoint_path!r}, config_path={config_path!r}"
        )
    if config_path is not None:
        return record(
            config_path,
            max_frames=max_frames,
            output_dir=output_dir,
            checkpoint_interval=checkpoint_interval,
        )

    assert checkpoint_path is not None  # the exactly-one-of check above guarantees this
    checkpoint = read_checkpoint(checkpoint_path)
    if max_frames <= checkpoint.frame_count:
        raise NothingToResumeError(
            f"checkpoint is already at frame {checkpoint.frame_count}; "
            f"--max-frames {max_frames} is not past it"
        )

    configure_logging(checkpoint.config.logging)

    resolved_output_dir = Path(
        output_dir if output_dir is not None else Path(checkpoint_path).parent
    )
    interval = (
        checkpoint_interval
        if checkpoint_interval is not None
        else checkpoint.config.recording.checkpoint_interval
    )

    _mesh, numerics, state = restore_simulation_state(checkpoint)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_frames = _advance_and_checkpoint(
        state,
        numerics,
        checkpoint.config,
        start_frame=checkpoint.frame_count,
        max_frames=max_frames,
        output_dir=resolved_output_dir,
        interval=interval,
    )

    logger.info(
        "resumed from frame %d, recorded %d checkpoint(s) to %s, frames %s",
        checkpoint.frame_count,
        len(checkpoint_frames),
        resolved_output_dir,
        checkpoint_frames,
    )
    return RecordingResult(
        output_dir=resolved_output_dir,
        checkpoint_frames=checkpoint_frames,
        final_frame_count=max_frames,
    )
