"""Unit tests for pyflow.configuration.generator (TASK-039).

Pure in-process calls, `tmp_path` for the round-trip fixture files --
same scope as `test_configuration.py`, per `tests/unit/CLAUDE.md`.
"""

from pathlib import Path

import yaml

from pyflow.configuration import (
    LoggingConfig,
    MeshConfig,
    PyFlowConfig,
    RenderingConfig,
    load_config,
)
from pyflow.configuration.generator import generate_config_yaml
from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    NumericsConfig,
)


def test_default_round_trip(tmp_path: Path) -> None:
    """`generate_config_yaml(PyFlowConfig())`, fed back through
    `load_config` with no edits, must reproduce `PyFlowConfig()` exactly
    -- the actual claim this task makes, not just "it produced some
    YAML".
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(generate_config_yaml(PyFlowConfig()))

    assert load_config(config_file) == PyFlowConfig()


def test_no_argument_defaults_to_pyflowconfig_defaults(tmp_path: Path) -> None:
    """`generate_config_yaml()` with no argument must behave exactly like
    passing `PyFlowConfig()` explicitly -- the documented default.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(generate_config_yaml())

    assert load_config(config_file) == PyFlowConfig()


def test_non_default_round_trip_including_tuple_fields(tmp_path: Path) -> None:
    """`logging`/`rendering`/`mesh` fields set to non-default values,
    every value distinct from every other, including two tuple-typed
    fields (`mesh.origin`/`mesh.spacing`/`mesh.extent`, `rendering.pan`).
    `numerics.timestep` (TASK-020) and `numerics.linear_solver_tolerance`/
    `numerics.linear_solver_max_iterations` (TASK-022) join them as the
    `numerics` fields with a real non-default value to round-trip --
    `advection`/`diffusion`/`time_integration`/`linear_solver` still have
    only one valid name each (Stage 3 Completion Criterion 1), so there
    is nothing distinct to set them to yet.

    Distinct values matter (`docs/practices.md`'s "distinct factors"
    rule): if the tuple-to-list conversion transposed or dropped a
    component, this fixture would produce a visibly wrong
    `PyFlowConfig` rather than accidentally still comparing equal.
    """
    config = PyFlowConfig(
        logging=LoggingConfig(level="DEBUG"),
        rendering=RenderingConfig(
            backend="offscreen",
            width=321,
            height=417,
            title="Non-Default Title",
            background_color="#112233",
            show_mesh=True,
            grid_color="#aabbcc",
            zoom=2.5,
            pan=(11.1, -22.2),
            zoom_min=0.25,
            zoom_max=8.0,
        ),
        mesh=MeshConfig(
            origin=(3.3, -4.4),
            spacing=(0.7, 1.9),
            extent=(6, 9),
        ),
        numerics=NumericsConfig(
            timestep=0.025,
            linear_solver_tolerance=0.0005,
            linear_solver_max_iterations=250,
        ),
    )

    config_file = tmp_path / "config.yaml"
    config_file.write_text(generate_config_yaml(config))

    assert load_config(config_file) == config


def test_boundary_conditions_round_trip(tmp_path: Path) -> None:
    """`NumericsConfig.boundary_conditions` (TASK-019) is the first
    nested-dataclass-within-a-dataclass field this schema has --
    `asdict()` converts it recursively without extra code, but nothing
    else exercises `loader.py`'s own matching reconstruction
    (`_numerics_config_from_raw`/`_boundary_conditions_config_from_raw`)
    against real, non-default, distinct-per-boundary values.
    """
    config = PyFlowConfig(
        numerics=NumericsConfig(
            boundary_conditions=BoundaryConditionsConfig(
                north=BoundaryFaceConfig(type="periodic", velocity=None, pressure=None),
                south=BoundaryFaceConfig(type="periodic", velocity=None, pressure=None),
                east=BoundaryFaceConfig(type="dirichlet", velocity=None, pressure=2.5),
                west=BoundaryFaceConfig(type="neumann", velocity=-3.5, pressure=None),
            )
        )
    )

    config_file = tmp_path / "config.yaml"
    config_file.write_text(generate_config_yaml(config))

    assert load_config(config_file) == config


def test_tuple_fields_are_written_as_plain_yaml_lists(tmp_path: Path) -> None:
    """`yaml.safe_dump` has no representer for a bare Python `tuple`
    (`SafeDumper` excludes the `!!python/tuple` tag the full `Dumper`
    would use) -- proves the generator's own recursive conversion runs,
    rather than relying on the round-trip test's success to imply it.
    """
    config = PyFlowConfig(mesh=MeshConfig(origin=(1.5, -2.5)))

    text = generate_config_yaml(config)

    assert "!!python/tuple" not in text
    parsed = yaml.safe_load(text)
    assert parsed["mesh"]["origin"] == [1.5, -2.5]
    assert isinstance(parsed["mesh"]["origin"], list)


def test_top_level_key_order_matches_pyflowconfig_field_order() -> None:
    """`sort_keys=False` alone doesn't prove the order matches the
    schema's own declared field order -- it only proves the dict
    iteration order was preserved. Check the parsed keys directly
    against `PyFlowConfig`'s declared order (`logging`, `rendering`,
    `mesh`, `field_display`, `fields`, `simulation`, `fluid`, `numerics`),
    not assumed from the dumper flag.
    """
    text = generate_config_yaml(PyFlowConfig())

    parsed = yaml.safe_load(text)

    assert list(parsed.keys()) == [
        "logging",
        "rendering",
        "mesh",
        "field_display",
        "fields",
        "simulation",
        "fluid",
        "numerics",
    ]
