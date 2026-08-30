"""Thermal Buoyancy golden demo (TASK-035, Stage 6).

The acceptance criteria are `tests/features/thermal_buoyancy.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). The first golden demo
combining a declared field with solved, pressure-corrected velocity --
`bootstrap.py`'s `_add_declared_field_transport` already supported this
combination generically (built for TASK-042, not anticipating
buoyancy), so no bootstrap.py change was needed to run it.
"""

from __future__ import annotations

from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.scalar_field import ScalarField
from pyflow.rendering.window import RenderWindow

from ._demo import DemoRun

scenarios("thermal_buoyancy.feature")

_FRAMES = 10
"""Measured directly against this demo's own config (mesh, viscosity,
buoyancy coefficient) before choosing it, not guessed: the warmest
cell's own vertical velocity is already clearly positive after a single
frame and grows monotonically through at least ten -- enough real
timesteps to be a genuine claim about the dynamics, not the first-frame
transient alone.
"""


@when("it is bootstrapped for several real timesteps", target_fixture="window")
def _when_bootstrapped(demo: DemoRun) -> RenderWindow:
    return bootstrap(demo.config_path, backend="offscreen", max_frames=_FRAMES)


@then("the vertical velocity at the temperature field's own warmest cell is positive")
def _then_warmest_cell_rises(window: RenderWindow) -> None:
    assert window.simulation_fields is not None
    temperature = window.simulation_fields["temperature"]
    vertical_velocity = window.simulation_fields["velocity.1"]
    assert isinstance(temperature, ScalarField)
    assert isinstance(vertical_velocity, ScalarField)

    mesh = temperature.mesh
    warmest_cell = max(range(mesh.num_cells), key=lambda cell: temperature.value_at(cell))

    assert vertical_velocity.value_at(warmest_cell) > 0.0, (
        "expected the warmest cell's own vertical velocity to be positive (rising)"
    )
