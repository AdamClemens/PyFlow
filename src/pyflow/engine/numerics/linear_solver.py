"""LinearSolver (TASK-022): the interface that solves the linear system
pressure-velocity coupling (and any other implicit step) produces,
independent of where the system came from
(`docs/architecture/engine.md`'s Linear Solver contract: "given a linear
system, produces its solution, independent of the system's origin").

Knows nothing about pressure -- a solver that knew it was solving a
pressure-correction equation could not be reused for the implicit steps
its own upgrade path anticipates (`docs/planning/roadmap.md` TASK-022's
design decisions). Takes a plain dense `matrix`/`rhs` pair, not a
dedicated "system" type -- this task's own Artifacts Produced names only
one new type, the result, so the system stays exactly the two tensors
the contract needs and nothing else.

Convergence is reported, not assumed: a solver that silently returns its
last iterate when it fails to converge produces a plausible wrong
answer, the failure mode this repository has recorded three times
already (`Mesh` accessors, mesh config truncation, pan scale) --
`LinearSolverResult` carries a `converged` flag the caller is required to
be able to check.

No concrete solver lived here through Stage 3 -- Stage 3 Completion
Criterion 1. `ConjugateGradientSolver` (TASK-026, Stage 4) is the first,
and it is what actually carries the null-space handling `icds.md`
requires for the lid-driven cavity's positive-semi-definite pressure
system -- see its own docstring for the reasoning, verified numerically
before being written (`docs/planning/roadmap.md` TASK-026's own Context).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class LinearSolverResult:
    """The outcome of one `LinearSolver.solve` call.

    `converged`/`iterations` sit alongside `solution` on the same
    object, not in a log line, precisely so a caller that checks the
    flag can tell a real answer from an unconverged iterate, and a
    caller that doesn't still gets a value -- the design decision
    `docs/planning/roadmap.md` TASK-022 states directly.
    """

    solution: torch.Tensor
    converged: bool
    iterations: int


class LinearSolver(ABC):
    """Solves a dense linear system `matrix @ x = rhs` for `x`."""

    @abstractmethod
    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        """Return the solution to `matrix @ x = rhs`, plus whether it
        converged and in how many iterations.

        `matrix` is `(n, n)`, `rhs` is `(n,)`.
        """


_NULL_SPACE_DETECTION_TOLERANCE = 1e-9
_DEGENERATE_DIRECTION_TOLERANCE = 1e-300


class ConjugateGradientSolver(LinearSolver):
    """Standard Conjugate Gradient for a symmetric positive-definite
    `matrix`, starting from `x0 = 0`.

    **Null-space handling is gated, not unconditional
    (`docs/handbook/numerical-methods/linear-solvers.md`'s "CG"
    section).** When every boundary prescribes velocity and none
    prescribes pressure (the lid-driven cavity), PISO's own
    pressure-correction matrix is only positive *semi*-definite -- the
    constant vector lies in its null space, since pressure is fixed only
    up to an additive constant. Detected once per `solve` call, cheaply:
    `matrix @ ones` close to zero, relative to `matrix`'s own norm. When
    true, the constant mode is projected out of the residual after every
    update (the initial residual included) -- a defensive correction
    against floating-point drift, not what makes convergence possible in
    the first place: starting from `x0 = 0` with a consistent (zero-mean)
    `rhs` already keeps every CG iterate in `range(matrix)` in exact
    arithmetic (`range` is `matrix`-invariant and contains `r0`), so the
    projection only stops roundoff from slowly injecting a spurious
    null-space component over many iterations.

    **Applying this projection unconditionally would silently solve a
    different problem.** Verified directly, not assumed: on a generic
    well-conditioned SPD system, unconditional projection reports
    `converged=True` after one iteration with a confidently wrong answer,
    not a crash or a non-convergence flag -- exactly the
    "plausible-looking wrong answer" failure mode `docs/practices.md`
    names repeatedly. The gate is what keeps this solver correct for both
    the contract suite's own generic systems (gate false, plain textbook
    CG) and the real PISO-shaped one (gate true).

    A degenerate-direction guard (`abs(p @ (matrix @ p))` below a tiny
    epsilon stops the loop rather than dividing by ~0) is ordinary
    defensive practice, harmless for any well-conditioned system.

    No rejection path of its own -- the same reasoning every other
    concrete `TimeIntegrator`/`LinearSolver` test double in this
    repository already establishes: symmetry is a mathematical
    precondition this interface has never asked an implementation to
    validate.
    """

    def __init__(self, tolerance: float, max_iterations: int) -> None:
        self._tolerance = tolerance
        self._max_iterations = max_iterations

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        matrix_norm = torch.linalg.matrix_norm(matrix)
        row_sums = matrix @ torch.ones(matrix.shape[0], dtype=matrix.dtype)
        has_null_space = bool(
            torch.linalg.vector_norm(row_sums) < _NULL_SPACE_DETECTION_TOLERANCE * matrix_norm
        )

        def _project(vector: torch.Tensor) -> torch.Tensor:
            return vector - vector.mean() if has_null_space else vector

        x = torch.zeros_like(rhs)
        residual = _project(rhs - matrix @ x)
        residual_dot = residual @ residual
        if torch.sqrt(residual_dot) < self._tolerance:
            return LinearSolverResult(solution=x, converged=True, iterations=0)
        direction = residual.clone()

        for iteration in range(1, self._max_iterations + 1):
            direction_curvature = direction @ (matrix @ direction)
            if abs(float(direction_curvature)) < _DEGENERATE_DIRECTION_TOLERANCE:
                # A nonzero `direction` this repository's own fixtures can
                # construct always has strictly positive curvature here:
                # either `matrix` is genuinely full-rank (no null space to
                # begin with), or `has_null_space` is true and `_project`
                # has kept every `residual`/`direction` in `range(matrix)`,
                # where the restricted operator is positive *definite*.
                # Defensive protection against a floating-point pathology
                # this repository cannot realistically construct a test
                # for, not a path expected to run.
                break  # pragma: no cover
            step_size = residual_dot / direction_curvature
            x = x + step_size * direction
            residual = _project(residual - step_size * (matrix @ direction))
            new_residual_dot = residual @ residual
            if torch.sqrt(new_residual_dot) < self._tolerance:
                return LinearSolverResult(solution=x, converged=True, iterations=iteration)
            direction = residual + (new_residual_dot / residual_dot) * direction
            residual_dot = new_residual_dot

        converged = bool(torch.sqrt(residual_dot) < self._tolerance)
        return LinearSolverResult(solution=x, converged=converged, iterations=self._max_iterations)
