"""Unit tests for tools/benchmarks/benchmark_demos.py.

Not part of the `pyflow` package (a repo-consistency/dev-tool script, not
library code), so it's imported via `sys.path` -- see
tools/benchmarks/CLAUDE.md and the identical convention
`tests/unit/test_generate_status_report.py` already establishes for
`tools/generators/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_BENCHMARKS = Path(__file__).resolve().parents[2] / "tools" / "benchmarks"
if str(TOOLS_BENCHMARKS) not in sys.path:
    sys.path.insert(0, str(TOOLS_BENCHMARKS))

from benchmark_demos import (  # noqa: E402
    DEFAULT_CONFIGS,
    BenchmarkRecord,
    PhaseTiming,
    append_history,
    build_records,
    format_phase_report,
    format_report,
    main,
    phase_totals,
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


def test_phase_totals_recombines_startup_and_per_frame_per_repeat() -> None:
    timings = [
        PhaseTiming(startup=2.0, steady_per_frame=0.1),
        PhaseTiming(startup=3.0, steady_per_frame=0.2),
    ]
    # frames=10: repeat 1 -> 2.0 + 9*0.1 = 2.9; repeat 2 -> 3.0 + 9*0.2 = 4.8.
    assert phase_totals(timings, frames=10) == [2.9, 4.8]


def _fake_records(config: Path, count: int = 1) -> list[BenchmarkRecord]:
    return [
        BenchmarkRecord(
            timestamp=f"2026-09-06T00:00:0{i}+00:00",
            pyflow_version="0.3.0",
            git_commit="abc1234",
            hostname="test-host",
            config=str(config),
            frames=50,
            repeats=3,
            startup_min_s=5.0,
            startup_mean_s=5.1,
            startup_stdev_s=0.1,
            per_frame_min_s=0.1,
            per_frame_mean_s=0.11,
            per_frame_stdev_s=0.01,
            total_min_s=9.9,
            total_mean_s=10.5,
            total_stdev_s=0.3,
        )
        for i in range(count)
    ]


def test_build_records_computes_totals_and_stats_per_config(tiny_config: Path) -> None:
    phase_results = {
        tiny_config: [
            PhaseTiming(startup=2.0, steady_per_frame=0.1),
            PhaseTiming(startup=4.0, steady_per_frame=0.3),
        ]
    }
    records = build_records(
        phase_results,
        frames=10,
        repeats=2,
        timestamp="2026-09-06T00:00:00+00:00",
        pyflow_version="0.3.0",
        git_commit="abc1234",
        hostname="test-host",
    )
    assert len(records) == 1
    record = records[0]
    # tiny_config lives under tmp_path, not REPO_ROOT, so _display_path
    # falls back to the path as given (as_posix(), for cross-platform
    # committed history) rather than a repo-relative form.
    assert record.config == tiny_config.as_posix()
    assert record.frames == 10
    assert record.repeats == 2
    assert record.startup_min_s == 2.0
    assert record.per_frame_min_s == 0.1
    # totals: 2.0 + 9*0.1 = 2.9; 4.0 + 9*0.3 = 6.7 -- min is 2.9.
    assert record.total_min_s == pytest.approx(2.9)


def test_append_history_writes_one_json_line_per_record(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    fake_config = Path("examples/experiments/smoke_transport_mesh64.yaml")
    append_history(_fake_records(fake_config, count=2), history_path)

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["config"] == str(fake_config)
    assert first["pyflow_version"] == "0.3.0"


def test_append_history_appends_rather_than_overwrites(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    fake_config = Path("examples/experiments/smoke_transport_mesh64.yaml")
    append_history(_fake_records(fake_config, count=1), history_path)
    append_history(_fake_records(fake_config, count=1), history_path)

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_main_record_appends_a_real_entry_to_the_history_file(
    tiny_config: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    history_path = tmp_path / "history.jsonl"
    main(
        [
            "--config",
            str(tiny_config),
            "--frames",
            "3",
            "--repeats",
            "1",
            "--record",
            "--history-file",
            str(history_path),
        ]
    )
    output = capsys.readouterr().out
    assert "Appended 1 record" in output

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["config"] == tiny_config.as_posix()
    assert record["frames"] == 3
    assert record["repeats"] == 1
    assert record["pyflow_version"]
    assert record["git_commit"]
    assert record["hostname"]

    # --record without --phases still prints the plain report, derived
    # from the same phase-split measurement rather than re-run.
    assert "min (s)" in output
