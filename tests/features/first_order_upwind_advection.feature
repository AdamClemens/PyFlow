# The acceptance criteria for First-order Upwind Advection (TASK-023,
# Stage 4's first real numerical scheme). Not a golden demo -- no config
# file under `examples/golden-demos/`, no CLI run; `tests/unit/
# test_first_order_upwind_advection.py` binds these scenarios directly,
# per that directory's own scope (isolated logic, no process boundary).

Feature: First-order Upwind Advection
  Stage 4 Completion Criterion 4's own claim for this task: bounded --
  for an arbitrary field, no interpolated face value falls outside the
  range of the values it interpolates between -- and, separately,
  conservation on a closed domain. Neither is implied by the other, and
  neither is implied by stability, which this task's scheme does not
  have unconditionally (`docs/handbook/numerical-methods/advection.md`).

  Background:
    Given a small, non-square, non-trivially-origined mesh

  Scenario: Every interior face's value is exactly one of its two neighbouring cells' own values
    Given a non-monotonic field and a velocity not aligned with either mesh axis
    When the advective flux is computed
    Then every interior face's implied value equals its owner's or its neighbour's own value, within the range of the two

  Scenario: A boundary face where flow leaves the domain uses the interior cell's own value
    Given a boundary face where the flow points out of the domain
    And that boundary's own condition prescribes a value the interior cell does not have
    When the advective flux is computed
    Then the outflow boundary face's implied value is the interior cell's own value, not the boundary condition's

  Scenario: A boundary face where flow enters the domain and the condition prescribes a value uses that value
    Given a boundary face where the flow points into the domain
    And that boundary's own condition prescribes a fixed value
    When the advective flux is computed
    Then the inflow boundary face's implied value is exactly the prescribed value

  Scenario: A boundary face where flow enters the domain and the condition prescribes a gradient extrapolates from the interior
    Given a boundary face where the flow points into the domain
    And that boundary's own condition prescribes a gradient instead of a value
    When the advective flux is computed
    Then the inflow boundary face's implied value is the interior cell's own value

  Scenario: Inflow at a boundary with no configured condition is rejected
    Given a boundary face where the flow points into the domain
    And that boundary has no configured condition at all
    When the advective flux is computed
    Then an UnconfiguredBoundaryFaceError is raised

  Scenario: Bounded at a modest timestep, the scheme never exceeds its initial range
    Given a one-dimensional line of cells with a single non-zero pulse
    And zero-gradient conditions at both ends
    When the field is advanced for several timesteps at half the CFL limit
    Then the field's magnitude never exceeds its initial maximum at any step

  # Boundedness is a property of a single interpolation; stability is a
  # property of repeated application over time. Advancing the same
  # bounded scheme above its CFL limit shows the two are not the same
  # claim -- `docs/handbook/numerical-methods/advection.md`'s own
  # "boundedness is not stability" note, made executable.
  Scenario: Above the CFL limit, the same scheme diverges beyond its initial range
    Given a one-dimensional line of cells with a single non-zero pulse
    And zero-gradient conditions at both ends
    When the field is advanced for several timesteps at twice the CFL limit
    Then the field's magnitude grows far beyond its initial maximum

  Scenario: Conservation on a closed domain
    Given a domain whose boundary cells all have zero velocity
    And interior cells with a nonzero velocity
    When the field is advanced for many timesteps
    Then the field's total summed over every cell is unchanged to floating-point tolerance
