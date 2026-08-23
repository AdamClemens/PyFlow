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

No concrete strategy lives here -- Stage 3 Completion Criterion 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pyflow.engine.numerics.linear_solver import LinearSolver
from pyflow.engine.scalar_field import ScalarField
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
    def correct(self, provisional_velocity: VectorField) -> tuple[VectorField, ScalarField]:
        """Return `(corrected_velocity, pressure)` for `provisional_velocity`.

        Must not mutate `provisional_velocity`.
        """
