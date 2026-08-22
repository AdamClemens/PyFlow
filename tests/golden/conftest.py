"""Shared Given/When/Then steps for every golden demo's feature file.

The scenarios live in `tests/features/*.feature` and *are* the demos'
acceptance criteria (`adr/ADR-007-executable-acceptance-criteria.md`);
this module is the vocabulary they are written in, and `_demo.py` is the
machinery behind it.

**Keep this vocabulary small and demo-independent.** Every step here is
phrased in terms a reader of `docs/implementation/golden-demos.md` would
recognise -- run the demo, render a frame, compare two frames -- and
none of them mentions a specific demo, colour or mesh. A step only one
feature file could ever use belongs in that demo's own module
(`test_field_display.py` has several), not here. The reason is Stage 4:
its physics scenarios inherit whatever is in this file, and a vocabulary
that has grown demo-specific is one they cannot reuse.
"""

from __future__ import annotations

import subprocess
import sys

import numpy as np
from pytest_bdd import given, parsers, then, when

from pyflow.configuration import load_config

from ._demo import GOLDEN_DEMOS, DemoRun, hex_to_rgba, render_offscreen

# -- Given -----------------------------------------------------------------


@given(parsers.parse('the golden demo "{name}"'), target_fixture="demo")
def _given_the_golden_demo(name: str) -> DemoRun:
    path = GOLDEN_DEMOS / f"{name}.yaml"
    assert path.is_file(), f"no such golden demo config: {path}"
    return DemoRun(config_path=path, config=load_config(path))


# -- When ------------------------------------------------------------------


@when("it is run through the public CLI, headless")
def _when_run_through_the_cli(demo: DemoRun) -> None:
    """The literal command a user would type, as a real subprocess.

    `docs/implementation/golden-demos.md` requires at least one check
    per demo to go through this path rather than an internal shortcut;
    `--backend offscreen` is the one sanctioned override, for CI.
    """
    demo.process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(demo.config_path),
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@when("a frame is rendered offscreen")
def _when_a_frame_is_rendered(demo: DemoRun) -> None:
    render_offscreen(demo)


@when("it is rendered twice")
def _when_rendered_twice(demo: DemoRun) -> None:
    render_offscreen(demo)
    render_offscreen(demo)


# -- Then ------------------------------------------------------------------


@then("the command exits cleanly")
def _then_command_exits_cleanly(demo: DemoRun) -> None:
    assert demo.process is not None, "no CLI run to check"
    assert demo.process.returncode == 0, demo.process.stderr


@then("exactly one frame is presented and the window closes cleanly")
def _then_one_frame_and_closed(demo: DemoRun) -> None:
    assert demo.frame_count == 1
    assert demo.canvas_closed is True


@then("every pixel is the configured background colour")
def _then_every_pixel_is_background(demo: DemoRun) -> None:
    expected = hex_to_rgba(demo.config.rendering.background_color or "#000000")
    assert np.all(demo.image == expected)


@then(parsers.parse("a pixel of the configured {which} colour appears"))
def _then_a_pixel_of_colour_appears(demo: DemoRun, which: str) -> None:
    colors = {
        "background": demo.config.rendering.background_color or "#000000",
        "grid": demo.config.rendering.grid_color,
    }
    assert which in colors, f"unknown configured colour {which!r}; known: {sorted(colors)}"
    expected = hex_to_rgba(colors[which])
    assert np.any(np.all(demo.image == expected, axis=-1)), f"no {which}-coloured pixel found"


@then("the two frames are pixel-identical")
def _then_frames_identical(demo: DemoRun) -> None:
    assert len(demo.images) == 2, f"expected two rendered frames, got {len(demo.images)}"
    assert np.array_equal(demo.images[0], demo.images[1])
