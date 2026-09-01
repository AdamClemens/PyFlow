"""Unit tests for `src/pyflow/rendering/field_visualization.py` (TASK-017).

Pure colour-math and geometry-construction checks -- no actual GPU
render here, matching `test_mesh_visualization.py`'s own split: this
file checks the arrays/objects these functions build, and
`tests/golden/test_field_display.py` checks what they look like once
actually rendered (the real sRGB round-trip lives there, since it's a
property of the render pipeline, not of these functions' own output).
"""

from __future__ import annotations

import math

import numpy as np
import pygfx as gfx
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
    # 2 cells, 6 points each: the shaft (2 points, first) plus two
    # arrowhead segments (4 points) appended after -- shaft points come
    # first and in cell order, so the existing shaft-only assertion below
    # still holds against a slice, not the whole array.
    assert positions.shape == (12, 2)

    c0 = mesh.cell_centroid(0)
    c1 = mesh.cell_centroid(1)
    expected_shafts = np.array(
        [
            c0,
            (c0[0] + 0.5 * 1.0, c0[1] + 0.5 * 0.0),
            c1,
            (c1[0] + 0.5 * 0.0, c1[1] + 0.5 * 2.0),
        ],
        dtype=np.float32,
    )
    np.testing.assert_allclose(positions[:4], expected_shafts, atol=1e-5)


def test_build_vector_field_arrows_skips_zero_vectors() -> None:
    mesh = _mesh(nx=3, ny=1)
    field = VectorField(mesh, "v", num_components=2)
    field.set_value_at(0, (1.0, 0.0))
    field.set_value_at(1, (0.0, 0.0))  # zero -- must not produce a segment
    field.set_value_at(2, (0.0, -1.0))

    line = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    assert line is not None
    # Two non-zero cells -> two shafts (4 points) + two arrowheads each
    # (2 segments = 4 points per arrow) -> 2 * (2 + 4) = 12, not 8 (a zero
    # vector must still contribute nothing at all, shaft or head).
    assert line.geometry.positions.data.shape[0] == 12


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

    # The one cell's centroid is origin + spacing/2 = (-2.9, 7.95). Only
    # the shaft (first 2 points) is checked here -- the arrowhead's own
    # geometry is `test_build_vector_field_arrows_head_*` below.
    np.testing.assert_allclose(
        line.geometry.positions.data[:2, :2],
        np.array([(-2.9, 7.95), (-2.9 + 2.0, 7.95 - 2.0)], dtype=np.float32),
        atol=1e-5,
    )


# -- build_vector_field_arrows: arrowhead geometry --------------------------


def test_build_vector_field_arrows_head_segments_start_at_the_tip() -> None:
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 0.0))
    line = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    assert line is not None

    positions = line.geometry.positions.data[:, :2]
    tip = positions[1]
    # Two head segments after the one shaft segment: (tip, head1), (tip, head2).
    assert positions.shape == (6, 2)
    np.testing.assert_allclose(positions[2], tip, atol=1e-5)
    np.testing.assert_allclose(positions[4], tip, atol=1e-5)


def test_build_vector_field_arrows_head_points_are_not_the_tip_itself() -> None:
    # A degenerate (zero-length) arrowhead would defeat the whole point --
    # both head endpoints must actually be displaced from the tip.
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 0.0))
    line = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    assert line is not None

    positions = line.geometry.positions.data[:, :2]
    tip = positions[1]
    assert not np.allclose(positions[3], tip, atol=1e-6)
    assert not np.allclose(positions[5], tip, atol=1e-6)


def _head_length(line: gfx.Line) -> float:
    positions = line.geometry.positions.data[:, :2]
    tip, head = positions[1], positions[3]
    return float(np.hypot(*(head - tip)))


def test_build_vector_field_arrows_head_length_scales_with_shaft_length() -> None:
    # A longer shaft (bigger scale, same direction) must get a
    # proportionally longer arrowhead -- honest about magnitude, not a
    # fixed decoration that would overstate a tiny vector or vanish
    # against a large one. Both scales are chosen well above the
    # minimum-length floor (see the test below) so this checks the
    # proportional regime in isolation.
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 0.0))

    short = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    long_ = build_vector_field_arrows(field, color="#ffffff", scale=10.0)
    assert short is not None
    assert long_ is not None

    # 10x the shaft length -> 10x the head length (same fixed fraction).
    assert _head_length(long_) == pytest.approx(_head_length(short) * 10, rel=1e-4)


def test_build_vector_field_arrows_head_has_a_minimum_length_for_tiny_vectors() -> None:
    # A genuinely tiny vector's shaft can shrink until a purely
    # proportional head is imperceptible -- direction becomes unreadable
    # even though the (very short) shaft is still technically there. The
    # head must instead floor out at a fraction of the cell's own
    # characteristic size, not keep shrinking with the shaft.
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 0.0))

    line = build_vector_field_arrows(field, color="#ffffff", scale=1e-6)
    assert line is not None

    cell_size = math.sqrt(mesh.cell_volume(0))
    # Far above what the proportional-only rule would give (~3e-7): tied
    # to the cell's own size instead, per the source's own documented
    # minimum fraction.
    assert _head_length(line) == pytest.approx(cell_size * 0.3, rel=1e-4)


def test_build_vector_field_arrows_head_floor_does_not_affect_large_shafts() -> None:
    # The floor must only rescue small vectors, not perturb the
    # already-correct proportional behaviour for ordinary ones.
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 0.0))

    line = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    assert line is not None
    assert _head_length(line) == pytest.approx(1.0 * 0.3, rel=1e-4)


def test_build_vector_field_arrows_head_segments_are_symmetric_about_the_shaft() -> None:
    mesh = _mesh(nx=1, ny=1)
    field = VectorField(mesh, "v", num_components=2, initial_value=(1.0, 0.0))
    line = build_vector_field_arrows(field, color="#ffffff", scale=1.0)
    assert line is not None

    positions = line.geometry.positions.data[:, :2]
    tail, tip, head1, head2 = positions[0], positions[1], positions[3], positions[5]
    shaft_dir = (tip - tail) / np.linalg.norm(tip - tail)

    def angle_from_reversed_shaft(head: np.ndarray) -> float:
        head_dir = (head - tip) / np.linalg.norm(head - tip)
        cos_angle = np.clip(np.dot(head_dir, -shaft_dir), -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angle)))

    angle1 = angle_from_reversed_shaft(head1)
    angle2 = angle_from_reversed_shaft(head2)
    assert angle1 == pytest.approx(angle2, abs=0.5)
    # A real, visually distinct chevron, not a near-zero sliver -- picked
    # a generous band (10-45 degrees) rather than the exact constant so
    # this doesn't pin an implementation detail.
    assert 10.0 < angle1 < 45.0
    # And the two head points must be on opposite sides of the shaft, not
    # both drifted the same way (which would look like a hook, not a head).
    perp = np.array([-shaft_dir[1], shaft_dir[0]])
    assert np.dot(head1 - tip, perp) * np.dot(head2 - tip, perp) < 0
