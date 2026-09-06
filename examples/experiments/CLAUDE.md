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
  vectorised fifth and sixth** (`gradient.py`/`divergence.py`,
  TASK-027's own first revisit) -- called once per PISO corrector pass;
  this demo's own runtime dropped to ~7.1s, a modest gain here
  specifically (this demo converges in few corrector passes), but the
  full `tests/unit/`+`tests/golden/` suite (many more corrector passes
  overall, the Ghia cavity comparison especially) dropped from under 5
  minutes to ~3.5. **`PISO._rhie_chow_divergence` vectorised seventh and
  last** (`pressure_coupling.py`, TASK-027's own second revisit) --
  wrongly assumed unfixable by the same approach when the sixth fix
  landed (it computes a face-valued array feeding `accumulate_flux_to_
  cells` too, the identical shape, found by actually reading the method
  rather than trusting that assumption), and simpler than every prior
  fix once corrected: no `BoundaryCondition` is ever consulted in this
  method, so no scalar boundary loop is needed at all, only a mask.
  **This demo's own five-frame runtime is now ~6.85s**, against a 16x16
  baseline of ~5.1s (down from ~11.6s) -- an 11.2x total improvement
  from the original ~77s; the original ~10x-for-4x-cells gap is now
  ~1.33x. Full record of all seven, in landing order:
  `docs/planning/roadmap.md`'s TASK-022/026 (sparse solver), TASK-040
  (`accumulate_flux_to_cells`), TASK-024 (`CentralDifferenceDiffusion`),
  TASK-023 (`FirstOrderUpwindAdvection`), and TASK-027's two entries
  (`GreenGaussGradient`/`GreenGaussDivergence`, then
  `PISO._rhie_chow_divergence`). Nothing from this investigation remains
  unattempted.

  **Every one of the numbers above came from an ad hoc, hand-typed timing
  script, rewritten from scratch for each fix and thrown away once the
  number was copied in here** -- one of those runs was contaminated by a
  concurrent `make ci` and had to be caught and re-measured by hand.
  `tools/benchmarks/benchmark_demos.py` (`make benchmark`, added
  2026-09-06) is that measurement made repeatable: it runs this demo (and
  the 16x16 original) through a real `pyflow run` subprocess, several
  times, and reports the fastest. A fresh run through it just after
  landing reproduced this row's own numbers (min 6.640s here against the
  ~6.85s recorded above, min 5.620s for the 16x16 baseline against the
  ~5.1s recorded above -- both within ordinary run-to-run noise on one
  machine, not a regression). See the tool's own docstring for why it
  shells out to a real subprocess rather than calling `bootstrap()`
  in-process -- an earlier version did the latter and was caught
  reporting 4-10x too fast by exactly this comparison.
