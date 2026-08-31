# The acceptance criteria for the Smoke Transport golden demo (TASK-038,
# Stage 6, `docs/planning/implementation-plan.md` Level 3's own Golden
# Demo list). `tests/golden/test_smoke_transport.py` binds these
# scenarios.
#
# Added while implementing TASK-038, the same "the roadmap's own
# Artifacts Produced bullet named the demo config, not a second feature
# file" gap `heat_transport.feature`/`thermal_buoyancy.feature` each
# closed for TASK-035 -- see either file's own header comment.
#
# The exactness of "passive" (no effect on velocity, and not itself
# inert) is Stage 6 Completion Criterion 5, proven at the engine level by
# `tests/features/passive_tracers.feature` against a small, purpose-built
# fixture -- not re-proven here. This demo's own job, per
# `docs/implementation/golden-demos.md`'s Definition of Done, is a
# reproducible, visible run that verifies meaningful behaviour: a
# declared field genuinely being carried by a real, solved, recirculating
# lid-driven flow.

Feature: Smoke Transport
  Passive tracers carried by a solved velocity field, with no effect on
  it (`planning/data/demos.yaml`'s own description) -- the same
  lid-driven-cavity flow `lid_driven_cavity.yaml` already proved stable,
  now also carrying a declared `smoke` field.

  Background:
    Given the golden demo "smoke_transport"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: The smoke field is genuinely carried by the recirculating flow
    When it is bootstrapped for a single real timestep and again for several more
    Then the smoke field after several timesteps differs from the smoke field after one
