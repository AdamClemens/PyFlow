"""Contract test suite for `SourceTerm` (TASK-018) -- the last of the
three operators with an interface but no configuration field
(`docs/planning/roadmap.md` TASK-018's design decisions). Computes the
per-cell source contribution to a field's governing equation.

Exercised over both a `ScalarField` and a `VectorField` -- unlike
Gradient/Divergence, a source term applies to any transported quantity,
so its output shape must follow whichever field it's handed
(`component_shape` isn't knowable from `Field` alone, since `Field`
carries no storage; a test-only implementation reads it off the
concrete field via `CollocatedField`).

Same shape as `test_advection_contract.py` otherwise: two test-only
implementations for the parametrised suite, plus a deliberately inert
third one asserted to fail the "varies with input" check.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable

import pytest
import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


class _ZeroSource(SourceTerm):
    """Trivial: always zero, correct shape."""

    def source(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


class _DoubleSource(SourceTerm):
    """Varies with input: twice the field's own values -- not a real
    numerical scheme, only something whose output changes when its
    input does.
    """

    def source(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return 2.0 * field.values


class _InertSource(SourceTerm):
    """Deliberately ignores its argument -- exists only to prove the
    "varies with input" assertion below would fail against an
    implementation that doesn't.
    """

    def source(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


_FACTORIES: list[tuple[str, Callable[[], SourceTerm]]] = [
    ("zero", _ZeroSource),
    ("double", _DoubleSource),
]

_FIELD_FACTORIES: list[tuple[str, Callable[[Mesh, float], Field]]] = [
    ("scalar", lambda mesh, value: ScalarField(mesh, "temperature", initial_value=value)),
    (
        "vector",
        lambda mesh, value: VectorField(
            mesh, "velocity", num_components=2, initial_value=(value, 0.0)
        ),
    ),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _assert_varies_with_input(scheme: SourceTerm) -> None:
    mesh = _mesh()
    field_a = ScalarField(mesh, "temperature", initial_value=1.0)
    field_b = ScalarField(mesh, "temperature", initial_value=2.0)
    result_a = scheme.source(field_a)
    result_b = scheme.source(field_b)
    assert not torch.equal(result_a, result_b), "source did not change when the field did"


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_scheme(request: pytest.FixtureRequest) -> SourceTerm:
    factory: Callable[[], SourceTerm] = request.param[1]
    return factory()


@pytest.fixture(params=_FIELD_FACTORIES, ids=lambda factory: factory[0])
def make_field(request: pytest.FixtureRequest) -> Callable[[Mesh, float], Field]:
    result: Callable[[Mesh, float], Field] = request.param[1]
    return result


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        SourceTerm()  # type: ignore[abstract]


def test_subclass_missing_source_cannot_be_instantiated() -> None:
    class _Incomplete(SourceTerm):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_source_is_the_only_abstract_method() -> None:
    assert SourceTerm.__abstractmethods__ == frozenset({"source"})


def test_source_signature_takes_only_field_no_mesh() -> None:
    params = list(inspect.signature(SourceTerm.source).parameters)
    assert params == ["self", "field"]


def test_source_returns_a_contribution_shaped_like_the_field(
    make_scheme: SourceTerm, make_field: Callable[[Mesh, float], Field]
) -> None:
    mesh = _mesh()
    field = make_field(mesh, 1.0)
    assert isinstance(field, CollocatedField)
    result = make_scheme.source(field)
    assert result.shape == (mesh.num_cells, *field.component_shape)


def test_double_source_varies_with_input() -> None:
    _assert_varies_with_input(_DoubleSource())


def test_inert_source_fails_the_varies_check() -> None:
    with pytest.raises(AssertionError):
        _assert_varies_with_input(_InertSource())
