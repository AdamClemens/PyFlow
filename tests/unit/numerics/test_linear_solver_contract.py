"""Contract test suite for `LinearSolver` (TASK-022) -- the interface
that solves the linear system pressure-velocity coupling (and any other
implicit step) produces, independent of where the system came from
(`docs/architecture/engine.md`'s Linear Solver contract: "given a linear
system, produces its solution, independent of the system's origin").

Two test-only implementations, per Stage 3 Completion Criterion 2: one
exact (`_ExactSolver`, `torch.linalg.solve`), one iterative-shaped
(`_JacobiSolver`) that can be made to fail to converge on demand -- the
second exists specifically so the non-convergence criteria are
checkable at all, since an exact direct solve can't fail to converge.
Plus, since TASK-026 (2026-08-27), a real third fixture:
`ConjugateGradientSolver` joins these two, unlike TASK-025's own join --
`LinearSolver.solve`'s signature is untouched, so this is a real "add a
factory, edit nothing existing" join, the same shape TASK-023/024's own
joins used. `ConjugateGradientSolver`'s own physical-correctness claims
(the positive-semi-definite/null-space case) are
`tests/features/conjugate_gradient_solver.feature`, bound by
`tests/unit/test_conjugate_gradient_solver.py`.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable

import pytest
import torch

from pyflow.engine.numerics.linear_solver import (
    ConjugateGradientSolver,
    LinearSolver,
    LinearSolverResult,
)


class _ExactSolver(LinearSolver):
    """Direct solve: always converges, in one step by definition."""

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        solution = torch.linalg.solve(matrix, rhs)
        return LinearSolverResult(solution=solution, converged=True, iterations=1)


class _JacobiSolver(LinearSolver):
    """Iterative-shaped: plain Jacobi iteration from a zero initial
    guess. Not a scheme this project will ship -- exists only to be
    structurally different from `_ExactSolver` (iterative vs. direct)
    and tunable, via `tolerance`/`max_iterations`, to fail to converge
    on demand.
    """

    def __init__(self, tolerance: float, max_iterations: int) -> None:
        self._tolerance = tolerance
        self._max_iterations = max_iterations

    def solve(self, matrix: torch.Tensor, rhs: torch.Tensor) -> LinearSolverResult:
        x = torch.zeros_like(rhs)
        diagonal = torch.diagonal(matrix)
        for iteration in range(self._max_iterations):
            residual = rhs - matrix @ x
            if torch.linalg.vector_norm(residual) < self._tolerance:
                return LinearSolverResult(solution=x, converged=True, iterations=iteration)
            x = x + residual / diagonal
        residual = rhs - matrix @ x
        converged = bool(torch.linalg.vector_norm(residual) < self._tolerance)
        return LinearSolverResult(solution=x, converged=converged, iterations=self._max_iterations)


def _system_2x2() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    # Diagonally dominant (Jacobi converges), a non-"nice" known solution.
    matrix = torch.tensor([[4.0, 1.0], [1.0, 3.0]], dtype=torch.float64)
    x_true = torch.tensor([1.5, -2.25], dtype=torch.float64)
    rhs = matrix @ x_true
    return matrix, rhs, x_true


def _system_3x3() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    matrix = torch.tensor([[5.0, 1.0, 0.5], [1.0, 4.0, 0.5], [0.5, 0.5, 3.0]], dtype=torch.float64)
    x_true = torch.tensor([2.25, -1.5, 0.75], dtype=torch.float64)
    rhs = matrix @ x_true
    return matrix, rhs, x_true


_FACTORIES: list[tuple[str, Callable[[], LinearSolver]]] = [
    ("exact", _ExactSolver),
    ("jacobi", lambda: _JacobiSolver(tolerance=1e-10, max_iterations=200)),
    (
        "conjugate_gradient",
        lambda: ConjugateGradientSolver(tolerance=1e-10, max_iterations=200),
    ),
]


@pytest.fixture(params=_FACTORIES, ids=lambda factory: factory[0])
def make_solver(request: pytest.FixtureRequest) -> LinearSolver:
    factory: Callable[[], LinearSolver] = request.param[1]
    return factory()


def test_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        LinearSolver()  # type: ignore[abstract]


def test_subclass_missing_solve_cannot_be_instantiated() -> None:
    class _Incomplete(LinearSolver):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_solve_is_the_only_abstract_method() -> None:
    assert LinearSolver.__abstractmethods__ == frozenset({"solve"})


def test_solve_signature_takes_matrix_and_rhs() -> None:
    params = list(inspect.signature(LinearSolver.solve).parameters)
    assert params == ["self", "matrix", "rhs"]


@pytest.mark.parametrize("system", [_system_2x2(), _system_3x3()], ids=["2x2", "3x3"])
def test_solve_returns_the_known_solution_within_tolerance(
    make_solver: LinearSolver, system: tuple[torch.Tensor, torch.Tensor, torch.Tensor]
) -> None:
    matrix, rhs, x_true = system

    result = make_solver.solve(matrix, rhs)

    assert result.converged
    assert torch.allclose(result.solution, x_true, atol=1e-6)


def test_a_zero_right_hand_side_solves_to_the_zero_vector_immediately(
    make_solver: LinearSolver,
) -> None:
    matrix, _, _ = _system_2x2()
    rhs = torch.zeros(2, dtype=torch.float64)

    result = make_solver.solve(matrix, rhs)

    assert result.converged
    assert torch.allclose(result.solution, torch.zeros(2, dtype=torch.float64), atol=1e-9)


def test_jacobi_reports_non_convergence_when_the_iteration_limit_is_too_low() -> None:
    matrix, rhs, _ = _system_2x2()
    solver = _JacobiSolver(tolerance=1e-12, max_iterations=1)

    result = solver.solve(matrix, rhs)

    assert result.converged is False
    assert result.iterations == 1


def test_exact_solver_always_converges() -> None:
    matrix, rhs, _ = _system_3x3()

    result = _ExactSolver().solve(matrix, rhs)

    assert result.converged is True
    assert result.iterations == 1
