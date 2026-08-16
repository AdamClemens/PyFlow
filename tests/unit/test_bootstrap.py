"""Unit tests for pyflow.bootstrap (in-process, offscreen backend).

Complements `tests/integration/test_bootstrap.py`, which verifies the
real `python -m pyflow run` subprocess; this calls `bootstrap()` directly
so pytest-cov can actually measure it -- subprocess execution isn't
tracked, which is why `bootstrap.py` showed 0% coverage despite the
integration test genuinely running it.
"""

from pathlib import Path

from pyflow.bootstrap import bootstrap


def test_bootstrap_loads_config_and_runs_headless(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rendering:\n  backend: offscreen\n  width: 64\n  height: 64\n")

    window = bootstrap(config_file, max_frames=2)

    assert window.frame_count == 2
    assert window.canvas.get_closed()


def test_bootstrap_backend_override(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rendering:\n  backend: glfw\n"
    )  # would open a real window if not overridden

    window = bootstrap(config_file, max_frames=1, backend="offscreen")

    assert window.canvas.get_closed()
