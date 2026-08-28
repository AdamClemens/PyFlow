# The acceptance criteria for the Passive Scalar Transport golden demo,
# in the form that executes. `docs/implementation/golden-demos.md`
# describes what this demo is and why; the scenarios below are what
# "working" means -- see `adr/ADR-007-executable-acceptance-criteria.md`.

Feature: Passive Scalar Transport
  Stage 4's own golden demo (TASK-030, roadmap Stage 4 Completion
  Criterion 1): the first `pyflow run` that actually steps a real
  simulation forward, live, via `simulation.step()` wired into
  `RenderWindow.run(on_frame=...)` -- every earlier demo rendered exactly
  one static frame. A prescribed (not solved -- Stage 5 solves
  Navier-Stokes for real) uniform velocity field carries a scalar blob
  across a periodic domain.

  Background:
    Given the golden demo "passive_scalar_transport"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  # "physical fields evolve" (`docs/implementation/mvp.md`'s own
  # Definition of Done), measured directly rather than only checked by
  # pixel-diffing two frames: the field's own mass-weighted centroid
  # (the closest thing a scalar field has to "position") has to move
  # downstream at roughly the prescribed velocity over real elapsed
  # time -- not merely "the pixels changed somewhere", which a stalled
  # or frozen simulation loop could not distinguish from a broken one.
  Scenario: The transported field's own centroid moves downstream at the prescribed velocity over real elapsed time
    When it is bootstrapped once after a few real timesteps and again after many more
    Then the field's mass-weighted centroid has moved downstream by approximately the prescribed velocity times the elapsed time
