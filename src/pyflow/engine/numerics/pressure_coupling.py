"""PressureCoupling (TASK-021): the interface that enforces
incompressibility -- given a provisional velocity field, produce a
corrected, divergence-free one and the pressure field consistent with it
(`docs/architecture/engine.md`'s Pressure-Velocity Coupling contract).

**Takes a `LinearSolver` at construction; a strategy cannot be built
without one.** `docs/architecture/icds.md` names this the one real
cross-layer dependency among the six `adr/ADR-003-modular-numerical-
strategies.md` components -- Stage 3 Completion Criterion 6 makes it
structural rather than advice living in prose. The check is a real
runtime `isinstance` guard, not only a type annotation: a type hint is
not a runtime guarantee, and criterion 6 is about the interface, not
what `mypy` happens to catch.

No dedicated result type: `correct` returns a plain
`tuple[VectorField, ScalarField]` -- this task's own Artifacts Produced
bullet names only the ABC as a new type, the same reasoning
`LinearSolver` follows for its `matrix`/`rhs` pair.

**`correct`'s second parameter, `dt`, was added in TASK-027 (Stage 4,
`adr/ADR-009-pressure-coupling-dt.md`)** -- a real, audited interface
change, the same category `adr/ADR-008-time-integrator-derivative-
callable.md` was for `TimeIntegrator.advance`, not only a registry
addition. `u_corrected = u* - dt * grad(p)` needs `dt` to give the
returned pressure field's units a real physical meaning; nothing before
TASK-027 needed a concrete strategy to exist, so nothing needed this
parameter until then. `PISO` (below) is the first, and so far only,
concrete `PressureCoupling` to use it.

`PISO` (TASK-027, Stage 4) is the first real concrete strategy -- Stage 3
Completion Criterion 1 restricted every implementation of the six
`adr/ADR-003-modular-numerical-strategies.md` components to `tests/`
only through Stage 3; Stage 4 lifts that restriction for the task that
brings each component's real MVP scheme. See `docs/planning/roadmap.md`
TASK-021 for the interface's own design rationale and TASK-027 for the
concrete scheme's, including the collocated-grid limitation its own
docstring below records.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

import torch

from pyflow.engine.field import Field
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.divergence import GreenGaussDivergence
from pyflow.engine.numerics.gradient import GreenGaussGradient
from pyflow.engine.numerics.linear_solver import LinearSolver
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.simulation import accumulate_flux_to_cells
from pyflow.engine.vector_field import VectorField


class PressureCoupling(ABC):
    """Enforces incompressibility given a provisional velocity field."""

    def __init__(self, linear_solver: LinearSolver) -> None:
        if not isinstance(linear_solver, LinearSolver):
            raise TypeError(
                f"linear_solver must be a LinearSolver, got {type(linear_solver).__name__}"
            )
        self._linear_solver = linear_solver

    @property
    def linear_solver(self) -> LinearSolver:
        """The `LinearSolver` this strategy was constructed with."""
        return self._linear_solver

    @abstractmethod
    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        """Return `(corrected_velocity, pressure)` for `provisional_velocity`,
        corrected by one pass of `dt`-scaled pressure correction.

        Must not mutate `provisional_velocity`.
        """


class _ZeroGradientPressureCondition(BoundaryCondition):
    """The impermeable-wall assumption `PISO` (below) applies to pressure
    at every boundary face, internally -- not read from `NumericsConfig`,
    since pressure has no boundary-condition representation there
    (`BoundaryFaceConfig` prescribes velocity or pressure *values*, never
    a zero-normal-gradient wall condition). See TASK-027's own Design
    decision One, `docs/planning/roadmap.md`.
    """

    @property
    def kind(self) -> Literal["value", "gradient"]:
        return "gradient"

    def evaluate(self, field: Field, face: int) -> float:
        self._check_boundary_face(field, face)
        return 0.0


_PRESSURE_BOUNDARY_FACE_NAMES = ("north", "south", "east", "west")


class PISO(PressureCoupling):
    """A single dt-scaled pressure-correction pass (TASK-027): solves the
    Poisson equation `Laplacian(p) = div(u*) / dt` for the pressure
    correction, then returns `u* - dt * grad(p)`.

    **Registered under `"piso"`, but not the full multi-pass Issa PISO
    algorithm** -- honestly scoped to what a single pass, checked in
    isolation, can actually deliver on PyFlow's collocated mesh. See
    `docs/planning/roadmap.md` TASK-027's own Design decision Two for the
    full numerical investigation: composing this task's own
    `GreenGaussGradient`/`GreenGaussDivergence` into a Poisson matrix
    produces one that is provably not symmetric (confirmed both
    algebraically, via the discrete integration-by-parts identity, and
    numerically), so it cannot be solved by `ConjugateGradientSolver` --
    the only registered `LinearSolver`, which requires a symmetric matrix.
    Genuinely suppressing pressure-velocity decoupling under *repeated*
    correction needs Rhie-Chow interpolation, which needs momentum-
    equation coefficients this class's own interface has no way to
    obtain -- that is Stage 5 TASK-033's own claim (Pressure Correction
    Loop), not this one's.

    **The Poisson matrix is built via `CentralDifferenceDiffusion`**
    (`diffusion_coefficient=1.0`, pressure's own zero-gradient boundary
    condition on every wall), reusing TASK-024's already-tested,
    already-symmetric compact Laplacian rather than composing this task's
    own `GradientScheme`/`DivergenceScheme` into a matrix -- the specific
    thing Design decision Two proved does not work. `GreenGaussDivergence`
    still computes the Poisson equation's right-hand side (`div(u*)`,
    using `provisional_velocity`'s own boundary conditions), and
    `GreenGaussGradient` still computes the cell-centred pressure gradient
    the returned corrected velocity is built from -- both real,
    necessary, exercised uses, not decorative registrations.
    """

    def __init__(
        self, linear_solver: LinearSolver, boundary_conditions: Mapping[str, BoundaryCondition]
    ) -> None:
        super().__init__(linear_solver)
        pressure_boundary_conditions = MappingProxyType(
            {name: _ZeroGradientPressureCondition() for name in _PRESSURE_BOUNDARY_FACE_NAMES}
        )
        self._diffusion = CentralDifferenceDiffusion(
            pressure_boundary_conditions, diffusion_coefficient=1.0
        )
        self._gradient = GreenGaussGradient(pressure_boundary_conditions)
        self._divergence = GreenGaussDivergence(boundary_conditions)

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        mesh = provisional_velocity.mesh
        divergence = self._divergence.divergence(provisional_velocity)

        num_cells = mesh.num_cells
        matrix = torch.zeros((num_cells, num_cells), dtype=torch.float64)
        for column in range(num_cells):
            basis = ScalarField(mesh, "e")
            basis.values[column] = 1.0
            matrix[:, column] = -accumulate_flux_to_cells(mesh, self._diffusion.flux(basis))

        result = self._linear_solver.solve(matrix, -divergence / dt)
        if not result.converged:
            raise PressureSolveDidNotConvergeError(
                f"pressure correction did not converge in {result.iterations} iterations"
            )

        pressure = ScalarField(mesh, "pressure")
        pressure.values[:] = result.solution

        corrected = provisional_velocity.copy()
        corrected.values[:] = provisional_velocity.values - dt * self._gradient.gradient(pressure)
        return corrected, pressure


class PressureSolveDidNotConvergeError(RuntimeError):
    """Raised when `PISO.correct`'s own pressure-correction solve fails
    to converge -- returning its unconverged solution anyway would be
    exactly the "plausible-looking wrong answer" failure mode
    `docs/practices.md` names repeatedly (pan scale, mesh accessors,
    `ConjugateGradientSolver`'s own honest treatment of the same flag).
    """
