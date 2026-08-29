# The acceptance criteria for Velocity Field Support (TASK-031, Stage
# 5's second task in build order). Four subtasks, one feature file --
# scenarios grouped by subtask below, not four files
# (`docs/planning/roadmap.md` TASK-031's own Artifacts Produced: "one
# task's claim", and `make check-scenarios` only cares that every
# scenario runs, not how many files they live in). Not a golden demo --
# no config file under `examples/golden-demos/`, no CLI subprocess run,
# since every claim here is checked against the engine mechanism
# directly, the same `tests/unit/` shape every Stage 4 numerical-scheme
# feature file already established. `tests/unit/
# test_velocity_field_support.py` binds these scenarios.

Feature: Velocity Field Support

  Background:
    Given a small, non-square, non-trivially-origined mesh

  # -- TASK-031a: velocity as component fields -----------------------
  #
  # Isolated from anything that transports or configures -- design
  # question one's own answer (momentum is one ScalarField per
  # component, reassembled into a VectorField for consumers that need
  # one), checked on its own before anything else in this file uses it.

  Scenario: A round trip through decompose and reassemble reproduces the original field's values exactly
    Given a vector field whose values are not 0 or 1 anywhere
    When it is decomposed into components and the components are reassembled
    Then the reassembled field's values exactly match the original

  Scenario: Each decomposed component is a real ScalarField, defined over the original's mesh, named by the fixed convention
    Given a vector field whose values are not 0 or 1 anywhere
    When it is decomposed into components
    Then each component is a ScalarField defined over the same mesh as the original
    And each component's name follows the fixed component-naming convention

  Scenario: Reassembly rejects a component count that disagrees with the mesh's spatial dimensionality
    Given three scalar fields on the same mesh
    When they are reassembled into a vector field
    Then a ComponentCountMismatchError is raised

  Scenario: Reassembly rejects components defined over different meshes
    Given two scalar fields defined over different meshes
    When they are reassembled into a vector field
    Then a ComponentMeshMismatchError is raised

  # -- TASK-031b: viscosity, distinct from a scalar's diffusivity -----
  #
  # The failure mode this subtask guards against is silent: a run using
  # the wrong coefficient still produces a plausible-looking flow, not
  # an error. Both directions are checked, since either alone passes an
  # implementation that wires the two configured values to one number.

  Scenario: Changing viscosity changes a velocity component's diffusive flux and leaves a scalar's own unchanged
    Given a velocity component field and an unrelated scalar field, diffused by the same scheme
    When viscosity changes but the scalar's own diffusion coefficient does not
    Then the velocity component's diffusive flux changes
    And the scalar's own diffusive flux does not change

  Scenario: Changing a scalar's diffusion coefficient changes its own diffusive flux and leaves a velocity component's unchanged
    Given a velocity component field and an unrelated scalar field, diffused by the same scheme
    When the scalar's own diffusion coefficient changes but viscosity does not
    Then the scalar's own diffusive flux changes
    And the velocity component's diffusive flux does not change

  # -- TASK-031c: per-field boundary values at one wall ----------------
  #
  # Exercised by two ordinary scalars, not a velocity pair -- the
  # mechanism this subtask introduces is general (Criterion 1's "applies
  # to any field" clause), and a scenario that only ever used velocity
  # would not distinguish "field-aware" from "velocity-specific".

  Scenario: Two fields prescribed different Dirichlet values at the same wall each see their own value in the interior scheme's flux
    Given two scalar fields with different prescribed Dirichlet values at the same wall
    When the diffusive flux is computed for each field at that wall
    Then each field's flux reflects its own prescribed value, not the other's

  Scenario: A field's own prescribed wall value is independent of another field's
    Given two scalar fields with different prescribed Dirichlet values at the same wall
    When one field's prescribed value changes
    Then the other field's flux at that wall is unchanged

  # -- TASK-031d: velocity advanced by step -----------------------------

  Scenario: Velocity's own components are advanced by the same step call that advances a scalar
    Given a velocity field decomposed into components alongside an unrelated transported scalar
    When the simulation is stepped by one timestep
    Then every velocity component and the scalar are all present, and all advanced, in the result

  Scenario: A transported scalar's result is identical whether the velocity carrying it was solved or prescribed
    Given a scalar transported by a velocity field
    When the simulation is stepped once with that velocity's own components also being transported and once with the same velocity held fixed
    Then the scalar's own result agrees to floating-point tolerance either way

  Scenario: Velocity advected by itself reproduces a hand-derived result
    Given a velocity field whose own components are the only fields being transported
    When the simulation is stepped by one timestep
    Then each component's result matches its own hand-derived value

  Scenario: A velocity field with the wrong component count is rejected by the existing velocity-shape check
    Given a one-component vector field standing in for velocity, and a scalar transported by it
    When the simulation is stepped
    Then an IncompatibleVelocityFieldError is raised

  Scenario: The orchestrator's own source contains no field-name-specific branching for velocity
    When the orchestrator module's source is inspected
    Then it contains no "velocity" string literal, no VectorField isinstance check, and no hardcoded component-name pair
