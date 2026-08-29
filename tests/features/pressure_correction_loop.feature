# The acceptance criteria for Pressure Correction Loop (TASK-033, Stage
# 5's fourth task in build order). Not a golden demo -- no config file
# under `examples/golden-demos/`, no CLI subprocess run, since every
# claim here is checked against the engine mechanism directly, the same
# `tests/unit/` shape every prior numerical-scheme feature file in this
# stage established. `tests/unit/test_pressure_correction_loop.py` binds
# these scenarios.
#
# The claim is that divergence decreases monotonically with each
# corrector iteration and reaches the configured tolerance -- measured
# across iterations, not asserted at the end. `PISO` (`engine/numerics/
# pressure_coupling.py`) is the strategy this task makes genuinely
# multi-pass; see its own docstring for design question three's answer
# (found by numerical prototyping, not reasoned about in advance) and
# why `PressureCoupling.correct`'s own signature needed no change.
#
# Couette flow's exact linear profile (Stage 5 Completion Criterion 5)
# is deliberately not a scenario here -- it is discharged jointly with
# TASK-034, the first task with a fully assembled timestep to run it
# against; this task lays the corrector-loop groundwork it needs, not
# the demonstration itself.

Feature: Pressure Correction Loop

  Background:
    Given a small, non-square, non-trivially-origined mesh
    And a provisional velocity field with real interior divergence, not aligned with either mesh axis

  Scenario: A corrector loop against a real divergent field converges, with a non-increasing recorded divergence sequence
    Given a real linear solver
    When the field is corrected by PISO's own corrector loop
    Then the recorded divergence sequence is non-increasing at every element
    And its last element is at or below the configured tolerance

  Scenario: A corrector loop that only partially corrects divergence each pass still takes multiple genuine passes to converge
    Given a linear solver that only ever removes half of the remaining divergence per pass
    When the field is corrected by PISO's own corrector loop
    Then the recorded divergence sequence has more than two elements
    And each element is smaller than the one before it
    And its last element is at or below the configured tolerance

  Scenario: Exhausting the corrector iteration limit without reaching tolerance raises rather than returning a best-effort result
    Given a linear solver that reports success but never actually reduces divergence
    And a corrector iteration limit of 3
    When the field is corrected by PISO's own corrector loop
    Then a divergence-did-not-converge error is raised
    And the recorded divergence sequence has exactly 4 elements
