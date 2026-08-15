# ADR-003: Numerical Components Are Modular, Independently Replaceable Strategies

**Status:** Accepted

---

# Context

PyFlow's MVP fixes specific numerical choices for the sake of a simple,
working initial implementation: first-order upwind advection, central
diffusion, RK4 time integration, PISO pressure-velocity coupling, and a
Conjugate Gradient linear solver.

The project's own guiding philosophy (`docs/planning/implementation-plan.md`,
"Replaceable Components") already states that every major numerical
component should sit behind a stable interface, and that future
improvement should primarily mean *adding* new implementations rather than
modifying existing ones. If numerical method choice were embedded
directly in the time-stepping/orchestration code, every future numerical
improvement (see the project's Upgrade Paths, and Capability Level 4,
"Numerical Improvements") would require changing the core engine instead
of extending it.

---

# Decision

Every major replaceable numerical component -- advection scheme, diffusion
scheme, time integrator, pressure-velocity coupling strategy, linear
solver, and boundary condition type -- is implemented behind a stable
interface.

Which concrete implementation is used for each component is a
construction-time/configuration concern, selected through PyFlow's
configuration system (`src/pyflow/configuration/`, per
`docs/planning/roadmap.md` TASK-005), not hardcoded into the simulation's
execution/timestep logic.

---

# Consequences

## Positive

- New numerical schemes can be added without modifying existing, working
  code, directly supporting the principle of extending through addition
  rather than modification.
- Numerical method choice becomes directly configurable and comparable --
  this is what Capability Level 4's "numerical comparison between
  algorithms by changing configuration only" golden demo depends on.
- Each component's interface becomes a natural place to document its
  contract, feeding the future Interface Contract Definitions (ICDs).

## Negative

- Requires upfront interface-design discipline. A poorly designed
  interface is harder to correct later than a quick hardcoded
  implementation would have been -- this decision raises the cost of
  getting an interface wrong.
- Some cross-cutting numerical interactions (for example, known stability
  interactions between particular advection and diffusion scheme
  combinations) are harder to enforce purely through independent
  interfaces, and may need explicit compatibility documentation rather
  than being caught structurally.

---

# Alternatives Considered

## Monolithic solver per scheme combination

Rejected.

Writing a separate, self-contained solver for each combination of
advection/diffusion/time-integration/etc. choices produces a
combinatorial explosion as more schemes are added, and duplicates logic
across many near-identical solver variants.

## Ad hoc mix of pluggable and hardcoded components

Rejected.

Allowing some components to be swappable and others to require engine
changes, decided case by case, produces an inconsistent codebase with no
predictable rule for which components are safe to extend -- directly
against the project's preference for clarity and a single, predictable
pattern.

## Full plugin/entry-point discovery system from day one

Deferred, not rejected.

A dynamic plugin/entry-point system (e.g. via packaging entry points) is a
plausible future evolution of the same idea -- it's already noted as a
possible future direction for the ICDs ("future plugin/component
discovery"). It introduces packaging and discovery complexity the MVP
doesn't need yet; simple, explicit strategy objects selected through
configuration are preferred to start, consistent with the project's
preference for the smallest useful implementation and reversible
decisions.

---

# Notes

This decision underlies every entry in the project's Upgrade Paths
(`docs/implementation/upgrade-paths.md`, KA-032) -- each assumes its
component can be swapped independently of the others.

If an interface itself proves inadequate once real implementations exist,
revising it should be an explicit, recorded decision (a new or amended
ADR), not a silent change -- per the root `CLAUDE.md`'s instruction not to
silently change established architecture.
