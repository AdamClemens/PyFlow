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
