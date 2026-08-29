"""Unit tests for pyflow.bootstrap (in-process, offscreen backend).

Complements `tests/integration/test_bootstrap.py`, which verifies the
real `python -m pyflow run` subprocess; this calls `bootstrap()` directly
so pytest-cov can actually measure it -- subprocess execution isn't
tracked, which is why `bootstrap.py` showed 0% coverage despite the
integration test genuinely running it.
"""

from pathlib import Path

import pygfx as gfx
import torch

from pyflow.bootstrap import bootstrap
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


def test_bootstrap_applies_configured_zoom_regardless_of_grid(tmp_path: Path) -> None:
    """`apply_camera_config` runs unconditionally -- zoom/pan aren't
    mesh-specific, so they shouldn't require the mesh to be shown.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  zoom: 2.0\n")

    window = bootstrap(config_file, max_frames=1)

    assert window.camera.zoom == 2.0


def test_bootstrap_without_show_mesh_adds_no_mesh_grid(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n")

    window = bootstrap(config_file, max_frames=1)

    assert not any(isinstance(child, gfx.Line) for child in window.scene.children)


def test_bootstrap_with_show_mesh_adds_a_mesh_grid_line(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_mesh: true\nmesh:\n  extent: [4, 3]\n"
    )

    window = bootstrap(config_file, max_frames=1)

    grid_lines = [child for child in window.scene.children if isinstance(child, gfx.Line)]
    assert len(grid_lines) == 1
    # 4x3 mesh: (4+1)*3 vertical + 4*(3+1) horizontal = 15 + 16 = 31 faces.
    assert grid_lines[0].geometry.positions.data.shape == (31 * 2, 3)


def test_show_mesh_is_what_decides_and_grid_colour_is_only_a_colour(tmp_path: Path) -> None:
    """The toggle and the colour are independent (2026-08-21 audit).
    `grid_color` used to be both: setting a colour was the only way to
    ask for a mesh, and there was no way to ask for one in the default
    colour. Asking for the mesh without naming a colour must work, and
    naming a colour without asking for the mesh must not smuggle one in.
    """
    shown = tmp_path / "shown.yaml"
    shown.write_text("rendering:\n  backend: offscreen\n  show_mesh: true\n")
    coloured_only = tmp_path / "coloured_only.yaml"
    coloured_only.write_text("rendering:\n  backend: offscreen\n  grid_color: '#ff0000'\n")

    with_mesh = bootstrap(shown, max_frames=1)
    without_mesh = bootstrap(coloured_only, max_frames=1)

    assert any(isinstance(child, gfx.Line) for child in with_mesh.scene.children)
    assert not any(isinstance(child, gfx.Line) for child in without_mesh.scene.children)


def test_bootstrap_loads_config_and_runs_headless(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  width: 64\n  height: 64\n")

    window = bootstrap(config_file, max_frames=2)

    assert window.frame_count == 2
    assert window.canvas.get_closed()


def test_bootstrap_with_vector_pattern_only_adds_no_scalar_field_mesh(tmp_path: Path) -> None:
    """Every combination of scalar/vector pattern is independently
    switchable -- vector alone must not implicitly turn the scalar
    display on, or vice versa (covered separately by
    `tests/golden/test_field_display.py`, which uses both together).
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\nfield_display:\n  vector_pattern: rotational\n"
    )

    window = bootstrap(config_file, max_frames=1)

    assert not any(isinstance(child, gfx.Mesh) for child in window.scene.children)
    assert any(isinstance(child, gfx.Line) for child in window.scene.children)


def test_bootstrap_scalar_pattern_with_legend_disabled_adds_no_legend(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "field_display:\n  scalar_pattern: radial_gradient\n  show_legend: false\n"
    )

    window = bootstrap(config_file, max_frames=1)

    meshes = [child for child in window.scene.children if isinstance(child, gfx.Mesh)]
    # Exactly one Mesh (the field fill itself) -- a legend would be a
    # second one.
    assert len(meshes) == 1


def test_bootstrap_vector_pattern_with_an_entirely_zero_field_adds_no_arrows(
    tmp_path: Path,
) -> None:
    """A single-cell mesh centred exactly on itself: the rotational
    pattern's one vector is `(0, 0)`, so `build_vector_field_arrows`
    returns `None` and nothing should be added for it.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "mesh:\n  origin: [0.0, 0.0]\n  extent: [1, 1]\n  spacing: [1.0, 1.0]\n"
        "field_display:\n  vector_pattern: rotational\n"
    )

    window = bootstrap(config_file, max_frames=1)

    assert not any(isinstance(child, gfx.Line) for child in window.scene.children)


def test_bootstrap_with_velocity_solved_advances_velocitys_own_components(
    tmp_path: Path,
) -> None:
    """`simulation.velocity_solved` (TASK-031, 2026-08-29): velocity's
    own two components join the live loop's own `state` alongside the
    transported scalar, and change frame over frame -- proving the real
    `bootstrap()` path actually decomposes/steps/reassembles, not only
    `simulation.step()` called directly
    (`tests/features/velocity_field_support.feature`).
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "simulation:\n"
        "  scalar_pattern: gaussian_blob\n"
        "  velocity_pattern: uniform\n"
        "  velocity: [1.0, 0.0]\n"
        "  velocity_solved: true\n"
    )

    window = bootstrap(config_file, max_frames=1)
    assert window.simulation_fields is not None
    u_name = VectorField.component_name("velocity", 0)
    v_name = VectorField.component_name("velocity", 1)
    early_u = window.simulation_fields[u_name]
    assert isinstance(early_u, ScalarField)
    early_values = early_u.values.clone()

    later_window = bootstrap(config_file, max_frames=50)
    assert later_window.simulation_fields is not None
    later_u = later_window.simulation_fields[u_name]
    assert v_name in later_window.simulation_fields
    assert isinstance(later_u, ScalarField)
    assert not torch.equal(early_values, later_u.values)


def test_bootstrap_backend_override(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: glfw\n"
    )  # would open a real window if not overridden

    window = bootstrap(config_file, max_frames=1, backend="offscreen")

    assert window.canvas.get_closed()
