"""Implementation-specific tests for `VectorField` (TASK-016). In
addition to the two shared contract suites -- `test_field_contract.py`
(`Field`) and `test_collocated_field_contract.py` (`CollocatedField`),
both of which `VectorField` joins by extending a parametrisation, not by
writing new contract tests here -- `VectorField` makes its own specific
claims --
ergonomic `tuple` access, per-component addressing, magnitude, and its
own error conditions -- that the contract suite deliberately does not
(and must not) assert, since a differently-shaped implementation
wouldn't satisfy them.
"""

from __future__ import annotations

import pytest

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.vector_field import VectorField


def _mesh(nx: int = 3, ny: int = 2) -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def test_component_shape_matches_num_components() -> None:
    field = VectorField(_mesh(), "velocity", num_components=3)
    assert field.component_shape == (3,)


def test_default_num_components_is_two() -> None:
    field = VectorField(_mesh(), "velocity")
    assert field.component_shape == (2,)


@pytest.mark.parametrize("num_components", [0, -1, -5])
def test_non_positive_num_components_raises(num_components: int) -> None:
    with pytest.raises(ValueError, match="num_components must be positive"):
        VectorField(_mesh(), "velocity", num_components=num_components)


def test_value_at_returns_a_tuple_of_floats_not_a_tensor() -> None:
    field = VectorField(_mesh(), "velocity", initial_value=(1.0, 2.0))
    value = field.value_at(0)
    assert value == (1.0, 2.0)
    assert isinstance(value, tuple)
    assert all(isinstance(component, float) for component in value)


def test_set_value_at_rejects_a_mismatched_length() -> None:
    field = VectorField(_mesh(), "velocity", num_components=2)
    with pytest.raises(ValueError, match="length"):
        field.set_value_at(0, (1.0, 2.0, 3.0))
    with pytest.raises(ValueError, match="length"):
        field.set_value_at(0, (1.0,))


def test_callable_initial_value_matches_the_formula_per_component() -> None:
    # `lambda x, y: (x, -y)` makes the two components genuinely
    # independent of each other -- a bug that swaps components, or
    # duplicates one into both, fails visibly, unlike a function that
    # happened to return the same thing in every slot.
    mesh = _mesh()
    field = VectorField(mesh, "velocity", initial_value=lambda x, y: (x, -y))

    for cell in range(mesh.num_cells):
        x, y = mesh.cell_centroid(cell)
        assert field.value_at(cell) == (x, -y)


def test_component_returns_the_matching_column_not_transposed_or_duplicated() -> None:
    # Every (cell, component) entry is distinct, so returning the wrong
    # row, the wrong column, or a duplicated slot all produce a visibly
    # wrong answer rather than accidentally matching.
    mesh = _mesh(nx=2, ny=1)
    field = VectorField(mesh, "velocity", num_components=2)
    field.set_value_at(0, (1.0, 2.0))
    field.set_value_at(1, (3.0, 4.0))

    assert field.component(0).tolist() == [1.0, 3.0]
    assert field.component(1).tolist() == [2.0, 4.0]


def test_component_shape_is_one_dimensional_per_cell() -> None:
    mesh = _mesh(nx=2, ny=1)
    field = VectorField(mesh, "velocity", num_components=2)
    assert field.component(0).shape == (mesh.num_cells,)


@pytest.mark.parametrize("bad_index", [-1, 2, 5])
def test_component_rejects_an_out_of_range_index(bad_index: int) -> None:
    field = VectorField(_mesh(), "velocity", num_components=2)
    with pytest.raises(IndexError):
        field.component(bad_index)


def test_magnitude_is_the_euclidean_norm_not_the_sum_or_a_single_component() -> None:
    # Two Pythagorean triples, one per cell: 3-4-5 (sum would give 7,
    # either component alone 3 or 4) and 5-12-13 with a negative
    # component (sum would give 7 or 17 depending on whether the sign is
    # handled, either component alone 5 or 12). Every plausible wrong
    # implementation is distinguishable at both cells, and **no cell's
    # norm is trivially 0 or 1** -- TASK-016's acceptance criterion says
    # so in as many words, and this test set one of its two cells to
    # `(0.0, 0.0)` until the 2026-08-22 retro-audit read the criterion
    # against the test (`docs/practices.md`, "The intent lives in the
    # qualifier"). A zero vector is covered where it actually matters,
    # in `test_field_visualization.py`'s arrow tests, which is the only
    # place its behaviour differs.
    mesh = _mesh(nx=2, ny=1)
    field = VectorField(mesh, "velocity", num_components=2)
    field.set_value_at(0, (3.0, 4.0))
    field.set_value_at(1, (-5.0, 12.0))

    magnitude = field.magnitude()
    assert magnitude.shape == (mesh.num_cells,)
    assert magnitude[0].item() == pytest.approx(5.0)
    assert magnitude[1].item() == pytest.approx(13.0)


def test_copy_preserves_num_components_not_just_mesh_and_name() -> None:
    field = VectorField(_mesh(), "velocity", num_components=3, initial_value=(1.0, 2.0, 3.0))
    copied = field.copy()

    assert copied.component_shape == (3,)
    with pytest.raises(ValueError, match="length"):
        copied.set_value_at(0, (1.0, 2.0))


def test_copy_independence_for_vector_storage_specifically() -> None:
    field = VectorField(_mesh(), "velocity", initial_value=(1.0, 1.0))
    copied = field.copy()

    copied.set_value_at(0, (99.0, 99.0))
    assert field.value_at(0) == (1.0, 1.0)
    assert copied.value_at(0) == (99.0, 99.0)
