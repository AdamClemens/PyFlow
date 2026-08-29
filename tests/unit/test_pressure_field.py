"""Binds `tests/features/pressure_field.feature` (TASK-032) -- Stage 5's
third task in build order. `PISO` (TASK-027, Stage 4) already performs
the solve this task's own criteria describe; these scenarios prove the
properties Stage 4's own criteria never had cause to check (constant
pressure for a divergence-free input, the null-space remedy actually
holding, pressure rejected by `step`), not a new pressure-solving
mechanism.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest
import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.configuration import load_config
from pyflow.engine import simulation
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.gradient import GreenGaussGradient
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver
from pyflow.engine.numerics.pressure_coupling import PISO
from pyflow.engine.scalar_field import PressureField
from pyflow.engine.vector_field import VectorField

from ._numerics import FixedGradientCondition, default_mesh

scenarios("pressure_field.feature")


class _ZeroNormalVelocity(BoundaryCondition):
    """Dirichlet, fixed at zero -- a closed box: every boundary
    prescribes zero normal velocity, the same fixture shape
    `test_piso_pressure_coupling.py`'s own identically-named double
    uses, for the divergent scenario's own provisional field.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


def _divergent_provisional_velocity(mesh: StructuredCartesianMesh) -> VectorField:
    # Neither axis-aligned nor uniform -- a real divergence field, not a
    # degenerate one a wrong implementation could satisfy by luck
    # (docs/practices.md, "distinct factors").
    center_x, center_y = 1.0, -0.4

    def value(x: float, y: float) -> tuple[float, float]:
        return (
            0.6 * (x - center_x) - 0.2 * (y - center_y),
            0.3 * (x - center_x) + 0.9 * (y - center_y),
        )

    return VectorField(mesh, "u_star", num_components=2, initial_value=value)


def _closed_box_boundary_conditions() -> dict[str, BoundaryCondition]:
    condition = _ZeroNormalVelocity()
    return {"north": condition, "south": condition, "east": condition, "west": condition}


# -- Fixture context -------------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    boundary_conditions: dict[str, BoundaryCondition]
    provisional_velocity: VectorField
    dt: float = 1.0
    pressure: PressureField | None = None
    corrected_velocity: VectorField | None = None
    shifted_correction: torch.Tensor | None = None
    error: Exception | None = None
    config_error: ValueError | None = None


def _piso(boundary_conditions: dict[str, BoundaryCondition]) -> PISO:
    return PISO(ConjugateGradientSolver(tolerance=1e-10, max_iterations=500), boundary_conditions)


# -- Given -------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    mesh = default_mesh(extent=(5, 4))
    return _Context(
        mesh=mesh,
        boundary_conditions=_closed_box_boundary_conditions(),
        provisional_velocity=VectorField(
            mesh, "u_star", num_components=2, initial_value=(0.0, 0.0)
        ),
    )


@given("a uniform provisional velocity field with zero-gradient boundaries on every wall")
def _given_uniform_divergence_free_velocity(ctx: _Context) -> None:
    # A uniform vector field's own divergence is exactly zero by the
    # discrete Gauss theorem's own closure identity (sum of face
    # area-weighted outward normals over any closed cell is the zero
    # vector), regardless of the field's own value -- verified directly
    # in this scenario's own `Then` step, not just assumed.
    ctx.provisional_velocity = VectorField(
        ctx.mesh, "u_star", num_components=2, initial_value=(1.3, -0.7)
    )
    condition = FixedGradientCondition(0.0)
    ctx.boundary_conditions = {
        "north": condition,
        "south": condition,
        "east": condition,
        "west": condition,
    }


@given(
    "a provisional velocity field with real interior divergence, not aligned with either mesh axis"
)
def _given_divergent_velocity(ctx: _Context) -> None:
    ctx.provisional_velocity = _divergent_provisional_velocity(ctx.mesh)
    ctx.boundary_conditions = _closed_box_boundary_conditions()


@given("a pressure field produced by a real PISO correction", target_fixture="ctx")
def _given_real_pressure_field() -> _Context:
    mesh = default_mesh(extent=(5, 4))
    boundary_conditions = _closed_box_boundary_conditions()
    provisional = _divergent_provisional_velocity(mesh)
    _corrected, pressure = _piso(boundary_conditions).correct(provisional, dt=1.0)
    # `PressureCoupling.correct`'s own abstract signature stays
    # `ScalarField` (no Stage 3 interface change) -- this assertion is
    # what actually proves `PISO`'s concrete implementation constructs
    # the narrower `PressureField`, which is what makes the "rejected by
    # step" scenario below meaningful at all.
    assert isinstance(pressure, PressureField)
    ctx = _Context(
        mesh=mesh, boundary_conditions=boundary_conditions, provisional_velocity=provisional
    )
    ctx.pressure = pressure
    return ctx


@given("a configuration prescribing a nonzero net velocity flux across all four boundaries")
def _given_incompatible_boundary_config(ctx: _Context) -> None:
    # nx=4, ny=2, dx=dy=1: north/south length 4, east/west length 2.
    # 1*4 + 0*4 + (-2)*2 + (-1)*2 = 4 - 4 - 2 = -2, nonzero -- the same
    # fixture shape `test_configuration.py`'s own net-flux rejection test
    # uses, since this is exactly the existing check TASK-019 already
    # built (`_validate_boundary_conditions_jointly`), not reimplemented
    # here.
    del ctx


# -- When ------------------------------------------------------------------


@when("the field is corrected by one PISO pass")
def _when_corrected(ctx: _Context) -> None:
    piso = PISO(
        ConjugateGradientSolver(tolerance=1e-10, max_iterations=500), ctx.boundary_conditions
    )
    corrected, pressure = piso.correct(ctx.provisional_velocity, dt=ctx.dt)
    assert isinstance(pressure, PressureField)
    ctx.corrected_velocity = corrected
    ctx.pressure = pressure


@when("a nonzero constant is added to the solved pressure field everywhere")
def _when_constant_added(ctx: _Context) -> None:
    assert ctx.pressure is not None
    shifted = PressureField(ctx.mesh, "pressure_shifted")
    shifted.values[:] = ctx.pressure.values + 7.5
    pressure_boundary_conditions = {
        name: FixedGradientCondition(0.0) for name in ("north", "south", "east", "west")
    }
    gradient_scheme = GreenGaussGradient(pressure_boundary_conditions)
    ctx.shifted_correction = ctx.provisional_velocity.values - ctx.dt * gradient_scheme.gradient(
        shifted
    )


@when("the simulation is stepped with that pressure field included among the transported fields")
def _when_stepped_with_pressure(ctx: _Context) -> None:
    assert ctx.pressure is not None
    velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    fields: dict[str, Field] = {"pressure": ctx.pressure}
    try:
        simulation.step(fields, velocity, _StubNumerics(), 0.1)  # type: ignore[arg-type]
    except simulation.PressureFieldTransportError as exc:
        ctx.error = exc


class _StubNumerics:
    """Never reached -- `step`'s own pressure guard raises before
    `numerics` is used for anything, so this only needs to exist to
    satisfy the parameter.
    """


@when("the configuration is loaded")
def _when_config_loaded(ctx: _Context, tmp_path: Path) -> None:
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
    try:
        load_config(config_file)
    except ValueError as exc:
        ctx.config_error = exc


# -- Then ------------------------------------------------------------------


@then("the solved pressure field is constant to solver tolerance")
def _then_pressure_constant(ctx: _Context) -> None:
    assert ctx.pressure is not None
    spread = float(ctx.pressure.values.max() - ctx.pressure.values.min())
    assert spread == pytest.approx(0.0, abs=1e-6), f"pressure spread {spread} is not ~0"


@then("the solved pressure field is not constant")
def _then_pressure_not_constant(ctx: _Context) -> None:
    assert ctx.pressure is not None
    spread = float(ctx.pressure.values.max() - ctx.pressure.values.min())
    assert spread > 1e-3, f"pressure spread {spread} is too close to constant"


@then(
    "the velocity correction computed from the shifted pressure field matches the original exactly"
)
def _then_shifted_correction_matches(ctx: _Context) -> None:
    assert ctx.corrected_velocity is not None
    assert ctx.shifted_correction is not None
    torch.testing.assert_close(
        ctx.shifted_correction, ctx.corrected_velocity.values, rtol=1e-9, atol=1e-9
    )


@then("a named error says pressure is not transported")
def _then_pressure_transport_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, simulation.PressureFieldTransportError)


@then("loading is rejected before any pressure solve could be attempted")
def _then_config_rejected(ctx: _Context) -> None:
    assert ctx.config_error is not None
    assert "net flux" in str(ctx.config_error)
