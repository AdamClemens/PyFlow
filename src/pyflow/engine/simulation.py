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
from dataclasses import dataclass
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

import torch

from pyflow.engine.field import Field
from pyflow.engine.mesh import Mesh, StructuredCartesianMesh
from pyflow.engine.scalar_field import PressureField, ScalarField
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


@dataclass(frozen=True)
class _FluxGeometry:
    """`accumulate_flux_to_cells`'s own per-mesh geometry, gathered once
    instead of re-read from `Mesh` on every call -- see that function's
    own docstring for why.
    """

    owner_ids: torch.Tensor
    neighbour_ids: torch.Tensor
    has_neighbour: torch.Tensor
    face_areas: torch.Tensor
    cell_volumes: torch.Tensor


_flux_geometry_cache: WeakKeyDictionary[Mesh, _FluxGeometry] = WeakKeyDictionary()


def _flux_geometry(mesh: Mesh) -> _FluxGeometry:
    """Built once per distinct `mesh` and cached for as long as the mesh
    object itself lives (`WeakKeyDictionary`, keyed by identity -- the
    same "cached by mesh identity, not equality" reasoning
    `PISO._cached_poisson_matrix` already established, applied here to a
    module-level free function with no instance to attach a cache
    attribute to). `Mesh`/`StructuredCartesianMesh` define no
    `__slots__`/`__hash__`/`__eq__`, so default identity hashing and weak
    referencing both apply with no further change needed.

    Found while investigating a narrower fix to `PISO`'s own Rhie-Chow
    correction loop (`src/pyflow/engine/CLAUDE.md`'s own entry for the
    full finding): this geometry -- which face touches which cell(s), each
    face's area, each cell's volume -- depends only on the mesh, never on
    the `face_values` a particular call is reducing, so re-reading it via
    `Mesh`'s own per-element accessors on every call was pure waste,
    exactly the shape `_poisson_matrix`'s own caching fix already found
    and fixed for a different piece of geometry.
    """
    cached = _flux_geometry_cache.get(mesh)
    if cached is not None:
        return cached

    num_faces = mesh.num_faces
    owner_ids = torch.zeros(num_faces, dtype=torch.long)
    neighbour_ids = torch.zeros(num_faces, dtype=torch.long)
    has_neighbour = torch.zeros(num_faces, dtype=torch.bool)
    face_areas = torch.zeros(num_faces, dtype=torch.float64)
    for face in range(num_faces):
        owner, neighbour = mesh.face_neighbours(face)
        owner_ids[face] = owner
        face_areas[face] = mesh.face_area(face)
        if neighbour is not None:
            has_neighbour[face] = True
            neighbour_ids[face] = neighbour
    cell_volumes = torch.tensor(
        [mesh.cell_volume(cell) for cell in range(mesh.num_cells)], dtype=torch.float64
    )

    geometry = _FluxGeometry(owner_ids, neighbour_ids, has_neighbour, face_areas, cell_volumes)
    _flux_geometry_cache[mesh] = geometry
    return geometry


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

    **Vectorised via `_flux_geometry`'s cached arrays, not a per-face
    Python loop, since 2026-09-05** -- measured directly (a disposable
    prototype, not committed) at 275x-1349x faster in isolation across
    four mesh sizes (256 to 16384 cells), with identical results to
    machine precision. This function sits underneath nearly every
    flux-based operator in the engine (`step`'s own derivative closure,
    `GreenGaussGradient`, `GreenGaussDivergence`, `PISO`'s Rhie-Chow
    correction), so the win is not confined to one caller -- but each of
    those callers still has its *own*, separate per-face Python loop
    building the array this function reduces, so a real end-to-end
    timing improves by less than the isolated figure above; that
    remaining cost is unaddressed by this change.
    """
    geometry = _flux_geometry(mesh)
    contribution = face_values * geometry.face_areas
    result = torch.zeros(mesh.num_cells, dtype=torch.float64)
    result.index_add_(0, geometry.owner_ids, contribution)
    interior = geometry.has_neighbour
    result.index_add_(0, geometry.neighbour_ids[interior], -contribution[interior])
    return result / geometry.cell_volumes


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

    **`derivative` also adds `numerics.source_term.source(field, state)`
    (TASK-035, `adr/ADR-010-source-term-state.md`)** -- passed the same
    `state` this evaluation is already computing over, so a source term
    can read a different field's own current value than the one it
    contributes to (a buoyancy term reading temperature while
    contributing to momentum). This module stays field-name-agnostic
    either way: it hands every field to the same configured term and
    accumulates whatever comes back, never asking which field is which
    (Stage 6 Completion Criterion 1's own structural check, the same
    discipline this module already keeps for momentum's own name). The default
    (`NumericsConfig.source_term: "none"`) contributes exact zero to
    every field, so a run naming no source term advances identically to
    before this addition.
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
            source = numerics.source_term.source(field, state)
            result[name] = accumulate_flux_to_cells(mesh, diffusive_flux - advective_flux) + source
        return result

    return numerics.time_integration.advance(fields, derivative, dt)


@dataclass(frozen=True)
class NavierStokesStepResult:
    """The three parts of one `navier_stokes_step` call, each on its own
    field rather than folded into a single returned mapping -- Stage 5
    Completion Criterion 4's own "each part observable, not only the end
    state" (`docs/planning/roadmap.md` TASK-034).

    `fields` is the fully advanced state: every entry `step` advanced,
    with momentum's own two components replaced by their corrected
    values. `provisional_velocity` is the predictor's own output, before
    correction -- divergent in general. `corrected_velocity`/`pressure`
    are exactly `numerics.pressure_coupling.correct`'s own return values.
    """

    fields: dict[str, Field]
    provisional_velocity: VectorField
    corrected_velocity: VectorField
    pressure: ScalarField


def navier_stokes_step(
    fields: Mapping[str, Field],
    velocity_field_name: str,
    numerics: AssembledNumerics,
    dt: float,
) -> NavierStokesStepResult:
    """One incompressible Navier-Stokes timestep (TASK-034, Stage 5):
    predictor, corrector, corrected state -- the fractional-step sequence
    `docs/handbook/numerical-methods/pressure-velocity-coupling.md`
    describes. **The projection sits once per timestep, outside
    `TimeIntegrator` entirely**, not inside any of RK4's own four stage
    evaluations -- Stage 5's own design question five, resolved by the
    maintainer in favour of the classical arrangement: the momentum
    predictor is fully explicit, with no pressure term at all, and the
    corrector loop (`PressureCoupling.correct`) projects the *result* of
    that predictor once, not each of RK4's own intermediate states.

    `velocity_field_name` names which two entries of `fields`
    (`VectorField.component_name(velocity_field_name, 0)`/`(..., 1)`) are
    momentum's own components -- an explicit parameter, not a fixed
    convention baked into this module, so this function keeps Stage 5
    Completion Criterion 1's own structural guarantee intact: no
    hardcoded component-name pair anywhere in this file's own source
    (`tests/features/velocity_field_support.feature`'s own check,
    `inspect.getsource(simulation)`, still passes unchanged with this
    function added).

    **Predictor:** every entry of `fields` -- momentum's own two
    components and any other transported field alongside them (a scalar
    transported by the same velocity, say) -- advances through the
    ordinary `step` path above, self-advected by the *current* (not yet
    corrected) velocity, with no pressure term. **Corrector:** the two
    advanced momentum components are reassembled into a provisional
    `VectorField` and handed to `numerics.pressure_coupling.correct`,
    which projects it onto a divergence-free field and reports the
    pressure consistent with that projection -- reached only through the
    configured `PressureCoupling`/`LinearSolver`, never a hardcoded
    concrete class (Stage 5 Completion Criterion 13's own substitution
    check). **Corrected state:** the provisional momentum components
    inside the predictor's own result are overwritten with the corrected
    ones; every other field is left exactly as the predictor advanced it,
    since nothing pressure-corrects a scalar.

    Raises whatever `step`/`numerics.pressure_coupling.correct` raise --
    `MismatchedMeshError`/`PressureFieldTransportError` from the former,
    `PressureSolveDidNotConvergeError`/`DivergenceDidNotConvergeError`
    from the latter (`pressure_coupling.py`) -- rather than catching and
    re-wrapping either.
    """
    u_name = VectorField.component_name(velocity_field_name, 0)
    v_name = VectorField.component_name(velocity_field_name, 1)
    u_field = fields[u_name]
    v_field = fields[v_name]
    assert isinstance(u_field, ScalarField)
    assert isinstance(v_field, ScalarField)
    current_velocity = VectorField.assemble([u_field, v_field], velocity_field_name)

    predicted = step(fields, current_velocity, numerics, dt)

    predicted_u = predicted[u_name]
    predicted_v = predicted[v_name]
    assert isinstance(predicted_u, ScalarField)
    assert isinstance(predicted_v, ScalarField)
    provisional_velocity = VectorField.assemble([predicted_u, predicted_v], velocity_field_name)

    corrected_velocity, pressure = numerics.pressure_coupling.correct(provisional_velocity, dt)

    new_fields = dict(predicted)
    for component in corrected_velocity.decompose():
        new_fields[component.name] = component

    return NavierStokesStepResult(
        fields=new_fields,
        provisional_velocity=provisional_velocity,
        corrected_velocity=corrected_velocity,
        pressure=pressure,
    )


_STABILITY_SAFETY_FACTOR = 0.25
"""Multiplies the tighter of the CFL/diffusive stability limits below to
get a timestep this project's own explicit RK4 predictor -- first-order
upwind advection plus central-difference diffusion, `navier_stokes_step`'s
own scheme combination -- actually stays stable at. **Measured directly
with a disposable prototype script before being trusted, not derived
analytically** (`docs/planning/roadmap.md` TASK-034's own design
question four, "the derivation is stated in the scenario either way"):
swept across a mixed advection/diffusion regime, a diffusion-dominated
regime, and an advection-dominated regime alike, `0.3` was the largest
factor that stayed stable for 500 steps in every regime tried and `0.35`
already blew up in the mixed one; `0.25` keeps real margin below that
measured edge rather than shipping a value discovered exactly at the
boundary of blowing up.
"""


def stable_timestep(
    mesh: StructuredCartesianMesh,
    viscosity: float,
    velocity_scale: float,
    safety_factor: float = _STABILITY_SAFETY_FACTOR,
) -> float:
    """A timestep within this scheme combination's own explicit stability
    limit on `mesh`, for a flow whose characteristic speed is
    `velocity_scale` and whose viscosity is `viscosity` (TASK-034, Stage
    5's own design question four -- "the timestep becomes derivable from
    the mesh and the configured viscosity", chosen over a separately
    hand-tuned timestep per mesh resolution, which `docs/planning/
    roadmap.md` TASK-034 itself names as "a convergence study measuring
    the tuning" rather than a real one).

    Explicit RK4 is stability-limited two ways at once, and the tighter
    one governs: the CFL condition (`dx / velocity_scale`, advection) and
    the diffusive limit (`dx**2 / viscosity`, central-difference
    diffusion) -- both scale differently under mesh refinement (the first
    linearly in `dx`, the second quadratically), so a single fixed
    timestep that is stable at a coarse resolution is guaranteed unstable
    at a finer one. `dx` is this mesh's own smallest cell spacing (`min`
    of its two axes, so a non-square mesh is governed by its tighter
    axis); `velocity_scale <= 0` (the periodic null test's own zero-
    forcing, non-advecting fixtures never call this at all, but a caller
    that does pass one gets a well-defined answer rather than a division
    by zero) is treated as "no advective limit", leaving the diffusive
    one alone to govern.
    """
    north_face = next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "north")
    west_face = next(f for f in range(mesh.num_faces) if mesh.boundary_face_name(f) == "west")
    dx = min(float(mesh.face_area(north_face)), float(mesh.face_area(west_face)))
    diffusive_limit = dx**2 / viscosity
    if velocity_scale <= 0:
        return safety_factor * diffusive_limit
    convective_limit = dx / velocity_scale
    return safety_factor * min(convective_limit, diffusive_limit)
