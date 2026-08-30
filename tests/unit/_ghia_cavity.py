"""One lid-driven-cavity resolution's own run, extracted from
`test_navier_stokes_timestep.py` (TASK-034) on 2026-08-30 -- not for the
"shared building blocks" reason `_numerics.py` exists for (nothing else
in this directory needs a cavity run), but because `ProcessPoolExecutor`
needs this logic importable with no `pytest-bdd` registration at module
scope.

`test_navier_stokes_timestep.py`'s own Ghia comparison scenario runs
three resolutions (9x9, 13x13, 17x17) to a measured steady state, fully
independently of each other -- found, while speeding up the test suite
at a user's direct request, to be the single largest cost in it (~706s
of the suite's own ~1018s serial total). Running the three concurrently
needed *processes*, not threads (measured directly: `ThreadPoolExecutor`
was 2.7x *slower* than sequential at a reduced scale, since these meshes
are tiny enough that the loop's own Python-level orchestration dominates
and is GIL-bound, not `torch`'s own tensor kernels -- see that test
module's own `_when_cavity_runs` docstring for the full measurement).
`ProcessPoolExecutor` on Windows uses `spawn`, which re-imports whatever
module defines the function being called in a fresh interpreter with no
pytest context at all -- and `test_navier_stokes_timestep.py`'s own
module-scope call binding this feature file's scenarios (`pytest_bdd`'s
own `scenarios` function) raises `IndexError` outside a running pytest
session (it reads a config stack that does not exist), which crashed
every worker before this module existed. This module holds no
`pytest`/`pytest_bdd` import at all and nothing in it imports from the
test module, so re-importing it in a worker process is exactly as safe
as importing any
other part of `pyflow` itself -- the dependency runs one way, the test
module importing from here, never the reverse.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import torch
from fixtures.ghia_1982_re100 import (
    U_VELOCITY_ALONG_VERTICAL_CENTERLINE,
    V_VELOCITY_ALONG_HORIZONTAL_CENTERLINE,
)

from pyflow.engine import simulation
from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import AssembledNumerics
from pyflow.engine.numerics.boundary_condition import BoundaryCondition, DirichletBoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver
from pyflow.engine.numerics.pressure_coupling import PISO
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

# These constants moved here from `test_navier_stokes_timestep.py`
# (which now imports the ones it still needs -- `CAVITY_ORIGIN`,
# `CAVITY_MAX_STEPS` -- back from here) rather than being duplicated:
# the dependency direction is one-way, this module importing nothing
# from the test module, which is what keeps a `spawn`-ed worker process
# safe (see this module's own docstring).
VELOCITY_NAME = "velocity"
U_NAME = VectorField.component_name(VELOCITY_NAME, 0)
V_NAME = VectorField.component_name(VELOCITY_NAME, 1)
TOLERANCE = 1e-6

CAVITY_REYNOLDS_NUMBER = 100
CAVITY_LID_SPEED = 1.0
CAVITY_VISCOSITY = CAVITY_LID_SPEED / CAVITY_REYNOLDS_NUMBER  # Re = U*L/nu, L = 1
CAVITY_STEADY_RESIDUAL_TOLERANCE = 1e-6
CAVITY_MAX_STEPS = 6000
CAVITY_ORIGIN = (0.35, -0.2)


class _ZeroSourceTerm(SourceTerm):
    """Contributes exactly zero -- this run's own hand-derived/measured
    claims were derived before a source term existed, and none of them
    is about buoyancy. Identical to `test_navier_stokes_timestep.py`'s
    own class of the same name, for the same "no cross-import" reason
    the module constants above are duplicated.
    """

    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        return torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)


@dataclass
class CavityRun:
    resolution: int
    error: float
    u_field: ScalarField | None = None
    v_field: ScalarField | None = None
    mesh: StructuredCartesianMesh | None = None
    steady: bool = False


def run_cavity(n: int) -> CavityRun:
    mesh = StructuredCartesianMesh(origin=CAVITY_ORIGIN, spacing=(1.0 / n, 1.0 / n), extent=(n, n))
    lid = DirichletBoundaryCondition(0.0, {U_NAME: CAVITY_LID_SPEED, V_NAME: 0.0})
    wall = DirichletBoundaryCondition(0.0)
    bcs: dict[str, BoundaryCondition] = {"north": lid, "south": wall, "east": wall, "west": wall}
    solver = ConjugateGradientSolver(tolerance=1e-10, max_iterations=1000)
    numerics = AssembledNumerics(
        advection=FirstOrderUpwindAdvection(bcs, {}),
        diffusion=CentralDifferenceDiffusion(bcs, {}, CAVITY_VISCOSITY),
        time_integration=RK4Integrator(),
        linear_solver=solver,
        pressure_coupling=PISO(solver, bcs, tolerance=TOLERANCE),
        source_term=_ZeroSourceTerm(),
        boundary_conditions=bcs,
        names={},
    )
    dt = simulation.stable_timestep(mesh, CAVITY_VISCOSITY, CAVITY_LID_SPEED, safety_factor=0.25)

    velocity = VectorField(mesh, VELOCITY_NAME, num_components=2, initial_value=(0.0, 0.0))
    fields: dict[str, Field] = {c.name: c for c in velocity.decompose()}
    previous_u: torch.Tensor | None = None
    steady = False
    for _ in range(CAVITY_MAX_STEPS):
        result = simulation.navier_stokes_step(fields, VELOCITY_NAME, numerics, dt)
        fields = result.fields
        u_field = fields[U_NAME]
        assert isinstance(u_field, ScalarField)
        u_values = u_field.values
        if previous_u is not None:
            residual = float((u_values - previous_u).abs().max()) / dt
            if residual < CAVITY_STEADY_RESIDUAL_TOLERANCE:
                steady = True
                break
        previous_u = u_values.clone()

    u_field = fields[U_NAME]
    v_field = fields[V_NAME]
    assert isinstance(u_field, ScalarField)
    assert isinstance(v_field, ScalarField)

    center = n // 2
    u_errors = []
    for y_ghia, u_ghia in U_VELOCITY_ALONG_VERTICAL_CENTERLINE:
        row = min(int(y_ghia * n), n - 1)
        cell = mesh.cell_id(center, row)
        u_errors.append((float(u_field.value_at(cell)) - u_ghia) ** 2)
    v_errors = []
    for x_ghia, v_ghia in V_VELOCITY_ALONG_HORIZONTAL_CENTERLINE:
        column = min(int(x_ghia * n), n - 1)
        cell = mesh.cell_id(column, center)
        v_errors.append((float(v_field.value_at(cell)) - v_ghia) ** 2)
    error = math.sqrt((sum(u_errors) + sum(v_errors)) / (len(u_errors) + len(v_errors)))

    return CavityRun(
        resolution=n, error=error, u_field=u_field, v_field=v_field, mesh=mesh, steady=steady
    )
