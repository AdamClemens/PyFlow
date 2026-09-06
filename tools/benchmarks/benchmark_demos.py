"""Benchmark PyFlow's end-to-end demo runtime through the real `pyflow
run` CLI (`tools/benchmarks/`, added 2026-09-06).

This session's own seven-fix vectorization arc (`docs/planning/
roadmap.md` TASK-022/026/040/024/023/027 x2, `examples/experiments/
CLAUDE.md`) needed a real before/after number after every change, and
every one of those numbers came from an ad hoc, hand-typed timing script
-- rewritten from scratch each time, with nothing left behind once the
number was copied into a document. One of those ad hoc runs was measured
while a background `make ci` run was still using the CPU, producing a
misleadingly slow number that had to be caught and re-measured by hand
before it was recorded. This script is that same measurement, made
repeatable: run the demo exactly the way a user does, several times, and
report the fastest -- so the next perf change gets a number from one
command instead of a rewritten script, and a contaminated run shows up
as an outlier against its own repeats instead of being reported alone.

**Only measures end-to-end demo wall-clock time, not an isolated
internal call** (e.g. timing `PISO.correct()` by itself) --
deliberately. `bootstrap()` is PyFlow's one sanctioned public entry point
(`src/pyflow/CLAUDE.md`, `docs/implementation/golden-demos.md`), the same
reason a golden demo is defined as "the relevant command with the
relevant configuration, not bespoke code." An isolated per-function
number is real, useful, investigative data -- this session produced
several -- but it depends on internals that change shape with every one
of these fixes; reaching into `PISO`/`CentralDifferenceDiffusion`
directly here would need updating this script every time those internals
change, the exact restated-fact drift this repository's own generators
exist to avoid (`docs/CLAUDE.md`). The public API's shape is stable;
time that instead.

**Times the real `uv run python -m pyflow run ...` command as a
subprocess, not an in-process `bootstrap()` call.** The first version of
this script called `bootstrap()` directly and timed only that call --
verified wrong, not assumed, by comparing its own numbers against the
documented ones: it reported roughly 4-10x faster than every number this
session's own documents recorded for the same configs (`examples/
experiments/CLAUDE.md`, `docs/planning/roadmap.md`), because those
numbers were all produced by running the demo exactly the way its own
config-file comment says to reproduce it -- `uv run python -m pyflow
run --config ... --backend offscreen --max-frames N`, a fresh process
per run -- while an in-process call skips interpreter startup and
`torch`/`pygfx` import entirely, and running several repeats in the same
process lets `torch` warm up across them in a way a real one-shot user
invocation never gets to. Re-running the same config through the real
subprocess command confirmed the documented number instead (~5.67s
against a recorded ~5.1s, well within run-to-run noise) -- see
`docs/CLAUDE.md`'s Integrity section on reporting a mistake plainly
rather than quietly fixing it. Costs one process-startup per repeat,
which is the point: that startup is part of what a user actually
experiences and what the historical numbers already include.

**Reports the minimum across repeats, not the mean.** A contaminated run
(another heavy process sharing the CPU) only ever makes a run slower,
never faster, so the minimum is the closer estimate of the demo's own
real cost, and is far less sensitive to a single bad repeat than an
average would be. Run this in isolation -- nothing else CPU-heavy (a
`make ci`, another benchmark, a background test run) -- or a
contaminated repeat can still drag every repeat down together.

Not wired into `make ci`, and has no `--check` mode -- like
`tools/generators/generate_graph_view.py`: a performance number varies by
machine and by everything else running on it, so there is no structural
fact here to gate on, and no committed file for a `--check` to compare
against. Run via `make benchmark`.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The benchmark suite: every config whose performance history matters
# going forward (2026-09-06, when `--record`/`benchmark_history.jsonl`
# below made "history" a real, growing, committed thing rather than a
# one-off comparison). Started as the two configs the original
# investigation was anchored to (`examples/experiments/CLAUDE.md`) and
# grew the same day to the full 32/64/128 mesh-scaling series plus the
# Re = 1000 trial once those existed too -- add a config here, per
# `tools/benchmarks/CLAUDE.md`'s own standing rule, whenever new
# functionality earns a benchmark. Resolved against REPO_ROOT so
# `make benchmark`/`make record-benchmarks` work from the repository
# root regardless of Makefile invocation details, the same convention
# `tools/generators/generate_status_report.py` uses.
DEFAULT_CONFIGS: tuple[Path, ...] = (
    REPO_ROOT / "examples" / "golden-demos" / "smoke_transport.yaml",
    REPO_ROOT / "examples" / "experiments" / "smoke_transport_high_res.yaml",
    REPO_ROOT / "examples" / "experiments" / "smoke_transport_mesh64.yaml",
    REPO_ROOT / "examples" / "experiments" / "smoke_transport_mesh128.yaml",
    REPO_ROOT / "examples" / "experiments" / "smoke_transport_re1000.yaml",
)

# `tools/benchmarks/benchmark_history.jsonl`: the permanent, append-only
# record `--record` writes to and `tools/generators/
# generate_benchmark_report.py` reads from -- see both modules' own
# docstrings.
HISTORY_PATH = REPO_ROOT / "tools" / "benchmarks" / "benchmark_history.jsonl"

# 50, not 5 (2026-09-06, raised at the maintainer's request as the new
# standard for a mesh-scaling comparison): 5 frames spends a
# disproportionate share of total time on frame one's own one-time cost
# (PISO's cached Poisson-matrix build, `pressure_coupling.py`'s own
# `_cached_poisson_matrix`) rather than the steady per-step cost a real
# run mostly consists of -- exactly what `time_phases` below exists to
# separate out and quantify, rather than leave as an unmeasured
# assumption baked into a short run.
DEFAULT_FRAMES = 50
DEFAULT_REPEATS = 3


def time_one_run(config_path: Path, frames: int) -> float:
    """Wall-clock seconds for one full `pyflow run` subprocess of
    `config_path` for `frames` frames, headless (`--backend offscreen`)
    -- the same command examples/experiments/smoke_transport_high_res.yaml's
    own comment names as how to reproduce its numbers, run for real
    rather than approximated in-process (see this module's own docstring
    for why an in-process `bootstrap()` call gave the wrong number).
    """
    command = [
        sys.executable,
        "-m",
        "pyflow",
        "run",
        "--config",
        str(config_path),
        "--backend",
        "offscreen",
        "--max-frames",
        str(frames),
    ]
    start = time.perf_counter()
    subprocess.run(command, cwd=REPO_ROOT, capture_output=True, check=True)
    return time.perf_counter() - start


def run_benchmark(configs: list[Path], frames: int, repeats: int) -> dict[Path, list[float]]:
    """`{config_path: [seconds, ...]}`, `repeats` timings per config, run
    in the order given -- one config's own repeats stay adjacent, so a
    transient contamination is easier to spot as an outlier within them.
    """
    return {
        config_path: [time_one_run(config_path, frames) for _ in range(repeats)]
        for config_path in configs
    }


def format_report(results: dict[Path, list[float]], frames: int, repeats: int) -> str:
    """`stdev`/`max` alongside `min`/`mean` (added 2026-09-06, prompted by
    a direct question about how consistent repeats actually are): `min`
    is what every consumer of this report acts on (the "a contaminated
    run only ever makes a run slower" reasoning above), but a reader
    cannot judge whether 3 repeats is enough to trust that minimum from
    `min`/`mean` alone -- `stdev`/`max` are what let them see the spread
    the minimum was drawn from, in the same report, rather than needing
    to re-run this script with more repeats just to find out.
    """
    lines = [
        f"PyFlow demo benchmark -- {frames} frame(s) per run, "
        f"best of {repeats} repeat(s), offscreen backend",
        "",
        f"{'config':<55} {'min (s)':>9} {'mean (s)':>9} {'stdev (s)':>10} {'max (s)':>9}",
        "-" * 94,
    ]
    for config_path, timings in results.items():
        lines.append(
            f"{str(config_path):<55} {min(timings):>9.3f} {statistics.mean(timings):>9.3f} "
            f"{statistics.pstdev(timings):>10.3f} {max(timings):>9.3f}"
        )
    return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class PhaseTiming:
    """One phase-split measurement of a single config: `startup` is a
    lone `--max-frames 1` subprocess (process/import startup, config and
    window/mesh setup, and -- for a run whose first frame steps at all --
    `PISO`'s own one-time cached Poisson-matrix build, all baked into
    frame one's own cost since nothing in `bootstrap.py` logs a boundary
    between "setup" and "stepping"); `steady_per_frame` is the marginal
    cost of every frame *after* that one-time cost, computed rather than
    measured directly -- see `time_phases` below for how.
    """

    startup: float
    steady_per_frame: float


def time_phases(config_path: Path, frames: int) -> PhaseTiming:
    """Splits one config's own runtime into `startup` and
    `steady_per_frame` from two real subprocess runs (`time_one_run`,
    unchanged) rather than by adding timing instrumentation inside
    `bootstrap.py` itself -- this module's own docstring already commits
    to timing only the public API, not internals, and internals reshape
    with every performance fix (`examples/experiments/CLAUDE.md`'s own
    eight-fix history) while `pyflow run --max-frames N` does not.

    `time_one_run(config_path, frames=1)` gives `startup` directly: a
    single frame's own cost, which is *all* one-time cost for a
    velocity-solved run (frame one is the only frame that builds and
    caches `PISO`'s own Poisson matrix; every later frame reuses it,
    ADR-012). `time_one_run(config_path, frames)` minus that gives the
    total cost of the remaining `frames - 1` frames, all steady-state;
    dividing by `frames - 1` gives the marginal per-frame cost. Requires
    `frames > 1` -- there is no "remaining frames" to divide by
    otherwise, and a caller asking to split a single frame into
    "startup" and "the rest" is asking a question with no answer.
    """
    if frames <= 1:
        raise ValueError(f"time_phases needs frames > 1 to compute a per-frame cost, got {frames}")
    startup = time_one_run(config_path, frames=1)
    total = time_one_run(config_path, frames=frames)
    return PhaseTiming(startup=startup, steady_per_frame=(total - startup) / (frames - 1))


def run_phase_benchmark(
    configs: list[Path], frames: int, repeats: int
) -> dict[Path, list[PhaseTiming]]:
    """`run_benchmark`'s phase-split counterpart: `repeats` independent
    `PhaseTiming`s per config, each from its own fresh pair of subprocess
    runs (`time_phases`) rather than reusing one `startup` measurement
    across several `steady_per_frame` ones -- an independent pair per
    repeat is what lets `format_phase_report` report `stdev`/`max` for
    `startup` and `steady_per_frame` separately, each from a genuinely
    repeated measurement rather than a single shared one.
    """
    return {
        config_path: [time_phases(config_path, frames) for _ in range(repeats)]
        for config_path in configs
    }


def format_phase_report(results: dict[Path, list[PhaseTiming]], frames: int, repeats: int) -> str:
    lines = [
        f"PyFlow demo benchmark, phase-split -- startup (1 frame, includes "
        f"PISO's one-time cached Poisson-matrix build if this config solves "
        f"velocity) vs steady per-frame cost (frames 2..{frames}, matrix "
        f"already cached), best/mean/stdev of {repeats} repeat(s), offscreen backend",
        "",
        f"{'config':<45} {'startup min':>11} {'mean':>7} {'stdev':>7}"
        f"{'  per-frame min':>16} {'mean':>8} {'stdev':>8}",
        "-" * 104,
    ]
    for config_path, timings in results.items():
        startups = [t.startup for t in timings]
        per_frames = [t.steady_per_frame for t in timings]
        lines.append(
            f"{str(config_path):<45} {min(startups):>11.3f} {statistics.mean(startups):>7.3f} "
            f"{statistics.pstdev(startups):>7.3f}  {min(per_frames):>14.4f} "
            f"{statistics.mean(per_frames):>8.4f} {statistics.pstdev(per_frames):>8.4f}"
        )
    return "\n".join(lines)


def phase_totals(timings: list[PhaseTiming], frames: int) -> list[float]:
    """Per-repeat total run time (`startup + (frames - 1) * steady_per_frame`),
    re-derived rather than re-measured -- `time_phases` already paid for
    both halves of this sum in one pair of subprocess runs, so recovering
    the plain total this way costs nothing further. Computed per repeat,
    not by combining `min(startups)` with `min(per_frames))` -- those two
    minima can come from different repeats, which would report a total
    that no single run actually produced.
    """
    return [timing.startup + (frames - 1) * timing.steady_per_frame for timing in timings]


@dataclasses.dataclass(frozen=True)
class BenchmarkRecord:
    """One row of `benchmark_history.jsonl`: a single config's own
    phase-split result from one `--record` invocation, plus the context
    (`pyflow` version, git commit, hostname, when) needed to make that
    row comparable -- or knowably *not* comparable -- to another one
    recorded later. `min`/`mean`/`stdev` for each of `startup`,
    `per_frame`, and the re-derived `total` (`phase_totals` above), the
    same three statistics `format_report`/`format_phase_report` already
    show, so the permanent record carries no less information than the
    report a reader saw when it was made.
    """

    timestamp: str
    pyflow_version: str
    git_commit: str
    hostname: str
    config: str
    frames: int
    repeats: int
    startup_min_s: float
    startup_mean_s: float
    startup_stdev_s: float
    per_frame_min_s: float
    per_frame_mean_s: float
    per_frame_stdev_s: float
    total_min_s: float
    total_mean_s: float
    total_stdev_s: float


def _git_commit(root: Path) -> str:
    """The short commit hash `HEAD` resolves to in `root` -- part of a
    record's own context, since a performance number is only meaningful
    alongside *what was running* when it was measured.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _pyflow_version() -> str:
    """Imported lazily (not at module scope) so importing this script for
    its report-formatting/argument-parsing alone -- what every test not
    exercising `--record` does -- never pays for importing `pyflow`
    itself, `torch` included.
    """
    from pyflow import __version__

    return __version__


def _display_path(path: Path) -> str:
    """`path` relative to `REPO_ROOT` when it lives there (every config
    in `DEFAULT_CONFIGS` does, since they're built as `REPO_ROOT / ...`)
    -- a committed history file recording someone's local absolute
    checkout path (`C:\\Users\\...\\PyFlow\\examples\\...`) would be both
    ugly and non-portable to any other clone. Falls back to `path`
    unchanged when it isn't under `REPO_ROOT` (a test's own `tmp_path`
    fixture config, most likely), where there is no repo-relative form
    to give.
    """
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def build_records(
    phase_results: dict[Path, list[PhaseTiming]],
    frames: int,
    repeats: int,
    *,
    timestamp: str,
    pyflow_version: str,
    git_commit: str,
    hostname: str,
) -> list[BenchmarkRecord]:
    """One `BenchmarkRecord` per config in `phase_results`, sharing the
    context arguments (all as of the one `--record` invocation that
    produced every config's own results together). Context is threaded
    in rather than computed here so `main` fetches it once per
    invocation, not once per config, and so tests can supply fixed
    values instead of a real git repo/clock/hostname.
    """
    records = []
    for config_path, timings in phase_results.items():
        startups = [timing.startup for timing in timings]
        per_frames = [timing.steady_per_frame for timing in timings]
        totals = phase_totals(timings, frames)
        records.append(
            BenchmarkRecord(
                timestamp=timestamp,
                pyflow_version=pyflow_version,
                git_commit=git_commit,
                hostname=hostname,
                config=_display_path(config_path),
                frames=frames,
                repeats=repeats,
                startup_min_s=min(startups),
                startup_mean_s=statistics.mean(startups),
                startup_stdev_s=statistics.pstdev(startups),
                per_frame_min_s=min(per_frames),
                per_frame_mean_s=statistics.mean(per_frames),
                per_frame_stdev_s=statistics.pstdev(per_frames),
                total_min_s=min(totals),
                total_mean_s=statistics.mean(totals),
                total_stdev_s=statistics.pstdev(totals),
            )
        )
    return records


def append_history(records: list[BenchmarkRecord], history_path: Path) -> None:
    """Appends one JSON object per line to `history_path` -- JSON Lines,
    not a JSON array or a growing YAML document, specifically because it
    is append-only-safe: adding a record never requires reading, parsing,
    or rewriting anything already there, so a history spanning years of
    runs stays a cheap `open(..., "a")` regardless of how large it gets.
    Creates the file (and never truncates an existing one) since this is
    the one and only writer a real history is ever supposed to have.
    """
    with history_path.open("a", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(dataclasses.asdict(record), sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark PyFlow's end-to-end demo runtime via a real 'pyflow run' "
            "subprocess per repeat -- reports the minimum wall-clock time across "
            "repeated runs for each configuration. Run in isolation (nothing "
            "else CPU-heavy) for a clean number."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        action="append",
        dest="configs",
        default=None,
        help="A config file to benchmark (repeatable). Default: the "
        "benchmark suite (DEFAULT_CONFIGS), grown as new configs earn a "
        "benchmark -- see tools/benchmarks/CLAUDE.md.",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=DEFAULT_FRAMES,
        help=f"Frames per run (default: {DEFAULT_FRAMES}).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=DEFAULT_REPEATS,
        help=f"Repeats per config; the minimum is reported (default: {DEFAULT_REPEATS}).",
    )
    parser.add_argument(
        "--phases",
        action="store_true",
        help="Split each config's own runtime into startup (1 frame, "
        "includes any one-time cost such as PISO's cached Poisson-matrix "
        "build) and steady per-frame cost, via two subprocess runs per "
        "repeat instead of one -- see time_phases' own docstring. "
        "Requires --frames > 1.",
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Append each config's own result to benchmark_history.jsonl "
        "(git commit, pyflow version, hostname, timestamp, and the same "
        "phase-split statistics --phases prints) for long-term "
        "comparison -- see BenchmarkRecord's own docstring. Always "
        "measures phase-split internally, regardless of --phases, since "
        "the recorded entry stores both; --phases only changes what is "
        "printed to stdout, not what is recorded.",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=HISTORY_PATH,
        help=f"Where --record appends to (default: {HISTORY_PATH}). "
        "Overridable mainly so tests don't write into the real history.",
    )
    args = parser.parse_args(argv)

    configs: list[Path] = args.configs if args.configs is not None else list(DEFAULT_CONFIGS)

    if args.record or args.phases:
        phase_results = run_phase_benchmark(configs, args.frames, args.repeats)
        if args.record:
            records = build_records(
                phase_results,
                args.frames,
                args.repeats,
                timestamp=datetime.now(UTC).isoformat(),
                pyflow_version=_pyflow_version(),
                git_commit=_git_commit(REPO_ROOT),
                hostname=platform.node(),
            )
            append_history(records, args.history_file)
            print(f"Appended {len(records)} record(s) to {args.history_file}")
        if args.phases:
            print(format_phase_report(phase_results, args.frames, args.repeats))
        else:
            totals = {
                config_path: phase_totals(timings, args.frames)
                for config_path, timings in phase_results.items()
            }
            print(format_report(totals, args.frames, args.repeats))
    else:
        results = run_benchmark(configs, args.frames, args.repeats)
        print(format_report(results, args.frames, args.repeats))


if __name__ == "__main__":
    main()
