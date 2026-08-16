"""Empty Window golden demo (Capability Level 0).

The simplest possible golden demo: open a rendering window, display an
empty scene, close cleanly. No physics, no mesh, no fields -- it proves
the Stage 0 bootstrap chain (configuration -> logging -> rendering)
produces a real, visible frame end to end. See
`docs/implementation/golden-demos.md` for what "working" means here and
how `tests/golden/test_empty_window.py` verifies it.

Run directly for the interactive version -- a real window, glfw backend,
that waits for you to press Escape or Enter (or close the window
normally) rather than closing itself, so there is actually time to look
at it:

    uv run python examples/golden-demos/empty_window.py

Not an importable package (`examples/` deliberately isn't one, see
`examples/CLAUDE.md`) -- the regression test loads this file directly by
path instead of importing it by dotted name.
"""

from __future__ import annotations

from typing import Any

import pygfx as gfx

from pyflow.configuration import LoggingConfig, RenderingConfig
from pyflow.engine import configure_logging
from pyflow.rendering import RenderWindow

# Solid, deterministic background colour -- not pygfx's default
# (transparent black), which would make "produces useful visual output"
# (golden-demos.md's Definition of Done) trivially true and nothing a
# regression test could actually verify.
BACKGROUND_COLOR = "#1a1a2e"

_CLOSE_KEYS = ("Escape", "Enter")


def run(
    config: RenderingConfig | None = None,
    *,
    max_frames: int | None = None,
    close_on_key: bool = False,
) -> RenderWindow:
    """Build and run the Empty Window demo.

    `close_on_key`: when true (and the backend is interactive), pressing
    Escape or Enter closes the window -- lets a human watching it decide
    when they're done looking, rather than either an automatic timeout or
    having to find the OS window's own close button. Ignored for the
    offscreen backend, which has no keyboard events to listen for.

    Returns the `RenderWindow` afterward so a caller (the regression
    test) can inspect what was actually rendered, not just that nothing
    raised.
    """
    resolved_config = config or RenderingConfig()
    window = RenderWindow(resolved_config)
    window.scene.add(gfx.Background(None, gfx.BackgroundMaterial(BACKGROUND_COLOR)))

    if close_on_key and resolved_config.backend != "offscreen":

        def _on_key(event: dict[str, Any]) -> None:
            if event.get("key") in _CLOSE_KEYS:
                window.canvas.close()

        window.canvas.add_event_handler(_on_key, "key_down")

    window.run(max_frames=max_frames)
    return window


if __name__ == "__main__":
    configure_logging(LoggingConfig())
    print(f"Empty Window demo -- background {BACKGROUND_COLOR}.")
    print("Press Escape or Enter to close (or close the window normally).")
    run(close_on_key=True)
