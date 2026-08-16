"""Empty Window golden demo (Capability Level 0).

The simplest possible golden demo: open a rendering window, display an
empty scene, close cleanly. No physics, no mesh, no fields -- it proves
the Stage 0 bootstrap chain (configuration -> logging -> rendering)
produces a real, visible frame end to end. See
`docs/implementation/golden-demos.md` for what "working" means here and
how `tests/golden/test_empty_window.py` verifies it.

Run directly for the interactive version (a real window, glfw backend):

    uv run python examples/golden-demos/empty_window.py

Not an importable package (`examples/` deliberately isn't one, see
`examples/CLAUDE.md`) -- the regression test loads this file directly by
path instead of importing it by dotted name.
"""

from __future__ import annotations

import pygfx as gfx

from pyflow.configuration import LoggingConfig, RenderingConfig
from pyflow.engine import configure_logging
from pyflow.rendering import RenderWindow

# Solid, deterministic background colour -- not pygfx's default
# (transparent black), which would make "produces useful visual output"
# (golden-demos.md's Definition of Done) trivially true and nothing a
# regression test could actually verify.
BACKGROUND_COLOR = "#1a1a2e"


def run(config: RenderingConfig | None = None, *, max_frames: int | None = None) -> RenderWindow:
    """Build and run the Empty Window demo.

    Returns the `RenderWindow` afterward so a caller (the regression
    test) can inspect what was actually rendered, not just that nothing
    raised.
    """
    window = RenderWindow(config or RenderingConfig())
    window.scene.add(gfx.Background(None, gfx.BackgroundMaterial(BACKGROUND_COLOR)))
    window.run(max_frames=max_frames)
    return window


if __name__ == "__main__":
    configure_logging(LoggingConfig())
    run()
