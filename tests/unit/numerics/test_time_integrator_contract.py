"""Contract test suite for `TimeIntegrator` (TASK-020) -- the interface
that advances every transported field from one timestep to the next,
given the state and each field's time derivative
(`docs/architecture/engine.md`'s Time Integrator contract: "given the
full simulation state and its time derivative, advances it by one
timestep").

**`advance`'s second parameter is a re-evaluatable callable
(`derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]`),
not a precomputed `Mapping[str, torch.Tensor]` (TASK-025, `adr/ADR-008`).**
TASK-020's original signature only ever offered a single derivative
snapshot, which is all `_EulerIntegrator`-shaped schemes need -- but RK4
(TASK-025) evaluates the derivative three more times at intermediate
states within the step, which a fixed value cannot supply. Every test
below that used to build a raw tensor mapping now wraps it with
`_constant_derivative`, a callable that ignores the state it's handed and
always returns the same values -- reproducing exactly what the old
signature offered, for tests that don't care about re-evaluation.

Three test-only/real implementations, per Stage 3 Completion Criterion 2
(two test-only, genuinely different update rules) plus Stage 4 Completion
Criterion 3's real join (`_rk4_integrator`, TASK-025) -- `_EulerIntegrator`/
`_DoubleStepIntegrator` so the suite cannot accidentally encode one
scheme's arithmetic. No "inert implementation" teeth-check third class,
unlike the five TASK-018 suites: TASK-020's own acceptance criteria
already supply the two-sided proof that pattern exists for --
`test_zero_derivative_leaves_state_unchanged` is the boundary case an
integrator that ignores its input would also pass, and
`test_same_derivative_values_give_the_same_result_regardless_of_source`
is the nonzero case that same inert integrator would fail, so a separate
inert class would only restate what these two already establish.
`RK4Integrator`'s own genuinely-multi-stage claims (four evaluations, at
different states, fourth-order accuracy) are not this suite's job --
`tests/features/rk4_time_integration.feature`, bound by
`tests/unit/test_rk4_time_integration.py`.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping

import pytest
import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.numerics.time_integrator import RK4Integrator, TimeIntegrator
from pyflow.engine.scalar_field import ScalarField


def _constant_derivative(
    values: Mapping[str, torch.Tensor],
) -> Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]:
    """A derivative function that ignores whatever state it's called with
    and always returns `values` -- what every test here needed before
    `advance`'s second parameter became a callable (TASK-025).
    """
    return lambda _state: values


class _EulerIntegrator(TimeIntegrator):
    """Explicit Euler: `new = old + dt * derivative(old)`. Calls
    `derivative` exactly once, at the current state -- everything this
    scheme needs, and a valid (if minimal) use of the re-evaluatable
    interface.
    """

    def advance(
        self,
        fields: Mapping[str, Field],
        derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]],
        dt: float,
    ) -> dict[str, Field]:
        rates = derivative(fields)
        result: dict[str, Field] = {}
        for name, field in fields.items():
            assert isinstance(field, CollocatedField)
            advanced = field.copy()
            assert isinstance(advanced, CollocatedField)
            advanced.values[:] = field.values + dt * rates[name]
            result[name] = advanced
        return result


class _DoubleStepIntegrator(TimeIntegrator):
    """A structurally different (not physically meaningful) two-stage
    rule: applies the derivative at the *current* state as if it were an
    Euler step taken twice in sequence -- `new = old + 2 * dt *
    derivative(old)` -- so its output genuinely differs from
    `_EulerIntegrator`'s for any nonzero derivative. Evaluates
    `derivative` once, not twice, deliberately: it reuses the same rate
    for both notional increments rather than re-evaluating at the
    intermediate stage, which is what keeps it a different *rule* from
    Euler rather than a (much smaller) RK2.
    """

    def advance(
        self,
        fields: Mapping[str, Field],
        derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]],
        dt: float,
    ) -> dict[str, Field]:
        rates = derivative(fields)
        result: dict[str, Field] = {}
        for name, field in fields.items():
            assert isinstance(field, CollocatedField)
            stage = field.copy()
            assert isinstance(stage, CollocatedField)
            stage.values[:] = field.values + dt * rates[name]
            advanced = stage.copy()
            assert isinstance(advanced, CollocatedField)
            advanced.values[:] = stage.values + dt * rates[name]
            result[name] = advanced
        return result


_FACTORIES: list[tuple[str, Callable[[], TimeIntegrator]]] = [
    ("euler", _EulerIntegrator),
    ("double_step", _DoubleStepIntegrator),
    ("rk4", RK4Integrator),
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


def test_advance_signature_takes_fields_derivative_and_dt() -> None:
    params = list(inspect.signature(TimeIntegrator.advance).parameters)
    assert params == ["self", "fields", "derivative", "dt"]


def test_advance_returns_the_same_name_and_mesh(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    fields = {"temperature": _field(mesh, "temperature", 1.0)}
    derivative = _constant_derivative(
        {"temperature": torch.full((mesh.num_cells,), 2.0, dtype=torch.float64)}
    )

    result = make_integrator.advance(fields, derivative, dt=0.1)

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
    derivative = _constant_derivative(
        {
            "u": torch.full((mesh.num_cells,), 1.0, dtype=torch.float64),
            "v": torch.full((mesh.num_cells,), -1.0, dtype=torch.float64),
            "p": torch.zeros(mesh.num_cells, dtype=torch.float64),
        }
    )

    result = make_integrator.advance(fields, derivative, dt=0.5)

    assert set(result.keys()) == {"u", "v", "p"}
    for name, field in fields.items():
        assert result[name].name == name
        assert result[name].mesh is field.mesh


def test_advance_does_not_mutate_the_input(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    field = _field(mesh, "temperature", 1.0)
    fields = {"temperature": field}
    derivative = _constant_derivative(
        {"temperature": torch.full((mesh.num_cells,), 5.0, dtype=torch.float64)}
    )
    before = field.values.clone()

    make_integrator.advance(fields, derivative, dt=0.2)

    assert torch.equal(field.values, before)


def test_zero_derivative_leaves_state_unchanged(make_integrator: TimeIntegrator) -> None:
    mesh = _mesh()
    field = _field(mesh, "temperature", 3.0)
    fields = {"temperature": field}
    derivative = _constant_derivative(
        {"temperature": torch.zeros(mesh.num_cells, dtype=torch.float64)}
    )

    result = make_integrator.advance(fields, derivative, dt=0.7)

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
        {"temperature": field_a},
        _constant_derivative({"temperature": _via_scale(field_a)}),
        dt=0.3,
    )
    result_b = make_integrator.advance(
        {"temperature": field_b},
        _constant_derivative({"temperature": _via_self_sum(field_b)}),
        dt=0.3,
    )

    assert isinstance(result_a["temperature"], CollocatedField)
    assert isinstance(result_b["temperature"], CollocatedField)
    assert torch.equal(result_a["temperature"].values, result_b["temperature"].values)


def test_euler_and_double_step_produce_different_results_for_a_nonzero_derivative() -> None:
    mesh = _mesh()
    field_a = _field(mesh, "temperature", 1.0)
    field_b = _field(mesh, "temperature", 1.0)
    derivative = _constant_derivative(
        {"temperature": torch.full((mesh.num_cells,), 2.0, dtype=torch.float64)}
    )

    euler_result = _EulerIntegrator().advance({"temperature": field_a}, derivative, dt=0.5)
    double_step_result = _DoubleStepIntegrator().advance(
        {"temperature": field_b}, derivative, dt=0.5
    )

    assert isinstance(euler_result["temperature"], CollocatedField)
    assert isinstance(double_step_result["temperature"], CollocatedField)
    assert not torch.equal(
        euler_result["temperature"].values, double_step_result["temperature"].values
    )
