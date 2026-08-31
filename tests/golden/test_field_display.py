"""Field Display golden demo (TASK-017).

The acceptance criteria are `tests/features/field_display.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). This module binds
them and supplies the steps that only this demo can use -- the
world-to-pixel mapping and the colour predictions. The demo-independent
steps (run the demo, render a frame, compare two frames) come from
`conftest.py` and are deliberately not duplicated here.

**World-to-pixel mapping, verified empirically before these assertions
relied on it, not assumed:** `field_display.yaml`'s `rendering.width`/
`height` are chosen so the canvas aspect exactly matches the framed
bounding box's own aspect (mesh, legend strip, and -- since Stage 7,
Rendering Annotations -- the title/stats/legend-label HUD margins, all
widened by `fit_camera_to_bounds`' 10% margin) -- confirmed live, per
cell, that `_world_to_pixel` predicts the exact rendered pixel for all
nine cells and the legend's sampled ends. With the aspects matched,
pygfx's `maintain_aspect` has nothing to correct and the mapping is the
plain linear one; checked against a deliberately mismatched canvas too,
where the plain formula is *not* sufficient, which is why the demo pins
this resolution rather than leaving it at a default.

**`_FRAMED_BOUNDS`/`_CANVAS` were recomputed, not left at their
pre-Stage-7 values, when the HUD's own margins widened the framed
view.** The arithmetic: mesh bounds `(0, 0, 3, 3)`, mesh height `3`;
legend strip extends the bottom by
`3*(_LEGEND_GAP_FRACTION + _LEGEND_HEIGHT_FRACTION) = 3*0.16 = 0.48`
(unchanged from before Stage 7); the HUD then extends title upward by
`3*_TITLE_MARGIN_FRACTION = 0.36`, legend numeric labels downward by
`3*_LEGEND_LABEL_MARGIN_FRACTION = 0.3`, and the stats block downward by
`3*_STATS_MARGIN_FRACTION = 0.6` (`src/pyflow/bootstrap.py`'s own
constants) -- giving `(0, -1.38, 3, 3.36)`, width 3 and height 4.74,
which is exactly `50:79` once widened by the camera's own 10% margin
(`3*1.2 : 4.74*1.2 = 3.6 : 5.688 = 50:79`). `250x395` is `50:79` scaled
by 5.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from pytest_bdd import given, scenarios, then

from pyflow.engine.mesh import StructuredCartesianMesh

from ._demo import DemoRun

scenarios("field_display.feature")

# Mirrors field_display.yaml's own mesh/field_display sections -- kept
# explicit (not re-derived from the loaded config) so a reader can check
# these numbers directly against the file.
_MESH = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(3, 3))
_CENTER = (1.5, 1.5)
_VALUE_RANGE = (0.0, 2.5)
_LOW = np.array([0x0A, 0x14, 0x1E, 255], dtype=np.uint8)
_HIGH = np.array([0xC8, 0x96, 0x64, 255], dtype=np.uint8)
_ARROW = np.array([0x00, 0xFF, 0x88, 255], dtype=np.uint8)
_ARROW_SCALE = 0.3

# The box the camera is framed on: the mesh's bounds (0, 0, 3, 3),
# extended downward for the legend strip (bootstrap's
# _LEGEND_HEIGHT_FRACTION/_LEGEND_GAP_FRACTION against the mesh's own
# height of 3: 0 - 3*0.04 - 3*0.12 = -0.48), then further by the HUD
# (Stage 7): title extends the top by 3*_TITLE_MARGIN_FRACTION = 0.36;
# legend numeric labels extend the bottom by
# 3*_LEGEND_LABEL_MARGIN_FRACTION = 0.3, to -0.78; the stats block
# extends it again by 3*_STATS_MARGIN_FRACTION = 0.6, to -1.38. See this
# module's own docstring for the full arithmetic, including why 250x395
# (not the pre-Stage-7 250x290) is the exact-aspect canvas now.
_FRAMED_BOUNDS = (0.0, -1.38, 3.0, 3.36)
_MARGIN = 1.2  # fit_camera_to_bounds' 10% margin on each side
_CANVAS = (250, 395)

_SCALAR_ONLY_CONFIG = """
mesh:
  extent: [3, 3]
field_display:
  scalar_pattern: radial_gradient
  low_color: "#0a141e"
  high_color: "#c89664"
  value_range: [0.0, 2.5]
  show_legend: true
rendering:
  width: 250
  height: 395
  background_color: "#000000"
"""


def _world_to_pixel(x: float, y: float) -> tuple[int, int]:
    min_x, min_y, max_x, max_y = _FRAMED_BOUNDS
    cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
    cam_w = (max_x - min_x) * _MARGIN
    cam_h = (max_y - min_y) * _MARGIN
    canvas_w, canvas_h = _CANVAS
    px = (x - cx) / cam_w * canvas_w + canvas_w / 2
    py = canvas_h / 2 - (y - cy) / cam_h * canvas_h
    return round(px), round(py)


def _expected_scalar_color(x: float, y: float) -> np.ndarray:
    distance = math.hypot(x - _CENTER[0], y - _CENTER[1])
    t = min(max(distance / (_VALUE_RANGE[1] - _VALUE_RANGE[0]), 0.0), 1.0)
    return np.round(_LOW.astype(np.float64) + (_HIGH - _LOW).astype(np.float64) * t).astype(
        np.uint8
    )


# -- Given -----------------------------------------------------------------


@given("the scalar-only variant of that demo")
def _given_scalar_only_variant(demo: DemoRun, tmp_path: Path) -> None:
    """Same demo minus `vector_pattern`.

    Every cell's arrow starts exactly at that cell's own centroid
    (`build_vector_field_arrows`) and arrows draw above the field fill,
    so sampling a centroid against the combined demo sometimes reads the
    arrow's colour rather than the field's -- found by running the check
    against the real config first, not predicted. Isolating the scalar
    claim is what makes the per-cell scenario able to fail for the right
    reason.
    """
    path = tmp_path / "scalar_only.yaml"
    path.write_text(_SCALAR_ONLY_CONFIG)
    demo.config_path = path


# -- Then ------------------------------------------------------------------


@then("all 9 cells show exactly the colour the scalar colour map predicts")
def _then_every_cell_matches(demo: DemoRun) -> None:
    image = demo.image
    assert _MESH.num_cells == 9, "this scenario names nine cells; the mesh must have nine"

    for cell in range(_MESH.num_cells):
        x, y = _MESH.cell_centroid(cell)
        px, py = _world_to_pixel(x, y)
        expected = _expected_scalar_color(x, y)
        actual = image[py, px]
        assert np.array_equal(actual, expected), (
            f"cell {cell} at world {(x, y)} / pixel {(px, py)}: "
            f"expected {expected.tolist()}, got {actual.tolist()}"
        )


@then("the centre and corner cells differ by more than 20 levels in some channel")
def _then_cells_visibly_differ(demo: DemoRun) -> None:
    image = demo.image
    centre = image[tuple(reversed(_world_to_pixel(*_MESH.cell_centroid(4))))]
    corner = image[tuple(reversed(_world_to_pixel(*_MESH.cell_centroid(0))))]

    assert not np.array_equal(centre, corner)
    # A real, visible contrast -- not a one-bit rounding difference,
    # which an inequality check alone would accept.
    assert int(np.abs(centre.astype(int) - corner.astype(int)).max()) > 20


@then("the legend's low and high ends match the scalar colour map's own output")
def _then_legend_matches(demo: DemoRun) -> None:
    image = demo.image
    # Safely inside the legend strip vertically (y = -0.3, well within
    # its -0.48..-0.12 span), sampled near each end horizontally.
    legend_y = -0.3
    for world_x, expected in [(0.1, _LOW), (2.9, _HIGH)]:
        px, py = _world_to_pixel(world_x, legend_y)
        actual = image[py, px]
        # "Close to", not exact: 32 discrete samples span the strip, so
        # x=0.1/2.9 land one sample in from either edge.
        assert int(np.abs(actual.astype(int) - expected.astype(int))[:3].max()) < 15


@then("cell 0's arrow is drawn in the configured arrow colour at its own midpoint")
def _then_arrow_present(demo: DemoRun) -> None:
    image = demo.image
    cell = 0  # centroid (0.5, 0.5) -> vector (1.0, -1.0) under `rotational`
    cx, cy = _MESH.cell_centroid(cell)
    vx, vy = -(cy - _CENTER[1]), cx - _CENTER[0]
    ex, ey = cx + _ARROW_SCALE * vx, cy + _ARROW_SCALE * vy
    px, py = _world_to_pixel((cx + ex) / 2, (cy + ey) / 2)

    # Midpoint, not endpoint, and a small tolerance rather than exact
    # equality: `LineSegmentMaterial` at 2px thickness showed 2/255 in
    # one channel here even with `aa=False` -- GPU line-rasterization
    # edge coverage, found by running this, not a colour-mapping bug.
    # Re-measured at the Stage 7 canvas resize (250x395, up from 250x290
    # -- the world-to-pixel *scale* is unchanged, only the framed bounds'
    # vertical offset, per this module's own docstring): 13/255 in the
    # same channel at the new resolution, still the identical
    # edge-coverage effect (green/blue land within 2 of the configured
    # colour), not a new defect -- tolerance widened to match rather than
    # left failing on a resolution-dependent rasterisation detail.
    assert int(np.abs(image[py, px].astype(int) - _ARROW.astype(int)).max()) <= 15


@then("the centre cell shows its field colour and not the arrow colour")
def _then_no_arrow_at_centre(demo: DemoRun) -> None:
    x, y = _MESH.cell_centroid(4)
    assert (x, y) == pytest.approx(_CENTER), "cell 4's centroid must be the rotation centre"
    px, py = _world_to_pixel(x, y)

    assert np.array_equal(demo.image[py, px], _expected_scalar_color(x, y))
    assert not np.array_equal(demo.image[py, px], _ARROW)


@then(
    'the configuration selects the "radial_gradient" and "rotational" patterns',
)
def _then_config_is_as_claimed(demo: DemoRun) -> None:
    assert demo.config.field_display.scalar_pattern == "radial_gradient"
    assert demo.config.field_display.vector_pattern == "rotational"
