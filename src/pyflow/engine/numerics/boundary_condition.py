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
        return self._overrides.get(field.name, self._value)


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
