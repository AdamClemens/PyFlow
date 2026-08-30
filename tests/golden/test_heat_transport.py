"""Heat Transport golden demo (TASK-035, Stage 6).

The acceptance criteria are `tests/features/heat_transport.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). Same shape as
`test_heat_diffusion.py`'s own join -- this demo is that one's physics,
under a field the configuration actually names -- reusing its own
two-frame-count decay measurement rather than re-deriving it.
"""

from __future__ import annotations

import math

import pytest
from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.scalar_field import ScalarField

from ._demo import DemoRun

scenarios("heat_transport.feature")

_EARLY_FRAMES = 1
_LATE_FRAMES = 201
"""Identical to `test_heat_diffusion.py`'s own constants -- same mesh,
same timestep, same diffusion coefficient, so the same 200-step decay
window applies for the same reason.
"""


def _rms_amplitude(field: ScalarField) -> float:
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
    early_temperature = early_window.simulation_fields["temperature"]
    assert isinstance(early_temperature, ScalarField)

    late_window = bootstrap(demo.config_path, backend="offscreen", max_frames=_LATE_FRAMES)
    assert late_window.simulation_fields is not None
    late_temperature = late_window.simulation_fields["temperature"]
    assert isinstance(late_temperature, ScalarField)

    return (_rms_amplitude(early_temperature), _rms_amplitude(late_temperature))


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
    temperature = next(
        declared for declared in demo.config.fields if declared.name == "temperature"
    )
    analytic_rate = temperature.diffusion_coefficient * wavenumber**2

    # Same mesh/timestep/coefficient as `test_heat_diffusion.py`'s own
    # measured demo, so the same rel=0.1 margin applies for the same
    # reason -- see that module's own comment for the measured ~0.6%
    # real agreement this bound is deliberately looser than.
    assert measured_rate == pytest.approx(analytic_rate, rel=0.1), (
        f"expected the mode to decay at roughly {analytic_rate} per unit time, "
        f"measured {measured_rate} instead"
    )


def _mesh_x_extent(demo: DemoRun) -> tuple[float, float, float, float]:
    nx, ny = demo.config.mesh.extent
    dx, dy = demo.config.mesh.spacing
    origin_x, origin_y = demo.config.mesh.origin
    return (origin_x, origin_y, origin_x + nx * dx, origin_y + ny * dy)
