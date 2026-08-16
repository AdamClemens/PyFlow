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
