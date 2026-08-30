"""Loads a `PyFlowConfig` from a YAML file, or returns defaults.

Deliberately simple, per TASK-005 ("keep the implementation intentionally
simple"): no schema-inference library, no partial-merge-with-defaults
logic beyond what dataclass field defaults already give for free. A
config file only needs to state the fields it wants to override.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml

from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    FieldConfig,
    FieldDisplayConfig,
    FluidConfig,
    LoggingConfig,
    MeshConfig,
    NumericsConfig,
    PyFlowConfig,
    RenderingConfig,
    SimulationConfig,
)

_BOUNDARY_NAMES = ("north", "south", "east", "west")


def _boundary_conditions_config_from_raw(raw: object) -> BoundaryConditionsConfig:
    if not isinstance(raw, dict):
        raise TypeError(f"boundary_conditions must be a mapping, got {type(raw).__name__}")
    unknown = set(raw) - set(_BOUNDARY_NAMES)
    if unknown:
        raise ValueError(f"unknown boundary_conditions section(s): {sorted(unknown)}")
    faces = {}
    for name in _BOUNDARY_NAMES:
        face_raw = raw.get(name, {})
        if not isinstance(face_raw, dict):
            raise TypeError(
                f"boundary_conditions.{name} must be a mapping, got {type(face_raw).__name__}"
            )
        faces[name] = BoundaryFaceConfig(**face_raw)
    return BoundaryConditionsConfig(**faces)


def _numerics_config_from_raw(raw: dict[str, Any]) -> NumericsConfig:
    raw = dict(raw)
    if "diffusion_coefficient" in raw:
        raise ValueError(
            "numerics.diffusion_coefficient has moved to fluid.diffusion_coefficient "
            "(TASK-041) -- update your configuration file"
        )
    boundary_conditions_raw = raw.pop("boundary_conditions", {})
    return NumericsConfig(
        boundary_conditions=_boundary_conditions_config_from_raw(boundary_conditions_raw),
        **raw,
    )


def _simulation_config_from_raw(raw: dict[str, Any]) -> SimulationConfig:
    if "scalar_pattern" in raw:
        raise ValueError(
            "simulation.scalar_pattern has moved to the top-level fields: section "
            "(TASK-042) -- update your configuration file"
        )
    return SimulationConfig(**raw)


def _fields_from_raw(raw: object) -> list[FieldConfig]:
    if not isinstance(raw, list):
        raise TypeError(f"fields must be a list, got {type(raw).__name__}")
    declared = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TypeError(f"fields[{index}] must be a mapping, got {type(item).__name__}")
        declared.append(FieldConfig(**item))
    return declared


def load_config(path: str | Path | None = None) -> PyFlowConfig:
    """Load configuration from `path`, or return all-defaults if `path` is None.

    Raises `FileNotFoundError` if `path` is given but doesn't exist,
    `ValueError` if the file's structure or values are invalid. Every
    such `ValueError` names the file and the offending field -- see the
    `except` clause below for why that needs saying.
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

    # Derived from `PyFlowConfig`'s own fields, not restated (P-011):
    # adding a section to the schema should not also require editing a
    # list here for the loader to accept it.
    known_sections = {section.name for section in dataclasses.fields(PyFlowConfig)}
    unknown = set(raw) - known_sections
    if unknown:
        raise ValueError(f"{path}: unknown config section(s): {sorted(unknown)}")

    # `validate()` is inside this `try`, not after it. It used to sit
    # outside, on the assumption that construction was the only step that
    # could fail on malformed input -- but a wrong-typed scalar survives
    # construction and blows up in a comparison instead, so
    # `width: "wide"` escaped as a raw `TypeError` that this function's
    # own docstring said it wouldn't raise (found 2026-08-21). Catching
    # both here also means the file's name is attached to *every*
    # failure, including the hand-written checks in `schema.py`, which
    # name their field but have no idea which file it came from.
    try:
        config = PyFlowConfig(
            logging=LoggingConfig(**raw.get("logging", {})),
            rendering=RenderingConfig(**raw.get("rendering", {})),
            mesh=MeshConfig(**raw.get("mesh", {})),
            field_display=FieldDisplayConfig(**raw.get("field_display", {})),
            fields=_fields_from_raw(raw.get("fields", [])),
            simulation=_simulation_config_from_raw(raw.get("simulation", {})),
            fluid=FluidConfig(**raw.get("fluid", {})),
            numerics=_numerics_config_from_raw(raw.get("numerics", {})),
        )
        config.validate()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}: {exc}") from exc

    return config
