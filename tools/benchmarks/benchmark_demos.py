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
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The two configs this session's own investigation is anchored to
# (`examples/experiments/CLAUDE.md`): the golden demo the investigation
# started from, and the higher-resolution experiment whose slowdown
# triggered it. Resolved against REPO_ROOT so `make benchmark` works from
# the repository root regardless of Makefile invocation details, the same
# convention `tools/generators/generate_status_report.py` uses.
DEFAULT_CONFIGS: tuple[Path, ...] = (
    REPO_ROOT / "examples" / "golden-demos" / "smoke_transport.yaml",
    REPO_ROOT / "examples" / "experiments" / "smoke_transport_high_res.yaml",
)

DEFAULT_FRAMES = 5
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
    lines = [
        f"PyFlow demo benchmark -- {frames} frame(s) per run, "
        f"best of {repeats} repeat(s), offscreen backend",
        "",
        f"{'config':<60} {'min (s)':>10} {'mean (s)':>10}",
        "-" * 82,
    ]
    for config_path, timings in results.items():
        lines.append(
            f"{str(config_path):<60} {min(timings):>10.3f} {statistics.mean(timings):>10.3f}"
        )
    return "\n".join(lines)


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
        help="A config file to benchmark (repeatable). Default: the two "
        "configs this session's own performance investigation used "
        "(examples/golden-demos/smoke_transport.yaml and "
        "examples/experiments/smoke_transport_high_res.yaml).",
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
    args = parser.parse_args(argv)

    configs: list[Path] = args.configs if args.configs is not None else list(DEFAULT_CONFIGS)
    results = run_benchmark(configs, args.frames, args.repeats)
    print(format_report(results, args.frames, args.repeats))


if __name__ == "__main__":
    main()
