# ADR-008: Time Integrator Consumes a Re-evaluatable Derivative Function, Not a Precomputed Snapshot

**Status:** Accepted

---

# Context

TASK-020 (Stage 3, done 2026-08-23) gave `TimeIntegrator` this abstract
method:

```python
def advance(
    self,
    fields: Mapping[str, Field],
    derivatives: Mapping[str, torch.Tensor],
    dt: float,
) -> dict[str, Field]: ...
```

`derivatives` was a single precomputed snapshot -- `simulation.step`
(TASK-040) computed it once, before calling `advance`, from the
currently-configured advection/diffusion schemes evaluated at the
current state.

That is everything an Euler-shaped scheme needs. It is not enough for
RK4, PyFlow's own MVP time integrator
(`docs/architecture/icds.md`: "`rk4` (the only implementation; MVP)").
RK4 is a four-stage explicit method: it evaluates the time derivative at
the current state and at three successively refined intermediate
estimates *within* the timestep, then combines all four
(`docs/handbook/numerical-methods/time-integration.md`). A fixed
snapshot cannot supply the derivative at a state the caller has not yet
computed -- and `simulation.step`'s own source confirms there was no path
for an integrator to ask for one: `step` built exactly one dict and
handed it to `advance`, full stop.

This was found before TASK-025 (RK4) wrote any implementation code, not
discovered partway through it -- `docs/practices.md`'s "hold a design
session before implementing" rule exists precisely for a criterion
("fourth-order accurate") that cannot honestly be met without first
settling this. `adr/ADR-003-modular-numerical-strategies.md` already
named the resolution path in advance, in its own Notes section: "If an
interface itself proves inadequate once real implementations exist,
revising it should be an explicit, recorded decision (a new or amended
ADR), not a silent change."

---

# Decision

**`TimeIntegrator.advance`'s second parameter becomes**

```python
derivative: Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]]
```

**replacing `derivatives: Mapping[str, torch.Tensor]`.** `derivative(state)`
returns each field's time derivative evaluated at `state`, which need
not be `fields` itself. A single-stage integrator (`_EulerIntegrator`)
calls it once, with `fields` -- reproducing exactly what the old
signature offered. A multi-stage integrator (`RK4Integrator`) calls it
again at each intermediate state it constructs.

`simulation.step` builds this callable as a closure over `numerics`,
`velocity`, and `mesh` rather than a precomputed dict. `velocity` stays
fixed across every evaluation within one `step` call -- `step` only ever
advances `fields`; nothing advances `velocity` itself until Stage 5's
pressure coupling exists, so holding it constant across RK4's own
sub-stages is not a new assumption, only an explicit one.

This is a real, breaking change to a previously-"Done" Stage 3 interface.
Every existing `TimeIntegrator.advance` implementation needed its call
site adapted: `tests/unit/numerics/test_time_integrator_contract.py`'s
`_EulerIntegrator`/`_DoubleStepIntegrator` test doubles, and
`tests/unit/test_simulation.py`'s own local `_EulerIntegrator` double.
The arithmetic each performs is unchanged; only the shape of what they
call to get a derivative changed.

---

# Alternatives Considered

## Scope RK4 to a derivative analytically re-derivable from one sample

Rejected. E.g. assume the derivative is proportional to the field's own
value (`dy/dt = k*y`, inferring `k = derivative / y` from the single
snapshot) and re-derive it at each intermediate stage without calling
back into `numerics`. This keeps the old signature and lets a genuine
four-stage RK4 *arithmetic* run, provable against a closed-form
exponential-decay test case.

It is also a plausible-looking wrong answer the moment it is wired into
the real engine: `simulation.step`'s actual derivative is not, in
general, proportional to the field's own value (it depends on the
mesh, the configured advection/diffusion schemes, and the velocity
field), so an integrator built on this assumption would silently
compute an incorrect update for every real simulation while passing a
narrow unit test built around the one problem shape it was designed for.
This is exactly the failure class `docs/practices.md` names repeatedly
(the pan-tracking bug, the unvalidated mesh accessors): code that looks
correct and is checked against a test that cannot tell the difference.

## Give only `RK4Integrator` a constructor-injected re-evaluation callback, leave `advance`'s own signature alone

Rejected. This would mean two different implementations of one ABC's one
abstract method accept meaningfully different information at
construction to make `advance` work at all -- `RK4Integrator` needing an
extra callback that `_EulerIntegrator` does not, with no way to express
that difference in the shared interface itself. It stops being one
interface with interchangeable implementations (`adr/ADR-003`'s own
premise) and becomes two interfaces that happen to share a method name.
`simulation.step` would also need to know, at the call site, whether the
configured integrator needs this extra wiring -- reintroducing exactly
the kind of "orchestrator knows about a specific scheme's own needs"
leak `adr/ADR-003`'s modular-component design exists to avoid.

## Add a seventh, integrator-callback-shaped component

Rejected under P-016 (`docs/engineering-principles.md`): nothing has
anticipated a second way to re-evaluate a derivative, and `adr/ADR-003`
already names exactly six independently-configured components. This
would be speculative generality for a distinction (single- vs.
multi-stage integration) the widened `advance` signature already
expresses without a new component.

---

# Consequences

**Positive**

- `RK4Integrator` (and any future multi-stage explicit or adaptive
  scheme, per `docs/implementation/upgrade-paths.md`'s Time Integration
  path: Euler → RK2 → RK4 → adaptive RK) can be built as a real,
  general-purpose implementation, correct for the actual engine dynamics
  it will drive -- not only for a restricted test problem.
- `_EulerIntegrator`-shaped schemes are unaffected in spirit: calling
  `derivative(fields)` once is a valid, minimal use of the wider
  interface, not a special case bolted on beside it.
- `simulation.step`'s own Stage 4 Completion Criterion 1 obligation
  (never branches on `Mesh.is_boundary_face`) is untouched -- the
  closure rewrite only changes how the derivative is supplied, not how
  boundary faces are handled.

**Negative**

- A real migration cost, paid once: every existing `TimeIntegrator`
  implementation (test doubles included) needed its call site adapted,
  and TASK-020's own contract suite needed non-trivial edits rather than
  the "join adds a factory, edits nothing" shape TASK-023/024 both
  achieved when adding a real advection/diffusion scheme.
- `TimeIntegrator.advance`'s contract is slightly less simple to state:
  "given the derivative" becomes "given a function that computes the
  derivative at any state," which is one more level of indirection for a
  reader encountering the interface for the first time.

---

# Notes

Recorded against `docs/planning/roadmap.md` TASK-020 (a short correction
pointer, not a rewrite of that closed record) and TASK-025 (the full
design decision, in context). `adr/ADR-003-modular-numerical-
strategies.md`'s own "Updated" section points here for the interface
revision itself, alongside its existing note that Time Integrator is now
a real implementation.
