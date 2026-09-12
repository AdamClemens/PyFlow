"""Sealed Box golden demo (TASK-052, Stage 9).

The acceptance criteria are `tests/features/sealed_box.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`). Stage 9's own Golden
Demo, and the visible form of the defect that opened the stage: a tracer
in a closed, no-slip lid-driven cavity has nowhere to go, and before
TASK-052 it left through the walls anyway.

**This module checks the wall, not the domain integral**, and the
config file's own header says why: diffusion to a zero-valued wall
removes tracer legitimately, and `FieldConfig` rejects a perfectly
non-diffusive one, so exact conservation is proven at the engine level
instead (`tests/features/boundary_velocity.feature`) against a purely
advective fixture. What this demo proves, on a committed config through
the public API, is that no tracer crosses a wall by advection while the
flow against those walls is still moving -- which is false on the
pre-TASK-052 engine and true on this one.
"""

from __future__ import annotations

import math

from pytest_bdd import scenarios, then, when

from pyflow.bootstrap import bootstrap
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField
from pyflow.rendering.window import RenderWindow

from ._demo import DemoRun

scenarios("sealed_box.feature")

_FRAMES = 12
"""Measured directly against this demo's own config before choosing it,
the same discipline `test_smoke_transport.py`'s own `_FRAMES` uses: by
twelve real timesteps the lid-driven circulation has reached the walls
(the fastest wall-adjacent cell is moving at ~0.29, well clear of the
bound below) and the tracer field has visibly changed from its initial
blob. Fewer frames and the flow has not yet reached the walls, which
would make a zero wall flux prove nothing.
"""

_MOVING_WALL_CELL_SPEED = 0.05
"""A cell against a wall must be moving at least this fast for "no flux
crosses the wall" to mean the wall is impermeable rather than the flow
dead. Measured ~0.29 at `_FRAMES`, so this keeps a factor of five in
hand.
"""


def _velocity(window: RenderWindow) -> VectorField:
    assert window.simulation_fields is not None
    components = [
        window.simulation_fields[VectorField.component_name("velocity", index)]
        for index in range(2)
    ]
    return VectorField.assemble(components, "velocity")  # type: ignore[arg-type]


def _boundary_faces(mesh: StructuredCartesianMesh) -> list[int]:
    return [face for face in range(mesh.num_faces) if mesh.face_neighbours(face)[1] is None]


@when("it is bootstrapped for several real timesteps", target_fixture="window")
def _when_bootstrapped(demo: DemoRun) -> RenderWindow:
    return bootstrap(demo.config_path, backend="offscreen", max_frames=_FRAMES)


@then("every wall face carries exactly zero advective flux")
def _then_no_wall_flux(window: RenderWindow) -> None:
    assert window.simulation_fields is not None
    assert window.assembled_numerics is not None
    tracer = window.simulation_fields["tracer"]
    assert isinstance(tracer, ScalarField)
    mesh = tracer.mesh
    assert isinstance(mesh, StructuredCartesianMesh)
    flux = window.assembled_numerics.advection.flux(tracer, _velocity(window))
    for face in _boundary_faces(mesh):
        assert float(flux[face]) == 0.0, (
            f"wall face {face} ({mesh.boundary_face_name(face)}) carries advective flux "
            f"{float(flux[face])}; a sealed box must carry none through any wall"
        )


@then("the cells against those walls still carry real motion")
def _then_wall_cells_move(window: RenderWindow) -> None:
    assert window.simulation_fields is not None
    velocity = _velocity(window)
    mesh = velocity.mesh
    assert isinstance(mesh, StructuredCartesianMesh)
    owners = {mesh.face_neighbours(face)[0] for face in _boundary_faces(mesh)}
    fastest = max(math.hypot(*velocity.value_at(cell)) for cell in owners)
    assert fastest > _MOVING_WALL_CELL_SPEED, (
        f"the cells against the walls must still be moving for a zero wall flux to mean the wall "
        f"is impermeable rather than the flow dead; fastest was {fastest}"
    )


@then("the tracer field has measurably changed from where it started")
def _then_tracer_transported(demo: DemoRun, window: RenderWindow) -> None:
    initial = bootstrap(demo.config_path, backend="offscreen", max_frames=1)
    assert initial.simulation_fields is not None
    assert window.simulation_fields is not None
    early = initial.simulation_fields["tracer"]
    late = window.simulation_fields["tracer"]
    assert isinstance(early, ScalarField)
    assert isinstance(late, ScalarField)
    assert not early.values.equal(late.values), (
        "expected the tracer to keep being carried by the recirculating flow, not freeze after "
        "one step"
    )
