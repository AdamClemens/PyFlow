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


_advection_registry: dict[str, Callable[[], AdvectionScheme]] = {}
_diffusion_registry: dict[str, Callable[[], DiffusionScheme]] = {}
_time_integrator_registry: dict[str, Callable[[], TimeIntegrator]] = {}
_linear_solver_registry: dict[str, Callable[[], LinearSolver]] = {}
_pressure_coupling_registry: dict[str, Callable[[LinearSolver], PressureCoupling]] = {}
_boundary_condition_registry: dict[str, Callable[[BoundaryFaceConfig], BoundaryCondition]] = {}


def register_advection_scheme(name: str, factory: Callable[[], AdvectionScheme]) -> None:
    """Make `name` resolve to `factory()` in future `assemble_numerics` calls."""
    _advection_registry[name] = factory


def register_diffusion_scheme(name: str, factory: Callable[[], DiffusionScheme]) -> None:
    _diffusion_registry[name] = factory


def register_time_integrator(name: str, factory: Callable[[], TimeIntegrator]) -> None:
    _time_integrator_registry[name] = factory


def register_linear_solver(name: str, factory: Callable[[], LinearSolver]) -> None:
    _linear_solver_registry[name] = factory


def register_pressure_coupling(
    name: str, factory: Callable[[LinearSolver], PressureCoupling]
) -> None:
    _pressure_coupling_registry[name] = factory


def register_boundary_condition_type(
    type_name: str, factory: Callable[[BoundaryFaceConfig], BoundaryCondition]
) -> None:
    _boundary_condition_registry[type_name] = factory


def _resolve[T](registry: Mapping[str, Callable[[], T]], name: str, component: str) -> T:
    factory = registry.get(name)
    if factory is None:
        raise UnknownSchemeError(f"no {component} implementation registered under {name!r}")
    return factory()


def assemble_numerics(config: NumericsConfig) -> AssembledNumerics:
    """Resolve every name in `config` to a live instance.

    Reads `config` once; the returned `AssembledNumerics` holds
    instances, not a reference back to `config` -- mutating `config`
    afterwards changes nothing about what was already assembled (Stage 3
    Completion Criterion 4).
    """
    advection = _resolve(_advection_registry, config.advection, "advection")
    diffusion = _resolve(_diffusion_registry, config.diffusion, "diffusion")
    time_integration = _resolve(
        _time_integrator_registry, config.time_integration, "time_integration"
    )
    linear_solver = _resolve(_linear_solver_registry, config.linear_solver, "linear_solver")

    pressure_coupling_factory = _pressure_coupling_registry.get(config.pressure_coupling)
    if pressure_coupling_factory is None:
        raise UnknownSchemeError(
            f"no pressure_coupling implementation registered under {config.pressure_coupling!r}"
        )
    pressure_coupling = pressure_coupling_factory(linear_solver)

    names: dict[str, str] = {
        "advection": config.advection,
        "diffusion": config.diffusion,
        "time_integration": config.time_integration,
        "linear_solver": config.linear_solver,
        "pressure_coupling": config.pressure_coupling,
    }
    boundary_conditions: dict[str, BoundaryCondition] = {}
    for face_name in _BOUNDARY_FACE_NAMES:
        face_config: BoundaryFaceConfig = getattr(config.boundary_conditions, face_name)
        names[f"boundary_conditions.{face_name}"] = face_config.type
        boundary_factory = _boundary_condition_registry.get(face_config.type)
        if boundary_factory is not None:
            boundary_conditions[face_name] = boundary_factory(face_config)

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
    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _NullDiffusionScheme(DiffusionScheme):
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
    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        return LinearSolverResult(solution=torch.zeros_like(rhs), converged=True, iterations=0)


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
