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
    assert config.rendering.show_mesh is False
    assert config.rendering.grid_color == "#4477aa"
    assert config.rendering.zoom == 1.0
    assert config.rendering.pan == (0.0, 0.0)
    assert config.rendering.zoom_min == 0.1
    assert config.rendering.zoom_max == 10.0
    assert config.mesh.origin == (0.0, 0.0)
    assert config.mesh.spacing == (1.0, 1.0)
    assert config.mesh.extent == (10, 10)
    assert config.field_display.scalar_pattern is None
    assert config.field_display.vector_pattern is None
    assert config.field_display.low_color == "#0000ff"
    assert config.field_display.high_color == "#ff0000"
    assert config.field_display.value_range == (0.0, 1.0)
    assert config.field_display.arrow_color == "#ffffff"
    assert config.field_display.arrow_scale == 0.3
    assert config.field_display.show_legend is True
    assert config.numerics.advection == "first_order_upwind"
    assert config.numerics.diffusion == "central_difference"
    assert config.numerics.diffusion_coefficient == 1.0
    assert config.numerics.time_integration == "rk4"
    assert config.numerics.timestep == 0.01
    assert config.numerics.linear_solver == "conjugate_gradient"
    assert config.numerics.linear_solver_tolerance == 1e-6
    assert config.numerics.linear_solver_max_iterations == 1000
    assert config.numerics.pressure_coupling == "piso"
    for boundary_name in ("north", "south", "east", "west"):
        face = getattr(config.numerics.boundary_conditions, boundary_name)
        assert face.type == "dirichlet"
        assert face.velocity == 0.0
        assert face.pressure is None
        assert face.scalar_value == 0.0


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


# -- Malformed-input handling (2026-08-21 audit) -------------------------
#
# Every message a user sees for a bad config file should name the file
# and the field, the way the hand-written checks above already do
# ("mesh.spacing must be positive, got dx=..."). Three inputs did not:
# a wrong-typed scalar escaped as a raw `TypeError` from `validate()`,
# which runs *outside* the loader's `try`; a wrong-length sequence
# escaped as Python's own unpacking message with no file and no field;
# and a non-integer extent was silently truncated instead of rejected.


def test_load_config_rejects_a_wrong_typed_scalar_with_context(tmp_path: Path) -> None:
    """`width: "wide"` previously raised, uncaught, from `validate()`:
    `TypeError: '<=' not supported between instances of 'str' and 'int'`
    -- no file, no field, and not even the `ValueError` `load_config`
    documents itself as raising.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text('rendering:\n  width: "wide"\n')

    with pytest.raises(ValueError, match=r"config\.yaml.*rendering\.width"):
        load_config(config_file)


def test_load_config_rejects_a_wrong_length_pair_with_context(tmp_path: Path) -> None:
    """`origin: [1.0, 2.0, 3.0]` previously raised `ValueError: too many
    values to unpack (expected 2, got 3)` -- technically the documented
    exception type, but naming neither the file nor `mesh.origin`.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mesh:\n  origin: [1.0, 2.0, 3.0]\n")

    with pytest.raises(ValueError, match=r"config\.yaml.*mesh\.origin"):
        load_config(config_file)


def test_load_config_rejects_a_non_integer_extent(tmp_path: Path) -> None:
    """`extent: [10.9, 3.99]` previously became `(10, 3)` silently --
    the user gets a different mesh than they asked for, with nothing
    printed. A cell count is not a quantity to round on the user's
    behalf.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mesh:\n  extent: [10.9, 3.99]\n")

    with pytest.raises(ValueError, match=r"mesh\.extent.*whole number"):
        load_config(config_file)


def test_load_config_accepts_an_integer_valued_float_extent(tmp_path: Path) -> None:
    """`10.0` is a whole number written as a float -- YAML makes that
    easy to do by accident, and it is unambiguous, so it is accepted.
    Only a genuinely fractional cell count is an error.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mesh:\n  extent: [10.0, 4.0]\n")

    assert load_config(config_file).mesh.extent == (10, 4)


def test_load_config_rejects_a_non_numeric_pair_member(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mesh:\n  spacing: [1.0, wide]\n")

    with pytest.raises(ValueError, match=r"mesh\.spacing"):
        load_config(config_file)


def test_load_config_rejects_a_wrong_length_pan(tmp_path: Path) -> None:
    """`RenderingConfig.pan` unpacks in `__post_init__` exactly like
    `MeshConfig`'s pairs do, and had the same gap.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  pan: [1.0]\n")

    with pytest.raises(ValueError, match=r"rendering\.pan"):
        load_config(config_file)


def test_every_config_error_names_the_file(tmp_path: Path) -> None:
    """The loader's own contract: whatever goes wrong in a config file,
    the message says which file. Covers the hand-written validators too,
    which previously reported the field but not the path.
    """
    config_file = tmp_path / "broken.yaml"
    for text in (
        "rendering:\n  width: 0\n",
        "logging:\n  level: LOUD\n",
        "mesh:\n  spacing: [0.0, 1.0]\n",
        "rendering:\n  zoom: -1.0\n",
    ):
        config_file.write_text(text)
        with pytest.raises(ValueError, match="broken.yaml"):
            load_config(config_file)


# -- FieldDisplayConfig (TASK-017) ---------------------------------------


def test_load_config_reads_field_display_section(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "field_display:\n"
        "  scalar_pattern: radial_gradient\n"
        "  vector_pattern: rotational\n"
        "  low_color: '#0a141e'\n"
        "  high_color: '#c89664'\n"
        "  value_range: [0.0, 5.0]\n"
        "  arrow_color: '#00ff00'\n"
        "  arrow_scale: 0.5\n"
        "  show_legend: false\n"
    )

    config = load_config(config_file)

    assert config.field_display.scalar_pattern == "radial_gradient"
    assert config.field_display.vector_pattern == "rotational"
    assert config.field_display.low_color == "#0a141e"
    assert config.field_display.high_color == "#c89664"
    assert config.field_display.value_range == (0.0, 5.0)
    assert isinstance(config.field_display.value_range, tuple)
    assert config.field_display.arrow_color == "#00ff00"
    assert config.field_display.arrow_scale == 0.5
    assert config.field_display.show_legend is False


def test_load_config_rejects_an_unknown_scalar_pattern(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  scalar_pattern: checkerboard\n")

    with pytest.raises(ValueError, match="scalar_pattern"):
        load_config(config_file)


def test_load_config_rejects_an_unknown_vector_pattern(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  vector_pattern: spiral\n")

    with pytest.raises(ValueError, match="vector_pattern"):
        load_config(config_file)


def test_load_config_rejects_an_invalid_low_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  low_color: not-a-color\n")

    with pytest.raises(ValueError, match="low_color"):
        load_config(config_file)


def test_load_config_rejects_an_invalid_high_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  high_color: not-a-color\n")

    with pytest.raises(ValueError, match="high_color"):
        load_config(config_file)


def test_load_config_rejects_an_invalid_arrow_color(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  arrow_color: not-a-color\n")

    with pytest.raises(ValueError, match="arrow_color"):
        load_config(config_file)


def test_load_config_rejects_a_degenerate_value_range(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  value_range: [5.0, 5.0]\n")

    with pytest.raises(ValueError, match="value_range"):
        load_config(config_file)


def test_load_config_rejects_an_inverted_value_range(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  value_range: [5.0, 1.0]\n")

    with pytest.raises(ValueError, match="value_range"):
        load_config(config_file)


def test_load_config_rejects_a_non_positive_arrow_scale(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  arrow_scale: 0.0\n")

    with pytest.raises(ValueError, match="arrow_scale"):
        load_config(config_file)


def test_load_config_rejects_a_non_boolean_show_legend(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("field_display:\n  show_legend: maybe\n")

    with pytest.raises(ValueError, match="show_legend"):
        load_config(config_file)


@pytest.mark.parametrize(
    ("yaml_text", "expected"),
    [
        # `_number_pair`: not a sequence at all, and a string (which *is* a
        # sequence, and would otherwise unpack into two characters).
        ("mesh:\n  origin: 5\n", "mesh.origin"),
        ("mesh:\n  origin: xy\n", "mesh.origin"),
        # `_number_pair`: non-finite. `.inf` survives `dx <= 0`, so without
        # this it would reach the mesh as a real spacing.
        ("mesh:\n  spacing: [.inf, 1.0]\n", "mesh.spacing"),
        # `_require_number` / `_require_str` / the `show_mesh` check.
        ("rendering:\n  zoom: high\n", "rendering.zoom"),
        ("rendering:\n  zoom: .nan\n", "rendering.zoom"),
        ("rendering:\n  title: 7\n", "rendering.title"),
        ("rendering:\n  grid_color: 7\n", "rendering.grid_color"),
        ("rendering:\n  background_color: 7\n", "rendering.background_color"),
        ("rendering:\n  show_mesh: maybe\n", "rendering.show_mesh"),
    ],
)
def test_load_config_rejects_wrong_typed_values(
    yaml_text: str, expected: str, tmp_path: Path
) -> None:
    """One case per guard in `schema.py`'s normalisation helpers.

    YAML types a bare scalar for you, so several of these are things a
    user genuinely writes by accident -- `.inf` and `.nan` are real YAML
    floats, and an unquoted `xy` is a real string where a pair belongs.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_text)

    with pytest.raises(ValueError, match=expected):
        load_config(config_file)


def test_load_config_reads_numerics_section(tmp_path: Path) -> None:
    # Only one valid name exists for each field yet (TASK-018's own
    # share of `NumericsConfig` -- `docs/architecture/icds.md` names
    # exactly one MVP choice per component), so there is no distinct
    # non-default value to assert against here the way
    # `test_load_config_reads_field_display_section` does. This still
    # proves the section is actually read from YAML, not only ever seen
    # at its default.
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n  advection: first_order_upwind\n  diffusion: central_difference\n"
    )

    config = load_config(config_file)

    assert config.numerics.advection == "first_order_upwind"
    assert config.numerics.diffusion == "central_difference"


def test_load_config_rejects_an_unknown_advection_scheme(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  advection: quick\n")

    with pytest.raises(ValueError, match="numerics.advection"):
        load_config(config_file)


def test_load_config_rejects_an_unknown_diffusion_scheme(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  diffusion: quick\n")

    with pytest.raises(ValueError, match="numerics.diffusion"):
        load_config(config_file)


def test_load_config_reads_diffusion_coefficient(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  diffusion_coefficient: 2.5\n")

    config = load_config(config_file)

    assert config.numerics.diffusion_coefficient == 2.5


def test_load_config_rejects_a_non_positive_diffusion_coefficient(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  diffusion_coefficient: 0.0\n")

    with pytest.raises(ValueError, match="numerics.diffusion_coefficient"):
        load_config(config_file)


def test_load_config_rejects_a_negative_diffusion_coefficient(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  diffusion_coefficient: -1.0\n")

    with pytest.raises(ValueError, match="numerics.diffusion_coefficient"):
        load_config(config_file)


def test_load_config_reads_time_integration_section(tmp_path: Path) -> None:
    # Only one valid name exists for `time_integration` yet (same reason
    # as `test_load_config_reads_numerics_section`); `timestep` does have
    # a real non-default value to assert, so this test carries both.
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  time_integration: rk4\n  timestep: 0.05\n")

    config = load_config(config_file)

    assert config.numerics.time_integration == "rk4"
    assert config.numerics.timestep == 0.05


def test_load_config_rejects_an_unknown_time_integration_scheme(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  time_integration: leapfrog\n")

    with pytest.raises(ValueError, match="numerics.time_integration"):
        load_config(config_file)


def test_load_config_rejects_a_non_positive_timestep(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  timestep: 0.0\n")

    with pytest.raises(ValueError, match="numerics.timestep"):
        load_config(config_file)


def test_load_config_rejects_a_negative_timestep(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  timestep: -0.1\n")

    with pytest.raises(ValueError, match="numerics.timestep"):
        load_config(config_file)


def test_load_config_reads_linear_solver_section(tmp_path: Path) -> None:
    # Only one valid name exists for `linear_solver` yet (same reason as
    # `test_load_config_reads_numerics_section`); `linear_solver_tolerance`/
    # `linear_solver_max_iterations` do have real non-default values.
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n"
        "  linear_solver: conjugate_gradient\n"
        "  linear_solver_tolerance: 0.001\n"
        "  linear_solver_max_iterations: 50\n"
    )

    config = load_config(config_file)

    assert config.numerics.linear_solver == "conjugate_gradient"
    assert config.numerics.linear_solver_tolerance == 0.001
    assert config.numerics.linear_solver_max_iterations == 50


def test_load_config_rejects_an_unknown_linear_solver(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  linear_solver: gmres\n")

    with pytest.raises(ValueError, match="numerics.linear_solver"):
        load_config(config_file)


def test_load_config_rejects_a_non_positive_linear_solver_tolerance(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  linear_solver_tolerance: 0.0\n")

    with pytest.raises(ValueError, match="numerics.linear_solver_tolerance"):
        load_config(config_file)


def test_load_config_rejects_a_non_positive_linear_solver_max_iterations(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  linear_solver_max_iterations: 0\n")

    with pytest.raises(ValueError, match="numerics.linear_solver_max_iterations"):
        load_config(config_file)


def test_load_config_reads_pressure_coupling_section(tmp_path: Path) -> None:
    # Only one valid name exists yet (same reason as
    # test_load_config_reads_numerics_section).
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  pressure_coupling: piso\n")

    config = load_config(config_file)

    assert config.numerics.pressure_coupling == "piso"


def test_load_config_rejects_an_unknown_pressure_coupling_strategy(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  pressure_coupling: simple\n")

    with pytest.raises(ValueError, match="numerics.pressure_coupling"):
        load_config(config_file)


def test_load_config_reads_boundary_conditions_section(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n"
        "  boundary_conditions:\n"
        "    north:\n"
        "      type: periodic\n"
        "    south:\n"
        "      type: periodic\n"
        "    east:\n"
        "      type: dirichlet\n"
        "      velocity: null\n"
        "      pressure: 0.0\n"
        "    west:\n"
        "      type: dirichlet\n"
        "      velocity: 2.0\n"
    )

    config = load_config(config_file)

    assert config.numerics.boundary_conditions.north.type == "periodic"
    assert config.numerics.boundary_conditions.south.type == "periodic"
    assert config.numerics.boundary_conditions.east.pressure == 0.0
    assert config.numerics.boundary_conditions.east.velocity is None
    assert config.numerics.boundary_conditions.west.velocity == 2.0


def test_load_config_reads_boundary_condition_scalar_value(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n"
        "  boundary_conditions:\n"
        "    north:\n"
        "      type: dirichlet\n"
        "      scalar_value: 300.0\n"
    )

    config = load_config(config_file)

    assert config.numerics.boundary_conditions.north.scalar_value == 300.0


def test_load_config_rejects_a_non_numeric_boundary_condition_scalar_value(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n  boundary_conditions:\n    north:\n      scalar_value: not-a-number\n"
    )

    with pytest.raises(ValueError, match="numerics.boundary_conditions.north.scalar_value"):
        load_config(config_file)


def test_load_config_rejects_an_unknown_boundary_condition_type(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  boundary_conditions:\n    north:\n      type: robin\n")

    with pytest.raises(ValueError, match="numerics.boundary_conditions.north.type"):
        load_config(config_file)


@pytest.mark.parametrize(("periodic_side", "unpaired_side"), [("east", "west"), ("north", "south")])
def test_load_config_rejects_periodic_without_its_paired_boundary(
    periodic_side: str, unpaired_side: str, tmp_path: Path
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"numerics:\n"
        f"  boundary_conditions:\n"
        f"    {periodic_side}:\n"
        f"      type: periodic\n"
        f"      velocity: null\n"
    )

    with pytest.raises(
        ValueError, match=f"{periodic_side}.*{unpaired_side}|{unpaired_side}.*{periodic_side}"
    ):
        load_config(config_file)


def test_load_config_rejects_velocity_and_pressure_both_prescribed_on_one_boundary(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n  boundary_conditions:\n    north:\n      velocity: 1.0\n      pressure: 0.0\n"
    )

    with pytest.raises(ValueError, match="numerics.boundary_conditions.north"):
        load_config(config_file)


def test_load_config_rejects_velocity_on_every_boundary_with_nonzero_net_flux(
    tmp_path: Path,
) -> None:
    # nx=4, ny=2, dx=dy=1: north/south length 4, east/west length 2.
    # Weighted: 1*4 + 0*4 + (-2)*2 + 0*2 = 4 - 4 = 0 -- see the
    # acceptance test below for why this exact fixture matters.
    # Here, break it: west carries -1.0 instead of 0.0 -> weighted
    # net flux is 1*4 + 0*4 + (-2)*2 + (-1)*2 = 4 - 4 - 2 = -2 != 0.
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "mesh:\n"
        "  extent: [4, 2]\n"
        "  spacing: [1.0, 1.0]\n"
        "numerics:\n"
        "  boundary_conditions:\n"
        "    north:\n      velocity: 1.0\n"
        "    south:\n      velocity: 0.0\n"
        "    east:\n      velocity: -2.0\n"
        "    west:\n      velocity: -1.0\n"
    )

    with pytest.raises(ValueError, match="net flux"):
        load_config(config_file)


def test_load_config_accepts_velocity_on_every_boundary_with_zero_weighted_net_flux(
    tmp_path: Path,
) -> None:
    # Distinct boundary lengths (`docs/practices.md`'s "distinct
    # factors" rule): nx=4, ny=2, dx=dy=1 makes north/south length 4,
    # east/west length 2. Raw (unweighted) sum of these four values is
    # 1 + 0 - 2 + 0 = -1, nonzero -- an implementation that summed
    # values without weighting by boundary length would wrongly reject
    # this config. Weighted: 1*4 + 0*4 + (-2)*2 + 0*2 = 4 - 4 = 0,
    # correctly accepted.
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "mesh:\n"
        "  extent: [4, 2]\n"
        "  spacing: [1.0, 1.0]\n"
        "numerics:\n"
        "  boundary_conditions:\n"
        "    north:\n      velocity: 1.0\n"
        "    south:\n      velocity: 0.0\n"
        "    east:\n      velocity: -2.0\n"
        "    west:\n      velocity: 0.0\n"
    )

    config = load_config(config_file)

    assert config.numerics.boundary_conditions.north.velocity == 1.0


def test_load_config_skips_net_flux_check_when_not_all_boundaries_prescribe_velocity(
    tmp_path: Path,
) -> None:
    # Three velocity boundaries with a wildly nonzero sum, one pressure
    # boundary -- accepted, because criterion 7 activates specifically
    # "on all four boundaries", not a partial set (a pressure boundary
    # absorbs any imbalance, per `docs/handbook/numerical-methods/
    # boundary-conditions.md`).
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n"
        "  boundary_conditions:\n"
        "    north:\n      velocity: 100.0\n"
        "    south:\n      velocity: 100.0\n"
        "    east:\n      velocity: 100.0\n"
        "    west:\n      velocity: null\n      pressure: 0.0\n"
    )

    config = load_config(config_file)

    assert config.numerics.boundary_conditions.west.pressure == 0.0


def test_load_config_rejects_a_non_mapping_boundary_conditions_section(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  boundary_conditions: not-a-mapping\n")

    with pytest.raises(ValueError, match="boundary_conditions must be a mapping"):
        load_config(config_file)


def test_load_config_rejects_an_unknown_boundary_name(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "numerics:\n  boundary_conditions:\n    northeast:\n      type: dirichlet\n"
    )

    with pytest.raises(ValueError, match="unknown boundary_conditions section"):
        load_config(config_file)


def test_load_config_rejects_a_non_mapping_boundary_face(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("numerics:\n  boundary_conditions:\n    north: not-a-mapping\n")

    with pytest.raises(ValueError, match="boundary_conditions.north must be a mapping"):
        load_config(config_file)
