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

import math
from collections.abc import Callable
from pathlib import Path

from pyflow import __version__
from pyflow.configuration import load_config
from pyflow.configuration.schema import FieldDisplayConfig, RenderBackend
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.assembly import assemble_numerics
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField
from pyflow.rendering import RenderWindow
from pyflow.rendering.field_visualization import (
    build_field_legend,
    build_scalar_field_mesh,
    build_vector_field_arrows,
    scalar_field_colors,
)
from pyflow.rendering.mesh_visualization import (
    build_mesh_grid_line,
    fit_camera_to_bounds,
    mesh_bounding_box,
)

logger = get_logger(__name__)

# Fraction of the mesh's own height reserved for the legend strip drawn
# beneath it, and the gap left between the two. The legend extends past
# the mesh's own bounding box, so the camera must be framed on the
# combined box `_add_field_display` returns, not the mesh's bounds alone
# (`fit_camera_to_bounds`, not TASK-013's mesh-only `fit_camera_to_mesh`).
_LEGEND_HEIGHT_FRACTION = 0.12
_LEGEND_GAP_FRACTION = 0.04

# Z-offsets so overlapping same-plane content composites predictably
# (arrows/legend drawn over field fills) rather than depending on draw
# order at equal depth, which this renderer's tie-breaking behaviour was
# never verified for.
_ARROWS_Z = 0.01
_LEGEND_Z = 0.02

_Bounds = tuple[float, float, float, float]


def _scalar_display_initializer(
    pattern: str, center: tuple[float, float]
) -> Callable[[float, float], float]:
    """A `Field`-style `(x, y) -> value` callable for `pattern`."""
    cx, cy = center
    if pattern == "radial_gradient":
        return lambda x, y: math.hypot(x - cx, y - cy)
    raise ValueError(f"unknown scalar display pattern: {pattern!r}")  # pragma: no cover


def _vector_display_initializer(
    pattern: str, center: tuple[float, float]
) -> Callable[[float, float], tuple[float, float]]:
    """A `Field`-style `(x, y) -> (vx, vy)` callable for `pattern`."""
    cx, cy = center
    if pattern == "rotational":
        return lambda x, y: (-(y - cy), x - cx)
    raise ValueError(f"unknown vector display pattern: {pattern!r}")  # pragma: no cover


def _add_field_display(
    window: RenderWindow, mesh: Mesh, field_display: FieldDisplayConfig
) -> _Bounds:
    """Build and add whatever `field_display` asks for -- the scalar
    colour map, its legend, and the vector arrows -- entirely from
    configuration, per the golden-demo public-API rule. Does nothing for
    whichever of scalar/vector isn't configured (`None`, the default for
    both).

    Returns the bounding box the caller should frame the camera on:
    the mesh's own bounds, extended downward to include the legend strip
    if one was drawn.
    """
    bounds = mesh_bounding_box(mesh)
    min_x, min_y, max_x, max_y = bounds
    center = ((min_x + max_x) / 2, (min_y + max_y) / 2)

    if field_display.scalar_pattern is not None:
        scalar_initializer = _scalar_display_initializer(field_display.scalar_pattern, center)
        scalar_field = ScalarField(mesh, "scalar_display", initial_value=scalar_initializer)
        colors = scalar_field_colors(
            scalar_field,
            field_display.low_color,
            field_display.high_color,
            field_display.value_range,
        )
        window.scene.add(build_scalar_field_mesh(scalar_field, colors))

        if field_display.show_legend:
            mesh_height = max_y - min_y
            legend_height = mesh_height * _LEGEND_HEIGHT_FRACTION
            gap = mesh_height * _LEGEND_GAP_FRACTION
            legend_bottom = min_y - gap - legend_height
            legend_bounds = (min_x, legend_bottom, max_x, min_y - gap)
            legend = build_field_legend(
                field_display.low_color,
                field_display.high_color,
                field_display.value_range,
                legend_bounds,
            )
            legend.local.position = (0.0, 0.0, _LEGEND_Z)
            window.scene.add(legend)
            bounds = (min_x, legend_bottom, max_x, max_y)

    if field_display.vector_pattern is not None:
        vector_initializer = _vector_display_initializer(field_display.vector_pattern, center)
        vector_field = VectorField(
            mesh, "vector_display", num_components=2, initial_value=vector_initializer
        )
        arrows = build_vector_field_arrows(
            vector_field, field_display.arrow_color, field_display.arrow_scale
        )
        if arrows is not None:
            arrows.local.position = (0.0, 0.0, _ARROWS_Z)
            window.scene.add(arrows)

    return bounds


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
    (`window.last_image`) rather than only that nothing raised, and
    (TASK-021) what got assembled from `config.numerics`
    (`window.assembled_numerics`).
    """
    config = load_config(config_path)
    if backend is not None:
        config.rendering.backend = backend
        config.rendering.validate()
    configure_logging(config.logging)

    logger.info("pyflow %s bootstrapping", __version__)
    window = RenderWindow(config.rendering)

    # TASK-021: assemble all six numerics components from `config.numerics`
    # and report the result -- Stage 3 Completion Criterion 8. Every run
    # does this, not only ones that need numerics for anything yet, since
    # `NumericsConfig` always has a full section (defaulted or not) and
    # assembly must not depend on whether a caller happens to care.
    window.assembled_numerics = assemble_numerics(config.numerics)
    logger.info("numerics assembled: %s", window.assembled_numerics.names)

    show_fields = (
        config.field_display.scalar_pattern is not None
        or config.field_display.vector_pattern is not None
    )
    if config.rendering.show_mesh or show_fields:
        # TASK-013/017: visualise the configured mesh's grid and/or its
        # fields -- no bespoke code, per the golden-demo public-API rule.
        # `show_mesh` is gated separately from `grid_color` being set
        # (changed 2026-08-21): a colour is a colour, not a feature
        # switch. `fit_camera_to_bounds` must run before
        # `apply_camera_config` below: it sets the "zoom == 1" base view
        # (and centres the camera), which configured zoom/pan then apply
        # on top of. `bounds` starts as the mesh's own bounding box and
        # `_add_field_display` widens it if a legend was drawn below the
        # mesh -- when only `show_mesh` is set, this is exactly what
        # `fit_camera_to_mesh` used to compute directly, unchanged.
        mesh = StructuredCartesianMesh.from_config(config.mesh)
        bounds = mesh_bounding_box(mesh)
        if config.rendering.show_mesh:
            window.scene.add(build_mesh_grid_line(mesh, config.rendering.grid_color))
        if show_fields:
            bounds = _add_field_display(window, mesh, config.field_display)
        fit_camera_to_bounds(window.camera, bounds)

    window.apply_camera_config()

    window.run(max_frames=max_frames)
    logger.info("pyflow exited cleanly")
    return window
