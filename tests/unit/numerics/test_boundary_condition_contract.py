"""Contract test suite for `BoundaryCondition` (TASK-019) -- the
interface for how a field behaves at a domain edge where no
neighbouring control volume supplies a flux
(`docs/architecture/engine.md`'s Boundary Condition contract: "given a
boundary face and the field's interior state, produces the face value
or gradient the interior scheme needs").

Two test-only implementations, per Stage 3 Completion Criterion 2: one
supplying a face value (the Dirichlet shape), one supplying a face
gradient (the Neumann shape) -- without being either, since no concrete
condition shipped in Stage 3 (Criterion 1).

`DirichletBoundaryCondition` (TASK-028, Stage 4) is the real third
fixture this suite joins -- its own physical-correctness claim (a real
interior scheme, not this suite's own doubles, computes the right thing
with it) is `tests/features/dirichlet_boundary.feature`, bound by
`tests/unit/test_dirichlet_boundary.py`. `NeumannBoundaryCondition`
(TASK-029, Stage 4) is the real fourth, the same way; its own
physical-correctness claim is `tests/features/neumann_boundary.feature`,
bound by `tests/unit/test_neumann_boundary.py`.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Literal

import pytest

from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import (
    BoundaryCondition,
    DirichletBoundaryCondition,
    NeumannBoundaryCondition,
    NotABoundaryFaceError,
)
from pyflow.engine.scalar_field import ScalarField


class _FixedValueCondition(BoundaryCondition):
    """The Dirichlet shape: supplies a fixed face value."""

    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._value


class _FixedGradientCondition(BoundaryCondition):
    """The Neumann shape: supplies a fixed face gradient."""

    def __init__(self, gradient: float) -> None:
        self._gradient = gradient

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._gradient


_FACTORIES: list[tuple[str, Callable[[], BoundaryCondition]]] = [
    ("value", lambda: _FixedValueCondition(3.0)),
    ("gradient", lambda: _FixedGradientCondition(-1.5)),
    ("dirichlet", lambda: DirichletBoundaryCondition(3.0)),
    ("neumann", lambda: NeumannBoundaryCondition(-1.5)),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _boundary_and_interior_faces(mesh: Mesh) -> tuple[int, int]:
    boundary_face = next(f for f in range(mesh.num_faces) if mesh.is_boundary_face(f))
    interior_face = next(f for f in range(mesh.num_faces) if not mesh.is_boundary_face(f))
    return boundary_face, interior_face


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_condition(request: pytest.FixtureRequest) -> BoundaryCondition:
    factory: Callable[[], BoundaryCondition] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        BoundaryCondition()  # type: ignore[abstract]


def test_subclass_missing_kind_cannot_be_instantiated() -> None:
    class _Incomplete(BoundaryCondition):
        def evaluate(self, field: Field, face: int) -> float:
            return 0.0

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_subclass_missing_evaluate_cannot_be_instantiated() -> None:
    class _Incomplete(BoundaryCondition):
        @property
        def kind(self) -> Literal["value", "gradient"]:
            return "value"

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_kind_and_evaluate_are_the_only_abstract_members() -> None:
    assert BoundaryCondition.__abstractmethods__ == frozenset({"kind", "evaluate"})


def test_evaluate_signature_takes_field_and_face_no_mesh() -> None:
    params = list(inspect.signature(BoundaryCondition.evaluate).parameters)
    assert params == ["self", "field", "face"]


def test_evaluate_produces_the_boundary_faces_value_or_gradient(
    make_condition: BoundaryCondition,
) -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "temperature", initial_value=1.0)
    boundary_face, _ = _boundary_and_interior_faces(mesh)

    result = make_condition.evaluate(field, boundary_face)

    assert isinstance(result, float)


def test_fixed_value_condition_reports_its_kind_and_value() -> None:
    condition = _FixedValueCondition(3.0)
    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    boundary_face, _ = _boundary_and_interior_faces(mesh)

    assert condition.kind == "value"
    assert condition.evaluate(field, boundary_face) == 3.0


def test_fixed_gradient_condition_reports_its_kind_and_gradient() -> None:
    condition = _FixedGradientCondition(-1.5)
    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    boundary_face, _ = _boundary_and_interior_faces(mesh)

    assert condition.kind == "gradient"
    assert condition.evaluate(field, boundary_face) == -1.5


def test_dirichlet_boundary_condition_reports_its_kind_and_value() -> None:
    condition = DirichletBoundaryCondition(7.25)
    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    boundary_face, _ = _boundary_and_interior_faces(mesh)

    assert condition.kind == "value"
    assert condition.evaluate(field, boundary_face) == 7.25


def test_neumann_boundary_condition_reports_its_kind_and_gradient() -> None:
    condition = NeumannBoundaryCondition(-4.25)
    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    boundary_face, _ = _boundary_and_interior_faces(mesh)

    assert condition.kind == "gradient"
    assert condition.evaluate(field, boundary_face) == -4.25


def test_applying_a_condition_to_an_interior_face_raises(
    make_condition: BoundaryCondition,
) -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    _, interior_face = _boundary_and_interior_faces(mesh)

    with pytest.raises(NotABoundaryFaceError):
        make_condition.evaluate(field, interior_face)
