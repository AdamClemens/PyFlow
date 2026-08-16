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
