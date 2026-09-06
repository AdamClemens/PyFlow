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

A third subdirectory of `tools/`, alongside `generators/` (write a file
from repository state) and `validators/` (repository-consistency
checks). This one measures performance instead -- neither writing a
committed artifact nor checking one, which is why it doesn't fit either
existing subdirectory.
