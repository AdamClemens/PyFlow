"""DivergenceScheme (TASK-018): computes the cell-centred divergence of
a field -- one of the three operators (with Gradient and Source) that
get an interface but no configuration field, per `docs/planning/
roadmap.md` TASK-018's design decisions.

`GreenGaussDivergence` (TASK-027, Stage 4) is the first real concrete
scheme -- built and owned by TASK-027 itself, the same reasoning
`GreenGaussGradient` (`gradient.py`) follows; see that task's own Design
decision One, `docs/planning/roadmap.md`.
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
from pyflow.engine.simulation import accumulate_flux_to_cells


class DivergenceScheme(ABC):
    """Computes the cell-centred divergence of a (typically vector) field."""

    @abstractmethod
    def divergence(self, field: Field) -> torch.Tensor:
        """`field`'s divergence at every cell centre.

        Returns a tensor of shape `(field.mesh.num_cells,)`.
        """


class UnconfiguredBoundaryFaceError(ValueError):
    """Raised when a `GreenGaussDivergence` boundary face's named edge
    has no `BoundaryCondition` in this scheme's own mapping -- the
    periodic case, mirroring `gradient.py`'s identically-named exception
    for the identical underlying reason.
    """


class IncompatibleVectorFieldError(ValueError):
    """Raised when a field's `component_shape` does not match the mesh's
    spatial dimensionality -- the same reasoning as `advection.py`'s
    `IncompatibleVelocityFieldError`, generalised to any vector field
    rather than specifically velocity, since `DivergenceScheme.divergence`
    is not velocity-specific.
    """


_SPATIAL_DIMENSIONS = 2
"""PyFlow is 2D-only for now (`docs/implementation/mvp.md`) -- see
`advection.py`'s identical constant for the full reasoning.
"""


class GreenGaussDivergence(DivergenceScheme):
    """Green-Gauss reconstruction (TASK-027): the cell-centred divergence
    is `(1/V) * sum(face_normal_velocity * face_area)` over every face of
    the cell -- the discrete Gauss theorem applied to a vector field's own
    face-normal component, exact for a linear field on PyFlow's uniform
    orthogonal MVP mesh (verified numerically before being written,
    `docs/planning/roadmap.md` TASK-027's own Context).

    Reduces to `accumulate_flux_to_cells` (TASK-040's shared Gauss-theorem
    helper) once the field's cell-centred vector values are interpolated
    to a face-normal component -- the one extra step `Advection`/
    `Diffusion` do not need, since they are face-valued already
    (TASK-027's own Design decision One, `docs/planning/roadmap.md`).

    Boundary-aware by construction, the same pattern
    `FirstOrderUpwindAdvection` establishes: a Dirichlet (`"value"`)
    condition supplies the boundary's own prescribed normal-component
    value directly (`BoundaryFaceConfig.velocity`'s own convention,
    positive outward); a Neumann (`"gradient"`) condition extrapolates
    zero-order from the owner's own normal-component velocity, the same
    convention `FirstOrderUpwindAdvection`'s own Neumann handling uses.
    """

    def __init__(self, boundary_conditions: Mapping[str, BoundaryCondition]) -> None:
        self._boundary_conditions = boundary_conditions

    def _check_field(self, field: CollocatedField[Any]) -> None:
        if field.component_shape != (_SPATIAL_DIMENSIONS,):
            raise IncompatibleVectorFieldError(
                f"field must have component_shape {(_SPATIAL_DIMENSIONS,)}, "
                f"got {field.component_shape}"
            )

    def divergence(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        self._check_field(field)
        mesh = field.mesh
        assert isinstance(mesh, StructuredCartesianMesh)

        face_normal_velocity = torch.zeros(mesh.num_faces, dtype=torch.float64)
        for face in range(mesh.num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            normal_x, normal_y = mesh.face_normal(face)
            owner_x, owner_y = field.value_at(owner)
            if neighbour is not None:
                neighbour_x, neighbour_y = field.value_at(neighbour)
                value_x, value_y = (owner_x + neighbour_x) / 2, (owner_y + neighbour_y) / 2
                face_normal_velocity[face] = value_x * normal_x + value_y * normal_y
            else:
                face_normal_velocity[face] = self._boundary_face_normal_velocity(
                    mesh, field, face, owner_x, owner_y, normal_x, normal_y
                )
        return accumulate_flux_to_cells(mesh, face_normal_velocity)

    def _boundary_face_normal_velocity(
        self,
        mesh: StructuredCartesianMesh,
        field: Field,
        face: int,
        owner_x: float,
        owner_y: float,
        normal_x: float,
        normal_y: float,
    ) -> float:
        boundary_name = mesh.boundary_face_name(face)
        assert boundary_name is not None
        condition = self._boundary_conditions.get(boundary_name)
        if condition is None:
            raise UnconfiguredBoundaryFaceError(
                f"face {face} (boundary {boundary_name!r}) has no BoundaryCondition configured"
            )
        if condition.kind == "value":
            return condition.evaluate(field, face)
        return owner_x * normal_x + owner_y * normal_y
