"""Binds `tests/features/neumann_boundary.feature` (TASK-029) -- Stage
4's eighth task, and its own Intent: correctness is checked in what a
real interior scheme (Advection, Diffusion) computes at a boundary face
using a real `NeumannBoundaryCondition`, not only in what `evaluate()`
returns in isolation, with a *nonzero* prescribed gradient throughout --
a zero-gradient result is also what a boundary wired to nothing at all
would silently produce. Every scenario builds the real interior scheme
and the real condition together; the only hand-written `BoundaryCondition`
double in this file (`_FixedGradientCondition`) covers the three boundary
faces the diffusion scenario doesn't exercise, not the condition under
test.

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
from pyflow.engine.numerics.boundary_condition import BoundaryCondition, NeumannBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

from ._numerics import (
    default_mesh,
    face_normal_velocity,
    west_face,
    zero_gradient_everywhere,
)

scenarios("neumann_boundary.feature")

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
    prescribed_gradient: float | None = None


# -- Given -----------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    mesh = default_mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    scalar = ScalarField(mesh, "temperature", initial_value=1.0)
    return _Context(
        mesh=mesh, scalar=scalar, velocity=velocity, boundary_conditions=zero_gradient_everywhere()
    )


@given("a boundary face")
def _given_a_boundary_face(ctx: _Context) -> None:
    ctx.target_face = west_face(ctx.mesh)


@given("a real Neumann boundary condition prescribing a nonzero gradient")
def _given_real_neumann_condition(ctx: _Context) -> None:
    # Shared by both scenarios: the diffusion scenario needs every face
    # configured (no inflow/outflow carve-out), the advection scenario
    # only ever reads "west" -- rebuilding the full mapping here is
    # correct and harmless for both.
    ctx.prescribed_gradient = -3.5
    ctx.boundary_conditions = {
        **zero_gradient_everywhere(),
        "west": NeumannBoundaryCondition(ctx.prescribed_gradient),
    }


@given("a boundary face where the flow points into the domain")
def _given_inflow_boundary(ctx: _Context) -> None:
    # west's canonical normal is (-1, 0); velocity (+1, 0) gives
    # velocity_normal = 1*(-1) = -1 -- inflow.
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.target_face = west_face(ctx.mesh)


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


@then(
    "that boundary face's flux equals the diffusion coefficient times the prescribed "
    "gradient, regardless of the owner's own value"
)
def _then_diffusion_uses_prescribed_gradient(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    assert ctx.prescribed_gradient is not None
    expected = _GAMMA * ctx.prescribed_gradient
    assert math.isclose(float(ctx.flux[ctx.target_face]), expected, abs_tol=1e-9)


@then(
    "the inflow boundary face's implied value is the interior cell's own value, "
    "not the prescribed gradient"
)
def _then_advection_extrapolates_owner(ctx: _Context) -> None:
    assert ctx.flux is not None
    assert ctx.target_face is not None
    owner, _ = ctx.mesh.face_neighbours(ctx.target_face)
    velocity_normal = face_normal_velocity(ctx.mesh, ctx.velocity, ctx.target_face)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert implied == ctx.scalar.value_at(owner)
