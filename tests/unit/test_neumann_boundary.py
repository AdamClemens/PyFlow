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
from typing import Literal

import torch
from pytest_bdd import given, scenarios, then, when

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.boundary_condition import BoundaryCondition, NeumannBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

scenarios("neumann_boundary.feature")

_GAMMA = 2.0
"""The diffusion coefficient used in this file's own diffusion scenario
-- deliberately not `1.0`, the same reasoning
`test_central_difference_diffusion.py`'s own identically-named constant
states.
"""


class _FixedGradientCondition(BoundaryCondition):
    """The Neumann shape, for the three boundary faces the diffusion
    scenario in this file doesn't exercise -- not the class under test.
    """

    def __init__(self, gradient: float) -> None:
        self._gradient = gradient

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._gradient


@dataclass
class _Context:
    mesh: StructuredCartesianMesh
    scalar: ScalarField
    velocity: VectorField
    boundary_conditions: dict[str, BoundaryCondition]
    flux: torch.Tensor | None = None
    target_face: int | None = None
    prescribed_gradient: float | None = None


def _mesh() -> StructuredCartesianMesh:
    # Non-"nice" origin/spacing and a non-square extent, matching every
    # other contract suite's fixture in this repository.
    return StructuredCartesianMesh(origin=(0.5, -1.0), spacing=(0.2, 0.3), extent=(3, 2))


def _zero_gradient_everywhere() -> dict[str, BoundaryCondition]:
    condition = _FixedGradientCondition(0.0)
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def _west_face(mesh: StructuredCartesianMesh) -> int:
    return next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "west")


def _face_normal_velocity(ctx: _Context, face: int) -> float:
    """Independently derived, not calling into `FirstOrderUpwindAdvection`
    itself -- the same reasoning `test_first_order_upwind_advection.py`'s
    own identically-named helper states, so this test's own notion of
    "upstream" isn't circular with the implementation under test.
    """
    owner, neighbour = ctx.mesh.face_neighbours(face)
    normal_x, normal_y = ctx.mesh.face_normal(face)
    owner_x, owner_y = ctx.velocity.value_at(owner)
    if neighbour is None:
        v_x, v_y = owner_x, owner_y
    else:
        neighbour_x, neighbour_y = ctx.velocity.value_at(neighbour)
        v_x, v_y = (owner_x + neighbour_x) / 2, (owner_y + neighbour_y) / 2
    return v_x * normal_x + v_y * normal_y


# -- Given -----------------------------------------------------------------


@given("a small, non-square, non-trivially-origined mesh", target_fixture="ctx")
def _given_default_mesh() -> _Context:
    mesh = _mesh()
    velocity = VectorField(mesh, "velocity", num_components=2, initial_value=(0.0, 0.0))
    scalar = ScalarField(mesh, "temperature", initial_value=1.0)
    return _Context(
        mesh=mesh, scalar=scalar, velocity=velocity, boundary_conditions=_zero_gradient_everywhere()
    )


@given("a boundary face")
def _given_a_boundary_face(ctx: _Context) -> None:
    ctx.target_face = _west_face(ctx.mesh)


@given("a real Neumann boundary condition prescribing a nonzero gradient")
def _given_real_neumann_condition(ctx: _Context) -> None:
    # Shared by both scenarios: the diffusion scenario needs every face
    # configured (no inflow/outflow carve-out), the advection scenario
    # only ever reads "west" -- rebuilding the full mapping here is
    # correct and harmless for both.
    ctx.prescribed_gradient = -3.5
    ctx.boundary_conditions = {
        **_zero_gradient_everywhere(),
        "west": NeumannBoundaryCondition(ctx.prescribed_gradient),
    }


@given("a boundary face where the flow points into the domain")
def _given_inflow_boundary(ctx: _Context) -> None:
    # west's canonical normal is (-1, 0); velocity (+1, 0) gives
    # velocity_normal = 1*(-1) = -1 -- inflow.
    ctx.velocity = VectorField(ctx.mesh, "velocity", num_components=2, initial_value=(1.0, 0.0))
    ctx.target_face = _west_face(ctx.mesh)


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
    velocity_normal = _face_normal_velocity(ctx, ctx.target_face)
    implied = float(ctx.flux[ctx.target_face]) / velocity_normal
    assert implied == ctx.scalar.value_at(owner)
