# CLAUDE

The graph's content, conforming to `../model/schema.yaml` -- see
`../CLAUDE.md` for the scope rule that governs what belongs here at all.

These hold content:

- `components.yaml` -- the engine's nine conceptual layers, following
  `docs/architecture/engine.md`. **Every `depends_on` edge quotes the
  sentence it was derived from**, out of that layer's own **Contract** in
  `engine.md`. Keep doing that: it is the difference between a
  dependency someone read off the architecture and one they assumed from
  how CFD engines generally look, and it makes a stale edge visible --
  if the quote no longer matches `engine.md`, one of the two is wrong.
- `capabilities.yaml` -- the implementation plan's eleven capability
  levels. One progression axis only; the capability *map*'s groups are a
  different axis and modelling both without deciding how they relate
  would hard-code `docs/planning/backlog.md` §9's competing-vocabularies
  problem into a machine-readable file.
- `demos.yaml` -- the golden demos, each with a `validates` edge to the
  level whose own **Golden Demo** section names it.

- `releases.yaml` -- released versions, one entity per release. Empty
  from creation until 2026-08-29, correctly so; its stated trigger
  ("populate only if PyFlow gains a release process") fired when
  reaching the MVP closed Stage 5.

The other three are empty, each with a stated trigger in
`../model/entities.yaml`. Populate a file when its content exists *and*
something consumes it, not to make the directory look complete
(`adr/ADR-006-knowledge-graph-scope.md` rule 6). **`releases.yaml` is
the first file here to make that transition, and it is worth reading as
a worked example of the trigger mechanism**: the trigger was written
down, the condition genuinely fired, and nothing noticed for a day --
the Stage 5 exit audit did. A stated trigger is a good record and a poor
alarm (`docs/practices.md`, "A checkable trigger still needs somebody to
check it").

**A missing edge must be declared, not merely absent.** An entity that
would normally have an edge and does not carries an `unresolved:` field
saying why -- `capability-level-7` (no roadmap Stage corresponds to it)
and `capability-level-0` (infrastructure, not an engine layer) are the
two worked examples, and they are different kinds of absence.
`make check-graph` enforces this for capabilities, which is what turns a
gap someone has to remember into one the repository states.
