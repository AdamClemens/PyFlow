# The acceptance criteria for Central Difference Diffusion (TASK-024,
# Stage 4's third task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_central_difference_diffusion.py` binds these scenarios directly,
# per that directory's own scope (isolated logic, no process boundary).

Feature: Central Difference Diffusion
  Stage 4 Completion Criterion 4's own claim for this task: second-order
  accuracy under mesh refinement (`docs/handbook/numerical-methods/
  diffusion.md`) -- a measured convergence rate, not a qualitative "the
  field diffuses" -- and, separately, conservation under zero-flux
  boundaries. Neither is implied by the other.

  Background:
    Given a small, non-square, non-trivially-origined mesh

  Scenario: Every interior face's flux matches the central-difference formula
    Given a non-uniform field with known values at every cell
    When the diffusive flux is computed
    Then every interior face's flux equals the diffusion coefficient times the neighbouring cells' value difference divided by their centroid distance

  Scenario: A boundary face whose condition prescribes a value uses the central difference to that value
    Given a boundary face whose condition prescribes a fixed value
    When the diffusive flux is computed
    Then that boundary face's flux equals the diffusion coefficient times the prescribed value minus the owner's own value, divided by the owner-to-face distance

  Scenario: A boundary face whose condition prescribes a gradient uses that gradient directly
    Given a boundary face whose condition prescribes a gradient
    When the diffusive flux is computed
    Then that boundary face's flux equals the diffusion coefficient times the prescribed gradient, regardless of the owner's own value

  Scenario: A boundary face with no configured condition is rejected
    Given a boundary face with no configured condition at all
    When the diffusive flux is computed
    Then an UnconfiguredBoundaryFaceError is raised

  # `docs/handbook/numerical-methods/diffusion.md`'s own claim, made
  # executable: central differencing is second-order accurate on a
  # uniform orthogonal mesh. Measured on the spatial operator alone
  # (the discrete Laplacian `accumulate_flux_to_cells` recovers from this
  # scheme's own face flux), not through real time-stepping -- TASK-025
  # (RK4) doesn't exist yet, and isolating spatial from temporal error is
  # exactly what TASK-025's own convergence criterion does in reverse.
  Scenario: The scheme is second-order accurate under mesh refinement
    Given a smooth field with a known exact Laplacian, at increasing mesh resolutions
    When the discrete Laplacian is measured at each resolution
    Then the observed convergence order is close to two

  Scenario: Conservation under zero-flux boundaries
    Given a domain whose boundary conditions all prescribe a zero gradient
    And interior cells with a non-uniform field
    When the field is advanced for many timesteps
    Then the field's total summed over every cell is unchanged to floating-point tolerance
