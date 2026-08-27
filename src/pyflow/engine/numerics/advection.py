"""AdvectionScheme (TASK-018): the interface computing a field's
advective flux contribution at each mesh face, given the field and the
velocity field transporting it (`docs/architecture/engine.md`'s
Advection contract: "given a field and a velocity field, produces the
advective contribution to that field's flux at each face").

`FirstOrderUpwindAdvection` (TASK-023, Stage 4) is the first real
concrete scheme -- Stage 3 Completion Criterion 1 restricted every
implementation of the six `adr/ADR-003-modular-numerical-
strategies.md` components to `tests/` only through Stage 3; Stage 4
lifts that restriction for the task that brings each component's real
MVP scheme. See `docs/planning/roadmap.md` TASK-018 for the interface's
own design rationale and TASK-023 for the concrete scheme's.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
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


class UnconfiguredBoundaryFaceError(ValueError):
    """Raised when inflow occurs at a boundary face whose named edge
    (`StructuredCartesianMesh.boundary_face_name`) has no
    `BoundaryCondition` in this scheme's own mapping -- the periodic
    case (`assemble_numerics` resolves no `BoundaryCondition` object for
    a periodic-type boundary; TASK-030's own concern, not this scheme's).

    Outflow at the same face never raises this: the upstream value is
    the owner cell's own, and the boundary condition is never consulted
    -- this fires only when the exterior value is genuinely needed and
    there is nothing to supply it, never defaulted to a plausible-
    looking value silently.
    """


class FirstOrderUpwindAdvection(AdvectionScheme):
    """First-order upwind (TASK-023): the face value is the upstream
    cell's own value, determined by the sign of the face-normal
    velocity -- unconditionally bounded, per `docs/handbook/
    numerical-methods/advection.md`. PyFlow's MVP advection scheme
    (`docs/implementation/mvp.md`).

    Boundary-aware by construction (TASK-040's own Design decision,
    `docs/planning/roadmap.md`): holds the boundary conditions it needs,
    keyed by named edge, and consults them itself rather than the
    orchestrator substituting a value into its output afterward.
    """

    def __init__(self, boundary_conditions: Mapping[str, BoundaryCondition]) -> None:
        self._boundary_conditions = boundary_conditions

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        assert isinstance(field, CollocatedField)
        mesh = field.mesh
        assert isinstance(mesh, StructuredCartesianMesh)

        result = torch.zeros(mesh.num_faces, dtype=torch.float64)
        for face in range(mesh.num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            normal_x, normal_y = mesh.face_normal(face)
            velocity_normal = self._face_normal_velocity(
                velocity, owner, neighbour, normal_x, normal_y
            )
            phi_face = self._upwind_face_value(mesh, field, face, owner, neighbour, velocity_normal)
            result[face] = velocity_normal * phi_face
        return result

    def _face_normal_velocity(
        self,
        velocity: VectorField,
        owner: int,
        neighbour: int | None,
        normal_x: float,
        normal_y: float,
    ) -> float:
        """The face-normal velocity component, interpolated to the face.

        A boundary face has only the owner's own velocity to draw on; an
        interior face averages owner and neighbour -- exact for PyFlow's
        MVP uniform mesh, where both cells are equidistant from the
        shared face.
        """
        owner_x, owner_y = velocity.value_at(owner)
        if neighbour is None:
            v_x, v_y = owner_x, owner_y
        else:
            neighbour_x, neighbour_y = velocity.value_at(neighbour)
            v_x, v_y = (owner_x + neighbour_x) / 2, (owner_y + neighbour_y) / 2
        return v_x * normal_x + v_y * normal_y

    def _upwind_face_value(
        self,
        mesh: StructuredCartesianMesh,
        field: CollocatedField[Any],
        face: int,
        owner: int,
        neighbour: int | None,
        velocity_normal: float,
    ) -> float:
        """The upstream value for `face`, per upwind's own rule: the
        actual value of whichever side the flow comes *from*.

        `velocity_normal >= 0` means flow moves along the face's
        canonical normal (owner toward neighbour, or outward for a
        boundary face) -- the owner is upstream either way. Otherwise
        the neighbour is upstream for an interior face; for a boundary
        face there is no neighbour, so the exterior value comes from
        this scheme's own boundary conditions instead (a fixed value for
        Dirichlet, or the owner's own value -- zero-order extrapolation,
        `docs/handbook/numerical-methods/boundary-conditions.md`'s own
        "typically extrapolated from the adjacent cell-centred value" --
        for Neumann). `field` is typed `CollocatedField` here, not `Field`
        -- `flux` above already narrows it before calling this helper, so
        this method doesn't need to repeat that `isinstance` check itself.
        """
        if velocity_normal >= 0:
            return float(field.value_at(owner))
        if neighbour is not None:
            return float(field.value_at(neighbour))

        boundary_name = mesh.boundary_face_name(face)
        assert boundary_name is not None
        condition = self._boundary_conditions.get(boundary_name)
        if condition is None:
            raise UnconfiguredBoundaryFaceError(
                f"face {face} (boundary {boundary_name!r}) has inflow but no "
                "BoundaryCondition is configured for it"
            )
        if condition.kind == "gradient":
            return float(field.value_at(owner))
        return condition.evaluate(field, face)
