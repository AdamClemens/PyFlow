# Time Integration

Per `docs/planning/knowledge-architecture.md` KA-022. Explicit and
implicit time integration, and the conceptual upgrade path between them.

Corresponds to `docs/architecture/engine.md`'s "Time Integration" layer:
advancing every transported field's state forward by one timestep, given
the time derivative the other layers (advection, diffusion, sources)
compute for the current state.

---

## The Problem

Once the spatial discretisation (FVM, `fvm.md`) has turned the governing
PDE into a large system of ordinary differential equations in time -- one
per cell, per transported field -- time integration is the separate
question of how to advance that system from one timestep to the next.
This document is about that ODE-in-time problem specifically; it does not
depend on which spatial scheme produced the derivative being integrated.

## Explicit Integration

An explicit scheme computes the next timestep's state using only
already-known information -- the current (and, for multi-stage schemes,
intermediate) state's time derivative -- so each cell's update can be
computed independently and directly, with no system of equations to
solve.

**Stability -- the CFL condition:** explicit schemes are only
*conditionally* stable: the timestep must be small enough that
information cannot propagate more than roughly one cell width per step,
formalised as the **Courant-Friedrichs-Lewy (CFL) condition**,
$\text{CFL} = \frac{u \, \Delta t}{\Delta x} \leq \text{CFL}_{\max}$,
where $\text{CFL}_{\max}$ depends on the specific scheme. Diffusion
imposes a comparably restrictive, but distinct, limit that scales as
$\Delta t \propto (\Delta x)^2$ rather than linearly
(`diffusion.md`'s "Stability" section) -- for fine meshes, the diffusive
limit typically dominates. In a real solver both limits apply at once and
the timestep must respect the smaller of the two.

**$\text{CFL}_{\max}$ is a property of the time integrator and the
spatial scheme *jointly*, never of either alone.** The clearest
illustration is also a trap worth knowing about before walking into it:
forward Euler combined with central-difference advection is unstable at
*every* timestep, because central differencing of pure advection produces
eigenvalues on the imaginary axis and forward Euler's stability region
touches that axis only at the origin. The same spatial scheme integrated
with RK4 is stable up to roughly $\text{CFL} \approx 2.8$, since RK4's
stability region does contain a segment of the imaginary axis. This
matters directly to PyFlow: `docs/implementation/upgrade-paths.md` lists
Euler and RK2 as *simpler predecessors* of RK4 on the Time Integration
path and central difference as a *successor* to upwind on the Advection
path, so the two paths must not be read as independently traversable in
either direction. Moving one layer down while the other has moved up is
exactly the advection/time-integration interaction
`adr/ADR-003-modular-numerical-strategies.md`'s Negative consequences
warn about, and the pairing above is the concrete instance of it.

**Computational cost per step:** low -- no linear system to assemble or
solve, just a direct evaluation of the derivative and an update. The cost
that explicit integration pays instead is in the *number* of steps
required, since the stability limit forces $\Delta t$ to shrink as the
mesh is refined.

**Memory:** low -- only the current state (and, for a multi-stage
scheme, its intermediate stages) need to be held; no system matrix.

**Code complexity:** low -- an explicit scheme is a direct formula
applied cell-by-cell, with no linear-solver dependency.

## RK4 (Fourth-Order Runge-Kutta)

RK4 is a four-stage explicit scheme: it evaluates the time derivative at
the current state and at three successively refined intermediate
estimates within the timestep, then combines all four evaluations with
fixed weights to produce a step that is fourth-order accurate in time --
substantially more accurate per step than a simple first-order Euler
step, at the cost of four derivative evaluations instead of one.

RK4 is PyFlow's MVP choice (`docs/implementation/mvp.md`). It stays
firmly on the explicit side of this document's central trade-off (still
subject to the CFL/diffusive stability limits above, still no linear
system of its own), but its higher formal accuracy means a given error
tolerance can be met with a larger timestep than a lower-order explicit
scheme would allow -- a meaningful advantage within the explicit family,
even though it does not remove the fundamental conditional-stability
limit that motivates implicit integration in the first place.

**RK4's fourth-order accuracy is an accuracy bound for the ODE system it
is handed, not a promise about the finished incompressible solver.** Two
things cap the overall order independently of the integrator. First, the
spatial discretisation: with first-order upwind advection
(`advection.md`), the MVP's overall solution error is dominated by the
spatial first-order term long before the temporal fourth-order one
matters. Second, and less obvious, the pressure-velocity coupling: PISO
(`pressure-velocity-coupling.md`) advances momentum and then projects the
result onto a divergence-free field as a separate operation, and that
operator splitting introduces a temporal error of its own that a
higher-order integrator does not remove. Combining RK4 with a
predict-correct pressure coupling in the straightforward way therefore
yields a scheme whose observed temporal order is well below four. This is
not an argument against RK4 -- it is the standard situation for
projection-type incompressible solvers, and it is worth stating here so
that a future measured convergence rate is read as expected behaviour
rather than as a bug.

## Implicit Integration

An implicit scheme evaluates the time derivative (at least partly) using
the *next*, not-yet-known state -- which means the next state can no
longer be computed directly; instead a (generally large, sparse) system
of algebraic equations must be assembled and solved every timestep, using
the linear solvers `linear-solvers.md` describes.

**Stability:** the defining advantage -- many implicit schemes are
**unconditionally stable**, meaning there is no CFL-type limit on
timestep size for stability's sake (accuracy still bounds how large a
timestep is *useful*, but not how large one can be without the solution
diverging). This is what makes implicit integration attractive for stiff
problems or fine meshes, where an explicit scheme's stability limit would
force an impractically small timestep.

**Computational cost per step:** substantially higher -- assembling and
solving a linear (or, for a nonlinear problem, an outer-iterated
nonlinear) system every timestep costs far more than a direct explicit
update, though this can be more than offset by taking many fewer, larger
timesteps overall.

**Memory:** higher -- the system matrix (or enough information to apply
it, for a matrix-free solver) must be held, in addition to the state
itself.

**Code complexity:** substantially higher -- requires a working linear
solver, and typically some form of matrix assembly, as a genuine
dependency of the time integrator itself, not just of the pressure
correction step already needed for pressure-velocity coupling.

## Explicit vs. Implicit: The Trade-Off Summarised

|                        | Explicit (RK4)                | Implicit                          |
| ---------------------- | ------------------------------ | ---------------------------------- |
| Stability               | Conditional (CFL/diffusive limit) | Often unconditional               |
| Cost per step            | Low                             | High (system solve)               |
| Steps needed             | Many (small $\Delta t$)         | Few (large $\Delta t$ possible)    |
| Memory                   | Low                              | Higher (system matrix)             |
| Code/dependency complexity | Low                            | High (needs a linear solver)       |

Neither is unconditionally cheaper -- the right choice depends on whether
the stability-limited timestep an explicit scheme requires is already
small relative to the accuracy the simulation needs (in which case
explicit's low per-step cost wins) or artificially small relative to it
(in which case implicit's ability to take much larger steps wins despite
each step costing more).

## Future Implicit Methods

`docs/implementation/upgrade-paths.md`'s "Time Integration" entry: Euler
→ RK2 → RK4 → adaptive RK → implicit. PyFlow's path stays within the
explicit family through progressively higher-order, and eventually
adaptive-timestep, schemes before implicit integration becomes relevant
-- consistent with the MVP's own priority of validating the full engine
architecture with the simplest reliable scheme first
(`docs/engineering-principles.md` P-018), and with implicit integration's
real cost: it introduces the Linear Solver layer as a hard runtime
dependency of time integration itself, not merely of pressure-velocity
coupling as in the MVP.

## References

- Butcher, J.C., *Numerical Methods for Ordinary Differential
  Equations*, 3rd ed., Wiley, 2016. The standard reference for
  Runge-Kutta methods, their order conditions, and stability regions.
- Ferziger, J.H., Perić, M., and Street, R.L., *Computational Methods for
  Fluid Dynamics*, 4th ed., Springer, 2020. Ch. 6 covers explicit and
  implicit time integration for CFD specifically, including the CFL
  condition's derivation.
- Courant, R., Friedrichs, K., and Lewy, H., "Über die partiellen
  Differenzengleichungen der mathematischen Physik", *Mathematische
  Annalen*, 100(1), 1928, pp. 32-74. The original CFL condition.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3g), against `fvm.md`
and `diffusion.md`.

Reviewed 2026-08-18, adding two things a reader would otherwise meet
first as a bug. $\text{CFL}_{\max}$ is now stated as a joint property of
integrator and spatial scheme, with the forward-Euler/central-difference
pairing (unstable at every timestep) as the concrete case -- directly
relevant because `docs/implementation/upgrade-paths.md` lists Euler below
RK4 and central difference above upwind, so the two paths must not be
traversed independently. And RK4's fourth-order claim is now scoped to the
ODE system it is handed, with the spatial and operator-splitting caps on
the finished solver's observed order stated;
`docs/architecture/icds.md`'s Time Integrator ICD carries the same
caveat.
