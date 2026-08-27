# ADR-009: PressureCoupling.correct Takes an Explicit Timestep

**Status:** Accepted

---

# Context

TASK-021 (Stage 3, done 2026-08-23) gave `PressureCoupling` this
abstract method:

```python
def correct(
    self, provisional_velocity: VectorField
) -> tuple[VectorField, ScalarField]: ...
```

No timestep. That was sufficient through Stage 3, where no concrete
strategy existed to need one -- `_NullPressureCoupling` (the reference
implementation `assembly.py` registered under `"piso"`) returned the
provisional velocity unchanged and a zero pressure field, computing
nothing.

TASK-027 (Stage 4) builds `PISO`, the first real strategy. A pressure
correction is `u_corrected = u* - dt * grad(p)`, where `p` solves
`Laplacian(p) = div(u*) / dt` -- `dt` is not a tunable, it is the
physical quantity that gives the returned pressure field's units a real
meaning (`docs/planning/roadmap.md` TASK-027's own Context, quoting the
handbook's `u_corrected = u* - dt/rho * grad(p)`, density folded to 1
per `docs/handbook/numerical-methods/fvm.md`'s own documented kinematic-
pressure convention). Without it, `correct` can only produce a
correction scaled by an arbitrary, undocumented constant -- exactly the
kind of confident, plausible-looking wrong answer `docs/practices.md`
names repeatedly.

This was found while starting TASK-027, before any implementation code
was written, during the same design session that found PyFlow's
collocated mesh cannot support a fully-converged (near-zero) divergence-
free claim within this task's own scope (`docs/planning/roadmap.md`
TASK-027's own Design decision Two; that finding did not, on its own,
require an interface change -- this one does, independently).

---

# Decision

**`PressureCoupling.correct`'s signature becomes**

```python
def correct(
    self, provisional_velocity: VectorField, dt: float
) -> tuple[VectorField, ScalarField]: ...
```

**adding `dt: float`.** `PISO` is the only concrete strategy today; its
own `correct` builds the Poisson right-hand side as `-div(u*) / dt` and
the returned velocity correction as `provisional_velocity - dt *
grad(pressure)`.

This is a real, breaking change to a previously-"Done" Stage 3
interface, the same category `adr/ADR-008-time-integrator-derivative-
callable.md` was for `TimeIntegrator.advance`. Every existing
`PressureCoupling.correct` implementation needed its call site adapted:
`tests/unit/numerics/test_pressure_coupling_contract.py`'s
`_PassthroughCoupling`/`_ScaledCoupling` test doubles (both discard
`dt`, since neither performs a real correction), and every call site in
that same file's generic tests.

Density does not appear as a separate parameter. `NumericsConfig` has no
density field, and nothing downstream of `PISO` needs a dimensional
(rather than kinematic) pressure yet -- adding one now, with no real
consumer, would be exactly the speculative generality P-016
(`docs/engineering-principles.md`) refuses. `fvm.md`'s own kinematic
convention is invoked explicitly in `PISO`'s own docstring, not silently
assumed.

---

# Alternatives Considered

## Leave `correct` as `correct(provisional_velocity)`, fold `dt` into `PISO`'s own constructor

Rejected. `dt` is not a property of the strategy the way `tolerance`/
`max_iterations` are properties of `ConjugateGradientSolver` -- it is a
property of the specific correction being requested, and a real engine
loop's timestep is not necessarily fixed for the strategy's whole
lifetime (`docs/planning/roadmap.md` TASK-020's own design decision
already treats `timestep` as a per-call quantity threaded through
`simulation.step`, not a construction-time constant baked into
`TimeIntegrator`). Binding it at construction would make `PISO` unable
to answer a call with a different `dt` without being rebuilt, for no
benefit.

## Give only `PISO` a way to accept `dt`, leave `correct`'s own signature alone

Rejected, for the identical reason `adr/ADR-008` rejected the same shape
of alternative for `RK4Integrator`: it would mean two implementations of
one ABC's one abstract method accept meaningfully different information
to do their job, with no way to express that difference in the shared
interface itself -- `adr/ADR-003-modular-numerical-strategies.md`'s
"one interface, interchangeable implementations" premise breaks the
moment a caller has to know, out of band, whether the configured
strategy needs extra wiring.

## Add density as a third parameter now, anticipating a future non-kinematic use

Rejected under P-016. Nothing has identified a real consumer that needs
dimensional pressure; `fvm.md` already documents the kinematic
convention as a legitimate, named alternative, not a placeholder for a
missing feature. Add it the day a real consumer needs it, the same
"build against a real, tested requirement" discipline every other
interface widening in this project has followed.

---

# Consequences

**Positive**

- `PISO`'s pressure field carries a real physical meaning
  (kinematic-pressure-per-unit-density, per `fvm.md`'s own convention),
  not an arbitrary constant multiple of it.
- Any future `PressureCoupling` strategy needing a timestep (e.g. a
  future SIMPLE/SIMPLEC implementation, `docs/implementation/
  upgrade-paths.md`'s "Pressure–Velocity Coupling" entry) receives it
  through the same interface, not a bespoke constructor argument.

**Negative**

- A real migration cost, paid once: `test_pressure_coupling_contract.py`'s
  two test doubles and every call site needed adapting, the same
  "join is not free" cost `adr/ADR-008` already paid for `TimeIntegrator`.
- `PressureCoupling.correct`'s contract is one parameter less simple to
  state than before -- unavoidable given what a real correction pass
  actually needs.

---

# Notes

Recorded against `docs/planning/roadmap.md` TASK-021 (a short correction
pointer to here, not a rewrite of that closed record) and TASK-027 (the
full design decision, in context). `adr/ADR-003-modular-numerical-
strategies.md`'s own "Updated" section points here for the interface
revision, alongside its existing note that Pressure-Velocity Coupling is
now a real implementation.

Distinct from `register_pressure_coupling`'s own factory widening (also
TASK-027, adding `boundary_conditions` as a second constructor
argument) -- that follows the same registry-level pattern
`register_diffusion_scheme` already established for
`diffusion_coefficient` (TASK-024), which needed no ADR because it does
not touch `PressureCoupling`'s own abstract method. Only the ABC change
above does.
