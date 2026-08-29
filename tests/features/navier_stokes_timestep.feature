# The acceptance criteria for Navier-Stokes Timestep (TASK-034, Stage
# 5's fifth and last task in build order). Assembles TASK-031/032/033
# into one incompressible Navier-Stokes timestep, then validates it.
# Not a golden demo -- no config file under `examples/golden-demos/`, no
# CLI subprocess run, since every claim here is checked against the
# engine mechanism directly, the same `tests/unit/` shape every prior
# Stage 4/5 numerical-scheme feature file already established. Each of
# this stage's two golden demos (Lid-Driven Cavity, Heat Diffusion) has
# its own separate feature file, per `docs/planning/roadmap.md`
# TASK-034's own Artifacts Produced bullet. `tests/unit/
# test_navier_stokes_timestep.py` binds these scenarios.

Feature: Navier-Stokes Timestep

  # -- Criterion 4: predictor, corrector, corrected state, each observable

  Scenario: One timestep produces an observable predictor, corrector, and corrected state
    Given a closed, no-slip domain with a divergent initial velocity field
    When one Navier-Stokes timestep is taken
    Then the provisional velocity, the corrected velocity, and the pressure field are all present
    And the corrected velocity differs from the provisional velocity
    And the corrected velocity's own divergence is smaller than the provisional velocity's

  # -- Criterion 4: the two null tests neither of the others can substitute for

  Scenario: Uniform flow on a fully periodic, inviscid, unforced domain stays divergence-free and unchanged over many steps
    Given a fully periodic domain with a uniform, non-axis-aligned velocity field and zero viscosity
    When many Navier-Stokes timesteps are taken
    Then the velocity field is exactly the same uniform value at every step
    And the velocity field's own divergence never leaves solver tolerance at any step

  Scenario: Fluid at rest in a closed, no-slip domain stays at rest over many steps
    Given a closed, no-slip domain with the fluid initially at rest
    When many Navier-Stokes timesteps are taken
    Then the velocity field stays at rest to floating-point tolerance at every step

  # -- Criterion 4: determinism

  Scenario: The same configuration run twice produces identical state
    Given a closed, no-slip domain with a divergent initial velocity field
    When one Navier-Stokes timestep is taken twice from the same initial state
    Then both runs produce identical corrected velocity and pressure fields

  # -- Criterion 13: the solver runs through ADR-003's seams, not around them

  Scenario: The timestep calls the configured PressureCoupling strategy, not a hardcoded one
    Given a PressureCoupling test double registered under its own name and selected by configuration
    When one Navier-Stokes timestep is taken
    Then the test double's own distinctive pressure value appears in the result, not a real solve's

  # -- Criterion 5: Couette flow, at solver tolerance rather than a loose one

  Scenario: Couette flow reaches the exact linear steady velocity profile
    Given a channel periodic in the flow direction, no-slip walls, one stationary and one moving tangentially
    When Navier-Stokes timesteps are taken until the flow reaches steady state
    Then the steady streamwise velocity profile matches the exact linear Couette solution at solver tolerance
    And the wall-normal velocity component stays zero everywhere

  # -- Criterion 5: Lid-driven cavity against Ghia, Ghia & Shin (1982) --
  # the criterion is convergence across resolutions, not a fixed
  # percentage at one; this is this project's most computationally
  # expensive scenario (three real runs to a measured steady state),
  # deliberately, per this task's own Design decision.

  Scenario: The Ghia comparison error decreases monotonically across three mesh resolutions, and the finest shows the right vortex structure
    Given three lid-driven cavity meshes at increasing resolution, at Reynolds number 100
    When each is run to a measured steady state
    Then the error against Ghia's centreline profiles decreases monotonically across the three resolutions
    And the finest resolution's primary vortex centre is within a stated distance of Ghia's own
    And the finest resolution shows both downstream secondary corner vortices, rotating opposite the primary

  # -- Criterion 5: the emergent-phenomenon pair, and its negative control.
  # Taylor-Green vortex decay, chosen over Kelvin-Helmholtz by measurement
  # (`docs/planning/roadmap.md` TASK-034's own Design decision): it
  # reuses this task's own periodic-domain infrastructure directly and
  # has a closed-form decay rate to measure against, rather than needing
  # a roll-up detector.

  Scenario: Taylor-Green vortex decay matches the exact rate when physical viscosity dominates numerical diffusion
    Given a Taylor-Green vortex on a periodic domain at a viscosity where physical diffusion dominates
    When the vortex is advanced and its own decay rate is measured
    Then the measured decay rate matches the exact closed-form rate closely

  Scenario: Taylor-Green vortex decay does not match the exact rate when the advection scheme's own numerical diffusion dominates
    Given a Taylor-Green vortex on a periodic domain at a viscosity where numerical diffusion dominates
    When the vortex is advanced and its own decay rate is measured
    Then the measured decay rate does not match the exact closed-form rate

  # -- Criterion 5: conservation, a claim none of the scenarios above make

  Scenario: No single step increases total kinetic energy for an inviscid, unforced, closed-domain flow
    Given a closed, no-slip domain with a divergent initial velocity field and negligible viscosity
    When many Navier-Stokes timesteps are taken
    Then total kinetic energy never increases from one step to the next
