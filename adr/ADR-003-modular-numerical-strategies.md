# ADR-003: Numerical Components Are Modular, Independently Replaceable Strategies

**Status:** Accepted, partially implemented

# Implementation Status

**Added 2026-08-22, by a repository consistency sweep** -- see
`adr/ADR-002-fvm-first.md`'s section of the same name for why both
appeared at once. **Left stale for five days**, not updated when Stage 3
(TASK-018..022, done 2026-08-23) actually built all six interfaces --
found and corrected 2026-08-27 while TASK-023's own Blast Radius sweep
was checking for other restatements of "no numerics interface exists
yet". Exactly the failure mode this ADR's own "Implementation Status"
convention (`adr/README.md`) exists to catch, caught late because
nothing re-reads a closed ADR's status section on its own.

**What exists:** the pattern, proven twice now. `RenderingConfig.backend`
selects between two `RenderCanvas` implementations at construction
(`src/pyflow/rendering/canvas.py`), with the per-timestep code path never
branching on which was chosen -- this ADR's "construction selects
implementations; execution operates through contracts" applied to
windowing. All six numerical components now have that same shape for
real (Stage 3, TASK-018..022): a `numerics` configuration section
(`NumericsConfig`), one interface per component
(`src/pyflow/engine/numerics/`), and a registry (`assembly.py`) that
resolves a configured name to a live instance with no `if`/`match` chain
to edit for a new one (Criterion 3's own test,
`register_a_new_name_resolves_without_editing_assembly`). **Advection is
the first to prove replaceability with a real second implementation, not
just a hypothetical one** (TASK-023, Stage 4, 2026-08-27):
`FirstOrderUpwindAdvection` replaced `assembly.py`'s
`_NullAdvectionScheme` under the exact same registered name
(`"first_order_upwind"`), with no edit to `assemble_numerics`'s own body
and no edit to `test_advection_contract.py`'s existing test bodies --
this ADR's claim, demonstrated rather than only architected.
`docs/architecture/icds.md` specifies all six components' user-facing
contracts.

**Diffusion followed the same day** (TASK-024, Stage 4, 2026-08-27):
`CentralDifferenceDiffusion` replaced `assembly.py`'s
`_NullDiffusionScheme` under the exact same registered name
(`"central_difference"`), again with no edit to `assemble_numerics`'s
own body and no edit to `test_diffusion_contract.py`'s existing test
bodies -- the pattern proven a second time, not a special case the first
time happened to need.

**Time Integration followed the next day** (TASK-025, Stage 4,
2026-08-27): `RK4Integrator` replaced `assembly.py`'s
`_NullTimeIntegrator` under the exact same registered name (`"rk4"`).
**Unlike advection/diffusion, this one also required revising the
interface itself** -- `TimeIntegrator.advance`'s `derivatives` parameter
(a single precomputed snapshot) could not supply what RK4's own
multi-stage evaluation needs, exactly the situation this ADR's own Notes
section anticipated below ("If an interface itself proves inadequate ...
revising it should be an explicit, recorded decision"). Recorded as
`adr/ADR-008-time-integrator-derivative-callable.md`, the first time that
anticipated situation actually arose.

**Linear Solver followed the next day** (TASK-026, Stage 4, 2026-08-27):
`ConjugateGradientSolver` replaced `assembly.py`'s `_NullLinearSolver`
under the exact same registered name (`"conjugate_gradient"`), again
with no interface change and no edit to `test_linear_solver_contract.py`'s
existing test bodies. Its own real content was the positive-semi-definite
pressure system `icds.md`'s Linear Solver ICD already named as "a real
compatibility requirement, not an incidental detail" -- a genuine
correctness trap (naive "always project the null space out" silently
solves a different problem for a well-conditioned system) caught by a
numerical prototype before any test or implementation code was written,
not discovered afterward. Full reasoning:
`docs/planning/roadmap.md` TASK-026's own Design decisions.

**Pressure-Velocity Coupling followed the next day** (TASK-027, Stage 4,
2026-08-27): `PISO` replaced `assembly.py`'s `_NullPressureCoupling`
under the exact same registered name (`"piso"`), again with no edit to
`test_pressure_coupling_contract.py`'s existing test bodies -- and, this
time, alongside two non-`ADR-003` interfaces gaining their own first real
implementations too (`GreenGaussGradient`/`GreenGaussDivergence`,
`Gradient`/`Divergence`, owned by this task directly rather than
resolved through the registry, since neither is one of the six
components this ADR names). **A real interface change again, the second
since Time Integration's**: `PressureCoupling.correct` gained a second
parameter, `dt`, recorded as `adr/ADR-009-pressure-coupling-dt.md`.
**A genuine, honestly-scoped limitation, not a hidden one**: `PISO`
performs a single correction pass, verified to measurably and boundedly
reduce a manufactured field's divergence -- not the full multi-pass Issa
algorithm, because PyFlow's collocated mesh needs Rhie-Chow interpolation
(and the momentum-equation coefficients this task's own interface has no
way to obtain) to suppress pressure-velocity decoupling under *repeated*
correction. That stronger claim was found, during this task's own design
session, to belong to Stage 5 TASK-033 instead -- full reasoning:
`docs/planning/roadmap.md` TASK-027's own Design decisions, and
`docs/practices.md`'s "A criterion whose strong reading depends on a
later task must say so when drafted", the standing rule this finding
produced.

**What still does not exist:** a real Boundary Condition implementation
-- `dirichlet`/`neumann` still resolve to `assembly.py`'s own trivial,
non-physical reference classes. Stage 4 (`docs/planning/roadmap.md`,
TASK-028/029) brings each in turn, the same way TASK-023/024/025/026/027
brought advection/diffusion/time integration/linear solver/pressure
coupling.

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
  contract, feeding the Interface Contract Definitions (ICDs) --
  `docs/architecture/icds.md`, written 2026-08-17, which covers exactly
  the six components this decision names.

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

  **That documentation now exists** (added to the Handbook 2026-08-17/18,
  after this ADR was accepted), and the two concrete instances found so
  far are worth naming here because they cross *different* layer pairs:
  central-difference advection's boundedness depends on the cell Péclet
  number, hence on the configured diffusion coefficient
  (`docs/handbook/numerical-methods/advection.md`); and forward Euler
  combined with central-difference advection is unstable at every
  timestep, an advection/*time-integration* interaction rather than an
  advection/diffusion one
  (`docs/handbook/numerical-methods/time-integration.md`). Both matter
  because the relevant upgrade paths are traversed independently by
  design -- which is exactly this consequence, realised.

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
plausible future evolution of the same idea -- `docs/planning/
knowledge-architecture.md` KA-030 lists "future plugin/component
discovery" among what the ICDs enable. Note that this is the KA *spec*'s
Enables list; `docs/architecture/icds.md` itself does not yet address
plugin discovery, and says so as of 2026-08-18 rather than leaving the
gap implicit. It introduces packaging and discovery complexity the MVP
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
