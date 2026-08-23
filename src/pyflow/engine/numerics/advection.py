"""AdvectionScheme (TASK-018): the interface computing a field's
advective flux contribution at each mesh face, given the field and the
velocity field transporting it (`docs/architecture/engine.md`'s
Advection contract: "given a field and a velocity field, produces the
advective contribution to that field's flux at each face").

No concrete scheme lives here -- Stage 3 Completion Criterion 1 requires
every implementation of the six `adr/ADR-003-modular-numerical-
strategies.md` components to live under `tests/` until Stage 4. See
`docs/planning/roadmap.md` TASK-018 for the full design rationale and
this module's acceptance criteria.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from pyflow.engine.field import Field
from pyflow.engine.vector_field import VectorField

_SPATIAL_DIMENSIONS = 2
"""PyFlow is 2D-only for now (`docs/implementation/mvp.md`) -- every
mesh accessor already assumes it (`Mesh.cell_centroid -> tuple[float,
float]`). Named here, not repeated as a bare `2`, so a future 3D mesh
(`docs/implementation/upgrade-paths.md` "Mesh") has one place to change.
"""


class IncompatibleVelocityFieldError(ValueError):
    """Raised when a velocity field's `component_shape` does not match
    the mesh's spatial dimensionality -- the same reasoning as
    `InvalidMeshEntityError` (`mesh.py`): an implementation that didn't
    check this would either crash confusingly deep inside its own
    arithmetic or, worse, silently drop/zero-fill a component and
    produce a plausible wrong answer.
    """


class AdvectionScheme(ABC):
    """Computes a transported field's advective flux at each mesh face.

    `_check_velocity` is provided so every implementation gets the
    rejection check for free (the same pattern `Mesh._check_cell`
    establishes) -- an implementation must still call it itself; the
    contract suite (`tests/unit/numerics/test_advection_contract.py`)
    is what actually holds implementations to that.
    """

    def _check_velocity(self, velocity: VectorField) -> None:
        """Raise `IncompatibleVelocityFieldError` unless `velocity` has
        exactly one component per spatial dimension.
        """
        if velocity.component_shape != (_SPATIAL_DIMENSIONS,):
            raise IncompatibleVelocityFieldError(
                f"velocity field must have component_shape "
                f"{(_SPATIAL_DIMENSIONS,)}, got {velocity.component_shape}"
            )

    @abstractmethod
    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        """The advective contribution to `field`'s flux at each of its
        mesh's faces, transported by `velocity`.

        Returns a tensor of shape `(field.mesh.num_faces,)`.

        Raises `IncompatibleVelocityFieldError` if `velocity`'s
        `component_shape` doesn't match the mesh's dimensionality.
        """
