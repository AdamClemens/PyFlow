"""Canvas-selection seam (TASK-007 / backlog D3).

Creates the concrete `rendercanvas` canvas backing pygfx's renderer,
chosen by `RenderingConfig.backend`. Everything past canvas creation --
`pygfx.WgpuRenderer`, the scene, the render loop in `window.py` -- is
backend-agnostic: both backends implement `rendercanvas.base.
BaseRenderCanvas`, which is all a pygfx renderer actually depends on.
`adr/ADR-003-modular-numerical-strategies.md` already commits PyFlow to
selecting implementations behind a stable interface, at construction --
this is that pattern applied to the windowing layer rather than the
whole renderer.

Adding a third backend (Qt, the maintainer's stated ambition for a real
GUI toolkit) means adding one branch here, not touching `window.py`.
"""

from __future__ import annotations

from typing import Any

from pyflow.configuration.schema import RenderingConfig


def create_canvas(config: RenderingConfig) -> Any:
    """Create the canvas backend selected by `config.backend`.

    Return type is `Any`, not `BaseRenderCanvas`: `rendercanvas` ships no
    py.typed marker (see the mypy override in `pyproject.toml`), so a
    precise annotation here would be cosmetic, not checked.
    """
    size = (config.width, config.height)

    if config.backend == "glfw":
        from rendercanvas.glfw import GlfwRenderCanvas

        return GlfwRenderCanvas(size=size, title=config.title)
    elif config.backend == "offscreen":
        from rendercanvas.offscreen import OffscreenRenderCanvas

        return OffscreenRenderCanvas(size=size, title=config.title)
    else:
        raise ValueError(f"unknown rendering backend: {config.backend!r}")


def get_loop(config: RenderingConfig) -> Any:
    """Return the event loop that runs canvases for `config.backend`.

    Only meaningful for interactive backends -- `rendercanvas.offscreen`
    has no loop or scheduling (its own docstring: "No scheduling"); it
    draws when told to, directly, in `window.py`.
    """
    if config.backend == "glfw":
        from rendercanvas.glfw import loop

        return loop
    raise ValueError(f"backend {config.backend!r} has no event loop")
