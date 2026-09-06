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
from dataclasses import dataclass
from typing import Any

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.vector_field import (
    IncompatibleVelocityFieldError as IncompatibleVelocityFieldError,
)
from pyflow.engine.vector_field import VectorField

_SPATIAL_DIMENSIONS = 2
"""PyFlow is 2D-only for now (`docs/implementation/mvp.md`) -- every
mesh accessor already assumes it (`Mesh.cell_centroid -> tuple[float,
float]`). Named here, not repeated as a bare `2`, so a future 3D mesh
(`docs/implementation/upgrade-paths.md` "Mesh") has one place to change.
"""

# `IncompatibleVelocityFieldError` moved to `vector_field.py` in TASK-031a
# (2026-08-29): `VectorField.assemble`'s own rejection needed the same
# error, and `vector_field.py` cannot import it back from here without a
# circular import (this module already imports `VectorField` from
# there). Re-exported at this name for every existing importer.


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
    `BoundaryCondition` in this scheme's own mapping and is not periodic
    either (`periodic_pairs`, TASK-030) -- a face genuinely wired to
    neither.

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

    **Periodic-aware the same way (TASK-030).** `periodic_pairs` names
    which boundary faces wrap to the opposite edge (e.g. `{"west":
    "east", "east": "west"}`) -- absence from it is never read as
    "periodic" by omission. At a periodic face, `mesh.wrapped_neighbour_cell`
    stands in for `neighbour` before either helper below runs, so the
    rest of `flux` treats it exactly like a genuine interior face; a
    periodic face never consults `boundary_conditions` at all.
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

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        assert isinstance(field, CollocatedField)
        mesh = field.mesh
        assert isinstance(mesh, StructuredCartesianMesh)
        geometry = self._face_geometry(mesh)

        v_owner = velocity.values[geometry.owner_ids]
        v_neighbour = velocity.values[geometry.neighbour_ids]
        # At a genuine boundary face, `neighbour_ids` is a placeholder
        # equal to `owner_ids` (built below), so this average reduces to
        # `v_owner` exactly -- "a boundary face has only the owner's own
        # velocity to draw on" falls out of the same formula, no separate
        # branch needed.
        v_avg = (v_owner + v_neighbour) / 2
        velocity_normal = v_avg[:, 0] * geometry.normal_x + v_avg[:, 1] * geometry.normal_y

        values = field.values
        owner_values = values[geometry.owner_ids]
        neighbour_values = values[geometry.neighbour_ids]
        # Correct by construction for interior/periodic faces (whichever
        # side is upstream) and for boundary *outflow* (owner is upstream
        # regardless, and the placeholder neighbour also equals owner) --
        # wrong only for boundary *inflow*, fixed by the loop below.
        phi = torch.where(velocity_normal >= 0, owner_values, neighbour_values)

        for face in geometry.boundary_faces:
            if float(velocity_normal[face]) < 0:
                phi[face] = self._boundary_upwind_value(
                    field, face, geometry.boundary_names[face], owner_values[face]
                )

        return velocity_normal * phi

    def _face_geometry(self, mesh: StructuredCartesianMesh) -> _FaceGeometry:
        """Built once per distinct `mesh` and cached for the rest of this
        instance's own lifetime -- `CentralDifferenceDiffusion._face_
        geometry`'s own pattern (`diffusion.py`), applied here since
        `boundary_conditions`/`periodic_pairs` are already fixed at
        construction.

        **Splits interior/periodic faces (resolved via pure `Mesh`
        geometry) from genuine boundary faces the same way, and for the
        same reason**: a genuine boundary face's inflow value can call
        `BoundaryCondition.evaluate(field, face)`, an open,
        user-extensible interface that receives the whole `field`, not
        just this face's own geometry -- see that method's own docstring
        for the full reasoning, which applies unchanged here.

        **One further narrowing specific to advection**: unlike
        diffusion, a genuine boundary face only ever needs a real
        `BoundaryCondition` call for *inflow* (`velocity_normal < 0`) --
        outflow always uses the owner's own value, never consulting one
        at all (the existing "no inflow/outflow carve-out" distinction,
        unchanged). Since inflow/outflow depends on the velocity field's
        own data, not fixed mesh geometry, it cannot be resolved into
        this cache; the small scalar loop this method's own boundary-face
        list feeds checks it per call instead.
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
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
            nx, ny = mesh.face_normal(face)
            owner_ids[face] = owner
            normal_x[face] = nx
            normal_y[face] = ny
            if neighbour is not None:
                neighbour_ids[face] = neighbour
            else:
                assert boundary_name is not None
                neighbour_ids[face] = owner  # placeholder, see `flux`'s own note
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

    def _boundary_upwind_value(
        self,
        field: CollocatedField[Any],
        face: int,
        boundary_name: str,
        owner_value: torch.Tensor,
    ) -> float:
        """The inflow value at a genuine boundary face -- only ever
        called where `velocity_normal < 0` (see `flux`): a fixed value
        for Dirichlet, or the owner's own value -- zero-order
        extrapolation, `docs/handbook/numerical-methods/
        boundary-conditions.md`'s own "typically extrapolated from the
        adjacent cell-centred value" -- for Neumann, which never reads
        its condition's numeric value at all.
        """
        condition = self._boundary_conditions.get(boundary_name)
        if condition is None:
            raise UnconfiguredBoundaryFaceError(
                f"face {face} (boundary {boundary_name!r}) has inflow but no "
                "BoundaryCondition is configured for it"
            )
        if condition.kind == "gradient":
            return float(owner_value)
        return condition.evaluate(field, face)


@dataclass(frozen=True)
class _FaceGeometry:
    """`FirstOrderUpwindAdvection._face_geometry`'s own per-mesh cache --
    see that method's own docstring for why interior/periodic faces are
    split from genuine boundary faces.
    """

    owner_ids: torch.Tensor
    neighbour_ids: torch.Tensor
    normal_x: torch.Tensor
    normal_y: torch.Tensor
    boundary_faces: tuple[int, ...]
    boundary_names: dict[int, str]
