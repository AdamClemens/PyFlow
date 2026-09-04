# Documentation Guidelines

These guidelines describe how documentation should be written throughout the project.

---

# Objectives

Documentation should:

- explain intent
- reduce cognitive load
- capture project knowledge
- avoid duplication
- remain maintainable

---

# Documentation Philosophy

Documentation exists to help future contributors understand the project.

Assume the reader has forgotten everything.

Optimise for understanding rather than completeness.

---

# General Rules

Every document should have a single primary purpose.

Avoid mixing unrelated concepts.

Prefer links over duplicated information.

Examples are preferred over abstract descriptions where appropriate.

Keep conceptual documentation separate from implementation details.

---

# Style

Prefer:

- clear language
- short sections
- descriptive headings
- diagrams where appropriate

Avoid:

- unnecessary verbosity
- undocumented assumptions
- duplicated explanations

---

# Source of Truth

Every piece of information should have one authoritative location.

Other documents should reference that location rather than duplicating it.

---

# Generated Documentation

Generated documentation must never be edited manually.

Edit the authoritative source instead.

---

# Cross-Referencing Into a Generated Document

**A link into a generated document must name a heading, and something
must check the anchor.** `make check-docs` resolves `file.md#heading`
fragments against the target's real headings as of 2026-09-05; before
that it checked only that the file existed.

The order matters and is the whole point. A generated document's
headings belong to its generator, which can rewrite them in a change
that never touches the linking prose -- so a cross-reference into one is
a restated fact wearing a link's clothes unless the anchor is verified.
Adding the references first and the check afterwards would have traded
a stale sentence for a silently broken link, which is not an
improvement.

Where this is used today: `docs/repository-manifest.md`'s per-directory
sections link to their listing in the generated
`docs/repository-inventory.md` -- the two are a declared pair, the
reasoning half and the factual half, and nothing pointed between them
per section before. `README.md`'s Current Phase links to the named
stage's entry in the generated `docs/planning/status.md`.

**Prefer a link over a restatement, and a restatement over neither.** If
prose needs a fact a generated document already holds, link to it. If it
genuinely needs the fact inline, that is a restatement and wants a gate
(see below).

---

# An Update a Task Owes Is Declared, Not Described

**If a document is waiting on a task to update it, say so in a form
something can check, and make sure the task's own entry says it too.**

    Updated-by: TASK-030 -- Section 4's `on_frame` note
    Updated-by: unassigned -- Section 3's checkpointing placeholder

`make check-documents` verifies three things a reader cannot: the task
exists, **the task's own roadmap entry names this document**, and the
task is not already Done -- because an obligation on a finished task is
overdue by definition.

**That last check is why this exists.** `docs/architecture/sequences.md`
asked in prose to be updated "once TASK-030 wires a live timestep loop
through it". TASK-030 landed on 2026-08-28, and that note went on
describing a seam nothing used for six days, on the same page as two
live paths through it. Nothing could have caught it: a note naming the
task that will invalidate it is not a trigger anything runs, and "re-read
it when that task is touched" never fires either, because nobody touches
a closed task.

**Declared rather than detected, deliberately.** Almost every mention of
a task beside the word "update" in this repository is *historical* --
"TASK-034 landed and deliberately did not build it" -- and telling those
from a live obligation needs a reader. `tools/validators/CLAUDE.md`
records why a check needing judgement must not gate, so this is a marker
somebody writes, like `Checked-by:` above, not a phrase a script guesses
at.

`unassigned` is allowed and is a real state: an obligation nobody has
scheduled is better recorded where an inventory reaches it than left in
prose. It must still say what it owes.

Unlike `Checked-by:`, this may appear anywhere in a document -- one
document has one honesty mechanism, but may owe several updates, each
belonging beside the paragraph that owes it.

---

# How a Document Is Kept Honest

**Every document under `docs/planning/`, `docs/architecture/` and
`docs/implementation/` declares, in its own first lines, which mechanism
keeps it true.** `make check-documents` (part of `make ci`) fails if one
does not. Three mechanisms, and they are deliberately not equally
strong:

- **`generated`** -- written by a tool from the repository's own state,
  with a stale copy failing `make ci`. It cannot drift. Never edit by
  hand. Names the target responsible:
  `Checked-by: generated (make status-report)`.
- **`gated`** -- hand-written, but some specific claim in it is
  machine-compared against reality. `make check-status` reads the
  roadmap's counts; `make check-stages` reads its stage structure. **The
  gated claim cannot drift; everything else in the document still can**,
  which is why the declaration names the target rather than implying the
  whole document is covered.
- **`stage-boundary`** -- hand-written, nothing mechanical reads its
  meaning, and it must be re-read whole at every stage boundary. **This
  is not a reliable mechanism**, and declaring it says so out loud.

**The declaration lives in the document, not in a register file.** A
central list of documents and their mechanisms would be a second copy of
a fact -- the failure mode this repository keeps finding -- and would
drift from the tree the moment a document was added. A line inside a
document cannot drift from that document.

**Why this exists.** Stage 7's exit audit found two documents stale for
days: `docs/architecture/rendering.md` described a package that had
gained a module, and `docs/architecture/sequences.md` described a seam
whose only caller had changed. Both were stale for the same reason --
nobody knew they were in the blast radius. The Blast Radius rule says to
work out what a change affects, and answering that from memory is what
failed. This turns "which documents does anybody check, and how?" from
tribal knowledge into an enumerated, checked inventory, and
`make check-documents` prints the `stage-boundary` list as the reading
list an exit audit needs -- derived every run, never restated.

**Prefer moving a document up the list.** A `stage-boundary` document
that keeps going stale in one specific way is asking for that one fact
to be generated or gated, not for more discipline.

---

# Documentation Definition of Done

Documentation is complete when:

- its purpose is clear
- it is internally consistent
- it links to related information where appropriate
- it avoids unnecessary duplication
- examples are included where they improve understanding
- it reflects the current state of the project

---

# Continuous Improvement

Documentation should evolve continuously.

Small improvements are preferred over infrequent large rewrites.
