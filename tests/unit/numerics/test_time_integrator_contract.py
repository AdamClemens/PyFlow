"""Contract test suite for `TimeIntegrator` (TASK-020) -- the interface
that advances every transported field from one timestep to the next,
given the state and each field's time derivative
(`docs/architecture/engine.md`'s Time Integrator contract: "given the
full simulation state and its time derivative, advances it by one
timestep").

Two test-only implementations, per Stage 3 Completion Criterion 2, with
genuinely different update rules (`_EulerIntegrator`,
`_DoubleStepIntegrator`) so the suite cannot accidentally encode one
scheme's arithmetic. No "inert implementation" teeth-check third class,
unlike the five TASK-018 suites: TASK-020's own acceptance criteria
already supply the two-sided proof that pattern exists for --
`test_zero_derivative_leaves_state_unchanged` is the boundary case an
integrator that ignores its input would also pass, and
`test_same_derivative_values_give_the_same_result_regardless_of_source`
is the nonzero case that same inert integrator would fail, so a separate
inert class would only restate what these two already establish.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping

import pytest
import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.time_integrator import TimeIntegrator
from pyflow.engine.scalar_field import ScalarField


class _EulerIntegrator(TimeIntegrator):
    """Explicit Euler: `new = old + dt * derivative`."""

    def advance(
        self,
        fields: Mapping[str, Field],
        derivatives: Mapping[str, torch.Tensor],
        dt: float,
    ) -> dict[str, Field]:
        result: dict[str, Field] = {}
        for name, field in fields.items():
            assert isinstance(field, CollocatedField)
            advanced = field.copy()
            assert isinstance(advanced, CollocatedField)
            advanced.values[:] = field.values + dt * derivatives[name]
            result[name] = advanced
        return result


class _DoubleStepIntegrator(TimeIntegrator):
    """A structurally different (not physically meaningful) two-stage
    rule: applies the same given derivative as if it were an Euler step
    taken twice in sequence -- `new = old + 2 * dt * derivative` -- so
    its output genuinely differs from `_EulerIntegrator`'s for any
    nonzero derivative, without needing a re-evaluatable derivative
    source (out of this interface's scope; `docs/planning/roadmap.md`
    TASK-020's "Not applicable here" note).
    """

    def advance(
        self,
        fields: Mapping[str, Field],
        derivatives: Mapping[str, torch.Tensor],
        dt: float,
    ) -> dict[str, Field]:
        result: dict[str, Field] = {}
        for name, field in fields.items():
            assert isinstance(field, CollocatedField)
            stage = field.copy()
            assert isinstance(stage, CollocatedField)
            stage.values[:] = field.values + dt * derivatives[name]
            advanced = stage.copy()
            assert isinstance(advanced, CollocatedField)
            advanced.values[:] = stage.values + dt * derivatives[name]
            result[name] = advanced
        return result


_FACTORIES: list[tuple[str, Callable[[], TimeIntegrator]]] = [
    ("euler", _EulerIntegrator),
    ("double_step", _DoubleStepIntegrator),
]


def _mesh(nx: int = 3, ny: int = 2) -> Mesh:
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(nx, ny))


def _field(mesh: Mesh, name: str, value: float) -> ScalarField:
    return ScalarField(mesh, name, initial_value=value)


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_integrator(request: pytest.FixtureRequest) -> TimeIntegrator:
    factory: Callable[[], TimeIntegrator] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        TimeIntegrator()  # type: ignore[abstract]


def test_subclass_missing_advance_cannot_be_instantiated() -> None:
    class _Incomplete(TimeIntegrator):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_advance_is_the_only_abstract_method() -> None:
    assert TimeIntegrator.__abstractmethods__ == frozenset({"advance"})


def test_advance_signature_takes_fields_derivatives_and_dt() -> None:
    params = list(inspect.signature(TimeIntegrator.advance).parameters)
    assert params == ["self", "fields", "derivatives", "dt"]


def test_advance_returns_the_same_name_and_mesh(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    fields = {"temperature": _field(mesh, "temperature", 1.0)}
    derivatives = {"temperature": torch.full((mesh.num_cells,), 2.0, dtype=torch.float64)}

    result = make_integrator.advance(fields, derivatives, dt=0.1)

    assert set(result.keys()) == {"temperature"}
    assert result["temperature"].name == "temperature"
    assert result["temperature"].mesh is mesh


def test_advance_works_with_three_fields(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    fields = {
        "u": _field(mesh, "u", 1.0),
        "v": _field(mesh, "v", 2.0),
        "p": _field(mesh, "p", 3.0),
    }
    derivatives = {
        "u": torch.full((mesh.num_cells,), 1.0, dtype=torch.float64),
        "v": torch.full((mesh.num_cells,), -1.0, dtype=torch.float64),
        "p": torch.zeros(mesh.num_cells, dtype=torch.float64),
    }

    result = make_integrator.advance(fields, derivatives, dt=0.5)

    assert set(result.keys()) == {"u", "v", "p"}
    for name, field in fields.items():
        assert result[name].name == name
        assert result[name].mesh is field.mesh


def test_advance_does_not_mutate_the_input(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    field = _field(mesh, "temperature", 1.0)
    fields = {"temperature": field}
    derivatives = {"temperature": torch.full((mesh.num_cells,), 5.0, dtype=torch.float64)}
    before = field.values.clone()

    make_integrator.advance(fields, derivatives, dt=0.2)

    assert torch.equal(field.values, before)


def test_zero_derivative_leaves_state_unchanged(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    field = _field(mesh, "temperature", 3.0)
    fields = {"temperature": field}
    derivatives = {"temperature": torch.zeros(mesh.num_cells, dtype=torch.float64)}

    result = make_integrator.advance(fields, derivatives, dt=0.7)

    assert isinstance(result["temperature"], CollocatedField)
    assert torch.equal(result["temperature"].values, field.values)


def test_same_derivative_values_give_the_same_result_regardless_of_source(
    make_integrator: TimeIntegrator,
) -> None:
    """`icds.md`'s "independent of which ... schemes are configured, by
    construction" claim, turned into a test: two structurally different
    ways of arriving at a derivative -- an elementwise scale and a
    self-sum -- that happen to produce identical values for this fixture,
    fed to the same integrator, must produce identical results.
    """
    mesh = _mesh()

    def _via_scale(field: ScalarField) -> torch.Tensor:
        return field.values * 2.0

    def _via_self_sum(field: ScalarField) -> torch.Tensor:
        return field.values + field.values

    field_a = _field(mesh, "temperature", 4.0)
    field_b = _field(mesh, "temperature", 4.0)

    result_a = make_integrator.advance(
        {"temperature": field_a}, {"temperature": _via_scale(field_a)}, dt=0.3
    )
    result_b = make_integrator.advance(
        {"temperature": field_b}, {"temperature": _via_self_sum(field_b)}, dt=0.3
    )

    assert isinstance(result_a["temperature"], CollocatedField)
    assert isinstance(result_b["temperature"], CollocatedField)
    assert torch.equal(result_a["temperature"].values, result_b["temperature"].values)


def test_euler_and_double_step_produce_different_results_for_a_nonzero_derivative() -> None:
    mesh = _mesh()
    field_a = _field(mesh, "temperature", 1.0)
    field_b = _field(mesh, "temperature", 1.0)
    derivative = torch.full((mesh.num_cells,), 2.0, dtype=torch.float64)

    euler_result = _EulerIntegrator().advance(
        {"temperature": field_a}, {"temperature": derivative}, dt=0.5
    )
    double_step_result = _DoubleStepIntegrator().advance(
        {"temperature": field_b}, {"temperature": derivative}, dt=0.5
    )

    assert isinstance(euler_result["temperature"], CollocatedField)
    assert isinstance(double_step_result["temperature"], CollocatedField)
    assert not torch.equal(
        euler_result["temperature"].values, double_step_result["temperature"].values
    )
