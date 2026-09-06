"""Unit tests for tools/generators/generate_benchmark_report.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_GENERATORS = Path(__file__).resolve().parents[2] / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_benchmark_report import OUTPUT_PATH, load_records, render  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _record(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "timestamp": "2026-09-06T00:00:00+00:00",
        "pyflow_version": "0.3.0",
        "git_commit": "abc1234",
        "hostname": "test-host",
        "config": "examples/experiments/smoke_transport_mesh64.yaml",
        "frames": 50,
        "repeats": 3,
        "startup_min_s": 6.222,
        "startup_mean_s": 6.522,
        "startup_stdev_s": 0.370,
        "per_frame_min_s": 0.1761,
        "per_frame_mean_s": 0.1923,
        "per_frame_stdev_s": 0.0133,
        "total_min_s": 14.85,
        "total_mean_s": 15.9,
        "total_stdev_s": 0.5,
    }
    base.update(overrides)
    return base


def test_render_with_no_records_says_so_honestly() -> None:
    output = render([])
    assert "No benchmark records yet" in output
    assert "make record-benchmarks" in output


def test_render_says_it_is_generated() -> None:
    """Root CLAUDE.md: generated documentation must never be edited
    manually. A generated file that doesn't say so invites exactly that.
    """
    output = render([])
    assert "generated" in output.lower()
    assert "benchmark_history.jsonl" in output


def test_render_groups_by_config_and_names_every_field() -> None:
    output = render([_record()])
    assert "examples/experiments/smoke_transport_mesh64.yaml" in output
    assert "abc1234" in output
    assert "test-host" in output
    assert "6.222" in output  # startup min
    assert "0.1761" in output  # per-frame min


def test_render_orders_entries_newest_first_within_a_config() -> None:
    older = _record(timestamp="2026-09-01T00:00:00+00:00", git_commit="older01")
    newer = _record(timestamp="2026-09-06T00:00:00+00:00", git_commit="newer01")
    output = render([older, newer])
    assert output.index("newer01") < output.index("older01")


def test_render_sorts_configs_so_output_is_stable() -> None:
    a = _record(config="examples/experiments/zeta.yaml")
    b = _record(config="examples/experiments/alpha.yaml")
    output = render([a, b])
    assert output.index("alpha.yaml") < output.index("zeta.yaml")


def test_load_records_returns_empty_list_for_a_missing_file(tmp_path: Path) -> None:
    assert load_records(tmp_path / "does-not-exist.jsonl") == []


def test_load_records_reads_one_json_object_per_line(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    history_path.write_text(
        '{"config": "a.yaml"}\n{"config": "b.yaml"}\n',
        encoding="utf-8",
    )
    records = load_records(history_path)
    assert [r["config"] for r in records] == ["a.yaml", "b.yaml"]


def test_the_committed_benchmark_history_is_up_to_date() -> None:
    """The same assertion `make check-benchmark-report` makes, run as
    part of the ordinary suite so a stale file fails fast rather than
    only at the end of `make ci`.
    """
    expected = render(load_records())
    assert OUTPUT_PATH.read_text(encoding="utf-8") == expected
