# The acceptance criteria for Dirichlet Boundary (TASK-028, Stage 4's
# seventh task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_dirichlet_boundary.py` binds these scenarios directly, per that
# directory's own scope (isolated logic, no process boundary).

Feature: Dirichlet Boundary Condition
  Stage 4 Completion Criterion 4's own claim for this task: correctness
  is checked in what a real *interior* scheme (Advection, Diffusion)
  computes at a boundary face using a real `DirichletBoundaryCondition`,
  not only in what `evaluate()` returns in isolation
  (`docs/planning/roadmap.md` TASK-028's own Intent). A condition object
  can return the right value and still be wired into the flux
  computation wrongly -- these scenarios build the real interior scheme
  and the real condition together, never a hand-written double standing
  in for either.

  Background:
    Given a small, non-square, non-trivially-origined mesh

  Scenario: A real Dirichlet condition wired into advection supplies its prescribed value at an inflow boundary
    Given a boundary face where the flow points into the domain
    And a real Dirichlet boundary condition prescribing a value distinct from the interior cell's own value
    When the advective flux is computed using this condition
    Then the inflow boundary face's implied value is exactly the condition's prescribed value

  Scenario: A real Dirichlet condition wired into diffusion supplies its prescribed value to the central-difference boundary flux
    Given a boundary face
    And a real Dirichlet boundary condition prescribing a value distinct from the owner cell's own value
    When the diffusive flux is computed using this condition
    Then that boundary face's flux equals the diffusion coefficient times the prescribed value minus the owner's own value, divided by the owner-to-face distance
