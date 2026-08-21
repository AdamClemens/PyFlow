"""Unit tests for Mesh grid-line visualisation and camera framing
(TASK-013).

Rendering-correctness tests use the offscreen backend and inspect real
pixels, the same technique
`tests/golden/test_empty_window.py::test_empty_window_renders_configured_background`
already established. One methodology note worth recording, found while
writing these tests (not obvious in advance): to detect *vertical* grid
line positions, scan a single screen row at a world-y strictly between
two horizontal grid lines -- scanning "any pixel differs in this column,
across every row" is contaminated by the horizontal lines, which cross
almost every column. Same the other way round for horizontal lines.
"""

from __future__ import annotations

import numpy as np
import pygfx as gfx
import pytest
from rendercanvas.offscreen import OffscreenRenderCanvas

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.rendering.mesh_visualization import (
    build_mesh_grid_line,
    fit_camera_to_bounds,
    fit_camera_to_mesh,
    mesh_bounding_box,
)

_BLACK = np.array([0, 0, 0, 255], dtype=np.uint8)


def _mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(4, 3))


def test_build_mesh_grid_line_has_one_segment_per_face() -> None:
    mesh = _mesh()
    line = build_mesh_grid_line(mesh, color="#ffffff")

    assert line.geometry.positions.data.shape == (mesh.num_faces * 2, 3)


def test_build_mesh_grid_line_segment_endpoints_match_face_vertices() -> None:
    mesh = _mesh()
    line = build_mesh_grid_line(mesh, color="#ffffff")
    positions = line.geometry.positions.data

    for face in range(mesh.num_faces):
        (x0, y0), (x1, y1) = mesh.face_vertices(face)
        assert tuple(positions[2 * face]) == (x0, y0, 0.0)
        assert tuple(positions[2 * face + 1]) == (x1, y1, 0.0)


def test_mesh_bounding_box_matches_the_domain_extent() -> None:
    mesh = _mesh()
    assert mesh_bounding_box(mesh) == (0.0, 0.0, 4.0, 3.0)


def test_fit_camera_to_mesh_centres_on_the_bounding_box() -> None:
    mesh = _mesh()
    camera = gfx.OrthographicCamera()

    fit_camera_to_mesh(camera, mesh)

    assert tuple(camera.local.position)[:2] == pytest.approx((2.0, 1.5))
    # A margin around the exact bounding box, so boundary grid lines
    # aren't clipped at the viewport edge -- verified as "wider than the
    # bare domain", not tied to one specific margin fraction.
    assert camera.width > 4.0
    assert camera.height > 3.0


def test_fit_camera_to_bounds_centres_on_an_arbitrary_box() -> None:
    # A box that is not any mesh's own bounding box, and not centred on
    # the origin either -- proves this takes the box it's given, not
    # secretly still deriving one from a mesh.
    camera = gfx.OrthographicCamera()

    fit_camera_to_bounds(camera, (10.0, -5.0, 14.0, -2.0))

    assert tuple(camera.local.position)[:2] == pytest.approx((12.0, -3.5))
    assert camera.width > 4.0
    assert camera.height > 3.0


def test_fit_camera_to_mesh_delegates_to_fit_camera_to_bounds() -> None:
    # Framing the mesh directly must agree exactly with framing its own
    # bounding box explicitly -- not just similarly, exactly, since
    # `fit_camera_to_mesh` is now defined in terms of the other.
    mesh = _mesh()
    camera_via_mesh = gfx.OrthographicCamera()
    camera_via_bounds = gfx.OrthographicCamera()

    fit_camera_to_mesh(camera_via_mesh, mesh)
    fit_camera_to_bounds(camera_via_bounds, mesh_bounding_box(mesh))

    assert tuple(camera_via_mesh.local.position) == tuple(camera_via_bounds.local.position)
    assert camera_via_mesh.width == camera_via_bounds.width
    assert camera_via_mesh.height == camera_via_bounds.height


def _screen_column(camera: gfx.OrthographicCamera, canvas_width: int, world_x: float) -> float:
    width = float(camera.width)  # pygfx ships no stubs; camera.width resolves as Any
    left = float(camera.local.position[0]) - width / 2
    return (world_x - left) / width * canvas_width


def _screen_row(camera: gfx.OrthographicCamera, canvas_height: int, world_y: float) -> float:
    height = float(camera.height)
    top = float(camera.local.position[1]) + height / 2
    return (top - world_y) / height * canvas_height


def _cluster_centers(indices: np.ndarray) -> list[float]:
    if len(indices) == 0:
        return []
    groups: list[list[int]] = [[int(indices[0])]]
    for value in indices[1:]:
        if value - groups[-1][-1] <= 1:
            groups[-1].append(int(value))
        else:
            groups.append([int(value)])
    return [sum(group) / len(group) for group in groups]


def _render(mesh: StructuredCartesianMesh, *, size: tuple[int, int] = (400, 300)) -> np.ndarray:
    canvas = OffscreenRenderCanvas(size=size)
    renderer = gfx.WgpuRenderer(canvas)
    scene = gfx.Scene()
    scene.add(gfx.Background(None, gfx.BackgroundMaterial("#000000")))
    scene.add(build_mesh_grid_line(mesh, color="#ffffff"))

    camera = gfx.OrthographicCamera()
    fit_camera_to_mesh(camera, mesh)

    canvas.request_draw(lambda: renderer.render(scene, camera))
    image: np.ndarray = canvas.draw()
    return image


def test_grid_lines_render_at_every_boundary_and_internal_position() -> None:
    mesh = _mesh()
    canvas_size = (400, 300)
    image = _render(mesh, size=canvas_size)

    camera = gfx.OrthographicCamera()
    fit_camera_to_mesh(camera, mesh)

    # A clean scanline strictly between two horizontal grid lines (world
    # y=0.5) avoids the horizontal lines' own pixels contaminating the
    # search for *vertical* line positions -- see module docstring.
    scan_row = round(_screen_row(camera, canvas_size[1], 0.5))
    nonbackground_cols = np.where(np.any(image[scan_row] != _BLACK, axis=1))[0]
    detected_x = _cluster_centers(nonbackground_cols)

    # Sorted, not zipped in world-index order: world x increases with
    # screen column (no flip), but world y increases *upward* while
    # screen rows increase *downward* -- comparing by sorted pixel
    # position sidesteps that flip rather than assuming either order.
    expected_x = sorted(_screen_column(camera, canvas_size[0], float(i)) for i in range(5))
    assert len(detected_x) == len(expected_x)
    for detected, expected in zip(detected_x, expected_x, strict=True):
        assert detected == pytest.approx(expected, abs=3)

    scan_col = round(_screen_column(camera, canvas_size[0], 0.5))
    nonbackground_rows = np.where(np.any(image[:, scan_col] != _BLACK, axis=1))[0]
    detected_y = _cluster_centers(nonbackground_rows)

    expected_y = sorted(_screen_row(camera, canvas_size[1], float(j)) for j in range(4))
    assert len(detected_y) == len(expected_y)
    for detected, expected in zip(detected_y, expected_y, strict=True):
        assert detected == pytest.approx(expected, abs=3)


def test_grid_lines_are_visually_distinguishable_from_the_background() -> None:
    mesh = _mesh()
    image = _render(mesh)

    camera = gfx.OrthographicCamera()
    fit_camera_to_mesh(camera, mesh)
    row = round(_screen_row(camera, image.shape[0], 0.5))
    col = round(_screen_column(camera, image.shape[1], 0.0))  # a vertical line's x position

    line_pixel = image[row, col].astype(np.int32)
    background_pixel = _BLACK.astype(np.int32)
    contrast = np.abs(line_pixel - background_pixel).sum()

    # A fixed minimum contrast, not "differs at all" -- so this can't
    # pass vacuously against a background that happens to almost match.
    assert contrast > 200


def test_mesh_bounding_box_is_exact_for_an_awkward_origin_and_spacing() -> None:
    """The bounding box is measured in `float64`, not the `float32` the
    renderer wants (2026-08-21). Camera framing shouldn't be quantised by
    the GPU's precision, and `0.1` is exactly the kind of spacing where
    the difference is visible -- `np.float32(1.5 + 3 * 0.1)` is not
    `1.5 + 3 * 0.1`.
    """
    mesh = StructuredCartesianMesh(origin=(1.5, -2.25), spacing=(0.1, 0.3), extent=(3, 2))

    min_x, min_y, max_x, max_y = mesh_bounding_box(mesh)

    assert (min_x, min_y) == (1.5, -2.25)
    assert (max_x, max_y) == (1.5 + 3 * 0.1, -2.25 + 2 * 0.3)
