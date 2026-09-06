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

  **This measurement is what triggered three fixes, tracked here as
  each landed rather than only at the end.** `adr/ADR-011-sparse-
  linear-solver-matrix.md` (2026-09-05): `PISO`'s dense Conjugate
  Gradient solve turned out to genuinely benefit from a sparse
  representation (2.56x faster at 1024 cells, verified in isolation),
  but this demo's own ~10x slowdown was dominated by
  `PISO._poisson_matrix`'s build cost, which that decision left
  unchanged -- re-running this demo after that fix alone showed no
  visible improvement, honestly reported as such at the time.
  **`accumulate_flux_to_cells` (`simulation.py`) vectorised next**,
  found while chasing a narrower fix -- since the Poisson matrix build
  itself calls that function once per column, the build dropped from
  ~52s to ~34s at 1024 cells, and this demo's own five-frame runtime
  from ~77s to ~45s. **`CentralDifferenceDiffusion.flux` vectorised
  third** (`diffusion.py`, TASK-024's own revisit) -- also called once
  per column inside the same build, which dropped again, to ~2.5s at
  1024 cells; this demo's own runtime dropped to ~12.6s. **`FirstOrder
  UpwindAdvection.flux` vectorised fourth** (`advection.py`, TASK-023's
  own revisit) -- called every RK4 stage for every transported field,
  including momentum; this demo's own runtime dropped to ~7.4s.
  **`GreenGaussGradient.gradient`/`GreenGaussDivergence.divergence`
  vectorised fifth and sixth, last** (`gradient.py`/`divergence.py`,
  TASK-027's own revisit) -- called once per PISO corrector pass; **this
  demo's own five-frame runtime is now ~7.1s**, against a 16x16 baseline
  of ~5.0s (down from ~11.6s) -- a modest further gain here specifically
  (this demo converges in few corrector passes), but the full
  `tests/unit/`+`tests/golden/` suite (many more corrector passes
  overall, the Ghia cavity comparison especially) dropped from under 5
  minutes to ~3.5. A 10.9x total improvement on this demo from the
  original ~77s; the original ~10x-for-4x-cells gap is now ~1.42x. Full
  record of all six, in landing order: `docs/planning/roadmap.md`'s
  TASK-022/026 (sparse solver), TASK-040 (`accumulate_flux_to_cells`),
  TASK-024 (`CentralDifferenceDiffusion`), TASK-023
  (`FirstOrderUpwindAdvection`), and TASK-027 (`GreenGaussGradient`/
  `GreenGaussDivergence`) entries. `PISO._rhie_chow_divergence` is the
  one per-face loop from this investigation that remains -- it computes
  a genuinely new quantity each call, not an intermediate array feeding
  `accumulate_flux_to_cells` the same way the other five did.
