# The acceptance criteria for Humidity (TASK-037, Stage 6's fourth task
# in build order). Per this task's own Intent (`docs/planning/
# roadmap.md`), adds a named humidity field, transported alongside
# temperature at its own mass diffusivity, taking its own value at a
# shared wall -- the first real test of whether Stage 5's per-field
# coefficient (`CentralDifferenceDiffusion.coefficient_overrides`,
# TASK-031b) and boundary-value (`BoundaryFaceConfig.field_values`/
# `field_gradients`, TASK-031c) mechanisms generalise past momentum, the
# only field either has ever varied for until now.
#
# Not a golden demo -- no config file under `examples/golden-demos/`, no
# CLI subprocess run, the same `tests/unit/` shape `density_field.feature`
# (TASK-036) already established for a Stage 6 task with no golden demo
# of its own (Criterion 9 names only Heat Transport, Smoke Transport and
# Thermal Buoyancy). `tests/unit/test_humidity_field.py` binds these
# scenarios.
#
# **Expected: zero lines under `src/pyflow/`** (this task's own Artifacts
# Produced bullet, `docs/planning/roadmap.md` TASK-037) -- every
# mechanism this feature exercises (`fields:` declaring more than one
# scalar with its own `diffusion_coefficient`, `field_values`/
# `field_gradients` at a wall) already exists, built for velocity's own
# two components (TASK-031b/c) and for a single scalar at a time
# (TASK-042). This task's real subject is whether those surfaces
# generalise to two independently-named, independently-configured
# scalar fields sharing one run -- not whether new machinery is needed.

Feature: Humidity

  # -- Criterion 3's first bullet: two fields transported together, each
  # diffusing at its own configured rate -- `temperature_field.feature`'s
  # own decay-rate scenario, doubled onto two fields sharing one run, and
  # the first time `coefficient_overrides` carries anything but momentum.
  # A shared-rate bug (both fields decaying at the same rate regardless
  # of their own configured diffusivity) would still pass a scenario that
  # only checked one field; checking both, at two different configured
  # rates, is what makes this scenario able to fail on that specific
  # defect.

  Scenario: Temperature and humidity, transported together at different diffusivities, each decay at their own configured rate
    Given a periodic domain transporting a temperature field and a humidity field together, each with its own diffusivity
    When it is run for a few real timesteps and again for many more
    Then each field's own measured decay rate matches the analytic rate set by its own diffusion coefficient and wavenumber

  # -- Criterion 3's second bullet: the `field_values`/`field_gradients`
  # surface TASK-031c built and proved at the hand-constructed-object
  # level (`velocity_field_support.feature`'s own two components) and
  # nothing since has exercised through real configuration -- this
  # scenario is the first to go `load_config` -> `assemble_numerics` ->
  # a resolved `BoundaryCondition` for two independently-named scalar
  # fields.

  Scenario: A committed configuration prescribes different Dirichlet values for temperature and humidity at the same wall
    Given a committed configuration declaring field_values for a temperature field and a humidity field at the same wall
    When numerics are assembled from that configuration
    Then the resolved boundary condition returns each field's own configured value at that wall, not the other's or the wall's own default

  # -- Criterion 6: species-mass-shaped conservation, the same shape
  # `density_field.feature`'s own pure-advection scenario already
  # establishes for density, applied to humidity -- pure advection, no
  # diffusion, no source, so nothing but the transport itself could be
  # responsible for a leak.

  Scenario: The humidity field's own domain integral is conserved under pure advection on a periodic domain
    Given a periodic domain transporting a humidity field by pure advection alone, with no diffusion and no source
    When many timesteps are taken
    Then the humidity field's own domain integral is unchanged to floating-point precision

  # -- Criterion: "humidity does not perturb temperature" made concrete
  # -- a shared diffusion scheme dispatching on field name is exactly
  # where a leak between two fields transported together would live, and
  # nothing before this task has ever run two declared scalar fields
  # through one configuration to check for it.

  Scenario: Running with a humidity field declared leaves temperature identical to running without it
    Given a configuration transporting a temperature field alone
    And the same configuration with a humidity field also declared
    When both are run for the same number of real timesteps
    Then the temperature field is identical, element by element, whether or not humidity is present
