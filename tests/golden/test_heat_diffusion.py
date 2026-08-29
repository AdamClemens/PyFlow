"""Heat Diffusion golden demo (TASK-034, Stage 5).

The acceptance criteria are `tests/features/heat_diffusion.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). This module binds
them and supplies the one step only this demo needs -- measuring the
transported field's own decay rate between two frame counts, the same
"two independent bootstraps, not one run read back twice" shape
`test_passive_scalar_transport.py` already established, reused here
rather than re-derived.
"""

from __future__ import annotations

import math

import pytest
from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.scalar_field import ScalarField

from ._demo import DemoRun

scenarios("heat_diffusion.feature")

_EARLY_FRAMES = 1
_LATE_FRAMES = 201
"""200 real RK4 timesteps apart -- at this demo's own configured
`numerics.timestep` (0.01), that is 2.0 time units of decay, enough for
the mode's own amplitude to drop by roughly 35% at the configured
diffusion coefficient -- measured directly (`docs/planning/roadmap.md`
TASK-034's own Design decision) before choosing this frame count, not
guessed: too few steps leaves too little decay to measure the rate from
accurately, too many costs test runtime for no added precision.
"""


def _rms_amplitude(field: ScalarField) -> float:
    """The field's own root-mean-square value over every cell -- a
    single number describing "how much mode is left" that does not
    depend on knowing which cell the mode's own peak currently sits in,
    unlike sampling one specific cell.
    """
    mesh = field.mesh
    total = 0.0
    for cell in range(mesh.num_cells):
        total += float(field.value_at(cell)) ** 2
    return math.sqrt(total / mesh.num_cells)


@when(
    "it is bootstrapped once after a few real timesteps and again after many more",
    target_fixture="amplitudes",
)
def _when_bootstrapped_at_two_frame_counts(demo: DemoRun) -> tuple[float, float]:
    early_window = bootstrap(demo.config_path, backend="offscreen", max_frames=_EARLY_FRAMES)
    assert early_window.simulation_fields is not None
    early_tracer = early_window.simulation_fields["tracer"]
    assert isinstance(early_tracer, ScalarField)

    late_window = bootstrap(demo.config_path, backend="offscreen", max_frames=_LATE_FRAMES)
    assert late_window.simulation_fields is not None
    late_tracer = late_window.simulation_fields["tracer"]
    assert isinstance(late_tracer, ScalarField)

    return (_rms_amplitude(early_tracer), _rms_amplitude(late_tracer))


@then(
    "the measured decay rate matches the analytic rate for the configured diffusion "
    "coefficient and wavenumber"
)
def _then_decay_rate_matches_analytic(demo: DemoRun, amplitudes: tuple[float, float]) -> None:
    early_amplitude, late_amplitude = amplitudes
    dt = demo.config.numerics.timestep
    elapsed_steps = _LATE_FRAMES - _EARLY_FRAMES
    elapsed_time = dt * elapsed_steps
    measured_rate = -math.log(late_amplitude / early_amplitude) / elapsed_time

    min_x, _min_y, max_x, _max_y = _mesh_x_extent(demo)
    domain_width = max_x - min_x
    wavenumber = 2 * math.pi / domain_width
    analytic_rate = demo.config.fluid.diffusion_coefficient * wavenumber**2

    # Measured directly before choosing this bound, not guessed
    # (`docs/planning/roadmap.md` TASK-034's own Design decision): a real
    # run agrees with the closed-form rate to within ~0.6% at this
    # demo's own resolution/timestep -- rel=0.1 stays comfortably above
    # that margin without being so loose a genuinely broken diffusion
    # scheme (wrong coefficient, wrong sign, no diffusion at all) could
    # still pass.
    assert measured_rate == pytest.approx(analytic_rate, rel=0.1), (
        f"expected the mode to decay at roughly {analytic_rate} per unit time, "
        f"measured {measured_rate} instead"
    )


def _mesh_x_extent(demo: DemoRun) -> tuple[float, float, float, float]:
    nx, ny = demo.config.mesh.extent
    dx, dy = demo.config.mesh.spacing
    origin_x, origin_y = demo.config.mesh.origin
    return (origin_x, origin_y, origin_x + nx * dx, origin_y + ny * dy)
