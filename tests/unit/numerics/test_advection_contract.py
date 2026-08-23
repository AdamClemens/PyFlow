"""Contract test suite for `AdvectionScheme` (TASK-018) -- the interface
computing a field's advective flux contribution at each mesh face, given
the field and the velocity field transporting it
(`docs/architecture/engine.md`'s Advection contract: "given a field and
a velocity field, produces the advective contribution to that field's
flux at each face").

Two test-only implementations, per Stage 3 Completion Criterion 2: one
trivially zero, one that actually varies with its inputs -- plus a
deliberately inert third implementation, asserted to fail the same
"varies with input" check the real one must pass, so the suite is shown
to discriminate rather than merely run.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable

import pytest
import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.advection import AdvectionScheme, IncompatibleVelocityFieldError
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


class _ZeroAdvection(AdvectionScheme):
    """Trivial: always zero, correct shape."""

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _SumAdvection(AdvectionScheme):
    """Varies with input: broadcasts the sum of the field's and
    velocity's own values to every face -- not a real numerical scheme,
    only something whose output changes when its inputs do.
    """

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        assert isinstance(field, CollocatedField)
        total = field.values.sum() + velocity.values.sum()
        return torch.full((field.mesh.num_faces,), float(total), dtype=torch.float64)


class _InertAdvection(AdvectionScheme):
    """Deliberately ignores both arguments -- exists only to prove the
    "varies with input" assertion below would fail against an
    implementation that doesn't.
    """

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


_FACTORIES: list[tuple[str, Callable[[], AdvectionScheme]]] = [
    ("zero", _ZeroAdvection),
    ("sum", _SumAdvection),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    # Non-"nice" origin/spacing and a non-square extent, matching every
    # other contract suite's fixture -- a contract that only holds for
    # convenient numbers is not a contract.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _field_and_velocity(mesh: Mesh, value: float = 1.0) -> tuple[ScalarField, VectorField]:
    field = ScalarField(mesh, "temperature", initial_value=value)
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    return field, velocity


def _assert_varies_with_input(scheme: AdvectionScheme) -> None:
    mesh = _mesh()
    field_a, velocity = _field_and_velocity(mesh, value=1.0)
    field_b, _ = _field_and_velocity(mesh, value=2.0)
    result_a = scheme.flux(field_a, velocity)
    result_b = scheme.flux(field_b, velocity)
    assert not torch.equal(result_a, result_b), "flux did not change when the field did"


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_scheme(request: pytest.FixtureRequest) -> AdvectionScheme:
    factory: Callable[[], AdvectionScheme] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        AdvectionScheme()  # type: ignore[abstract]


def test_subclass_missing_flux_cannot_be_instantiated() -> None:
    class _Incomplete(AdvectionScheme):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_flux_is_the_only_abstract_method() -> None:
    assert AdvectionScheme.__abstractmethods__ == frozenset({"flux"})


def test_flux_signature_takes_field_and_velocity_no_mesh() -> None:
    params = list(inspect.signature(AdvectionScheme.flux).parameters)
    assert params == ["self", "field", "velocity"]


def test_flux_returns_a_value_for_every_face(make_scheme: AdvectionScheme) -> None:
    mesh = _mesh()
    field, velocity = _field_and_velocity(mesh)
    result = make_scheme.flux(field, velocity)
    assert result.shape == (mesh.num_faces,)


def test_sum_advection_varies_with_input() -> None:
    _assert_varies_with_input(_SumAdvection())


def test_inert_advection_fails_the_varies_check() -> None:
    with pytest.raises(AssertionError):
        _assert_varies_with_input(_InertAdvection())


def test_incompatible_velocity_field_raises(make_scheme: AdvectionScheme) -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    bad_velocity = VectorField(mesh, "velocity", num_components=3)
    with pytest.raises(IncompatibleVelocityFieldError):
        make_scheme.flux(field, bad_velocity)
