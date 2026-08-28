"""Implementation-specific tests for `StructuredCartesianMesh`
(TASK-012). In addition to the shared contract suite
(`test_mesh_contract.py`), which every `Mesh` must pass, this
implementation makes its own specific claims -- exact formulas, uniform
spacing, index-arithmetic neighbours, and its own error condition --
that the contract suite deliberately does not (and must not) assert,
since a future unstructured implementation wouldn't satisfy them.
"""

from __future__ import annotations

import itertools
import math

import pytest

from pyflow.configuration.schema import MeshConfig
from pyflow.engine.coordinate_system import UniformVertexCoordinateSystem
from pyflow.engine.mesh import (
    InvalidMeshEntityError,
    NotABoundaryFaceError,
    StructuredCartesianMesh,
)

_ORIGIN = (1.5, -2.25)
_SPACING = (0.1, 0.3)
_EXTENT = (4, 3)


def _mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=_ORIGIN, spacing=_SPACING, extent=_EXTENT)


def test_cell_volume_equals_dx_times_dy_exactly() -> None:
    mesh = _mesh()
    dx, dy = _SPACING
    for cell in range(mesh.num_cells):
        assert mesh.cell_volume(cell) == dx * dy


def test_cell_centroid_is_the_average_of_its_four_corner_vertices() -> None:
    mesh = _mesh()
    coordinate_system = UniformVertexCoordinateSystem(origin=_ORIGIN, spacing=_SPACING)
    nx, ny = _EXTENT

    for i, j in itertools.product(range(nx), range(ny)):
        corners = [
            coordinate_system.to_physical(i, j),
            coordinate_system.to_physical(i + 1, j),
            coordinate_system.to_physical(i + 1, j + 1),
            coordinate_system.to_physical(i, j + 1),
        ]
        expected = (
            sum(x for x, _ in corners) / 4,
            sum(y for _, y in corners) / 4,
        )
        assert mesh.cell_centroid(mesh.cell_id(i, j)) == expected


def test_face_areas_match_spacing_by_orientation() -> None:
    mesh = _mesh()
    dx, dy = _SPACING

    for face in range(mesh.num_faces):
        normal_x, _ = mesh.face_normal(face)
        expected_area = dy if abs(normal_x) == 1.0 else dx
        assert mesh.face_area(face) == expected_area


def test_face_vertices_match_the_coordinate_system_exactly() -> None:
    mesh = _mesh()
    coordinate_system = UniformVertexCoordinateSystem(origin=_ORIGIN, spacing=_SPACING)
    nx, ny = _EXTENT

    for i, j in itertools.product(range(nx), range(ny)):
        cell = mesh.cell_id(i, j)
        west, east, south, north = mesh.cell_faces(cell)

        assert mesh.face_vertices(west) == (
            coordinate_system.to_physical(i, j),
            coordinate_system.to_physical(i, j + 1),
        )
        assert mesh.face_vertices(east) == (
            coordinate_system.to_physical(i + 1, j),
            coordinate_system.to_physical(i + 1, j + 1),
        )
        assert mesh.face_vertices(south) == (
            coordinate_system.to_physical(i, j),
            coordinate_system.to_physical(i + 1, j),
        )
        assert mesh.face_vertices(north) == (
            coordinate_system.to_physical(i, j + 1),
            coordinate_system.to_physical(i + 1, j + 1),
        )


def test_cell_id_and_cell_index_round_trip() -> None:
    mesh = _mesh()
    nx, ny = _EXTENT

    for i, j in itertools.product(range(nx), range(ny)):
        assert mesh.cell_index(mesh.cell_id(i, j)) == (i, j)


def test_neighbours_of_an_interior_cell_are_exactly_index_arithmetic() -> None:
    mesh = _mesh()
    nx, ny = _EXTENT

    for i, j in itertools.product(range(1, nx - 1), range(1, ny - 1)):
        cell = mesh.cell_id(i, j)

        neighbours = set()
        for face in mesh.cell_faces(cell):
            owner, neighbour = mesh.face_neighbours(face)
            other = neighbour if owner == cell else owner
            assert other is not None  # interior cell: no boundary faces
            neighbours.add(other)

        expected = {
            mesh.cell_id(i - 1, j),
            mesh.cell_id(i + 1, j),
            mesh.cell_id(i, j - 1),
            mesh.cell_id(i, j + 1),
        }
        assert neighbours == expected


def test_boundary_faces_are_exactly_the_domain_edge_cells() -> None:
    mesh = _mesh()
    nx, ny = _EXTENT

    expected_boundary_cells = {
        mesh.cell_id(i, j)
        for i, j in itertools.product(range(nx), range(ny))
        if i in (0, nx - 1) or j in (0, ny - 1)
    }

    actual_boundary_cells = set()
    for face in range(mesh.num_faces):
        if mesh.is_boundary_face(face):
            owner, _ = mesh.face_neighbours(face)
            actual_boundary_cells.add(owner)

    assert actual_boundary_cells == expected_boundary_cells


@pytest.mark.parametrize(("nx", "ny"), [(0, 5), (5, 0), (-1, 5), (5, -1)])
def test_non_positive_extent_raises(nx: int, ny: int) -> None:
    with pytest.raises(ValueError, match="extent must be positive"):
        StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(nx, ny))


def test_from_config_builds_a_matching_mesh() -> None:
    config = MeshConfig(origin=_ORIGIN, spacing=_SPACING, extent=_EXTENT)
    mesh = StructuredCartesianMesh.from_config(config)

    assert mesh.num_cells == _EXTENT[0] * _EXTENT[1]
    assert mesh.cell_volume(0) == _SPACING[0] * _SPACING[1]


@pytest.mark.parametrize(("i", "j"), [(-1, 0), (0, -1), (_EXTENT[0], 0), (0, _EXTENT[1])])
def test_cell_id_rejects_an_out_of_range_structured_index(i: int, j: int) -> None:
    """`cell_id` validates `(i, j)`, not the flat id it produces.

    `(nx, 0)` flattens to the same integer as `(0, 1)`, so a range check
    applied after flattening would silently accept a column overrun as a
    valid cell in the next row -- and it would do so precisely at the
    domain edge, where boundary handling lives and where an off-by-one
    is most likely. Added 2026-08-21 alongside the flat-id validation
    the `Mesh` contract suite now requires.
    """
    mesh = _mesh()
    with pytest.raises(InvalidMeshEntityError):
        mesh.cell_id(i, j)


def test_cell_index_rejects_an_out_of_range_flat_id() -> None:
    mesh = _mesh()
    with pytest.raises(InvalidMeshEntityError):
        mesh.cell_index(mesh.num_cells)


def test_boundary_face_name_matches_the_domain_edge_a_face_lies_on() -> None:
    # TASK-023: a concrete Advection scheme needs to map a boundary face
    # to which of the four named edges (`NumericsConfig.boundary_conditions`)
    # it belongs to, in order to pick the right `BoundaryCondition` --
    # additive here, off the abstract `Mesh` interface, the same pattern
    # TASK-030's own periodic wrapped-neighbour lookup uses (`docs/
    # planning/roadmap.md` TASK-023's Design decision).
    mesh = _mesh()
    nx, ny = _EXTENT

    for i, j in itertools.product(range(nx), range(ny)):
        cell = mesh.cell_id(i, j)
        west, east, south, north = mesh.cell_faces(cell)

        assert mesh.boundary_face_name(west) == ("west" if i == 0 else None)
        assert mesh.boundary_face_name(east) == ("east" if i == nx - 1 else None)
        assert mesh.boundary_face_name(south) == ("south" if j == 0 else None)
        assert mesh.boundary_face_name(north) == ("north" if j == ny - 1 else None)


def test_boundary_face_name_rejects_an_out_of_range_face() -> None:
    mesh = _mesh()
    with pytest.raises(InvalidMeshEntityError):
        mesh.boundary_face_name(mesh.num_faces)


def test_interior_face_centroid_distance_equals_the_grid_spacing() -> None:
    # TASK-024: on a uniform mesh, two neighbouring cells' centroids are
    # exactly one grid spacing apart along the axis their shared face is
    # normal to -- `dx` for a vertical (east/west-facing) face, `dy` for a
    # horizontal one. Computed generically (via `cell_centroid`
    # subtraction, not `self._dx`/`self._dy` directly), so `math.isclose`
    # rather than `==`: unlike `cell_volume`, this isn't a bit-exact
    # single multiplication.
    mesh = _mesh()
    dx, dy = _SPACING

    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        if neighbour is None:
            continue
        normal_x, _ = mesh.face_normal(face)
        expected = dx if abs(normal_x) == 1.0 else dy
        assert math.isclose(mesh.face_centroid_distance(face), expected)


def test_wrapped_neighbour_cell_pairs_each_boundary_face_with_the_opposite_edge_cell() -> None:
    # TASK-030: the west/east boundary faces of the same row wrap to each
    # other's owner cell, and likewise north/south of the same column --
    # a periodic domain's own "the same relative position on the opposite
    # edge" reading, checked directly rather than assumed.
    mesh = _mesh()
    nx, ny = _EXTENT

    for i, j in itertools.product(range(nx), range(ny)):
        cell = mesh.cell_id(i, j)
        west, east, south, north = mesh.cell_faces(cell)

        if i == 0:
            assert mesh.wrapped_neighbour_cell(west) == mesh.cell_id(nx - 1, j)
        if i == nx - 1:
            assert mesh.wrapped_neighbour_cell(east) == mesh.cell_id(0, j)
        if j == 0:
            assert mesh.wrapped_neighbour_cell(south) == mesh.cell_id(i, ny - 1)
        if j == ny - 1:
            assert mesh.wrapped_neighbour_cell(north) == mesh.cell_id(i, 0)


def test_wrapped_neighbour_cell_rejects_an_interior_vertical_face() -> None:
    mesh = _mesh()
    nx, ny = _EXTENT
    interior_cell = mesh.cell_id(nx // 2, ny // 2)
    west, east, _south, _north = mesh.cell_faces(interior_cell)
    interior_vertical_face = next(f for f in (west, east) if not mesh.is_boundary_face(f))

    with pytest.raises(NotABoundaryFaceError):
        mesh.wrapped_neighbour_cell(interior_vertical_face)


def test_wrapped_neighbour_cell_rejects_an_interior_horizontal_face() -> None:
    mesh = _mesh()
    nx, ny = _EXTENT
    interior_cell = mesh.cell_id(nx // 2, ny // 2)
    _west, _east, south, north = mesh.cell_faces(interior_cell)
    interior_horizontal_face = next(f for f in (south, north) if not mesh.is_boundary_face(f))

    with pytest.raises(NotABoundaryFaceError):
        mesh.wrapped_neighbour_cell(interior_horizontal_face)


def test_wrapped_neighbour_cell_rejects_an_out_of_range_face() -> None:
    mesh = _mesh()
    with pytest.raises(InvalidMeshEntityError):
        mesh.wrapped_neighbour_cell(mesh.num_faces)


def test_boundary_face_centroid_distance_is_half_the_grid_spacing() -> None:
    # A boundary face sits exactly midway between where its owner's
    # centroid is and where a (non-existent) neighbour's would be, so
    # the owner-to-face distance is exactly half the interior spacing.
    mesh = _mesh()
    dx, dy = _SPACING

    for face in range(mesh.num_faces):
        if not mesh.is_boundary_face(face):
            continue
        normal_x, _ = mesh.face_normal(face)
        expected = (dx if abs(normal_x) == 1.0 else dy) / 2
        assert math.isclose(mesh.face_centroid_distance(face), expected)
