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
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.boundary_condition import BoundaryCondition
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion
from pyflow.engine.numerics.divergence import GreenGaussDivergence
from pyflow.engine.numerics.gradient import GreenGaussGradient
from pyflow.engine.numerics.linear_solver import LinearSolver
from pyflow.engine.scalar_field import PressureField, ScalarField
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
    """A genuine corrector *loop* (TASK-033, Stage 5): repeats a
    dt-scaled pressure-correction pass -- solve `Laplacian(dp) =
    div(u) / dt`, accumulate `p += dp`, correct `u -= dt * grad(dp)` --
    until the corrected velocity's own divergence reaches `tolerance` or
    `max_iterations` is exhausted. **Registered under `"piso"`, and
    genuinely PISO (Pressure-Implicit with Splitting of Operators) for
    the first time**: TASK-027 (Stage 4) registered the name for a single
    pass, honestly scoped and documented as not yet the real algorithm
    (see that task's own Design decision Two, `docs/planning/roadmap.md`)
    -- this is the task that closes that gap, per Stage 5 Completion
    Criterion 3's own "whether `piso` is now genuinely multi-pass, or has
    been renamed" instruction.

    **Design question three's answer, found by numerical prototyping
    (`docs/planning/roadmap.md` TASK-033), not reasoned about in
    advance** -- TASK-027 already showed that guessing here produces a
    confident wrong answer: composing `GreenGaussGradient`/
    `GreenGaussDivergence` into a Poisson matrix is provably not
    symmetric, and three correction strategies tried without momentum
    coefficients each left most of the original divergence in place
    (46-54% reduction for a single naive pass). **The missing momentum
    coefficient `a_P` is simply `dt`.** Rhie-Chow interpolation's own
    weight is `V / a_P`; a real momentum equation's `a_P` bundles the
    unsteady term (`V / dt`) with advection/diffusion's own implicit
    contributions, but PyFlow's momentum predictor is fully explicit
    (RK4, no pressure term, Stage 5's own design decision that "the
    correction sits outside the integrator, once per timestep") -- so the
    only term `a_P` has to carry here *is* the unsteady one, `a_P = V /
    dt`, and `V / a_P` cancels to exactly `dt`. Because PyFlow's mesh has
    uniform cell volume (`docs/implementation/mvp.md`), `dt` is the same
    constant for every cell -- no per-cell momentum operator, no widened
    interface, no ADR. **Verified directly with disposable prototype
    scripts before writing any test or implementation code** (not
    committed, the same discipline TASK-026/027 both used): a Rhie-Chow
    face-velocity correction built from this `dt` weight, paired with
    the *same* compact `CentralDifferenceDiffusion`-based Laplacian used
    for both the correction term's own face-pressure difference and the
    Poisson matrix (rather than a separately-composed Gradient/Divergence
    pair, which TASK-027 already proved is not the discrete adjoint of
    itself), restores the discrete integration-by-parts identity exactly
    -- confirmed by driving a manufactured, non-axis-aligned provisional
    velocity field's divergence (measured Rhie-Chow-consistently, not by
    `GreenGaussDivergence`'s own naive face averaging, which is precisely
    the measure that does *not* see this) to floating-point zero in a
    single corrector pass, for both a linear and a genuinely nonlinear
    fixture -- a dramatically different outcome from TASK-027's own
    "genuine Rhie-Chow... converging far too slowly" finding, because
    that attempt paired Rhie-Chow with the composed (non-adjoint)
    Gradient/Divergence pair for the matrix instead of the compact one.

    **`tolerance`/`max_iterations` (constructor-bound, both new) are
    "outer-loop state the strategy owns"** -- the third of Stage 5's own
    three candidate answers to design question three (a widened
    `PressureCoupling.correct`, a momentum operator handed in at
    construction, or outer-loop state), chosen because it needs no
    change to `PressureCoupling`'s own abstract signature at all: `dt`
    was already `correct`'s own second parameter (`adr/ADR-009`), and
    the loop's own tolerance/iteration-limit are exactly the kind of
    tunable `ConjugateGradientSolver`'s own `tolerance`/`max_iterations`
    already established the precedent for -- bound at construction, not
    per call. Both default to `1e-6`/`50`, matching
    `NumericsConfig.pressure_correction_tolerance`/
    `pressure_correction_max_iterations`'s own defaults, so every
    existing call site that only passes `(linear_solver,
    boundary_conditions)` keeps working unchanged.

    **`last_divergence_history` is the recorded per-iteration sequence**
    (populated on both success and `DivergenceDidNotConvergeError`) --
    Criterion 3's own "the sequence asserted, not just its last value"
    needs somewhere to read it back from without widening `correct`'s own
    return type.

    **The Poisson matrix is still built via `CentralDifferenceDiffusion`**
    (`diffusion_coefficient=1.0`, pressure's own zero-gradient boundary
    condition on every wall), reusing TASK-024's already-tested,
    already-symmetric compact Laplacian -- built once per `correct` call
    and reused across every corrector pass within it, since it depends
    only on the fixed mesh/boundary conditions, never on the current
    velocity or pressure. `GreenGaussDivergence` still computes the
    "simple-averaged" half of the Rhie-Chow-corrected divergence (the
    correction term this task adds is a small, separate face loop, added
    on top rather than duplicating `GreenGaussDivergence`'s own
    boundary-aware logic); `GreenGaussGradient` still computes both the
    cell-centred pressure gradient the velocity correction is built from
    and the per-cell gradients the Rhie-Chow correction term needs.

    **`periodic_pairs` (added TASK-034, Stage 5) is a new fifth,
    defaulted constructor parameter -- `PISO`'s own pressure treatment
    had no periodic case at all before this, unconditionally
    `UnconfiguredBoundaryFaceError` for any periodic boundary face (see
    `gradient.py`/`divergence.py`'s own entries).** Found while building
    TASK-034's mandated "uniform flow on a fully periodic domain" null
    test (Stage 5 Completion Criterion 4): that scenario cannot reach
    `PISO` at all without this, since even *measuring* an already
    divergence-free field's divergence goes through `GreenGaussDivergence`,
    which raised for every periodic face regardless of the field's actual
    values. Threaded to `_diffusion` (the Poisson matrix, which already
    knew how to be periodic via `CentralDifferenceDiffusion`'s own
    TASK-030 support -- only `PISO` was passing it a hardcoded `{}`),
    `_gradient`, `_divergence`, and `_rhie_chow_divergence`'s own
    per-face loop (a periodic face gets the same Rhie-Chow correction an
    interior face does, via `mesh.wrapped_neighbour_cell` and the same
    doubled-distance convention `CentralDifferenceDiffusion` already
    established). Defaults to an empty mapping, so every existing call
    site that only passes `(linear_solver, boundary_conditions)` keeps
    working unchanged, the same courtesy `tolerance`/`max_iterations`
    already extend. **Verified directly, not assumed**: a uniform,
    non-axis-aligned velocity field on a genuinely periodic mesh measures
    exactly `0.0` divergence through this path, so `correct`'s very first
    iteration returns without ever calling the linear solver -- the
    physically correct answer for a flow that is already steady, and the
    reason this task's own periodic null test needed no further PISO
    correctness work beyond making the measurement possible at all.
    """

    def __init__(
        self,
        linear_solver: LinearSolver,
        boundary_conditions: Mapping[str, BoundaryCondition],
        tolerance: float = 1e-6,
        max_iterations: int = 50,
        periodic_pairs: Mapping[str, str] = MappingProxyType({}),
    ) -> None:
        super().__init__(linear_solver)
        self._tolerance = tolerance
        self._max_iterations = max_iterations
        self._periodic_pairs = periodic_pairs
        pressure_boundary_conditions = MappingProxyType(
            {name: _ZeroGradientPressureCondition() for name in _PRESSURE_BOUNDARY_FACE_NAMES}
        )
        self._diffusion = CentralDifferenceDiffusion(
            pressure_boundary_conditions,
            periodic_pairs,
            diffusion_coefficient=1.0,
        )
        self._gradient = GreenGaussGradient(pressure_boundary_conditions, periodic_pairs)
        self._divergence = GreenGaussDivergence(boundary_conditions, periodic_pairs)
        self.last_divergence_history: tuple[float, ...] = ()
        self._cached_poisson_mesh: StructuredCartesianMesh | None = None
        self._cached_poisson_matrix: torch.Tensor | None = None

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        mesh = provisional_velocity.mesh
        assert isinstance(mesh, StructuredCartesianMesh)
        matrix = self._poisson_matrix(mesh)

        velocity = provisional_velocity
        pressure = PressureField(mesh, "pressure", initial_value=0.0)
        history: list[float] = []

        for iteration in range(self._max_iterations + 1):
            gradient = self._gradient.gradient(pressure)
            divergence = self._rhie_chow_divergence(velocity, pressure, gradient, dt)
            max_divergence = float(divergence.abs().max())
            history.append(max_divergence)
            if max_divergence <= self._tolerance:
                self.last_divergence_history = tuple(history)
                return velocity, pressure
            if iteration == self._max_iterations:
                break

            result = self._linear_solver.solve(matrix, -divergence / dt)
            if not result.converged:
                self.last_divergence_history = tuple(history)
                raise PressureSolveDidNotConvergeError(
                    f"pressure correction did not converge in {result.iterations} iterations"
                )
            correction = PressureField(mesh, "pressure_correction")
            correction.values[:] = result.solution

            new_pressure = PressureField(mesh, "pressure")
            new_pressure.values[:] = pressure.values + correction.values
            pressure = new_pressure

            new_velocity = velocity.copy()
            new_velocity.values[:] = velocity.values - dt * self._gradient.gradient(correction)
            velocity = new_velocity

        self.last_divergence_history = tuple(history)
        raise DivergenceDidNotConvergeError(
            f"pressure correction loop did not reach tolerance {self._tolerance} within "
            f"{self._max_iterations} iterations; divergence history: {history}"
        )

    def _poisson_matrix(self, mesh: StructuredCartesianMesh) -> torch.Tensor:
        """Built once per distinct `mesh` and cached for the rest of this
        `PISO` instance's own lifetime (TASK-034, Stage 5), not rebuilt on
        every `correct` call as before -- found while measuring the Lid-
        Driven Cavity validation's own real runtime (Stage 5 Completion
        Criterion 5's "the runtime this implies is part of the criterion,
        not a surprise to discover in CI"): this construction is
        `O(num_cells * num_faces)` (one full `self._diffusion.flux` call
        per column), which used to dominate measured per-timestep cost by
        roughly 70-90% at MVP cavity mesh sizes (8x8 through 16x16) before
        the caching above amortized it across the whole run. The matrix
        depends only on `mesh` and this instance's own fixed pressure
        boundary treatment -- never on the current velocity, pressure, or
        `dt` -- so nothing about repeating it across timesteps was ever
        buying correctness. Cached by mesh *identity*, not equality: a
        real run always hands `correct` the same mesh object every
        timestep, so the common case is a cache hit; a genuinely
        different mesh object (unusual -- no code path in this repository
        reuses one `PISO` instance across meshes today) safely recomputes
        rather than serving a stale matrix.

        **Stored sparse (CSR), not dense, since 2026-09-05
        (`adr/ADR-011-sparse-linear-solver-matrix.md`).** The probe loop
        itself is unchanged -- still one `self._diffusion.flux` call per
        column, still `O(num_cells * num_faces)` to build -- only the
        final assembly differs: each column's nonzero rows (an
        interior/periodic-face stencil touches only a handful of cells,
        never all of them) are collected as sparse `(row, col, value)`
        triples across every column, then built once via `coalesce()`
        (summing any duplicate
        `(row, col)` entries, though none arise here since each column
        contributes each row at most once) and converted to CSR. This
        replaces an `O(num_cells^2)` dense tensor (a 128x128 mesh needs
        ~2.1GB at float64) with `O(nnz)` storage, and turns every
        downstream `ConjugateGradientSolver` matvec from
        `O(num_cells^2)` into `O(nnz)` -- measured directly as a real
        2.56x solve-only speedup at 1024 cells, growing with resolution.

        **This construction's own `O(num_cells * num_faces)` build cost
        is unchanged, and dominates a short run.** Measured directly,
        not assumed: at 1024 cells this build costs ~52s against ~0.02s
        for the solve alone on the same mesh -- three orders of
        magnitude apart. The ~10x-per-4x-cells slowdown measured on
        `examples/experiments/smoke_transport_high_res.yaml` (a five-frame
        demo) is dominated by *this* cost, not the solve, and this change
        does not fix it -- see `adr/ADR-011-sparse-linear-solver-matrix.md`'s
        own Consequences for the honest accounting. A direct per-face
        construction (skipping this probe loop entirely, `O(num_faces)`
        rather than `O(num_cells * num_faces)`) would address the build
        itself; considered and rejected for now -- see the ADR's
        Alternatives.
        """
        if self._cached_poisson_mesh is mesh and self._cached_poisson_matrix is not None:
            return self._cached_poisson_matrix
        num_cells = mesh.num_cells
        row_indices: list[torch.Tensor] = []
        col_indices: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        for column in range(num_cells):
            basis = ScalarField(mesh, "e")
            basis.values[column] = 1.0
            column_values = -accumulate_flux_to_cells(mesh, self._diffusion.flux(basis))
            nonzero_rows = column_values.nonzero(as_tuple=True)[0]
            if nonzero_rows.numel() == 0:
                continue
            row_indices.append(nonzero_rows)
            col_indices.append(torch.full_like(nonzero_rows, column))
            values.append(column_values[nonzero_rows])
        indices = torch.stack([torch.cat(row_indices), torch.cat(col_indices)])
        matrix = (
            torch.sparse_coo_tensor(indices, torch.cat(values), (num_cells, num_cells))
            .coalesce()
            .to_sparse_csr()
        )
        self._cached_poisson_mesh = mesh
        self._cached_poisson_matrix = matrix
        return matrix

    def _rhie_chow_divergence(
        self,
        velocity: VectorField,
        pressure: PressureField,
        pressure_gradient: torch.Tensor,
        dt: float,
    ) -> torch.Tensor:
        """`GreenGaussDivergence`'s own simple-averaged divergence, minus
        a Rhie-Chow correction at every *interior* face: `dt * [(p_N -
        p_P) / distance - avg(gradP, gradN) . n]` -- the mismatch between
        the direct face-normal pressure difference and the average of
        each neighbour's own cell-centred gradient, which is exactly what
        the naive simple-averaged divergence cannot see and what makes it
        fail to be the discrete adjoint of the compact Laplacian
        `correct`'s own Poisson solve uses. Zero at every boundary face --
        there is no neighbour to Rhie-Chow-interpolate against, and
        `GreenGaussDivergence`'s own boundary handling (this class's
        `boundary_conditions`, velocity's own) already supplies the
        correct value there.
        """
        mesh = velocity.mesh
        assert isinstance(mesh, StructuredCartesianMesh)
        naive = self._divergence.divergence(velocity)

        correction_face = torch.zeros(mesh.num_faces, dtype=torch.float64)
        for face in range(mesh.num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            distance = mesh.face_centroid_distance(face)
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
                    distance = 2 * distance
                else:
                    continue
            normal_x, normal_y = mesh.face_normal(face)
            direct = (pressure.value_at(neighbour) - pressure.value_at(owner)) / distance
            gx_o, gy_o = float(pressure_gradient[owner, 0]), float(pressure_gradient[owner, 1])
            gx_n, gy_n = (
                float(pressure_gradient[neighbour, 0]),
                float(pressure_gradient[neighbour, 1]),
            )
            avg_normal = ((gx_o + gx_n) / 2) * normal_x + ((gy_o + gy_n) / 2) * normal_y
            correction_face[face] = dt * (direct - avg_normal)
        return naive - accumulate_flux_to_cells(mesh, correction_face)


class PressureSolveDidNotConvergeError(RuntimeError):
    """Raised when one corrector pass's own inner linear solve fails to
    converge -- returning its unconverged solution anyway would be
    exactly the "plausible-looking wrong answer" failure mode
    `docs/practices.md` names repeatedly (pan scale, mesh accessors,
    `ConjugateGradientSolver`'s own honest treatment of the same flag).
    """


class DivergenceDidNotConvergeError(RuntimeError):
    """Raised when `PISO.correct`'s own outer corrector loop exhausts
    `max_iterations` without the divergence reaching `tolerance` -- a
    different failure from `PressureSolveDidNotConvergeError` (every
    inner linear solve can converge just fine while the outer loop still
    fails to reduce divergence enough, e.g. an inner solver tolerance too
    loose relative to the outer one). The same honesty: a best-effort
    velocity field that never reached the configured tolerance is not
    returned as if it had.
    """
