"""DiffusionScheme (TASK-018): the interface computing a field's
diffusive flux contribution at each mesh face, given the field alone
(`docs/architecture/engine.md`'s Diffusion contract: "given a field,
produces the diffusive contribution to that field's flux at each
face").

`CentralDifferenceDiffusion` (TASK-024, Stage 4) is the first real
concrete scheme -- Stage 3 Completion Criterion 1 restricted every
implementation of the six `adr/ADR-003-modular-numerical-
strategies.md` components to `tests/` only through Stage 3; Stage 4
lifts that restriction for the task that brings each component's real
MVP scheme. See `docs/planning/roadmap.md` TASK-018 for the interface's
own design rationale and TASK-024 for the concrete scheme's.
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


class DiffusionScheme(ABC):
    """Computes a field's diffusive flux at each mesh face."""

    @abstractmethod
    def flux(self, field: Field) -> torch.Tensor:
        """The diffusive contribution to `field`'s flux at each of its
        mesh's faces.

        Returns a tensor of shape `(field.mesh.num_faces,)`.
        """


class UnconfiguredBoundaryFaceError(ValueError):
    """Raised when a `CentralDifferenceDiffusion` boundary face's named
    edge (`StructuredCartesianMesh.boundary_face_name`) has no
    `BoundaryCondition` in this scheme's own mapping and is not periodic
    either (`periodic_pairs`, TASK-030) -- mirroring `advection.py`'s
    identically-named exception for the identical underlying reason, but
    its own class in its own module (each numerics interface owns its
    own exception vocabulary).

    Unlike advection's own version, there is no inflow/outflow carve-out
    here: diffusion has no flow direction, so *every* non-periodic
    boundary face needs a configured condition to compute a diffusive
    flux at all, not only the faces where flow happens to be entering.
    """


class CentralDifferenceDiffusion(DiffusionScheme):
    """Central differencing (TASK-024): the face-normal gradient is the
    difference between the two neighbouring cell-centred values divided
    by the distance between their centroids -- second-order accurate on
    PyFlow's uniform orthogonal MVP mesh, per `docs/handbook/
    numerical-methods/diffusion.md`. PyFlow's MVP diffusion scheme
    (`docs/implementation/mvp.md`).

    Boundary-aware by construction, the same pattern
    `FirstOrderUpwindAdvection` establishes (TASK-040's own Design
    decision): holds the boundary conditions and the diffusion
    coefficient (Gamma, `FluidConfig.diffusion_coefficient` -- migrated
    from `NumericsConfig.diffusion_coefficient` by TASK-041, 2026-08-28)
    it needs, rather than the orchestrator substituting either in
    afterward.

    **Periodic-aware the same way `FirstOrderUpwindAdvection` is
    (TASK-030).** At a face named in `periodic_pairs`, `flux` substitutes
    `mesh.wrapped_neighbour_cell` for `neighbour` and the correct
    one-cell-width distance (`2 * mesh.face_centroid_distance(face)` --
    see this module's own TASK-030 note in `docs/planning/roadmap.md` for
    why doubling the owner-to-face distance is exactly right on a uniform
    mesh, verified numerically before relying on it) before falling
    through the ordinary interior-face formula below; `boundary_conditions`
    is never consulted for a periodic face.
    """

    def __init__(
        self,
        boundary_conditions: Mapping[str, BoundaryCondition],
        periodic_pairs: Mapping[str, str],
        diffusion_coefficient: float,
    ) -> None:
        self._boundary_conditions = boundary_conditions
        self._periodic_pairs = periodic_pairs
        self._gamma = diffusion_coefficient

    def flux(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        mesh = field.mesh
        assert isinstance(mesh, StructuredCartesianMesh)

        result = torch.zeros(mesh.num_faces, dtype=torch.float64)
        for face in range(mesh.num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            owner_value = float(field.value_at(owner))
            distance = mesh.face_centroid_distance(face)
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
                    distance = 2 * distance
            if neighbour is not None:
                neighbour_value = float(field.value_at(neighbour))
                gradient = (neighbour_value - owner_value) / distance
            else:
                gradient = self._boundary_gradient(mesh, field, face, owner_value, distance)
            result[face] = self._gamma * gradient
        return result

    def _boundary_gradient(
        self,
        mesh: StructuredCartesianMesh,
        field: CollocatedField[Any],
        face: int,
        owner_value: float,
        distance: float,
    ) -> float:
        """The face-normal gradient at a boundary face, per its
        `BoundaryCondition`'s own `kind`: a Dirichlet (`"value"`)
        condition supplies the boundary's own value, so the gradient is
        the ordinary central difference between it and the owner's value
        over the owner-to-face distance; a Neumann (`"gradient"`)
        condition *is* the face-normal gradient already -- read directly,
        unlike `FirstOrderUpwindAdvection`'s own Neumann handling, which
        never reads its condition's numeric value at all. No condition
        configured (the periodic case) raises `UnconfiguredBoundaryFaceError`
        rather than silently defaulting to a plausible-looking gradient.
        """
        boundary_name = mesh.boundary_face_name(face)
        assert boundary_name is not None
        condition = self._boundary_conditions.get(boundary_name)
        if condition is None:
            raise UnconfiguredBoundaryFaceError(
                f"face {face} (boundary {boundary_name!r}) has no BoundaryCondition configured"
            )
        if condition.kind == "gradient":
            return condition.evaluate(field, face)
        boundary_value = condition.evaluate(field, face)
        return (boundary_value - owner_value) / distance
