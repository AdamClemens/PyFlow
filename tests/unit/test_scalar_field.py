"""Implementation-specific tests for `ScalarField` (TASK-015). In
addition to the two shared contract suites -- `test_field_contract.py`,
which every `Field` must pass, and
`test_collocated_field_contract.py`, which every `CollocatedField` must
pass on top of it -- `ScalarField` makes its own specific
claims -- ergonomic `float` access, and formula-level exactness -- that
the contract suite deliberately does not (and must not) assert, since a
future, differently-shaped implementation (e.g. `VectorField`) wouldn't
satisfy them.
"""

from __future__ import annotations

import torch

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField


def _mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(3, 2))


def test_component_shape_is_empty() -> None:
    field = ScalarField(_mesh(), "temperature")
    assert field.component_shape == ()


def test_value_at_returns_a_plain_float_not_a_tensor() -> None:
    field = ScalarField(_mesh(), "temperature", initial_value=2.0)
    value = field.value_at(0)
    assert isinstance(value, float)
    assert not isinstance(value, torch.Tensor)


def test_callable_initial_value_matches_the_formula_exactly() -> None:
    # `lambda x, y: x + 10 * y` reads both axes with different
    # coefficients, so a formula that only reads one axis, or swaps
    # `x`/`y`, fails visibly -- the same distinct-factors reasoning the
    # contract suite's own callable-initialiser test uses, re-verified
    # here for the concrete `float` this implementation actually stores.
    mesh = _mesh()
    field = ScalarField(mesh, "temperature", initial_value=lambda x, y: x + 10.0 * y)

    for cell in range(mesh.num_cells):
        x, y = mesh.cell_centroid(cell)
        assert field.value_at(cell) == x + 10.0 * y


def test_set_value_at_stores_exactly_the_given_float() -> None:
    field = ScalarField(_mesh(), "temperature")
    field.set_value_at(0, 42.5)
    assert field.value_at(0) == 42.5


def test_copy_independence_for_scalar_storage_specifically() -> None:
    # The contract suite already checks copy independence generically;
    # this re-checks it against `ScalarField`'s own storage, in case a
    # hypothetical override of `copy()` broke it in a way that only
    # shows up for this concrete type.
    field = ScalarField(_mesh(), "temperature", initial_value=1.0)
    copied = field.copy()

    copied.set_value_at(0, 123.0)
    assert field.value_at(0) == 1.0
    assert copied.value_at(0) == 123.0

    field.set_value_at(1, -7.0)
    assert copied.value_at(1) == 1.0
    assert field.value_at(1) == -7.0


def test_copy_preserves_mesh_and_name() -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "temperature", initial_value=1.0)
    copied = field.copy()

    assert copied is not field
    assert copied.mesh is mesh
    assert copied.name == "temperature"
