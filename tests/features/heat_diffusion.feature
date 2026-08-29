# The acceptance criteria for the Heat Diffusion golden demo (TASK-034,
# Stage 5 Completion Criterion 8, and `docs/implementation/mvp.md`'s own
# Validation section, reconciled 2026-08-28 -- heat diffusion is the
# diffusion equation on a transported scalar, no named Temperature field
# needed). `tests/golden/test_heat_diffusion.py` binds these scenarios.

Feature: Heat Diffusion
  A single sinusoidal mode, one full wavelength across the mesh's own
  x-extent, on an otherwise unforced, unadvected, fully periodic domain
  -- the one initial condition PyFlow's diffusion equation has a
  closed-form answer for: exponential decay at a rate set only by the
  diffusion coefficient and the mode's own wavenumber.

  Background:
    Given the golden demo "heat_diffusion"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  # "Numerical solution is measurable" (`docs/implementation/mvp.md`'s
  # own Definition of Done), checked against an exact analytic answer
  # rather than only "heat visibly spread" -- distinct from Stage 4's
  # own diffusion criteria, which measured spatial convergence order and
  # conservation, neither of which is a decay *rate*.
  Scenario: The mode's own amplitude decays at the exact analytic rate set by the diffusion coefficient and its wavenumber
    When it is bootstrapped once after a few real timesteps and again after many more
    Then the measured decay rate matches the analytic rate for the configured diffusion coefficient and wavenumber
