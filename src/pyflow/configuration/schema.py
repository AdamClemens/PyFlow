"""Configuration schema: what a PyFlow run can be parameterised by.

Every field has a default, so `PyFlowConfig()` is a complete, valid
configuration on its own -- TASK-005's acceptance criterion is that the
application can be started entirely from configuration, which includes
the case where no config file is given at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RenderBackend = Literal["glfw", "offscreen"]

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_VALID_RENDER_BACKENDS = frozenset({"glfw", "offscreen"})


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
    """

    backend: RenderBackend = "glfw"
    width: int = 1280
    height: int = 720
    title: str = "PyFlow"

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


@dataclass
class PyFlowConfig:
    """The complete configuration for one PyFlow run."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    rendering: RenderingConfig = field(default_factory=RenderingConfig)

    def validate(self) -> None:
        self.logging.validate()
        self.rendering.validate()
