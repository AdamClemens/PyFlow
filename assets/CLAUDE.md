# CLAUDE

Static, non-code files the engine or its documentation loads at runtime.
One subdirectory so far, `colourmaps/` -- see its own `CLAUDE.md`.

`icons/`, `shaders/` and `textures/` were retired 2026-08-19
(`docs/planning/backlog.md` E9): no document anywhere had ever stated
what they were for, which is the same test that retired
`tools/planner/`/`tools/scripts/`. Do not recreate a directory here
speculatively -- add one when something specific is about to load files
from it, and say in that directory's own `CLAUDE.md` what those files
are and who reads them.
