# The acceptance criteria for Density (TASK-036, Stage 6's third task in
# build order). Adds a named density field that drives motion through
# the coupling TASK-035 already built (`BoussinesqBuoyancy`), and shows
# that doing so takes no second implementation and no engine change --
# this task's own real subject, per its own Intent, is Criterion 4:
# turning TASK-035's buoyancy implementation from an implementation into
# a claim.
#
# Not a golden demo -- density is not one of Stage 6's three demos
# (Heat Transport, Smoke Transport, Thermal Buoyancy), so there is no
# config file under `examples/golden-demos/` and no CLI subprocess run.
# `tests/unit/test_density_field.py` binds these scenarios, the same
# `tests/unit/` shape `temperature_field.feature` already established.
#
# Design question three (resolved 2026-08-30, `docs/planning/roadmap.md`):
# this stage is Boussinesq, so "conserves mass" below means the density
# field's own domain integral is conserved by its transport, not that
# continuity itself has been generalised -- the scenario named
# "conserved" is about the field, and the one named "unchanged" is about
# continuity, deliberately two different claims.

Feature: Density

  # -- Criterion 6: dense fluid sinks, the mirror of TASK-035's warm
  # patch rising -- a scenario that fails if the shared coupling's own
  # coefficient convention were wrong in a direction temperature alone
  # could not detect (a sign error common to both couplings would still
  # pass every direction check TASK-035 wrote).

  Scenario: A denser patch in a still, uniform domain acquires downward vertical velocity
    Given a closed, no-slip domain at rest with a denser patch and downward gravity
    When several Navier-Stokes timesteps are taken
    Then the denser patch's own vertical velocity is measurably downward

  # -- Criterion 4: the object, not the behaviour. Two implementations
  # that individually get their own sign right would still pass every
  # scenario above and fail this one if they were two objects instead of
  # one -- which is why this is a substitution check against a single
  # constructed instance, not two direction checks compared by eye.

  Scenario: One BoussinesqBuoyancy instance is constructed from a configuration declaring both a temperature and a density coupling
    Given a committed configuration declaring a temperature field and a density field, each with its own buoyancy coupling
    And a SourceTerm test double registered under its own name and selected by configuration
    When numerics are assembled from that configuration
    Then the test double was constructed with both couplings, keyed by field name

  # -- Criterion 6: species-mass-shaped conservation, the density
  # analogue of Stage 4's own advection conservation check, under pure
  # advection (no diffusion, no source) so nothing but the transport
  # itself could be responsible for a leak.

  Scenario: The density field's own domain integral is conserved under pure advection on a periodic domain
    Given a periodic domain transporting a density field by pure advection alone, with no diffusion and no source
    When many timesteps are taken
    Then the density field's own domain integral is unchanged to floating-point precision

  # -- Design question three's own exclusion, made executable: continuity
  # itself is untouched by this task, checked against the actual
  # mechanism ("the corrector still drives cell divergence to the
  # configured tolerance"), not against GreenGaussDivergence's own naive
  # measure, which `lid_driven_cavity.feature`'s own note already records
  # is not what PISO's corrector loop actually converges.

  Scenario: The pressure corrector still drives divergence to the configured tolerance whether or not a density field is present
    Given a closed, no-slip domain with a divergent initial velocity field and no density field
    And the same domain carrying a density field with a buoyancy coupling instead
    When one Navier-Stokes timestep is taken on both
    Then both runs converge their own recorded divergence below the configured tolerance
