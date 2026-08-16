"""Regression test for the Empty Window golden demo (backlog D5).

Golden demos must run through the public API alone -- `pyflow run
--config <file>`, exactly what a user would type -- per
`docs/implementation/golden-demos.md`'s Definition of Done. There is no
demo-specific Python module to load any more: `empty_window.yaml` *is*
the demo.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np

from pyflow.bootstrap import bootstrap
from pyflow.configuration import load_config

CONFIG_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "golden-demos" / "empty_window.yaml"
)


def _hex_to_rgba(hex_color: str) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, 255)


def test_empty_window_runs_via_the_public_cli() -> None:
    """At least one test must run the demo exactly as a user would --
    the literal command `docs/implementation/golden-demos.md` documents,
    not an internal shortcut. `--backend offscreen` is the one allowed
    override: it's what makes an interactive demo runnable headlessly in
    CI, the same way a user could run it themselves for the same reason.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyflow",
            "run",
            "--config",
            str(CONFIG_PATH),
            "--backend",
            "offscreen",
            "--max-frames",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_empty_window_renders_configured_background() -> None:
    """Deeper pixel verification, via `bootstrap()` -- also the public
    API (just the Python one, not the CLI), used because it's the only
    way to get the rendered frame back for inspection.
    """
    expected = np.array(
        _hex_to_rgba(load_config(CONFIG_PATH).rendering.background_color or "#000000"),
        dtype=np.uint8,
    )

    window = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1)

    assert window.frame_count == 1
    assert window.canvas.get_closed()
    assert window.last_image is not None
    assert np.all(window.last_image == expected)


def test_empty_window_is_deterministic() -> None:
    first = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1).last_image
    second = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1).last_image

    assert first is not None
    assert second is not None
    assert np.array_equal(first, second)
