"""Regression test for the Mesh Visualiser golden demo (TASK-013).

Golden demos must run through the public API alone -- `pyflow run
--config <file>` -- per `docs/implementation/golden-demos.md`'s
Definition of Done. `empty_mesh.yaml` *is* the demo; no demo-specific
Python module. Follows `test_empty_window.py`'s exact three-test shape.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np

from pyflow.bootstrap import bootstrap
from pyflow.configuration import load_config

CONFIG_PATH = Path(__file__).resolve().parents[2] / "examples" / "golden-demos" / "empty_mesh.yaml"


def _hex_to_rgba(hex_color: str) -> np.ndarray:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return np.array([r, g, b, 255], dtype=np.uint8)


def test_empty_mesh_runs_via_the_public_cli() -> None:
    """At least one test must run the demo exactly as a user would --
    the literal command `docs/implementation/golden-demos.md` documents.
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


def test_empty_mesh_renders_grid_lines_over_the_configured_background() -> None:
    """Deeper pixel verification, via `bootstrap()`. `LineSegmentMaterial`
    defaults to `aa=False` (`build_mesh_grid_line`), so grid-line pixels
    render at the exact configured colour, not blended by antialiasing --
    the same exact-colour-match technique
    `test_empty_window_renders_configured_background` already uses,
    checked for two colours here (grid line and background) instead of
    one, since both must actually be present, not just one of them.
    """
    config = load_config(CONFIG_PATH)
    expected_grid = _hex_to_rgba(config.rendering.grid_color)
    expected_background = _hex_to_rgba(config.rendering.background_color or "#000000")

    window = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1)

    assert window.last_image is not None
    image = window.last_image
    assert np.any(np.all(image == expected_grid, axis=-1)), "no grid-line-coloured pixel found"
    assert np.any(np.all(image == expected_background, axis=-1)), (
        "no background-coloured pixel found"
    )


def test_empty_mesh_is_deterministic() -> None:
    first = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1).last_image
    second = bootstrap(CONFIG_PATH, backend="offscreen", max_frames=1).last_image

    assert first is not None
    assert second is not None
    assert np.array_equal(first, second)
