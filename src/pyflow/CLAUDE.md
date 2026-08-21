# CLAUDE

Four subpackages, each with its own `CLAUDE.md`: `configuration/`,
`engine/`, `physics/`, `rendering/` -- per `docs/planning/roadmap.md`
TASK-000. Two top-level modules alongside them: `__main__.py` (the CLI
entry point, `python -m pyflow`) and `bootstrap.py`.

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

**`__main__.py`'s second subcommand, `pyflow generate-config [--output
PATH]` (TASK-039, added 2026-08-21)**, does not orchestrate multiple
subpackages the way `bootstrap()` does -- it is a thin argparse wrapper
around `pyflow.configuration.generator.generate_config_yaml`, so it
lives directly in `__main__.py` rather than needing a root-level module
of its own. See `configuration/CLAUDE.md` for what the generator does
and why it reuses `dataclasses.asdict()`.
