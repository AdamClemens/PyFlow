"""TimeIntegrator (TASK-020): the interface that advances every
transported field from one timestep to the next, given the state and
each field's time derivative from the other numerics layers
(`docs/architecture/engine.md`'s Time Integrator contract: "given the
full simulation state and its time derivative, advances it by one
timestep").

Consumes a time derivative, not the schemes that produced it -- the
consequence `docs/architecture/icds.md` states explicitly: the
integrator is "independent of which advection/diffusion/pressure-
coupling schemes are configured, by construction". Advances a *mapping*
of fields, not one -- `engine.md`: "independent of which fields exist or
how many" -- so a caller never has to loop, and coupled systems (Stage
5's velocity/pressure) can express themselves through one call.

**`advance`'s second parameter is a re-evaluatable callable, not a
precomputed value (TASK-025, `adr/ADR-008`).** TASK-020's original
signature took `derivatives: Mapping[str, torch.Tensor]` -- a single
snapshot, computed once by the caller before `advance` was ever called.
That is everything an Euler-shaped scheme needs, but RK4 (below)
evaluates the derivative three more times at intermediate states within
the step, which a fixed value cannot supply -- confirmed by reading
`simulation.step`'s own source before this change, not assumed.
`derivative(state)` returns each field's time derivative evaluated *at*
`state`, which need not be `fields` itself; a single-stage integrator
calls it once, with `fields`, reproducing exactly what the old signature
offered.

No concrete integrator lived here through Stage 3 -- Stage 3 Completion
Criterion 1. `RK4Integrator` (TASK-025, Stage 4) is the first.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field


class TimeIntegrator(ABC):
    """Advances a named set of fields forward by `dt`, given a function
    that computes each field's time derivative at any state.
    """

    @abstractmethod
    def advance(
        self,
        fields: Mapping[str, Field],
        derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]],
        dt: float,
    ) -> dict[str, Field]:
        """Return a new set of fields, one per key in `fields`, each
        advanced by `dt` from its current state.

        `derivative(state)` returns each field's time derivative
        evaluated at `state` -- called with `fields` itself for a
        single-stage (e.g. Euler) scheme, and again with one or more
        intermediate states for a multi-stage scheme (e.g. RK4). Must
        not mutate `fields`, any field in it, or any state passed to
        `derivative`.
        """


def _advanced_by(
    fields: Mapping[str, Field], deltas: Mapping[str, torch.Tensor]
) -> dict[str, Field]:
    """`{name: field.value + deltas[name]}`, one fresh `Field` per entry
    -- the same `.copy()`-then-`.values[:] =` shape every concrete
    `TimeIntegrator` in this repository already uses, factored out here
    since `RK4Integrator` needs it four times (three intermediate stages
    plus the final weighted combination) rather than once.
    """
    result: dict[str, Field] = {}
    for name, field in fields.items():
        assert isinstance(field, CollocatedField)
        advanced = field.copy()
        assert isinstance(advanced, CollocatedField)
        advanced.values[:] = field.values + deltas[name]
        result[name] = advanced
    return result


class RK4Integrator(TimeIntegrator):
    """Classical fourth-order Runge-Kutta
    (`docs/handbook/numerical-methods/time-integration.md`): evaluates
    the derivative at the current state and at three successively
    refined intermediate estimates within the timestep, then combines
    all four with fixed weights.

    ```
    k1 = derivative(fields)
    k2 = derivative(fields + dt/2 * k1)
    k3 = derivative(fields + dt/2 * k2)
    k4 = derivative(fields + dt   * k3)
    result = fields + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
    ```

    No rejection path of its own -- the same reasoning TASK-020's own
    design decision already recorded for `_EulerIntegrator`/
    `_DoubleStepIntegrator`: a mismatched key between `fields` and what
    `derivative` returns is a plain `KeyError` from reading the mapping,
    not a condition this interface needs to name and reject.
    """

    def advance(
        self,
        fields: Mapping[str, Field],
        derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]],
        dt: float,
    ) -> dict[str, Field]:
        k1 = derivative(fields)
        stage_b = _advanced_by(fields, {name: dt / 2 * rate for name, rate in k1.items()})
        k2 = derivative(stage_b)
        stage_c = _advanced_by(fields, {name: dt / 2 * rate for name, rate in k2.items()})
        k3 = derivative(stage_c)
        stage_d = _advanced_by(fields, {name: dt * rate for name, rate in k3.items()})
        k4 = derivative(stage_d)

        combined = {
            name: dt / 6 * (k1[name] + 2 * k2[name] + 2 * k3[name] + k4[name]) for name in fields
        }
        return _advanced_by(fields, combined)
