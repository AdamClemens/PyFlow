"""Simulation Orchestrator (TASK-040): turns a mesh, a set of transported
fields, and an already-assembled `AssembledNumerics` into an actual
per-timestep state advance -- the mechanism `docs/architecture/engine.md`'s
Flux entry describes ("jointly compute[d]" by the Advection/Diffusion/
Gradient/Divergence interfaces) but assigns to no module.

Not a new swappable interface (`adr/ADR-003-modular-numerical-strategies.md`
names exactly six, and this is not a seventh, per P-016) -- a concrete
module, the same status `bootstrap.py` has relative to `configuration`/
`rendering`. See `docs/planning/roadmap.md` TASK-040 for the full design
rationale, including the two design decisions (boundary-face substitution,
periodic's own shape) this module's own shape depends on.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import torch

from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh
from pyflow.engine.scalar_field import PressureField
from pyflow.engine.vector_field import VectorField

if TYPE_CHECKING:
    # Deferred: `pyflow.engine.numerics.assembly` (via `pressure_coupling`)
    # imports `accumulate_flux_to_cells` from this module (TASK-027,
    # `GreenGaussGradient`/`GreenGaussDivergence`/`PISO` all reuse it) -- an
    # eager import here would be circular. `AssembledNumerics` is only ever
    # used as a type annotation below, which `from __future__ import
    # annotations` already makes lazy, so deferring the import costs
    # nothing at runtime. See `src/pyflow/engine/CLAUDE.md`'s `simulation.py`
    # entry.
    from pyflow.engine.numerics.assembly import AssembledNumerics


class MismatchedMeshError(ValueError):
    """Raised when a field in `step`'s `fields` mapping is not defined
    over the same mesh as `velocity` -- the same reasoning as
    `InvalidMeshEntityError`/`IncompatibleVelocityFieldError`: mixing
    two fields from different meshes would either crash confusingly deep
    inside a mismatched-shape tensor operation or, on a coincidentally
    same-sized mesh, silently combine values from unrelated cells.
    """


class PressureFieldTransportError(ValueError):
    """Raised when `step`'s own `fields` mapping contains a
    `PressureField` (TASK-032, Stage 5 Completion Criterion 2,
    `docs/planning/roadmap.md`): pressure is solved from the
    incompressibility constraint, not transported, so quietly advecting
    it would silently discard exactly the property that makes it
    meaningful. Stated at the API level -- a real `isinstance` check
    against the field object itself, since there is no configuration
    surface today that names which fields are transported.
    """


def accumulate_flux_to_cells(mesh: Mesh, face_values: torch.Tensor) -> torch.Tensor:
    """Reduce a face-valued array to a cell-valued one via the discrete
    Gauss theorem: `sum(value * area * outward_normal_sign) / volume`,
    per cell.

    `outward_normal_sign` is `+1` for a face's owner cell and `-1` for
    its neighbour (if any) -- `Mesh.face_normal`'s own canonical
    direction, owner toward neighbour or outward for a boundary face, so
    a face's owner sees it as outward and its neighbour sees it as
    inward. Generic over any `(mesh.num_faces,)` array regardless of
    which scheme produced it -- `step` (below) uses this for its own
    advection/diffusion combination, and TASK-027 reuses it for its own
    concrete `DivergenceScheme`, rather than reimplementing the same
    geometric arithmetic a second time.
    """
    result = torch.zeros(mesh.num_cells, dtype=torch.float64)
    for face in range(mesh.num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        contribution = face_values[face] * mesh.face_area(face)
        result[owner] += contribution
        if neighbour is not None:
            result[neighbour] -= contribution

    volumes = torch.tensor(
        [mesh.cell_volume(cell) for cell in range(mesh.num_cells)], dtype=torch.float64
    )
    return result / volumes


def step(
    fields: Mapping[str, Field],
    velocity: VectorField,
    numerics: AssembledNumerics,
    dt: float,
) -> dict[str, Field]:
    """Advance every field in `fields` by `dt`, using `numerics.advection`/
    `.diffusion` (already boundary-aware, per TASK-040's own Design
    decision -- each was constructed with the boundary conditions it
    needs) and `accumulate_flux_to_cells` to build a `derivative`
    function, then `numerics.time_integration.advance(...)` to advance
    the fields with it.

    Does not mutate `fields`, any field in it, `velocity`, or `numerics`
    -- the same contract `TimeIntegrator.advance` already carries,
    extended to its caller.

    **`derivative` is a closure, not a precomputed value (TASK-025,
    `adr/ADR-008`).** `TimeIntegrator.advance`'s second parameter is a
    function of state, not a fixed mapping, precisely so a multi-stage
    integrator (RK4) can ask for the derivative again at an intermediate
    state it constructs -- this is what makes that re-evaluation possible
    without `step` itself knowing which integrator is configured.
    `velocity` and `mesh` are captured once, at the top of this call, and
    stay fixed across every evaluation `derivative` is asked for within
    it -- `step` only ever advances `fields`; `velocity` is external
    input here, not something RK4's own sub-stages evolve (Stage 5's
    pressure coupling is what will eventually advance it).

    **Combining the two face-flux contributions into one derivative**
    follows `docs/handbook/numerical-methods/fvm.md`'s own conservation
    equation directly: `d/dt \\int_V \\rho\\phi\\,dV = -\\oint_{\\partial V}
    \\rho\\phi\\mathbf{u}\\cdot\\mathbf{n}\\,dA + \\oint_{\\partial V}
    \\Gamma\\nabla\\phi\\cdot\\mathbf{n}\\,dA + \\text{source}` -- the
    advective face flux enters with a minus sign (it is *subtracted* from
    the rate of change), the
    diffusive face flux with a plus sign. So the derivative accumulated
    per cell is `accumulate_flux_to_cells(mesh, diffusion_flux -
    advection_flux)`, not the sum of the two. Nothing in `engine.md`/
    `icds.md` pins this down at the implementation level (deliberately --
    `AdvectionScheme`/`DiffusionScheme`'s own docstrings only promise "the
    ... contribution to that field's flux at each face"), so this is a
    real design decision, made here rather than left for whichever
    concrete scheme (TASK-023/024) happened to be built first to
    improvise -- see `docs/planning/roadmap.md` TASK-040's own Design
    decisions for the recorded version of this paragraph.

    Raises `MismatchedMeshError` if any field in `fields` is not defined
    over the same mesh as `velocity`, and `PressureFieldTransportError`
    (TASK-032) if `fields` contains a `PressureField` -- pressure is
    solved from the incompressibility constraint, never transported.
    """
    mesh = velocity.mesh
    for name, field in fields.items():
        if isinstance(field, PressureField):
            raise PressureFieldTransportError(
                f"field {name!r} is a PressureField -- pressure is solved, not transported"
            )
        if field.mesh is not mesh:
            raise MismatchedMeshError(
                f"field {name!r} is defined over a different mesh than the velocity field"
            )

    def derivative(state: Mapping[str, Field]) -> dict[str, torch.Tensor]:
        result: dict[str, torch.Tensor] = {}
        for name, field in state.items():
            advective_flux = numerics.advection.flux(field, velocity)
            diffusive_flux = numerics.diffusion.flux(field)
            result[name] = accumulate_flux_to_cells(mesh, diffusive_flux - advective_flux)
        return result

    return numerics.time_integration.advance(fields, derivative, dt)
