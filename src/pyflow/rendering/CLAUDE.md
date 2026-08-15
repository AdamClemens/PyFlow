# CLAUDE

Rendering subsystem: window/render-loop bootstrap (`docs/planning/roadmap.md`
TASK-007) and visualisation of scalar/vector fields.

As of 2026-08-15, this package's scope also covers what was briefly a
separate, undocumented `interaction/` package (user input, camera/view
control) -- interactive visualisation and the input handling that drives
it belong together. See `docs/planning/backlog.md` §1 "TASK-000 package
structure mismatch" and `docs/CHANGELOG-DESIGN.md` for why. Split input
handling back out only once it's grown large enough to justify its own
package.
