"""Unit tests for `src/pyflow/rendering/field_visualization.py` (TASK-017).

Pure colour-math and geometry-construction checks -- no actual GPU
render here, matching `test_mesh_visualization.py`'s own split: this
file checks the arrays/objects these functions build, and
`tests/golden/test_field_display.py` checks what they look like once
actually rendered (the real sRGB round-trip lives there, since it's a
property of the render pipeline, not of these functions' own output).
"""

from __future__ import annotations

import numpy as np
import pytest

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField
from pyflow.rendering.field_visualization import (
    build_field_legend,
    build_scalar_field_mesh,
    build_vector_field_arrows,
    scalar_field_colors,
)

_LOW = "#0a141e"  # (10, 20, 30, 255) -- every channel distinct
_HIGH = "#c89664"  # (200, 150, 100, 255) -- every channel distinct, and
# distinct from _LOW's own channels, so a bug that swaps R/B or forgets
# alpha produces a visibly wrong answer rather than an accidental match.


def _mesh(nx: int = 3, ny: int = 2) -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


# -- scalar_field_colors --------------------------------------------------


def test_scalar_field_colors_shape_and_dtype() -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "s", initial_value=1.0)
    colors = scalar_field_colors(field, _LOW, _HIGH, value_range=(0.0, 2.0))
    assert colors.shape == (mesh.num_cells, 4)
    assert colors.dtype == np.uint8


def test_scalar_field_colors_at_range_endpoints_and_midpoint() -> None:
    mesh = _mesh(nx=3, ny=1)
    field = ScalarField(mesh, "s")
    field.set_value_at(0, 0.0)
    field.set_value_at(1, 5.0)
    field.set_value_at(2, 10.0)

    colors = scalar_field_colors(field, _LOW, _HIGH, value_range=(0.0, 10.0))

    assert colors[0].tolist() == [10, 20, 30, 255]
    assert colors[2].tolist() == [200, 150, 100, 255]
    # Exact linear interpolation at the midpoint -- every channel checked,
    # not just one, since a bug in only one channel's lerp would
    # otherwise pass.
    expected_mid = [
        round((lo + hi) / 2) for lo, hi in zip((10, 20, 30, 255), (200, 150, 100, 255), strict=True)
    ]
    assert colors[1].tolist() == expected_mid


def test_scalar_field_colors_clamps_outside_the_configured_range() -> None:
    mesh = _mesh(nx=2, ny=1)
    field = ScalarField(mesh, "s")
    field.set_value_at(0, -100.0)  # far below range
    field.set_value_at(1, 100.0)  # far above range

    colors = scalar_field_colors(field, _LOW, _HIGH, value_range=(0.0, 10.0))

    assert colors[0].tolist() == [10, 20, 30, 255], "below-range value must clamp to low_color"
    assert colors[1].tolist() == [200, 150, 100, 255], "above-range value must clamp to high_color"


def test_scalar_field_colors_rejects_a_degenerate_range() -> None:
    field = ScalarField(_mesh(), "s")
    with pytest.raises(ValueError, match="value_range"):
        scalar_field_colors(field, _LOW, _HIGH, value_range=(5.0, 5.0))
    with pytest.raises(ValueError, match="value_range"):
        scalar_field_colors(field, _LOW, _HIGH, value_range=(5.0, 1.0))


# -- build_scalar_field_mesh -----------------------------------------------


def test_build_scalar_field_mesh_has_two_triangles_per_cell() -> None:
    mesh = _mesh(nx=3, ny=2)
    field = ScalarField(mesh, "s")
    colors = np.zeros((mesh.num_cells, 4), dtype=np.uint8)
    colors[:, 3] = 255
    obj = build_scalar_field_mesh(field, colors)
    assert obj.geometry.indices.data.shape == (mesh.num_cells * 2, 3)


def test_build_scalar_field_mesh_quad_matches_cell_corners() -> None:
    # A single cell's quad corners must be exactly the cell's own
    # geometry, not an approximation -- checked against `StructuredCartesianMesh`'s
    # own known formula for a 1x1 cell at a non-trivial origin/spacing.
    mesh = StructuredCartesianMesh(origin=(1.5, -2.25), spacing=(0.4, 0.6), extent=(1, 1))
    field = ScalarField(mesh, "s")
    colors = np.array([[255, 0, 0, 255]], dtype=np.uint8)
    obj = build_scalar_field_mesh(field, colors)

    corners = {tuple(round(float(c), 6) for c in row) for row in obj.geometry.positions.data[:, :2]}
    expected = {(1.5, -2.25), (1.9, -2.25), (1.9, -1.65), (1.5, -1.65)}
    assert corners == expected


def test_build_scalar_field_mesh_rejects_a_mismatched_colors_shape() -> None:
    mesh = _mesh(nx=3, ny=2)
    field = ScalarField(mesh, "s")
    wrong_shape = np.zeros((mesh.num_cells - 1, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="colors"):
        build_scalar_field_mesh(field, wrong_shape)


def test_build_scalar_field_mesh_uses_the_field_s_own_mesh() -> None:
    # Stage 2 Completion Criterion 1: a field carries its mesh, so this
    # builder takes no separate mesh argument that could disagree with
    # it. Checked by giving the field a mesh whose geometry no default
    # could coincide with -- if the quad corners match this mesh, they
    # came from `field.mesh` and nowhere else.
    mesh = StructuredCartesianMesh(origin=(-3.25, 7.5), spacing=(0.7, 0.9), extent=(1, 1))
    field = ScalarField(mesh, "s")
    obj = build_scalar_field_mesh(field, np.array([[255, 0, 0, 255]], dtype=np.uint8))

    corners = {tuple(round(float(c), 6) for c in row) for row in obj.geometry.positions.data[:, :2]}
    assert corners == {(-3.25, 7.5), (-2.55, 7.5), (-2.55, 8.4), (-3.25, 8.4)}


# -- build_vector_field_arrows ---------------------------------------------


def test_build_vector_field_arrows_segment_endpoints() -> None:
    mesh = _mesh(nx=2, ny=1)
    field = VectorField(mesh, "v", num_components=2)
    field.set_value_at(0, (1.0, 0.0))
    field.set_value_at(1, (0.0, 2.0))

    line = build_vector_field_arrows(field, color="#ffffff", scale=0.5)
    assert line is not None

    positions = line.geometry.positions.data[:, :2]
    assert positions.shape == (4, 2)  # 2 cells, 2 points (one segment) each

    c0 = mesh.cell_centroid(0)
    c1 = mesh.cell_centroid(1)
    expected = np.array(
        [
            c0,
            (c0[0] + 0.5 * 1.0, c0[1] + 0.5 * 0.0),
            c1,
            (c1[0] + 0.5 * 0.0, c1[1] + 0.5 * 2.0),
        ],
        dtype=np.float32,
    )
    np.testing.assert_allclose(positions, expected, atol=1e-5)


def test_build_vector_field_arrows_skips_zero_vectors() -> None:
    mesh = _mesh(nx=3, ny=1)
    field = VectorField(mesh, "v", num_components=2)
    field.set_value_at(0, (1.0, 0.0))
    field.set_value_at(1, (0.0, 0.0))  # zero -- must not produce a segment
    field.set_value_at(2, (0.0, -1.0))

    line = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    assert line is not None
    # Two non-zero cells -> two segments -> four points, not six.
    assert line.geometry.positions.data.shape[0] == 4


def test_build_vector_field_arrows_returns_none_when_every_vector_is_zero() -> None:
    mesh = _mesh(nx=2, ny=1)
    field = VectorField(mesh, "v", num_components=2)
    assert build_vector_field_arrows(field, color="#ffffff", scale=1.0) is None


def test_build_vector_field_arrows_uses_the_configured_color() -> None:
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 1.0))
    line = build_vector_field_arrows(field, color="#4477aa", scale=1.0)
    assert line is not None
    assert tuple(round(c, 4) for c in line.material.color)[:3] == (
        round(0x44 / 255, 4),
        round(0x77 / 255, 4),
        round(0xAA / 255, 4),
    )


# -- build_field_legend ------------------------------------------------


def test_build_field_legend_spans_the_given_bounds() -> None:
    bounds = (0.0, 0.0, 10.0, 1.0)
    obj = build_field_legend(_LOW, _HIGH, value_range=(0.0, 1.0), bounds=bounds, num_samples=8)

    xy = obj.geometry.positions.data[:, :2]
    assert xy[:, 0].min() == pytest.approx(0.0)
    assert xy[:, 0].max() == pytest.approx(10.0)
    assert xy[:, 1].min() == pytest.approx(0.0)
    assert xy[:, 1].max() == pytest.approx(1.0)


def test_build_field_legend_has_one_quad_per_sample() -> None:
    obj = build_field_legend(
        _LOW, _HIGH, value_range=(0.0, 1.0), bounds=(0.0, 0.0, 1.0, 1.0), num_samples=16
    )
    assert obj.geometry.indices.data.shape == (16 * 2, 3)


def test_build_field_legend_rejects_too_few_samples() -> None:
    with pytest.raises(ValueError, match="num_samples"):
        build_field_legend(
            _LOW, _HIGH, value_range=(0.0, 1.0), bounds=(0.0, 0.0, 1.0, 1.0), num_samples=1
        )


def test_build_vector_field_arrows_uses_the_field_s_own_mesh() -> None:
    # The companion to `test_build_scalar_field_mesh_uses_the_field_s_own_mesh`,
    # and the reason this builder lost its separate `mesh` argument:
    # arrow tails come from `field.mesh.cell_centroid`, so there is no
    # second mesh that could silently disagree with the values being
    # drawn (Stage 2 Completion Criterion 1).
    mesh = StructuredCartesianMesh(origin=(-3.25, 7.5), spacing=(0.7, 0.9), extent=(1, 1))
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, -1.0))
    line = build_vector_field_arrows(field, color="#ffffff", scale=2.0)
    assert line is not None

    # The one cell's centroid is origin + spacing/2 = (-2.9, 7.95).
    np.testing.assert_allclose(
        line.geometry.positions.data[:, :2],
        np.array([(-2.9, 7.95), (-2.9 + 2.0, 7.95 - 2.0)], dtype=np.float32),
        atol=1e-5,
    )
