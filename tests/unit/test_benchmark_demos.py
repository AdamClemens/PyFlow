"""Unit tests for tools/benchmarks/benchmark_demos.py.

Not part of the `pyflow` package (a repo-consistency/dev-tool script, not
library code), so it's imported via `sys.path` -- see
tools/benchmarks/CLAUDE.md and the identical convention
`tests/unit/test_generate_status_report.py` already establishes for
`tools/generators/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS_BENCHMARKS = Path(__file__).resolve().parents[2] / "tools" / "benchmarks"
if str(TOOLS_BENCHMARKS) not in sys.path:
    sys.path.insert(0, str(TOOLS_BENCHMARKS))

from benchmark_demos import (  # noqa: E402
    DEFAULT_CONFIGS,
    PhaseTiming,
    format_phase_report,
    format_report,
    main,
    run_benchmark,
    run_phase_benchmark,
    time_one_run,
    time_phases,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def tiny_config(tmp_path: Path) -> Path:
    """The smallest real, headless-renderable config `bootstrap()` accepts
    -- mirrors `tests/unit/test_bootstrap.py`'s own tiny fixtures. Real
    enough to exercise a genuine `bootstrap()` call end to end without
    the cost of an actual golden demo.
    """
    config_file = tmp_path / "tiny.yaml"
    config_file.write_text(
        "rendering:\n  backend: offscreen\nmesh:\n  extent: [2, 2]\n  spacing: [1.0, 1.0]\n",
        encoding="utf-8",
    )
    return config_file


def test_time_one_run_returns_a_positive_duration(tiny_config: Path) -> None:
    duration = time_one_run(tiny_config, frames=1)
    assert duration > 0.0


def test_run_benchmark_returns_repeats_timings_per_config(tiny_config: Path) -> None:
    results = run_benchmark([tiny_config], frames=1, repeats=2)
    assert list(results.keys()) == [tiny_config]
    timings = results[tiny_config]
    assert len(timings) == 2
    assert all(duration > 0.0 for duration in timings)


def test_format_report_names_every_config_with_its_min_and_mean() -> None:
    fake_config = Path("examples/golden-demos/smoke_transport.yaml")
    report = format_report({fake_config: [1.5, 1.0, 2.0]}, frames=5, repeats=3)
    assert str(fake_config) in report
    assert "min (s)" in report
    assert "mean (s)" in report
    assert "1.000" in report  # the minimum of [1.5, 1.0, 2.0]
    assert "5 frame" in report
    assert "3 repeat" in report


def test_default_configs_point_at_real_files() -> None:
    """Regression: a typo'd default path would silently benchmark nothing
    useful the moment `bootstrap()` raised, but only when someone actually
    ran `make benchmark` -- catch it at collection time instead.
    """
    for config_path in DEFAULT_CONFIGS:
        assert (REPO_ROOT / config_path).is_file()


def test_main_runs_end_to_end_for_an_explicit_tiny_config(
    tiny_config: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--config", str(tiny_config), "--frames", "1", "--repeats", "1"])
    output = capsys.readouterr().out
    assert str(tiny_config) in output
    assert "1 frame" in output
    assert "1 repeat" in output


def test_format_report_includes_spread() -> None:
    """stdev/max columns, for judging how consistent repeats are."""
    fake_config = Path("examples/golden-demos/smoke_transport.yaml")
    report = format_report({fake_config: [1.5, 1.0, 2.0]}, frames=5, repeats=3)
    assert "stdev" in report
    assert "max (s)" in report
    assert "2.000" in report  # the maximum of [1.5, 1.0, 2.0]


def test_time_phases_rejects_frames_not_greater_than_one(tiny_config: Path) -> None:
    with pytest.raises(ValueError):
        time_phases(tiny_config, frames=1)


def test_time_phases_returns_startup_and_steady_per_frame(tiny_config: Path) -> None:
    timing = time_phases(tiny_config, frames=3)
    assert isinstance(timing, PhaseTiming)
    assert timing.startup > 0.0
    assert isinstance(timing.steady_per_frame, float)


def test_run_phase_benchmark_returns_repeats_of_phase_timings(tiny_config: Path) -> None:
    results = run_phase_benchmark([tiny_config], frames=3, repeats=2)
    assert list(results.keys()) == [tiny_config]
    timings = results[tiny_config]
    assert len(timings) == 2
    assert all(isinstance(t, PhaseTiming) for t in timings)


def test_format_phase_report_names_every_config_with_startup_and_per_frame() -> None:
    fake_config = Path("examples/experiments/smoke_transport_mesh64.yaml")
    report = format_phase_report(
        {
            fake_config: [
                PhaseTiming(startup=2.5, steady_per_frame=0.06),
                PhaseTiming(startup=2.0, steady_per_frame=0.05),
            ]
        },
        frames=50,
        repeats=2,
    )
    assert str(fake_config) in report
    assert "startup" in report
    assert "per-frame" in report
    assert "2.000" in report  # the minimum startup


def test_main_runs_phase_mode_end_to_end_for_an_explicit_tiny_config(
    tiny_config: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--config", str(tiny_config), "--frames", "3", "--repeats", "1", "--phases"])
    output = capsys.readouterr().out
    assert str(tiny_config) in output
    assert "startup" in output
