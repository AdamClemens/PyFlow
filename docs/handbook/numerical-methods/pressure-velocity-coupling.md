# Pressure–Velocity Coupling

Per `docs/planning/knowledge-architecture.md` KA-023. How pressure and
velocity are coupled in incompressible CFD -- the mechanism that turns
independent per-field advection-diffusion solves (`advection.md`,
`diffusion.md`) into an actual incompressible-flow solver.

Depends on `docs/handbook/physics/incompressible-flow.md` (KA-010) for
the continuity and momentum equations being coupled, and on `fvm.md` for
the discretisation those equations are expressed in.

---

## The Coupling Problem

Incompressible flow's momentum equation
(`docs/handbook/physics/incompressible-flow.md`) determines how velocity
evolves *given* a pressure field, but the incompressible continuity
equation ($\nabla \cdot \mathbf{u} = 0$) contains no independent equation
for pressure at all -- pressure appears only through its gradient in the
momentum equation, with no equation of state relating it to density or
any other directly-evolvable quantity (unlike a compressible flow, where
an equation of state closes the system). Pressure's actual role in an
incompressible flow is to instantaneously adjust so that continuity is
satisfied everywhere -- it is best understood as a constraint-enforcing
field, not a transported one in the same sense as velocity or
temperature. Pressure-velocity coupling is the numerical machinery that
extracts a pressure field serving exactly that role, from an equation
system that does not hand it over directly.

## Pressure Correction

The common strategy is to advance velocity using a momentum equation
evaluated with a **provisional** pressure (or none at all), producing a
velocity field that does *not* yet satisfy continuity, and then derive a
**pressure correction** equation from the requirement that the
*corrected* velocity must be divergence-free. Substituting the momentum
equation's own relationship between a velocity correction and a pressure
correction into the continuity constraint produces an equation for the
pressure correction alone (structurally a Poisson equation, solved with
the machinery `linear-solvers.md` describes) -- solving it, then applying
the resulting velocity and pressure corrections, is what actually
enforces incompressibility at the discrete level. Every algorithm below
is a specific procedure for organising this predict-correct idea,
differing mainly in how many correction passes they perform per timestep
and what they assume about the flow.

## When the Pressure Equation Has No Unique Solution

A practical consequence of pressure being a constraint-enforcing field
rather than a transported one, and one worth knowing before the first
solve is attempted rather than after it fails to converge: **if every
domain boundary prescribes velocity, nothing anywhere fixes the level of
the pressure.** Only $\nabla p$ appears in the momentum equation, so
adding any constant to $p$ everywhere leaves the physics untouched. The
discrete pressure-correction system inherits this exactly -- it is
singular, with a one-dimensional null space of constant vectors, and is
positive *semi*-definite rather than positive definite.

Two things follow, both directly relevant to PyFlow's MVP, whose
lid-driven cavity validation case (`docs/implementation/mvp.md`) is
precisely a domain with velocity prescribed on all four boundaries:

- **A compatibility condition must hold**, or the system has no solution
  at all rather than merely a non-unique one. The net volumetric flux
  through the boundary must be zero, $\oint_{\partial V} \mathbf{u} \cdot
  \mathbf{n} \, dA = 0$ -- what flows in must flow out, since a
  constant-density fluid in a fixed domain cannot accumulate. Boundary
  values that violate this are not a solver problem to be tuned around;
  they describe an impossible flow (`boundary-conditions.md`).
- **The null space must be removed** before an iterative solver is asked
  for an answer. The two standard remedies are to pin the pressure at one
  reference cell (turning one equation into a Dirichlet condition), or to
  subtract the mean from the solution each iteration so it stays
  orthogonal to the constant vector. `linear-solvers.md` covers what this
  means for Conjugate Gradient specifically, which assumes a positive-
  *definite* system.

Neither point is exotic or advanced -- both are unavoidable the first
time a closed-domain incompressible case is run, which is why they are
recorded here rather than left to be rediscovered.

## PISO

**PISO** (Pressure-Implicit with Splitting of Operators) performs one
momentum predictor step followed by **two or more** pressure-correction
passes within a single timestep, each pass further refining both the
velocity and pressure fields. Because it does not simply accept the first
correction as final, PISO achieves good accuracy for **transient**
(time-accurate) simulation without needing outer iteration across
multiple full timesteps -- correction happens *within* one timestep, not
across successive ones.

PISO is PyFlow's MVP choice (`docs/implementation/mvp.md`), directly
matched to the MVP's real-time-visualised, genuinely transient flow
(`docs/architecture/icds.md`'s Pressure–Velocity Coupling ICD): its
multiple-correction-per-step design is what makes it well-suited to
producing an accurate time history of the flow, rather than only its
eventual steady state.

PISO's derivation drops terms whose size depends on the timestep, so its
accuracy claim is conditional on the timestep being small in the sense
Issa's original analysis sets out -- for a genuinely transient simulation
already timestep-limited by an explicit integrator's CFL condition
(`time-integration.md`), that condition is comfortably met, but PISO
should not be read as licence to take arbitrarily large steps. This is
the same operator-splitting error `time-integration.md` notes as the cap
on the finished solver's temporal order.

## SIMPLE and SIMPLEC

**SIMPLE** (Semi-Implicit Method for Pressure-Linked Equations) performs
a single momentum predictor and a single pressure correction per outer
iteration, but under-relaxes the correction and repeats the whole cycle
until the solution converges -- suited to **steady-state** problems,
where only the converged final state matters and the path of outer
iterations toward it need not itself represent a physically accurate
time history. **SIMPLEC** (SIMPLE-Consistent) modifies SIMPLE's
correction-equation derivation to remove an approximation SIMPLE makes,
typically converging faster (needing less or no under-relaxation) at
comparable cost per iteration.

## Relevant Alternatives and Suitability

Whether PISO or a SIMPLE-family algorithm is appropriate depends on
whether the simulation genuinely needs an accurate *transient* solution
(PISO) or only the converged *steady-state* result (SIMPLE/SIMPLEC) --
neither is "more advanced" than the other in a way that makes one
obsolete; they are suited to different regimes
(`docs/implementation/upgrade-paths.md`'s "Pressure–Velocity Coupling"
entry makes this distinction explicitly, correcting an earlier internally
inconsistent version of this project's own upgrade path that implied
otherwise -- see that document's own note). A future configuration
exposing both is a real capability, not a strict upgrade over PISO alone.

## Convergence and Computational Cost

PISO's multiple correction passes per timestep cost more per step than a
single-correction algorithm would, but avoid the outer-iteration loop
SIMPLE/SIMPLEC need to reach convergence -- the two approaches spend
their computational budget differently (PISO: more work per timestep,
one timestep per point in the time history; SIMPLE: less work per outer
iteration, many outer iterations per converged result) rather than one
being strictly cheaper. Every pressure-correction pass in either family
requires solving a Poisson-type system, making
`linear-solvers.md`'s Linear Solver layer a hard dependency of
pressure-velocity coupling regardless of which algorithm is used
(`docs/architecture/icds.md` already records this as the one real
cross-layer dependency among PyFlow's six configurable numerical
components).

## References

- Issa, R.I., "Solution of the implicit discretised fluid flow equations
  by operator-splitting", *Journal of Computational Physics*, 62(1),
  1986, pp. 40-65. The original PISO algorithm.
- Patankar, S.V. and Spalding, D.B., "A calculation procedure for heat,
  mass and momentum transfer in three-dimensional parabolic flows",
  *International Journal of Heat and Mass Transfer*, 15(10), 1972, pp.
  1787-1806. The original SIMPLE algorithm.
- Van Doormaal, J.P. and Raithby, G.D., "Enhancements of the SIMPLE
  method for predicting incompressible fluid flows", *Numerical Heat
  Transfer*, 7(2), 1984, pp. 147-163. The original SIMPLEC algorithm.
- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  6 covers SIMPLE, SIMPLEC and PISO with worked derivations.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3h), against `fvm.md`
and forward-referencing `docs/handbook/physics/incompressible-flow.md`
(written later the same session, per the backlog's stated E4 order) for
the continuity/momentum equations being coupled.

Reviewed 2026-08-18: added "When the Pressure Equation Has No Unique
Solution". The entry previously described the pressure-correction equation
without noting that a domain with velocity prescribed on every boundary --
the MVP's own lid-driven cavity validation case -- produces a singular
system requiring a compatibility condition on the boundary data and
explicit null-space removal. `linear-solvers.md`, `boundary-conditions.md`
and `docs/architecture/icds.md` were updated in the same pass; this entry
is the authoritative statement and the others point here.
