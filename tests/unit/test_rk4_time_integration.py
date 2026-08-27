"""Binds `tests/features/rk4_time_integration.feature` (TASK-025) --
Stage 4's fourth real numerical scheme, and Stage 4 Completion Criterion
4's own claim for it: fourth-order accuracy in time, measured with a
manufactured derivative (no real mesh/spatial scheme involved, so spatial
error cannot dominate -- the mirror image of
`test_central_difference_diffusion.py`'s own isolation, which measures
spatial order with no time-stepping at all). Separately: genuine
four-stage evaluation, at four different states, is checked directly --
`RK4Integrator`'s own specific claim, not something the generic
`TimeIntegrator` contract suite can assert (an Euler-shaped integrator is
not obligated to call its derivative more than once).

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField

scenarios("rk4_time_integration.feature")

_DECAY_RATE = 2.0
"""The manufactured ODE's own rate constant, `dy/dt = -_DECAY_RATE * y`
-- deliberately not `1.0`, the same reasoning
`test_central_difference_diffusion.py`'s `_GAMMA` records: a formula that
dropped the coefficient would still fail an assertion instead of
coincidentally passing.
"""

_Derivative = Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]


def _mesh() -> StructuredCartesianMesh:
    # Non-"nice" origin/spacing and a non-square extent, matching every
    # other contract suite's fixture in this repository.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(3, 2))


def _decay_derivative(rate: float) -> _Derivative:
    """`dy/dt = -rate * y`, evaluated at whatever state it's called
    with -- never the real mesh/`AdvectionScheme`/`DiffusionScheme`
    machinery, per Stage 4 Completion Criterion 4's "manufactured or zero
    spatial term" isolation.
    """

    def derivative(state: Mapping[str, Field]) -> Mapping[str, torch.Tensor]:
        y = state["y"]
        assert isinstance(y, CollocatedField)
        return {"y": -rate * y.values}

    return derivative


@dataclass
class _RecordingDerivative:
    """Wraps a derivative function, recording every state's own values
    it was actually called with -- what distinguishes genuine multi-stage
    evaluation from a scheme that calls its derivative four times with
    the same, stale state.
    """

    inner: _Derivative
    calls: list[torch.Tensor] = field(default_factory=list)

    def __call__(self, state: Mapping[str, Field]) -> Mapping[str, torch.Tensor]:
        y = state["y"]
        assert isinstance(y, CollocatedField)
        self.calls.append(y.values.clone())
        return self.inner(state)


def _field_with_values(mesh: StructuredCartesianMesh, values: list[float]) -> ScalarField:
    scalar = ScalarField(mesh, "y")
    scalar.values[:] = torch.tensor(values, dtype=torch.float64)
    return scalar


def _run_to(
    mesh: StructuredCartesianMesh, y0: list[float], rate: float, dt: float, steps: int
) -> torch.Tensor:
    fields: dict[str, Field] = {"y": _field_with_values(mesh, y0)}
    integrator = RK4Integrator()
    derivative = _decay_derivative(rate)
    for _ in range(steps):
        fields = integrator.advance(fields, derivative, dt)
    result = fields["y"]
    assert isinstance(result, CollocatedField)
    return result.values


# -- Fixture context -----------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    y0: list[float]
    recording: _RecordingDerivative | None = None
    dts: list[float] = field(default_factory=list)
    errors: list[float] = field(default_factory=list)


_Y0 = [1.0, 2.0, 0.5, 3.0, 1.5, 2.5]


# -- Given -----------------------------------------------------------------


@given(
    "a manufactured derivative function that records every state it is called with",
    target_fixture="ctx",
)
def _given_recording_derivative() -> _Context:
    mesh = _mesh()
    return _Context(
        mesh=mesh, y0=_Y0, recording=_RecordingDerivative(_decay_derivative(_DECAY_RATE))
    )


@given(
    "a manufactured exponential-decay derivative with a known exact solution, "
    "at decreasing timestep sizes",
    target_fixture="ctx",
)
def _given_convergence_setup() -> _Context:
    mesh = _mesh()
    return _Context(mesh=mesh, y0=_Y0, dts=[0.2, 0.1, 0.05, 0.025])


# -- When ------------------------------------------------------------------


@when("the state is advanced by one RK4 step")
def _when_one_step(ctx: _Context) -> None:
    assert ctx.recording is not None
    fields: dict[str, Field] = {"y": _field_with_values(ctx.mesh, ctx.y0)}
    RK4Integrator().advance(fields, ctx.recording, dt=0.1)


@when("the state is advanced to a fixed final time at each timestep size")
def _when_advanced_to_final_time(ctx: _Context) -> None:
    final_time = 1.0
    for dt in ctx.dts:
        steps = round(final_time / dt)
        final_values = _run_to(ctx.mesh, ctx.y0, _DECAY_RATE, dt, steps)
        exact = torch.tensor(
            [y0 * math.exp(-_DECAY_RATE * final_time) for y0 in ctx.y0], dtype=torch.float64
        )
        max_error = float(torch.max(torch.abs(final_values - exact)))
        ctx.errors.append(max_error)


# -- Then ------------------------------------------------------------------


@then("the derivative was evaluated exactly four times")
def _then_four_evaluations(ctx: _Context) -> None:
    assert ctx.recording is not None
    assert len(ctx.recording.calls) == 4


@then("every recorded state is genuinely different from every other recorded state")
def _then_states_genuinely_differ(ctx: _Context) -> None:
    # Every pair, not just some pair -- a scheme that re-evaluates once
    # but then reuses a stale intermediate state for the remaining
    # stages (e.g. RK2 masquerading as RK4) would still have *a*
    # differing pair and pass a weaker "any two differ" check.
    assert ctx.recording is not None
    calls = ctx.recording.calls
    for i in range(len(calls)):
        for j in range(i + 1, len(calls)):
            assert not torch.equal(calls[i], calls[j]), (
                f"recorded states {i} and {j} are identical -- not a genuine four-stage evaluation"
            )


@then("the observed convergence order is close to four")
def _then_order_close_to_four(ctx: _Context) -> None:
    assert len(ctx.errors) >= 3
    log_h = [math.log(h) for h in ctx.dts]
    log_e = [math.log(e) for e in ctx.errors]
    n = len(log_h)
    mean_h = sum(log_h) / n
    mean_e = sum(log_e) / n
    numerator = sum((log_h[i] - mean_h) * (log_e[i] - mean_e) for i in range(n))
    denominator = sum((log_h[i] - mean_h) ** 2 for i in range(n))
    order = numerator / denominator
    assert 3.8 <= order <= 4.2, f"expected convergence order close to 4, got {order}"
