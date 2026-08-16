# CLAUDE

Runnable golden demo code. The *specification* -- what each demo must do,
how it's verified -- lives at `docs/implementation/golden-demos.md`
(KA-035), not here.

`empty_window.py` (D5, 2026-08-16) is the first demo, Capability Level
0's: opens a real window (glfw backend) with a solid background colour
when run directly (`uv run python examples/golden-demos/empty_window.py`),
and exposes a `run(config, *, max_frames, close_on_key)` function that
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
  just trusts the regression test's pixel assertions;
- **when interactive, wait for explicit input before closing rather than
  either an automatic timeout or relying on the OS window's own close
  button** (maintainer's request, 2026-08-16, after wanting to actually
  look at Empty Window and finding it either closed itself too fast to
  see, or had no obvious way to close). `empty_window.py`'s
  `close_on_key=True` is the pattern: register a `key_down` handler via
  `window.canvas.add_event_handler(handler, "key_down")` that calls
  `window.canvas.close()` on Escape or Enter (`event["key"]`, per
  `rendercanvas`'s event dict), only when the backend isn't `offscreen`
  (which has no keyboard events at all). Print a one-line instruction
  when running interactively (`__main__` block) so it's obvious what to
  press -- don't make someone guess or read the source to find out.
