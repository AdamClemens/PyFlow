"""A run that raises inside a frame must fail (TASK-053, Stage 9).

Stage 9 Completion Criterion 4. Until this task, it did not: an exception
raised inside `RenderWindow._draw`'s own `on_frame` callback was swallowed
by `rendercanvas`'s `with log_exception("Draw error")` block (in that
third-party package's own `base.py`, not anything tracked here), so
PyFlow never saw it and `pyflow run` printed `pyflow exited cleanly` and
returned 0. Measured on the shipped lid-driven cavity refined to 64x64
with its own `numerics.timestep` untouched: **22 of 40 frames failed and
the exit code was 0.**

Integration tests, not unit ones, and deliberately so: the defect lives
in what happens when control is inverted to a third-party event loop, and
the exit code is the observable the criterion names. A unit test calling
`RenderWindow.run` in-process would check the re-raise but not that it
becomes a non-zero exit, which is the half a user actually meets
(`tests/CLAUDE.md`'s own split).

**The fixture is a real configuration that genuinely diverges**, not a
monkeypatched exception. A patched one would prove the plumbing carries
*an* exception; this proves the engine's own
`DivergenceDidNotConvergeError` reaches a user, which is Stage 4's own
use case ("be told when it did not converge instead of receiving a
plausible wrong answer") and the reason this criterion exists.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_DIVERGING_CONFIG = """\
# The shipped lid-driven cavity, refined to 64x64 with its own timestep
# left alone -- `stable_timestep` puts the limit at 0.00391 for this
# mesh, so 0.008 is 2.05x over it and the run blows up at step 17.
# Measured before this fixture was written, not assumed.
mesh:
  extent: [64, 64]
  spacing: [0.015625, 0.015625]

numerics:
  timestep: 0.008
  boundary_conditions:
    north:
      type: dirichlet
      field_values:
        velocity.0: 1.0
        velocity.1: 0.0
    south:
      type: dirichlet
    east:
      type: dirichlet
    west:
      type: dirichlet

simulation:
  velocity_solved: true

fluid:
  viscosity: 0.01
"""

_FRAMES = 25
"""Past the measured divergence at step 17, with margin. Deliberately not
hundreds: the point is that the run stops, and a run that kept going to
frame 500 before anyone noticed is the behaviour under repair.
"""


@pytest.fixture
def diverging_config(tmp_path: Path) -> Path:
    config = tmp_path / "diverging.yaml"
    config.write_text(_DIVERGING_CONFIG, encoding="utf-8")
    return config


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pyflow", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_run_exits_non_zero_when_a_frame_raises(diverging_config: Path) -> None:
    result = _run(
        "run",
        "--config",
        str(diverging_config),
        "--backend",
        "offscreen",
        "--max-frames",
        str(_FRAMES),
    )

    assert result.returncode != 0, (
        "a run whose frames raise must not report success; got exit 0 with "
        f"stderr:\n{result.stderr}"
    )
    # The engine's own diagnostic, not merely *an* error -- per
    # `tests/integration/CLAUDE.md`'s convention that a non-zero
    # assertion carries a stderr substring, so argparse failures and real
    # ones stay distinguishable.
    assert "pressure correction loop did not reach tolerance" in result.stderr, result.stderr


def test_a_failed_run_does_not_claim_to_have_exited_cleanly(diverging_config: Path) -> None:
    result = _run(
        "run",
        "--config",
        str(diverging_config),
        "--backend",
        "offscreen",
        "--max-frames",
        str(_FRAMES),
    )

    # The specific sentence a user saw before this task, immediately
    # after a traceback that `rendercanvas` had logged and PyFlow had not
    # seen. Asserted by its absence rather than only by the exit code,
    # because the two failed independently: the message is emitted by
    # `bootstrap()` on any normal return from `window.run`.
    assert "pyflow exited cleanly" not in result.stderr, result.stderr


def test_a_failed_run_stops_rather_than_finishing_its_frame_budget(
    diverging_config: Path,
) -> None:
    result = _run(
        "run",
        "--config",
        str(diverging_config),
        "--backend",
        "offscreen",
        "--max-frames",
        str(_FRAMES),
    )

    # `offscreen render complete: N frame(s)` is logged only after the
    # whole budget has been drawn. Before this task the loop ran to
    # completion over failing frames and logged it; now the run stops at
    # the first failure, so the line must be absent.
    assert "offscreen render complete" not in result.stderr, result.stderr


def test_a_healthy_run_still_exits_cleanly() -> None:
    # The other half of the claim: this must not fire on every run. A
    # guard that always trips is a guard nobody can act on -- the same
    # reasoning TASK-054's own "absent below the limit" criterion states.
    result = _run(
        "run",
        "--config",
        "examples/golden-demos/lid_driven_cavity.yaml",
        "--backend",
        "offscreen",
        "--max-frames",
        "5",
    )

    assert result.returncode == 0, result.stderr
    assert "pyflow exited cleanly" in result.stderr, result.stderr


# -- The interactive backend -------------------------------------------------
#
# Criterion 4 names both backends, and the two fail differently. On
# `offscreen` the loop above ran its whole budget over failing frames and
# reported success; on `glfw` the raise also skipped `on_draw`'s own
# reschedule, so the frame budget was never reached and the process
# **hung** -- observed at 300 s before being killed, and now exiting 1 in
# 22 s.
#
# **Display-guarded, so this runs on Windows CI and skips on Linux**
# (`tests/integration/CLAUDE.md`; `docs/planning/backlog.md` carries the
# open item for that asymmetry, with the two attempted fixes and why each
# was reverted). Recorded rather than left implicit: this half of the
# criterion is evidenced on one of the two platforms CI covers.

_needs_a_real_display = pytest.mark.skipif(
    not (
        os.environ.get("DISPLAY")
        or os.environ.get("WAYLAND_DISPLAY")
        or sys.platform in ("win32", "darwin")
    ),
    reason="no display available for a real glfw window",
)


@_needs_a_real_display
def test_an_interactive_run_terminates_rather_than_hanging_when_a_frame_raises(
    diverging_config: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(diverging_config),
            "--max-frames",
            str(_FRAMES),
        ],
        capture_output=True,
        text=True,
        check=False,
        # The bug this guards is a hang, so the timeout *is* the
        # assertion -- generous enough that a slow machine is not a false
        # failure, and far below the 300 s the unfixed version ran past.
        timeout=180,
    )

    assert result.returncode != 0, result.stderr
    assert "pressure correction loop did not reach tolerance" in result.stderr, result.stderr
