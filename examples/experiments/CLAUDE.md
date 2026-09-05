# CLAUDE

Working configs that don't (yet, or ever) meet
`examples/golden-demos/CLAUDE.md`'s bar for a golden demo -- no roadmap
task backing them, no `tests/golden/` coverage, not curated in
`pyflow run --demos`. Still real `PyFlowConfig` YAML, run the same way:
`uv run python -m pyflow run --config examples/experiments/<name>.yaml`.

- `smoke_transport_high_res.yaml` (2026-09-04) -- `smoke_transport.yaml`
  at 2x linear resolution (16x16 -> 32x32 cells, same domain), timestep
  halved to match so the CFL and diffusive stability margins are
  unchanged from the original. Left here rather than promoted because
  the cost is real and unmeasured-until-now: 5 rendered frames took
  ~10x as long as the original (offscreen backend, one measurement on
  one machine -- see the file's own comment), steeper than the ~5x
  `thermal_buoyancy.yaml` saw for a similarly-sized cell increase.
  Promote it to `examples/golden-demos/` only behind a roadmap task that
  says what the extra resolution demonstrates that the original doesn't
  -- per that directory's own rule, a demo needs a reason beyond "higher
  resolution."

  **This measurement is what triggered `adr/ADR-011-sparse-linear-
  solver-matrix.md` (2026-09-05)** -- investigated, not fixed here:
  `PISO`'s dense Conjugate Gradient solve turned out to genuinely
  benefit from a sparse representation (2.56x faster at 1024 cells,
  verified in isolation), but this demo's own ~10x slowdown is
  dominated by `PISO._poisson_matrix`'s build cost, which that decision
  left unchanged (three orders of magnitude larger than the solve at
  this mesh size, measured directly). Re-running this demo after that
  fix shows no visible improvement, honestly -- the build, not the
  solve, is what a five-frame run actually pays for.
