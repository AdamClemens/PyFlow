"""Core numerical engine: mesh, field storage, numerical operators, time
integration, pressure-velocity coupling, linear solvers, and boundary
conditions -- the reusable simulation machinery, independent of any
specific physics. Also covers state I/O, run-loop orchestration, and
shared utilities, absorbed here per the 2026-08-15 package
reconciliation (see docs/planning/backlog.md).
"""

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.coordinate_system import (
    CoordinateSystem,
    OffGridCoordinateError,
    UniformVertexCoordinateSystem,
)
from pyflow.engine.field import Field
from pyflow.engine.logging_setup import configure_logging, get_logger
from pyflow.engine.mesh import InvalidMeshEntityError, Mesh, StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

__all__ = [
    "CollocatedField",
    "CoordinateSystem",
    "Field",
    "InvalidMeshEntityError",
    "Mesh",
    "OffGridCoordinateError",
    "ScalarField",
    "StructuredCartesianMesh",
    "UniformVertexCoordinateSystem",
    "VectorField",
    "configure_logging",
    "get_logger",
]
