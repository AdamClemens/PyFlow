# The acceptance criteria for Fluid Configuration Section (TASK-041,
# Stage 5's first task). Not a golden demo of its own -- no new config
# file under `examples/golden-demos/`, reusing the existing Passive
# Scalar Transport demo for the migration scenario instead -- but its
# own claims are genuinely user-observable (loading a configuration
# file), so `tests/integration/test_fluid_configuration.py` binds these
# scenarios, crossing the real CLI subprocess boundary the last scenario
# needs (`tests/CLAUDE.md`'s own split between `unit/` and
# `integration/`), rather than living in `tests/unit/`.
#
# `numerics.diffusion_coefficient` moves into a new `fluid:` section
# alongside a new `fluid.viscosity`. The criterion that matters is that
# the break is complete and visible, not partial and silent
# (`docs/planning/roadmap.md` TASK-041's own Intent): a config still
# setting the old field must fail loudly, never run with a silently
# substituted default. Per-field type/range rejection (a non-numeric or
# non-positive value) is not repeated here -- it stays in
# `tests/unit/test_configuration.py`, where every other field's own
# rejection tests already live; these scenarios carry the migration's
# own claims only.

Feature: Fluid Configuration Section

  Scenario: A fluid configuration section loads both of its fields
    Given a configuration file setting fluid.viscosity and fluid.diffusion_coefficient
    When the configuration is loaded
    Then both values arrive on the loaded configuration's fluid section

  Scenario: Setting one fluid field leaves the other at its own default
    Given a configuration file setting only fluid.viscosity
    When the configuration is loaded
    Then fluid.diffusion_coefficient is still its own default value

  Scenario: A configuration still setting the retired numerics field is rejected, not silently defaulted
    Given a configuration file setting numerics.diffusion_coefficient
    When the configuration is loaded
    Then loading is rejected with a named error saying the field moved to fluid.diffusion_coefficient

  Scenario: The Passive Scalar Transport golden demo still runs through the real CLI after the migration
    Given the Passive Scalar Transport golden demo's own committed configuration file
    When the demo is run through the real CLI as a subprocess
    Then the process exits successfully
