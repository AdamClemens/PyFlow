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

Every demo module here should follow the same shape: a `run()` function
the regression test can call directly (loaded by file path, not import
-- see `tests/golden/CLAUDE.md` for why), plus an `if __name__ ==
"__main__":` block for interactive/manual use.
