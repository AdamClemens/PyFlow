# The acceptance criteria for RK4 Time Integration (TASK-025, Stage 4's
# fourth task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_rk4_time_integration.py` binds these scenarios directly, per that
# directory's own scope (isolated logic, no process boundary).

Feature: RK4 Time Integration
  Stage 4 Completion Criterion 4's own claim for this task: fourth-order
  accuracy in time for the ODE system the integrator is handed
  (`docs/handbook/numerical-methods/time-integration.md`), with spatial
  error isolated out via a manufactured derivative -- no real mesh or
  spatial scheme involved -- so it cannot dominate the measured order.
  Separately, and just as necessary: RK4 is a *four-stage* method, and a
  scheme that quietly degenerated to fewer evaluations (or reused one
  stale state four times) could still look accurate on an easy problem by
  coincidence, so genuine multi-stage evaluation is checked directly
  rather than only inferred from the accuracy result.

  Scenario: The derivative is evaluated four times per step, at four genuinely different states
    Given a manufactured derivative function that records every state it is called with
    When the state is advanced by one RK4 step
    Then the derivative was evaluated exactly four times
    And every recorded state is genuinely different from every other recorded state

  Scenario: The scheme is fourth-order accurate under timestep refinement
    Given a manufactured exponential-decay derivative with a known exact solution, at decreasing timestep sizes
    When the state is advanced to a fixed final time at each timestep size
    Then the observed convergence order is close to four
