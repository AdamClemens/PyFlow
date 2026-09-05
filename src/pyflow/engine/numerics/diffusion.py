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
from dataclasses import dataclass
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

    **`coefficient_overrides` (TASK-031b, added 2026-08-29) is a
    per-field-name exception to "one Gamma for the whole scheme"**: a
    momentum component (`velocity.0`/`velocity.1`, `VectorField.
    component_name`) is diffused with `fluid.viscosity`, while an
    ordinary transported scalar keeps using `fluid.diffusion_coefficient`
    -- one shared `CentralDifferenceDiffusion` instance, dispatched by
    `field.name` inside `flux`, the same "default value plus per-field
    overrides" shape `DirichletBoundaryCondition.overrides` uses
    (`boundary_condition.py`, same task). Defaults to empty, so every
    existing call site that only passes `diffusion_coefficient` keeps
    its old, single-coefficient behaviour unchanged. Which field names
    actually get an override is not this class's concern -- whoever
    assembles a run decides that (`assemble_numerics`'s own widened
    parameter, `bootstrap.py`'s the one place that legitimately knows a
    velocity field is conventionally named `"velocity"`), keeping this
    scheme itself field-name-agnostic.

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
        coefficient_overrides: Mapping[str, float] | None = None,
    ) -> None:
        self._boundary_conditions = boundary_conditions
        self._periodic_pairs = periodic_pairs
        self._gamma = diffusion_coefficient
        self._coefficient_overrides = coefficient_overrides or {}
        self._cached_geometry_mesh: StructuredCartesianMesh | None = None
        self._cached_geometry: _FaceGeometry | None = None

    def flux(self, field: Field) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        mesh = field.mesh
        assert isinstance(mesh, StructuredCartesianMesh)
        gamma = self._coefficient_overrides.get(field.name, self._gamma)
        geometry = self._face_geometry(mesh)

        values = field.values
        raw = (values[geometry.neighbour_ids] - values[geometry.owner_ids]) / geometry.distances
        gradient = torch.where(geometry.resolved, raw, torch.zeros_like(raw))

        for face in geometry.boundary_faces:
            owner_value = float(field.value_at(int(geometry.owner_ids[face])))
            distance = float(geometry.distances[face])
            gradient[face] = self._boundary_gradient(
                field, face, geometry.boundary_names[face], owner_value, distance
            )

        return gamma * gradient

    def _face_geometry(self, mesh: StructuredCartesianMesh) -> _FaceGeometry:
        """Built once per distinct `mesh` and cached for the rest of this
        instance's own lifetime, not rebuilt on every `flux` call --
        `PISO._cached_poisson_matrix`'s own "cached by mesh identity, not
        equality" pattern, applied here since `boundary_conditions`/
        `periodic_pairs` are already fixed at construction, so nothing
        about repeating this per call was ever buying correctness.

        **Splits interior/periodic faces (resolved via pure `Mesh`
        geometry, safe to gather in bulk) from genuine boundary faces
        (which need a real `BoundaryCondition.evaluate` call) rather than
        vectorising the whole loop** -- `BoundaryCondition` is an open,
        user-extensible interface (`adr/ADR-003-modular-numerical-
        strategies.md`); `evaluate` receives the whole `field`, and
        nothing in the ABC forbids a future implementation from reading
        other cells' values, even though neither current one
        (`DirichletBoundaryCondition`, `NeumannBoundaryCondition`) does.
        Vectorising past that interface would be speculation this
        project's own P-016 refuses. The boundary-face loop that remains
        shrinks as a fraction of `mesh.num_faces` as resolution grows
        (`2*(nx+ny)` boundary faces out of `(nx+1)*ny + nx*(ny+1)` total,
        for an nx-by-ny structured mesh), so it matters less at exactly
        the resolutions where the vectorised majority matters most.
        """
        if self._cached_geometry_mesh is mesh and self._cached_geometry is not None:
            return self._cached_geometry

        num_faces = mesh.num_faces
        owner_ids = torch.zeros(num_faces, dtype=torch.long)
        neighbour_ids = torch.zeros(num_faces, dtype=torch.long)
        distances = torch.zeros(num_faces, dtype=torch.float64)
        resolved = torch.zeros(num_faces, dtype=torch.bool)
        boundary_faces: list[int] = []
        boundary_names: dict[int, str] = {}
        for face in range(num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            distance = mesh.face_centroid_distance(face)
            owner_ids[face] = owner
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
                    distance = 2 * distance
            if neighbour is not None:
                neighbour_ids[face] = neighbour
                distances[face] = distance
                resolved[face] = True
            else:
                assert boundary_name is not None
                neighbour_ids[face] = owner  # placeholder, masked out by `resolved`
                distances[face] = distance
                boundary_faces.append(face)
                boundary_names[face] = boundary_name

        geometry = _FaceGeometry(
            owner_ids=owner_ids,
            neighbour_ids=neighbour_ids,
            distances=distances,
            resolved=resolved,
            boundary_faces=tuple(boundary_faces),
            boundary_names=boundary_names,
        )
        self._cached_geometry_mesh = mesh
        self._cached_geometry = geometry
        return geometry

    def _boundary_gradient(
        self,
        field: CollocatedField[Any],
        face: int,
        boundary_name: str,
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
        condition = self._boundary_conditions.get(boundary_name)
        if condition is None:
            raise UnconfiguredBoundaryFaceError(
                f"face {face} (boundary {boundary_name!r}) has no BoundaryCondition configured"
            )
        if condition.kind == "gradient":
            return condition.evaluate(field, face)
        boundary_value = condition.evaluate(field, face)
        return (boundary_value - owner_value) / distance


@dataclass(frozen=True)
class _FaceGeometry:
    """`CentralDifferenceDiffusion._face_geometry`'s own per-mesh cache --
    see that method's own docstring for why interior/periodic faces are
    split from genuine boundary faces.
    """

    owner_ids: torch.Tensor
    neighbour_ids: torch.Tensor
    distances: torch.Tensor
    resolved: torch.Tensor
    boundary_faces: tuple[int, ...]
    boundary_names: dict[int, str]
