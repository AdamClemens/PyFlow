"""Regression test: every pyflow subpackage must import cleanly first
(backlog D4).

D4 found a real circular import: `pyflow.engine` (which then held
`bootstrap.py`) needed `pyflow.rendering`, while `pyflow.rendering.window`
needed `pyflow.engine.logging_setup` -- so whichever package a program
imported first would find the other only partially initialised. Fixed by
moving `bootstrap.py` to the `pyflow` package root (see
`src/pyflow/CLAUDE.md`). This test guards against that specific class of
bug reappearing: within a single process, Python caches every import in
`sys.modules` after the first one, so re-importing modules that are
already cached would not actually re-exercise import *order* -- each
case here runs in a fresh subprocess instead, the only way to genuinely
test "this module, imported first, in a clean interpreter."
"""

import subprocess
import sys

import pytest

# Every subpackage/module that could plausibly be someone's first import
# of pyflow. Add to this list if a new top-level module or subpackage is
# added -- that's exactly the kind of change that could reintroduce this
# class of bug.
MODULES = [
    "pyflow",
    "pyflow.configuration",
    "pyflow.engine",
    "pyflow.rendering",
    "pyflow.physics",
    "pyflow.physics.buoyancy",
    "pyflow.bootstrap",
    "pyflow.simulation_run",
    "pyflow.checkpoint",
    "pyflow.recording",
    "pyflow.replay",
    "pyflow.playback",
    "pyflow.__main__",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_cleanly_first(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


# Stage 8 Completion Criterion 1 (`docs/planning/roadmap.md`): the
# headless-recording modules must not be able to reach the renderer at
# all -- not merely default to headless. TASK-046's own Acceptance
# Criteria state the same claim for `replay.py`.
#
# **Added 2026-09-11 by the Stage 8 exit audit.** Both criteria were
# true and neither was gated: Criterion 1 said in its own text that the
# claim "was checked by hand at implementation time", and
# `test_module_imports_cleanly_first` above proves only that each module
# imports without error -- it would pass just as happily with
# `import pyflow.rendering` at the top of `recording.py`. A by-hand
# check does not survive the next import somebody adds, which is exactly
# what this criterion exists to prevent.
HEADLESS_MODULES = [
    "pyflow.checkpoint",
    "pyflow.recording",
    "pyflow.replay",
    "pyflow.simulation_run",
]

# `pyflow.rendering` itself, plus the three third-party layers underneath
# it -- a module could pull in `pygfx`/`wgpu`/`glfw` directly without
# going through `pyflow.rendering`, and that would break this criterion
# just as thoroughly.
_RENDERING_PREFIXES = ("pyflow.rendering", "pygfx", "rendercanvas", "wgpu", "glfw")


@pytest.mark.parametrize("module", HEADLESS_MODULES)
def test_headless_module_never_reaches_the_renderer(module: str) -> None:
    """A fresh subprocess, so `sys.modules` reflects this import alone.

    Checks the *transitive* closure, not the module's own import
    statements: anything `recording.py` imports that itself imports
    `rendering` would show up here, which is the form the criterion is
    actually written in ("nor anything that transitively imports it").
    """
    probe = (
        f"import sys; import {module}; "
        f"print([m for m in sys.modules if m.startswith({_RENDERING_PREFIXES!r})])"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", (
        f"{module} transitively imported a rendering module: {result.stdout.strip()}"
    )
