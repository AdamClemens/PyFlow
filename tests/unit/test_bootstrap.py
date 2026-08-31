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
from pyflow.engine.numerics.divergence import GreenGaussDivergence
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


def _text_children(scene: gfx.Scene) -> list[gfx.Text]:
    return [child for child in scene.children if isinstance(child, gfx.Text)]


def _text_content(text_obj: gfx.Text) -> str:
    # No public readback on `gfx.Text` -- see `tests/unit/test_hud.py`'s
    # own module docstring for why this reaches into pygfx's private
    # `_text_blocks`, confirmed live against the installed pygfx==0.17.0.
    return "\n".join(block._input[1] for block in text_obj._text_blocks)


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


# -- HUD (Stage 7, Rendering Annotations) -----------------------------------


def test_bootstrap_shows_hud_even_with_nothing_else_configured(tmp_path: Path) -> None:
    """Reversed 2026-08-31 after real user feedback on the first cut of
    this feature: the HUD used to stay off unless `show_mesh`/
    `field_display`/a live simulation was also configured, specifically
    to protect Empty Window's own contract (`tests/features/
    empty_window.feature`, "every pixel is the configured background
    colour"). That made every demo with nothing else to show (e.g.
    Numerics Assembly, Stage 3's own "no CFD yet" demo) render a
    genuinely blank window with zero information, which is worse than
    the gap this stage exists to close. The HUD now defaults on
    regardless of what else is configured -- `rendering.show_title`/
    `show_stats` are the opt-out, not a side effect of not visualising
    anything else. Empty Window itself is the one demo that still wants
    the bare look, and now asks for it explicitly (see the sibling test
    below and `examples/golden-demos/empty_window.yaml`).
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  title: My Simulation\n")

    window = bootstrap(config_file, max_frames=1)

    titles = [t for t in _text_children(window.scene) if _text_content(t) == "My Simulation"]
    assert len(titles) == 1


def test_bootstrap_show_title_and_show_stats_both_false_shows_nothing(tmp_path: Path) -> None:
    """The explicit, opt-in way to get Empty Window's own bare look back
    -- both HUD toggles off, with nothing else configured either.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_title: false\n  show_stats: false\n"
    )

    window = bootstrap(config_file, max_frames=1)

    assert not any(_text_children(window.scene))


def test_bootstrap_adds_a_title_by_default(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_mesh: true\n  title: My Simulation\n"
    )

    window = bootstrap(config_file, max_frames=1)

    titles = [t for t in _text_children(window.scene) if _text_content(t) == "My Simulation"]
    assert len(titles) == 1


def test_bootstrap_show_title_false_adds_no_title(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_mesh: true\n"
        "  title: My Simulation\n  show_title: false\n"
    )

    window = bootstrap(config_file, max_frames=1)

    assert not any(_text_content(t) == "My Simulation" for t in _text_children(window.scene))


def test_bootstrap_adds_a_stats_block_with_cell_and_domain_size(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_mesh: true\n"
        "mesh:\n  spacing: [0.5, 0.25]\n  extent: [4, 2]\n"
    )

    window = bootstrap(config_file, max_frames=1)

    stats = [
        _text_content(t) for t in _text_children(window.scene) if "cell" in _text_content(t).lower()
    ]
    assert len(stats) == 1
    assert "0.5" in stats[0]
    assert "0.25" in stats[0]
    # Domain = spacing * extent = 2.0 x 0.5.
    assert "2" in stats[0]


def test_bootstrap_show_stats_false_adds_no_stats_block(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_mesh: true\n  show_stats: false\n"
    )

    window = bootstrap(config_file, max_frames=1)

    assert not any("cell" in _text_content(t).lower() for t in _text_children(window.scene))


def test_bootstrap_static_display_stats_have_no_step_or_time_line(tmp_path: Path) -> None:
    """A static (non-live-stepping) run has no timestep concept -- the
    stats block must not claim one.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  show_mesh: true\n")

    window = bootstrap(config_file, max_frames=1)

    stats = next(t for t in _text_children(window.scene) if "cell" in _text_content(t).lower())
    assert "step" not in _text_content(stats).lower()


def test_bootstrap_live_stepping_stats_include_step_and_change_between_frames(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "fields:\n  - name: scalar\n    initial_condition: gaussian_blob\n"
    )

    early = bootstrap(config_file, max_frames=1)
    early_stats = next(t for t in _text_children(early.scene) if "cell" in _text_content(t).lower())
    assert "step" in _text_content(early_stats).lower()

    later = bootstrap(config_file, max_frames=5)
    later_stats = next(t for t in _text_children(later.scene) if "cell" in _text_content(t).lower())
    assert _text_content(early_stats) != _text_content(later_stats)


def test_bootstrap_scalar_display_with_legend_adds_numeric_labels(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "field_display:\n  scalar_pattern: radial_gradient\n  value_range: [0.0, 5.0]\n"
    )

    window = bootstrap(config_file, max_frames=1)

    contents = [_text_content(t) for t in _text_children(window.scene)]
    assert "0" in contents
    assert "5" in contents


def test_bootstrap_scalar_display_legend_disabled_adds_no_numeric_labels(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "field_display:\n  scalar_pattern: radial_gradient\n  show_legend: false\n"
        "  value_range: [0.0, 5.0]\n"
    )

    window = bootstrap(config_file, max_frames=1)

    contents = [_text_content(t) for t in _text_children(window.scene)]
    assert "0" not in contents
    assert "5" not in contents


def test_bootstrap_legend_field_label_defaults_to_render_field_name(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "fields:\n  - name: temperature\n    initial_condition: gaussian_blob\n"
        "field_display:\n  render_field: temperature\n"
    )

    window = bootstrap(config_file, max_frames=1)

    contents = [_text_content(t) for t in _text_children(window.scene)]
    assert "temperature" in contents


def test_bootstrap_legend_field_label_overrides_render_field_name(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "fields:\n  - name: temperature\n    initial_condition: gaussian_blob\n"
        "field_display:\n  render_field: temperature\n  field_label: Temperature (K)\n"
    )

    window = bootstrap(config_file, max_frames=1)

    contents = [_text_content(t) for t in _text_children(window.scene)]
    assert "Temperature (K)" in contents
    assert "temperature" not in contents


def test_bootstrap_stats_use_configured_physical_units(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n  show_mesh: true\n"
        "mesh:\n  spacing: [1.0, 1.0]\n  extent: [1, 1]\n"
        "units:\n  length_unit: mm\n  length_scale: 25.0\n"
    )

    window = bootstrap(config_file, max_frames=1)

    stats = next(t for t in _text_children(window.scene) if "cell" in _text_content(t).lower())
    assert "mm" in _text_content(stats)
    assert "25" in _text_content(stats)


def test_bootstrap_vector_label_adds_a_scale_line_for_static_arrows(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "field_display:\n  vector_pattern: rotational\n"
        "  vector_label: Rotational vector\n  arrow_scale: 0.4\n"
    )

    window = bootstrap(config_file, max_frames=1)

    scale_line = next(
        t for t in _text_children(window.scene) if "rotational vector" in _text_content(t).lower()
    )
    assert "0.4" in _text_content(scale_line)


def test_bootstrap_no_vector_label_configured_adds_no_scale_line(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\nfield_display:\n  vector_pattern: rotational\n"
    )

    window = bootstrap(config_file, max_frames=1)

    assert not any("length =" in _text_content(t) for t in _text_children(window.scene))


def test_bootstrap_vector_label_adds_a_scale_line_for_live_velocity_only_arrows(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\n"
        "simulation:\n  velocity_solved: true\n  velocity_pattern: uniform\n"
        "  velocity: [1.0, 0.0]\n"
        "field_display:\n  vector_label: Velocity\n  arrow_scale: 0.05\n"
    )

    window = bootstrap(config_file, max_frames=1)

    scale_line = next(
        t for t in _text_children(window.scene) if "velocity" in _text_content(t).lower()
    )
    assert "0.05" in _text_content(scale_line)


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
        "fields:\n  - name: scalar\n    initial_condition: gaussian_blob\n"
        "simulation:\n"
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


_SOLVED_WITH_SCALAR_CONFIG = (
    "rendering:\n  backend: offscreen\n"
    "mesh:\n  origin: [0.4, -0.3]\n  extent: [8, 6]\n  spacing: [0.2, 0.25]\n"
    "numerics:\n  timestep: 0.005\n"
    "fluid:\n  viscosity: 0.05\n"
    "fields:\n  - name: scalar\n    initial_condition: gaussian_blob\n"
    "simulation:\n"
    "  velocity_pattern: uniform\n"
    "  velocity: [1.3, -0.7]\n"
    "  velocity_solved: true\n"
)
"""A uniform interior velocity inside a closed no-slip box -- the walls
immediately generate real divergence, which is what makes the assertion
below discriminating. Distinct factors throughout (non-square mesh,
non-trivial origin, unequal spacing, a velocity aligned with neither
axis), per `docs/practices.md`.
"""

_SOLVED_DIVERGENCE_BOUND = 0.5
"""Measured on real runs of both behaviours before being chosen, not
guessed (Stage 5 exit audit, 2026-08-29). Pressure-corrected, this
fixture's own maximum divergence falls 2.30 -> 0.47 -> 0.057 over 1, 10
and 40 frames; transported by plain `step` and never corrected, it sits
at 9.16 -> 8.24 -> 6.95 across the same frames. The bound has roughly
nine times' margin below the corrected value at 40 frames and is more
than an order of magnitude under the uncorrected one, so it separates the
two behaviours rather than merely recording one of them.

**Not driven to solver tolerance, and that is expected**:
`GreenGaussDivergence`'s naive face-averaged divergence is deliberately
not the Rhie-Chow-consistent measure `PISO`'s corrector loop drives to
its own tolerance -- see `tests/golden/test_lid_driven_cavity.py`'s own
module docstring, which declines to assert an absolute bound for exactly
this reason. What this test claims is the weaker, sufficient thing: the
divergence collapses instead of persisting.
"""


def test_bootstrap_with_velocity_solved_and_a_scalar_pressure_corrects_the_velocity(
    tmp_path: Path,
) -> None:
    """A solved velocity carrying a scalar alongside it is genuinely
    incompressible, not merely self-advected.

    **This was a real defect until the Stage 5 exit audit (2026-08-29)
    found it**, and a configuration-reachable one:
    `simulation.velocity_solved` had two live paths, and only the
    velocity-*only* one (`_add_solved_velocity_rendering`, TASK-034)
    called `navier_stokes_step`. Adding a `scalar_pattern` silently
    switched a run to `_add_passive_scalar_transport`, which transported
    velocity's components like any other scalar and never
    pressure-corrected them -- so a configuration saying "solved"
    produced a velocity that was not incompressible, with no error and
    nothing rendered differently. Recorded as a known gap in two
    `CLAUDE.md` files at the time and against no completion criterion,
    which is why it survived Stage 5's own Criterion 12 being marked met.
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(_SOLVED_WITH_SCALAR_CONFIG)

    window = bootstrap(config_file, max_frames=40)

    assert window.simulation_fields is not None
    assert window.assembled_numerics is not None
    u = window.simulation_fields[VectorField.component_name("velocity", 0)]
    v = window.simulation_fields[VectorField.component_name("velocity", 1)]
    assert isinstance(u, ScalarField)
    assert isinstance(v, ScalarField)
    velocity = VectorField.assemble([u, v], "velocity")
    divergence = GreenGaussDivergence(window.assembled_numerics.boundary_conditions, {}).divergence(
        velocity
    )

    assert float(divergence.abs().max()) < _SOLVED_DIVERGENCE_BOUND, (
        "the solved velocity's own divergence did not collapse; this path is transporting "
        "velocity without pressure-correcting it"
    )


def test_bootstrap_backend_override(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: glfw\n"
    )  # would open a real window if not overridden

    window = bootstrap(config_file, max_frames=1, backend="offscreen")

    assert window.canvas.get_closed()
