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
from dataclasses import dataclass
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
        self._pressure_boundary_conditions: Mapping[str, BoundaryCondition] = (
            pressure_boundary_conditions
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
        self._cached_rhie_chow_geometry_mesh: StructuredCartesianMesh | None = None
        self._cached_rhie_chow_geometry: _RhieChowGeometry | None = None

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
        every `correct` call -- see the caching note below for why a
        cache hit is the common case.

        **Direct per-face construction, `O(num_faces)`, since 2026-09-06
        (`adr/ADR-012-direct-poisson-matrix-construction.md`).** Until
        then this walked `num_cells` basis-vector probes through
        `self._diffusion.flux` + `accumulate_flux_to_cells`, `O(num_cells
        * num_faces)` -- `adr/ADR-011-sparse-linear-solver-matrix.md`
        measured that probe loop, not the solve, dominating a short run
        (~52s of a ~1024-cell build against ~0.02s to solve) and
        explicitly named a direct construction as the fix, deferring it
        because it would hard-code two facts true only of *this*
        instance's own current wiring: a zero-gradient pressure boundary
        on every wall, and uniform cell volume. Both are now asserted
        rather than assumed (`_assert_zero_gradient_pressure_boundary`,
        `_assert_uniform_cell_volume`, below), which is what makes
        hard-coding them safe -- a future PISO change that breaks either
        fails loudly building the matrix, not silently.

        The stencil itself: an interior face (owner `o`, neighbour `n`,
        area `a`, centroid distance `d`, shared cell volume `V`,
        `c = gamma * a / (d * V)`) contributes the standard symmetric
        Laplacian entries, `[o,o] += c`, `[n,n] += c`, `[o,n] -= c`,
        `[n,o] -= c` -- the same stencil the old probe loop produced,
        derived by hand from `accumulate_flux_to_cells`'s own `+owner
        area/-neighbour area, /volume` reduction and confirmed by the
        matrix-comparison tests below. **A periodic face (`mesh.
        boundary_face_name(face) in self._periodic_pairs`) is one-sided,
        not symmetric**: `accumulate_flux_to_cells`'s own geometry has no
        knowledge of `periodic_pairs` at all, so a periodic face
        contributes only to its owner's row (`d = 2 *
        mesh.face_centroid_distance(face)`, `wrapped =
        mesh.wrapped_neighbour_cell(face)`, `[o,o] += c`, `[o,wrapped] -=
        c`) -- the paired face on the opposite domain edge supplies the
        missing half independently. Getting this wrong was a real risk
        while designing this change: a first hand derivation assumed the
        full symmetric stencil applied to periodic faces too, and was
        only caught wrong by testing a mesh where the periodic
        connection does *not* coincide with an existing interior one
        (`test_poisson_matrix_matches_independent_reference_construction`'s
        own parametrised cases cover both). A genuine boundary face
        (neither branch above) is zero-gradient by construction and
        contributes nothing -- skipped, no `BoundaryCondition.evaluate`
        call at all.

        `coalesce()` is still required, and now does real work it
        previously did not: a periodic pair that coincides with an
        existing interior connection (e.g. a mesh only two cells tall,
        wrapping north/south onto the same pair of rows an interior face
        already connects) produces two contributions at the same `(row,
        col)` that must be summed, unlike the old probe loop's own
        comment claiming no duplicates ever arise (true there, since each
        probed column touched each row at most once; not true here, where
        two different faces can touch the same cell pair).

        Cached by mesh *identity*, not equality, the same "the common
        case is a cache hit" reasoning as before: a real run always hands
        `correct` the same mesh object every timestep; a genuinely
        different mesh object (unusual -- no code path in this repository
        reuses one `PISO` instance across meshes today) safely recomputes.
        """
        if self._cached_poisson_mesh is mesh and self._cached_poisson_matrix is not None:
            return self._cached_poisson_matrix

        self._assert_zero_gradient_pressure_boundary(mesh)
        volume = self._assert_uniform_cell_volume(mesh)
        gamma = 1.0  # matches self._diffusion's own fixed diffusion_coefficient

        rows: list[int] = []
        cols: list[int] = []
        values: list[float] = []
        for face in range(mesh.num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            area = mesh.face_area(face)
            if neighbour is not None:
                distance = mesh.face_centroid_distance(face)
                coefficient = gamma * area / (distance * volume)
                rows += [owner, neighbour, owner, neighbour]
                cols += [owner, neighbour, neighbour, owner]
                values += [coefficient, coefficient, -coefficient, -coefficient]
                continue
            boundary_name = mesh.boundary_face_name(face)
            assert boundary_name is not None
            if boundary_name in self._periodic_pairs:
                wrapped = mesh.wrapped_neighbour_cell(face)
                distance = 2 * mesh.face_centroid_distance(face)
                coefficient = gamma * area / (distance * volume)
                rows += [owner, owner]
                cols += [owner, wrapped]
                values += [coefficient, -coefficient]
            # else: a genuine boundary face is zero-gradient (asserted
            # above) and contributes nothing.

        num_cells = mesh.num_cells
        indices = torch.tensor([rows, cols], dtype=torch.long)
        matrix = (
            torch.sparse_coo_tensor(
                indices, torch.tensor(values, dtype=torch.float64), (num_cells, num_cells)
            )
            .coalesce()
            .to_sparse_csr()
        )
        self._cached_poisson_mesh = mesh
        self._cached_poisson_matrix = matrix
        return matrix

    def _assert_uniform_cell_volume(self, mesh: StructuredCartesianMesh) -> float:
        """The one shared cell volume every cell in `mesh` reports --
        `_poisson_matrix`'s direct construction depends on every cell
        sharing one volume for its stencil to be symmetric (`adr/ADR-012
        -direct-poisson-matrix-construction.md`). Every
        `StructuredCartesianMesh` today guarantees this structurally (one
        mesh-wide `dx`/`dy`), so this is unreachable with the current
        `Mesh` hierarchy -- checked anyway so a future mesh variant that
        breaks it fails loudly here, not with a silently wrong matrix.
        `O(num_cells)`, negligible next to the old `O(num_cells *
        num_faces)` build this replaces.
        """
        volumes = {mesh.cell_volume(cell) for cell in range(mesh.num_cells)}
        if len(volumes) != 1:
            raise NonUniformCellVolumeError(
                f"PISO's direct Poisson-matrix construction requires every cell to share "
                f"one volume; found {len(volumes)} distinct values: {sorted(volumes)}"
            )
        return next(iter(volumes))

    def _assert_zero_gradient_pressure_boundary(self, mesh: StructuredCartesianMesh) -> None:
        """Raise unless every one of this instance's own pressure
        boundary conditions is genuinely zero-gradient -- `_poisson_
        matrix`'s direct construction skips every non-periodic boundary
        face outright rather than consulting a `BoundaryCondition`, which
        is only correct because `PISO.__init__` always builds
        `_ZeroGradientPressureCondition` for all four named edges today.
        Unreachable through the public constructor (there is no argument
        that changes `self._pressure_boundary_conditions`), checked
        anyway so a future change that makes pressure's own boundary
        treatment configurable fails loudly here rather than silently
        skipping a boundary contribution that should exist. At most 4
        `evaluate` calls, against any one real boundary face of `mesh` --
        cheap, and run only on a cache miss.
        """
        probe_face = next(face for face in range(mesh.num_faces) if mesh.is_boundary_face(face))
        probe_field = ScalarField(mesh, "_poisson_boundary_probe", initial_value=0.0)
        for name in _PRESSURE_BOUNDARY_FACE_NAMES:
            condition = self._pressure_boundary_conditions[name]
            if condition.kind != "gradient" or condition.evaluate(probe_field, probe_face) != 0.0:
                raise UnsupportedPressureBoundaryConditionError(
                    f"PISO's direct Poisson-matrix construction requires every pressure "
                    f"boundary condition to be zero-gradient; {name!r} is not"
                )

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

        **Per-face loop split and vectorised, the last of this session's
        six-fix arc (`simulation.py`'s own `accumulate_flux_to_cells`
        entry, `src/pyflow/engine/CLAUDE.md`, names all six).** Unlike
        the five before it, this one needed no scalar loop at all, not
        even a small one: every genuine (non-periodic) boundary face's
        correction is exactly zero by construction (the docstring above,
        unchanged) -- no `BoundaryCondition` is ever consulted here, so
        there is no open interface to stay clear of the way diffusion's/
        gradient's own boundary formulas do. A per-instance geometry
        cache (`_rhie_chow_geometry`, mirroring `_poisson_matrix`'s own
        "cached by mesh identity" pattern, a second and distinct cache on
        this same instance) resolves interior/periodic faces; a
        `resolved` mask zeroes the placeholder-derived value at every
        genuine boundary face directly, since nothing needs to overwrite
        it afterward.
        """
        mesh = velocity.mesh
        assert isinstance(mesh, StructuredCartesianMesh)
        naive = self._divergence.divergence(velocity)
        geometry = self._rhie_chow_geometry(mesh)

        pressure_values = pressure.values
        p_owner = pressure_values[geometry.owner_ids]
        p_neighbour = pressure_values[geometry.neighbour_ids]
        direct = (p_neighbour - p_owner) / geometry.distances

        g_owner = pressure_gradient[geometry.owner_ids]
        g_neighbour = pressure_gradient[geometry.neighbour_ids]
        g_avg = (g_owner + g_neighbour) / 2
        avg_normal = g_avg[:, 0] * geometry.normal_x + g_avg[:, 1] * geometry.normal_y

        correction_face = torch.where(
            geometry.resolved,
            dt * (direct - avg_normal),
            torch.zeros(mesh.num_faces, dtype=torch.float64),
        )
        return naive - accumulate_flux_to_cells(mesh, correction_face)

    def _rhie_chow_geometry(self, mesh: StructuredCartesianMesh) -> _RhieChowGeometry:
        """Built once per distinct `mesh` and cached for the rest of this
        `PISO` instance's own lifetime -- `_poisson_matrix`'s own
        "cached by mesh identity, not equality" pattern, a second and
        distinct cache on the same instance (this one never invalidates
        the other, and vice versa).
        """
        if (
            self._cached_rhie_chow_geometry_mesh is mesh
            and self._cached_rhie_chow_geometry is not None
        ):
            return self._cached_rhie_chow_geometry

        num_faces = mesh.num_faces
        owner_ids = torch.zeros(num_faces, dtype=torch.long)
        neighbour_ids = torch.zeros(num_faces, dtype=torch.long)
        normal_x = torch.zeros(num_faces, dtype=torch.float64)
        normal_y = torch.zeros(num_faces, dtype=torch.float64)
        distances = torch.zeros(num_faces, dtype=torch.float64)
        resolved = torch.zeros(num_faces, dtype=torch.bool)
        for face in range(num_faces):
            owner, neighbour = mesh.face_neighbours(face)
            distance = mesh.face_centroid_distance(face)
            if neighbour is None:
                boundary_name = mesh.boundary_face_name(face)
                if boundary_name in self._periodic_pairs:
                    neighbour = mesh.wrapped_neighbour_cell(face)
                    distance = 2 * distance
            nx, ny = mesh.face_normal(face)
            owner_ids[face] = owner
            normal_x[face] = nx
            normal_y[face] = ny
            distances[face] = distance
            if neighbour is not None:
                neighbour_ids[face] = neighbour
                resolved[face] = True
            else:
                neighbour_ids[face] = owner  # placeholder, masked out by `resolved`

        geometry = _RhieChowGeometry(
            owner_ids=owner_ids,
            neighbour_ids=neighbour_ids,
            normal_x=normal_x,
            normal_y=normal_y,
            distances=distances,
            resolved=resolved,
        )
        self._cached_rhie_chow_geometry_mesh = mesh
        self._cached_rhie_chow_geometry = geometry
        return geometry


@dataclass(frozen=True)
class _RhieChowGeometry:
    """`PISO._rhie_chow_geometry`'s own per-mesh cache -- see that
    method's own docstring for why no scalar boundary loop is needed
    here (unlike every other numerics scheme this session vectorised).
    """

    owner_ids: torch.Tensor
    neighbour_ids: torch.Tensor
    normal_x: torch.Tensor
    normal_y: torch.Tensor
    distances: torch.Tensor
    resolved: torch.Tensor


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


class NonUniformCellVolumeError(ValueError):
    """Raised by `PISO._poisson_matrix`'s direct per-face construction
    (`adr/ADR-012-direct-poisson-matrix-construction.md`) if a mesh's
    cells do not all report the same `cell_volume` -- see
    `PISO._assert_uniform_cell_volume`'s own docstring for why.
    """


class UnsupportedPressureBoundaryConditionError(ValueError):
    """Raised by `PISO._poisson_matrix`'s direct per-face construction
    (`adr/ADR-012-direct-poisson-matrix-construction.md`) if any of
    PISO's own internally-built pressure boundary conditions is not
    zero-gradient -- see `PISO._assert_zero_gradient_pressure_boundary`'s
    own docstring for why.
    """
