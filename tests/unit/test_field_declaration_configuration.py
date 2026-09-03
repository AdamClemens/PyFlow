"""Binds `tests/features/field_declaration.feature` (TASK-042, Stage 6's
first task). Lives here, not `tests/integration/` or `tests/golden/`,
per that feature file's own header: every scenario is a configuration
loading or failing to load, plus one real end-to-end run and one real
render check, neither needing a rendered frame
(`RenderWindow.last_image`) -- only `bootstrap()`'s own field state and
scene graph, offscreen. No config file lives under
`examples/golden-demos/` for this task, so this is not a golden demo
either. Supplies its own local steps, the same "each binding module is
local" shape every Stage 4/5 module in this directory already
established (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pygfx as gfx
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.configuration import PyFlowConfig, load_config
from pyflow.engine.scalar_field import ScalarField
from pyflow.rendering.window import RenderWindow

scenarios("field_declaration.feature")


@dataclass
class _Context:
    config_path: Path
    alternate_config_path: Path | None = None
    loaded: PyFlowConfig | None = None
    error: ValueError | None = None
    early_window: RenderWindow | None = None
    late_window: RenderWindow | None = None
    alternate_window: RenderWindow | None = None


_FOUR_FIELDS_CONFIG = (
    "rendering:\n  backend: offscreen\n"
    "mesh:\n  extent: [6, 6]\n  spacing: [0.3, 0.3]\n"
    "fields:\n"
    "  - name: alpha\n    initial_condition: gaussian_blob\n    diffusion_coefficient: 0.2\n"
    "  - name: beta\n    initial_condition: sinusoidal_mode\n    diffusion_coefficient: 0.15\n"
    "  - name: gamma\n    initial_condition: gaussian_blob\n    diffusion_coefficient: 0.05\n"
    "  - name: delta\n    initial_condition: sinusoidal_mode\n    diffusion_coefficient: 0.3\n"
)


def _render_field_config(render_field: str) -> str:
    return (
        "rendering:\n  backend: offscreen\n"
        "mesh:\n  extent: [4, 4]\n"
        "fields:\n"
        "  - name: alpha\n    initial_condition: gaussian_blob\n"
        "  - name: beta\n    initial_condition: sinusoidal_mode\n"
        f"field_display:\n  render_field: {render_field}\n"
    )


# -- Given -------------------------------------------------------------


@given(
    "a configuration declaring four named fields, each with its own initial condition "
    "and diffusion coefficient",
    target_fixture="ctx",
)
def _given_four_fields(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(_FOUR_FIELDS_CONFIG)
    return _Context(config_path=config_path)


@given("a configuration file still setting simulation.scalar_pattern", target_fixture="ctx")
def _given_stale_simulation_field(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("simulation:\n  scalar_pattern: gaussian_blob\n")
    return _Context(config_path=config_path)


@given("a configuration file setting field_display.scalar_pattern", target_fixture="ctx")
def _given_field_display_scalar_pattern(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("field_display:\n  scalar_pattern: radial_gradient\n")
    return _Context(config_path=config_path)


@given("a configuration declaring two fields with the same name", target_fixture="ctx")
def _given_duplicate_names(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "fields:\n"
        "  - name: alpha\n    initial_condition: gaussian_blob\n"
        "  - name: alpha\n    initial_condition: sinusoidal_mode\n"
    )
    return _Context(config_path=config_path)


@given("a configuration declaring a field named velocity.0", target_fixture="ctx")
def _given_velocity_component_name(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fields:\n  - name: velocity.0\n    initial_condition: gaussian_blob\n")
    return _Context(config_path=config_path)


@given("a configuration declaring a field named pressure", target_fixture="ctx")
def _given_pressure_name(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fields:\n  - name: pressure\n    initial_condition: gaussian_blob\n")
    return _Context(config_path=config_path)


@given(
    "a configuration declaring a field with a non-positive diffusion coefficient",
    target_fixture="ctx",
)
def _given_non_positive_diffusion_coefficient(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "fields:\n  - name: alpha\n    initial_condition: gaussian_blob\n"
        "    diffusion_coefficient: 0.0\n"
    )
    return _Context(config_path=config_path)


@given(
    "a configuration declaring a field with an unrecognised initial condition",
    target_fixture="ctx",
)
def _given_unrecognised_initial_condition(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("fields:\n  - name: alpha\n    initial_condition: checkerboard\n")
    return _Context(config_path=config_path)


@given(
    "a configuration declaring two named fields and naming one of them as "
    "field_display.render_field",
    target_fixture="ctx",
)
def _given_render_field_selected(tmp_path: Path) -> _Context:
    config_path = tmp_path / "selected.yaml"
    config_path.write_text(_render_field_config("alpha"))
    alternate_path = tmp_path / "alternate.yaml"
    alternate_path.write_text(_render_field_config("beta"))
    return _Context(config_path=config_path, alternate_config_path=alternate_path)


@given(
    "a configuration whose field_display.render_field names a field nothing declares",
    target_fixture="ctx",
)
def _given_undeclared_render_field(tmp_path: Path) -> _Context:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "fields:\n  - name: alpha\n    initial_condition: gaussian_blob\n"
        "field_display:\n  render_field: nowhere\n"
    )
    return _Context(config_path=config_path)


# -- When ----------------------------------------------------------------


@when("the configuration is loaded")
def _when_loaded(ctx: _Context) -> None:
    try:
        ctx.loaded = load_config(ctx.config_path)
    except ValueError as exc:
        ctx.error = exc


@when("the configuration is loaded and run for a few real timesteps")
def _when_loaded_and_run(ctx: _Context) -> None:
    ctx.early_window = bootstrap(ctx.config_path, max_frames=1)
    ctx.late_window = bootstrap(ctx.config_path, max_frames=6)


@when("the configuration is loaded and run for one real timestep")
def _when_loaded_and_run_once(ctx: _Context) -> None:
    ctx.late_window = bootstrap(ctx.config_path, max_frames=1)
    assert ctx.alternate_config_path is not None
    ctx.alternate_window = bootstrap(ctx.alternate_config_path, max_frames=1)


# -- Then ------------------------------------------------------------------


def _scalar(window: RenderWindow, name: str) -> ScalarField:
    assert window.simulation_fields is not None
    field = window.simulation_fields[name]
    assert isinstance(field, ScalarField)
    return field


@then("all four declared fields are present afterward, each changed from its own initial condition")
def _then_four_fields_transported(ctx: _Context) -> None:
    assert ctx.early_window is not None
    assert ctx.late_window is not None
    for name in ("alpha", "beta", "gamma", "delta"):
        early = _scalar(ctx.early_window, name)
        late = _scalar(ctx.late_window, name)
        assert not torch.equal(early.values, late.values), (
            f"expected {name!r} to change after real timesteps, but it did not"
        )


@then(
    "loading is rejected with a named error saying the field moved to the top-level fields section"
)
def _then_rejected_naming_new_home(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the retired field"
    message = str(ctx.error)
    assert "simulation.scalar_pattern" in message
    assert "fields" in message


@then(
    "field_display.scalar_pattern carries the configured value, not rejected as the field "
    "that moved"
)
def _then_field_display_scalar_pattern_untouched(ctx: _Context) -> None:
    assert ctx.loaded is not None, ctx.error
    assert ctx.loaded.field_display.scalar_pattern == "radial_gradient"


@then("loading is rejected with a named error naming the duplicated field")
def _then_rejected_naming_duplicate(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the duplicate name"
    message = str(ctx.error)
    assert "alpha" in message
    assert "more than once" in message


@then("loading is rejected with a named error naming the reserved field name")
def _then_rejected_naming_reserved(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the reserved name"
    assert "reserved" in str(ctx.error)


@then("loading is rejected with a named error naming the field and its diffusion coefficient")
def _then_rejected_naming_diffusion_coefficient(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the non-positive coefficient"
    message = str(ctx.error)
    assert "alpha" in message
    assert "diffusion_coefficient" in message


@then("loading is rejected with a named error naming the field and the valid initial conditions")
def _then_rejected_naming_initial_condition(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the unknown pattern"
    message = str(ctx.error)
    assert "alpha" in message
    assert "initial_condition" in message
    assert "gaussian_blob" in message
    assert "sinusoidal_mode" in message


def _rendered_meshes(window: RenderWindow) -> list[gfx.Mesh]:
    return [child for child in window.scene.children if isinstance(child, gfx.Mesh)]


# The `_render_field_config` mesh is 4x4 = 16 cells, two triangles each --
# distinguishes the field-fill mesh from the legend strip (Stage 7,
# Rendering Annotations, on by default) below by shape, not by scene
# insertion order. Order is not reliable here: `_advance()` (called once
# even at `max_frames=1`, since `RenderWindow._draw` fires `on_frame`
# straight after every render) removes and re-adds the field mesh every
# frame, which moves it *after* the legend -- added once, never
# removed -- in `window.scene.children` from the second render onward.
_FIELD_MESH_TRIANGLE_ROWS = 16 * 2


def _field_fill_mesh(window: RenderWindow) -> gfx.Mesh:
    (mesh,) = [
        m
        for m in _rendered_meshes(window)
        if m.geometry.colors.data.shape[0] == _FIELD_MESH_TRIANGLE_ROWS
    ]
    return mesh


@then("the named field's own colour map is rendered and the other field's is not")
def _then_render_field_selected(ctx: _Context) -> None:
    assert ctx.late_window is not None
    assert ctx.alternate_window is not None
    # Two meshes each since Stage 7 (Rendering Annotations): the field
    # fill and the legend strip (`bootstrap._add_legend`, on by default --
    # `field_display.show_legend` is not set in this scenario's own
    # config). Was exactly one before that stage added a legend to this
    # live-stepping path.
    assert len(_rendered_meshes(ctx.late_window)) == 2
    assert len(_rendered_meshes(ctx.alternate_window)) == 2
    # Different declared fields (a gaussian blob vs. a sinusoidal mode) on
    # the same mesh produce different colour maps -- if `render_field`
    # were ignored, or always picked the same field regardless of which
    # name was configured, both runs would render identical colours.
    selected_colors = _field_fill_mesh(ctx.late_window).geometry.colors.data
    alternate_colors = _field_fill_mesh(ctx.alternate_window).geometry.colors.data
    assert selected_colors.shape == alternate_colors.shape
    assert (selected_colors != alternate_colors).any()


@then("loading is rejected with a named error naming the undeclared field")
def _then_rejected_naming_undeclared_render_field(ctx: _Context) -> None:
    assert ctx.error is not None, "expected load_config to reject the undeclared render_field"
    message = str(ctx.error)
    assert "field_display.render_field" in message
    assert "nowhere" in message
