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
  **This demo's own five-frame runtime was ~6.85s** after the seventh
  fix, against a 16x16 baseline of ~5.1s (down from ~11.6s) -- an 11.2x
  total improvement from the original ~77s; the ~10x-for-4x-cells gap
  was down to ~1.33x. That was reported as the investigation's end
  ("nothing remains unattempted") at the time.

  **Every one of the numbers above came from an ad hoc, hand-typed timing
  script, rewritten from scratch for each fix and thrown away once the
  number was copied in here** -- one of those runs was contaminated by a
  concurrent `make ci` and had to be caught and re-measured by hand.
  `tools/benchmarks/benchmark_demos.py` (`make benchmark`, added
  2026-09-06) is that measurement made repeatable: it runs this demo (and
  the 16x16 original) through a real `pyflow run` subprocess, several
  times, and reports the fastest. A fresh run through it just after
  landing reproduced this row's own then-current numbers (min 6.640s
  here against the ~6.85s recorded above, min 5.620s for the 16x16
  baseline against the ~5.1s recorded above -- both within ordinary
  run-to-run noise on one machine, not a regression). See the tool's own
  docstring for why it shells out to a real subprocess rather than
  calling `bootstrap()` in-process -- an earlier version did the latter
  and was caught reporting 4-10x too fast by exactly this comparison.

  **"Nothing remains unattempted" turned out to be wrong, found by
  continuing to look rather than by a further idea.** Profiling this
  same demo again found an eighth: `PISO._poisson_matrix`'s own probe
  loop, unchanged by any of the seven fixes above since each of them
  made a *single* `flux`/`accumulate_flux_to_cells` call faster, not how
  many times the matrix build called them. **`_poisson_matrix` rebuilt
  directly per face, not probed per cell, eighth and last**
  (`pressure_coupling.py`, `adr/ADR-012-direct-poisson-matrix-
  construction.md`, TASK-026's own second revisit) -- this was ADR-011's
  own explicitly deferred Alternative, not a fresh discovery; adopted
  once its real cost was measured rather than assumed amortised away,
  exactly as that ADR's own closing line asked. The build itself: ~52s
  to ~0.012s at 1024 cells (~4200x, now linear in cell count rather than
  quadratic). **This demo's own five-frame runtime is now ~5.46s at
  32x32** (reproduced via `make benchmark`, not another ad hoc script),
  within ordinary run-to-run noise of the 16x16 baseline -- the original
  ~10x-for-4x-cells gap is effectively closed. Full record of all eight,
  in landing order: `docs/planning/roadmap.md`'s TASK-022/026 (sparse
  solver), TASK-040 (`accumulate_flux_to_cells`), TASK-024
  (`CentralDifferenceDiffusion`), TASK-023 (`FirstOrderUpwindAdvection`),
  TASK-027's two entries (`GreenGaussGradient`/`GreenGaussDivergence`,
  then `PISO._rhie_chow_divergence`), and TASK-026's own second revisit
  (`_poisson_matrix`). Nothing from this investigation remains
  unattempted -- said once before and found wrong by continuing to look,
  so this time backed by a profile of the actual current code (every
  pyflow-owned function summed to ~0.86s of an 8.16s profiled run, the
  rest third-party import/startup overhead this repository does not
  control), not by the absence of a further idea.

- `smoke_transport_re1000.yaml` (2026-09-06) -- `smoke_transport.yaml`
  at 4x linear resolution (16x16 -> 64x64 cells, same 1x1 domain) *and*
  Re = 100 -> 1000 (viscosity 0.01 -> 0.001, lid velocity and domain
  unchanged), raised together on purpose: mesh alone would just get
  smoothed by first-order upwind's own numerical diffusion, and Re alone
  without matching resolution makes that diffusion dominate even more
  (`docs/planning/roadmap.md`'s own warning that upwind "can suppress
  Kelvin-Helmholtz roll-up entirely at coarse resolution"). Built to
  answer a direct question about whether the two golden-demo-adjacent
  smoke configs (this one's own 16x16 and 32x32) are too coarse to show
  more than the single dominant primary vortex -- Ghia, Ghia & Shin
  (1982) resolve well-defined secondary corner vortices by Re = 1000 at
  comparable or coarser resolution, so 64x64 is a reasonable first mesh
  to try rather than a guess at the edge of affordability. Timestep
  (0.002) is hand-derived, not copied: CFL = 0.128, identical to both
  existing smoke configs (`time-integration.md`); the viscosity's own
  diffusive limit is relaxed by the lower viscosity (~3.3% of its limit
  used); the smoke field's own diffusive limit (diffusion_coefficient
  unchanged at 0.01) is the tightest constraint at ~32.8% of its limit
  (`diffusion.md`'s `dt <= dx^2 / (4 * diffusivity)`) -- still well
  inside it, but worth naming since it is the constraint that would bind
  first if this config's resolution or Re were pushed further.

  **Benchmarked against the 16x16 baseline via `tools/benchmarks/
  benchmark_demos.py` the same day, in isolation, 5 frames/3 repeats:**
  16x16 min 4.936s (mean 5.667s) against this file's 64x64-at-Re-1000
  min 6.565s (mean 7.037s) -- roughly 1.33x for 16x the cell count, one
  measurement on one machine. Consistent with the `smoke_transport_
  high_res.yaml` entry above's own closing finding that ADR-012's direct
  Poisson matrix construction closed the earlier ~10x-for-4x-cells gap:
  cost here no longer scales anywhere near cell count, so a further
  resolution bump is unlikely to be gated by runtime the way it used to
  be. Not promoted to `examples/golden-demos/` -- no roadmap task names
  what this demonstrates, and changing the golden demo's own validated
  Re = 100 shape would need its own justification; whether it actually
  shows a visible secondary vortex (as opposed to only being affordable
  and stable) has not yet been checked by eye or measured against Ghia's
  own Re = 1000 profiles -- that is the open question this file leaves
  for whoever picks it up next, not a settled result.
