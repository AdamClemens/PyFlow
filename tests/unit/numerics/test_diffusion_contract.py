"""Contract test suite for `DiffusionScheme` (TASK-018) -- the interface
computing a field's diffusive flux contribution at each mesh face, given
the field alone (`docs/architecture/engine.md`'s Diffusion contract:
"given a field, produces the diffusive contribution to that field's flux
at each face").

Same shape as `test_advection_contract.py`: two test-only
implementations for the parametrised suite, plus a deliberately inert
third one asserted to fail the "varies with input" check.
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
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion, DiffusionScheme
from pyflow.engine.scalar_field import ScalarField


class _ZeroGradientCondition(BoundaryCondition):
    """A Neumann condition this suite's own fixture uses uniformly on
    every edge, so `CentralDifferenceDiffusion`'s join below never hits
    an unconfigured boundary -- irrelevant to what this suite actually
    checks (shape, "varies with input") -- mirrors
    `test_advection_contract.py`'s own identically-named, identically-
    purposed double.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


def _central_difference_diffusion() -> CentralDifferenceDiffusion:
    condition = _ZeroGradientCondition()
    return CentralDifferenceDiffusion(
        {"north": condition, "south": condition, "east": condition, "west": condition},
        {},
        1.0,
    )


class _ZeroDiffusion(DiffusionScheme):
    """Trivial: always zero, correct shape."""

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _SumDiffusion(DiffusionScheme):
    """Varies with input: broadcasts the field's own value sum to every
    face -- not a real numerical scheme, only something whose output
    changes when its input does.
    """

    def flux(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.full((field.mesh.num_faces,), float(field.values.sum()), dtype=torch.float64)


class _InertDiffusion(DiffusionScheme):
    """Deliberately ignores its argument -- exists only to prove the
    "varies with input" assertion below would fail against an
    implementation that doesn't.
    """

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


_FACTORIES: list[tuple[str, Callable[[], DiffusionScheme]]] = [
    ("zero", _ZeroDiffusion),
    ("sum", _SumDiffusion),
    # The real MVP scheme (TASK-024, Stage 4) -- joins by adding a factory
    # here, per Stage 4 Completion Criterion 3; no existing test body in
    # this module changes.
    ("central_difference", _central_difference_diffusion),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _assert_varies_with_input(scheme: DiffusionScheme) -> None:
    mesh = _mesh()
    field_a = ScalarField(mesh, "temperature", initial_value=1.0)
    field_b = ScalarField(mesh, "temperature", initial_value=2.0)
    result_a = scheme.flux(field_a)
    result_b = scheme.flux(field_b)
    assert not torch.equal(result_a, result_b), "flux did not change when the field did"


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_scheme(request: pytest.FixtureRequest) -> DiffusionScheme:
    factory: Callable[[], DiffusionScheme] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        DiffusionScheme()  # type: ignore[abstract]


def test_subclass_missing_flux_cannot_be_instantiated() -> None:
    class _Incomplete(DiffusionScheme):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_flux_is_the_only_abstract_method() -> None:
    assert DiffusionScheme.__abstractmethods__ == frozenset({"flux"})


def test_flux_signature_takes_only_field_no_mesh() -> None:
    params = list(inspect.signature(DiffusionScheme.flux).parameters)
    assert params == ["self", "field"]


def test_flux_returns_a_value_for_every_face(make_scheme: DiffusionScheme) -> None:
    mesh = _mesh()
    field = ScalarField(mesh, "temperature", initial_value=1.0)
    result = make_scheme.flux(field)
    assert result.shape == (mesh.num_faces,)


def test_sum_diffusion_varies_with_input() -> None:
    _assert_varies_with_input(_SumDiffusion())


def test_inert_diffusion_fails_the_varies_check() -> None:
    with pytest.raises(AssertionError):
        _assert_varies_with_input(_InertDiffusion())
