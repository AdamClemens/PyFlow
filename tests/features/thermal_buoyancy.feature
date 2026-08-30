# The acceptance criteria for the Thermal Buoyancy golden demo
# (TASK-035, Stage 6, `docs/planning/implementation-plan.md` Level 3's
# own Golden Demo list). `tests/golden/test_thermal_buoyancy.py` binds
# these scenarios.
#
# Added while implementing TASK-035, alongside `heat_transport.feature`
# -- see that file's own header comment for why two feature files exist
# where the roadmap's own Artifacts Produced bullet named one.
#
# The first golden demo combining a declared field with solved,
# pressure-corrected velocity in one configuration -- `bootstrap.py`'s
# `_add_declared_field_transport` already supported this combination
# generically (built for TASK-042, not anticipating buoyancy), so this
# demo needed no new bootstrap.py control flow, only the two new
# configuration fields (`fluid.gravity`, the field's own buoyancy
# coupling) this task adds.

Feature: Thermal Buoyancy
  A warm patch in an otherwise still, uniform-temperature domain rises
  under a Boussinesq body force -- `tests/features/temperature_field.
  feature`'s own "warm fluid rises" claim, demonstrated as a
  reproducible, visible golden demo rather than re-validated here.

  Background:
    Given the golden demo "thermal_buoyancy"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: The warm patch develops upward vertical velocity
    When it is bootstrapped for several real timesteps
    Then the vertical velocity at the temperature field's own warmest cell is positive
