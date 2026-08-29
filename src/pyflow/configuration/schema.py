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


ScalarTransportPattern = Literal["gaussian_blob", "sinusoidal_mode"]
VelocityPrescriptionPattern = Literal["uniform"]

_VALID_SCALAR_TRANSPORT_PATTERNS = frozenset(get_args(ScalarTransportPattern))
_VALID_VELOCITY_PRESCRIPTION_PATTERNS = frozenset(get_args(VelocityPrescriptionPattern))


@dataclass
class SimulationConfig:
    """Live simulation stepping (TASK-030) -- distinct from
    `FieldDisplayConfig` above, which seeds one static rendered frame.
    `scalar_pattern`/`velocity_pattern` here seed a real, repeatedly
    `simulation.step()`-advanced run, driven from `RenderWindow.run(
    on_frame=...)` (`src/pyflow/bootstrap.py`) -- Stage 4's own Passive
    Scalar Transport golden demo, and the first config section to wire a
    live timestepping loop into an actual `pyflow run` at all.

    `None` (the default, for both) means no live simulation -- every
    existing demo (`field_display`, `numerics_assembly`) is unaffected.
    Colouring the live field reuses `field_display.low_color`/
    `high_color`/`value_range`/`show_legend` as-is, deliberately not
    duplicated here: those already answer "how is a scalar field
    coloured", a question this section has no reason to answer twice.

    Shape parameters (the blob's own center and width) are deliberately
    not configurable here, derived from the mesh's own bounds in
    `bootstrap.py` instead -- the same "derived from mesh bounds, not a
    config field" precedent `FieldDisplayConfig`'s own
    `_scalar_display_initializer`'s `center` already set, keeping this
    section small the same way `FieldDisplayConfig` stays small.
    `velocity` is a prescribed (not solved) constant vector by default --
    `velocity_solved` (TASK-031, added 2026-08-29) is what lets a run ask
    for the other kind. Stage 5 is what eventually solves Navier-Stokes
    for real; Stage 4 demos, and this section's own default, can only
    have the prescribed kind.

    **`velocity_solved: bool` is a separate field from `velocity_pattern`,
    deliberately -- not a widened `velocity_pattern` value.** A pattern
    says *what shape* the initial condition has (`velocity_pattern`
    already answers that, `"uniform"` being the only one so far);
    solved-vs-prescribed says *what happens to it afterward* (transported
    by `step`, or held fixed every frame). Conflating a switch with the
    thing it configures is a mistake this project has made once already
    and corrected (`RenderingConfig.show_mesh`/`grid_color`, `src/pyflow/
    configuration/CLAUDE.md`'s own entry) -- the same shape here: folding
    `"solved"` into `velocity_pattern` would mean there is no way to ask
    for a *non-uniform* solved initial condition without inventing a
    second closed set, and no way to record a preferred pattern without
    also deciding whether it is solved. `velocity` still seeds the
    initial condition either way -- `velocity_solved` decides only
    whether `step` transports it afterward.
    """

    scalar_pattern: ScalarTransportPattern | None = None
    velocity_pattern: VelocityPrescriptionPattern | None = None
    velocity: tuple[float, float] = (1.0, 0.0)
    velocity_solved: bool = False

    def __post_init__(self) -> None:
        self.velocity = _number_pair(self.velocity, "simulation.velocity")

    def validate(self) -> None:
        if (
            self.scalar_pattern is not None
            and self.scalar_pattern not in _VALID_SCALAR_TRANSPORT_PATTERNS
        ):
            raise ValueError(
                f"simulation.scalar_pattern must be one of "
                f"{sorted(_VALID_SCALAR_TRANSPORT_PATTERNS)} or null, got {self.scalar_pattern!r}"
            )
        if (
            self.velocity_pattern is not None
            and self.velocity_pattern not in _VALID_VELOCITY_PRESCRIPTION_PATTERNS
        ):
            raise ValueError(
                f"simulation.velocity_pattern must be one of "
                f"{sorted(_VALID_VELOCITY_PRESCRIPTION_PATTERNS)} or null, "
                f"got {self.velocity_pattern!r}"
            )
        if not isinstance(self.velocity_solved, bool):
            raise ValueError(
                f"simulation.velocity_solved must be true or false, got {self.velocity_solved!r}"
            )


@dataclass
class FluidConfig:
    """Physical properties of the simulated fluid (TASK-041, added
    2026-08-28) -- separate from `NumericsConfig` below, which selects
    numerical *schemes* and their solver tunables, not properties of the
    fluid those schemes act on (Stage 5's design question four,
    `docs/planning/roadmap.md`).

    `diffusion_coefficient` migrates here from
    `NumericsConfig.diffusion_coefficient` (TASK-024's original field) --
    Gamma, a transported scalar's own diffusivity. `viscosity` is new:
    momentum's own diffusion coefficient, distinct from a scalar's
    (TASK-031b threads it into the diffusive flux `assemble_numerics`
    builds for velocity's own components). Both default to `1.0`, the
    same arbitrary-MVP-scaffolding reasoning `NumericsConfig.timestep`'s
    `0.01` already carries -- no golden demo or handbook page names a
    specific value for either yet.
    """

    viscosity: float = 1.0
    diffusion_coefficient: float = 1.0

    def validate(self) -> None:
        _require_number(self.viscosity, "fluid.viscosity")
        if self.viscosity <= 0:
            raise ValueError(f"fluid.viscosity must be > 0, got {self.viscosity!r}")
        _require_number(self.diffusion_coefficient, "fluid.diffusion_coefficient")
        if self.diffusion_coefficient <= 0:
            raise ValueError(
                f"fluid.diffusion_coefficient must be > 0, got {self.diffusion_coefficient!r}"
            )


AdvectionSchemeName = Literal["first_order_upwind"]
DiffusionSchemeName = Literal["central_difference"]
TimeIntegrationSchemeName = Literal["rk4"]
LinearSolverName = Literal["conjugate_gradient"]
PressureCouplingName = Literal["piso"]
BoundaryConditionType = Literal["dirichlet", "neumann", "periodic"]

_VALID_ADVECTION_SCHEMES = frozenset(get_args(AdvectionSchemeName))
_VALID_DIFFUSION_SCHEMES = frozenset(get_args(DiffusionSchemeName))
_VALID_TIME_INTEGRATION_SCHEMES = frozenset(get_args(TimeIntegrationSchemeName))
_VALID_LINEAR_SOLVERS = frozenset(get_args(LinearSolverName))
_VALID_PRESSURE_COUPLINGS = frozenset(get_args(PressureCouplingName))
_VALID_BOUNDARY_TYPES = frozenset(get_args(BoundaryConditionType))
_BOUNDARY_NAMES = ("north", "south", "east", "west")
_PAIRED_BOUNDARY = {"north": "south", "south": "north", "east": "west", "west": "east"}


@dataclass
class BoundaryFaceConfig:
    """One domain edge's boundary condition (TASK-019).

    `type` selects the condition shape -- `icds.md`'s Choices:
    `dirichlet`, `neumann`, `periodic`. `velocity`/`pressure` are the
    two quantities `icds.md` names as prescribable
    ("velocity and pressure cannot both be prescribed on the same
    boundary"); each is `None` when this boundary doesn't prescribe
    that quantity. `velocity` is the boundary-*normal* component only
    (positive = outward) -- sufficient for this task's net-flux
    criterion below; a richer per-component (e.g. tangential, for a
    lid-driven-cavity moving wall) value is deferred to whichever task
    builds a concrete condition against a real consumer (P-016), not
    modelled speculatively here.

    **`scalar_value` (TASK-028, added 2026-08-28) is a third, independent
    quantity -- the boundary value a real `DirichletBoundaryCondition`
    supplies to whichever transported *scalar* field asks (advection/
    diffusion's own consumer), not to velocity's own momentum-equation
    prescription `GreenGaussDivergence`/PISO reads through the same
    resolved condition object.** Deliberately a plain `float`, not
    `float | None` like `velocity`/`pressure` -- it carries no mutual-
    exclusivity or net-flux relation to either (`icds.md`'s Compatibility
    requirements are specifically about the momentum/pressure system), so
    it needs no "not prescribed" sentinel, and defaults to `0.0` for the
    same reason `velocity` does: every existing default `NumericsConfig`
    stays valid without a config author having to name it. Found and
    resolved here, not invented speculatively: `docs/planning/roadmap.md`
    TASK-040's own Design decisions flagged this exact gap --
    `BoundaryFaceConfig` had no field at all for an arbitrary transported
    scalar's own value, which TASK-030's Passive Scalar Transport demo
    needs to configure -- and named this task as the one to resolve it.
    A `DirichletBoundaryCondition` and a `PressureCoupling` strategy
    reading the *same* resolved condition for two different fields at the
    same wall, with two different required numbers, stays out of scope
    (P-016) -- Stage 4 exercises Advection/Diffusion and Pressure-Velocity
    Coupling under real Dirichlet boundaries separately, never together
    in one run, and the existing "one global set... does not yet express
    two fields' own values at once" note above already names the general
    case as deferred.

    **`scalar_gradient` (TASK-029, added 2026-08-28) is `scalar_value`'s
    Neumann counterpart -- the boundary gradient a real
    `NeumannBoundaryCondition` supplies to whichever transported scalar
    field asks.** Same reasoning as `scalar_value` throughout: a plain
    `float`, not `float | None`, no mutual-exclusivity/net-flux relation
    to `velocity`/`pressure`, defaults to `0.0` for the same "every
    existing default `NumericsConfig` stays valid" reason. TASK-028's own
    drafting named this exact gap in advance, inherited by this task
    rather than rediscovered here (`docs/planning/roadmap.md` TASK-029's
    own Intent).

    **`field_values`/`field_gradients` (TASK-031c, added 2026-08-29) are
    per-field-name overrides of `scalar_value`/`scalar_gradient`
    respectively** -- the general mechanism this wall's own "one global
    set of boundary conditions" limitation (TASK-040's own note, above)
    needed: two fields transported in one run can each be given their
    own prescribed value at this same wall (`u = U`, `v = 0` at a moving
    lid, the motivating example, but general -- any field name, not only
    a velocity component). A field's own name absent from either dict
    falls back to `scalar_value`/`scalar_gradient`, so every existing
    config (which sets neither) is unaffected. `DirichletBoundaryCondition`/
    `NeumannBoundaryCondition` read these through `assembly.py`'s own
    adapters (`_dirichlet_boundary_condition`/`_neumann_boundary_condition`),
    keyed at `evaluate()` time by whichever field is asking.
    """

    type: BoundaryConditionType = "dirichlet"
    velocity: float | None = 0.0
    pressure: float | None = None
    scalar_value: float = 0.0
    scalar_gradient: float = 0.0
    field_values: dict[str, float] = field(default_factory=dict)
    field_gradients: dict[str, float] = field(default_factory=dict)

    def validate(self, boundary_name: str) -> None:
        if self.type not in _VALID_BOUNDARY_TYPES:
            raise ValueError(
                f"numerics.boundary_conditions.{boundary_name}.type must be one of "
                f"{sorted(_VALID_BOUNDARY_TYPES)}, got {self.type!r}"
            )
        if self.velocity is not None:
            _require_number(self.velocity, f"numerics.boundary_conditions.{boundary_name}.velocity")
        if self.pressure is not None:
            _require_number(self.pressure, f"numerics.boundary_conditions.{boundary_name}.pressure")
        _require_number(
            self.scalar_value, f"numerics.boundary_conditions.{boundary_name}.scalar_value"
        )
        _require_number(
            self.scalar_gradient, f"numerics.boundary_conditions.{boundary_name}.scalar_gradient"
        )
        for key, val in self.field_values.items():
            _require_number(val, f"numerics.boundary_conditions.{boundary_name}.field_values.{key}")
        for key, val in self.field_gradients.items():
            _require_number(
                val, f"numerics.boundary_conditions.{boundary_name}.field_gradients.{key}"
            )


@dataclass
class BoundaryConditionsConfig:
    """One `BoundaryFaceConfig` per domain edge (TASK-019).

    Per-face shape/type checks live on `BoundaryFaceConfig.validate()`
    above; whole-configuration consistency (periodic pairing, dual
    prescription, net flux) is deliberately *not* here -- no individual
    face can see the others, and `PyFlowConfig.validate()` is where all
    three checks live instead, per this task's own design decision
    (`docs/planning/roadmap.md` TASK-019).
    """

    north: BoundaryFaceConfig = field(default_factory=BoundaryFaceConfig)
    south: BoundaryFaceConfig = field(default_factory=BoundaryFaceConfig)
    east: BoundaryFaceConfig = field(default_factory=BoundaryFaceConfig)
    west: BoundaryFaceConfig = field(default_factory=BoundaryFaceConfig)

    def validate(self) -> None:
        for name in _BOUNDARY_NAMES:
            getattr(self, name).validate(name)


def _validate_boundary_conditions_jointly(
    mesh: MeshConfig, boundary_conditions: BoundaryConditionsConfig
) -> None:
    """The three whole-configuration constraints `icds.md` records --
    periodic pairing, no dual prescription, and (only when every
    boundary prescribes velocity) zero net flux -- checked together
    because each is a relation between boundaries, not a property of
    one (`docs/planning/roadmap.md` TASK-019's design decision).
    """
    faces = {name: getattr(boundary_conditions, name) for name in _BOUNDARY_NAMES}

    for name, paired in _PAIRED_BOUNDARY.items():
        if faces[name].type == "periodic" and faces[paired].type != "periodic":
            raise ValueError(
                f"numerics.boundary_conditions.{name} is periodic but its paired boundary "
                f"{paired!r} is {faces[paired].type!r}, not periodic"
            )

    for name, face_config in faces.items():
        if face_config.velocity is not None and face_config.pressure is not None:
            raise ValueError(
                f"numerics.boundary_conditions.{name} prescribes both velocity and "
                "pressure; a boundary may prescribe only one"
            )

    velocities = {name: faces[name].velocity for name in _BOUNDARY_NAMES}
    if all(v is not None for v in velocities.values()):
        nx, ny = mesh.extent
        dx, dy = mesh.spacing
        lengths = {"north": nx * dx, "south": nx * dx, "east": ny * dy, "west": ny * dy}
        net_flux = sum(v * lengths[name] for name, v in velocities.items() if v is not None)
        if not math.isclose(net_flux, 0.0, abs_tol=1e-9):
            raise ValueError(
                "numerics.boundary_conditions: velocity prescribed on every boundary must "
                f"sum to zero net flux, got {net_flux!r}"
            )


@dataclass
class NumericsConfig:
    """Numerical scheme selection (TASK-018 onward, `adr/ADR-003-
    modular-numerical-strategies.md`).

    Each field names, by a closed set of known values, which strategy
    fills one of the six configuration-selected numerical components
    `docs/architecture/icds.md` describes -- validated immediately in
    `validate()`, the same pattern `rendering.backend` already
    established, rather than left to fail wherever the name is first
    used. `advection`/`diffusion` (TASK-018), `boundary_conditions`
    (TASK-019), `time_integration`/`timestep` (TASK-020),
    `linear_solver`/`linear_solver_tolerance`/`linear_solver_max_iterations`
    (TASK-022) and `pressure_coupling` (TASK-021) complete the section.
    Only one value validates for `advection`/`diffusion`/
    `time_integration`/`linear_solver`/`pressure_coupling`: `icds.md`'s
    sole named MVP choice for each. No real numerical scheme shipped
    under `src/` through Stage 3 (Stage 3 Completion Criterion 1), so a
    validated name resolved only to `engine/numerics/assembly.py`'s
    trivial, non-physical reference implementation -- Stage 4 replaces
    each in turn, `advection` first (TASK-023, 2026-08-27): a validated
    `"first_order_upwind"` now resolves to a real scheme
    (`FirstOrderUpwindAdvection`); the other four still resolve to their
    own reference implementation until their own task lands. See
    `assembly.py`'s own docstring for why a reference implementation is
    there at all, and for which name(s) still resolve to one.

    `timestep`/`linear_solver_tolerance`/`linear_solver_max_iterations`
    are plain positive numbers, not closed sets of names --
    `docs/planning/roadmap.md` TASK-020/022's design decisions (a fixed
    timestep with no automatic stability limit; convergence tolerance
    and iteration limit as the solver's own tunables, not baked into a
    scheme name). Their defaults (`0.01`, `1e-6`, `1000`) are all
    arbitrary MVP values -- no golden demo or handbook page names
    specific ones yet; rejecting each at `<= 0` is the one acceptance
    criterion each field carries on its own.

    `diffusion_coefficient` (TASK-024, added 2026-08-27; **migrated to
    `FluidConfig.diffusion_coefficient` by TASK-041, 2026-08-28**) used
    to live here, following the same plain-positive-number pattern as
    `timestep`: Gamma (`docs/handbook/numerical-methods/diffusion.md`),
    a physical property of what's being transported, not a scheme
    choice -- which is exactly why it moved: a fluid property has no
    business in the section that selects numerical schemes (Stage 5's
    design question four, `docs/planning/roadmap.md`). A config still
    setting `numerics.diffusion_coefficient` is rejected with a named
    error pointing at its new home (`loader.py`'s
    `_numerics_config_from_raw`), not silently ignored.

    **`pressure_correction_tolerance`/`pressure_correction_max_iterations`
    (TASK-033, added 2026-08-29) are the corrector *loop*'s own tunables
    -- distinct from `linear_solver_tolerance`/`linear_solver_max_iterations`
    above, which govern the *inner* linear solve each corrector pass
    makes, not how many passes the outer loop itself may take.** Same
    plain-positive-number pattern as every other tunable here; `PISO`'s
    own constructor is threaded these via `assemble_numerics`
    (`register_pressure_coupling`'s own widened factory), the "outer-loop
    state the strategy owns" resolution to Stage 5's design question
    three (`docs/planning/roadmap.md` TASK-033).
    """

    advection: AdvectionSchemeName = "first_order_upwind"
    diffusion: DiffusionSchemeName = "central_difference"
    time_integration: TimeIntegrationSchemeName = "rk4"
    timestep: float = 0.01
    linear_solver: LinearSolverName = "conjugate_gradient"
    linear_solver_tolerance: float = 1e-6
    linear_solver_max_iterations: int = 1000
    pressure_coupling: PressureCouplingName = "piso"
    pressure_correction_tolerance: float = 1e-6
    pressure_correction_max_iterations: int = 50
    boundary_conditions: BoundaryConditionsConfig = field(default_factory=BoundaryConditionsConfig)

    def validate(self) -> None:
        if self.advection not in _VALID_ADVECTION_SCHEMES:
            raise ValueError(
                f"numerics.advection must be one of {sorted(_VALID_ADVECTION_SCHEMES)}, "
                f"got {self.advection!r}"
            )
        if self.diffusion not in _VALID_DIFFUSION_SCHEMES:
            raise ValueError(
                f"numerics.diffusion must be one of {sorted(_VALID_DIFFUSION_SCHEMES)}, "
                f"got {self.diffusion!r}"
            )
        if self.time_integration not in _VALID_TIME_INTEGRATION_SCHEMES:
            raise ValueError(
                f"numerics.time_integration must be one of "
                f"{sorted(_VALID_TIME_INTEGRATION_SCHEMES)}, got {self.time_integration!r}"
            )
        if self.timestep <= 0:
            raise ValueError(f"numerics.timestep must be > 0, got {self.timestep!r}")
        if self.linear_solver not in _VALID_LINEAR_SOLVERS:
            raise ValueError(
                f"numerics.linear_solver must be one of {sorted(_VALID_LINEAR_SOLVERS)}, "
                f"got {self.linear_solver!r}"
            )
        if self.linear_solver_tolerance <= 0:
            raise ValueError(
                f"numerics.linear_solver_tolerance must be > 0, "
                f"got {self.linear_solver_tolerance!r}"
            )
        if self.linear_solver_max_iterations <= 0:
            raise ValueError(
                f"numerics.linear_solver_max_iterations must be > 0, "
                f"got {self.linear_solver_max_iterations!r}"
            )
        if self.pressure_coupling not in _VALID_PRESSURE_COUPLINGS:
            raise ValueError(
                f"numerics.pressure_coupling must be one of "
                f"{sorted(_VALID_PRESSURE_COUPLINGS)}, got {self.pressure_coupling!r}"
            )
        if self.pressure_correction_tolerance <= 0:
            raise ValueError(
                f"numerics.pressure_correction_tolerance must be > 0, "
                f"got {self.pressure_correction_tolerance!r}"
            )
        if self.pressure_correction_max_iterations <= 0:
            raise ValueError(
                f"numerics.pressure_correction_max_iterations must be > 0, "
                f"got {self.pressure_correction_max_iterations!r}"
            )
        self.boundary_conditions.validate()


@dataclass
class PyFlowConfig:
    """The complete configuration for one PyFlow run."""

    logging: LoggingConfig = field(default_factory=LoggingConfig)
    rendering: RenderingConfig = field(default_factory=RenderingConfig)
    mesh: MeshConfig = field(default_factory=MeshConfig)
    field_display: FieldDisplayConfig = field(default_factory=FieldDisplayConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    fluid: FluidConfig = field(default_factory=FluidConfig)
    numerics: NumericsConfig = field(default_factory=NumericsConfig)

    def validate(self) -> None:
        self.logging.validate()
        self.rendering.validate()
        self.mesh.validate()
        self.field_display.validate()
        self.simulation.validate()
        self.fluid.validate()
        self.numerics.validate()
        _validate_boundary_conditions_jointly(self.mesh, self.numerics.boundary_conditions)
