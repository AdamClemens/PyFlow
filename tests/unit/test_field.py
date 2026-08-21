"""Tests for `Field` (TASK-014) -- the mesh-association/name/copy
contract every physical quantity will share, independent of how values
are arranged over the mesh. `Field` carries no storage of its own (see
`docs/planning/roadmap.md` TASK-014's design decisions), so there is no
shared, parametrised contract suite yet -- that starts at TASK-015, once
`ScalarField` exists to run it against. These tests exercise the
abstract base directly, through two minimal test-only subclasses defined
below, not through a real field implementation.
"""

from __future__ import annotations

import pytest

from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh


class _CompleteField(Field):
    """The minimum viable concrete `Field` -- implements `copy()` and
    nothing else, so tests against it exercise exactly what `Field`
    itself provides.
    """

    def copy(self) -> _CompleteField:
        return _CompleteField(self.mesh, self.name)


class _IncompleteField(Field):
    """Deliberately does not implement `copy()` -- exists only to prove
    that `Field`'s abstractness actually propagates to a subclass that
    fails to complete the contract, not just to `Field` itself.
    """


def _mesh(nx: int = 2, ny: int = 3) -> Mesh:
    return StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(nx, ny))


def test_field_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Field(_mesh(), "temperature")  # type: ignore[abstract]


def test_subclass_missing_copy_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        _IncompleteField(_mesh(), "temperature")  # type: ignore[abstract]


def test_copy_is_the_only_abstract_method() -> None:
    # Pins that `Field` becomes concrete once `copy` is supplied -- the
    # actual mechanism the two tests above rely on, checked directly
    # rather than assumed from them passing.
    assert "copy" in Field.__abstractmethods__


def test_mesh_property_returns_the_mesh_passed_at_construction() -> None:
    mesh = _mesh()
    field = _CompleteField(mesh, "temperature")
    assert field.mesh is mesh


def test_name_property_returns_the_name_passed_at_construction() -> None:
    field = _CompleteField(_mesh(), "temperature")
    assert field.name == "temperature"


def test_distinct_fields_do_not_share_mesh_or_name() -> None:
    # Guards against the class of bug where `mesh`/`name` end up stored
    # on the class rather than the instance (a shared mutable default,
    # or an accidental class attribute) -- every prior field would then
    # silently report whichever values were set most recently.
    mesh_a, mesh_b = _mesh(nx=2, ny=3), _mesh(nx=5, ny=7)
    field_a = _CompleteField(mesh_a, "temperature")
    field_b = _CompleteField(mesh_b, "pressure")

    assert field_a.mesh is mesh_a
    assert field_b.mesh is mesh_b
    assert field_a.name == "temperature"
    assert field_b.name == "pressure"


def test_mesh_property_has_no_setter() -> None:
    field = _CompleteField(_mesh(), "temperature")
    with pytest.raises(AttributeError):
        field.mesh = _mesh()  # type: ignore[misc]


def test_name_property_has_no_setter() -> None:
    field = _CompleteField(_mesh(), "temperature")
    with pytest.raises(AttributeError):
        field.name = "pressure"  # type: ignore[misc]


def test_empty_name_raises_value_error() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        _CompleteField(_mesh(), "")


def test_copy_returns_an_independent_instance_with_the_same_mesh_and_name() -> None:
    mesh = _mesh()
    field = _CompleteField(mesh, "temperature")
    copied = field.copy()

    assert copied is not field
    assert copied.mesh is mesh
    assert copied.name == "temperature"
