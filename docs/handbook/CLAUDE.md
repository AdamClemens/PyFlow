# CLAUDE

The Handbook: stable scientific and engineering knowledge, split per
`docs/planning/knowledge-architecture.md` §8-9 into two independent
collections:

- `physics/` -- physical phenomena PyFlow models (see `physics/README.md`
  and `physics/CLAUDE.md`)
- `numerical-methods/` -- numerical methods PyFlow implements, explained
  independently of the implementation (see `numerical-methods/CLAUDE.md`)

This directory did not exist before 2026-08-15; a flat `docs/handbook.md`
(project meta/planning content, unrelated to this) previously held the
name and was retired the same day -- see `docs/CHANGELOG-DESIGN.md`.

Written: `numerical-methods/overview.md` (KA-007) and
`numerical-methods/compatibility.md` (KA-008), both moved here from
`docs/planning/numerical-frameworks.md` on 2026-08-15. **All sixteen
per-topic entries** (ten `numerical-methods/`, six `physics/`) were
written 2026-08-17 (`docs/planning/backlog.md` E3/E4) -- real domain
content with citations, following the dependency order each area's KA
entries state (`fvm.md` and `incompressible-flow.md` first in their
respective directories, since later entries in each build on them).
`docs/references/{books,papers,websites}.md` were populated from those
sixteen entries' citations the same day (E6).

## Maths Notation

Both collections write inline maths as `$...$` and display maths as
`$$...$$` on their own lines, LaTeX-style. Nothing in the repository
renders or validates this -- there is no docs site, and `make ci` does
not read Markdown bodies (root `CLAUDE.md`, Development Commands). The
delimiters are there so the notation is unambiguous to a reader and
ready for a renderer if one is ever added; until then, **an equation is
only as correct as the last person to read it.**

Two consequences worth knowing before editing an entry:

- **Check the maths renders as text, not just that the file saved.** A
  corrupted equation looks like ordinary prose damage and passes every
  check the project runs. `$\rho$` silently became `$ho$` in
  `prompts/features/handbook.md` during the 2026-08-18 review -- a shell
  heredoc interpreted the `\r` as a carriage return -- and `make
  check-docs` passed with the raw control character still in the file.
- **Bulk-editing these files through a shell is where that happens.**
  Backslash-heavy LaTeX (`\rho`, `\Delta`, `\mathbf`, `\frac`,
  `\nabla`) goes through at least one escaping layer on the way to
  disk. Prefer an editing tool that writes the file directly; if a
  script is genuinely the right approach, grep the result for stray
  control characters and re-read the changed equations afterwards.

`docs/glossary.md` defines the terms that carry the heaviest load across
both collections -- notably boundedness versus stability, which three
documents once conflated.
