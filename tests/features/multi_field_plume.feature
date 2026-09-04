# Executable acceptance criteria -- see `empty_window.feature`'s header.

Feature: Multi-Field Plume
  Stage 6's own claim, made runnable: four differently-named physical
  fields -- temperature, humidity, smoke and a passive tracer --
  declared in one configuration file and transported together in one
  run, alongside a solved velocity, with buoyancy driving the motion
  from one of them.

  Stage 6 shipped three golden demos and every one of them declares
  exactly one field. Its own Completion Criterion 1 says four fields in
  one run, "not four separate one-field runs, which would never
  exercise the sharing that makes this claim interesting" -- and three
  separate one-field runs is precisely what that stage's demos were.
  The criterion was discharged by a scenario in
  `passive_tracers.feature` using four passive *tracers*: four
  instances of one phenomenon, which proves the sharing but does not
  demonstrate the field-centricity. Added 2026-09-04.

  **Exit-code-zero cannot cover what this demo claims to show.** On
  screen it renders one colour-mapped field and looks much like Thermal
  Buoyancy; what makes it this demo is the three fields riding along
  beside the one being drawn. So it follows `numerics_assembly`'s own
  precedent (`tests/golden/CLAUDE.md`): the run reports what it
  declared, and that report is read back through the real CLI.

  Background:
    Given the golden demo "multi_field_plume"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: The run reports every field it was configured to transport
    # The demonstration itself, not a convenience: a reader cannot see
    # four fields in one rendered frame, so the run says what it is
    # carrying, through the process boundary a user actually crosses.
    When it is run through the public CLI, headless
    Then its output reports transporting exactly the fields the configuration declares

  Scenario: All four fields are transported together in one run
    When it is stepped for several real timesteps
    Then the run carries all four declared fields at once

  Scenario: No two fields are the same field under different names
    # The failure this guards against is one tensor shared across four
    # names, which would satisfy "four fields exist" perfectly.
    When it is stepped for several real timesteps
    Then no two of the four fields hold identical values

  Scenario: Each field diffuses at its own configured rate
    # Stage 6's "every field carries its own physical coefficients"
    # claim, seen in a demo rather than a unit fixture: the four
    # diffusivities span 25x, so the sharpest field must stay measurably
    # sharper than the smoothest.
    When it is stepped for several real timesteps
    Then the field with the smallest diffusivity is sharper than the field with the largest

  Scenario: The buoyant field drives the flow, and the others ride it
    # One coupling, four fields. Temperature is the only field declaring
    # a buoyancy coefficient; the plume must rise, and the three
    # non-buoyant fields must be carried by that same velocity.
    When it is stepped for several real timesteps
    Then the temperature field's centre of mass has risen
    And every other field has also been displaced from where it started

  Scenario: The orchestrator never learns what any of these fields is
    # The structural half, the same `inspect.getsource` mechanism
    # `passive_tracers.feature` already uses -- restated for this demo
    # because a demo that hardcoded a field name would still pass every
    # scenario above.
    When the orchestrator module's source is inspected
    Then it contains no "temperature", "humidity", "smoke" or "tracer" string literal

  Scenario: The same configuration always produces the same frame
    When it is rendered twice
    Then the two frames are pixel-identical
