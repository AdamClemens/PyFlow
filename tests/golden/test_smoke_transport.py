"""Smoke Transport golden demo (TASK-038, Stage 6).

The acceptance criteria are `tests/features/smoke_transport.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). The same
lid-driven-cavity shape `lid_driven_cavity.yaml` already proved stable,
now also carrying a declared `smoke` field
(`bootstrap.py`'s `_add_declared_field_transport`, which already
supported a declared field alongside solved velocity generically --
built for TASK-042, exercised the same way by `thermal_buoyancy.yaml`).
No `bootstrap.py` change was needed to run this demo.

The exactness of "passive" (no effect on velocity, not itself inert) is
proven at the engine level by `tests/features/passive_tracers.feature`
against a small, purpose-built fixture -- not re-proven here, the same
split `thermal_buoyancy.feature` uses relative to `temperature_field.
feature`'s own null-case scenario.
"""

from __future__ import annotations

from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.scalar_field import ScalarField
from pyflow.rendering.window import RenderWindow

from ._demo import DemoRun

scenarios("smoke_transport.feature")

_FRAMES = 10
"""Measured directly against this demo's own config before choosing it,
the same discipline `test_thermal_buoyancy.py`'s own `_FRAMES` uses: the
smoke field's own RMS value has already dropped measurably (~0.140 ->
~0.127) by ten real timesteps as it spreads under the recirculating
flow, and every element compared below differs well outside floating-
point noise.
"""


@when(
    "it is bootstrapped for a single real timestep and again for several more",
    target_fixture="frames",
)
def _when_bootstrapped_twice(demo: DemoRun) -> tuple[RenderWindow, RenderWindow]:
    early = bootstrap(demo.config_path, backend="offscreen", max_frames=1)
    late = bootstrap(demo.config_path, backend="offscreen", max_frames=_FRAMES)
    return early, late


@then("the smoke field after several timesteps differs from the smoke field after one")
def _then_smoke_transported(frames: tuple[RenderWindow, RenderWindow]) -> None:
    early, late = frames
    assert early.simulation_fields is not None
    assert late.simulation_fields is not None
    early_smoke = early.simulation_fields["smoke"]
    late_smoke = late.simulation_fields["smoke"]
    assert isinstance(early_smoke, ScalarField)
    assert isinstance(late_smoke, ScalarField)
    assert not early_smoke.values.equal(late_smoke.values), (
        "expected the smoke field to keep changing under the recirculating flow, not freeze "
        "after one step"
    )
