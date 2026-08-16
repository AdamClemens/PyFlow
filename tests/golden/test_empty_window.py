"""Regression test for the Empty Window golden demo (backlog D5).

Runs headless (offscreen backend) -- this is what CI executes, and what
"included in regression testing" (docs/implementation/golden-demos.md's
Definition of Done) means for a demo with no display available.

Loads `examples/golden-demos/empty_window.py` directly by file path
rather than importing it by dotted name: `examples/` is deliberately not
an importable package (see `examples/CLAUDE.md`), and its directory name
(`golden-demos`, with a hyphen) isn't a legal Python module path anyway.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import numpy as np

from pyflow.configuration import RenderingConfig

_DEMO_PATH = Path(__file__).resolve().parents[2] / "examples" / "golden-demos" / "empty_window.py"


def _load_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("empty_window_demo", _DEMO_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hex_to_rgba(hex_color: str) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, 255)


def test_empty_window_renders_solid_background() -> None:
    demo = _load_demo()
    config = RenderingConfig(backend="offscreen", width=64, height=48)

    window = demo.run(config, max_frames=1)

    assert window.frame_count == 1
    assert window.canvas.get_closed()

    image = window.last_image
    assert image is not None
    assert image.shape == (48, 64, 4)

    expected = np.array(_hex_to_rgba(demo.BACKGROUND_COLOR), dtype=np.uint8)
    assert np.all(image == expected)


def test_empty_window_is_deterministic() -> None:
    demo = _load_demo()
    config = RenderingConfig(backend="offscreen", width=32, height=32)

    first = demo.run(config, max_frames=1).last_image
    second = demo.run(
        RenderingConfig(backend="offscreen", width=32, height=32), max_frames=1
    ).last_image

    assert first is not None
    assert second is not None
    assert np.array_equal(first, second)
