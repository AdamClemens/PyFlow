# The acceptance criteria for the Heat Transport golden demo (TASK-035,
# Stage 6, `docs/planning/implementation-plan.md` Level 3's own
# named-Temperature demo -- distinct from Stage 5's Heat Diffusion, which
# transports an anonymous scalar). `tests/golden/test_heat_transport.py`
# binds these scenarios.
#
# Added while implementing TASK-035, alongside `thermal_buoyancy.feature`
# -- the roadmap's own Artifacts Produced bullet named only
# `temperature_field.feature`, but this task builds two brand-new golden
# demos, and every prior task that did (TASK-030, TASK-034) gave each of
# its own demos a dedicated feature file rather than folding a new demo's
# claims into a mechanism-level one. Followed here for the same reason:
# a golden demo's acceptance criteria belong next to its own config file,
# not mixed into scenarios that carry no config at all.

Feature: Heat Transport
  The same physics as Stage 5's Heat Diffusion demo, on a field the
  configuration actually names: a single sinusoidal mode decays at a
  rate set only by the diffusion coefficient and the mode's own
  wavenumber. This demo's whole content is that naming the field and
  giving it a real identity costs nothing -- no buoyancy coupling here.

  Background:
    Given the golden demo "heat_transport"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: The named temperature field decays at the same analytic rate Heat Diffusion measures for an anonymous scalar
    When it is bootstrapped once after a few real timesteps and again after many more
    Then the measured decay rate matches the analytic rate for the configured diffusion coefficient and wavenumber
