# The acceptance criteria for Field Declaration Configuration (TASK-042,
# Stage 6's first task, built before any phenomenon exists). This task
# contains no physics -- it gives a configuration file a way to declare
# the transported fields a run carries, so that every task after it in
# this stage is a configuration entry and a feature file, not a code
# change (`docs/planning/roadmap.md` TASK-042's own Purpose).
#
# Bound from `tests/unit/`, per that directory's own scope
# (`tests/features/CLAUDE.md`): every scenario here is a configuration
# loading or failing to load, plus one real end-to-end run and one real
# render check -- neither of the latter two needs a rendered frame
# (`RenderWindow.last_image`), only `bootstrap()`'s own scene graph and
# field state, offscreen.
#
# Every rejection scenario below calls `load_config` directly and never
# reaches `bootstrap()` at all -- which is itself Criterion 7's "at
# configuration load, not a KeyError inside bootstrap" made structural
# rather than a separate scenario: a step definition that only ever
# calls `load_config` cannot demonstrate a runtime `KeyError`, so there
# is nothing further for a dedicated scenario to add.

Feature: Field Declaration Configuration

  Scenario: A configuration declaring four named fields loads, and a run transports all four in one step
    Given a configuration declaring four named fields, each with its own initial condition and diffusion coefficient
    When the configuration is loaded and run for a few real timesteps
    Then all four declared fields are present afterward, each changed from its own initial condition

  Scenario: A configuration still setting simulation.scalar_pattern is rejected, not silently defaulted
    Given a configuration file still setting simulation.scalar_pattern
    When the configuration is loaded
    Then loading is rejected with a named error saying the field moved to the top-level fields section

  Scenario: A configuration setting field_display.scalar_pattern still loads, unaffected by the migration
    Given a configuration file setting field_display.scalar_pattern
    When the configuration is loaded
    Then field_display.scalar_pattern carries the configured value, not rejected as the field that moved

  Scenario: Two declared fields with the same name are rejected with a named error
    Given a configuration declaring two fields with the same name
    When the configuration is loaded
    Then loading is rejected with a named error naming the duplicated field

  Scenario: A declared field named after a velocity component is rejected with a named error
    Given a configuration declaring a field named velocity.0
    When the configuration is loaded
    Then loading is rejected with a named error naming the reserved field name

  Scenario: A declared field named after the pressure field is rejected with a named error
    Given a configuration declaring a field named pressure
    When the configuration is loaded
    Then loading is rejected with a named error naming the reserved field name

  Scenario: A declared field with a non-positive diffusion coefficient is rejected
    Given a configuration declaring a field with a non-positive diffusion coefficient
    When the configuration is loaded
    Then loading is rejected with a named error naming the field and its diffusion coefficient

  Scenario: A declared field with an unknown initial-condition pattern is rejected
    Given a configuration declaring a field with an unrecognised initial condition
    When the configuration is loaded
    Then loading is rejected with a named error naming the field and the valid initial conditions

  Scenario: Naming which declared field the renderer colours produces that field's colour map
    Given a configuration declaring two named fields and naming one of them as field_display.render_field
    When the configuration is loaded and run for one real timestep
    Then the named field's own colour map is rendered and the other field's is not

  Scenario: Naming an undeclared field as the renderer's field is rejected
    Given a configuration whose field_display.render_field names a field nothing declares
    When the configuration is loaded
    Then loading is rejected with a named error naming the undeclared field
