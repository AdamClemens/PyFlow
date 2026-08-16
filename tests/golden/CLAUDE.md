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

`test_empty_window.py` (D5, 2026-08-16) is the first example:
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
