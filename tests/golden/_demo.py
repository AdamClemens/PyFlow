"""The golden demos' shared test machinery -- the data a scenario
accumulates and the two operations every demo performs.

Separate from `conftest.py` (which holds the Gherkin steps themselves)
because a demo-specific step module has to import these, and importing
from a `conftest` is not something pytest guarantees.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from pyflow.bootstrap import bootstrap
from pyflow.configuration.schema import PyFlowConfig

GOLDEN_DEMOS = Path(__file__).resolve().parents[2] / "examples" / "golden-demos"


@dataclass
class DemoRun:
    """One demo under test, plus whatever running it has produced so far.

    Steps accumulate into this rather than into module globals so two
    scenarios in the same feature file cannot leak into each other.
    """

    config_path: Path
    config: PyFlowConfig
    images: list[np.ndarray] = field(default_factory=list)
    frame_count: int | None = None
    canvas_closed: bool | None = None
    process: subprocess.CompletedProcess[str] | None = None

    @property
    def image(self) -> np.ndarray:
        """The single rendered frame, asserting there is exactly one."""
        assert len(self.images) == 1, f"expected one rendered frame, got {len(self.images)}"
        return self.images[0]


def hex_to_rgba(hex_color: str) -> np.ndarray:
    """`"#rrggbb"` -> `uint8` RGBA, opaque. The one conversion every
    demo's colour assertions share.
    """
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return np.array([r, g, b, 255], dtype=np.uint8)


def render_offscreen(demo: DemoRun, config_path: Path | None = None) -> None:
    """Render one frame through the public Python API and record it on
    `demo`.

    Returns nothing on purpose: a step that wants the frame reads
    `demo.image`, which asserts there is exactly one, so a scenario
    cannot quietly inspect the first of two frames.

    `bootstrap()` rather than the CLI because it is the only way to get
    the frame back for inspection -- still the public API, per
    `docs/implementation/golden-demos.md`'s own carve-out.
    """
    window = bootstrap(config_path or demo.config_path, backend="offscreen", max_frames=1)
    assert window.last_image is not None, "no frame was rendered"
    demo.frame_count = window.frame_count
    demo.canvas_closed = window.canvas.get_closed()
    demo.images.append(window.last_image)
