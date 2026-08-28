# The acceptance criteria for Neumann Boundary (TASK-029, Stage 4's
# eighth task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_neumann_boundary.py` binds these scenarios directly, per that
# directory's own scope (isolated logic, no process boundary).

Feature: Neumann Boundary Condition
  Stage 4 Completion Criterion 4's own claim for this task: correctness
  is checked in what a real *interior* scheme (Advection, Diffusion)
  computes at a boundary face using a real `NeumannBoundaryCondition`,
  not only in what `evaluate()` returns in isolation
  (`docs/planning/roadmap.md` TASK-029's own Intent, "as TASK-028, for a
  prescribed gradient"). Every scenario here prescribes a *nonzero*
  gradient -- a zero-gradient result is also what a boundary wired to
  nothing at all would silently produce, so a zero-gradient fixture alone
  could not tell a genuine wiring from a missing one.

  Background:
    Given a small, non-square, non-trivially-origined mesh

  Scenario: A real Neumann condition wired into diffusion supplies its prescribed gradient directly to the boundary flux
    Given a boundary face
    And a real Neumann boundary condition prescribing a nonzero gradient
    When the diffusive flux is computed using this condition
    Then that boundary face's flux equals the diffusion coefficient times the prescribed gradient, regardless of the owner's own value

  Scenario: A real Neumann condition wired into advection is not read numerically for the advective boundary value
    Given a boundary face where the flow points into the domain
    And a real Neumann boundary condition prescribing a nonzero gradient
    When the advective flux is computed using this condition
    Then the inflow boundary face's implied value is the interior cell's own value, not the prescribed gradient
