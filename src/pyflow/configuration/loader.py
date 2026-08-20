"""Loads a `PyFlowConfig` from a YAML file, or returns defaults.

Deliberately simple, per TASK-005 ("keep the implementation intentionally
simple"): no schema-inference library, no partial-merge-with-defaults
logic beyond what dataclass field defaults already give for free. A
config file only needs to state the fields it wants to override.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from pyflow.configuration.schema import LoggingConfig, MeshConfig, PyFlowConfig, RenderingConfig


def load_config(path: str | Path | None = None) -> PyFlowConfig:
    """Load configuration from `path`, or return all-defaults if `path` is None.

    Raises `FileNotFoundError` if `path` is given but doesn't exist,
    `ValueError` if the file's structure or values are invalid.
    """
    if path is None:
        config = PyFlowConfig()
        config.validate()
        return config

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping, got {type(raw).__name__}")

    known_sections = {"logging", "rendering", "mesh"}
    unknown = set(raw) - known_sections
    if unknown:
        raise ValueError(f"{path}: unknown config section(s): {sorted(unknown)}")

    try:
        config = PyFlowConfig(
            logging=LoggingConfig(**raw.get("logging", {})),
            rendering=RenderingConfig(**raw.get("rendering", {})),
            mesh=MeshConfig(**raw.get("mesh", {})),
        )
    except TypeError as exc:
        raise ValueError(f"{path}: {exc}") from exc

    config.validate()
    return config
