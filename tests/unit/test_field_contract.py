"""Contract test suite for `CollocatedField` (TASK-014/015).

Written once `ScalarField` exists to run it against -- `Field` itself
(TASK-014) carries no storage, so a contract suite with zero concrete
implementations would prove nothing. Run against every concrete
`CollocatedField` implementation that exists now or is added later, per
`docs/planning/roadmap.md` TASK-015's Acceptance Criteria. TASK-016
joins `VectorField` by adding it to `_IMPLEMENTATIONS` below, not by
writing new tests here.
"""

from __future__ import annotations

from typing import Any

import pytest
import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.mesh import InvalidMeshEntityError, Mesh, StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField

_IMPLEMENTATIONS: list[type[CollocatedField[Any]]] = [ScalarField]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    # Deliberately non-"nice" origin/spacing and a non-square extent --
    # same reasoning as the Mesh/CoordinateSystem contract suites: proves
    # the contract holds for real floats and asymmetric meshes, not just
    # convenient numbers.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


@pytest.fixture(params=_IMPLEMENTATIONS, ids=lambda cls: cls.__name__)
def field_class(request: pytest.FixtureRequest) -> type[CollocatedField[Any]]:
    result: type[CollocatedField[Any]] = request.param
    return result


def test_storage_shape_matches_mesh_cell_count_and_component_shape(
    field_class: type[CollocatedField[Any]],
) -> None:
    # Checked against two differently-sized meshes so a hardcoded
    # constant in the implementation cannot pass by coincidence
    # (docs/practices.md's distinct-factors rule).
    for nx, ny in [(2, 3), (5, 4)]:
        mesh = _mesh(nx, ny)
        field = field_class(mesh, "field_under_test")
        assert field.values.shape == (mesh.num_cells, *field.component_shape)


def test_default_initial_value_is_zero(field_class: type[CollocatedField[Any]]) -> None:
    field = field_class(_mesh(), "field_under_test")
    assert torch.equal(field.values, torch.zeros_like(field.values))


def test_constant_initial_value_applies_to_every_cell(
    field_class: type[CollocatedField[Any]],
) -> None:
    field = field_class(_mesh(), "field_under_test", initial_value=3.5)
    expected = torch.full(field.values.shape, 3.5, dtype=torch.float64)
    assert torch.equal(field.values, expected)


def test_callable_initial_value_evaluated_once_per_cell_at_its_centroid(
    field_class: type[CollocatedField[Any]],
) -> None:
    # A scalar-returning, genuinely non-constant function -- reads both
    # axes with different coefficients, so a formula that only reads one
    # axis, or a bug that ignores the callable entirely, fails visibly.
    # Broadcasts into whatever `component_shape` is, so this stays
    # implementation-independent; per-component distinctness for a
    # multi-component field is that implementation's own specific test.
    def initializer(x: float, y: float) -> float:
        return x + 10.0 * y

    mesh = _mesh()
    field = field_class(mesh, "field_under_test", initial_value=initializer)

    for cell in range(mesh.num_cells):
        x, y = mesh.cell_centroid(cell)
        expected = torch.full(field.component_shape, initializer(x, y), dtype=torch.float64)
        assert torch.equal(torch.as_tensor(field.value_at(cell), dtype=torch.float64), expected)


def test_value_at_set_value_at_round_trip_every_cell(
    field_class: type[CollocatedField[Any]],
) -> None:
    mesh = _mesh()
    field = field_class(mesh, "field_under_test")

    for cell in range(mesh.num_cells):
        new_value = torch.full(field.component_shape, float(cell) + 0.5, dtype=torch.float64)
        field.set_value_at(cell, new_value)
        assert torch.equal(torch.as_tensor(field.value_at(cell), dtype=torch.float64), new_value)


def test_value_at_rejects_an_out_of_range_cell(
    field_class: type[CollocatedField[Any]],
) -> None:
    mesh = _mesh()
    field = field_class(mesh, "field_under_test")
    for bad_cell in (-1, mesh.num_cells, mesh.num_cells + 1):
        with pytest.raises(InvalidMeshEntityError):
            field.value_at(bad_cell)


def test_set_value_at_rejects_an_out_of_range_cell(
    field_class: type[CollocatedField[Any]],
) -> None:
    mesh = _mesh()
    field = field_class(mesh, "field_under_test")
    filler = torch.zeros(field.component_shape, dtype=torch.float64)
    for bad_cell in (-1, mesh.num_cells, mesh.num_cells + 1):
        with pytest.raises(InvalidMeshEntityError):
            field.set_value_at(bad_cell, filler)


def test_copy_is_independent_of_the_original(
    field_class: type[CollocatedField[Any]],
) -> None:
    mesh = _mesh()
    field = field_class(mesh, "field_under_test", initial_value=1.0)
    copied = field.copy()

    high = torch.full(field.component_shape, 99.0, dtype=torch.float64)
    low = torch.full(field.component_shape, -5.0, dtype=torch.float64)

    copied.set_value_at(0, high)
    assert not torch.equal(field.values[0], copied.values[0])

    field.set_value_at(1, low)
    assert not torch.equal(field.values[1], copied.values[1])
