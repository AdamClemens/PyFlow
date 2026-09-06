# CLAUDE

`benchmark_demos.py` (added 2026-09-06) -- times a real `bootstrap()`
demo run end to end, headlessly, repeated a few times, reporting the
minimum. Built at the end of this session's own seven-fix vectorization
arc (`docs/planning/roadmap.md` TASK-022/026/040/024/023/027 x2,
`examples/experiments/CLAUDE.md`), whose every measured before/after
number up to that point came from an ad hoc, hand-typed timing script
rewritten from scratch each time -- one of those runs was contaminated
by a concurrent `make ci` run and had to be caught and re-measured by
hand. This is that measurement, made repeatable and left behind instead
of thrown away once the number was copied into a document.

Run via `make benchmark` (`uv run python tools/benchmarks/
benchmark_demos.py`), never invoked ad hoc, the same convention
`generators/`/`validators/` already establish (`tools/CLAUDE.md`).
Deliberately **not** wired into `make ci` and has no `--check` mode --
like `tools/generators/generate_graph_view.py`, a performance number is
not a structural fact to gate on and there is no committed file for a
`--check` to compare against. See the script's own module docstring for
the full reasoning, including why it only ever times the public
`bootstrap()` API rather than an isolated internal call.

`tests/unit/test_benchmark_demos.py` covers it the same way
`tests/unit/test_generate_status_report.py` covers `tools/generators/
generate_status_report.py` -- imported via `sys.path`, not as a
`pyflow` subpackage, since this is a repo-support script rather than
library code (mirrored in `pyproject.toml`'s `[tool.mypy] mypy_path`,
which needs an entry for the same reason `tools/validators`/
`tools/generators` already have one). What it tests is the mechanism
(argument parsing, the report's shape, that repeated runs each produce
a positive duration, that the default configs are real files) -- never
a specific timing number, which is exactly what this tool exists to
measure rather than assert.

**`DEFAULT_FRAMES` raised 5 -> 50, 2026-09-06, at the maintainer's
request for a 32x64x128 mesh-scaling comparison.** 5 frames spends a
disproportionate share of total time on frame one's own one-time cost
(`PISO`'s cached Poisson-matrix build) rather than the steady per-step
cost a real run mostly consists of -- see `time_phases` immediately
below for the mechanism that made this visible rather than assumed.

**`time_phases`/`PhaseTiming`/`run_phase_benchmark`/`format_phase_report`
(`--phases`, added 2026-09-06) split a config's own runtime into
`startup` and `steady_per_frame`, still via two real subprocess runs
(`--max-frames 1` and `--max-frames N`), not by adding timing
instrumentation inside `bootstrap.py`.** That restraint is deliberate,
not an oversight: this module's own opening docstring already commits
to timing only the public API, and `bootstrap.py`'s internals reshape
with every performance fix (`examples/experiments/CLAUDE.md`'s own
eight-fix history) while `pyflow run --max-frames N` does not.
`startup = time_one_run(frames=1)`; `steady_per_frame = (time_one_run
(frames=N) - startup) / (N - 1)` -- valid because frame one is the
*only* frame that builds and caches `PISO`'s own Poisson matrix for a
velocity-solved run (ADR-012), so every one-time cost is concentrated
there and every later frame is genuinely steady-state. Requires
`frames > 1`, checked with a real `ValueError`, not an assertion --
"split one frame into startup and the rest" has no answer. Doubles the
subprocess count per repeat (one extra `--max-frames 1` run), so
`--phases` stays opt-in rather than replacing the plain report as
`make benchmark`'s own default.

**`format_report` gained `stdev`/`max` columns the same day, prompted by
a direct question about how consistent repeats actually are.** `min` is
still what every consumer of this report should act on (the "a
contaminated run only ever makes a run slower" reasoning above is
unchanged), but a reader could not previously judge from the report
alone whether 3 repeats was enough to trust that minimum -- `stdev`/
`max` show the spread it was drawn from in the same report, rather than
needing a separate investigation to find out. **That investigation was
run once, directly, rather than left to guesswork**: 8 repeats of
`smoke_transport_mesh64.yaml` at 50 frames landed `[15.499, 16.736,
15.371, 16.737, 15.47, 15.46, 15.361, 16.155]` (stdev ~3.6% of mean,
one apparent bimodal cluster of slower outliers -- consistent with
occasional contamination, never a run reporting faster than the true
cost); the minimum of the first 3 (15.371s) was within 0.06% of the
minimum of all 8 (15.361s). A second check at 128x128, 6 repeats,
found *zero* improvement from repeats 4-6 (stdev ~1.1% of mean).
**3 repeats is earning its keep, not a cargo-culted number**: it already
finds the same practical minimum more repeats do, at roughly a third the
cost -- see `examples/experiments/CLAUDE.md`'s own mesh-scaling entry
for the full comparison this was measured alongside.

A third subdirectory of `tools/`, alongside `generators/` (write a file
from repository state) and `validators/` (repository-consistency
checks). This one measures performance instead -- neither writing a
committed artifact nor checking one, which is why it doesn't fit either
existing subdirectory.
