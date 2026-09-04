"""Multi-Field Plume golden demo (Stage 6's own claim, made runnable).

The acceptance criteria are `tests/features/multi_field_plume.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). This module binds them
and supplies the steps only this demo needs.

**Why this demo exists.** Stage 6's goal is "demonstrate field-centric
architecture" and its Completion Criterion 1 asks for four named fields
in one run, "not four separate one-field runs, which would never
exercise the sharing that makes this claim interesting". That stage
shipped three golden demos -- Heat Transport, Smoke Transport, Thermal
Buoyancy -- and **every one of them declares exactly one field**, which
is the shape the criterion rules out. The criterion was discharged by a
scenario using four passive *tracers*: four instances of one phenomenon.
Nothing a user could run demonstrated four differently-named fields
sharing one engine. This does.

**It reports what it carries, and that is the demonstration.** A
rendered frame shows one colour-mapped field, so this demo looks much
like Thermal Buoyancy on screen -- exit-code-zero and a pixel diff both
cover it without covering what it claims. `tests/golden/CLAUDE.md` names
the precedent for exactly this case: `numerics_assembly` renders nothing
new, so its CLI report *is* the demonstration, and the Stage 3 exit audit
found that report was only ever checked in-process. This module reads
the field report back out of a real subprocess's stderr, the same way.
"""

from __future__ import annotations

import inspect

from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine import simulation
from pyflow.engine.scalar_field import ScalarField

from ._demo import DemoRun

scenarios("multi_field_plume.feature")

_STEPPED_FRAMES = 60
"""Enough real timesteps for the plume to move measurably at this demo's
own `numerics.timestep`, and few enough to keep the run quick. Chosen
against a real run, not guessed: the temperature centroid rises about
0.19 world units over these frames, roughly a whole cell.
"""

_FIELDS = ("temperature", "humidity", "smoke", "tracer")
"""Mirrors `multi_field_plume.yaml`'s own `fields:` list, kept explicit
so a reader can check it against the file rather than re-deriving it --
the same reason `test_field_display.py` restates its mesh.
"""


def _mass_and_centroid_y(field: ScalarField) -> tuple[float, float]:
    """Total mass and mass-weighted centroid height.

    Valid because every initial condition here is non-negative where it
    matters; the sinusoidal field is handled by its caller, which only
    asks whether it *changed*, never where its centre is.
    """
    mesh = field.mesh
    total = 0.0
    weighted = 0.0
    for cell in range(mesh.num_cells):
        value = float(field.value_at(cell))
        _x, y = mesh.cell_centroid(cell)
        total += value
        weighted += value * y
    return total, (weighted / total if total else 0.0)


def _sharpness(field: ScalarField) -> float:
    """Peak value over mean value -- a diffusion-sensitive shape measure
    that does not depend on the field's total mass.

    A field that has diffused further has spread its mass out, so its
    peak falls toward its mean and this ratio drops. Chosen over a
    variance because two of these fields start from different initial
    conditions and a variance would compare their *shapes* rather than
    how far each has smoothed.
    """
    values = [float(field.value_at(c)) for c in range(field.mesh.num_cells)]
    mean = sum(values) / len(values)
    assert mean > 0, "field has no mass to measure sharpness against"
    return max(values) / mean


# -- When ------------------------------------------------------------------


@when("it is stepped for several real timesteps", target_fixture="stepped")
def _when_stepped(demo: DemoRun) -> tuple[dict[str, ScalarField], dict[str, ScalarField]]:
    """Two independent real runs through the public `bootstrap()` entry
    point -- one stopped immediately, one after `_STEPPED_FRAMES` -- so
    there is a genuine "where it started" to compare against.

    `RenderWindow.simulation_fields` holds the live state after the run,
    the same readback `test_passive_scalar_transport.py` uses; there is
    no pre-step frame 0 recorded anywhere to read instead.
    """

    def run(frames: int) -> dict[str, ScalarField]:
        window = bootstrap(demo.config_path, backend="offscreen", max_frames=frames)
        state = window.simulation_fields
        assert state is not None, "the run recorded no simulation state"
        return {
            name: field
            for name, field in state.items()
            if isinstance(field, ScalarField) and name in _FIELDS
        }

    return run(1), run(_STEPPED_FRAMES)


@when("the orchestrator module's source is inspected", target_fixture="orchestrator_source")
def _when_orchestrator_inspected() -> str:
    return inspect.getsource(simulation)


# -- Then ------------------------------------------------------------------


@then("its output reports transporting exactly the fields the configuration declares")
def _then_reports_declared_fields(demo: DemoRun) -> None:
    assert demo.process is not None, "no CLI run to read a report from"
    output = demo.process.stderr + demo.process.stdout
    declared = [field.name for field in demo.config.fields]
    assert sorted(declared) == sorted(_FIELDS), (
        f"this demo's configuration must declare {sorted(_FIELDS)}, got {sorted(declared)}"
    )

    reported = [line for line in output.splitlines() if "transporting" in line]
    assert reported, (
        "the run reported no transported fields at all -- this demo's whole "
        f"demonstration is that report. Output was:\n{output}"
    )
    line = reported[-1]
    for name in declared:
        assert name in line, f"{name!r} is declared but not reported: {line!r}"


@then("the run carries all four declared fields at once")
def _then_carries_all_four(stepped: tuple[dict[str, ScalarField], dict[str, ScalarField]]) -> None:
    _initial, final = stepped
    assert sorted(final) == sorted(_FIELDS), (
        f"expected all of {sorted(_FIELDS)} in one run's state, got {sorted(final)}"
    )


@then("no two of the four fields hold identical values")
def _then_all_four_differ(stepped: tuple[dict[str, ScalarField], dict[str, ScalarField]]) -> None:
    _initial, final = stepped
    names = sorted(final)
    for i, first in enumerate(names):
        for second in names[i + 1 :]:
            a = [float(final[first].value_at(c)) for c in range(final[first].mesh.num_cells)]
            b = [float(final[second].value_at(c)) for c in range(final[second].mesh.num_cells)]
            assert a != b, (
                f"{first!r} and {second!r} hold identical values -- one tensor "
                "shared across two names would look exactly like this"
            )


@then("the field with the smallest diffusivity is sharper than the field with the largest")
def _then_diffusivities_are_honoured(
    demo: DemoRun, stepped: tuple[dict[str, ScalarField], dict[str, ScalarField]]
) -> None:
    _initial, final = stepped
    by_name = {field.name: field for field in demo.config.fields}
    gaussian = {
        name: by_name[name].diffusion_coefficient
        for name in final
        if by_name[name].initial_condition == "gaussian_blob"
        and by_name[name].diffusion_coefficient is not None
    }
    assert len(gaussian) >= 2, (
        "this check compares fields that started from the same shape; the "
        f"configuration must declare at least two gaussian_blob fields, got {sorted(gaussian)}"
    )

    sharpest = min(gaussian, key=lambda n: gaussian[n])
    smoothest = max(gaussian, key=lambda n: gaussian[n])
    assert _sharpness(final[sharpest]) > _sharpness(final[smoothest]), (
        f"{sharpest!r} (diffusivity {gaussian[sharpest]}) should stay sharper than "
        f"{smoothest!r} (diffusivity {gaussian[smoothest]}), but measured "
        f"{_sharpness(final[sharpest]):.4f} against {_sharpness(final[smoothest]):.4f}"
    )


@then("the temperature field's centre of mass has risen")
def _then_the_plume_rises(stepped: tuple[dict[str, ScalarField], dict[str, ScalarField]]) -> None:
    initial, final = stepped
    _mass, before = _mass_and_centroid_y(initial["temperature"])
    _mass, after = _mass_and_centroid_y(final["temperature"])
    assert after > before, (
        f"the buoyant field's centroid must rise; it went {before:.5f} -> {after:.5f}"
    )


@then("every other field has also been displaced from where it started")
def _then_the_others_are_carried(
    stepped: tuple[dict[str, ScalarField], dict[str, ScalarField]],
) -> None:
    """One coupling, four fields: the three non-buoyant fields declare no
    buoyancy coefficient at all, so any motion they show is the velocity
    temperature's coupling produced, carrying them.
    """
    initial, final = stepped
    for name in sorted(final):
        if name == "temperature":
            continue
        before = [float(initial[name].value_at(c)) for c in range(initial[name].mesh.num_cells)]
        after = [float(final[name].value_at(c)) for c in range(final[name].mesh.num_cells)]
        assert before != after, (
            f"{name!r} is unchanged after {_STEPPED_FRAMES} frames -- a field the "
            "flow never touched is not being carried by it"
        )


@then('it contains no "temperature", "humidity", "smoke" or "tracer" string literal')
def _then_orchestrator_is_field_agnostic(orchestrator_source: str) -> None:
    for name in _FIELDS:
        assert f'"{name}"' not in orchestrator_source, (
            f'`engine/simulation.py` contains the literal "{name}" -- an orchestrator '
            "that knows a phenomenon's name is what this stage exists to show is unnecessary"
        )
        assert f"'{name}'" not in orchestrator_source
