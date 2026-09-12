# The acceptance criteria for the Sealed Box golden demo (TASK-052,
# Stage 9). `tests/golden/test_sealed_box.py` binds these scenarios.
#
# Stage 9's own Golden Demo, and the visible form of the defect that
# opened the stage: a tracer in a closed, no-slip cavity has nowhere to
# go. Before TASK-052 it left through the walls, because
# `FirstOrderUpwindAdvection` took a boundary face's transporting
# velocity from the cell inside it rather than from what the
# configuration prescribed there.
#
# **This demo checks the wall, not the domain integral** -- see the
# config file's own header for why. Diffusion to a zero-valued wall
# removes tracer legitimately, and `FieldConfig` will not accept a
# perfectly non-diffusive one, so exact conservation is proven at the
# engine level instead (`tests/features/boundary_velocity.feature`)
# against a purely advective fixture. What is checkable here, on a
# committed config through the public API, is that no tracer crosses a
# wall by advection while the flow against those walls is still moving.

Feature: Sealed Box
  A tracer stirred by a real, solved lid-driven flow inside a closed
  no-slip cavity -- and still entirely inside it.

  Background:
    Given the golden demo "sealed_box"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  # The second scenario `tests/golden/CLAUDE.md` requires of any demo
  # whose output is its point: a clean exit alone would pass against a
  # box that leaked, and against one whose flow never started.

  Scenario: No tracer crosses a wall, and the flow against those walls is still moving
    When it is bootstrapped for several real timesteps
    Then every wall face carries exactly zero advective flux
    And the cells against those walls still carry real motion

  Scenario: The tracer is genuinely carried by the recirculating flow
    When it is bootstrapped for several real timesteps
    Then the tracer field has measurably changed from where it started
