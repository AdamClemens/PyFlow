# CLAUDE

Runnable golden demo code. The *specification* -- what each demo must do,
how it's verified -- lives at `docs/implementation/golden-demos.md`
(KA-035), not here.

`empty_window.py` (D5, 2026-08-16) is the first demo, Capability Level
0's: opens a real window (glfw backend) with a solid background colour
when run directly (`uv run python examples/golden-demos/empty_window.py`),
and exposes a `run(config, *, max_frames)` function that
`tests/golden/test_empty_window.py` calls with the offscreen backend for
headless regression verification. Not the 2D air-current simulation --
that's the *next* demo, still waiting on the MVP to exist, per
`docs/implementation/golden-demos.md`'s "Initial Golden Demo" section.

Every demo module here should follow the same shape:

- a `run(config, *, max_frames, ...)` function the regression test can
  call directly (loaded by file path, not import -- see
  `tests/golden/CLAUDE.md` for why), returning whatever the test needs to
  assert on (e.g. the `RenderWindow`, so its `last_image` is reachable);
- an `if __name__ == "__main__":` block for interactive/manual use --
  this is how a human actually looks at a demo to sanity-check it, not
  just trusts the regression test's pixel assertions.

**Closing an interactive window by keypress (Escape/Enter) is not a
demo-specific concern any more -- it's `RenderWindow.run()`'s own
default** (`src/pyflow/rendering/window.py`, `close_keys`), on for every
interactive window PyFlow opens, not just golden demos. It moved there
2026-08-16 after `empty_window.py` originally implemented it itself, and
the maintainer found `pyflow run` -- the actual product, not a demo --
had no way to close its window short of killing the process, because the
demo-only version never got wired into `bootstrap.py`'s path. Don't
reimplement this in a new demo; it's already there by default. If a demo
genuinely needs different behaviour, pass `close_keys=` explicitly to
`RenderWindow.run()` rather than adding a parallel handler.
