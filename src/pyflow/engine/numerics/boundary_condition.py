"""BoundaryCondition (TASK-019): the interface for how a field behaves
at a domain edge where no neighbouring control volume supplies a flux
(`docs/architecture/engine.md`'s Boundary Condition contract: "given a
boundary face and the field's interior state, produces the face value
or gradient the interior scheme needs").

`kind` tells the caller which of the two shapes `evaluate` returns --
a prescribed value (Dirichlet) or a prescribed gradient (Neumann) --
since one condition object only ever supplies one shape and the interior
scheme needs to know which before it can use the number.
`docs/architecture/icds.md` also names a third shape (periodic, "a
wrapped-neighbour reference") that neither shape here covers; TASK-019's
own scope is deliberately just the Dirichlet/Neumann pair -- see
`docs/planning/roadmap.md` TASK-019's design decisions for why periodic
is left for whichever task builds it concretely, not modelled here
speculatively (P-016).

No concrete condition lived here through Stage 3 -- Stage 3 Completion
Criterion 1. `DirichletBoundaryCondition` (TASK-028, Stage 4) is the
first; `NeumannBoundaryCondition` (TASK-029, Stage 4) is the second.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Literal

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field


class NotABoundaryFaceError(ValueError):
    """Raised when a `BoundaryCondition` is applied to a face the mesh
    does not classify as a boundary -- the same reasoning as
    `IncompatibleVelocityFieldError` (`advection.py`): an interior face
    has a neighbour on both sides, so evaluating a boundary condition
    there is meaningless, not merely unusual.
    """


class BoundaryCondition(ABC):
    """Supplies the face value or gradient a boundary face needs, given
    a field's interior state.

    `_check_boundary_face` is provided so every implementation gets the
    rejection check for free (the same pattern `AdvectionScheme.
    _check_velocity` establishes) -- an implementation must still call
    it itself; the contract suite is what actually holds implementations
    to that.
    """

    def _check_boundary_face(self, field: Field, face: int) -> None:
        """Raise `NotABoundaryFaceError` unless `face` is a boundary
        face of `field`'s mesh.
        """
        if not field.mesh.is_boundary_face(face):
            raise NotABoundaryFaceError(f"face {face} is not a boundary face")

    @property
    @abstractmethod
    def kind(self) -> Literal["value", "gradient"]:
        """Which shape `evaluate` supplies: a prescribed value
        (Dirichlet) or a prescribed gradient (Neumann).
        """

    @abstractmethod
    def evaluate(self, field: Field, face: int) -> float:
        """The face value or gradient (per `kind`) that `field`'s
        interior scheme needs at `face`.

        Raises `NotABoundaryFaceError` if `face` is not a boundary face.
        """


class DirichletBoundaryCondition(BoundaryCondition):
    """The Dirichlet shape (TASK-028): a fixed, prescribed face value,
    independent of `field`'s own interior *state* -- the same reasoning
    `test_boundary_condition_contract.py`'s own `_FixedValueCondition`
    test double already establishes, now the real implementation.

    **`overrides` (TASK-031c, added 2026-08-29) is a per-field-name
    exception to that independence**: `evaluate` still ignores `field`'s
    own values, but reads `field.name` to pick which number to return --
    `overrides.get(field.name, value)`, so two fields transported in one
    run can see different prescribed values at the same wall (`u = U`,
    `v = 0` at a moving lid, the motivating example, but exercised
    generically -- `field.name` could name any transported field, not
    only a velocity component). Every existing call site that passes
    only `value` keeps its old, single-value behaviour unchanged:
    `overrides` defaults to empty, so `overrides.get(field.name, value)`
    always falls through to `value`.
    """

    def __init__(self, value: float, overrides: Mapping[str, float] | None = None) -> None:
        self._value = value
        self._overrides = overrides or {}

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        override = self._overrides.get(field.name)
        if override is not None:
            return override
        if isinstance(field, CollocatedField) and field.component_shape != ():
            # A *vector* field with no override of its own prescribes
            # nothing here, and `value` is `BoundaryFaceConfig.
            # scalar_value` -- a transported scalar's boundary value,
            # which is not a velocity and must not be returned as one
            # (TASK-052, Stage 9). `0.0` is the honest answer: a
            # Dirichlet velocity boundary that names no normal component
            # is a no-penetration wall, which is what every
            # configuration in this repository relies on.
            #
            # **Found by a test, not by reading.** The scenario
            # `boundary_velocity.feature`'s "The same boundary without a
            # prescribed normal velocity transports nothing through
            # itself" failed against a fixture whose scalar boundary
            # value was `3.0`, because the wall then resolved to a
            # normal velocity of 3.0. Every shipped demo leaves
            # `scalar_value` at `0.0`, so the walls were impermeable by
            # coincidence of the defaults rather than by anything the
            # configuration said -- the same shape of accident
            # `GreenGaussDivergence`'s own pre-TASK-052 behaviour had.
            return 0.0
        return self._value


class NeumannBoundaryCondition(BoundaryCondition):
    """The Neumann shape (TASK-029): a fixed, prescribed face gradient,
    independent of `field`'s own interior *state* -- the same reasoning
    `DirichletBoundaryCondition` states, and
    `test_boundary_condition_contract.py`'s own `_FixedGradientCondition`
    test double already established, now the real implementation.

    **`overrides` (TASK-031c, added 2026-08-29) is `DirichletBoundaryCondition.
    overrides`'s exact Neumann mirror** -- same reasoning throughout.
    """

    def __init__(self, gradient: float, overrides: Mapping[str, float] | None = None) -> None:
        self._gradient = gradient
        self._overrides = overrides or {}

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._overrides.get(field.name, self._gradient)


def boundary_normal_velocity(
    condition: BoundaryCondition,
    velocity: Field,
    face: int,
    owner_normal_velocity: float,
) -> float:
    """The face-normal velocity **transporting** material across a genuine
    boundary face (TASK-052, Stage 9) -- the one source every operator
    that needs that number resolves it through.

    `velocity` is the whole velocity field, and `face` the boundary face;
    `owner_normal_velocity` is the owning cell's own velocity projected
    onto the face normal, which is what a gradient face extrapolates.

    The rule, and it is the one `docs/handbook/numerical-methods/
    boundary-conditions.md` already states for every boundary quantity
    ("the flux must instead be determined by the boundary condition
    itself"):

    - A **value** (Dirichlet) face prescribes its own normal velocity,
      and the condition supplies it. For every configuration this
      repository ships that resolves to `0.0` -- a no-penetration wall.
    - A **gradient** (Neumann) face prescribes none, by definition: the
      normal velocity is whatever the interior brings to it,
      extrapolated zero-order. This is how an outlet is expressed, and
      it is the one case where reading the owner cell is correct.

    **Exists because two operators disagreed about it for sixteen days.**
    This is exactly what `GreenGaussDivergence` already did, extracted
    unchanged so that `FirstOrderUpwindAdvection` does it too. Advection
    used the owner cell's own velocity instead and transported straight
    through solid walls -- 14.27% of a purely advected tracer lost in
    400 steps on a shipped demo (`docs/planning/roadmap.md` Stage 9,
    Completion Criterion 1). Neither operator decides this for itself any
    more, which is what makes "they agree" structural rather than a
    coincidence of whichever fixture is in front of them.

    **Deliberately per-face, not per-named-edge.** A first version of
    this took a `Mapping[str, float | None]` built from
    `BoundaryFaceConfig.velocity` -- one number per named edge -- and was
    abandoned when `tests/unit/numerics/test_divergence_contract.py`'s
    own linear-field exactness test could not be expressed through it: a
    linear velocity field's normal component varies *along* an edge, so
    a per-edge scalar cannot carry it, and a future non-uniform inlet (a
    parabolic channel profile) would have the same problem.
    `BoundaryCondition.evaluate` is already per-face and already open to
    a user-supplied implementation, so it is the right shape; that it is
    also what divergence was already calling means this change adds no
    new mechanism at all. See `docs/planning/roadmap.md` TASK-052's own
    Design decisions.

    Deliberately raises nothing: an unconfigured face is each calling
    module's own exception vocabulary (`advection.py` and `divergence.py`
    each own an `UnconfiguredBoundaryFaceError` of their own, for
    reasons their docstrings record), so a caller checks for a missing
    condition before reaching here.
    """
    if condition.kind == "gradient":
        return owner_normal_velocity
    return condition.evaluate(velocity, face)
