# CLAUDE

This file contains instructions specific to `prompts/global/`.

These rules extend the repository-level `CLAUDE.md`.

---

# Purpose

Durable, project-wide context for document-generation agents, per
`docs/planning/knowledge-architecture.md` KA-039. A fresh agent with no
conversation history should be able to read this and understand PyFlow's
enduring purpose and philosophy.

---

# Status

`project.md` (KA-039) exists as of 2026-08-15.

`prompts/common/BRIEF` used to serve as the de facto global context, but
its "Current Direction" section (FVM, Cartesian mesh, RK4, PISO, etc.) was
exactly the kind of current-numerical-architecture content KA-039 says
must not live at this layer -- and turned out to nearly duplicate the MVP
Numerical Framework section almost verbatim (then inside
`docs/planning/implementation-plan.md`; extracted to
`docs/implementation/mvp.md` later the same day). Resolved (maintainer's call): `project.md` supersedes
BRIEF entirely, with "Current Direction" cut rather than carried over
(that content already has one authoritative home). BRIEF was deleted.

KA-039 is explicit that this file must NOT contain current numerical
architecture, current stage, current implementation status, or
task-specific decisions -- `project.md` points to `roadmap.md`,
`backlog.md`, and `implementation-plan.md` instead of restating any of
that.

---

# Maintenance

Reconciled against KA §17-18 on 2026-08-15. If `project.md` starts
accumulating content that changes often, that's a sign it belongs in
local/task context instead -- move it out rather than let this file drift
out of KA-039 compliance again.
