"""Passive Scalar Transport golden demo (TASK-030).

The acceptance criteria are `tests/features/passive_scalar_transport.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). This module binds them
and supplies the one step only this demo needs -- reading back
`RenderWindow.simulation_fields` at two different frame counts, since the
shared vocabulary in `conftest.py` only knows how to render exactly one or
two *rendered* frames, not step a live simulation forward by a specific
count and read its own field state back.
"""

from __future__ import annotations

import pytest
from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.scalar_field import ScalarField

from ._demo import DemoRun

scenarios("passive_scalar_transport.feature")

_EARLY_FRAMES = 1
_LATE_FRAMES = 101
"""100 real RK4 timesteps apart -- at this demo's own configured
`velocity`/`timestep` (1.0, 0.02), that is 2.0 world units of expected
downstream travel, comfortably less than the mesh's own 5.0-unit domain
width (`mesh.extent[0] * mesh.spacing[0]`), so the blob never wraps
around the periodic boundary during this specific measurement -- the wrap
itself is `periodic_boundary.feature`'s own claim, not this one's.
"""


def _centroid_x(field: ScalarField) -> float:
    """The field's own mass-weighted centroid x-position -- the closest
    thing a scalar field has to "position", valid because every value
    here is non-negative (a Gaussian blob never goes negative).
    """
    mesh = field.mesh
    total_mass = 0.0
    weighted_x = 0.0
    for cell in range(mesh.num_cells):
        value = float(field.value_at(cell))
        x, _y = mesh.cell_centroid(cell)
        total_mass += value
        weighted_x += value * x
    assert total_mass > 0, "field has no mass to compute a centroid from"
    return weighted_x / total_mass


@when(
    "it is bootstrapped once after a few real timesteps and again after many more",
    target_fixture="centroids",
)
def _when_bootstrapped_at_two_frame_counts(demo: DemoRun) -> tuple[float, float]:
    # Two independent real runs (through the same public `bootstrap()`
    # entry point every other demo's deeper verification uses), not one
    # run read back twice -- there is no pre-step "frame 0" state to
    # compare against otherwise, since `RenderWindow.simulation_fields`
    # only starts existing once the first `on_frame` call has happened.
    early_window = bootstrap(demo.config_path, backend="offscreen", max_frames=_EARLY_FRAMES)
    assert early_window.simulation_fields is not None
    early_tracer = early_window.simulation_fields["tracer"]
    assert isinstance(early_tracer, ScalarField)

    late_window = bootstrap(demo.config_path, backend="offscreen", max_frames=_LATE_FRAMES)
    assert late_window.simulation_fields is not None
    late_tracer = late_window.simulation_fields["tracer"]
    assert isinstance(late_tracer, ScalarField)

    return (_centroid_x(early_tracer), _centroid_x(late_tracer))


@then(
    "the field's mass-weighted centroid has moved downstream by approximately the "
    "prescribed velocity times the elapsed time"
)
def _then_centroid_moved_at_the_prescribed_velocity(
    demo: DemoRun, centroids: tuple[float, float]
) -> None:
    early_x, late_x = centroids
    velocity_x, _velocity_y = demo.config.simulation.velocity
    dt = demo.config.numerics.timestep
    elapsed_steps = _LATE_FRAMES - _EARLY_FRAMES
    expected_displacement = velocity_x * dt * elapsed_steps
    actual_displacement = late_x - early_x
    # Measured directly before choosing this bound (not guessed): a real
    # run agrees with the closed-form prediction to within ~4% at this
    # demo's own resolution/timestep -- rel=0.15 stays comfortably above
    # that margin without being so loose a genuinely broken stepping loop
    # (frozen, backwards, or off by a large factor) could still pass.
    assert actual_displacement == pytest.approx(expected_displacement, rel=0.15), (
        f"expected the centroid to move roughly {expected_displacement} world units "
        f"downstream over {elapsed_steps} real timesteps, moved {actual_displacement} instead"
    )
