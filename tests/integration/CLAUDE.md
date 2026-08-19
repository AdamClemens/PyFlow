# CLAUDE

Tests that cross a real boundary rather than exercising isolated logic:
the packaged CLI entry point (via subprocess, not a direct function
call), multiple `pyflow` subsystems working together, file I/O.

`test_cli.py` is the first example: it invokes `python -m pyflow` as a
real subprocess and checks the process boundary (exit code, stdout) --
deliberately not just calling `pyflow.__main__.main()` in-process, since
that wouldn't catch packaging or entry-point issues a real user could
hit. Follow this pattern for anything that genuinely needs to cross a
boundary; if it doesn't, it belongs in `tests/unit/` instead. `main()`
also has a complementary in-process unit test
(`tests/unit/test_main.py`) purely so coverage.py has something to
measure -- see that file's own docstring and `pyproject.toml`'s
`[tool.coverage.report]` comment for why both exist.

`test_bootstrap.py` (D4) is the same pattern applied to `pyflow run`.

`test_import_order.py` (D4) is a different reason to cross the process
boundary: it isn't testing packaging, it's testing *import order* --
whether `pyflow.rendering`, say, still imports cleanly when it's the
*first* thing a program imports. Within one process, Python caches every
import in `sys.modules`, so re-importing an already-imported module in
the same test run never re-exercises that ordering; each case runs in a
fresh subprocess for exactly this reason. Exists because D4 found a real
circular import this way (see `src/pyflow/CLAUDE.md`) -- add a module to
its list whenever a new top-level module or subpackage is added.

`test_interactive_window.py` (added 2026-08-17) crosses a different
boundary again: a real OS window system, not just a subprocess. The
three tests needing an actual display carry an explicit
`@_needs_a_real_display` decorator (`pytest.mark.skipif`, built from a
throwaway `GlfwRenderCanvas` probe) -- runs for real on a machine with
one, skips cleanly on headless CI rather than failing. Previously this
behaviour (window creation, distinct per-frame presentation, the
close-key handler) was verified manually only; see
`src/pyflow/rendering/CLAUDE.md` for why that changed and what each test
automates. `test_bootstrap.py` gained a companion test the same day
(`test_run_offscreen_produces_non_blank_output`) that checks actual
pixel content via `bootstrap()`, not just the subprocess exit code -- the
exit-code check alone would not have caught the D5-class bug (a frame
rendered but never presented, silently staying blank) that this is
guarding against.

**The display probe itself crashed real Ubuntu CI, 2026-08-19 -- first
real GitHub Actions run, never reproducible locally.** The original
probe called straight into `GlfwRenderCanvas` inside a bare
`try/except Exception`, on the assumption a headless machine raises a
normal, catchable exception. `ubuntu-latest` has no `DISPLAY` or
`WAYLAND_DISPLAY` at all, and GLFW's native code doesn't fail there with
a Python exception -- it hard-aborts the whole process (`Fatal Python
error: Aborted`, a real SIGABRT inside `glfwSetFramebufferSizeCallback`),
which no `except` clause can catch. Fixed by checking
`DISPLAY`/`WAYLAND_DISPLAY` on Linux *before* `GlfwRenderCanvas` is ever
constructed, so the crash path is never reached. A dedicated regression
test, `test_display_probe_skips_glfw_when_no_display_env_is_set`,
deliberately runs *without* the `@_needs_a_real_display` decorator (it
must run precisely where there is no display) and proves the guard
short-circuits by making a monkeypatched `GlfwRenderCanvas` raise a bare
`BaseException` that `except Exception` would not catch -- standing in
for the real SIGABRT without actually crashing the test runner to prove
it.
