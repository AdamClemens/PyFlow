# The acceptance criteria for PISO Pressure Coupling (TASK-027, Stage
# 4's sixth task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_piso_pressure_coupling.py` binds these scenarios directly, per
# that directory's own scope (isolated logic, no process boundary).
#
# Stage 4 Completion Criterion 4's own claim for this task, corrected
# 2026-08-27 before implementation started (`docs/planning/roadmap.md`,
# Stage 4 Completion Criteria, Pressure-Velocity Coupling bullet; see
# `docs/practices.md`, "A criterion whose strong reading depends on a
# later task must say so when drafted"): a single correction pass
# measurably and boundedly reduces the divergence of a manufactured
# provisional velocity field, checked in isolation against a stated
# tolerance -- not "the pressure loop runs" and not "the flow looks
# incompressible". The stronger claim (divergence reaching a configured
# tolerance via monotonic multi-pass correction) is Stage 5 TASK-033's
# own claim, not this task's -- PyFlow's collocated mesh needs
# Rhie-Chow interpolation and a real momentum equation to suppress
# pressure-velocity decoupling under repeated correction, neither of
# which this task's own interface has.

Feature: PISO Pressure Coupling
  Scenario: A single correction pass measurably and boundedly reduces the divergence of a manufactured provisional velocity field
    Given a closed-box mesh with zero normal velocity prescribed on every boundary
    And a provisional velocity field with real interior divergence, not aligned with either mesh axis
    When the field is corrected by one PISO pass
    Then every cell's corrected divergence magnitude is less than 70% of the provisional field's own maximum divergence magnitude
    And the corrected field's own maximum divergence magnitude is smaller than the provisional field's

  Scenario: Non-convergence in the pressure solve is reported, not returned as a plausible answer
    Given a closed-box mesh with zero normal velocity prescribed on every boundary
    And a provisional velocity field with real interior divergence, not aligned with either mesh axis
    And a linear solver that never reports convergence
    When the field is corrected by one PISO pass
    Then a pressure solve non-convergence error is raised
