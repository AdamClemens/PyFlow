"""Binds `tests/features/dirichlet_boundary.feature` (TASK-028) -- Stage
4's seventh task, and its own Intent: correctness is checked in what a
real interior scheme (Advection, Diffusion) computes at a boundary face
using a real `DirichletBoundaryCondition`, not only in what `evaluate()`
returns in isolation. Every scenario builds the real interior scheme and
the real condition together; the only hand-written `BoundaryCondition`
double in this file (`_FixedGradientCondition`) covers the three
boundary faces neither scenario exercises, not the condition under test.

Not a golden demo -- no config file under `examples/golden-demos/`, no
CLI run. Lives here, not under `tests/golden/`, per this directory's own
scope: isolated logic, no process boundary (`tests/unit/CLAUDE.md`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.boundary_condition import BoundaryCondition, DirichletBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

from ._numerics import (
    default_mesh,
    face_normal_velocity,
    west_face,
    zero_gradient_everywhere,
)

scenarios("dirichlet_boundary.feature")

_GAMMA = 2.0
"""The diffusion coefficient used in this file's own diffusion scenario
-- deliberately not `1.0`, the same reasoning
`test_central_difference_diffusion.py`'s own identically-named constant
states.
"""


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    scalar: ScalarField
    velocity: VectorField
    boundary_conditions: dict[str, BoundaryCondition]
    flux: torch.Tensor | None = None
    target_face: int | None = None
    prescribed_value: float | None = None


# -- Given -----------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    mesh = default_mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    scalar = ScalarField(mesh, "temperature", initial_value=1.0)
    return _Context(
        mesh=mesh, scalar=scalar, velocity=velocity, boundary_conditions=zero_gradient_everywhere()
    )


@given("a boundary face where the flow points into the domain")
def _given_inflow_boundary(ctx: _Context) -> None:
    # west's canonical normal is (-1, 0); velocity (+1, 0) gives
    # velocity_normal = 1*(-1) = -1 -- inflow.
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.target_face = west_face(ctx.mesh)


@given(
    "a real Dirichlet boundary condition prescribing a value distinct from the "
    "interior cell's own value"
)
def _given_real_dirichlet_for_advection(ctx: _Context) -> None:
    ctx.prescribed_value = 42.0
    ctx.boundary_conditions = {"west": DirichletBoundaryCondition(ctx.prescribed_value)}


@given("a boundary face")
def _given_a_boundary_face(ctx: _Context) -> None:
    ctx.target_face = west_face(ctx.mesh)


@given(
    "a real Dirichlet boundary condition prescribing a value distinct from the "
    "owner cell's own value"
)
def _given_real_dirichlet_for_diffusion(ctx: _Context) -> None:
    ctx.prescribed_value = 9.5
    ctx.boundary_conditions = {
        **zero_gradient_everywhere(),
        "west": DirichletBoundaryCondition(ctx.prescribed_value),
    }


# -- When ------------------------------------------------------------------


@when("the advective flux is computed using this condition")
def _when_advective_flux(ctx: _Context) -> None:
    scheme = FirstOrderUpwindAdvection(ctx.boundary_conditions, {})
    ctx.flux = scheme.flux(ctx.scalar, ctx.velocity)


@when("the diffusive flux is computed using this condition")
def _when_diffusive_flux(ctx: _Context) -> None:
    scheme = CentralDifferenceDiffusion(ctx.boundary_conditions, {}, _GAMMA)
    ctx.flux = scheme.flux(ctx.scalar)


# -- Then ------------------------------------------------------------------


@then("the inflow boundary face's implied value is exactly the condition's prescribed value")
def _then_inflow_uses_prescribed_value(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_value is not None
    velocity_normal = face_normal_velocity(ctx.mesh, ctx.velocity, ctx.target_face)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert implied == ctx.prescribed_value


@then(
    "that boundary face's flux equals the diffusion coefficient times the prescribed value "
    "minus the owner's own value, divided by the owner-to-face distance"
)
def _then_diffusion_uses_prescribed_value(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_value is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    owner_value = ctx.scalar.value_at(owner)
    distance = ctx.mesh.face_centroid_distance(ctx.target_face)
    expected = _GAMMA * (ctx.prescribed_value - owner_value) / distance
    assert math.isclose(float(ctx.flux[ctx.target_face]), expected, abs_tol=1e-9)
