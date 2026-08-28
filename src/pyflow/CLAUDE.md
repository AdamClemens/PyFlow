# CLAUDE

Four subpackages, each with its own `CLAUDE.md`: `configuration/`,
`engine/`, `physics/`, `rendering/` -- per `docs/planning/roadmap.md`
TASK-000. Two top-level modules alongside them: `__main__.py` (the CLI
entry point, `python -m pyflow`) and `bootstrap.py`. A fifth,
`engine/numerics/`, landed in Stage 3 -- see below.

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

**`__main__.py`'s second subcommand, `pyflow generate-config [--output
PATH]` (TASK-039, added 2026-08-21)**, does not orchestrate multiple
subpackages the way `bootstrap()` does -- it is a thin argparse wrapper
around `pyflow.configuration.generator.generate_config_yaml`, so it
lives directly in `__main__.py` rather than needing a root-level module
of its own. See `configuration/CLAUDE.md` for what the generator does
and why it reuses `dataclasses.asdict()`.
