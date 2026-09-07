"""Unit tests for pyflow.simulation_run (TASK-045, Stage 8, Recording &
Playback) -- the simulation-state construction/advance logic extracted
from `bootstrap.py`'s two live-rendering paths so `recording.py`'s
headless one can share it. `tests/unit/test_bootstrap.py` and every
golden-demo/feature scenario touching either live path are this
refactor's own real regression coverage (unmodified, still green); these
tests cover the extracted functions directly, in isolation.
"""

from __future__ import annotations

from pyflow.configuration.schema import FieldConfig, MeshConfig, PyFlowConfig, SimulationConfig
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
