"""Field (TASK-014): the mesh-association, name, and copy contract every
physical quantity the engine transports shares, independent of how its
values are arranged over the mesh (collocated now, staggered later).

Deliberately carries no storage of its own. How a field's values map
onto the mesh is exactly what "collocated vs. staggered" differs on, so
it cannot live on an interface both are meant to satisfy -- see
`docs/planning/roadmap.md` TASK-014 for the full design rationale.
`CollocatedField` (`src/pyflow/engine/collocated_field.py`, TASK-015) is
where cell-centred storage, initialisation, and value access actually
live.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

from pyflow.engine.mesh import Mesh


class Field(ABC):
    """A physical quantity associated with a `Mesh`.

    Carries only what's true regardless of arrangement: which mesh a
    field belongs to, a name, and the promise of an independent copy.
    """

    def __init__(self, mesh: Mesh, name: str) -> None:
        if not name:
            raise ValueError("name must not be empty")
        self._mesh = mesh
        self._name = name

    @property
    def mesh(self) -> Mesh:
        """The `Mesh` this field is defined over, fixed at construction."""
        return self._mesh

    @property
    def name(self) -> str:
        """This field's name, fixed at construction."""
        return self._name

    @abstractmethod
    def copy(self) -> Self:
        """Return an independent copy of this field.

        Typed `Self`, not `Field`, so that e.g. `ScalarField.copy()`
        callers keep access to `ScalarField`-specific members without an
        explicit cast -- the concrete return type a subclass actually
        produces, not the abstract base's own type.
        """
