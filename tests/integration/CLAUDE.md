# CLAUDE

Tests that cross a real boundary rather than exercising isolated logic:
the packaged CLI entry point (via subprocess, not a direct function
call), multiple `pyflow` subsystems working together, file I/O.

`test_cli.py` is the first example: it invokes `python -m pyflow` as a
real subprocess and checks the process boundary (exit code, stdout) --
deliberately not just calling `pyflow.__main__.main()` in-process, since
that wouldn't catch packaging or entry-point issues a real user could
hit. Follow this pattern for anything that genuinely needs to cross a
boundary; if it doesn't, it belongs in `tests/unit/` instead.
