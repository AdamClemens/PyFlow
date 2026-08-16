"""Rendering subsystem: window/render-loop bootstrap and visualisation of
scalar/vector fields, using wgpu/pygfx per
adr/ADR-005-compute-rendering-instances.md. Also covers interaction
(input, camera/view control), absorbed here per the 2026-08-15 package
reconciliation (see docs/planning/backlog.md).
"""

from pyflow.rendering.window import RenderWindow

__all__ = [
    "RenderWindow",
]
