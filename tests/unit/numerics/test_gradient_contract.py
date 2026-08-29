"""Contract test suite for `GradientScheme` (TASK-018) -- one of the
three operators that get an interface but no configuration field
(`docs/planning/roadmap.md` TASK-018's design decisions: nothing has yet
identified a second implementation a user would choose between).
Computes the cell-centred gradient of a field.

Same shape as `test_advection_contract.py`: two test-only
implementations for the parametrised suite, plus a deliberately inert
third one asserted to fail the "varies with input" check.

**Gained a real third fixture, `GreenGaussGradient` (TASK-027,
2026-08-27)** -- Stage 4 Completion Criterion 3's own share for this
non-ADR-003 interface, joined the same way `test_advection_contract.py`'s
join wired `FirstOrderUpwindAdvection`: a uniform zero-gradient
`BoundaryCondition` on all four edges, so this suite's own generic
fixtures never hit an unconfigured boundary.
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
from pyflow.engine.numerics.gradient import (
    GradientScheme,
    GreenGaussGradient,
    UnconfiguredBoundaryFaceError,
)
from pyflow.engine.scalar_field import ScalarField

_SPATIAL_DIMENSIONS = 2


class _ZeroGradientCondition(BoundaryCondition):
    """Same reasoning as `test_advection_contract.py`'s identically-named
    double: a uniform Neumann zero-gradient condition on every edge, so
    `GreenGaussGradient`'s own join never hits an unconfigured boundary.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


def _green_gauss_gradient() -> GreenGaussGradient:
    condition = _ZeroGradientCondition()
    return GreenGaussGradient(
        {"north": condition, "south": condition, "east": condition, "west": condition}, {}
    )


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
    ("green_gauss", _green_gauss_gradient),
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


def test_green_gauss_gradient_is_exact_for_a_linear_field() -> None:
    # The physical-correctness claim this scheme's own docstring makes:
    # Green-Gauss reconstruction is exact for a linear field on a uniform
    # orthogonal mesh -- checked against a real, non-trivial linear field
    # (`docs/practices.md`, "verify a conversion where its factors are
    # distinct": neither slope is 0 or 1, and neither matches the other).
    mesh = _mesh()

    class _LinearDirichlet(BoundaryCondition):
        @property
        def kind(self) -> Literal["value", "gradient"]:
            return "value"

        def evaluate(self, field: Field, face: int) -> float:
            self._check_boundary_face(field, face)
            assert isinstance(field.mesh, StructuredCartesianMesh)
            (x0, y0), (x1, y1) = field.mesh.face_vertices(face)
            return 2.0 * (x0 + x1) / 2 - 3.0 * (y0 + y1) / 2

    condition = _LinearDirichlet()
    scheme = GreenGaussGradient(
        {"north": condition, "south": condition, "east": condition, "west": condition}, {}
    )
    field = ScalarField(mesh, "phi", initial_value=lambda x, y: 2.0 * x - 3.0 * y)

    result = scheme.gradient(field)

    expected = torch.tensor([2.0, -3.0], dtype=torch.float64).expand(mesh.num_cells, 2)
    assert torch.allclose(result, expected, atol=1e-9)


def test_green_gauss_gradient_raises_for_an_unconfigured_boundary_face() -> None:
    mesh = _mesh()
    scheme = GreenGaussGradient({}, {})
    field = ScalarField(mesh, "phi", initial_value=1.0)

    with pytest.raises(UnconfiguredBoundaryFaceError):
        scheme.gradient(field)


def test_green_gauss_gradient_is_periodic_aware() -> None:
    # TASK-034 (Stage 5): a face named in `periodic_pairs` must not raise
    # `UnconfiguredBoundaryFaceError` even with no `BoundaryCondition` at
    # all configured. A genuinely linear field is not itself periodic (it
    # does not agree with itself across the wrap), so "exact for a linear
    # field" is not the claim to check here -- a uniform field is
    # trivially periodic and must give an exactly zero gradient
    # everywhere, checked first; a non-uniform field with hand-assigned
    # per-cell values (not from a smooth function, so nothing about it is
    # accidentally continuous across the wrap) must give a real nonzero
    # gradient that matches a hand-derived value built directly from
    # `mesh.wrapped_neighbour_cell` -- proving the periodic branch reads
    # the real wrapped neighbour rather than silently skipping the face
    # (which would also avoid raising, but would leave every boundary
    # cell's own gradient contribution wrong). Verified numerically before
    # being written into this test, not assumed.
    mesh = _mesh()
    assert isinstance(mesh, StructuredCartesianMesh)
    all_periodic = {"north": "south", "south": "north", "east": "west", "west": "east"}
    scheme = GreenGaussGradient({}, all_periodic)

    uniform = ScalarField(mesh, "phi", initial_value=3.7)
    uniform_result = scheme.gradient(uniform)
    assert torch.allclose(
        uniform_result, torch.zeros((mesh.num_cells, 2), dtype=torch.float64), atol=1e-9
    )

    nonuniform = ScalarField(mesh, "phi", initial_value=0.0)
    for cell in range(mesh.num_cells):
        nonuniform.set_value_at(cell, float((cell * 7) % 5) - 2.0)
    nonuniform_result = scheme.gradient(nonuniform)
    assert not torch.allclose(
        nonuniform_result, torch.zeros((mesh.num_cells, 2), dtype=torch.float64), atol=1e-9
    )

    # Hand-derived directly from the mesh's own wrapped-neighbour lookup,
    # not from this scheme -- independent of the implementation under
    # test, the same discipline `_numerics.py`'s own `face_normal_velocity`
    # helper uses.
    cell = 0
    total = torch.zeros(2, dtype=torch.float64)
    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        if owner != cell and neighbour != cell:
            continue
        sign = 1.0 if owner == cell else -1.0
        normal_x, normal_y = mesh.face_normal(face)
        if neighbour is None:
            neighbour = mesh.wrapped_neighbour_cell(face)
        face_value = (nonuniform.value_at(owner) + nonuniform.value_at(neighbour)) / 2
        area = mesh.face_area(face)
        total[0] += sign * face_value * normal_x * area
        total[1] += sign * face_value * normal_y * area
    total = total / mesh.cell_volume(cell)
    assert torch.allclose(nonuniform_result[cell], total, atol=1e-9)
