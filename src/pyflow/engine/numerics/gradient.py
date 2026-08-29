"""GradientScheme (TASK-018): computes the cell-centred gradient of a
field -- one of the three operators (with Divergence and Source) that
jointly compute `docs/architecture/engine.md`'s Flux layer alongside
Advection/Diffusion, but get no configuration field of their own:
`adr/ADR-003-modular-numerical-strategies.md` names exactly six
configuration-selected components and Gradient is not one of them, per
`docs/planning/roadmap.md` TASK-018's design decisions.

`GreenGaussGradient` (TASK-027, Stage 4) is the first real concrete
scheme -- built and owned by TASK-027 itself, not resolved through
`assemble_numerics` (neither Gradient nor Divergence is one of the six
`adr/ADR-003` components, so neither has a registry); see that task's
own Design decision One, `docs/planning/roadmap.md`, for why it owns
building this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.simulation import accumulate_flux_to_cells

_SPATIAL_DIMENSIONS = 2
"""PyFlow is 2D-only for now (`docs/implementation/mvp.md`) -- see
`advection.py`'s identical constant for the full reasoning.
"""


class GradientScheme(ABC):
    """Computes the cell-centred gradient of a (typically scalar) field."""

    @abstractmethod
    def gradient(self, field: Field) -> torch.Tensor:
        """`field`'s gradient at every cell centre.

        Returns a tensor of shape `(field.mesh.num_cells,
        _SPATIAL_DIMENSIONS)` -- one gradient vector per cell.
        """


class UnconfiguredBoundaryFaceError(ValueError):
    """Raised when a `GreenGaussGradient` boundary face's named edge
    (`StructuredCartesianMesh.boundary_face_name`) has no
    `BoundaryCondition` in this scheme's own mapping -- the periodic
    case, mirroring `advection.py`/`diffusion.py`'s identically-named
    exceptions for the identical underlying reason (each numerics
    interface owns its own exception vocabulary).
    """


class GreenGaussGradient(GradientScheme):
    """Green-Gauss reconstruction (TASK-027): the cell-centred gradient
    is `(1/V) * sum(face_value * face_area * outward_normal)` over every
    face of the cell -- the discrete Gauss theorem applied to a scalar
    field's own face values, exact for a linear field on PyFlow's uniform
    orthogonal MVP mesh (verified numerically before being written,
    `docs/planning/roadmap.md` TASK-027's own Context).

    Reuses `accumulate_flux_to_cells` (TASK-040's shared Gauss-theorem
    helper) once per spatial component -- `face_value * normal_component`
    is exactly the per-face quantity that helper already reduces to
    cells, the same reasoning `GreenGaussDivergence` (`divergence.py`)
    applies to its own face-normal velocity.

    Boundary-aware by construction, the same pattern
    `CentralDifferenceDiffusion`/`FirstOrderUpwindAdvection` establish: a
    Dirichlet (`"value"`) condition supplies the boundary's own face
    value directly; a Neumann (`"gradient"`) condition extrapolates
    linearly from the owner's own value using `Mesh.face_centroid_distance`
    (`owner_value + gradient * distance`) -- exact for a linear field,
    and reduces to zero-order extrapolation for a zero-gradient condition
    (the impermeable-wall assumption `PISO` uses for pressure).

    **Periodic-aware the same way `CentralDifferenceDiffusion` is
    (TASK-030), added by TASK-034 (Stage 5) once `PISO` needed it: a
    fully periodic domain's own pressure Poisson solve reaches every
    boundary face through this class, and until this addition it had no
    periodic case at all -- `UnconfiguredBoundaryFaceError` unconditionally,
    the same gap `divergence.py`'s own entry describes.** At a face named
    in `periodic_pairs`, `gradient` substitutes `mesh.wrapped_neighbour_cell`
    for `neighbour` before falling through to the ordinary interior-face
    averaging -- no distance term to double here, unlike diffusion's own
    central-difference formula, since Green-Gauss face averaging never
    divides by distance; `boundary_conditions` is never consulted for a
    periodic face.
    """

    def __init__(
        self,
        boundary_conditions: Mapping[str, BoundaryCondition],
        periodic_pairs: Mapping[str, str],
    ) -> None:
        self._boundary_conditions = boundary_conditions
        self._periodic_pairs = periodic_pairs

    def gradient(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        mesh = field.mesh
        assert isinstance(mesh, StructuredCartesianMesh)

        face_values = torch.zeros(mesh.num_faces, dtype=torch.float64)
        normal_x = torch.zeros(mesh.num_faces, dtype=torch.float64)
        normal_y = torch.zeros(mesh.num_faces, dtype=torch.float64)
        for face in range(mesh.num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            normal_x[face], normal_y[face] = mesh.face_normal(face)
            owner_value = float(field.value_at(owner))
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
            if neighbour is not None:
                neighbour_value = float(field.value_at(neighbour))
                face_values[face] = (owner_value + neighbour_value) / 2
            else:
                face_values[face] = self._boundary_face_value(mesh, field, face, owner_value)

        gradient = torch.zeros((mesh.num_cells, _SPATIAL_DIMENSIONS), dtype=torch.float64)
        gradient[:, 0] = accumulate_flux_to_cells(mesh, face_values * normal_x)
        gradient[:, 1] = accumulate_flux_to_cells(mesh, face_values * normal_y)
        return gradient

    def _boundary_face_value(
        self,
        mesh: StructuredCartesianMesh,
        field: Field,
        face: int,
        owner_value: float,
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
        distance = mesh.face_centroid_distance(face)
        return owner_value + condition.evaluate(field, face) * distance
