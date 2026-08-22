# CLAUDE

Regression tests for the golden demos specified in
`docs/implementation/golden-demos.md` -- one test module per demo.

**Every demo's test module must include at least one test that runs it
through the real public CLI, as a subprocess** (maintainer's rule,
2026-08-16): `python -m pyflow run --config
examples/golden-demos/<name>.yaml --backend offscreen --max-frames N`.
That's the literal command a user would type (`--backend offscreen`
aside, the one sanctioned override for headless CI); a test that only
exercises some internal shortcut isn't verifying what the rule actually
requires -- that a demo is genuinely reproducible by a user, not just by
this test suite.

**Since 2026-08-22 these are BDD modules, and the criteria are not
here.** Each demo's acceptance criteria live in
`tests/features/<demo>.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`); a module in this
directory binds them with `scenarios(...)` and supplies only the steps
that no other demo could use. The demo-independent vocabulary -- run the
demo through the CLI, render a frame offscreen, compare two frames --
is in `conftest.py`, and `_demo.py` holds the machinery behind it.

The subprocess rule above is unchanged and is now expressed as a
scenario every demo carries ("A user can run it with the documented
command"), rather than as a convention each module had to remember.

**When adding a demo:** write the feature file first, bind it from a
module here, and add a step only when the shared vocabulary genuinely
cannot express the criterion -- not to make a scenario easier to write.
`make check-scenarios` fails if a feature file exists that nothing
binds, which is the one failure pytest itself is silent about.

`test_empty_window.py` (D5, 2026-08-16) was the first example, and its
original three-test shape is what the three scenarios in
`empty_window.feature` now say:
- `test_empty_window_runs_via_the_public_cli` is that required subprocess
  test.
- `test_empty_window_renders_configured_background` and
  `test_empty_window_is_deterministic` go deeper, via
  `pyflow.bootstrap.bootstrap()` called directly -- still the public API
  (the Python entry point rather than the CLI one), used here only
  because it's the only way to get the rendered frame back
  (`RenderWindow.last_image`) for pixel inspection. Asserts the demo's
  configured background colour renders as an exact, deterministic pixel
  match, not just that nothing raised -- "verifies meaningful behaviour"
  is the Definition of Done's own phrase for this.

There is no demo-specific Python module to load any more (no
`importlib.util.spec_from_file_location` trick, which the first version
of this test needed): golden demos are plain config files under
`examples/golden-demos/`, not scripts, per the public-API rule in
`docs/implementation/golden-demos.md`.
