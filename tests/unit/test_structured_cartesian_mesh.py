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

import pytest

from pyflow.configuration.schema import MeshConfig
from pyflow.engine.coordinate_system import UniformVertexCoordinateSystem
from pyflow.engine.mesh import StructuredCartesianMesh

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
