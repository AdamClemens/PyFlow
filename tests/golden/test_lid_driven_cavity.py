"""Lid-Driven Cavity golden demo (TASK-034, Stage 5) -- the MVP's own
golden demo.

The acceptance criteria are `tests/features/lid_driven_cavity.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). This module binds
them and supplies the steps only this demo needs: reading a *solved*
velocity field back from `RenderWindow.simulation_fields`
(`_add_solved_velocity_rendering`, `src/pyflow/bootstrap.py`), which
`conftest.py`'s shared vocabulary has no step for since no earlier demo
rendered a solved vector field at all.

**Deliberately does not assert an absolute divergence bound at this
demo's own coarse (16x16), early-frame (10 steps) resolution.** Tried
first, and found to fail even well away from the lid's own two corner
singularities (`u` jumps from 1 to 0 discontinuously where the moving
lid meets a stationary wall, a genuine, well-documented property of this
exact benchmark, not an artefact): the reason is that `GreenGaussDivergence`'s
own naive face-averaged divergence is, by construction, not the
Rhie-Chow-consistent measure `PISO`'s own corrector loop actually drives
to tolerance (`src/pyflow/engine/numerics/pressure_coupling.py`'s own
`_rhie_chow_divergence` docstring: "precisely the measure that does
*not* see this"). The real, tolerance-gated divergence claim is
`tests/features/navier_stokes_timestep.feature`'s own predictor/
corrector scenario and the Ghia comparison, both measured the way `PISO`
itself measures; this module stays a lighter reproducibility smoke test.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

from ._demo import DemoRun

scenarios("lid_driven_cavity.feature")

_FEW_FRAMES = 10


@dataclass
class _SolvedRun:
    velocity: VectorField
    boundary_conditions: dict[str, BoundaryCondition]


def _run(demo: DemoRun) -> _SolvedRun:
    window = bootstrap(demo.config_path, backend="offscreen", max_frames=_FEW_FRAMES)
    assert window.simulation_fields is not None
    assert window.assembled_numerics is not None
    u = window.simulation_fields[VectorField.component_name("velocity", 0)]
    v = window.simulation_fields[VectorField.component_name("velocity", 1)]
    assert isinstance(u, ScalarField)
    assert isinstance(v, ScalarField)
    velocity = VectorField.assemble([u, v], "velocity")
    return _SolvedRun(
        velocity=velocity, boundary_conditions=dict(window.assembled_numerics.boundary_conditions)
    )


@when("it is bootstrapped for a few real timesteps", target_fixture="run")
def _when_bootstrapped(demo: DemoRun) -> _SolvedRun:
    return _run(demo)


@when("it is bootstrapped for a few real timesteps twice", target_fixture="runs")
def _when_bootstrapped_twice(demo: DemoRun) -> tuple[_SolvedRun, _SolvedRun]:
    return (_run(demo), _run(demo))


@then("the velocity field has real nonzero motion away from the lid")
def _then_nonzero_motion(run: _SolvedRun) -> None:
    # The lid itself is a boundary, not a cell -- interior cells starting
    # at rest must have picked up real motion from the moving wall by
    # now, or this demo is rendering the initial condition and nothing
    # else.
    assert float(run.velocity.magnitude().max()) > 1e-6


@then("both runs produce identical velocity fields")
def _then_identical(runs: tuple[_SolvedRun, _SolvedRun]) -> None:
    first, second = runs
    torch.testing.assert_close(first.velocity.values, second.velocity.values, rtol=0, atol=0)
