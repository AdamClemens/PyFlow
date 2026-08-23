# Executable acceptance criteria -- see `empty_window.feature`'s header.

Feature: Empty Mesh
  Stage 1's golden demo (TASK-013): draw an empty computational mesh,
  proving the Mesh layer (TASK-011/012) and its visualisation work
  together. Geometry, still no physics.

  Background:
    Given the golden demo "empty_mesh"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: Both the grid and the background actually render
    # Not just one of them: a grid that failed to render at all would
    # still leave a frame full of the background colour.
    When a frame is rendered offscreen
    Then a pixel of the configured grid colour appears
    And a pixel of the configured background colour appears

  Scenario: The same configuration always produces the same frame
    When it is rendered twice
    Then the two frames are pixel-identical
