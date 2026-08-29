# Engineering Principles

These principles guide all engineering decisions made throughout the project.

They are intentionally stable and should change rarely.

---

## P-001

Knowledge should never depend upon individual memory.

---

## P-002

Everything that can reasonably be generated should be generated.

---

## P-003

Working software is more valuable than partially completed architecture.

---

## P-004

Every stage after Stage 0 must contain a working demonstration.

(Reworded 2026-08-15 from "every release after Release 0". The intent is
unchanged: "release" was never the unit the project plans in. That
rewording said "and PyFlow has no release process", which stopped being
true on 2026-08-29 when reaching the MVP triggered
`docs/planning/releases.md` -- corrected by the Stage 5 exit audit.
**The principle is unaffected, and the two now line up rather than
compete**: a release is cut when a stage closes and its exit audit
completes, so "every stage after Stage 0 must contain a working
demonstration" is also, in practice, what every release carries. Stage
remains the unit; release is downstream of it. See `docs/glossary.md`
and `docs/planning/releases.md`.)

---

## P-005

Prefer vertical slices over horizontal implementation.

---

## P-006

Documentation is part of the implementation.

---

## P-007

Prefer proven engineering practice over theoretical elegance unless there is a compelling reason otherwise.

---

## P-008

Optimise for maintainability over implementation speed.

---

## P-009

Optimise for clarity over cleverness.

---

## P-010

Every important decision should be recorded.

---

## P-011

Information should have a single authoritative source.

---

## P-012

Separate conceptual design from implementation.

---

## P-013

Design for future contributors, assuming they have forgotten everything.

---

## P-014

The repository should explain itself.

---

## P-015

Leave the project in a better state than you found it.

---

## P-016

Prefer reversible decisions until understanding justifies commitment.

---

## P-017

Model the problem domain before modelling the solution.

---

## P-018

Implement the simplest valid version of each layer, then improve them independently.
