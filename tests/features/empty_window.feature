# The acceptance criteria for the Empty Window golden demo, in the form
# that executes. `docs/implementation/golden-demos.md` describes what
# this demo is and why; the scenarios below are what "working" means,
# and they are the only statement of it -- see
# `adr/ADR-007-executable-acceptance-criteria.md`.

Feature: Empty Window
  Capability Level 0's golden demo (backlog D5). Open a rendering
  window, display an empty scene, close cleanly. It proves the Stage 0
  bootstrap chain (TASK-005/006/007/010) works end to end -- not any CFD
  functionality, since there is none yet.

  Background:
    Given the golden demo "empty_window"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: A frame actually renders, in the colour the demo configured
    When a frame is rendered offscreen
    Then exactly one frame is presented and the window closes cleanly
    And every pixel is the configured background colour

  Scenario: The same configuration always produces the same frame
    When it is rendered twice
    Then the two frames are pixel-identical
