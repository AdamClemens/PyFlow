"""Contract test suite for `Field` itself -- the mesh-association, name
and independent-copy promise every physical quantity shares, whatever
arrangement it uses to store its values.

Deliberately asserts *only* what `Field` (`src/pyflow/engine/field.py`,
TASK-014) declares, and nothing a particular arrangement adds: no
`values`, no `component_shape`, no cell-indexed access. That restraint
is the point. `Field` carries no storage precisely so that a staggered
placement (`docs/implementation/upgrade-paths.md` "Variables") can
satisfy it unchanged, and a contract suite that reached for cell-centred
storage would quietly re-impose the assumption the interface was split
to avoid -- which is exactly what `test_collocated_field_contract.py`
does, correctly, one layer down.

A future implementation joins by adding a factory to `_FACTORIES`, not
by writing new contract tests. A collocated implementation must pass
*both* this suite and `test_collocated_field_contract.py`; a
non-collocated one passes this suite alone.

Added 2026-08-22 by the Stage 2 exit audit (`docs/planning/roadmap.md`,
"Status as of 2026-08-22"), which found that Stage 2 Completion
Criterion 2 promised a suite "any future implementation (e.g. a
staggered placement) must pass unchanged" and that no such suite
existed: the only one was parametrised over `CollocatedField` subclasses
and asserted `values.shape == (num_cells, *component_shape)`.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

# A factory, not a class, so an implementation whose constructor needs
# more than `(mesh, name)` -- a staggered field naming its placement, say
# -- joins this list without changing any test below.
_FACTORIES: list[tuple[str, Callable[[Mesh, str], Field]]] = [
    ("ScalarField", lambda mesh, name: ScalarField(mesh, name)),
    ("VectorField", lambda mesh, name: VectorField(mesh, name, num_components=2)),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    # Non-"nice" origin and spacing, and a non-square extent, for the
    # same reason the Mesh/CoordinateSystem contract suites use them:
    # a contract that only holds for convenient numbers is not a
    # contract.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_field(request: pytest.FixtureRequest) -> Callable[[Mesh, str], Field]:
    result: Callable[[Mesh, str], Field] = request.param[1]
    return result


def test_is_a_field(make_field: Callable[[Mesh, str], Field]) -> None:
    assert isinstance(make_field(_mesh(), "field_under_test"), Field)


def test_mesh_is_the_one_passed_at_construction(
    make_field: Callable[[Mesh, str], Field],
) -> None:
    # Identity, not equality: the criterion is that a field *carries*
    # its mesh, so nothing downstream needs a second reference to it
    # passed alongside (Stage 2 Completion Criterion 1).
    mesh = _mesh()
    assert make_field(mesh, "field_under_test").mesh is mesh


def test_name_is_the_one_passed_at_construction(
    make_field: Callable[[Mesh, str], Field],
) -> None:
    assert make_field(_mesh(), "field_under_test").name == "field_under_test"


def test_distinct_fields_do_not_share_mesh_or_name(
    make_field: Callable[[Mesh, str], Field],
) -> None:
    # Guards the class of bug where `mesh`/`name` end up on the class
    # rather than the instance, which every field constructed after the
    # first would then inherit.
    first_mesh, second_mesh = _mesh(2, 2), _mesh(4, 3)
    first = make_field(first_mesh, "first")
    second = make_field(second_mesh, "second")

    assert (first.mesh, first.name) == (first_mesh, "first")
    assert (second.mesh, second.name) == (second_mesh, "second")


def test_mesh_and_name_have_no_setters(make_field: Callable[[Mesh, str], Field]) -> None:
    field = make_field(_mesh(), "field_under_test")
    with pytest.raises(AttributeError):
        field.mesh = _mesh(5, 5)  # type: ignore[misc]
    with pytest.raises(AttributeError):
        field.name = "renamed"  # type: ignore[misc]


def test_empty_name_is_rejected(make_field: Callable[[Mesh, str], Field]) -> None:
    with pytest.raises(ValueError, match="name"):
        make_field(_mesh(), "")


def test_copy_is_a_distinct_object_of_the_same_type(
    make_field: Callable[[Mesh, str], Field],
) -> None:
    field = make_field(_mesh(), "field_under_test")
    copied = field.copy()

    assert copied is not field
    assert type(copied) is type(field)


def test_copy_preserves_mesh_and_name(make_field: Callable[[Mesh, str], Field]) -> None:
    mesh = _mesh()
    field = make_field(mesh, "field_under_test")
    copied = field.copy()

    assert copied.mesh is mesh
    assert copied.name == field.name
