# Task Prompt Template

Reusable structure for delegating one PyFlow task to an agent. Instantiated
copies live alongside this file as `task-<slug>.md`. Grounded in the
Artifact Record Schema and Prompt Architecture described in
`docs/planning/knowledge-architecture.md` §5 and §17-18.

Only delegate a task once it has no open project-identity decisions left —
if picking an approach requires a judgment call only the maintainer should
make, resolve that first (see `docs/planning/backlog.md`), then instantiate
this template.

---

## Context

<1-2 sentence project mission, from CLAUDE.md/README>

<Relevant CLAUDE.md files, root -> target directory, concatenated verbatim
in that order. Where a lower file extends or overrides the parent, the
lower file wins.>

## Task

Target file(s): <exact path(s), to be created or modified>
Purpose: <why this file/change exists>
Scope: <precisely what's in scope -- and explicitly what's NOT>
Depends on: <files/decisions this task assumes are already resolved>
References: <source material to draw from, if any>

## Constraints

- Do not invent facts; if something is uncertain, flag it rather than guessing.
- Do not resolve contradictions silently -- report them instead.
- Preserve existing decisions and content unless explicitly told to change them.
- After making the change, update the nearest `CLAUDE.md` with guidance on
  how/when this file should be maintained going forward. If no CLAUDE.md
  exists yet at the appropriate level, create a minimal one.

## Definition of Done

- [ ] <concrete, checkable condition>
- [ ] <concrete, checkable condition>

## Review Cycle

If Output includes source under `src/` or `tests/`: once the Definition
of Done's own tests pass, review the diff under the Auditor stance
(`prompts/common/AUDITOR.md`) -- fix what it finds, then review again.
Repeat until a pass finds nothing, or every remaining finding is
explicitly deferred with a stated reason. Do not mark the Definition of
Done met on the strength of a single, self-reviewed pass; see
`AUDITOR.md` for why. Omit this section for prompts with no code
output (an ADR, a Handbook entry).

## Output

<exact file(s) to produce/modify, and in what format>

---

## Worked Example

`agents.md` (KA-043) tells an agent writing a `CLAUDE.md` to prefer a
real precedent over a hypothetical one; this template didn't follow its
own advice until this section existed. What follows is a condensed
instantiation against a real, already-closed task -- TASK-021, Pressure
Coupling Interface, done 2026-08-23 (`docs/planning/roadmap.md`,
TASK-021). It is compressed for length: the real task carried a
three-way design decision escalated to the maintainer and a full
per-criterion Stage 3 discharge record that this section leaves out
rather than restates. Match its *granularity and level of detail* when
writing a new prompt, not its exact content -- and follow the link for
what compression left out, rather than treating this as the complete
record.

### Context

PyFlow is a modular, field-centric CFD engine that separates physical
phenomena from numerical implementation (`CLAUDE.md`, `prompts/global/
project.md`).

<In a real instantiation this field holds the concatenated CLAUDE.md
chain, root to target, verbatim -- root `CLAUDE.md`, `src/pyflow/
CLAUDE.md`, `src/pyflow/engine/CLAUDE.md`, `src/pyflow/engine/numerics/
CLAUDE.md`, in that order. Omitted here only because reproducing four
files in full would obscure the other sections, not because a real
prompt may skip it.>

### Task

Target file(s): `src/pyflow/engine/numerics/pressure_coupling.py`
(new), `src/pyflow/engine/numerics/assembly.py` (new).
Purpose: define the interface that enforces incompressibility -- given
a provisional velocity field, produce a corrected, divergence-free one
and the pressure field consistent with it -- and, as Stage 3's last
task, assemble all six numerics components from configuration and
demonstrate the assembly works end to end.
Scope: the `PressureCoupling` ABC (one abstract method, `correct`) and
the assembly/registry path that resolves all six `NumericsConfig`
fields. Explicitly NOT in scope: any concrete PISO implementation --
Stage 3 defines interfaces and computes nothing (root `CLAUDE.md`,
"Acceptance Criteria for Simulation Work").
Depends on: TASK-022's `LinearSolver` type, required at
`PressureCoupling`'s construction (the one real cross-layer dependency
among the six, per `docs/architecture/icds.md`'s Pressure-Velocity
Coupling ICD); TASK-018, TASK-019, TASK-020, TASK-014..016.
References: `docs/architecture/icds.md` (Pressure-Velocity Coupling
ICD), `docs/planning/roadmap.md` TASK-021 and Stage 3 Completion
Criteria.

### Constraints

(unchanged from the template's own Constraints section above -- this is
the one part of a real instantiation that doesn't vary per task.)

### Definition of Done

- [ ] `PressureCoupling` defined with sole abstract method `correct`;
      a contract suite (`tests/unit/numerics/
      test_pressure_coupling_contract.py`) passes against at least two
      independent implementations, per `docs/practices.md`'s
      interface-first rule.
- [ ] `assemble_numerics(config)` resolves all six `NumericsConfig`
      fields through a name registry and raises a named error for an
      unregistered name (`tests/unit/numerics/test_assembly.py`).
- [ ] A golden demo runs `pyflow run` as a real subprocess and the
      assembled set is checked back out of it, not asserted only
      in-process (Stage 3 Completion Criterion 8 -- and see
      `prompts/common/AUDITOR.md` for why "a test exists and passes"
      was not sufficient evidence for this one).
- [ ] `make ci` clean, including the new/touched modules at 100%
      coverage.

### Review Cycle

Review the diff under `prompts/common/AUDITOR.md`'s stance once the
suites above are green; fix and re-review until a pass finds nothing.
The real TASK-021 predates this template section, and ran no such cycle
per task -- the three defects it would have caught (the missing
Criterion 8 assertion, `_NullLinearSolver`'s wrong `converged` value,
the unguarded registry) instead surfaced a day later, at the Stage 3
exit audit, after the branch had already merged (`docs/practices.md`,
"Audit code before calling it done"). This section exists so a new
task's cycle runs before Definition of Done is marked met, not after.

### Output

`src/pyflow/engine/numerics/pressure_coupling.py`,
`src/pyflow/engine/numerics/assembly.py`,
`tests/unit/numerics/test_pressure_coupling_contract.py`,
`tests/unit/numerics/test_assembly.py`, the golden demo fixture and its
feature file, plus the `CLAUDE.md` and architecture-doc updates the
change's own Blast Radius requires.
