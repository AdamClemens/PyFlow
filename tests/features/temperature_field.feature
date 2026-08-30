# The acceptance criteria for Temperature (TASK-035, Stage 6's second
# task in build order). Adds a named temperature field and the one
# coupling this stage needs -- a Boussinesq body force reaching momentum
# through `SourceTerm`, the Stage 3 interface with no implementation
# until now (`adr/ADR-010-source-term-state.md`).
#
# Not a golden demo -- no config file under `examples/golden-demos/`, no
# CLI subprocess run, the same `tests/unit/` shape
# `navier_stokes_timestep.feature` already established for engine-level
# claims. This task's own two golden demos (Heat Transport, Thermal
# Buoyancy) each get their own feature file, bound from `tests/golden/`,
# the same split TASK-034 used for its own two -- `tests/features/
# heat_transport.feature`, `tests/features/thermal_buoyancy.feature`.
# `tests/unit/test_temperature_field.py` binds the scenarios below.

Feature: Temperature

  # -- Criterion: naming the field costs nothing -- the anonymous scalar
  # in Stage 5's Heat Diffusion demo and a named temperature field must
  # decay at the identical analytic rate, since both are the same
  # physics under a different name.

  Scenario: A named temperature field decays at its own configured thermal diffusivity
    Given a periodic domain transporting a named temperature field with a sinusoidal initial condition
    When it is run for a few real timesteps and again for many more
    Then the measured decay rate matches the analytic rate set by the temperature field's own diffusion coefficient and wavenumber

  # -- Criterion: warm fluid rises, sign derived in advance
  # (`docs/planning/roadmap.md` TASK-035's own "The sign, derived here
  # rather than left to the implementer").

  Scenario: A warm patch in a still, uniform domain acquires upward vertical velocity
    Given a closed, no-slip domain at rest with a warm patch and downward gravity
    When several Navier-Stokes timesteps are taken
    Then the warm patch's own vertical velocity is measurably upward

  Scenario: Reversing gravity reverses the warm patch's own motion
    Given a closed, no-slip domain at rest with a warm patch and upward gravity
    When several Navier-Stokes timesteps are taken
    Then the warm patch's own vertical velocity is measurably downward

  # -- Criterion: the null case is exact, not approximate

  Scenario: A uniform temperature field produces a velocity field identical to carrying no temperature field at all
    Given a closed, no-slip domain at rest with a uniform temperature field and downward gravity
    And the same domain carrying no temperature field at all
    When several Navier-Stokes timesteps are taken on both
    Then the two velocity fields are identical, element by element

  # -- Criterion: the configured source term is the one the timestep
  # calls -- Stage 5 Criterion 13's own substitution mechanism, applied
  # to this stage's seventh seam.

  Scenario: The timestep calls the configured source term, not a hardcoded one
    Given a SourceTerm test double registered under its own name and selected by configuration
    When one Navier-Stokes timestep is taken
    Then the test double's own distinctive contribution appears in the result, not a real source's

  # -- Criterion: a field with no buoyancy coupling declared is
  # completely unaffected by the source-term mechanism -- the regression
  # guard for putting a new term inside every field's own derivative.

  Scenario: A run with no buoyancy coupling declared is identical whether or not a source term is selected
    Given a configuration transporting a declared field with no buoyancy coupling on it, source term left at its default
    And the same configuration with the boussinesq_buoyancy source term selected instead
    When several Navier-Stokes timesteps are taken on both
    Then the two runs produce identical fields, element by element

  # -- Criterion: convection onset, the qualitative bar design question
  # five settled -- rolls form heated from below, not heated from above.
  # The critical Rayleigh number (~1708, rigid-rigid) is explicitly not
  # this stage's bar; the quantitative comparison is deferred to Stage 7.

  Scenario: A fluid layer heated from below convects; the same layer heated from above does not
    Given a closed, no-slip fluid layer heated from below
    And the same layer heated from above instead
    When both are advanced for many Navier-Stokes timesteps
    Then the layer heated from below develops a substantially larger vertical velocity than the one heated from above

  # -- Criterion: rejection paths exercised against real bad input --
  # the sixth named surface, belonging to this task since only it knows
  # the buoyancy coupling exists.

  Scenario: A buoyancy coupling declared in a run whose velocity is not solved is rejected at configuration load
    Given a configuration declaring a field with a buoyancy coupling and simulation.velocity_solved left false
    When the configuration is loaded
    Then loading is rejected with a named error naming the field and requiring solved velocity

  # -- Criterion: the orchestrator never learns a phenomenon's name --
  # the same structural check `velocity_field_support.feature` already
  # makes for "velocity", now for "temperature".

  Scenario: The orchestrator's own source contains no field-name-specific branching for temperature
    When the orchestrator module's source is inspected
    Then it contains no "temperature" string literal
