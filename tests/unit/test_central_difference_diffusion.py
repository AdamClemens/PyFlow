"""Binds `tests/features/central_difference_diffusion.feature` (TASK-024)
-- Stage 4's third real numerical scheme, and Stage 4 Completion
Criterion 4's own claim for it: second-order accuracy under mesh
refinement, and (a distinct claim) conservation under zero-flux
boundaries.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import (
    CentralDifferenceDiffusion,
    UnconfiguredBoundaryFaceError,
)
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import accumulate_flux_to_cells

scenarios("central_difference_diffusion.feature")

_GAMMA = 2.0
"""The diffusion coefficient used throughout this file -- deliberately
not `1.0`, so a formula that forgot to multiply by it would still fail a
`Then` assertion instead of coincidentally passing.
"""


# -- Test-only boundary conditions ------------------------------------


class _FixedValueCondition(BoundaryCondition):
    """The Dirichlet shape: supplies a fixed face value."""

    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._value


class _FixedGradientCondition(BoundaryCondition):
    """The Neumann shape: supplies a fixed face gradient."""

    def __init__(self, gradient: float) -> None:
        self._gradient = gradient

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._gradient


# -- Fixture context -----------------------------------------------------


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    scalar: ScalarField
    boundary_conditions: dict[str, BoundaryCondition]
    flux: torch.Tensor | None = None
    error: Exception | None = None
    target_face: int | None = None
    prescribed_value: float | None = None
    prescribed_gradient: float | None = None
    history: list[torch.Tensor] | None = None
    dt: float | None = None
    resolutions: list[int] = field(default_factory=list)
    errors: list[float] = field(default_factory=list)
    spacings: list[float] = field(default_factory=list)


def _mesh() -> StructuredCartesianMesh:
    # Non-"nice" origin/spacing and a non-square extent, matching every
    # other contract suite's fixture in this repository.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(3, 2))


def _zero_gradient_everywhere() -> dict[str, BoundaryCondition]:
    condition = _FixedGradientCondition(0.0)
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def _west_face(mesh: StructuredCartesianMesh) -> int:
    return next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "west")


def _run_flux(ctx: _Context) -> None:
    scheme = CentralDifferenceDiffusion(ctx.boundary_conditions, _GAMMA)
    try:
        ctx.flux = scheme.flux(ctx.scalar)
    except UnconfiguredBoundaryFaceError as exc:
        ctx.error = exc


def _is_strictly_interior_cell(mesh: StructuredCartesianMesh, cell: int) -> bool:
    """`True` if none of `cell`'s own faces touch the domain boundary.

    Such a cell's own discrete Laplacian estimate depends only on the
    interior central-difference formula -- never on the boundary
    formula, whose own local truncation order the handbook doesn't
    claim (`docs/handbook/numerical-methods/diffusion.md` only claims
    second order for the *interior* formula on a uniform orthogonal
    mesh). Restricting the convergence measurement to these cells is
    what makes the scenario test exactly what's claimed, not a stronger,
    unclaimed statement about boundary-cell accuracy too.
    """
    return not any(mesh.is_boundary_face(face) for face in mesh.cell_faces(cell))


def _laplacian_eigenfunction(x: float, y: float) -> float:
    return math.sin(math.pi * x) * math.sin(math.pi * y)


def _exact_laplacian(x: float, y: float) -> float:
    return _GAMMA * (-2 * math.pi**2) * _laplacian_eigenfunction(x, y)


# -- Given -----------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    mesh = _mesh()
    scalar = ScalarField(mesh, "temperature", initial_value=0.0)
    return _Context(mesh=mesh, scalar=scalar, boundary_conditions=_zero_gradient_everywhere())


@given("a non-uniform field with known values at every cell")
def _given_non_uniform_field(ctx: _Context) -> None:
    values = [5.0, 1.0, 8.0, 2.0, 9.0, 3.0]
    for cell, value in enumerate(values):
        ctx.scalar.set_value_at(cell, value)


@given("a boundary face whose condition prescribes a fixed value")
def _given_dirichlet_boundary(ctx: _Context) -> None:
    ctx.prescribed_value = 7.5
    for cell in range(ctx.mesh.num_cells):
        ctx.scalar.set_value_at(cell, 4.0)
    ctx.boundary_conditions = {
        **_zero_gradient_everywhere(),
        "west": _FixedValueCondition(ctx.prescribed_value),
    }
    ctx.target_face = _west_face(ctx.mesh)


@given("a boundary face whose condition prescribes a gradient")
def _given_neumann_boundary(ctx: _Context) -> None:
    ctx.prescribed_gradient = -3.5
    for cell in range(ctx.mesh.num_cells):
        ctx.scalar.set_value_at(cell, 4.0)
    ctx.boundary_conditions = {
        **_zero_gradient_everywhere(),
        "west": _FixedGradientCondition(ctx.prescribed_gradient),
    }
    ctx.target_face = _west_face(ctx.mesh)


@given("a boundary face with no configured condition at all")
def _given_no_condition(ctx: _Context) -> None:
    ctx.boundary_conditions = {}


@given(
    "a smooth field with a known exact Laplacian, at increasing mesh resolutions",
    target_fixture="ctx",
)
def _given_convergence_setup() -> _Context:
    mesh = _mesh()
    scalar = ScalarField(mesh, "temperature")
    return _Context(
        mesh=mesh,
        scalar=scalar,
        boundary_conditions=_zero_gradient_everywhere(),
        resolutions=[8, 16, 32],
    )


@given("a domain whose boundary conditions all prescribe a zero gradient", target_fixture="ctx")
def _given_zero_flux_boundaries() -> _Context:
    mesh = StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(4, 3))
    scalar = ScalarField(mesh, "temperature")
    ctx = _Context(mesh=mesh, scalar=scalar, boundary_conditions=_zero_gradient_everywhere())
    return ctx


@given("interior cells with a non-uniform field")
def _given_non_uniform_interior_field(ctx: _Context) -> None:
    initial_values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0, 5.0, 3.0, 5.0, 8.0]
    for cell, value in enumerate(initial_values):
        ctx.scalar.set_value_at(cell, value)
    ctx.history = [ctx.scalar.values.clone()]


# -- When ------------------------------------------------------------------


@when("the diffusive flux is computed")
def _when_flux_computed(ctx: _Context) -> None:
    _run_flux(ctx)


@when("the discrete Laplacian is measured at each resolution")
def _when_measure_convergence(ctx: _Context) -> None:
    for n in ctx.resolutions:
        mesh = StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0 / n, 1.0 / n), extent=(n, n))
        field_values = ScalarField(mesh, "temperature")
        for cell in range(mesh.num_cells):
            x, y = mesh.cell_centroid(cell)
            field_values.set_value_at(cell, _laplacian_eigenfunction(x, y))

        condition = _FixedValueCondition(0.0)
        boundary_conditions = {
            "north": condition,
            "south": condition,
            "east": condition,
            "west": condition,
        }
        scheme = CentralDifferenceDiffusion(boundary_conditions, _GAMMA)
        discrete = accumulate_flux_to_cells(mesh, scheme.flux(field_values))

        max_error = 0.0
        for cell in range(mesh.num_cells):
            if not _is_strictly_interior_cell(mesh, cell):
                continue
            x, y = mesh.cell_centroid(cell)
            error = abs(float(discrete[cell]) - _exact_laplacian(x, y))
            max_error = max(max_error, error)

        ctx.errors.append(max_error)
        ctx.spacings.append(1.0 / n)


@when("the field is advanced for many timesteps")
def _when_advanced_many(ctx: _Context) -> None:
    ctx.dt = 0.001
    _advance(ctx, steps=20)


def _advance(ctx: _Context, steps: int) -> None:
    assert ctx.dt is not None
    assert ctx.history is not None
    scheme = CentralDifferenceDiffusion(ctx.boundary_conditions, _GAMMA)
    scalar = ctx.scalar
    for _ in range(steps):
        flux = scheme.flux(scalar)
        derivative = accumulate_flux_to_cells(ctx.mesh, flux)
        advanced = scalar.copy()
        advanced.values[:] = scalar.values + ctx.dt * derivative
        scalar = advanced
        ctx.history.append(scalar.values.clone())
    ctx.scalar = scalar


# -- Then ------------------------------------------------------------------


@then(
    "every interior face's flux equals the diffusion coefficient times the neighbouring "
    "cells' value difference divided by their centroid distance"
)
def _then_interior_formula(ctx: _Context) -> None:
    assert ctx.flux is not None
    for face in range(ctx.mesh.num_faces):
        owner, neighbour = ctx.mesh.face_neighbours(face)
        if neighbour is None:
            continue
        owner_value = ctx.scalar.value_at(owner)
        neighbour_value = ctx.scalar.value_at(neighbour)
        distance = ctx.mesh.face_centroid_distance(face)
        expected = _GAMMA * (neighbour_value - owner_value) / distance
        assert math.isclose(float(ctx.flux[face]), expected, abs_tol=1e-9)


@then(
    "that boundary face's flux equals the diffusion coefficient times the prescribed value "
    "minus the owner's own value, divided by the owner-to-face distance"
)
def _then_dirichlet_formula(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_value is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    owner_value = ctx.scalar.value_at(owner)
    distance = ctx.mesh.face_centroid_distance(ctx.target_face)
    expected = _GAMMA * (ctx.prescribed_value - owner_value) / distance
    assert math.isclose(float(ctx.flux[ctx.target_face]), expected, abs_tol=1e-9)


@then(
    "that boundary face's flux equals the diffusion coefficient times the prescribed "
    "gradient, regardless of the owner's own value"
)
def _then_neumann_formula(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_gradient is not None
    expected = _GAMMA * ctx.prescribed_gradient
    assert math.isclose(float(ctx.flux[ctx.target_face]), expected, abs_tol=1e-9)


@then("an UnconfiguredBoundaryFaceError is raised")
def _then_unconfigured_error(ctx: _Context) -> None:
    assert isinstance(ctx.error, UnconfiguredBoundaryFaceError)


@then("the observed convergence order is close to two")
def _then_order_close_to_two(ctx: _Context) -> None:
    assert len(ctx.errors) >= 3
    log_h = [math.log(h) for h in ctx.spacings]
    log_e = [math.log(e) for e in ctx.errors]
    n = len(log_h)
    mean_h = sum(log_h) / n
    mean_e = sum(log_e) / n
    numerator = sum((log_h[i] - mean_h) * (log_e[i] - mean_e) for i in range(n))
    denominator = sum((log_h[i] - mean_h) ** 2 for i in range(n))
    order = numerator / denominator
    assert 1.8 <= order <= 2.2, f"expected convergence order close to 2, got {order}"


@then("the field's total summed over every cell is unchanged to floating-point tolerance")
def _then_total_conserved(ctx: _Context) -> None:
    assert ctx.history is not None
    initial_total = float(ctx.history[0].sum())
    final_total = float(ctx.history[-1].sum())
    assert abs(final_total - initial_total) < 1e-9, (
        f"total drifted from {initial_total} to {final_total}"
    )
