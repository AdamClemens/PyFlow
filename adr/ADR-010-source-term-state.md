# ADR-010: SourceTerm.source Takes the Whole State, Not Only Its Own Field

**Status:** Accepted

---

# Context

TASK-018 (Stage 3, done 2026-08-23) gave `SourceTerm` this abstract
method:

```python
def source(self, field: Field) -> torch.Tensor: ...
```

No implementation, registry entry, or consumer existed for it through
Stage 5 -- the only one of Stage 3's five operator interfaces in that
state, a deliberate decision recorded in `source.py`'s own docstring
rather than an oversight (Stage 5's own design question six,
`docs/planning/roadmap.md`).

TASK-035 (Stage 6) builds `SourceTerm`'s first implementation: a
Boussinesq buoyancy body force, `f = c * (phi - phi_0) * g`, entering
momentum's own vertical component. The force is computed from a
*different* field than the one it acts on -- a temperature (or density)
difference drives a force on `velocity.1` -- and `source(self, field)`
is handed only the field being advanced. There is no way, with this
signature, for the term to read the temperature field's own current
value: the interface Stage 3 designed for exactly this consumer cannot
express its first one.

This was found on 2026-08-30 while drafting TASK-035's own roadmap
entry, before any implementation code was written -- `docs/practices.md`'s
"hold a design session before implementing" rule, applied here the same
way it already was for `adr/ADR-008-time-integrator-derivative-
callable.md` and `adr/ADR-009-pressure-coupling-dt.md`.
`adr/ADR-003-modular-numerical-strategies.md`'s own Notes section named
this resolution path in advance: "If an interface itself proves
inadequate once real implementations exist, revising it should be an
explicit, recorded decision ... not a silent change."

---

# Decision

**`SourceTerm.source`'s signature becomes**

```python
def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor: ...
```

**adding `state: Mapping[str, Field]`**, the same mapping
`engine/simulation.py`'s `derivative(state)` already has in scope at
every call. A source term reads whichever other field(s) it needs
directly out of `state`, by name, and returns zero for a field it has
no contribution to (`BoussinesqBuoyancy.source` returns zeros for
anything that isn't a velocity component).

`SourceTerm` has no implementations before this task, so nothing
existing breaks -- but this is still the one interface signature change
Stage 6 permits itself, named in that stage's Completion Criterion 2 in
advance, and the exit audit measures the stage's engine diff against
that count.

`simulation.py`'s own `derivative` closure gains one line:
`numerics.source_term.source(field, state)`, added to the accumulated
flux for every field in `state` -- the source term itself, not the
orchestrator, decides which fields it actually contributes to.

---

# Alternatives Considered

## Bind the term to a state inside `simulation.step`

Have `step` construct or configure the source term with a live reference
to `state` before calling `derivative`, so `source(field)` could read
`state` through that binding instead of receiving it as an argument.

Rejected. This repository has no precedent for a numerics component
holding a live reference into the orchestrator's own working state
outside its own call arguments -- every other interface (`AdvectionScheme.
flux`, `DiffusionScheme.flux`, `PressureCoupling.correct`) receives
everything it needs as explicit parameters. Introducing one now hides
the cross-field dependency inside a closure rather than a type, exactly
what `docs/practices.md`'s Design Rules ask to avoid where two options
are otherwise equivalent -- and these are not equivalent, since a bound
reference is invisible at the call site in a way an explicit parameter
is not.

## Construct the source term with its driving field once per step, accepting a stale reference across RK4's stages

Give `BoussinesqBuoyancy` a reference to the temperature `Field` at
construction time (once per `step` call) rather than reading it fresh
from `state` at each evaluation.

Rejected. RK4 evaluates `derivative` four times per step, at
successively refined intermediate states (`adr/ADR-008`) -- a source
term bound once at the step's opening state would see the *same* stale
temperature at all four stages instead of each stage's own intermediate
value, which is a real, first-order splitting error whose accuracy cost
would have to be stated and defended. Reading `state` fresh every call
costs nothing extra (`derivative` already has it) and keeps the term
consistent with RK4's own fourth-order claim.

## Add a seventh, state-aware component distinct from `SourceTerm`

Rejected under P-016 (`docs/engineering-principles.md`): nothing has
identified a second, structurally different kind of source term that
would need a separate interface. Widening the one interface Stage 3
already built for this purpose is not speculative generality -- it is
the interface arriving at its predicted first consumer
(`docs/planning/roadmap.md` Stage 6 design question two).

---

# Consequences

**Positive**

- `BoussinesqBuoyancy` (and any future source term needing a
  cross-field dependency -- a chemical reaction rate, a phase-change
  latent-heat term) can be built as a real, general-purpose
  implementation, correct for the actual engine state it drives.
- The dependency is explicit in the type (`state: Mapping[str, Field]`),
  not hidden in a closure or a construction-time binding.
- Costs nothing extra to get RK4-consistent: `derivative` already
  receives the state it's evaluating, so passing it through is free.

**Negative**

- `SourceTerm.source`'s contract is one parameter less simple to state:
  "given the field" becomes "given the field and everything else being
  transported," one more piece of context a reader meets on first
  encounter.
- A concrete source term can, in principle, read any field in `state`,
  not only ones it has a documented relationship with -- there is no
  static enforcement of which cross-field dependencies are legitimate,
  only each implementation's own docstring.

---

# Notes

Recorded against `docs/planning/roadmap.md` TASK-018 (a short correction
pointer to here, not a rewrite of that closed record) and TASK-035 (the
full design decision, in context, as Stage 6's own design question six).
`adr/ADR-003-modular-numerical-strategies.md`'s own "Updated" section
points here for the interface revision, alongside its existing notes for
`adr/ADR-008`/`adr/ADR-009`.

This is the third Stage 3 interface signature change recorded as its own
ADR, following the identical pattern both `adr/ADR-008` and `adr/ADR-009`
already established: written by the task that makes the change, not by
the design pass that decided it.
