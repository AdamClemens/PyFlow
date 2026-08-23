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

No concrete solver lives here -- Stage 3 Completion Criterion 1. The
null-space handling `icds.md` requires for the lid-driven cavity's
positive-semi-definite pressure system belongs to the concrete
implementation (TASK-026), not this interface -- recorded here only so
it isn't lost in between.
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
