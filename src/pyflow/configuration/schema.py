"""Configuration schema: what a PyFlow run can be parameterised by.

Every field has a default, so `PyFlowConfig()` is a complete, valid
configuration on its own -- TASK-005's acceptance criterion is that the
application can be started entirely from configuration, which includes
the case where no config file is given at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

RenderBackend = Literal["glfw", "offscreen"]

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_VALID_RENDER_BACKENDS = frozenset({"glfw", "offscreen"})
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass
class LoggingConfig:
    """Logging framework settings (TASK-006)."""

    level: str = "INFO"

    def validate(self) -> None:
        if self.level.upper() not in _VALID_LOG_LEVELS:
            raise ValueError(
                f"logging.level must be one of {sorted(_VALID_LOG_LEVELS)}, got {self.level!r}"
            )


@dataclass
class RenderingConfig:
    """Rendering framework settings (TASK-007).

    `backend` selects the canvas behind pygfx's renderer: "glfw" opens a
    real, interactive window; "offscreen" renders to a NumPy array with no
    window, GUI toolkit or event loop -- what CI and the golden-demo
    regression tests (D5) need. The renderer itself doesn't know or care
    which one it's given; see `src/pyflow/rendering/canvas.py`.

    `background_color`, if set, is drawn behind the scene -- `None` (the
    default) leaves it unset, matching pygfx's own default. Exists so a
    golden demo's distinctive visual content can be *configuration*, not
    demo-specific Python code: golden demos must be runnable through the
    public API alone (`pyflow run --config <file>`), per
    `docs/implementation/golden-demos.md`'s Definition of Done.

    `grid_color` (TASK-013), if set, draws mesh grid lines in that
    colour -- same `None`-means-off pattern as `background_color`, so a
    config that doesn't mention it renders exactly as before.

    `zoom`/`pan` (TASK-013) are the camera's initial state: `zoom`
    multiplies how much of the world a fixed-size viewport shows (higher
    = more magnified); `pan` is a world-space offset from whatever the
    camera's default centring would otherwise be (the origin, or a
    mesh's centre when one is being visualised). `zoom_min`/`zoom_max`
    bound live, interactive zoom (mouse wheel) at runtime -- see
    `RenderWindow`.
    """

    backend: RenderBackend = "glfw"
    width: int = 1280
    height: int = 720
    title: str = "PyFlow"
    background_color: str | None = None
    grid_color: str | None = None
    zoom: float = 1.0
    pan: tuple[float, float] = (0.0, 0.0)
    zoom_min: float = 0.1
    zoom_max: float = 10.0

    def __post_init__(self) -> None:
        pan_x, pan_y = self.pan
        self.pan = (float(pan_x), float(pan_y))

    def validate(self) -> None:
        if self.backend not in _VALID_RENDER_BACKENDS:
            raise ValueError(
                f"rendering.backend must be one of {sorted(_VALID_RENDER_BACKENDS)}, "
                f"got {self.backend!r}"
            )
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"rendering.width and rendering.height must be positive, "
                f"got {self.width}x{self.height}"
            )
        if self.background_color is not None and not _HEX_COLOR_RE.match(self.background_color):
            raise ValueError(
                "rendering.background_color must be a '#RRGGBB' hex string, "
                f"got {self.background_color!r}"
            )
        if self.grid_color is not None and not _HEX_COLOR_RE.match(self.grid_color):
            raise ValueError(
                f"rendering.grid_color must be a '#RRGGBB' hex string, got {self.grid_color!r}"
            )
        if self.zoom <= 0:
            raise ValueError(f"rendering.zoom must be positive, got {self.zoom}")
        if self.zoom_min <= 0:
            raise ValueError(f"rendering.zoom_min must be positive, got {self.zoom_min}")
        if self.zoom_max <= self.zoom_min:
            raise ValueError(
                "rendering.zoom_min must be less than rendering.zoom_max, "
                f"got zoom_min={self.zoom_min}, zoom_max={self.zoom_max}"
            )
        if not (self.zoom_min <= self.zoom <= self.zoom_max):
            raise ValueError(
                "rendering.zoom must be within [rendering.zoom_min, rendering.zoom_max], "
                f"got zoom={self.zoom}, zoom_min={self.zoom_min}, zoom_max={self.zoom_max}"
            )


@dataclass
class MeshConfig:
    """Structured Cartesian mesh settings (TASK-012).

    `origin`/`spacing` construct the mesh's `UniformVertexCoordinateSystem`
    (TASK-011); `extent` is `(nx, ny)`, the number of cells along each
    axis. Exists so `StructuredCartesianMesh.from_config` can build a
    mesh entirely from `PyFlowConfig` -- no bespoke code -- which is what
    TASK-013's golden demo needs.

    Normalises YAML's lists (`origin: [1.5, -2.25]` parses as a Python
    `list`, not a `tuple`) to tuples in `__post_init__`, so the declared
    `tuple[float, float]`/`tuple[int, int]` types hold regardless of
    whether a value came from YAML or was constructed directly in code.
    """

    origin: tuple[float, float] = (0.0, 0.0)
    spacing: tuple[float, float] = (1.0, 1.0)
    extent: tuple[int, int] = (10, 10)

    def __post_init__(self) -> None:
        x0, y0 = self.origin
        dx, dy = self.spacing
        nx, ny = self.extent
        self.origin = (float(x0), float(y0))
        self.spacing = (float(dx), float(dy))
        self.extent = (int(nx), int(ny))

    def validate(self) -> None:
        dx, dy = self.spacing
        if dx <= 0 or dy <= 0:
            raise ValueError(f"mesh.spacing must be positive, got dx={dx}, dy={dy}")
        nx, ny = self.extent
        if nx <= 0 or ny <= 0:
            raise ValueError(f"mesh.extent must be positive, got nx={nx}, ny={ny}")


@dataclass
class PyFlowConfig:
    """The complete configuration for one PyFlow run."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    mesh: MeshConfig = field(default_factory=MeshConfig)

    def validate(self) -> None:
        self.logging.validate()
        self.rendering.validate()
        self.mesh.validate()
