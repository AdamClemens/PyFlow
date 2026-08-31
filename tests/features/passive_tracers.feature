# The acceptance criteria for Passive Tracers (TASK-038, Stage 6's fifth
# and last task). Per this task's own Intent (`docs/planning/
# roadmap.md`): "passive" is the testable word -- a tracer must have no
# measurable effect on the velocity field, checked by running the same
# configuration with and without tracers and comparing the velocity
# field exactly, the only check that can fail.
#
# Not a golden demo -- no config file under `examples/golden-demos/`, no
# CLI subprocess run, the same `tests/unit/` shape `humidity_field.
# feature`/`density_field.feature` already established. This stage's
# actual golden demo (Smoke Transport) gets its own feature file,
# `tests/features/smoke_transport.feature`, bound from `tests/golden/`,
# the same split TASK-035's own two demos used.
#
# The second scenario below deliberately uses four named tracer fields,
# not two -- Stage 6 Completion Criterion 1's own "at least four named
# fields transport in one run... alongside a solved velocity, not four
# separate one-field runs" is discharged here, cheaply, per this task's
# own Acceptance Criteria bullet ("the multi-field case Criterion 1's
# first bullet asks for, exercised where it is cheapest to check").

Feature: Passive Tracers

  # -- Criterion 5, both bullets, in one scenario deliberately: a tracer
  # that the engine silently ignores would pass "velocity unaffected"
  # perfectly, which is exactly why the criterion's own text insists both
  # checks happen together rather than in separate scenarios that could
  # each pass for the wrong reason.

  Scenario: A passive tracer never affects velocity, and is not itself inert
    Given a configuration transporting solved velocity with no tracer declared
    And the same configuration with a passive tracer also declared
    When both are run for the same number of real timesteps
    Then the velocity fields are identical, element by element, whether or not the tracer is present
    And the tracer field is measurably different after several timesteps than after one

  # -- Criterion 5's third bullet, and Stage 6 Completion Criterion 1's
  # own "at least four named fields transport in one run... not four
  # separate one-field runs" -- four tracers, one configuration, one
  # `bootstrap()` call, each with its own diffusivity so a wrong
  # implementation that silently shared one field's tensor across all
  # four names cannot pass by coincidence.

  Scenario: Four passive tracers transported together in one run each behave independently
    Given a configuration transporting solved velocity alongside four passive tracers with different diffusivities
    When it is run for several real timesteps
    Then no two of the four tracer fields are identical to each other
    And a tracer's own field is identical whether it is transported alongside the other three or alone

  # -- Stage 6 Completion Criterion 1's own structural bullet, checked
  # for all four of this stage's phenomena at once -- the same
  # `inspect.getsource(simulation)` mechanism `velocity_field_support.
  # feature`/`temperature_field.feature` each already use for their own
  # one name, extended here since no earlier task's own Discharges
  # claimed this bullet for "density", "humidity" or "tracer".

  Scenario: The orchestrator's own source contains no field-name-specific branching for any of this stage's phenomena
    When the orchestrator module's source is inspected
    Then it contains no "temperature", "density", "humidity" or "tracer" string literal
