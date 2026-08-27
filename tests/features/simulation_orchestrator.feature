# The acceptance criteria for the Simulation Orchestrator (TASK-040),
# Stage 4's own criteria 1 and 5's share it owns. Not a golden demo --
# nothing here has a config file under `examples/golden-demos/` or a CLI
# run, since this is the mechanism a future demo (TASK-030) is built on,
# not a demo itself. `tests/unit/test_simulation.py` binds these
# scenarios, per that directory's own scope (isolated logic, no process
# boundary).

Feature: Simulation Orchestrator
  Stage 4 Completion Criterion 1: a real simulation-stepping mechanism
  assembles a mesh, a set of transported fields, and an
  `AssembledNumerics` into an actual per-timestep state advance. Nothing
  else in Stage 4 can be demonstrated without it.

  Background:
    Given a mesh-sharing set of fields and an AssembledNumerics

  Scenario: Stepping returns a new field per key, none mutated
    When the simulation is stepped by one timestep
    Then a new field is returned for every key in the input
    And no input field's own values changed

  Scenario: A zero-everywhere field with zero-everywhere boundary conditions stays at zero
    Given every field and boundary condition is zero everywhere
    When the simulation is stepped by one timestep
    Then every returned field is zero everywhere

  Scenario: Changing a boundary condition's prescribed value changes the accumulated derivative at the adjacent cell
    Given a scheme whose flux depends on its own boundary conditions
    When the simulation is stepped once with one boundary value and once with a different one
    Then the two runs disagree at the cell adjacent to that boundary
    And the accumulation code never asked whether any face was a boundary face

  Scenario: accumulate_flux_to_cells reproduces a hand-derived cell array
    Given a small, non-square, non-trivially-origined mesh
    And a hand-chosen face-value array
    When the face values are accumulated to cells
    Then the result matches the hand-derived cell array exactly, for every cell

  Scenario: A field or velocity on a different mesh than the rest is rejected
    Given a velocity field defined on a different mesh
    When the simulation is stepped by one timestep
    Then a MismatchedMeshError is raised
