"""Numerics Assembly golden demo (TASK-021).

The acceptance criteria are `tests/features/numerics_assembly.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). This module binds
them and supplies the steps only this demo needs -- reading back
`RenderWindow.assembled_numerics`, and the Field Display carve-out
check (Stage 3 Completion Criterion 8's "honest about having nothing new
to draw": a full `numerics` section must not change what an existing
demo renders). The demo-independent steps (run through the CLI, render a
frame, compare two frames) come from `conftest.py`.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.configuration import load_config
from pyflow.configuration.generator import generate_config_yaml
from pyflow.engine.numerics.assembly import AssembledNumerics

from ._demo import GOLDEN_DEMOS, DemoRun, render_offscreen

scenarios("numerics_assembly.feature")


def _expected_names(config: DemoRun) -> dict[str, str]:
    numerics = config.config.numerics
    boundary = numerics.boundary_conditions
    return {
        "advection": numerics.advection,
        "diffusion": numerics.diffusion,
        "time_integration": numerics.time_integration,
        "linear_solver": numerics.linear_solver,
        "pressure_coupling": numerics.pressure_coupling,
        "source_term": numerics.source_term,
        "boundary_conditions.north": boundary.north.type,
        "boundary_conditions.south": boundary.south.type,
        "boundary_conditions.east": boundary.east.type,
        "boundary_conditions.west": boundary.west.type,
    }


# -- "The assembled set matches what was configured" -----------------------


@when("it is bootstrapped directly", target_fixture="assembled")
def _when_bootstrapped_directly(demo: DemoRun) -> AssembledNumerics:
    window = bootstrap(demo.config_path, backend="offscreen", max_frames=1)
    assert window.assembled_numerics is not None, "bootstrap() did not assemble numerics"
    return window.assembled_numerics


@then("the reported assembled set matches the configured numerics section")
def _then_matches_configured(demo: DemoRun, assembled: AssembledNumerics) -> None:
    assert dict(assembled.names) == _expected_names(demo)


# -- "The run reports the assembled set through the real CLI" --------------
#
# The demo-independent step vocabulary (`conftest.py`) runs the CLI and
# checks it exits cleanly; reading the assembled set back out of its
# output is specific to this demo, so it lives here per that module's
# "keep the vocabulary demo-independent" rule.

_REPORT_PREFIX = "numerics assembled: "


@then("its output reports an assembled set matching the configured numerics section")
def _then_cli_output_reports_assembled_set(demo: DemoRun) -> None:
    assert demo.process is not None, "no CLI run to read"
    # Logging goes to stderr (`engine/logging_setup.py`), not stdout.
    lines = [line for line in demo.process.stderr.splitlines() if _REPORT_PREFIX in line]
    assert len(lines) == 1, (
        f"expected exactly one {_REPORT_PREFIX!r} line in the CLI's stderr, "
        f"got {len(lines)}. Full stderr: {demo.process.stderr!r}"
    )
    _, _, reported = lines[0].partition(_REPORT_PREFIX)
    # `literal_eval`, not `eval`: this is subprocess output being parsed.
    assert ast.literal_eval(reported.strip()) == _expected_names(demo)


# -- "Assembling the same configuration twice reports the same set" --------


@when("it is bootstrapped twice", target_fixture="assembled_pair")
def _when_bootstrapped_twice(demo: DemoRun) -> tuple[AssembledNumerics, AssembledNumerics]:
    first = bootstrap(demo.config_path, backend="offscreen", max_frames=1).assembled_numerics
    second = bootstrap(demo.config_path, backend="offscreen", max_frames=1).assembled_numerics
    assert first is not None
    assert second is not None
    return first, second


@then("both runs report an identical assembled set")
def _then_identical_assembled_sets(
    assembled_pair: tuple[AssembledNumerics, AssembledNumerics],
) -> None:
    first, second = assembled_pair
    assert dict(first.names) == dict(second.names)


# -- "Adding a numerics section does not change Field Display's output" ----


@given('the "field_display" demo\'s own configuration')
def _given_field_display_config(demo: DemoRun) -> None:
    demo.config_path = GOLDEN_DEMOS / "field_display.yaml"
    demo.config = load_config(demo.config_path)


@when(
    "a numerics section naming a non-default timestep is added to it",
    target_fixture="variant_config_path",
)
def _when_numerics_section_added(demo: DemoRun, tmp_path: Path) -> Path:
    # `timestep`'s default is 0.01 (schema.py); any distinct positive
    # value proves the section was genuinely added, not left at defaults
    # by coincidence.
    modified = replace(demo.config, numerics=replace(demo.config.numerics, timestep=0.05))
    variant_path = tmp_path / "field_display_with_numerics_section.yaml"
    variant_path.write_text(generate_config_yaml(modified))
    return variant_path


@when("both variants are rendered offscreen")
def _when_both_variants_rendered(demo: DemoRun, variant_config_path: Path) -> None:
    render_offscreen(demo, config_path=demo.config_path)
    render_offscreen(demo, config_path=variant_config_path)
