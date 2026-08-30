"""Binds `tests/features/passive_tracers.feature` (TASK-038, Stage 6's
fifth and last task). Not a golden demo -- no config file under
`examples/golden-demos/`, no CLI subprocess run, the same `tests/unit/`
shape `test_humidity_field.py`/`test_density_field.py` already
established. This stage's actual golden demo (Smoke Transport) is bound
separately, from `tests/golden/`.

Every scenario here goes through real `bootstrap()`, not a hand-built
`AssembledNumerics` -- the claim is about the configuration surface (a
solved-velocity run carrying one or more declared tracer fields)
producing the right behaviour end to end, which a hand-constructed
scheme would not exercise. Both scenarios reuse a small, cheap
lid-driven-cavity-shaped setup (`_LID_CAVITY_CONFIG`) -- the same
mesh/timestep/viscosity shape `examples/golden-demos/lid_driven_cavity.yaml`
already proved stable, at a coarser resolution chosen for test speed
since this module calls `bootstrap()` several times.

Every numeric threshold below was measured against this real
implementation while writing this file, the same discipline
`test_temperature_field.py`'s/`test_humidity_field.py`'s own module
docstrings record.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine import simulation
from pyflow.engine.scalar_field import ScalarField

scenarios("passive_tracers.feature")

# -- Shared physical fixtures --------------------------------------------
#
# A small, closed, no-slip cavity with the north wall moving tangentially
# -- the same shape `lid_driven_cavity.yaml` uses, at half the resolution
# (8x8, not 16x16) since this module runs several bootstrap() calls per
# scenario and needs none of Ghia's own quantitative comparison.

_LID_CAVITY_NUMERICS = (
    "mesh:\n  extent: [8, 8]\n  spacing: [0.125, 0.125]\n"
    "numerics:\n"
    "  timestep: 0.008\n"
    "  boundary_conditions:\n"
    "    north:\n"
    "      type: dirichlet\n"
    "      field_values:\n"
    "        velocity.0: 1.0\n"
    "        velocity.1: 0.0\n"
    "    south:\n      type: dirichlet\n"
    "    east:\n      type: dirichlet\n"
    "    west:\n      type: dirichlet\n"
    "simulation:\n  velocity_solved: true\n"
    "fluid:\n  viscosity: 0.01\n"
    "rendering:\n  backend: offscreen\n"
)

_FRAMES = 6
"""Measured directly against this fixture before choosing it: the lid's
own motion has clearly diffused into the interior and visibly advected
every declared tracer field by this many real timesteps, on a mesh small
enough that several `bootstrap()` calls in one scenario stay fast.
"""


def _config_with_fields(fields_yaml: str) -> str:
    return _LID_CAVITY_NUMERICS + fields_yaml


_NO_TRACER_CONFIG = _config_with_fields("")

_ONE_TRACER_CONFIG = _config_with_fields(
    "fields:\n  - name: tracer\n    initial_condition: gaussian_blob\n"
    "    diffusion_coefficient: 0.05\n"
)

_FOUR_TRACER_NAMES = ("tracer_a", "tracer_b", "tracer_c", "tracer_d")
_FOUR_TRACER_DIFFUSIVITIES = (0.02, 0.03, 0.04, 0.05)


def _four_tracer_config() -> str:
    fields = "fields:\n"
    for name, diffusivity in zip(_FOUR_TRACER_NAMES, _FOUR_TRACER_DIFFUSIVITIES, strict=True):
        fields += (
            f"  - name: {name}\n"
            "    initial_condition: gaussian_blob\n"
            f"    diffusion_coefficient: {diffusivity}\n"
        )
    return _config_with_fields(fields)


_SOLO_TRACER_CONFIG = _config_with_fields(
    f"fields:\n  - name: {_FOUR_TRACER_NAMES[0]}\n    initial_condition: gaussian_blob\n"
    f"    diffusion_coefficient: {_FOUR_TRACER_DIFFUSIVITIES[0]}\n"
)


# -- Fixture context ------------------------------------------------------


@dataclass
class _Context:
    without_tracer_path: Path | None = None
    with_tracer_path: Path | None = None
    without_tracer_velocity: dict[str, torch.Tensor] | None = None
    with_tracer_velocity: dict[str, torch.Tensor] | None = None
    tracer_after_one: torch.Tensor | None = None
    tracer_after_several: torch.Tensor | None = None
    four_tracer_path: Path | None = None
    solo_tracer_path: Path | None = None
    four_tracer_fields: dict[str, torch.Tensor] | None = None
    solo_tracer_field: torch.Tensor | None = None


# -- Given -----------------------------------------------------------------


@given("a configuration transporting solved velocity with no tracer declared", target_fixture="ctx")
def _given_no_tracer(tmp_path: Path) -> _Context:
    config_path = tmp_path / "no_tracer.yaml"
    config_path.write_text(_NO_TRACER_CONFIG)
    return _Context(without_tracer_path=config_path)


@given("the same configuration with a passive tracer also declared")
def _given_with_tracer(ctx: _Context, tmp_path: Path) -> None:
    config_path = tmp_path / "with_tracer.yaml"
    config_path.write_text(_ONE_TRACER_CONFIG)
    ctx.with_tracer_path = config_path


@given(
    "a configuration transporting solved velocity alongside four passive tracers with "
    "different diffusivities",
    target_fixture="ctx",
)
def _given_four_tracers(tmp_path: Path) -> _Context:
    four_path = tmp_path / "four_tracers.yaml"
    four_path.write_text(_four_tracer_config())
    solo_path = tmp_path / "solo_tracer.yaml"
    solo_path.write_text(_SOLO_TRACER_CONFIG)
    return _Context(four_tracer_path=four_path, solo_tracer_path=solo_path)


# -- When ------------------------------------------------------------------


@when("both are run for the same number of real timesteps")
def _when_both_run(ctx: _Context) -> None:
    assert ctx.without_tracer_path is not None
    assert ctx.with_tracer_path is not None

    without = bootstrap(ctx.without_tracer_path, backend="offscreen", max_frames=_FRAMES)
    with_tracer = bootstrap(ctx.with_tracer_path, backend="offscreen", max_frames=_FRAMES)
    after_one = bootstrap(ctx.with_tracer_path, backend="offscreen", max_frames=1)

    assert without.simulation_fields is not None
    assert with_tracer.simulation_fields is not None
    assert after_one.simulation_fields is not None

    ctx.without_tracer_velocity = {
        name: _as_scalar(without.simulation_fields[name]).values
        for name in ("velocity.0", "velocity.1")
    }
    ctx.with_tracer_velocity = {
        name: _as_scalar(with_tracer.simulation_fields[name]).values
        for name in ("velocity.0", "velocity.1")
    }
    ctx.tracer_after_several = _as_scalar(with_tracer.simulation_fields["tracer"]).values
    ctx.tracer_after_one = _as_scalar(after_one.simulation_fields["tracer"]).values


@when("it is run for several real timesteps")
def _when_four_tracers_run(ctx: _Context) -> None:
    assert ctx.four_tracer_path is not None
    assert ctx.solo_tracer_path is not None

    four = bootstrap(ctx.four_tracer_path, backend="offscreen", max_frames=_FRAMES)
    solo = bootstrap(ctx.solo_tracer_path, backend="offscreen", max_frames=_FRAMES)

    assert four.simulation_fields is not None
    assert solo.simulation_fields is not None

    ctx.four_tracer_fields = {
        name: _as_scalar(four.simulation_fields[name]).values for name in _FOUR_TRACER_NAMES
    }
    ctx.solo_tracer_field = _as_scalar(solo.simulation_fields[_FOUR_TRACER_NAMES[0]]).values


def _as_scalar(field: object) -> ScalarField:
    assert isinstance(field, ScalarField)
    return field


# -- Then --------------------------------------------------------------


@then("the velocity fields are identical, element by element, whether or not the tracer is present")
def _then_velocity_identical(ctx: _Context) -> None:
    assert ctx.without_tracer_velocity is not None
    assert ctx.with_tracer_velocity is not None
    for name in ("velocity.0", "velocity.1"):
        assert torch.equal(ctx.without_tracer_velocity[name], ctx.with_tracer_velocity[name]), (
            f"expected {name!r} to be bit-identical with and without the declared tracer"
        )


@then("the tracer field is measurably different after several timesteps than after one")
def _then_tracer_not_inert(ctx: _Context) -> None:
    assert ctx.tracer_after_one is not None
    assert ctx.tracer_after_several is not None
    assert not torch.equal(ctx.tracer_after_one, ctx.tracer_after_several), (
        "expected the tracer field to keep changing under transport, not freeze after one step"
    )


@then("no two of the four tracer fields are identical to each other")
def _then_four_tracers_differ(ctx: _Context) -> None:
    assert ctx.four_tracer_fields is not None
    names = list(_FOUR_TRACER_NAMES)
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            assert not torch.equal(
                ctx.four_tracer_fields[name_a], ctx.four_tracer_fields[name_b]
            ), (
                f"expected {name_a!r} and {name_b!r} to differ (they were given different "
                "diffusivities), got identical fields"
            )


@then(
    "a tracer's own field is identical whether it is transported alongside the other three or alone"
)
def _then_tracer_independent(ctx: _Context) -> None:
    assert ctx.four_tracer_fields is not None
    assert ctx.solo_tracer_field is not None
    together = ctx.four_tracer_fields[_FOUR_TRACER_NAMES[0]]
    assert torch.equal(together, ctx.solo_tracer_field), (
        f"expected {_FOUR_TRACER_NAMES[0]!r} to be bit-identical whether the other three "
        "tracers are also declared or not"
    )


@when("the orchestrator module's source is inspected")
def _when_source_inspected() -> None:
    pass


@then('it contains no "temperature", "density", "humidity" or "tracer" string literal')
def _then_no_phenomenon_literal() -> None:
    source = inspect.getsource(simulation)
    for literal in ('"temperature"', '"density"', '"humidity"', '"tracer"'):
        assert literal not in source, f"expected no {literal} string literal in simulation.py"
