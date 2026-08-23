# The acceptance criteria for the Numerics Assembly golden demo, in the
# form that executes. `docs/implementation/golden-demos.md` describes
# what this demo is and why; the scenarios below are what "working"
# means, and they are the only statement of it -- see
# `adr/ADR-007-executable-acceptance-criteria.md`.

Feature: Numerics Assembly
  Stage 3's golden demo (TASK-021, roadmap Completion Criterion 8):
  "Engine initialises entirely through interfaces. No CFD yet." Proves
  that all six `adr/ADR-003-modular-numerical-strategies.md` components
  resolve from configuration to real (if physically trivial) instances,
  end to end through the real CLI -- not any numerical correctness,
  since nothing here computes physics yet.

  Background:
    Given the golden demo "numerics_assembly"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: The assembled set matches what was configured
    When it is bootstrapped directly
    Then the reported assembled set matches the configured numerics section

  Scenario: Assembling the same configuration twice reports the same set
    When it is bootstrapped twice
    Then both runs report an identical assembled set

  Scenario: Adding a numerics section does not change Field Display's rendered output
    Given the "field_display" demo's own configuration
    When a numerics section naming a non-default timestep is added to it
    And both variants are rendered offscreen
    Then the two frames are pixel-identical
