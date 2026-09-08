# CLAUDE

Claude Code skills for this repository: reusable, user-invoked (`/<name>`)
prompt files that encode a workflow already documented elsewhere in the
repository, so it doesn't have to be re-described by hand each time it's
run. One subdirectory per skill, each `<name>/SKILL.md`.

- `ship/` -- the branch/TDD/blast-radius/preflight/CI/PR/merge sequence
  from root `CLAUDE.md`'s Branch Discipline and Merge Gate sections. See
  its own `CLAUDE.md`.

A skill here is a checklist referencing the repository's actual rules,
never a second copy of them -- if a skill's steps and the `CLAUDE.md`
section they cite disagree, the `CLAUDE.md` section wins, and the skill
gets fixed in the same change (the same restated-fact discipline
`docs/CLAUDE.md` asks of every generated document, applied here to a
hand-written one instead, since a skill's steps cannot be generated from
the rules they summarise).

Added 2026-09-08, alongside `ship/`, following the same "real content
first, `CLAUDE.md` and manifest entry in the same change" pattern
`tools/CLAUDE.md` already states for a new subdirectory.
