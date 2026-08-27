# The acceptance criteria for the Conjugate Gradient Solver (TASK-026,
# Stage 4's fifth task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_conjugate_gradient_solver.py` binds these scenarios directly, per
# that directory's own scope (isolated logic, no process boundary).

Feature: Conjugate Gradient Solver
  Stage 4 Completion Criterion 4's own claim for this task: converges on
  a system with the same character as the one PISO actually produces for
  the lid-driven cavity's boundary configuration -- positive
  *semi*-definite, pressure fixed only up to an additive constant, with
  the null space removed -- not only on a made-up well-conditioned system
  (`docs/handbook/numerical-methods/linear-solvers.md`). Separately, and
  just as necessary: non-convergence must remain distinguishable from a
  converged answer.

  Scenario: The solver converges on a positive semi-definite system built from the real diffusion operator
    Given a positive semi-definite system built from CentralDifferenceDiffusion on an all-zero-gradient-boundary mesh
    And a right-hand side satisfying the zero-mean compatibility condition
    When the system is solved
    Then the solver reports convergence
    And the residual of the reported solution is close to zero
    And the reported solution stays bounded

  Scenario: Non-convergence is reported, not returned as a plausible answer
    Given a well-conditioned system with a known solution
    And an iteration limit too low to reach the configured tolerance
    When the system is solved
    Then the solver reports non-convergence
    And the iteration count equals the configured limit
