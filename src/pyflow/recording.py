"""Headless checkpoint recording (TASK-045, Stage 8, Recording & Playback):
step a simulation forward with no rendering window at all, writing
periodic checkpoints to disk -- the write half of `docs/planning/
backlog.md`'s "decouple simulation from rendering" item.

**Never imports `rendering`, `pygfx`, or `rendercanvas` at all.** This is
the structural enforcement of "headless by default when recording" (the
backlog item's own stated requirement): `bootstrap()`/`RenderWindow`
never read `config.recording` (`schema.py`'s own `RecordingConfig`
docstring), so the same config file behaves identically under `pyflow
run` whether or not a `recording:` section is set -- recording is
enabled by *which command runs* (`pyflow record`, this module), not a
config switch that could accidentally turn a live interactive run into
one that also writes checkpoints. `RenderWindow.__init__`
unconditionally builds a real `wgpu` renderer (`rendering/window.py`),
so this is not merely a convenience: there is no way to get a genuinely
headless run out of `bootstrap()` itself, even with rendering "turned
off," which is why this is a separate entry point rather than a
`bootstrap()` keyword argument.

Orchestrates `configuration` + `engine` only, the same package-root
placement `bootstrap.py`/`simulation_run.py` both use
(`src/pyflow/CLAUDE.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyflow.checkpoint import write_checkpoint
from pyflow.configuration import load_config
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.engine.mesh import StructuredCartesianMesh
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


@dataclass(frozen=True)
class RecordingResult:
    """`record`'s own return value -- `checkpoint_frames` is every frame
    number a checkpoint was actually written at, in order (always starts
    with `0` and ends with `final_frame_count`, per `record`'s own
    docstring).
    """

    output_dir: Path
    checkpoint_frames: list[int]
    final_frame_count: int


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
    checkpoint_frames: list[int] = []

    def _checkpoint(frame_count: int) -> None:
        path = resolved_output_dir / f"checkpoint_{frame_count:08d}.pt"
        write_checkpoint(path, frame_count=frame_count, config=config, fields=state.fields)
        checkpoint_frames.append(frame_count)

    _checkpoint(0)
    for frame_count in range(1, max_frames + 1):
        state = advance_simulation_state(state, numerics, config.numerics.timestep)
        if frame_count % interval == 0 or frame_count == max_frames:
            _checkpoint(frame_count)

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
