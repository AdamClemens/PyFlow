"""Unit tests for pyflow.configuration (TASK-005)."""

from pathlib import Path

import pytest

from pyflow.configuration import PyFlowConfig, load_config


def test_defaults_are_valid() -> None:
    config = PyFlowConfig()
    config.validate()
    assert config.logging.level == "INFO"
    assert config.rendering.backend == "glfw"
    assert config.rendering.width == 1280
    assert config.rendering.height == 720
    assert config.rendering.background_color is None
    assert config.rendering.grid_color is None
    assert config.rendering.zoom == 1.0
    assert config.rendering.pan == (0.0, 0.0)
    assert config.rendering.zoom_min == 0.1
    assert config.rendering.zoom_max == 10.0
    assert config.mesh.origin == (0.0, 0.0)
    assert config.mesh.spacing == (1.0, 1.0)
    assert config.mesh.extent == (10, 10)


def test_load_config_with_no_path_returns_defaults() -> None:
    assert load_config(None) == PyFlowConfig()


def test_load_config_reads_partial_overrides(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  width: 640\n")

    config = load_config(config_file)

    assert config.rendering.backend == "offscreen"
    assert config.rendering.width == 640
    assert config.rendering.height == 720  # untouched default
    assert config.logging.level == "INFO"  # untouched default


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "does-not-exist.yaml")


def test_load_config_empty_file_returns_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    assert load_config(config_file) == PyFlowConfig()


def test_load_config_rejects_non_mapping(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("- just\n- a\n- list\n")

    with pytest.raises(ValueError, match="top-level YAML must be a mapping"):
        load_config(config_file)


def test_load_config_rejects_unknown_section(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("physics:\n  gravity: 9.81\n")

    with pytest.raises(ValueError, match="unknown config section"):
        load_config(config_file)


def test_load_config_rejects_unknown_field(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  fullscreen: true\n")

    with pytest.raises(ValueError):
        load_config(config_file)


def test_load_config_rejects_invalid_backend(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: vulkan-direct\n")

    with pytest.raises(ValueError, match="rendering.backend"):
        load_config(config_file)


def test_load_config_rejects_non_positive_dimensions(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  width: 0\n")

    with pytest.raises(ValueError, match="positive"):
        load_config(config_file)


def test_load_config_rejects_invalid_log_level(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("logging:\n  level: VERBOSE\n")

    with pytest.raises(ValueError, match="logging.level"):
        load_config(config_file)


def test_load_config_reads_background_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  background_color: '#1a1a2e'\n")

    assert load_config(config_file).rendering.background_color == "#1a1a2e"


def test_load_config_rejects_invalid_background_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  background_color: not-a-color\n")

    with pytest.raises(ValueError, match="background_color"):
        load_config(config_file)


def test_load_config_reads_grid_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  grid_color: '#4477aa'\n")

    assert load_config(config_file).rendering.grid_color == "#4477aa"


def test_load_config_rejects_invalid_grid_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  grid_color: not-a-color\n")

    with pytest.raises(ValueError, match="grid_color"):
        load_config(config_file)


def test_load_config_reads_zoom_and_pan(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  zoom: 2.0\n  pan: [1.5, -0.5]\n")

    config = load_config(config_file)

    assert config.rendering.zoom == 2.0
    assert config.rendering.pan == (1.5, -0.5)
    assert isinstance(config.rendering.pan, tuple)


def test_load_config_rejects_non_positive_zoom(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  zoom: 0.0\n")

    with pytest.raises(ValueError, match="rendering.zoom"):
        load_config(config_file)


def test_load_config_rejects_non_positive_zoom_min(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  zoom_min: 0.0\n")

    with pytest.raises(ValueError, match="rendering.zoom_min must be positive"):
        load_config(config_file)


def test_load_config_rejects_zoom_bounds_out_of_order(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  zoom_min: 5.0\n  zoom_max: 1.0\n")

    with pytest.raises(ValueError, match="zoom_min"):
        load_config(config_file)


def test_load_config_rejects_zoom_outside_its_own_bounds(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  zoom: 20.0\n  zoom_max: 10.0\n")

    with pytest.raises(ValueError, match="zoom_max"):
        load_config(config_file)


def test_load_config_reads_mesh_section(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "mesh:\n  origin: [1.5, -2.25]\n  spacing: [0.1, 0.3]\n  extent: [4, 3]\n"
    )

    config = load_config(config_file)

    # YAML parses [1.5, -2.25] as a list; MeshConfig must normalise it to
    # a tuple, both so equality with a hand-built PyFlowConfig() default
    # works and so downstream code can rely on the declared tuple type.
    assert config.mesh.origin == (1.5, -2.25)
    assert isinstance(config.mesh.origin, tuple)
    assert config.mesh.spacing == (0.1, 0.3)
    assert config.mesh.extent == (4, 3)


def test_load_config_rejects_non_positive_spacing(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mesh:\n  spacing: [0.0, 1.0]\n")

    with pytest.raises(ValueError, match="mesh.spacing"):
        load_config(config_file)


def test_load_config_rejects_non_positive_extent(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mesh:\n  extent: [0, 10]\n")

    with pytest.raises(ValueError, match="mesh.extent"):
        load_config(config_file)
