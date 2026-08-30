"""Unit tests for `pyflow.physics.buoyancy.BoussinesqBuoyancy` (TASK-035)
-- its own specific mechanics (axis detection, per-coupling summation),
distinct from `tests/features/temperature_field.feature`'s own
physical-correctness claims (`tests/unit/test_temperature_field.py`),
the same split `tests/unit/test_scalar_field.py` draws against its own
contract suite.
"""

from __future__ import annotations

import torch

from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.physics.buoyancy import BoussinesqBuoyancy


def _mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(2, 2))


def test_a_coupling_naming_a_field_absent_from_state_is_skipped() -> None:
    # A configured coupling's own driving field not being transported in
    # this particular state is not an error -- it simply contributes
    # nothing, the same as an unconfigured coupling would.
    mesh = _mesh()
    v = ScalarField(mesh, "velocity.1", initial_value=0.0)
    buoyancy = BoussinesqBuoyancy(gravity=(0.0, -9.81), couplings={"temperature": (0.0, -1.0)})

    result = buoyancy.source(v, {})

    assert torch.equal(result, torch.zeros((mesh.num_cells,), dtype=torch.float64))


def test_a_zero_gravity_component_contributes_nothing_regardless_of_coupling() -> None:
    mesh = _mesh()
    u = ScalarField(mesh, "velocity.0", initial_value=0.0)
    temperature = ScalarField(mesh, "temperature", initial_value=999.0)
    buoyancy = BoussinesqBuoyancy(gravity=(0.0, -9.81), couplings={"temperature": (0.0, -1.0)})

    result = buoyancy.source(u, {"temperature": temperature})

    assert torch.equal(result, torch.zeros((mesh.num_cells,), dtype=torch.float64))


def test_multiple_couplings_sum_their_own_contributions() -> None:
    mesh = _mesh()
    v = ScalarField(mesh, "velocity.1", initial_value=0.0)
    temperature = ScalarField(mesh, "temperature", initial_value=10.0)
    density = ScalarField(mesh, "density", initial_value=5.0)
    buoyancy = BoussinesqBuoyancy(
        gravity=(0.0, -9.81),
        couplings={"temperature": (0.0, -1.0), "density": (0.0, 1.0)},
    )

    result = buoyancy.source(v, {"temperature": temperature, "density": density})

    expected_per_cell = (-1.0) * (10.0 - 0.0) * (-9.81) + (1.0) * (5.0 - 0.0) * (-9.81)
    assert torch.equal(
        result, torch.full((mesh.num_cells,), expected_per_cell, dtype=torch.float64)
    )


def test_a_non_velocity_field_receives_no_contribution() -> None:
    mesh = _mesh()
    temperature = ScalarField(mesh, "temperature", initial_value=10.0)
    buoyancy = BoussinesqBuoyancy(gravity=(0.0, -9.81), couplings={"temperature": (0.0, -1.0)})

    result = buoyancy.source(temperature, {"temperature": temperature})

    assert torch.equal(result, torch.zeros((mesh.num_cells,), dtype=torch.float64))
