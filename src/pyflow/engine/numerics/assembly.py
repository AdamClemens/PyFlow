"""assembly.py (TASK-021): resolves each of `NumericsConfig`'s six
configured names to a real implementation instance --
`docs/planning/roadmap.md` TASK-021's own design decision: assembly
lives beside the interfaces it instantiates, not in `bootstrap.py`,
which only *calls* `assemble_numerics` the same way it already calls
`StructuredCartesianMesh.from_config`.

**Six independent registries, one dict each, not an `if`/`match`
chain.** `create_canvas` (`rendering/canvas.py`) gestures at
name-selects-implementation with an `if`/`elif` over two hardcoded
backends; that shape cannot satisfy Stage 3 Completion Criterion 3
("adding an implementation requires editing no existing function body")
because a chain has to be edited for every new name. A registry a caller
can add to (`register_advection_scheme`, and its five siblings) is what
makes that criterion true by construction rather than by discipline: the
`register_a_new_name_resolves_without_editing_assembly` test in
`tests/unit/numerics/test_assembly.py` proves it directly.

**Why default registrations exist under `src/` at all, when Stage 3
Completion Criterion 1 says no concrete implementation of these six may
ship here:** Criterion 8 requires a real `pyflow run` subprocess to
assemble all six components and report the result -- a subprocess
imports only `src/pyflow`, so it has nothing to assemble into unless
something registers under the exact MVP names `NumericsConfig`'s
defaults already validate (`"first_order_upwind"`, `"central_difference"`,
`"rk4"`, `"conjugate_gradient"`, `"piso"`, `"dirichlet"`, `"neumann"`).
**Explicit, maintainer-decided exception to Criterion 1's letter,
2026-08-23** (`docs/planning/roadmap.md`'s Stage 3 Completion Criteria,
Criterion 1's own carve-out note): the `_Null*` classes below compute
nothing -- zero flux, an unconverged no-op solve, a pass-through
velocity correction -- and exist solely so the assembly *mechanism* has
something to prove itself against. A real numerical scheme (first-order
upwind, PISO, Conjugate Gradient) still does not ship until Stage 4;
these are the one narrow exception, named as such everywhere they
appear, not a first real implementation in disguise.

**Retiring them is Stage 4's job, and it is enforced rather than
remembered:** the task that lands a real scheme deletes that name's
`register_*` line at the bottom of this module in the same change.
`DuplicateSchemeError` (below) makes shadowing one an import-time error,
because the alternative failure is silent -- a run reporting
`first_order_upwind` while computing zero flux, which no name-based
check can distinguish.

**`periodic` boundary faces resolve no `BoundaryCondition` object.**
`boundary_condition.py`'s own scope (TASK-019) is deliberately just the
Dirichlet/Neumann shapes -- periodic fits neither `value` nor `gradient`
-- so `assemble_numerics` reports a periodic face's configured type in
`AssembledNumerics.names` but omits it from `.boundary_conditions`
entirely, rather than fabricating an object the interface has no shape
for.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

import torch

from pyflow.configuration.schema import BoundaryFaceConfig, NumericsConfig
from pyflow.engine.field import Field
from pyflow.engine.numerics.advection import AdvectionScheme
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import DiffusionScheme
from pyflow.engine.numerics.linear_solver import LinearSolver, LinearSolverResult
from pyflow.engine.numerics.pressure_coupling import PressureCoupling
from pyflow.engine.numerics.time_integrator import TimeIntegrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField

_BOUNDARY_FACE_NAMES = ("north", "south", "east", "west")


class UnknownSchemeError(ValueError):
    """Raised when a configured name has no registered factory."""


class DuplicateSchemeError(ValueError):
    """Raised when a name is registered a second time with a *different*
    factory.

    The registries below are module-level and populated by import side
    effect, so without this the second registration would silently win
    and which one that is would depend on import order. Re-registering
    the identical factory stays a no-op, since a module imported twice
    in one session must not raise.

    **This is the guard Stage 4 needs.** `docs/architecture/icds.md`
    says a real scheme "registers under the same name a user already
    configures" -- the same names the `_Null*` reference implementations
    at the bottom of this module occupy. Shadowing one instead of
    removing it would leave a run reporting `first_order_upwind` while
    computing zero flux, and `AssembledNumerics.names` echoes the
    configured name either way, so no name-based check could tell.
    Whoever lands a real scheme deletes that name's reference
    registration in the same change; this makes forgetting an
    import-time error rather than a silent wrong answer.
    """


@dataclass(frozen=True)
class AssembledNumerics:
    """The six numerical components, resolved to live instances, plus
    the configured name each was resolved from (`names`) -- what
    `bootstrap()` reports as "the assembled set" (Stage 3 Completion
    Criterion 8), since comparing name strings against a YAML file is
    direct where comparing live objects would not be.
    """

    advection: AdvectionScheme
    diffusion: DiffusionScheme
    time_integration: TimeIntegrator
    linear_solver: LinearSolver
    pressure_coupling: PressureCoupling
    boundary_conditions: Mapping[str, BoundaryCondition]
    names: Mapping[str, str]


_advection_registry: dict[str, Callable[[Mapping[str, BoundaryCondition]], AdvectionScheme]] = {}
_diffusion_registry: dict[str, Callable[[Mapping[str, BoundaryCondition]], DiffusionScheme]] = {}
_time_integrator_registry: dict[str, Callable[[], TimeIntegrator]] = {}
_linear_solver_registry: dict[str, Callable[[], LinearSolver]] = {}
_pressure_coupling_registry: dict[str, Callable[[LinearSolver], PressureCoupling]] = {}
_boundary_condition_registry: dict[str, Callable[[BoundaryFaceConfig], BoundaryCondition]] = {}


def _register[F](registry: dict[str, F], name: str, factory: F, component: str) -> None:
    """Bind `name` to `factory` in `registry`, refusing to overwrite a
    different factory already bound to it (`DuplicateSchemeError`).
    """
    existing = registry.get(name)
    if existing is not None and existing is not factory:
        raise DuplicateSchemeError(
            f"{component} name {name!r} is already registered to "
            f"{getattr(existing, '__name__', existing)!r}; remove that registration "
            f"before registering {getattr(factory, '__name__', factory)!r} under it"
        )
    registry[name] = factory


def register_advection_scheme(
    name: str, factory: Callable[[Mapping[str, BoundaryCondition]], AdvectionScheme]
) -> None:
    """Make `name` resolve to `factory(boundary_conditions)` in future
    `assemble_numerics` calls -- `boundary_conditions` is the same
    face-name-keyed mapping `AssembledNumerics.boundary_conditions`
    carries, resolved before advection/diffusion so a concrete scheme can
    receive the boundary conditions it needs at construction (TASK-040's
    own Design decision, `docs/planning/roadmap.md`), rather than the
    orchestrator substituting a value after the fact.
    """
    _register(_advection_registry, name, factory, "advection")


def register_diffusion_scheme(
    name: str, factory: Callable[[Mapping[str, BoundaryCondition]], DiffusionScheme]
) -> None:
    _register(_diffusion_registry, name, factory, "diffusion")


def register_time_integrator(name: str, factory: Callable[[], TimeIntegrator]) -> None:
    _register(_time_integrator_registry, name, factory, "time_integration")


def register_linear_solver(name: str, factory: Callable[[], LinearSolver]) -> None:
    _register(_linear_solver_registry, name, factory, "linear_solver")


def register_pressure_coupling(
    name: str, factory: Callable[[LinearSolver], PressureCoupling]
) -> None:
    _register(_pressure_coupling_registry, name, factory, "pressure_coupling")


def register_boundary_condition_type(
    type_name: str, factory: Callable[[BoundaryFaceConfig], BoundaryCondition]
) -> None:
    _register(_boundary_condition_registry, type_name, factory, "boundary_condition")


def _resolve[T](registry: Mapping[str, Callable[[], T]], name: str, component: str) -> T:
    factory = registry.get(name)
    if factory is None:
        raise UnknownSchemeError(f"no {component} implementation registered under {name!r}")
    return factory()


def _resolve_with_argument[T, A](
    registry: Mapping[str, Callable[[A], T]], name: str, argument: A, component: str
) -> T:
    """Same as `_resolve`, for the three components whose factory needs
    one constructor argument -- advection/diffusion (the boundary-
    conditions mapping) and pressure_coupling (the resolved
    `LinearSolver`) -- rather than three near-identical inline
    get/raise/call blocks repeating the same lookup (found during
    TASK-040's own review cycle).
    """
    factory = registry.get(name)
    if factory is None:
        raise UnknownSchemeError(f"no {component} implementation registered under {name!r}")
    return factory(argument)


def assemble_numerics(config: NumericsConfig) -> AssembledNumerics:
    """Resolve every name in `config` to a live instance.

    Reads `config` once; the returned `AssembledNumerics` holds
    instances, not a reference back to `config` -- mutating `config`
    afterwards changes nothing about what was already assembled (Stage 3
    Completion Criterion 4).

    **Resolves `boundary_conditions` before advection/diffusion**,
    reordered from Stage 3's sequence (boundary conditions used to
    resolve last) -- TASK-040's own Design decision: a concrete
    advection/diffusion scheme is constructed *with* the boundary
    conditions it needs, so that mapping has to exist before either
    factory is called. Wrapped in `MappingProxyType` before being handed
    to either factory (and stored on the returned `AssembledNumerics`) --
    found during TASK-040's own review cycle: a plain `dict` passed to
    two different factories and then retained on a frozen dataclass is
    shared mutable state with three holders and no defensive copy.
    `AssembledNumerics` being `frozen` stops a caller reassigning its
    *fields*; it does nothing to stop a scheme mutating the mapping one
    of those fields refers to. Genuinely read-only now, not only by
    convention.
    """
    names: dict[str, str] = {}
    boundary_conditions_by_face: dict[str, BoundaryCondition] = {}
    for face_name in _BOUNDARY_FACE_NAMES:
        face_config: BoundaryFaceConfig = getattr(config.boundary_conditions, face_name)
        names[f"boundary_conditions.{face_name}"] = face_config.type
        boundary_factory = _boundary_condition_registry.get(face_config.type)
        if boundary_factory is not None:
            boundary_conditions_by_face[face_name] = boundary_factory(face_config)
    boundary_conditions = MappingProxyType(boundary_conditions_by_face)

    advection = _resolve_with_argument(
        _advection_registry, config.advection, boundary_conditions, "advection"
    )
    diffusion = _resolve_with_argument(
        _diffusion_registry, config.diffusion, boundary_conditions, "diffusion"
    )
    time_integration = _resolve(
        _time_integrator_registry, config.time_integration, "time_integration"
    )
    linear_solver = _resolve(_linear_solver_registry, config.linear_solver, "linear_solver")
    pressure_coupling = _resolve_with_argument(
        _pressure_coupling_registry, config.pressure_coupling, linear_solver, "pressure_coupling"
    )

    names.update(
        {
            "advection": config.advection,
            "diffusion": config.diffusion,
            "time_integration": config.time_integration,
            "linear_solver": config.linear_solver,
            "pressure_coupling": config.pressure_coupling,
        }
    )

    return AssembledNumerics(
        advection=advection,
        diffusion=diffusion,
        time_integration=time_integration,
        linear_solver=linear_solver,
        pressure_coupling=pressure_coupling,
        boundary_conditions=boundary_conditions,
        names=names,
    )


# -- Reference implementations, registered under the MVP names ------------
#
# Every class below computes nothing physical -- see the module docstring
# for why they exist under `src/` at all despite Stage 3 Completion
# Criterion 1.


class _NullAdvectionScheme(AdvectionScheme):
    # Accepts (and ignores) the boundary-conditions mapping every
    # advection factory now receives (TASK-040's Design decision) --
    # this reference scheme computes nothing, so it needs no boundary
    # data, but its constructor must still match the registered shape.
    def __init__(self, boundary_conditions: Mapping[str, BoundaryCondition]) -> None:
        del boundary_conditions

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _NullDiffusionScheme(DiffusionScheme):
    def __init__(self, boundary_conditions: Mapping[str, BoundaryCondition]) -> None:
        del boundary_conditions

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _NullTimeIntegrator(TimeIntegrator):
    def advance(
        self,
        fields: Mapping[str, Field],
        derivatives: Mapping[str, torch.Tensor],
        dt: float,
    ) -> dict[str, Field]:
        return {name: field.copy() for name, field in fields.items()}


class _NullLinearSolver(LinearSolver):
    # `converged=False`, deliberately: this solve computes nothing, and
    # `linear_solver.py`'s own contract exists precisely to stop a solver
    # returning an answer it did not reach. Reporting success for a zero
    # vector would be the "plausible wrong answer" failure that module's
    # docstring names as recorded three times in this repository. It also
    # makes the wiring loud rather than silent: a Stage 4 caller that
    # checks the flag fails immediately if a real solver (TASK-026) has
    # not yet replaced this one, instead of quietly accepting zeros.
    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=False, iterations=0)


class _NullPressureCoupling(PressureCoupling):
    def correct(self, provisional_velocity: VectorField) -> tuple[VectorField, ScalarField]:
        pressure = ScalarField(provisional_velocity.mesh, "pressure")
        return provisional_velocity.copy(), pressure


def _null_boundary_value(face_config: BoundaryFaceConfig) -> float:
    if face_config.velocity is not None:
        return face_config.velocity
    if face_config.pressure is not None:
        return face_config.pressure
    return 0.0


class _NullValueBoundaryCondition(BoundaryCondition):
    def __init__(self, face_config: BoundaryFaceConfig) -> None:
        self._value = _null_boundary_value(face_config)

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "value"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._value


class _NullGradientBoundaryCondition(BoundaryCondition):
    def __init__(self, face_config: BoundaryFaceConfig) -> None:
        self._value = _null_boundary_value(face_config)

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return self._value


register_advection_scheme("first_order_upwind", _NullAdvectionScheme)
register_diffusion_scheme("central_difference", _NullDiffusionScheme)
register_time_integrator("rk4", _NullTimeIntegrator)
register_linear_solver("conjugate_gradient", _NullLinearSolver)
register_pressure_coupling("piso", _NullPressureCoupling)
register_boundary_condition_type("dirichlet", _NullValueBoundaryCondition)
register_boundary_condition_type("neumann", _NullGradientBoundaryCondition)
