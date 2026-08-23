"""Contract test suite for `GradientScheme` (TASK-018) -- one of the
three operators that get an interface but no configuration field
(`docs/planning/roadmap.md` TASK-018's design decisions: nothing has yet
identified a second implementation a user would choose between).
Computes the cell-centred gradient of a field.

Same shape as `test_advection_contract.py`: two test-only
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
from pyflow.engine.numerics.gradient import GradientScheme
from pyflow.engine.scalar_field import ScalarField

_SPATIAL_DIMENSIONS = 2


class _ZeroGradient(GradientScheme):
    """Trivial: always zero, correct shape."""

    def gradient(self, field: Field) -> torch.Tensor:
        return torch.zeros((field.mesh.num_cells, _SPATIAL_DIMENSIONS), dtype=torch.float64)


class _BroadcastGradient(GradientScheme):
    """Varies with input: broadcasts the field's own value sum into
    both components of every cell's gradient -- not a real numerical
    scheme, only something whose output changes when its input does.
    """

    def gradient(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        total = float(field.values.sum())
        return torch.full((field.mesh.num_cells, _SPATIAL_DIMENSIONS), total, dtype=torch.float64)


class _InertGradient(GradientScheme):
    """Deliberately ignores its argument -- exists only to prove the
    "varies with input" assertion below would fail against an
    implementation that doesn't.
    """

    def gradient(self, field: Field) -> torch.Tensor:
        return torch.zeros((field.mesh.num_cells, _SPATIAL_DIMENSIONS), dtype=torch.float64)


_FACTORIES: list[tuple[str, Callable[[], GradientScheme]]] = [
    ("zero", _ZeroGradient),
    ("broadcast", _BroadcastGradient),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _assert_varies_with_input(scheme: GradientScheme) -> None:
    mesh = _mesh()
    field_a = ScalarField(mesh, "temperature", initial_value=1.0)
    field_b = ScalarField(mesh, "temperature", initial_value=2.0)
    result_a = scheme.gradient(field_a)
    result_b = scheme.gradient(field_b)
    assert not torch.equal(result_a, result_b), "gradient did not change when the field did"


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_scheme(request: pytest.FixtureRequest) -> GradientScheme:
    factory: Callable[[], GradientScheme] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        GradientScheme()  # type: ignore[abstract]


def test_subclass_missing_gradient_cannot_be_instantiated() -> None:
    class _Incomplete(GradientScheme):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_gradient_is_the_only_abstract_method() -> None:
    assert GradientScheme.__abstractmethods__ == frozenset({"gradient"})


def test_gradient_signature_takes_only_field_no_mesh() -> None:
    params = list(inspect.signature(GradientScheme.gradient).parameters)
    assert params == ["self", "field"]


def test_gradient_returns_one_vector_per_cell(make_scheme: GradientScheme) -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "temperature", initial_value=1.0)
    result = make_scheme.gradient(field)
    assert result.shape == (mesh.num_cells, _SPATIAL_DIMENSIONS)


def test_broadcast_gradient_varies_with_input() -> None:
    _assert_varies_with_input(_BroadcastGradient())


def test_inert_gradient_fails_the_varies_check() -> None:
    with pytest.raises(AssertionError):
        _assert_varies_with_input(_InertGradient())
