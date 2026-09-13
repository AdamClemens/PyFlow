"""Unit tests for pyflow.simulation_run (TASK-045, Stage 8, Recording &
Playback) -- the simulation-state construction/advance logic extracted
from `bootstrap.py`'s two live-rendering paths so `recording.py`'s
headless one can share it. `tests/unit/test_bootstrap.py` and every
golden-demo/feature scenario touching either live path are this
refactor's own real regression coverage (unmodified, still green); these
tests cover the extracted functions directly, in isolation.
"""

from __future__ import annotations

import logging

import pytest

from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    FieldConfig,
    FluidConfig,
    MeshConfig,
    NumericsConfig,
    PyFlowConfig,
    SimulationConfig,
)
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.assembly import assemble_numerics
from pyflow.rendering.mesh_visualization import mesh_bounding_box
from pyflow.simulation_run import (
    _domain_bounds,
    advance_simulation_state,
    build_simulation_state,
    velocity_field_from_state,
)

_MESH_CONFIG = MeshConfig(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(5, 4))


def test_domain_bounds_matches_mesh_bounding_box() -> None:
    """`_domain_bounds` deliberately doesn't import `mesh_bounding_box`
    (it would drag `pygfx` into `recording.py`'s own import chain -- see
    `simulation_run.py`'s own module docstring), so this is the
    permanent regression test proving the two stay numerically identical
    for a `StructuredCartesianMesh` -- not just verified once, ad hoc,
    while designing this.
    """
    mesh = StructuredCartesianMesh.from_config(_MESH_CONFIG)
    assert _domain_bounds(_MESH_CONFIG) == mesh_bounding_box(mesh)


def test_build_simulation_state_returns_none_for_a_static_config() -> None:
    config = PyFlowConfig(mesh=_MESH_CONFIG)
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    assert build_simulation_state(mesh, config) is None


def test_build_simulation_state_is_passive_mode_for_a_declared_unsolved_field() -> None:
    config = PyFlowConfig(
        mesh=_MESH_CONFIG, fields=[FieldConfig(name="smoke", initial_condition="gaussian_blob")]
    )
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    state = build_simulation_state(mesh, config)

    assert state is not None
    assert state.mode == "passive"
    assert state.velocity_field is not None
    assert set(state.fields) == {"smoke"}


def test_build_simulation_state_is_solved_mode_for_a_declared_solved_field() -> None:
    config = PyFlowConfig(
        mesh=_MESH_CONFIG,
        fields=[FieldConfig(name="smoke", initial_condition="gaussian_blob")],
        simulation=SimulationConfig(velocity_solved=True),
    )
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    state = build_simulation_state(mesh, config)

    assert state is not None
    assert state.mode == "solved"
    assert state.velocity_field is None
    assert set(state.fields) == {"smoke", "velocity.0", "velocity.1"}


def test_build_simulation_state_is_solved_mode_for_velocity_only() -> None:
    config = PyFlowConfig(mesh=_MESH_CONFIG, simulation=SimulationConfig(velocity_solved=True))
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    state = build_simulation_state(mesh, config)

    assert state is not None
    assert state.mode == "solved"
    assert set(state.fields) == {"velocity.0", "velocity.1"}


def test_advance_simulation_state_passive_mode_advances_declared_field() -> None:
    config = PyFlowConfig(
        mesh=_MESH_CONFIG, fields=[FieldConfig(name="smoke", initial_condition="gaussian_blob")]
    )
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    numerics = assemble_numerics(
        config.numerics, config.fluid.diffusion_coefficient, {}, (0, 0), {}
    )
    state = build_simulation_state(mesh, config)
    assert state is not None
    before = state.fields["smoke"].values.clone()  # type: ignore[attr-defined]

    advanced = advance_simulation_state(state, numerics, config.numerics.timestep)

    assert advanced.mode == "passive"
    after = advanced.fields["smoke"].values  # type: ignore[attr-defined]
    assert not before.equal(after)


def test_velocity_field_from_state_reassembles_the_named_vector_field() -> None:
    config = PyFlowConfig(mesh=_MESH_CONFIG, simulation=SimulationConfig(velocity_solved=True))
    mesh = StructuredCartesianMesh.from_config(config.mesh)
    state = build_simulation_state(mesh, config)
    assert state is not None

    velocity = velocity_field_from_state(state)

    assert velocity.name == "velocity"
    assert velocity.mesh is mesh


# -- Timestep stability warning (TASK-054, Stage 9) --------------------------
#
# Stage 9 Completion Criterion 5. `stable_timestep` has existed since
# TASK-034 and no live path called it -- a gap Stage 5's own Criterion 12
# verdict noted and filed rather than fixed. Measured by refining the
# shipped cavity and leaving `numerics.timestep` alone: at 64x64 the
# configured 0.008 is 2.05x the derived limit and the run diverges at
# step 17, silently, with nothing said beforehand.

_CAVITY_VISCOSITY = 0.01


def _cavity_config(cells: int, timestep: float) -> PyFlowConfig:
    """The shipped lid-driven cavity's own shape at a chosen resolution --
    a unit square, so `cells` alone sets both the mesh and the spacing.
    """
    return PyFlowConfig(
        mesh=MeshConfig(
            origin=(0.0, 0.0), spacing=(1.0 / cells, 1.0 / cells), extent=(cells, cells)
        ),
        numerics=NumericsConfig(
            timestep=timestep,
            boundary_conditions=BoundaryConditionsConfig(
                north=BoundaryFaceConfig(
                    type="dirichlet", field_values={"velocity.0": 1.0, "velocity.1": 0.0}
                ),
                south=BoundaryFaceConfig(type="dirichlet"),
                east=BoundaryFaceConfig(type="dirichlet"),
                west=BoundaryFaceConfig(type="dirichlet"),
            ),
        ),
        simulation=SimulationConfig(velocity_solved=True),
        fluid=FluidConfig(viscosity=_CAVITY_VISCOSITY),
    )


def test_a_timestep_above_the_stability_limit_is_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # 64x64 with the shipped 0.008: measured at 2.05x the derived limit,
    # and the resolution at which a real run diverges (at step 17).
    config = _cavity_config(cells=64, timestep=0.008)
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    with caplog.at_level(logging.WARNING, logger="pyflow.simulation_run"):
        build_simulation_state(mesh, config)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings, "expected a stability warning at 2.05x the derived limit"
    message = warnings[0].getMessage()
    # All three numbers, per the criterion: a warning that says only
    # "unstable" tells a user nothing they can act on.
    assert "0.008" in message, message
    assert "0.0039" in message, message
    assert "2.0" in message, message


def test_a_timestep_below_the_stability_limit_is_not_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The other half of the claim, and its own case: a warning that always
    # fires is a warning nobody reads. 16x16 with the same 0.008 is 0.51x
    # the limit -- the shipped demo's own configuration, which must stay
    # silent.
    config = _cavity_config(cells=16, timestep=0.008)
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    with caplog.at_level(logging.WARNING, logger="pyflow.simulation_run"):
        build_simulation_state(mesh, config)

    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_the_warning_is_not_fatal(caplog: pytest.LogCaptureFixture) -> None:
    config = _cavity_config(cells=64, timestep=0.008)
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    with caplog.at_level(logging.WARNING, logger="pyflow.simulation_run"):
        state = build_simulation_state(mesh, config)

    # The run proceeds: `_STABILITY_SAFETY_FACTOR` is deliberately
    # conservative (0.25 against a measured stable edge of 0.3), so a
    # configured timestep over the derived limit is not automatically
    # unstable -- 32x32 and 48x48 demonstrably run.
    assert state is not None
    assert state.mode == "solved"


def test_a_configuration_with_nothing_to_run_reports_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # `build_simulation_state` returns `None` when a config declares
    # nothing that changes frame to frame. There is no timestep to warn
    # about in that case, and warning anyway would fire on every
    # render-only demo (Empty Mesh, Field Display).
    config = PyFlowConfig(
        mesh=MeshConfig(origin=(0.0, 0.0), spacing=(0.01, 0.01), extent=(64, 64)),
        numerics=NumericsConfig(timestep=10.0),
    )
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    with caplog.at_level(logging.WARNING, logger="pyflow.simulation_run"):
        assert build_simulation_state(mesh, config) is None

    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_a_declared_scalars_wall_value_is_not_read_as_a_speed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`field_values` is keyed by field name and carries a declared
    scalar's own wall value alongside any velocity component's.

    **Added because mutation testing found the filter untested.**
    Replacing `_characteristic_velocity`'s own `name.startswith(
    "velocity.")` with an unconditional `True` left all of the tests
    above passing -- so nothing held the one line that stops a
    temperature of 300 being read as a speed of 300, which would shrink
    the CFL limit by two orders of magnitude and make this warning fire
    on configurations that are perfectly stable. The same shape of
    conflation TASK-052 fixed one layer down.
    """
    config = PyFlowConfig(
        mesh=MeshConfig(origin=(0.0, 0.0), spacing=(0.0625, 0.0625), extent=(16, 16)),
        numerics=NumericsConfig(
            timestep=0.008,
            boundary_conditions=BoundaryConditionsConfig(
                north=BoundaryFaceConfig(type="dirichlet", field_values={"temperature": 300.0}),
                south=BoundaryFaceConfig(type="dirichlet", field_values={"temperature": 300.0}),
                east=BoundaryFaceConfig(type="dirichlet", field_values={"temperature": 300.0}),
                west=BoundaryFaceConfig(type="dirichlet", field_values={"temperature": 300.0}),
            ),
        ),
        fields=[FieldConfig(name="temperature", diffusion_coefficient=0.01)],
        fluid=FluidConfig(viscosity=_CAVITY_VISCOSITY),
    )
    mesh = StructuredCartesianMesh.from_config(config.mesh)

    # Same mesh and timestep as the shipped cavity, which is 0.51x the
    # limit and silent. Read as a speed, 300 would put the CFL limit at
    # dx/300 and this would warn.
    with caplog.at_level(logging.WARNING, logger="pyflow.simulation_run"):
        build_simulation_state(mesh, config)

    assert [r for r in caplog.records if r.levelno == logging.WARNING] == [], (
        "a declared scalar's wall value must not be read as a flow speed"
    )
