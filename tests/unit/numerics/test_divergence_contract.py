"""Contract test suite for `DivergenceScheme` (TASK-018) -- another of
the three operators with an interface but no configuration field
(`docs/planning/roadmap.md` TASK-018's design decisions). Computes the
cell-centred divergence of a (typically vector) field.

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
from pyflow.engine.numerics.divergence import DivergenceScheme
from pyflow.engine.vector_field import VectorField


class _ZeroDivergence(DivergenceScheme):
    """Trivial: always zero, correct shape."""

    def divergence(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_cells, dtype=torch.float64)


class _SumDivergence(DivergenceScheme):
    """Varies with input: broadcasts the field's own value sum to every
    cell -- not a real numerical scheme, only something whose output
    changes when its input does.
    """

    def divergence(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.full((field.mesh.num_cells,), float(field.values.sum()), dtype=torch.float64)


class _InertDivergence(DivergenceScheme):
    """Deliberately ignores its argument -- exists only to prove the
    "varies with input" assertion below would fail against an
    implementation that doesn't.
    """

    def divergence(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_cells, dtype=torch.float64)


_FACTORIES: list[tuple[str, Callable[[], DivergenceScheme]]] = [
    ("zero", _ZeroDivergence),
    ("sum", _SumDivergence),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _assert_varies_with_input(scheme: DivergenceScheme) -> None:
    mesh = _mesh()
    field_a = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    field_b = VectorField(mesh, "velocity", num_components=2, initial_value=(2.0, 0.0))
    result_a = scheme.divergence(field_a)
    result_b = scheme.divergence(field_b)
    assert not torch.equal(result_a, result_b), "divergence did not change when the field did"


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_scheme(request: pytest.FixtureRequest) -> DivergenceScheme:
    factory: Callable[[], DivergenceScheme] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        DivergenceScheme()  # type: ignore[abstract]


def test_subclass_missing_divergence_cannot_be_instantiated() -> None:
    class _Incomplete(DivergenceScheme):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_divergence_is_the_only_abstract_method() -> None:
    assert DivergenceScheme.__abstractmethods__ == frozenset({"divergence"})


def test_divergence_signature_takes_only_field_no_mesh() -> None:
    params = list(inspect.signature(DivergenceScheme.divergence).parameters)
    assert params == ["self", "field"]


def test_divergence_returns_one_scalar_per_cell(make_scheme: DivergenceScheme) -> None:
    mesh = _mesh()
    field = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    result = make_scheme.divergence(field)
    assert result.shape == (mesh.num_cells,)


def test_sum_divergence_varies_with_input() -> None:
    _assert_varies_with_input(_SumDivergence())


def test_inert_divergence_fails_the_varies_check() -> None:
    with pytest.raises(AssertionError):
        _assert_varies_with_input(_InertDivergence())
