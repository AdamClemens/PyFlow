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

  # Stage 4 Completion Criterion 4 asks for conservation "on a periodic
  # or fully-closed domain". This is the fully-closed half, and it is
  # deliberately weak: every boundary face here has zero face-normal
  # velocity, so its flux is zero whatever face value the scheme picks,
  # and interior faces cancel by construction inside
  # `accumulate_flux_to_cells`. Verified by mutation at the 2026-08-28
  # Stage 4 exit audit: forcing every advective face flux to 0.0 leaves
  # this scenario passing. What it does still check is that a
  # zero-velocity boundary face contributes nothing *additively* -- a
  # scheme that added a boundary value rather than multiplying by the
  # face-normal velocity would fail it. The periodic half below is what
  # carries the criterion's own "a bounded scheme can still fail to
  # conserve if its flux accounting is wrong" qualifier.
  Scenario: Conservation on a closed domain
    Given a domain whose boundary cells all have zero velocity
    And interior cells with a nonzero velocity
    When the field is advanced for many timesteps
    Then the field's total summed over every cell is unchanged to floating-point tolerance

  # The periodic half, added by the 2026-08-28 Stage 4 exit audit. Here
  # every boundary face carries a genuinely nonzero flux, and
  # conservation is a real property of the wrap accounting rather than a
  # structural guarantee: `accumulate_flux_to_cells` credits a periodic
  # face's contribution to its owner only (the mesh reports no
  # neighbour), so the two faces of a periodic pair cancel globally only
  # if both resolve the same upstream cell -- which a wrapped-neighbour
  # lookup does and a mirrored or clamped one does not. Verified by
  # mutation, not assumed: clamping `neighbour` to the owner at a
  # periodic face makes the total drift and fails this scenario, while
  # leaving the closed-domain scenario above passing.
  Scenario: Conservation on a fully periodic domain
    Given a fully periodic domain and a velocity aligned with neither mesh axis
    When the field is advanced for many timesteps
    Then the field's total summed over every cell is unchanged to floating-point tolerance
