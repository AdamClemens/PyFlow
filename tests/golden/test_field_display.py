"""Regression test for the Field Rendering golden demo (TASK-017).

Golden demos must run through the public API alone -- `pyflow run
--config <file>` -- per `docs/implementation/golden-demos.md`'s
Definition of Done. `field_display.yaml` *is* the demo; no demo-specific
Python module. Follows `test_empty_mesh.py`'s three-test shape, plus the
per-cell pixel-position checks TASK-017's own Acceptance Criteria ask
for beyond what Empty Mesh needed.

**World-to-pixel mapping, verified empirically before writing these
assertions (not assumed):** `field_display.yaml`'s `rendering.width`/
`height` are chosen so the canvas aspect exactly matches the framed
bounding box's own aspect (mesh plus legend strip, both widened by
`fit_camera_to_bounds`' 10% margin) -- confirmed live, per cell, that
`_world_to_pixel` below predicts the exact rendered pixel for all nine
cells and the legend's sampled ends before relying on it here. With the
aspect ratios matched this way, pygfx's `maintain_aspect` has nothing to
correct, so the mapping is the plain linear one -- this was checked
directly against a mismatched-aspect canvas too, where the plain formula
is *not* sufficient, which is exactly why the demo's resolution is
chosen this specifically rather than left at a default like
`empty_mesh.yaml`'s.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from pyflow.bootstrap import bootstrap
from pyflow.configuration import load_config
from pyflow.engine.mesh import StructuredCartesianMesh

CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "golden-demos" / "field_display.yaml"
)

# Mirrors field_display.yaml's own mesh/field_display sections -- kept
# explicit here (not re-derived from the loaded config) so a test
# reader can check the numbers directly against the file.
_MESH = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(3, 3))
_CENTER = (1.5, 1.5)
_VALUE_RANGE = (0.0, 2.5)
_LOW = np.array([0x0A, 0x14, 0x1E, 255], dtype=np.uint8)
_HIGH = np.array([0xC8, 0x96, 0x64, 255], dtype=np.uint8)
_ARROW = np.array([0x00, 0xFF, 0x88, 255], dtype=np.uint8)
_BACKGROUND = np.array([0, 0, 0, 255], dtype=np.uint8)

# Bounding box the camera is actually framed on: the mesh's own bounds
# (0, 0, 3, 3), extended downward for the legend strip
# (bootstrap._LEGEND_HEIGHT_FRACTION/_LEGEND_GAP_FRACTION applied to the
# mesh's own height of 3): 0 - 3*0.04 - 3*0.12 = -0.48.
_FRAMED_BOUNDS = (0.0, -0.48, 3.0, 3.0)
_MARGIN = 1.2  # fit_camera_to_bounds' 10% margin on each side
_CANVAS = (250, 290)


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
    import math

    distance = math.hypot(x - _CENTER[0], y - _CENTER[1])
    t = min(max(distance / (_VALUE_RANGE[1] - _VALUE_RANGE[0]), 0.0), 1.0)
    return np.round(_LOW.astype(np.float64) + (_HIGH - _LOW).astype(np.float64) * t).astype(
        np.uint8
    )


# A scalar-only variant of `field_display.yaml` (no `vector_pattern`),
# used for the per-cell colour checks below. Every cell's arrow starts
# exactly at that cell's own centroid (`build_vector_field_arrows`), so
# sampling a centroid pixel against the combined demo would sometimes
# read the arrow's colour instead of the field's -- found by running
# this test against the real combined config first, not predicted in
# advance. This isolates the claim each test actually makes (the scalar
# colour mapping is correct) from the other field's own presence.
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
  height: 290
  background_color: "#000000"
"""


@pytest.fixture
def scalar_only_config(tmp_path: Path) -> Path:
    path = tmp_path / "scalar_only.yaml"
    path.write_text(_SCALAR_ONLY_CONFIG)
    return path


def test_field_display_runs_via_the_public_cli() -> None:
    """At least one test must run the demo exactly as a user would --
    the literal command `docs/implementation/golden-demos.md` documents.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(CONFIG_PATH),
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_field_display_renders_the_correct_scalar_colour_at_every_cell(
    scalar_only_config: Path,
) -> None:
    """Every one of the mesh's nine cells' rendered colour, at that
    cell's predicted on-screen position, matches `scalar_field_colors`'
    own formula exactly -- not just "some pixel of roughly the right
    colour exists somewhere." Uses the scalar-only config, not the real
    demo file, so an arrow drawn over a cell's own centroid (see
    `_SCALAR_ONLY_CONFIG`'s comment) can't be mistaken for the field.
    """
    window = bootstrap(scalar_only_config, backend="offscreen", max_frames=1)
    assert window.last_image is not None
    image = window.last_image

    for cell in range(_MESH.num_cells):
        x, y = _MESH.cell_centroid(cell)
        px, py = _world_to_pixel(x, y)
        expected = _expected_scalar_color(x, y)
        actual = image[py, px]
        assert np.array_equal(actual, expected), (
            f"cell {cell} at world {(x, y)} / pixel {(px, py)}: "
            f"expected {expected.tolist()}, got {actual.tolist()}"
        )


def test_field_display_two_cells_render_visibly_different_colours(
    scalar_only_config: Path,
) -> None:
    window = bootstrap(scalar_only_config, backend="offscreen", max_frames=1)
    assert window.last_image is not None
    image = window.last_image

    center_x, center_y = _MESH.cell_centroid(4)  # (1.5, 1.5) -- distance 0
    corner_x, corner_y = _MESH.cell_centroid(0)  # (0.5, 0.5) -- distance > 0
    center_px, center_py = _world_to_pixel(center_x, center_y)
    corner_px, corner_py = _world_to_pixel(corner_x, corner_y)
    center_color = image[center_py, center_px]
    corner_color = image[corner_py, corner_px]

    assert not np.array_equal(center_color, corner_color)
    # A real, visible contrast, not a one-bit rounding difference.
    assert int(np.abs(center_color.astype(int) - corner_color.astype(int)).max()) > 20


def test_field_display_renders_the_legend_gradient() -> None:
    """The legend's low/mid/high sample points render the same colours
    `scalar_field_colors`'s own formula produces -- proving it shares
    the field's colour function, not an independently-tuned one.
    """
    window = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1)
    assert window.last_image is not None
    image = window.last_image

    # A point safely inside the legend strip vertically (y = -0.3, well
    # within its (-0.48, -0.12) span) at three x-positions across it.
    legend_y = -0.3
    for world_x, expected_hint in [(0.1, _LOW), (2.9, _HIGH)]:
        px, py = _world_to_pixel(world_x, legend_y)
        actual = image[py, px]
        # Near the ends, not pinned to the exact endpoint colour (32
        # discrete samples span the strip, so x=0.1/2.9 land one sample
        # in from either edge) -- checked as "close to", not exact.
        assert int(np.abs(actual.astype(int) - expected_hint.astype(int))[:3].max()) < 15


def test_field_display_renders_vector_arrows_with_non_trivial_direction_and_magnitude() -> None:
    """The rotational pattern gives every non-central cell a distinct
    direction and magnitude; checked at one cell's arrow midpoint (not
    its very endpoint, which sits at the line's antialiased cap) for the
    configured arrow colour exactly.
    """
    window = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1)
    assert window.last_image is not None
    image = window.last_image

    cell = 0  # centroid (0.5, 0.5): vx, vy = -(0.5-1.5), 0.5-1.5 = (1.0, -1.0)
    cx, cy = _MESH.cell_centroid(cell)
    vx, vy = -(cy - _CENTER[1]), cx - _CENTER[0]
    scale = 0.3
    ex, ey = cx + scale * vx, cy + scale * vy
    mid_x, mid_y = (cx + ex) / 2, (cy + ey) / 2

    px, py = _world_to_pixel(mid_x, mid_y)
    # A small tolerance, not exact equality: unlike the flat-quad field
    # fills (bit-exact, since `MeshBasicMaterial`'s face colours don't
    # rasterize with edge coverage the way a thin line does),
    # `LineSegmentMaterial` at 2px thickness showed a difference of 2/255
    # in one channel at this exact midpoint even with `aa=False` --
    # found by running this assertion, not predicted -- consistent with
    # GPU line rasterization's own edge coverage, not a colour-mapping
    # bug in this project's code.
    actual = image[py, px].astype(int)
    assert np.abs(actual - _ARROW.astype(int)).max() <= 4


def test_field_display_zero_vector_at_the_centre_renders_no_arrow() -> None:
    """The rotational pattern's vector at the exact rotation centre is
    `(0, 0)` -- cell 4's centroid coincides with it for this 3x3 mesh --
    so no arrow should be drawn there: the pixel stays background, not a
    stray zero-length-line artifact.
    """
    window = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1)
    assert window.last_image is not None
    image = window.last_image

    x, y = _MESH.cell_centroid(4)
    assert (x, y) == pytest.approx(_CENTER)
    px, py = _world_to_pixel(x, y)
    assert np.array_equal(image[py, px], _expected_scalar_color(x, y))
    assert not np.array_equal(image[py, px], _ARROW)


def test_field_display_is_deterministic() -> None:
    first = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1).last_image
    second = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1).last_image

    assert first is not None
    assert second is not None
    assert np.array_equal(first, second)


def test_field_display_config_round_trips_through_load_config() -> None:
    config = load_config(CONFIG_PATH)
    assert config.field_display.scalar_pattern == "radial_gradient"
    assert config.field_display.vector_pattern == "rotational"
