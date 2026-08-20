"""CoordinateSystem (TASK-011): the mapping between a grid index and a
physical position -- the layer beneath `Mesh` (TASK-012). No cells, no
neighbours, no boundaries here; just index-to-physical and
physical-to-index conversion.

Deliberately assumes nothing about spacing (uniform or not) or
vertex-vs-cell-center placement -- those are properties of a concrete
implementation, not this contract. Same interface-first,
swappable-implementations-behind-it pattern as
`src/pyflow/rendering/canvas.py`'s `create_canvas`, applied here for the
first time to a component PyFlow owns outright. See
`docs/planning/roadmap.md` TASK-011 for the full design rationale and
acceptance criteria this module (and its contract test suite,
`tests/unit/test_coordinate_system_contract.py`) implements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class CoordinateOutOfBoundsError(ValueError):
    """Raised by `to_index` when a physical coordinate does not
    correspond to any valid index of the coordinate system it was asked
    of -- the same exception class for every implementation, so calling
    code can catch one type regardless of which concrete
    `CoordinateSystem` it's holding.
    """


class CoordinateSystem(ABC):
    """Maps between grid indices `(i, j)` and physical positions `(x, y)`."""

    @abstractmethod
    def to_physical(self, i: int, j: int) -> tuple[float, float]:
        """Return the physical `(x, y)` position of index `(i, j)`."""

    @abstractmethod
    def to_index(self, x: float, y: float) -> tuple[int, int]:
        """Return the index `(i, j)` whose physical position is `(x, y)`.

        Raises `CoordinateOutOfBoundsError` if `(x, y)` does not
        correspond to a valid index of this coordinate system.
        """


class UniformVertexCoordinateSystem(CoordinateSystem):
    """Vertex-based coordinate system with uniform spacing -- the first
    concrete `CoordinateSystem`, matching PyFlow's MVP mesh geometry
    (`docs/implementation/mvp.md`: 2D structured Cartesian, uniform grid
    spacing). A cell-center-based implementation is deliberately not
    built yet -- see TASK-011's own notes in `docs/planning/roadmap.md`.
    """

    def __init__(self, origin: tuple[float, float], spacing: tuple[float, float]) -> None:
        x0, y0 = origin
        dx, dy = spacing
        if dx <= 0 or dy <= 0:
            raise ValueError(f"spacing must be positive, got dx={dx}, dy={dy}")
        self._x0 = x0
        self._y0 = y0
        self._dx = dx
        self._dy = dy

    def to_physical(self, i: int, j: int) -> tuple[float, float]:
        return (self._x0 + i * self._dx, self._y0 + j * self._dy)

    def to_index(self, x: float, y: float) -> tuple[int, int]:
        # Normalising by spacing first keeps the off-grid tolerance below
        # scale-invariant: a fixed tolerance in this normalised "index
        # space" corresponds to a physical tolerance that scales with
        # dx/dy, rather than being wrong by construction for a coordinate
        # system with very small or very large spacing.
        i_float = (x - self._x0) / self._dx
        j_float = (y - self._y0) / self._dy
        i = round(i_float)
        j = round(j_float)

        tolerance = 1e-9
        if abs(i_float - i) > tolerance or abs(j_float - j) > tolerance:
            raise CoordinateOutOfBoundsError(
                f"({x}, {y}) does not correspond to a valid index of this coordinate system"
            )
        return (i, j)
