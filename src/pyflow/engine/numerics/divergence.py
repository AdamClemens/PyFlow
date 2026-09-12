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
from dataclasses import dataclass
from typing import Any

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import (
    BoundaryCondition,
    boundary_normal_velocity,
)
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

    **Periodic-aware the same way `CentralDifferenceDiffusion` is
    (TASK-030), added by TASK-034 (Stage 5) once `PISO` needed it.** A
    fully periodic domain's own null test (`docs/planning/roadmap.md`
    Stage 5 Completion Criterion 4) routes a real, already divergence-free
    velocity field through `PISO`'s own pressure solve, which measures
    divergence through this class at every boundary face -- until this
    addition, unconditionally `UnconfiguredBoundaryFaceError`, since a
    periodic face is never given a `BoundaryCondition` object at all
    (`assemble_numerics`'s own `periodic_pairs`/`boundary_conditions`
    split). **Verified directly before being trusted, not assumed**: a
    uniform, non-axis-aligned velocity field on a genuinely periodic mesh
    measures exactly `0.0` divergence at every cell through this path
    (float-exact, not merely small), while a non-uniform field on the same
    mesh still measures a real nonzero divergence -- confirming the wrap
    reads real neighbour values rather than silently zeroing every
    boundary face's own contribution. At a face named in `periodic_pairs`,
    `divergence` substitutes `mesh.wrapped_neighbour_cell` for `neighbour`
    before falling through to the ordinary interior-face averaging;
    `boundary_conditions` is never consulted for a periodic face.
    """

    def __init__(
        self,
        boundary_conditions: Mapping[str, BoundaryCondition],
        periodic_pairs: Mapping[str, str],
    ) -> None:
        self._boundary_conditions = boundary_conditions
        self._periodic_pairs = periodic_pairs
        self._cached_geometry_mesh: StructuredCartesianMesh | None = None
        self._cached_geometry: _FaceGeometry | None = None

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
        geometry = self._face_geometry(mesh)

        values = field.values
        v_owner = values[geometry.owner_ids]
        v_neighbour = values[geometry.neighbour_ids]  # placeholder=owner at boundary
        v_avg = (v_owner + v_neighbour) / 2
        face_normal_velocity = v_avg[:, 0] * geometry.normal_x + v_avg[:, 1] * geometry.normal_y

        for face in geometry.boundary_faces:
            face_normal_velocity[face] = self._boundary_face_normal_velocity(
                field,
                face,
                geometry.boundary_names[face],
                float(v_owner[face, 0]),
                float(v_owner[face, 1]),
                float(geometry.normal_x[face]),
                float(geometry.normal_y[face]),
            )
        return accumulate_flux_to_cells(mesh, face_normal_velocity)

    def _face_geometry(self, mesh: StructuredCartesianMesh) -> _FaceGeometry:
        """Built once per distinct `mesh` and cached for the rest of this
        instance's own lifetime -- the same pattern
        `GreenGaussGradient._face_geometry` (`gradient.py`) uses, for the
        same reason. See that method's own docstring for why interior/
        periodic faces are split from genuine boundary faces, and why no
        `resolved` mask is needed (every boundary face's entry is
        unconditionally overwritten before anything downstream reads it).
        No distance is cached here, unlike gradient's own version -- this
        scheme's boundary formula never needs one (a Neumann boundary's
        own zero-order extrapolation is exactly the average-with-itself
        the placeholder neighbour already produces; only the Dirichlet
        case ever actually changes the value, and both are recomputed
        explicitly below rather than special-cased, since the boundary
        face list is already small).
        """
        if self._cached_geometry_mesh is mesh and self._cached_geometry is not None:
            return self._cached_geometry

        num_faces = mesh.num_faces
        owner_ids = torch.zeros(num_faces, dtype=torch.long)
        neighbour_ids = torch.zeros(num_faces, dtype=torch.long)
        normal_x = torch.zeros(num_faces, dtype=torch.float64)
        normal_y = torch.zeros(num_faces, dtype=torch.float64)
        boundary_faces: list[int] = []
        boundary_names: dict[int, str] = {}
        for face in range(num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            nx, ny = mesh.face_normal(face)
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
            owner_ids[face] = owner
            normal_x[face] = nx
            normal_y[face] = ny
            if neighbour is not None:
                neighbour_ids[face] = neighbour
            else:
                assert boundary_name is not None
                neighbour_ids[face] = owner  # placeholder, overwritten below
                boundary_faces.append(face)
                boundary_names[face] = boundary_name

        geometry = _FaceGeometry(
            owner_ids=owner_ids,
            neighbour_ids=neighbour_ids,
            normal_x=normal_x,
            normal_y=normal_y,
            boundary_faces=tuple(boundary_faces),
            boundary_names=boundary_names,
        )
        self._cached_geometry_mesh = mesh
        self._cached_geometry = geometry
        return geometry

    def _boundary_face_normal_velocity(
        self,
        field: Field,
        face: int,
        boundary_name: str,
        owner_x: float,
        owner_y: float,
        normal_x: float,
        normal_y: float,
    ) -> float:
        """The face-normal velocity at a genuine boundary face.

        **No longer takes the `field` (TASK-052, Stage 9).** It used to,
        so it could call `condition.evaluate(field, face)` and read
        whatever number that returned as a wall-normal velocity -- which
        for a `VectorField` named `"velocity"` resolved to
        `BoundaryFaceConfig.scalar_value`, a *transported scalar's*
        boundary value, not a velocity at all. Every shipped
        configuration left both at `0.0`, so the wall came out
        impermeable by coincidence of the defaults rather than because
        anything read the velocity the configuration prescribed. It now
        reads that velocity, through the shared
        `boundary_normal_velocity` resolver, which is what makes this
        class's own docstring claim about
        `BoundaryFaceConfig.velocity`'s convention true.
        """
        condition = self._boundary_conditions.get(boundary_name)
        if condition is None:
            raise UnconfiguredBoundaryFaceError(
                f"face {face} (boundary {boundary_name!r}) has no BoundaryCondition configured"
            )
        return boundary_normal_velocity(
            condition, field, face, owner_x * normal_x + owner_y * normal_y
        )


@dataclass(frozen=True)
class _FaceGeometry:
    """`GreenGaussDivergence._face_geometry`'s own per-mesh cache -- see
    that method's own docstring for why interior/periodic faces are
    split from genuine boundary faces, and why no distances are cached.
    """

    owner_ids: torch.Tensor
    neighbour_ids: torch.Tensor
    normal_x: torch.Tensor
    normal_y: torch.Tensor
    boundary_faces: tuple[int, ...]
    boundary_names: dict[int, str]
