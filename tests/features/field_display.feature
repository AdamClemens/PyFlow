# Executable acceptance criteria -- see `empty_window.feature`'s header.

Feature: Field Display
  Stage 2's golden demo (TASK-017): a scalar field drawn as a colour
  map and a vector field drawn as arrows, over one mesh, sharing one
  legend. The fields hold values; nothing transports them yet.

  This demo checks rendered pixels at predicted positions rather than
  "a pixel of this colour exists somewhere", which is what Empty Mesh
  settles for. That is possible because `field_display.yaml` pins a
  canvas whose aspect matches the framed view's exactly, so the
  world-to-pixel mapping is plainly linear -- verified live before these
  criteria relied on it, per `src/pyflow/rendering/CLAUDE.md`.

  Background:
    Given the golden demo "field_display"

  Scenario: A user can run it with the documented command
    When it is run through the public CLI, headless
    Then the command exits cleanly

  Scenario: Every cell renders the exact colour its own value maps to
    # The scalar-only variant, not the demo file: every cell's arrow
    # starts at that cell's own centroid, so sampling a centroid against
    # the combined demo sometimes reads the arrow instead of the field.
    Given the scalar-only variant of that demo
    When a frame is rendered offscreen
    Then all 9 cells show exactly the colour the scalar colour map predicts

  Scenario: Cells with different values are visibly different, not merely unequal
    Given the scalar-only variant of that demo
    When a frame is rendered offscreen
    Then the centre and corner cells differ by more than 20 levels in some channel

  Scenario: The legend is drawn with the field's own colour function
    When a frame is rendered offscreen
    Then the legend's low and high ends match the scalar colour map's own output

  Scenario: An arrow points where its cell's vector points
    When a frame is rendered offscreen
    Then cell 0's arrow is drawn in the configured arrow colour at its own midpoint

  Scenario: A cell whose vector is exactly zero draws no arrow at all
    # Not a zero-length line rendered as a stray dot.
    When a frame is rendered offscreen
    Then the centre cell shows its field colour and not the arrow colour

  # Stage 7 (Rendering Annotations) -- this demo is that stage's own
  # Golden Demo, and its Goal is that a viewer can read what the run is,
  # what the colour map means and how large it is without opening the
  # config file. The four scenarios below check the annotations are
  # actually rasterised inside the framed view, not merely present in
  # the scene: each names a band of the frame that holds one annotation
  # and nothing else, so a HUD placed outside the camera's own bounds,
  # or not drawn at all, fails here while every object-presence
  # assertion in `tests/unit/test_bootstrap.py` still passes.

  Scenario: The title is drawn above the mesh, in the frame
    When a frame is rendered offscreen
    Then the "title" band of the frame is not empty

  Scenario: Both spatial axes are labelled with the mesh's own extent
    # P-019, the standing rule this stage produced.
    When a frame is rendered offscreen
    Then the "x-axis ticks" band of the frame is not empty
    And the "y-axis ticks" band of the frame is not empty

  Scenario: The legend carries its field's name and its numeric endpoints
    When a frame is rendered offscreen
    Then the "legend caption" band of the frame is not empty
    And the "legend endpoints" band of the frame is not empty

  Scenario: The mesh's cell and domain size are readable in the same frame
    When a frame is rendered offscreen
    Then the "stats" band of the frame is not empty

  Scenario: The same configuration always produces the same frame
    When it is rendered twice
    Then the two frames are pixel-identical

  Scenario: The demo's configuration is the one it claims to be
    Then the configuration selects the "radial_gradient" and "rotational" patterns
