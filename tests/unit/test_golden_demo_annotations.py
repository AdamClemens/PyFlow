"""P-019 conformance for every bundled golden demo (added 2026-09-03 by
the Stage 7 exit audit).

`docs/engineering-principles.md`'s **P-019** -- every rendered chart,
plot or mesh view labels its own axes and legends -- was written as a
standing rule and enforced by nothing. All ten demos happened to comply
on the day it was written, because the same change that wrote the rule
also fixed all ten; the eleventh demo, written by somebody who has not
read `src/pyflow/rendering/CLAUDE.md`, would have violated it silently.
`docs/practices.md`'s "A checkable trigger still needs somebody to check
it" is the rule this module exists to satisfy.

**Configuration conformance, not rendering.** These tests read the
committed demo configs and assert each one *asks* for the labels its
own rendering needs; that the asked-for labels are then actually drawn
inside the framed view is `tests/features/field_display.feature`'s own
four annotation scenarios, checked in real pixels on the one demo whose
canvas is aspect-pinned for pixel-exact work. The two halves are
deliberately separate: this one is cheap and covers every demo, that one
is expensive and covers one demo thoroughly.

Lives in `tests/unit/` rather than `tests/golden/`: it exercises no
process boundary, renders nothing, and runs no demo -- it loads YAML
through `pyflow.configuration` and inspects the result, which is exactly
`tests/unit/CLAUDE.md`'s own scope. It is not bound to a `.feature`
file for the same reason `test_golden_demos.py` is not: a repository
convention nothing physical would observe is not an acceptance criterion
for simulation work (`adr/ADR-007-executable-acceptance-criteria.md`'s
own scope).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pyflow.configuration import load_config
from pyflow.configuration.schema import PyFlowConfig

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_DEMOS_DIR = _REPO_ROOT / "examples" / "golden-demos"

_DEMO_PATHS = sorted(_GOLDEN_DEMOS_DIR.glob("*.yaml"))


def _demo_ids() -> list[str]:
    return [path.stem for path in _DEMO_PATHS]


@pytest.fixture(params=_DEMO_PATHS, ids=_demo_ids())
def demo_config(request: pytest.FixtureRequest) -> PyFlowConfig:
    return load_config(request.param)


def _colour_maps_a_field(config: PyFlowConfig) -> bool:
    """The two ways a demo puts a colour map on screen: a static
    `scalar_pattern` (`_add_field_display`) or a live-transported
    `render_field` (`_add_declared_field_transport`). Both draw the
    legend strip `_add_legend` builds, and so both need a caption.
    """
    return (
        config.field_display.scalar_pattern is not None
        or config.field_display.render_field is not None
    )


def _draws_arrows(config: PyFlowConfig) -> bool:
    """The two ways a demo puts arrows on screen: a static
    `vector_pattern`, or a velocity-only solved run
    (`_add_solved_velocity_rendering`).

    **`velocity_solved` with declared fields alongside it is not one of
    them** -- that configuration takes `_add_declared_field_transport`,
    which colour-maps a scalar and draws no arrows at all. Mirrors
    `bootstrap.py`'s own `run_velocity_only_simulation`; the two demos
    that combine a solved velocity with declared fields
    (`smoke_transport`, `thermal_buoyancy`) are correctly exempt.
    """
    return config.field_display.vector_pattern is not None or (
        config.simulation.velocity_solved and not config.fields
    )


def _renders_a_mesh_view(config: PyFlowConfig) -> bool:
    return (
        config.rendering.show_mesh
        or _colour_maps_a_field(config)
        or _draws_arrows(config)
        or bool(config.fields)
    )


def test_every_demo_that_colour_maps_a_field_names_the_quantity(
    demo_config: PyFlowConfig,
) -> None:
    """P-019's legend half. `_add_hud` captions the legend with
    `field_label or render_field`, so a static `scalar_pattern` demo
    setting neither renders a gradient strip with numbers at its ends
    and no statement of what is being measured.
    """
    if not _colour_maps_a_field(demo_config) or not demo_config.field_display.show_legend:
        pytest.skip("draws no legend")

    caption = demo_config.field_display.field_label or demo_config.field_display.render_field
    assert caption, (
        "a demo that colour-maps a field must name the quantity "
        "(field_display.field_label, or render_field as the fallback) -- P-019"
    )


def test_every_demo_that_draws_arrows_states_what_they_are(demo_config: PyFlowConfig) -> None:
    """P-019's vector half, and the gap the standing rule was written
    from: real user feedback on arrows with no label was "presumably
    velocity or something? Neither the direction nor magnitude is
    clear." `field_display.vector_label` is what adds the HUD line
    naming the quantity and stating `arrow_scale` as a
    length-per-magnitude conversion.
    """
    if not _draws_arrows(demo_config):
        pytest.skip("draws no arrows")

    assert demo_config.field_display.vector_label, (
        "a demo that draws arrows must name the quantity they represent "
        "(field_display.vector_label) -- P-019"
    )


def test_every_demo_that_renders_a_mesh_view_labels_its_axes(demo_config: PyFlowConfig) -> None:
    """P-019's axis half. Axis tick labels share `rendering.show_stats`
    as their gate rather than having a toggle of their own, so a demo
    that renders a mesh view and switches `show_stats` off has silently
    opted out of labelled axes -- legitimate only for a demo that
    renders nothing, which `empty_window` is and this check exempts.
    """
    if not _renders_a_mesh_view(demo_config):
        pytest.skip("renders no mesh view")

    assert demo_config.rendering.show_stats, (
        "a demo that renders a mesh view must leave rendering.show_stats on, "
        "which is what labels both spatial axes -- P-019"
    )


def test_every_demo_that_renders_anything_says_what_it_is(demo_config: PyFlowConfig) -> None:
    """The stage goal's own first question -- "what is it" -- rather
    than P-019 itself. `rendering.title` defaults to `"PyFlow"`, which
    is the application's name and not the run's, so a demo leaving it at
    the default has answered nothing.
    """
    if not _renders_a_mesh_view(demo_config):
        pytest.skip("renders nothing")

    assert demo_config.rendering.show_title, "a demo that renders something must show its title"
    assert demo_config.rendering.title != "PyFlow", (
        "a demo must set rendering.title to its own name, not leave it at the application default"
    )


def test_the_sweep_actually_covers_the_demos() -> None:
    """The guard every parametrised sweep needs: an empty or mis-globbed
    `_DEMO_PATHS` would make all four tests above pass by covering
    nothing (`docs/practices.md`, "A rule that matches nothing reports
    nothing"). Cross-checked against the registry's own count rather
    than a hand-typed one, so adding a demo does not need this number
    edited.
    """
    from pyflow.configuration.golden_demos import _GOLDEN_DEMOS

    assert _DEMO_PATHS, f"no golden demo configs found under {_GOLDEN_DEMOS_DIR}"
    assert len(_DEMO_PATHS) == len(_GOLDEN_DEMOS)
