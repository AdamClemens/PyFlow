"""Implementation-specific tests for `UniformVertexCoordinateSystem`
(TASK-011). In addition to the shared contract suite
(`test_coordinate_system_contract.py`), which every `CoordinateSystem`
must pass, this implementation makes its own specific claims -- an exact
formula, uniform spacing, and its own error condition -- that the
contract suite deliberately does not (and must not) assert, since a
future, differently-shaped implementation wouldn't satisfy them.
"""

from __future__ import annotations

import pytest

from pyflow.engine.coordinate_system import UniformVertexCoordinateSystem

_ORIGIN = (1.5, -2.25)
_SPACING = (0.1, 0.3)


def test_to_physical_matches_formula_exactly() -> None:
    cs = UniformVertexCoordinateSystem(origin=_ORIGIN, spacing=_SPACING)
    x0, y0 = _ORIGIN
    dx, dy = _SPACING

    for i, j in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1_000_000, -1_000_000)]:
        assert cs.to_physical(i, j) == (x0 + i * dx, y0 + j * dy)


def test_adjacent_indices_are_exactly_one_spacing_apart() -> None:
    cs = UniformVertexCoordinateSystem(origin=(0.0, 0.0), spacing=(0.5, 2.0))

    for i, j in [(0, 0), (10, -5)]:
        x, y = cs.to_physical(i, j)
        x_next, _ = cs.to_physical(i + 1, j)
        _, y_next = cs.to_physical(i, j + 1)

        assert x_next - x == 0.5
        assert y_next - y == 2.0


@pytest.mark.parametrize(
    ("dx", "dy"),
    [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)],
)
def test_non_positive_spacing_raises(dx: float, dy: float) -> None:
    with pytest.raises(ValueError, match="spacing must be positive"):
        UniformVertexCoordinateSystem(origin=(0.0, 0.0), spacing=(dx, dy))
