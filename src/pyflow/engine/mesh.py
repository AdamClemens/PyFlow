"""Mesh (TASK-012): cell geometry, face geometry, neighbour/adjacency
lookup, and boundary identification -- independent of whether the mesh
is structured or unstructured (`docs/architecture/engine.md`'s own Mesh
contract). Built on `CoordinateSystem` (TASK-011), the layer beneath it.

Deliberately assumes nothing about structured-vs-unstructured
connectivity, matching TASK-011's own interface-first pattern. See
`docs/planning/roadmap.md` TASK-012 for the full design rationale and
acceptance criteria this module (and its contract test suite,
`tests/unit/test_mesh_contract.py`) implements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pyflow.configuration.schema import MeshConfig
from pyflow.engine.coordinate_system import UniformVertexCoordinateSystem


class Mesh(ABC):
    """Cells and faces of a discretised spatial domain.

    Cells and faces are identified by a flat integer id (`0 <=
    cell < num_cells`, `0 <= face < num_faces`) -- structured
    implementations map this to an `(i, j)` index internally;
    unstructured implementations need not have one at all.
    """

    @property
    @abstractmethod
    def num_cells(self) -> int: ...

    @property
    @abstractmethod
    def num_faces(self) -> int: ...

    @abstractmethod
    def cell_volume(self, cell: int) -> float:
        """The cell's volume (area, in 2D)."""

    @abstractmethod
    def cell_centroid(self, cell: int) -> tuple[float, float]:
        """The cell's centroid, in physical coordinates."""

    @abstractmethod
    def cell_faces(self, cell: int) -> tuple[int, ...]:
        """The ids of every face bounding this cell."""

    @abstractmethod
    def face_area(self, face: int) -> float:
        """The face's area (length, in 2D)."""

    @abstractmethod
    def face_normal(self, face: int) -> tuple[float, float]:
        """The face's normal, pointing from its owner cell toward its
        neighbour -- or outward from the domain, for a boundary face.
        See `face_normal_from` for the normal relative to a specific
        cell.
        """

    @abstractmethod
    def face_neighbours(self, face: int) -> tuple[int, int | None]:
        """`(owner_cell, neighbour_cell)`. `neighbour_cell` is `None`
        for a boundary face, which has exactly one owning cell.
        """

    def is_boundary_face(self, face: int) -> bool:
        """`True` if `face` has no neighbour cell (lies on the domain
        exterior); `False` if it separates two interior cells.
        """
        return self.face_neighbours(face)[1] is None

    def face_normal_from(self, face: int, cell: int) -> tuple[float, float]:
        """`face`'s outward normal as seen from `cell` -- `face_normal`
        itself if `cell` is the face's owner, its negation if `cell` is
        the face's neighbour. Raises `ValueError` if `cell` is not
        adjacent to `face`.
        """
        owner, neighbour = self.face_neighbours(face)
        normal_x, normal_y = self.face_normal(face)
        if cell == owner:
            return (normal_x, normal_y)
        if cell == neighbour:
            return (-normal_x, -normal_y)
        raise ValueError(f"cell {cell} is not adjacent to face {face}")


class StructuredCartesianMesh(Mesh):
    """A 2D structured Cartesian mesh with uniform grid spacing --
    PyFlow's MVP mesh (`docs/implementation/mvp.md`). Cells are indexed
    `(i, j)`, `0 <= i < nx`, `0 <= j < ny`; flattened to a single id as
    `j * nx + i`.

    Owns its own `UniformVertexCoordinateSystem` (built from the same
    `origin`/`spacing` passed here) rather than accepting an externally
    constructed one, so `spacing` has exactly one source of truth: cell
    volume and face area are computed directly from it (`dx * dy`, `dx`,
    `dy`), which is what makes them exact per TASK-012's own Acceptance
    Criteria -- deriving them instead from vertex-position subtraction
    would be mathematically equivalent but not bit-exact for a
    non-trivial origin, since floating-point subtraction of two nearby
    large-ish floats isn't guaranteed to reproduce the exact spacing that
    produced them.
    """

    def __init__(
        self,
        origin: tuple[float, float],
        spacing: tuple[float, float],
        extent: tuple[int, int],
    ) -> None:
        nx, ny = extent
        if nx <= 0 or ny <= 0:
            raise ValueError(f"extent must be positive, got nx={nx}, ny={ny}")

        self._nx = nx
        self._ny = ny
        self._dx, self._dy = spacing
        # Validates spacing (raises ValueError for dx/dy <= 0) as a side
        # effect -- one source of truth for that check, per P-011.
        self._coordinate_system = UniformVertexCoordinateSystem(origin=origin, spacing=spacing)

        self._num_vertical_faces = (nx + 1) * ny
        self._num_horizontal_faces = nx * (ny + 1)

    @classmethod
    def from_config(cls, config: MeshConfig) -> StructuredCartesianMesh:
        """Build a mesh entirely from a `MeshConfig` -- no bespoke code,
        per TASK-012's own public-schema design decision.
        """
        return cls(origin=config.origin, spacing=config.spacing, extent=config.extent)

    # -- id/index conversion --------------------------------------------

    def cell_id(self, i: int, j: int) -> int:
        """The flat cell id for structured index `(i, j)`."""
        return j * self._nx + i

    def cell_index(self, cell: int) -> tuple[int, int]:
        """The structured index `(i, j)` for flat cell id `cell`."""
        return (cell % self._nx, cell // self._nx)

    # -- Mesh interface ---------------------------------------------------

    @property
    def num_cells(self) -> int:
        return self._nx * self._ny

    @property
    def num_faces(self) -> int:
        return self._num_vertical_faces + self._num_horizontal_faces

    def cell_volume(self, cell: int) -> float:
        return self._dx * self._dy

    def cell_centroid(self, cell: int) -> tuple[float, float]:
        i, j = self.cell_index(cell)
        cs = self._coordinate_system
        corners = (
            cs.to_physical(i, j),
            cs.to_physical(i + 1, j),
            cs.to_physical(i + 1, j + 1),
            cs.to_physical(i, j + 1),
        )
        return (
            sum(x for x, _ in corners) / 4,
            sum(y for _, y in corners) / 4,
        )

    def cell_faces(self, cell: int) -> tuple[int, ...]:
        i, j = self.cell_index(cell)
        return (
            self._vertical_face_id(i, j),  # west
            self._vertical_face_id(i + 1, j),  # east
            self._horizontal_face_id(i, j),  # south
            self._horizontal_face_id(i, j + 1),  # north
        )

    def face_area(self, face: int) -> float:
        return self._dy if face < self._num_vertical_faces else self._dx

    def face_normal(self, face: int) -> tuple[float, float]:
        if face < self._num_vertical_faces:
            p, _j = self._decode_vertical_face(face)
            # p == 0 is the west domain boundary: its one owning cell is
            # to the *east* of it, so the outward normal points west
            # (-1, 0) -- the one case that isn't "pointing toward
            # increasing i". Every other vertical face (p == nx, or an
            # interior face) points +x, per the derivation in
            # docs/planning/roadmap.md TASK-012.
            return (-1.0, 0.0) if p == 0 else (1.0, 0.0)
        i, q = self._decode_horizontal_face(face)
        # Same asymmetry, along y: q == 0 (south boundary) points -y,
        # every other horizontal face points +y.
        return (0.0, -1.0) if q == 0 else (0.0, 1.0)

    def face_neighbours(self, face: int) -> tuple[int, int | None]:
        if face < self._num_vertical_faces:
            p, j = self._decode_vertical_face(face)
            if p == 0:
                return (self.cell_id(0, j), None)
            if p == self._nx:
                return (self.cell_id(self._nx - 1, j), None)
            return (self.cell_id(p - 1, j), self.cell_id(p, j))

        i, q = self._decode_horizontal_face(face)
        if q == 0:
            return (self.cell_id(i, 0), None)
        if q == self._ny:
            return (self.cell_id(i, self._ny - 1), None)
        return (self.cell_id(i, q - 1), self.cell_id(i, q))

    # -- face id encoding/decoding ---------------------------------------
    # Vertical faces (normal in x): position p in [0, nx] (west/east
    # boundary at p == 0 / p == nx), row j in [0, ny). Horizontal faces
    # (normal in y): column i in [0, nx), position q in [0, ny] (south/
    # north boundary at q == 0 / q == ny). Vertical faces are numbered
    # first, horizontal faces follow.

    def _vertical_face_id(self, p: int, j: int) -> int:
        return j * (self._nx + 1) + p

    def _decode_vertical_face(self, face: int) -> tuple[int, int]:
        return (face % (self._nx + 1), face // (self._nx + 1))

    def _horizontal_face_id(self, i: int, q: int) -> int:
        return self._num_vertical_faces + i * (self._ny + 1) + q

    def _decode_horizontal_face(self, face: int) -> tuple[int, int]:
        local = face - self._num_vertical_faces
        return (local // (self._ny + 1), local % (self._ny + 1))
