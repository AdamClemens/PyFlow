# Implementation Plan / Task Prompt Context

Per `docs/planning/knowledge-architecture.md` KA-042. Tells an agent how
to write a task description precise enough that another agent -- with no
memory of this conversation -- can execute it correctly.

Read alongside, not instead of:

- `docs/planning/roadmap.md` -- the concrete, current-work-order view;
  its existing tasks (TASK-000 onward) are the working precedent for the
  shape described below.
- `docs/planning/implementation-plan.md` -- the long-range,
  capability-level vision a task should trace back to.
- `prompts/common/TEMPLATE.md` -- the reusable structure
  (Context/Task/Constraints/Definition of Done/Output) that an
  *instantiated* task prompt actually uses. This file is about what goes
  into that template's `## Task` section when the source is a
  roadmap/implementation-plan item; it does not replace the template.

---

## What Makes a Task Executable Without History

The test is literal: could a competent developer, or a fresh agent,
execute this with no access to the conversation that produced it? If
understanding the task requires knowing something that was only ever
said out loud, the task description is incomplete, not the agent.

Every task should state:

- **Purpose** -- what this produces and why it's needed now, not just a
  restatement of its title.
- **Place in the overall project** -- which capability level or roadmap
  stage this serves, so the task doesn't get executed in a vacuum
  disconnected from why it matters.
- **Dependencies** -- what must already exist or already be decided.
  Name specific artifacts or backlog items, not vague prerequisites
  ("the environment should be set up" -> "depends on TASK-001").
- **Artifacts** -- the specific files or components this task produces.
  Precise paths beat descriptions; roadmap.md's existing tasks list them
  as concrete bullets, not prose.
- **Implementation approach** -- concrete enough to start from, without
  prescribing every internal detail a competent implementer should be
  free to decide (`docs/engineering-principles.md` P-016: prefer
  reversible decisions until understanding justifies commitment --
  don't over-specify what hasn't been decided yet).
- **Verification** -- how completion is actually checked: a command to
  run, a test to pass, an output to inspect. "It works" is not
  verification; "`make test` exits 0 and asserts X" is.
- **Definition of Done** -- the checkable conditions, derived from
  Purpose and Verification, that make "is this done?" answerable without
  a judgement call. `docs/planning/backlog.md`'s own convention -- each
  item states what it produces and how completion is checked -- is the
  standard to match.
- **Upgrade implications**, where relevant -- what this task forecloses
  or leaves open for a later capability level, so a reversible-seeming
  choice isn't accidentally load-bearing three stages later.

## A Real Precedent to Follow

`docs/planning/roadmap.md`'s existing tasks (TASK-000 onward) already use
this shape under the headings Purpose / Dependencies / Artifacts Produced
/ Implementation / Acceptance Criteria -- Acceptance Criteria there
folds together Verification and Definition of Done. Match that structure
rather than inventing a new one; consistency across tasks is what lets an
agent orient quickly on task N+1 having only just read task N.

## Definition of Done

A task is executable by a competent developer without needing
undocumented historical context -- per KA-042. If executing it would
require asking "wait, what did we decide about X?", the task is not done
yet, regardless of how much prose it contains.
