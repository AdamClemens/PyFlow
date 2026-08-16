"""Application bootstrap (TASK-010): load configuration, initialise
logging, open the rendering window, run the loop, exit cleanly.

No simulation functionality -- Stage 0's job is to prove every
engineering-infrastructure piece (D1-D3) integrates into one coherent
run, not to simulate anything.

Lives at the `pyflow` package root, not inside `engine/`, deliberately:
it composes `configuration`, `engine` (for logging) and `rendering`
together, so it sits above all three in the dependency graph rather than
inside one of them. Putting it in `engine/` first (as TASK-010's own name
suggests) created a real circular import -- `engine` needing `rendering`
while `rendering.window` needs `engine.logging_setup` -- caught by
actually running the import, not just by inspection. See
`docs/CHANGELOG-DESIGN.md`, 2026-08-16 (D4).

This is PyFlow's public Python API for running anything, golden demos
included: a golden demo must be reproducible by a user as "the relevant
command with the relevant configuration," not bespoke code, so this
function -- and the `pyflow run` CLI built on it -- is the only sanctioned
way a demo gets run. See `docs/implementation/golden-demos.md`.
"""

from __future__ import annotations

from pathlib import Path

from pyflow import __version__
from pyflow.configuration import load_config
from pyflow.configuration.schema import RenderBackend
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.rendering import RenderWindow

logger = get_logger(__name__)


def bootstrap(
    config_path: str | Path | None = None,
    *,
    max_frames: int | None = None,
    backend: RenderBackend | None = None,
) -> RenderWindow:
    """Load configuration, initialise logging, open the render window, run.

    `max_frames` bounds the run for automated contexts (CI, the
    golden-demo regression test, backlog D5) that have no user to close a
    window. Left as `None` for a real interactive run, which blocks until
    the window is closed -- what `make demo` gives a developer.

    `backend`, if given, overrides whatever `config_path` specifies for
    `rendering.backend`. Exists so the same config file a user runs
    interactively can also be run headlessly for automated verification
    (`--backend offscreen`) without needing a second, duplicate config
    file just to change one field.

    Returns the `RenderWindow` so callers -- notably golden-demo
    regression tests -- can inspect what was actually rendered
    (`window.last_image`) rather than only that nothing raised.
    """
    config = load_config(config_path)
    if backend is not None:
        config.rendering.backend = backend
        config.rendering.validate()
    configure_logging(config.logging)

    logger.info("pyflow %s bootstrapping", __version__)
    window = RenderWindow(config.rendering)
    window.run(max_frames=max_frames)
    logger.info("pyflow exited cleanly")
    return window
