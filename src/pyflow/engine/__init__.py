"""Core numerical engine: mesh, field storage, numerical operators, time
integration, pressure-velocity coupling, linear solvers, and boundary
conditions -- the reusable simulation machinery, independent of any
specific physics. Also covers state I/O, run-loop orchestration, and
shared utilities, absorbed here per the 2026-08-15 package
reconciliation (see docs/planning/backlog.md).
"""

from pyflow.engine.coordinate_system import (
    CoordinateOutOfBoundsError,
    CoordinateSystem,
    UniformVertexCoordinateSystem,
)
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh

__all__ = [
    "CoordinateOutOfBoundsError",
    "CoordinateSystem",
    "Mesh",
    "StructuredCartesianMesh",
    "UniformVertexCoordinateSystem",
    "configure_logging",
    "get_logger",
]
