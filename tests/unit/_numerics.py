"""Shared building blocks for the Stage 4 numerical-scheme feature
bindings in this directory -- the `tests/unit/` counterpart to
`tests/golden/_demo.py`, and the same underscore-prefixed
"machinery, not a test module" naming.

**Why this is a helper module and not a `conftest.py` of shared
`pytest-bdd` steps.** Stage 4 Completion Criterion 6
(`docs/planning/roadmap.md`) asked for a shared step vocabulary in
`tests/golden/conftest.py`, reused rather than re-derived by every task
after. That is not reachable from here: a `conftest.py` applies only to
its own directory subtree, and every one of Stage 4's nine binding
modules lives in `tests/unit/`. Verified directly at the 2026-08-28
Stage 4 exit audit rather than reasoned about -- a `tests/unit/`
scenario using a step defined in `tests/golden/conftest.py` fails with
`StepDefinitionNotFoundError`. The criterion named a venue that could
not serve its own consumers, which is why the convention in
`tests/unit/CLAUDE.md` grew up in its place.

**What belongs here, and what deliberately does not.** This module holds
the *building blocks* a step definition is written from -- the fixture
constants, the test-only `BoundaryCondition` doubles, the independently
derived geometry helper -- never the `@given`/`@when`/`@then` definitions
themselves. Sharing a step definition would mean sharing the `_Context`
it populates, coupling nine tasks' fixture objects into one type; sharing
what a step is *built from* removes the duplication that can actually be
wrong without that coupling. Each module keeps its own `_Context`, its
own step bodies, and any double only it needs (`test_piso_pressure_
coupling.py`'s `_ZeroNormalVelocity`, `test_periodic_boundary.py`'s
`_InertLinearSolver`).

The duplication this replaced, measured at that same audit: the mesh
constants below appeared byte-identical in eight modules, with only
`extent` varying; `FixedValueCondition` in three and
`FixedGradientCondition` in four; `face_normal_velocity` in four, three
of them byte-identical. Eight copies of one fixture is not eight
independent fixtures -- it is one fixture with eight places to fix if it
is ever found degenerate, which is the opposite of what per-module
copies were meant to buy.
"""

from __future__ import annotations

from typing import Literal

from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.vector_field import VectorField

DEFAULT_ORIGIN = (0.5, -1.0)
"""Deliberately not `(0.0, 0.0)`: a trivial origin lets a scheme that
forgot to offset agree with one that didn't (`docs/practices.md`,
"Verify a conversion where its factors are distinct").
"""

DEFAULT_SPACING = (0.2, 0.3)
"""`dx != dy`, and neither is 1.0 -- so a scheme that confuses the two
axes, or that treats a face area as a cell volume, cannot pass by
coincidence.
"""


def default_mesh(extent: tuple[int, int] = (3, 2)) -> StructuredCartesianMesh:
    """The non-square, non-trivially-origined mesh every numerical-scheme
    feature in this directory is written against.

    `extent` varies per scenario (a convergence study needs more cells
    than a hand-derived flux check); the origin and spacing do not, and
    are shared precisely so that finding either of them degenerate is a
    one-line fix rather than an eight-module sweep.
    """
    return StructuredCartesianMesh(origin=DEFAULT_ORIGIN, spacing=DEFAULT_SPACING, extent=extent)


class FixedValueCondition(BoundaryCondition):
    """The Dirichlet shape: supplies a fixed face value, ignoring the
    field entirely -- the same shape `DirichletBoundaryCondition` itself
    has, kept as a double so a scheme's own wiring can be exercised
    without the real class under test standing in the way.

    A test whose *own* claim is that the real condition class is wired
    correctly must use the real one instead (`test_dirichlet_boundary.py`,
    `test_neumann_boundary.py` -- each uses a double only for the
    boundary faces its scenarios do not exercise).
    """

    def __init__(self, value: float) -> None:
        self._value = value

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._value


class FixedGradientCondition(BoundaryCondition):
    """The Neumann shape: supplies a fixed face gradient.

    Defaults to `0.0` for the common "an insulated wall this scenario
    does not care about" case -- typically the boundary faces a scenario
    does *not* exercise, so that the one it does exercise is the only
    thing that can move the result. Where a scenario's claim is about the
    gradient's numeric value, pass a nonzero one: a zero-gradient result
    is also what a boundary wired to nothing at all would silently
    produce (Stage 4 Completion Criterion 4's own Neumann bullet).

    Passing a nonzero gradient also proves the opposite where that is the
    claim -- `FirstOrderUpwindAdvection` never reads this number at all
    for its own advective treatment (zero-order extrapolation reads only
    `kind`), so an advection scenario using a deliberately odd gradient
    shows the value is not what gets used. Same as
    `FixedValueCondition`: a test whose own claim is that the *real*
    condition class is wired correctly must use the real one instead.
    """

    def __init__(self, gradient: float = 0.0) -> None:
        self._gradient = gradient

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._gradient


def zero_gradient_everywhere() -> dict[str, BoundaryCondition]:
    """A zero-gradient condition on each of the four named edges -- the
    "nothing crosses any wall" fixture several scenarios need as
    background before saying something about one face in particular.
    """
    condition = FixedGradientCondition()
    return {"north": condition, "south": condition, "east": condition, "west": condition}


def west_face(mesh: StructuredCartesianMesh) -> int:
    """The first face on the mesh's west edge -- the edge every
    boundary-treatment scenario in this directory happens to pick, since
    its canonical normal `(-1, 0)` makes "inflow" and "outflow" read
    the same way in each of them.
    """
    return next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "west")


def face_normal_velocity_toward(
    mesh: StructuredCartesianMesh,
    velocity: VectorField,
    face: int,
    neighbour: int | None,
) -> float:
    """The face-normal velocity at `face`, interpolating between its
    owner and `neighbour` -- or using the owner's own velocity alone when
    `neighbour` is `None`.

    Derived here independently rather than by calling into
    `FirstOrderUpwindAdvection`, so a test's own notion of "which side is
    upstream" is not circular with the implementation under test.

    `neighbour` is a parameter rather than something this function reads
    off the mesh because a **periodic** face has no mesh-reported
    neighbour at all -- `test_periodic_boundary.py` passes
    `mesh.wrapped_neighbour_cell(face)` instead, and that difference is
    the whole point of the scenario making the call. Use
    `face_normal_velocity` below for every other case.
    """
    owner, _reported_neighbour = mesh.face_neighbours(face)
    normal_x, normal_y = mesh.face_normal(face)
    owner_x, owner_y = velocity.value_at(owner)
    if neighbour is None:
        v_x, v_y = owner_x, owner_y
    else:
        neighbour_x, neighbour_y = velocity.value_at(neighbour)
        v_x, v_y = (owner_x + neighbour_x) / 2, (owner_y + neighbour_y) / 2
    return v_x * normal_x + v_y * normal_y


def face_normal_velocity(mesh: StructuredCartesianMesh, velocity: VectorField, face: int) -> float:
    """`face_normal_velocity_toward` against whichever neighbour the mesh
    itself reports -- the ordinary case, interior or boundary.
    """
    _owner, neighbour = mesh.face_neighbours(face)
    return face_normal_velocity_toward(mesh, velocity, face, neighbour)
