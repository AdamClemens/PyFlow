# CLAUDE

Four subpackages, each with its own `CLAUDE.md`: `configuration/`,
`engine/`, `physics/`, `rendering/` -- per `docs/planning/roadmap.md`
TASK-000. Top-level modules alongside them: `__main__.py` (the CLI entry
point, `python -m pyflow`), `bootstrap.py`, and -- all landed 2026-09-07,
Stage 8 (Recording & Playback) -- `simulation_run.py`, `checkpoint.py`,
`recording.py` (TASK-045), `replay.py` (TASK-046), `playback.py`
(TASK-047) (see below). A fifth subpackage, `engine/numerics/`, landed
in Stage 3 -- see below.

**`bootstrap.py` lives here, at the package root, not inside `engine/`,
deliberately.** It composes `configuration`, `engine` (for logging) and
`rendering` together to implement TASK-010 -- load config, initialise
logging, open the window, run the loop. Putting it inside `engine/`
first (TASK-010's name suggests "engine bootstrap") created a genuine
circular import: `engine` needing `rendering`, while `rendering.window`
needs `engine.logging_setup` for its own logger. Whichever package a
program imports first would find the other only partially initialised.
Caught 2026-08-16 (D4) by actually running the import, not by
inspection -- see `docs/CHANGELOG-DESIGN.md`.

**The standing rule this leaves behind:** a module that orchestrates two
or more of these subpackages belongs at the `pyflow` package root, not
inside whichever subpackage its task name happens to suggest. A
subpackage's own code should only need its siblings' *leaf* modules
(e.g. `rendering.window` needing `engine.logging_setup`), never a
sibling's top-level orchestration -- that's what turns "A depends on B"
into "A depends on B depends on A."

**`bootstrap()` is PyFlow's public API, not an implementation detail
behind `pyflow run`** (made explicit 2026-08-16, D5, when golden demos
were required to run through the public API only -- see
`docs/implementation/golden-demos.md`). It returns the `RenderWindow` it
built and ran (previously returned `None`), and takes a `backend`
keyword that overrides whatever `config_path` specifies for
`rendering.backend` -- the mechanism that lets one config file be both
"the interactive demo" (default) and "the headless regression-tested
version" (`backend="offscreen"`) without needing two files. Both
`pyflow run`'s `--backend` flag and any test calling `bootstrap()`
directly go through the same override, so they can never drift apart.

**A fifth subpackage arrived in Stage 3: `engine/numerics/`** (decided
2026-08-22 when Stage 3's tasks were drafted, built 2026-08-23 across
TASK-018..022 -- `docs/planning/roadmap.md` TASK-018's design
decisions). It holds the six
configuration-selected numerical strategies
`adr/ADR-003-modular-numerical-strategies.md` names -- advection,
diffusion, time integration, pressure-velocity coupling, linear solver,
boundary condition -- plus the gradient/divergence/source operators that
are interfaces but not user-selected, and the assembly registry that
builds them from a `numerics` configuration section.

It is a *sub*-package of `engine/`, not a fifth top-level one, because
these are engine layers (`docs/architecture/engine.md`'s nine) and
`engine/` would otherwise hold eleven flat modules. **It is deliberately
not `physics/`**: `physics/` is reserved for phenomena -- temperature,
buoyancy, species (Stage 6, TASK-035..038) -- and a numerical scheme is
machinery, not a phenomenon. Keep that line; the moment a discretisation
lands in `physics/` or a phenomenon in `numerics/`, the distinction stops
paying for itself.

**The CLI's own help text (`__main__.py`'s top-level `description`/
`epilog`, plus `run_parser`'s own `epilog`) must be kept current with
what PyFlow can actually do** (rule added 2026-08-28, prompted by a user
noticing it wasn't: the top-level `description` still read "Stage 0
skeleton -- no simulation functionality yet" through the entirety of
Stage 4 (TASK-023 through TASK-030, 2026-08-27..28) landing real
numerics, PISO, and a live-stepping golden demo -- stale from the first
of those, not from some distant point; PyFlow moves fast enough that a
day of silence is enough for this text to go wrong, so "recently" is not
a reason to skip re-reading it. Neither `--config` nor how to run a
golden demo was mentioned anywhere the bare-invocation or top-level
`--help` output would show them --
argparse only surfaces a subcommand's own flags under that subcommand's
own `--help`, so `run_parser`'s `--config` help text was never enough on
its own). Concretely: whenever a subcommand or flag is added, removed,
or renamed, or a new golden demo lands under `examples/golden-demos/`,
re-read `__main__.py`'s `description`/`epilog` text in the same change
and update it if it no longer matches -- this is the Blast Radius rule
applied to the CLI's own self-description, not a separate obligation.
Phrase the top-level `description` in terms of what the CLI can *do*,
never by roadmap stage number, so a stage exit that changes nothing
about the CLI itself never forces an edit here. **This is enforced by a
test, not only remembered**: `tests/unit/test_main.py`'s
`test_top_level_help_describes_current_capabilities` (mirrored in
`tests/integration/test_cli.py` across the real subprocess boundary)
asserts concrete current content (`--config`, `examples/golden-demos`)
is present and the stale `"Stage 0"` claim is not, rather than only the
structural markers (`usage:`, `-h, --help`) the original C1a test
already checked -- so a forgotten or reverted update fails `make test`
instead of depending on a reviewer noticing.

**The same rule covers `bootstrap.py`'s own module docstring, added
2026-08-28 after the Stage 4 exit audit found it carrying the identical
defect the rule was written for.** That docstring still opened "No
simulation functionality -- Stage 0's job..." while the module twenty
lines below imported `simulation_step` and wired a live per-frame
stepping loop -- the same stale self-description, in the same package,
missed the same morning, because that fix's blast-radius sweep re-read
the diff instead of grepping for the claim. **A module's own docstring
is a self-description exactly as the CLI's help text is**, and every
module at this package root describes what PyFlow *does* rather than
what one task did; re-read them on the same trigger. Unlike the help
text, no test asserts this one's content -- there is no equivalent of
"the user sees this string" to assert against -- so it is covered by
`docs/practices.md`'s "A stage's documentation sweep is a grep, not a
diff review" (its third grep, the negations) instead of by a test.

**`__main__.py`'s second subcommand, `pyflow generate-config [--output
PATH]` (TASK-039, added 2026-08-21)**, does not orchestrate multiple
subpackages the way `bootstrap()` does -- it is a thin argparse wrapper
around `pyflow.configuration.generator.generate_config_yaml`, so it
lives directly in `__main__.py` rather than needing a root-level module
of its own. See `configuration/CLAUDE.md` for what the generator does
and why it reuses `dataclasses.asdict()`.

**Three more root modules, added 2026-09-07 for TASK-045 (Stage 8,
Recording & Playback), and why each sits here rather than inside
`engine/`.**

`simulation_run.py` holds `SimulationState` (a `mode`/`fields`/optional
`velocity_field` triple) and `build_simulation_state`/
`advance_simulation_state`/`assembled_numerics_for` -- the simulation-
state construction and advancement logic `bootstrap.py`'s two rendering
closures (`_add_declared_field_transport`/
`_add_solved_velocity_rendering`) used to fuse together with their own
`window.scene.add(...)` calls. It applies the same standing rule this
file states above for `bootstrap.py` itself: a module that orchestrates
`configuration` and `engine` together belongs at the package root, not
inside whichever subpackage happened to hold the code first. It imports
neither `rendering` nor pulls in `pygfx` transitively (verified live,
not assumed, by checking `sys.modules` after importing it alone) --
that is what lets `recording.py` reuse it for a genuinely headless run.
`bootstrap.py` itself was refactored to call these functions rather than
duplicate them; the refactor was verified behaviour-preserving by the
full existing test suite passing unmodified, not by new tests written to
justify it.

`checkpoint.py` holds the on-disk checkpoint format:
`Checkpoint`/`write_checkpoint`/`read_checkpoint`/
`restore_simulation_state`. One `torch.save`d file per checkpoint,
`weights_only=True`-loadable (the config is embedded as
`dataclasses.asdict(config)`, not a pickled instance -- a pickled
`PyFlowConfig` would force `weights_only=False`, a real code-execution
surface on load). `restore_simulation_state` is the reason this needs
its own module rather than living inside `recording.py`: reconstructing
a resumable `SimulationState` from a checkpoint's raw tensors alone is
insufficient for "passive" mode, whose prescribed `velocity_field` is
never checkpointed (constant by construction, so checkpointing it would
only be a redundant record of `config.simulation.velocity_pattern`) --
it calls `build_simulation_state` again for the right structure, then
overwrites `.fields` with the checkpoint's real values.

**`checkpoint.list_checkpoints(directory)` (TASK-049, Stage 8
reopening, added 2026-09-09) is the one place "what checkpoints exist
here" is answered** -- `CHECKPOINT_FILENAME`, the filename regex, moved
here from being a private copy inside `replay.py`
(`find_checkpoint_at_or_before` now calls this instead), and
`recording.py`'s new retention pruning (below) is its second caller.
This project's own P-011: two callers reading one implementation of a
filename convention rather than two that could drift, the same
reasoning that produced `field_tensors` just above it.

`recording.py` holds `record`/`resume`/`RecordingResult`/
`NothingToRecordError`/`NothingToResumeError`, the functions `pyflow
record`/`pyflow resume` dispatch to. **It never imports `rendering`,
`pygfx`, or `rendercanvas` at all** -- not merely defaults to an
offscreen backend -- which is the structural enforcement of "headless by
default when recording": a `RenderWindow` cannot be constructed without
paying the real cost of building a `wgpu` renderer (`RenderWindow.
__init__`), so a genuinely headless path needs to never reach that
constructor rather than reach it and discard the result.
`tests/integration/test_import_order.py`'s parametrised module list
gained all three modules in the same change, per that test's own
"add to this list whenever a new top-level module or subpackage is
added" instruction.

**`resume`, added the same day at a user's direct request** ("how can a
second run ingest those checkpoints to continue the simulation") **--
still recording's own scope, not replay or playback.** It reads a
checkpoint (`checkpoint.read_checkpoint`), restores a `SimulationState`
from it (`checkpoint.restore_simulation_state`), and continues stepping
headlessly from the checkpoint's own `frame_count`, writing further
checkpoints at the same policy `record` uses -- shared with it through a
new `_advance_and_checkpoint` helper rather than a second copy of the
"every `interval` frames, and at `max_frames`" logic, confirmed to
genuinely share behaviour (not just source) by a deliberate off-by-one
mutation that broke both functions' own tests together. Given a
checkpoint, takes no `--config` at all: the checkpoint already carries
one, validated exactly as strictly as a config file (`checkpoint.py`'s
own docstring). It is not Stage 8's own second or third bullet
(deterministic windowed replay, now TASK-046; a playback path, now
TASK-047, both built the same day) -- neither renders anything or
materializes dense per-frame data for a watched range; `resume` only
ever produces more of the identical sparse checkpoint files `record`
already produces, starting from a later frame.

**`resume`'s own `config_path` parameter, added 2026-09-07 at a further
user request** ("do pyflow resume from a config file and have it start
from the first frame") **-- a second, mutually exclusive way to call
`resume`, not a widening of the checkpoint-only path above.** Pass
exactly one of `checkpoint_path`/`config_path`; given `config_path`,
`resume` is a pure delegation to `record` (`return record(config_path,
...)`), not a second copy of its logic, since there is nothing yet to
resume *from*. Lets a caller use `resume` as the single command name for
a recording's whole lifecycle (`--config` the first time, `--checkpoint
<latest>` every time after) rather than having to branch on whether a
checkpoint exists yet. Does not reopen the "no `--config` at all" design
the paragraph above records: that reasoning was specifically about a
checkpoint and a config being combined in one call, which `__main__.py`'s
own mutually exclusive, required `argparse` group (`--checkpoint`/
`--config`) still makes structurally impossible -- this adds an
alternate entry point, not a way to pass both at once.

**`RecordingConfig.max_checkpoints_retained` (TASK-049, Stage 8
reopening, added 2026-09-09) is an opt-in cap on total checkpoint
count, not another interval.** Criterion 2's own "never one file per
frame" already bounds the gap *between* checkpoints; nothing bounded
the *total* over a very long recording until this. `_prune_checkpoints`
(`recording.py`) runs after every checkpoint `_advance_and_checkpoint`
writes -- keeping disk usage bounded continuously, not only once a run
finishes -- and deletes the oldest checkpoints beyond the newest `cap`,
**always excluding frame 0 from the count itself**, not merely because
it happens to be old enough to survive: a capped recording that lost
its own starting point would have nothing left to resume from at all.
Confirmed to have real teeth by a deliberate mutation (removing that
exclusion) observed to fail
`test_record_retention_cap_never_prunes_frame_zero` before being
reverted, the same mutation-testing discipline TASK-046's own
`materialize_window` test already established. Applies to *everything*
already on disk in `output_dir`, not only what one `record`/`resume`
call itself wrote -- `resume` prunes checkpoints `record` left behind
just as readily as its own new ones. `--max-checkpoints-retained` on
both `pyflow record` and `pyflow resume`, overriding `config.recording.
max_checkpoints_retained` the same way `--checkpoint-interval` already
overrides that field.

**`replay.py` (TASK-046) is the windowed-materialization library those
two tasks needed** -- `MaterializedWindow`, `materialize_window`,
`materialize_or_load_window`, `find_checkpoint_at_or_before`. No
`rendering` import, the same rule `recording.py` follows: this is a pure
library, given a checkpoint directory and a frame range, that
re-simulates forward and returns dense, in-memory per-frame field
data -- what a renderer needs, built independently of whether one
exists. **Ephemeral by default, with an optional disk cache, not two
CLI commands** -- the maintainer's own choice: `materialize_window`
always re-simulates; `materialize_or_load_window` (what `pyflow play`
calls) reads an exact-range match from `--cache DIR` if one exists there
and writes one after materializing if not, so a caller opts into
avoiding recomputation rather than getting a second, separate artifact
by default. `find_checkpoint_at_or_before` ranks candidates by the frame
number in the *filename* first (cheap, no I/O for a discarded
candidate; `checkpoint.list_checkpoints`, factored out for exactly this
purpose by TASK-049, not this module's own glob any more), then reads
only the winner and cross-checks its real `frame_count` against that
filename -- `checkpoint.py`'s own "the filename is a convention,
`frame_count` is authoritative" rule, applied to a lookup that would
otherwise trust the filename outright. Memory
footprint was measured directly before trusting it safe with no cap: the
golden demo's own mesh (256 cells x 2 fields x 500 frames) is 2.05 MB;
extrapolated to the largest mesh anywhere in this repository (128x128,
an experiment config) at 500 frames, ~197 MB -- comfortably under a
gigabyte at every size and frame range this repository actually runs.

**`playback.py` (TASK-047) is `pyflow play`'s own rendering half, and
the one Stage 8 module that *does* import `rendering`** -- putting
pixels on screen is its whole job. `PlaybackState`/
`advance_playback_position`/`toggle_pause`/`increase_speed`/
`decrease_speed` are pure, no-rendering, no-window logic
(`tests/unit/test_playback.py`); `play()` is the rendering integration,
reusing `field_visualization.build_vector_field_arrows`/`hud.
build_title_text`/`build_stats_text`/`mesh_visualization.*` the same way
`bootstrap.py`'s own live-stepping paths do, just indexing into
`MaterializedWindow.frames[i]` instead of calling `advance_simulation_
state`. **Scoped to solved-velocity-only rendering for this first cut**
(`config.simulation.velocity_solved` true, no declared fields --
`UnsupportedPlaybackConfigError` otherwise), matching Lid-Driven
Cavity's own shape -- the same "scope to what a demo genuinely needs
first" precedent `_add_solved_velocity_rendering`'s own history above
already set. **Space pauses/resumes, `+`/`-` change speed, both live,
both verified to genuinely coexist with `RenderWindow.run`'s own
`close_keys` handler before being relied on** -- two separately
registered `key_down` handlers on the same canvas both fire, in
registration order, confirmed with the same real-event-loop-plus-
`submit_event` technique `test_interactive_window.py` established.
**Real draw rate stays capped near ~30fps by scene-rebuild cost alone at
larger mesh sizes** (measured directly: `build_vector_field_arrows`
takes 31.66ms at 4,096 cells, comparable to a 30fps frame budget by
itself, versus 3.05ms at the golden demo's own 256-cell mesh) -- which
is why "speed" advances the fractional frame *position* per real draw
(`position += speed`, floored to an index, clamped rather than looped at
the end) rather than trying to draw more often.

**`RenderWindow.playback_state`, a new attribute on `window.py` itself**
(the same narrow, precedented shape `assembled_numerics`/
`simulation_fields` already establish, `rendering/CLAUDE.md`'s own
entries above), exists purely so a caller can read back pause/speed
state that would otherwise be a local closure variable inside `play()`
-- typed via a `TYPE_CHECKING`-only import of `playback.PlaybackState`
in `window.py`, since a real runtime import would be circular
(`playback.py` already imports `rendering`). Found necessary while
writing `tests/integration/test_playback_cli.py::
test_space_pauses_playback_live`: proving Space actually freezes the
rendered pixels (not only that `PlaybackState.paused` flips in
isolation) needed a way to reach both the window and the playback state
from outside `play()`, which its own `on_frame(window)` parameter and
this attribute together provide.
