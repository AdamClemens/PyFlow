# The acceptance criteria for the Lid-Driven Cavity golden demo
# (TASK-034, Stage 5 Completion Criterion 8 -- the MVP's own golden
# demo). `tests/golden/test_lid_driven_cavity.py` binds these scenarios.
# The quantitative comparison against Ghia, Ghia & Shin (1982) is
# `tests/features/navier_stokes_timestep.feature`'s own scenario, run
# directly against the engine, not repeated here -- this file is the
# reproducible, visible demonstration the public-API rule requires.

Feature: Lid-Driven Cavity
  A square cavity, no-slip on every wall, the top wall moving
  tangentially at a constant speed -- rendered live as a real,
  incompressible `navier_stokes_step` solves it, one timestep per frame.
  The first velocity field PyFlow has ever rendered that was *solved*,
  not prescribed or seeded (`docs/implementation/mvp.md`'s own
  "visualisation shows the result").

  Background:
    Given the golden demo "lid_driven_cavity"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: The rendered velocity field is genuinely solved, not the zero it started from
    When it is bootstrapped for a few real timesteps
    Then the velocity field has real nonzero motion away from the lid

  Scenario: The same configuration run twice produces identical state
    When it is bootstrapped for a few real timesteps twice
    Then both runs produce identical velocity fields
