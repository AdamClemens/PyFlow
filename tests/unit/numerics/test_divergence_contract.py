"""Contract test suite for `DivergenceScheme` (TASK-018) -- another of
the three operators with an interface but no configuration field
(`docs/planning/roadmap.md` TASK-018's design decisions). Computes the
cell-centred divergence of a (typically vector) field.

Same shape as `test_advection_contract.py`: two test-only
implementations for the parametrised suite, plus a deliberately inert
third one asserted to fail the "varies with input" check.

**Gained a real third fixture, `GreenGaussDivergence` (TASK-027,
2026-08-27)** -- the divergence analogue of `test_gradient_contract.py`'s
own join, the same reasoning and the same uniform zero-gradient
`BoundaryCondition` wiring.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Literal

import pytest
import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.divergence import (
    DivergenceScheme,
    GreenGaussDivergence,
    IncompatibleVectorFieldError,
    UnconfiguredBoundaryFaceError,
)
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


class _ZeroGradientCondition(BoundaryCondition):
    """Same reasoning as `test_gradient_contract.py`'s identically-named
    double: a uniform Neumann zero-gradient condition on every edge, so
    `GreenGaussDivergence`'s own join never hits an unconfigured boundary.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


def _green_gauss_divergence() -> GreenGaussDivergence:
    condition = _ZeroGradientCondition()
    return GreenGaussDivergence(
        {"north": condition, "south": condition, "east": condition, "west": condition}
    )


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
    ("green_gauss", _green_gauss_divergence),
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


def test_green_gauss_divergence_is_exact_for_a_linear_field() -> None:
    # The physical-correctness claim this scheme's own docstring makes:
    # Green-Gauss reconstruction is exact for a linear field on a uniform
    # orthogonal mesh -- checked against a real, non-trivial linear
    # velocity field whose divergence is a nonzero constant
    # (`docs/practices.md`, "verify a conversion where its factors are
    # distinct").
    mesh = _mesh()

    class _LinearDirichlet(BoundaryCondition):
        @property
        def kind(self) -> Literal["value", "gradient"]:
            return "value"

        def evaluate(self, field: Field, face: int) -> float:
            self._check_boundary_face(field, face)
            assert isinstance(field.mesh, StructuredCartesianMesh)
            normal_x, normal_y = field.mesh.face_normal(face)
            (x0, y0), (x1, y1) = field.mesh.face_vertices(face)
            midpoint_x, midpoint_y = (x0 + x1) / 2, (y0 + y1) / 2
            vx = 1.5 * midpoint_x + 0.5 * midpoint_y
            vy = -0.5 * midpoint_x + 2.0 * midpoint_y
            return vx * normal_x + vy * normal_y

    condition = _LinearDirichlet()
    scheme = GreenGaussDivergence(
        {"north": condition, "south": condition, "east": condition, "west": condition}
    )
    field = VectorField(
        mesh,
        "velocity",
        num_components=2,
        initial_value=lambda x, y: (1.5 * x + 0.5 * y, -0.5 * x + 2.0 * y),
    )

    result = scheme.divergence(field)

    # divergence = d(vx)/dx + d(vy)/dy = 1.5 + 2.0 = 3.5, everywhere.
    assert torch.allclose(
        result, torch.full((mesh.num_cells,), 3.5, dtype=torch.float64), atol=1e-9
    )


def test_green_gauss_divergence_raises_for_an_unconfigured_boundary_face() -> None:
    mesh = _mesh()
    scheme = GreenGaussDivergence({})
    field = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))

    with pytest.raises(UnconfiguredBoundaryFaceError):
        scheme.divergence(field)


def test_green_gauss_divergence_rejects_a_field_with_the_wrong_component_shape() -> None:
    mesh = _mesh()
    condition = _ZeroGradientCondition()
    scheme = GreenGaussDivergence(
        {"north": condition, "south": condition, "east": condition, "west": condition}
    )
    field = ScalarField(mesh, "temperature", initial_value=1.0)

    with pytest.raises(IncompatibleVectorFieldError):
        scheme.divergence(field)
