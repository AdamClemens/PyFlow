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
