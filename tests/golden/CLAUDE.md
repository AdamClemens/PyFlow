# CLAUDE

Regression tests for the golden demos specified in
`docs/implementation/golden-demos.md` -- one test module per demo.

**Every demo's test module must include at least one test that runs it
through the real public CLI, as a subprocess** (maintainer's rule,
2026-08-16): `python -m pyflow run --config
examples/golden-demos/<name>.yaml --backend offscreen --max-frames N`.
That's the literal command a user would type (`--backend offscreen`
aside, the one sanctioned override for headless CI); a test that only
exercises some internal shortcut isn't verifying what the rule actually
requires -- that a demo is genuinely reproducible by a user, not just by
this test suite.

**Since 2026-08-22 these are BDD modules, and the criteria are not
here.** Each demo's acceptance criteria live in
`tests/features/<demo>.feature`
(`adr/ADR-007-executable-acceptance-criteria.md`); a module in this
directory binds them with `scenarios(...)` and supplies only the steps
that no other demo could use. The demo-independent vocabulary -- run the
demo through the CLI, render a frame offscreen, compare two frames --
is in `conftest.py`, and `_demo.py` holds the machinery behind it.

The subprocess rule above is unchanged and is now expressed as a
scenario every demo carries ("A user can run it with the documented
command"), rather than as a convention each module had to remember.

**That scenario asserts a clean exit and nothing more, so a demo whose
output is its point needs a second one.** `numerics_assembly` is the
worked example: Stage 3 renders nothing new, so the CLI's report *is*
the demonstration, and the Stage 3 exit audit found the report was only
ever checked in-process -- deleting the log line entirely left every
test passing. It now carries "The run reports the assembled set through
the real CLI", which reads the report back out of the subprocess's
stderr. Ask of any new demo whether exit-code-zero really covers what
it claims to show.

**When adding a demo:** write the feature file first, bind it from a
module here, and add a step only when the shared vocabulary genuinely
cannot express the criterion -- not to make a scenario easier to write.
`make check-scenarios` fails if a feature file exists that nothing
binds, which is the one failure pytest itself is silent about.

`test_empty_window.py` (D5, 2026-08-16) was the first example, and its
original three-test shape is what the three scenarios in
`empty_window.feature` now say:
- `test_empty_window_runs_via_the_public_cli` is that required subprocess
  test.
- `test_empty_window_renders_configured_background` and
  `test_empty_window_is_deterministic` go deeper, via
  `pyflow.bootstrap.bootstrap()` called directly -- still the public API
  (the Python entry point rather than the CLI one), used here only
  because it's the only way to get the rendered frame back
  (`RenderWindow.last_image`) for pixel inspection. Asserts the demo's
  configured background colour renders as an exact, deterministic pixel
  match, not just that nothing raised -- "verifies meaningful behaviour"
  is the Definition of Done's own phrase for this.

There is no demo-specific Python module to load any more (no
`importlib.util.spec_from_file_location` trick, which the first version
of this test needed): golden demos are plain config files under
`examples/golden-demos/`, not scripts, per the public-API rule in
`docs/implementation/golden-demos.md`.

**`test_passive_scalar_transport.py` (TASK-030, added 2026-08-28) is the
fifth demo module, and PyFlow's first that computes real physics** --
Stage 4 Completion Criterion 1's own golden demo, the first `pyflow run`
that steps a real simulation forward live rather than rendering one
static frame. Binds `tests/features/passive_scalar_transport.feature`:
the required CLI-subprocess scenario every demo carries, plus one
demo-specific step (`conftest.py`'s shared vocabulary only knows how to
render exactly one or two frames, not step a live simulation forward by
a specific count and read its own field state back) that bootstraps the
demo twice, at two different frame counts, and reads
`RenderWindow.simulation_fields` back from each -- a genuine physical
claim (the transported field's own mass-weighted centroid moves
downstream at approximately the prescribed velocity over real elapsed
time), not only a pixel-diff. **The tolerance (`rel=0.15`) was measured
from a real run, not guessed** -- a real run agrees with the closed-form
prediction to within ~4%; confirmed to actually fail under a mutation
that froze the simulation state every frame (never calling
`simulation.step`) before being trusted.

**`test_heat_diffusion.py` (TASK-034, added 2026-08-29) is the sixth
demo module** -- Stage 5's own reconciliation of `mvp.md`'s Validation
section: heat diffusion as the diffusion equation on a transported
scalar, no named Temperature field needed. Same shape as
`test_passive_scalar_transport.py`'s own join: the required
CLI-subprocess scenario, plus one demo-specific step (bootstraps twice,
at two frame counts, measures the transported field's own RMS amplitude
at each) proving a genuine physical claim -- a single sinusoidal mode's
own amplitude decays at the exact rate `Gamma * wavenumber**2` predicts,
not only that the field changed. **The tolerance (`rel=0.1`) was
measured from a real run** -- a real run agrees with the closed-form
rate to within ~0.6%.

**`test_lid_driven_cavity.py` (TASK-034, added 2026-08-29) is the
seventh demo module** -- the MVP's own golden demo
(`docs/implementation/mvp.md`, `docs/implementation/golden-demos.md`'s
"Lid-Driven Cavity" section), and the first velocity field PyFlow has
ever rendered that was *solved*, not prescribed or seeded. Reads
`RenderWindow.simulation_fields` back the same way
`test_passive_scalar_transport.py` does, reassembling velocity's own two
decomposed components via `VectorField.assemble` since this demo has no
scalar to read at all. **Deliberately does not assert an absolute
divergence bound** -- tried first, and found to fail even at cells well
away from the lid's own two corner singularities, because
`GreenGaussDivergence`'s own naive face-averaged divergence is not the
Rhie-Chow-consistent measure `PISO`'s own corrector loop actually drives
to tolerance (`src/pyflow/engine/numerics/pressure_coupling.py`'s own
`_rhie_chow_divergence` docstring). The real, tolerance-gated divergence
claim is `tests/features/navier_stokes_timestep.feature`'s own scenarios,
measured the way `PISO` itself measures; this module's own two physical
checks are lighter (genuine nonzero motion away from the lid,
determinism) -- see this module's own docstring for the full finding.
