"""Contract test suite for `CoordinateSystem` (TASK-011).

Written once, run against every `CoordinateSystem` implementation that
exists now or is added later -- asserts only what must hold regardless
of implementation, per `docs/planning/roadmap.md` TASK-011's Acceptance
Criteria. A future implementation joins this suite by adding a factory
to `_IMPLEMENTATIONS` below, not by writing new tests here.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import pytest

from pyflow.engine.coordinate_system import (
    CoordinateSystem,
    OffGridCoordinateError,
    UniformVertexCoordinateSystem,
)


def _uniform_vertex() -> CoordinateSystem:
    # Deliberately non-"nice" origin/spacing (not exactly representable
    # in binary floating point) -- proves the round-trip and
    # out-of-bounds tolerance below hold for real floats, not just
    # numbers that happen to be exact.
    return UniformVertexCoordinateSystem(origin=(1.5, -2.25), spacing=(0.1, 0.3))


_IMPLEMENTATIONS: list[Callable[[], CoordinateSystem]] = [_uniform_vertex]

_INDEX_RANGE = range(-50, 51)


@pytest.fixture(params=_IMPLEMENTATIONS, ids=lambda factory: factory.__name__.lstrip("_"))
def coordinate_system(request: pytest.FixtureRequest) -> CoordinateSystem:
    factory: Callable[[], CoordinateSystem] = request.param
    return factory()


def test_round_trip_every_valid_index(coordinate_system: CoordinateSystem) -> None:
    for i, j in itertools.product(_INDEX_RANGE, _INDEX_RANGE):
        x, y = coordinate_system.to_physical(i, j)
        assert coordinate_system.to_index(x, y) == (i, j)


def test_increasing_i_never_decreases_x(coordinate_system: CoordinateSystem) -> None:
    xs = [coordinate_system.to_physical(i, 0)[0] for i in _INDEX_RANGE]
    assert all(later >= earlier for earlier, later in itertools.pairwise(xs))


def test_increasing_j_never_decreases_y(coordinate_system: CoordinateSystem) -> None:
    ys = [coordinate_system.to_physical(0, j)[1] for j in _INDEX_RANGE]
    assert all(later >= earlier for earlier, later in itertools.pairwise(ys))


def test_to_index_raises_for_off_grid_coordinate(coordinate_system: CoordinateSystem) -> None:
    x0, y0 = coordinate_system.to_physical(0, 0)
    x1, _ = coordinate_system.to_physical(1, 0)
    midpoint_x = (x0 + x1) / 2

    with pytest.raises(OffGridCoordinateError):
        coordinate_system.to_index(midpoint_x, y0)
