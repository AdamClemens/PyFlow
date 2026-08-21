"""Configuration schema: what a PyFlow run can be parameterised by.

Every field has a default, so `PyFlowConfig()` is a complete, valid
configuration on its own -- TASK-005's acceptance criterion is that the
application can be started entirely from configuration, which includes
the case where no config file is given at all.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal, get_args

RenderBackend = Literal["glfw", "offscreen"]

_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
# Derived from `RenderBackend`, not restated (P-011): the two would
# otherwise be two places to edit when a third backend arrives, and
# `__main__.py` already builds its `--backend` choices this same way.
_VALID_RENDER_BACKENDS = frozenset(get_args(RenderBackend))
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


# -- Value normalisation and type checking -------------------------------
#
# Configuration arrives from YAML, so a field's declared type is a
# statement about what valid input produces, not a guarantee about what
# `load_config` will be handed. These helpers turn "the wrong shape or
# type of thing" into the same field-named `ValueError` the hand-written
# checks below raise, rather than letting Python's own message escape.
# Added 2026-08-21 after an audit found three inputs that didn't:
# `width: "wide"` raised a bare `TypeError` from a comparison,
# `origin: [1.0, 2.0, 3.0]` raised "too many values to unpack", and
# `extent: [10.9, 3.99]` was silently truncated to `(10, 3)`.


def _number_pair(value: object, field_name: str) -> tuple[float, float]:
    """`value` as a 2-tuple of finite floats, or a `ValueError` naming
    `field_name`. Accepts any YAML sequence -- a list, which is what YAML
    parses `[1.5, -2.25]` into, as readily as a tuple.
    """
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a pair of numbers, got {value!r}")
    items = list(value)
    if len(items) != 2:
        raise ValueError(
            f"{field_name} must be a pair of numbers, got {len(items)} of them: {value!r}"
        )
    numbers = []
    for item in items:
        # bool is an int subclass; `true` in YAML is not a coordinate.
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field_name} must be a pair of numbers, got {value!r}")
        if not math.isfinite(item):
            raise ValueError(f"{field_name} must be finite, got {value!r}")
        numbers.append(float(item))
    return (numbers[0], numbers[1])


def _integer_pair(value: object, field_name: str) -> tuple[int, int]:
    """`value` as a 2-tuple of ints, or a `ValueError` naming
    `field_name`.

    `[10.0, 4.0]` is accepted -- a whole number written as a float, which
    YAML makes easy to do by accident and which is unambiguous.
    `[10.9, 3.99]` is rejected rather than truncated: a cell count is not
    a quantity to round on the user's behalf, and silently building a
    different mesh than the one asked for is worse than refusing.
    """
    x, y = _number_pair(value, field_name)
    for component in (x, y):
        if component != int(component):
            raise ValueError(f"{field_name} must be a pair of whole numbers, got {value!r}")
    return (int(x), int(y))


def _require_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer, got {value!r}")
    return value


def _require_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number, got {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite, got {value!r}")
    return float(value)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string, got {value!r}")
    return value


@dataclass
class LoggingConfig:
    """Logging framework settings (TASK-006)."""

    level: str = "INFO"

    def validate(self) -> None:
        _require_str(self.level, "logging.level")
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

    `show_mesh` (TASK-013) draws the configured mesh's grid lines;
    `grid_color` is the colour it draws them in. These were one field
    until 2026-08-21: `grid_color` was `str | None` and a non-`None`
    value was *also* how a demo asked for the mesh at all. That made a
    presentation detail into a feature switch -- there was no way to show
    the mesh in the default colour, and no way to record a preferred
    colour without also turning the mesh on. `background_color` keeps its
    `None`-means-off shape deliberately and is not the same case: `None`
    there means "add no background object", a real rendering state that
    pygfx distinguishes, not "no background".

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
    show_mesh: bool = False
    grid_color: str = "#4477aa"
    zoom: float = 1.0
    pan: tuple[float, float] = (0.0, 0.0)
    zoom_min: float = 0.1
    zoom_max: float = 10.0

    def __post_init__(self) -> None:
        self.pan = _number_pair(self.pan, "rendering.pan")

    def validate(self) -> None:
        _require_int(self.width, "rendering.width")
        _require_int(self.height, "rendering.height")
        _require_str(self.title, "rendering.title")
        _require_number(self.zoom, "rendering.zoom")
        _require_number(self.zoom_min, "rendering.zoom_min")
        _require_number(self.zoom_max, "rendering.zoom_max")
        if self.background_color is not None:
            _require_str(self.background_color, "rendering.background_color")
        _require_str(self.grid_color, "rendering.grid_color")
        if not isinstance(self.show_mesh, bool):
            raise ValueError(f"rendering.show_mesh must be true or false, got {self.show_mesh!r}")

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
        if not _HEX_COLOR_RE.match(self.grid_color):
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
        self.origin = _number_pair(self.origin, "mesh.origin")
        self.spacing = _number_pair(self.spacing, "mesh.spacing")
        self.extent = _integer_pair(self.extent, "mesh.extent")

    def validate(self) -> None:
        dx, dy = self.spacing
        if dx <= 0 or dy <= 0:
            raise ValueError(f"mesh.spacing must be positive, got dx={dx}, dy={dy}")
        nx, ny = self.extent
        if nx <= 0 or ny <= 0:
            raise ValueError(f"mesh.extent must be positive, got nx={nx}, ny={ny}")


ScalarDisplayPattern = Literal["radial_gradient"]
VectorDisplayPattern = Literal["rotational"]

_VALID_SCALAR_PATTERNS = frozenset(get_args(ScalarDisplayPattern))
_VALID_VECTOR_PATTERNS = frozenset(get_args(VectorDisplayPattern))


@dataclass
class FieldDisplayConfig:
    """Field visualisation settings (TASK-017).

    `scalar_pattern`/`vector_pattern` select from a small, closed set of
    built-in initial-condition patterns, for the golden demo only --
    `None` (the default) means "don't display that field." This is
    deliberately narrower than `Field`'s own general-callable Python API
    (TASK-015/016): YAML cannot carry a Python callable, and a safe
    expression parser is real scope this stage doesn't need just to let
    this demo satisfy the public-API rule. Real simulation scenarios
    (Stage 4 onward) construct fields directly in Python, where the
    general callable API already applies in full.

    `low_color`/`high_color`/`value_range` parameterise the scalar
    colour ramp (`src/pyflow/rendering/field_visualization.py`'s
    `scalar_field_colors`); `arrow_color`/`arrow_scale` the vector
    arrows. `show_legend` toggles the legend strip -- its screen
    position is computed from the mesh's own bounding box, not
    separately configurable, keeping this schema small.
    """

    scalar_pattern: ScalarDisplayPattern | None = None
    vector_pattern: VectorDisplayPattern | None = None
    low_color: str = "#0000ff"
    high_color: str = "#ff0000"
    value_range: tuple[float, float] = (0.0, 1.0)
    arrow_color: str = "#ffffff"
    arrow_scale: float = 0.3
    show_legend: bool = True

    def __post_init__(self) -> None:
        self.value_range = _number_pair(self.value_range, "field_display.value_range")

    def validate(self) -> None:
        if self.scalar_pattern is not None and self.scalar_pattern not in _VALID_SCALAR_PATTERNS:
            raise ValueError(
                f"field_display.scalar_pattern must be one of "
                f"{sorted(_VALID_SCALAR_PATTERNS)} or null, got {self.scalar_pattern!r}"
            )
        if self.vector_pattern is not None and self.vector_pattern not in _VALID_VECTOR_PATTERNS:
            raise ValueError(
                f"field_display.vector_pattern must be one of "
                f"{sorted(_VALID_VECTOR_PATTERNS)} or null, got {self.vector_pattern!r}"
            )
        _require_str(self.low_color, "field_display.low_color")
        if not _HEX_COLOR_RE.match(self.low_color):
            raise ValueError(
                f"field_display.low_color must be a '#RRGGBB' hex string, got {self.low_color!r}"
            )
        _require_str(self.high_color, "field_display.high_color")
        if not _HEX_COLOR_RE.match(self.high_color):
            raise ValueError(
                f"field_display.high_color must be a '#RRGGBB' hex string, got {self.high_color!r}"
            )
        _require_str(self.arrow_color, "field_display.arrow_color")
        if not _HEX_COLOR_RE.match(self.arrow_color):
            raise ValueError(
                f"field_display.arrow_color must be a '#RRGGBB' hex string, "
                f"got {self.arrow_color!r}"
            )
        v_min, v_max = self.value_range
        if v_max <= v_min:
            raise ValueError(
                f"field_display.value_range must have max > min, got {self.value_range}"
            )
        _require_number(self.arrow_scale, "field_display.arrow_scale")
        if self.arrow_scale <= 0:
            raise ValueError(f"field_display.arrow_scale must be positive, got {self.arrow_scale}")
        if not isinstance(self.show_legend, bool):
            raise ValueError(
                f"field_display.show_legend must be true or false, got {self.show_legend!r}"
            )


@dataclass
class PyFlowConfig:
    """The complete configuration for one PyFlow run."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    mesh: MeshConfig = field(default_factory=MeshConfig)
    field_display: FieldDisplayConfig = field(default_factory=FieldDisplayConfig)

    def validate(self) -> None:
        self.logging.validate()
        self.rendering.validate()
        self.mesh.validate()
        self.field_display.validate()
