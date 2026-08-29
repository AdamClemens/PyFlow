# The acceptance criteria for Pressure Field (TASK-032, Stage 5's third
# task in build order). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI subprocess run, since every claim here
# is checked against the engine mechanism directly, the same
# `tests/unit/` shape every prior numerical-scheme feature file in this
# stage established. `tests/unit/test_pressure_field.py` binds these
# scenarios.
#
# Pressure is *not* transported -- it is solved for, from the
# incompressibility constraint. A criterion that treats it as another
# advected scalar has misunderstood the task
# (`docs/handbook/numerical-methods/pressure-velocity-coupling.md`).
# `PISO` (TASK-027, Stage 4) already performs the solve this task's own
# criteria describe -- these scenarios prove the properties Stage 4's
# own criteria never had cause to check (constant pressure for a
# divergence-free input, the null-space remedy actually holding), not a
# new pressure-solving mechanism.

Feature: Pressure Field

  Background:
    Given a small, non-square, non-trivially-origined mesh

  Scenario: A divergence-free provisional velocity field yields a pressure field constant to solver tolerance
    Given a uniform provisional velocity field with zero-gradient boundaries on every wall
    When the field is corrected by one PISO pass
    Then the solved pressure field is constant to solver tolerance

  Scenario: A provisional velocity field with known nonzero divergence yields a pressure field that is not constant
    Given a provisional velocity field with real interior divergence, not aligned with either mesh axis
    When the field is corrected by one PISO pass
    Then the solved pressure field is not constant

  Scenario: Adding a constant to the pressure field leaves the corrected velocity unchanged
    Given a provisional velocity field with real interior divergence, not aligned with either mesh axis
    When the field is corrected by one PISO pass
    And a nonzero constant is added to the solved pressure field everywhere
    Then the velocity correction computed from the shifted pressure field matches the original exactly

  Scenario: A fields mapping containing a pressure field is rejected by step, not silently transported
    Given a pressure field produced by a real PISO correction
    When the simulation is stepped with that pressure field included among the transported fields
    Then a named error says pressure is not transported

  Scenario: A boundary configuration whose prescribed velocities violate the zero-net-flux compatibility condition fails to load
    Given a configuration prescribing a nonzero net velocity flux across all four boundaries
    When the configuration is loaded
    Then loading is rejected before any pressure solve could be attempted
