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
        {"north": condition, "south": condition, "east": condition, "west": condition}, {}
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
        {"north": condition, "south": condition, "east": condition, "west": condition}, {}
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
    scheme = GreenGaussDivergence({}, {})
    field = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))

    with pytest.raises(UnconfiguredBoundaryFaceError):
        scheme.divergence(field)


def test_green_gauss_divergence_rejects_a_field_with_the_wrong_component_shape() -> None:
    mesh = _mesh()
    condition = _ZeroGradientCondition()
    scheme = GreenGaussDivergence(
        {"north": condition, "south": condition, "east": condition, "west": condition}, {}
    )
    field = ScalarField(mesh, "temperature", initial_value=1.0)

    with pytest.raises(IncompatibleVectorFieldError):
        scheme.divergence(field)


def test_green_gauss_divergence_is_periodic_aware() -> None:
    # TASK-034 (Stage 5): a face named in `periodic_pairs` must not raise
    # `UnconfiguredBoundaryFaceError`. A uniform velocity field is
    # trivially periodic and must give exactly zero divergence everywhere
    # (verified numerically before being written here) -- this is also
    # the mechanism Stage 5 Completion Criterion 4's own "uniform flow on
    # a fully periodic domain stays divergence-free" null test depends on
    # being true at the `PISO` level. A non-uniform, hand-assigned field
    # (not from a smooth function, so nothing is accidentally continuous
    # across the wrap) must give a real nonzero divergence matching a
    # value hand-derived directly from `mesh.wrapped_neighbour_cell` --
    # proving the periodic branch reads the real wrapped neighbour rather
    # than silently skipping the face.
    mesh = _mesh()
    assert isinstance(mesh, StructuredCartesianMesh)
    all_periodic = {"north": "south", "south": "north", "east": "west", "west": "east"}
    scheme = GreenGaussDivergence({}, all_periodic)

    uniform = VectorField(mesh, "velocity", num_components=2, initial_value=(1.3, -0.7))
    uniform_result = scheme.divergence(uniform)
    assert torch.allclose(
        uniform_result, torch.zeros(mesh.num_cells, dtype=torch.float64), atol=1e-9
    )

    nonuniform = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    for cell in range(mesh.num_cells):
        nonuniform.set_value_at(cell, (float((cell * 7) % 5) - 2.0, float((cell * 3) % 4) - 1.5))
    nonuniform_result = scheme.divergence(nonuniform)
    assert not torch.allclose(
        nonuniform_result, torch.zeros(mesh.num_cells, dtype=torch.float64), atol=1e-9
    )

    cell = 0
    total = 0.0
    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        if owner != cell and neighbour != cell:
            continue
        sign = 1.0 if owner == cell else -1.0
        normal_x, normal_y = mesh.face_normal(face)
        if neighbour is None:
            neighbour = mesh.wrapped_neighbour_cell(face)
        owner_x, owner_y = nonuniform.value_at(owner)
        neighbour_x, neighbour_y = nonuniform.value_at(neighbour)
        face_x, face_y = (owner_x + neighbour_x) / 2, (owner_y + neighbour_y) / 2
        face_normal_velocity = face_x * normal_x + face_y * normal_y
        total += sign * face_normal_velocity * mesh.face_area(face)
    total /= mesh.cell_volume(cell)
    assert float(nonuniform_result[cell]) == pytest.approx(total, abs=1e-9)
