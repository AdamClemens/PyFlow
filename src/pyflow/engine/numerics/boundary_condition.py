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

No concrete condition lives here -- Stage 3 Completion Criterion 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
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
