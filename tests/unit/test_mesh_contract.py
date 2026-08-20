"""Contract test suite for `Mesh` (TASK-012).

Written once, run against every `Mesh` implementation that exists now or
is added later -- asserts only what must hold regardless of whether the
mesh is structured or unstructured, per `docs/planning/roadmap.md`
TASK-012's Acceptance Criteria. A future implementation joins this suite
by adding a factory to `_IMPLEMENTATIONS` below, not by writing new
tests here.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import pytest

from pyflow.engine.mesh import Mesh, StructuredCartesianMesh


def _structured_3x2() -> Mesh:
    # Deliberately non-"nice" origin/spacing and a non-square extent --
    # proves the contract holds for real floats and asymmetric meshes,
    # not just convenient numbers.
    return StructuredCartesianMesh(origin=(1.5, -2.25), spacing=(0.1, 0.3), extent=(3, 2))


_IMPLEMENTATIONS: list[Callable[[], Mesh]] = [_structured_3x2]


@pytest.fixture(params=_IMPLEMENTATIONS, ids=lambda factory: factory.__name__.lstrip("_"))
def mesh(request: pytest.FixtureRequest) -> Mesh:
    factory: Callable[[], Mesh] = request.param
    return factory()


def test_every_cell_has_a_well_defined_volume(mesh: Mesh) -> None:
    for cell in range(mesh.num_cells):
        assert mesh.cell_volume(cell) > 0


def test_every_cell_has_a_well_defined_centroid(mesh: Mesh) -> None:
    for cell in range(mesh.num_cells):
        x, y = mesh.cell_centroid(cell)
        assert math.isfinite(x)
        assert math.isfinite(y)


def test_every_face_has_a_well_defined_area(mesh: Mesh) -> None:
    for face in range(mesh.num_faces):
        assert mesh.face_area(face) > 0


def test_every_face_has_a_well_defined_normal(mesh: Mesh) -> None:
    for face in range(mesh.num_faces):
        nx, ny = mesh.face_normal(face)
        assert math.isfinite(nx)
        assert math.isfinite(ny)


def test_boundary_identification_is_exhaustive_and_exclusive(mesh: Mesh) -> None:
    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        assert 0 <= owner < mesh.num_cells

        if neighbour is None:
            assert mesh.is_boundary_face(face)
        else:
            assert 0 <= neighbour < mesh.num_cells
            assert neighbour != owner
            assert not mesh.is_boundary_face(face)


def test_neighbour_connectivity_is_symmetric(mesh: Mesh) -> None:
    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        assert face in mesh.cell_faces(owner)
        if neighbour is not None:
            assert face in mesh.cell_faces(neighbour)


def test_face_normal_from_rejects_a_non_adjacent_cell(mesh: Mesh) -> None:
    # Cell 0 is guaranteed to exist (every implementation has at least
    # one cell); face `num_faces - 1` is its own last face, guaranteed
    # not to be adjacent to *every* cell in a mesh with more than one
    # cell -- pick the cell furthest from it in id-space as a
    # deliberately-not-adjacent pair.
    face = mesh.num_faces - 1
    owner, neighbour = mesh.face_neighbours(face)
    non_adjacent_cell = next(
        cell for cell in range(mesh.num_cells) if cell not in (owner, neighbour)
    )

    with pytest.raises(ValueError, match="is not adjacent to face"):
        mesh.face_normal_from(face, non_adjacent_cell)


def test_geometric_closure(mesh: Mesh) -> None:
    """Discrete Gauss/divergence theorem: for every cell, the sum of
    `face_area * outward_normal` over its faces is the zero vector.

    Every later flux-conservation check (Stage 4+) silently depends on
    this holding -- a broken mesh here is cheaper to catch now than to
    misdiagnose as a flux-scheme bug two stages later.
    """
    for cell in range(mesh.num_cells):
        total_x = 0.0
        total_y = 0.0
        for face in mesh.cell_faces(cell):
            area = mesh.face_area(face)
            normal_x, normal_y = mesh.face_normal_from(face, cell)
            total_x += area * normal_x
            total_y += area * normal_y

        assert math.isclose(total_x, 0.0, abs_tol=1e-9)
        assert math.isclose(total_y, 0.0, abs_tol=1e-9)
