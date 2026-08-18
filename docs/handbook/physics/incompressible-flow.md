# Incompressible Flow

Per `docs/planning/knowledge-architecture.md` KA-010. The physical model
underlying PyFlow's initial CFD prototype (`docs/implementation/mvp.md`).

See `README.md` in this directory for what a Physics Handbook entry
should generally contain. This entry deliberately separates the physics
(this document) from PyFlow's specific numerical treatment of it
(`docs/handbook/numerical-methods/pressure-velocity-coupling.md`,
`docs/architecture/engine.md`) -- an implementation choice like "PISO" is
not a physical fact and does not belong here.

---

## The Phenomenon

A fluid's motion is governed by the conservation of mass and momentum.
**Incompressible flow** is the regime in which the fluid's density can be
treated as constant, both in space and following a fluid parcel through
time -- true for liquids under essentially all conditions relevant to
PyFlow's scope, and true for gases (including air) when flow speeds are
small relative to the speed of sound (conventionally, Mach number below
roughly 0.3). The Mach criterion covers density change caused by
*pressure*, and it is the binding one for the MVP; it is not the only way
a gas's density can vary, since heating and composition change it too at
any flow speed. That is precisely the assumption `density.md` and
`buoyancy.md` relax, and the reason those entries exist as separate
extensions rather than as corrections to this one. This is precisely the regime PyFlow's MVP targets: an
air-current simulation at everyday speeds, far from the compressible
regime where density variation due to pressure becomes significant.

## Assumptions

- **Constant density.** $\rho$ is treated as a fixed constant, not a
  field the momentum/continuity equations solve for. (PyFlow's later
  capability levels introduce density as its own transported field,
  `docs/handbook/physics/density.md`, for buoyancy-driven flows where
  this assumption is deliberately relaxed -- see that entry for how the
  two pictures relate.)
- **Newtonian fluid.** Viscous stress is proportional to the local rate
  of strain, with a constant viscosity coefficient -- true for air and
  water under the conditions PyFlow targets, though not true for all
  fluids in general (e.g. many polymers, blood).
- **Continuum hypothesis.** The fluid is treated as a continuous medium
  describable by field quantities (velocity, pressure) at every point,
  rather than as discrete molecules -- valid at the length scales any
  CFD simulation operates at.

## Conservation Equations

Incompressible flow is governed by two coupled equations expressing
conservation of mass and momentum for a Newtonian fluid.

### Continuity (Conservation of Mass)

For a constant-density fluid, conservation of mass reduces to a purely
kinematic constraint on the velocity field:

$$
\nabla \cdot \mathbf{u} = 0
$$

This is the **incompressibility constraint**: the velocity field must be
**divergence-free** everywhere -- no net flow can converge into or
diverge out of any infinitesimal volume, since with constant density
there is nowhere for mass to accumulate or deplete. (The general,
compressible continuity equation, $\partial\rho/\partial t + \nabla \cdot
(\rho \mathbf{u}) = 0$, reduces to exactly this when $\rho$ is constant
and factored out.)

### Momentum (Navier–Stokes)

$$
\rho \left( \frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot
\nabla) \mathbf{u} \right) = -\nabla p + \mu \nabla^2 \mathbf{u} +
\mathbf{f}
$$

Reading the terms left to right: the rate of change of momentum
following a fluid parcel (the material derivative of velocity, the
left-hand side's two terms together) equals the net force per unit
volume acting on it -- the pressure gradient force ($-\nabla p$, fluid
accelerates from high to low pressure), viscous diffusion of momentum
($\mu \nabla^2 \mathbf{u}$, $\mu$ the dynamic viscosity), and any other
body force $\mathbf{f}$ (gravity, and -- once density becomes a field --
buoyancy; `docs/handbook/physics/buoyancy.md`).

The viscous term takes this compact Laplacian form only because two of
the assumptions above are in force together. The general Newtonian
viscous term is the divergence of the stress tensor, $\nabla \cdot
\left[\mu (\nabla \mathbf{u} + \nabla \mathbf{u}^{\mathsf{T}})\right]$;
it collapses to $\mu \nabla^2 \mathbf{u}$ when $\mu$ is uniform (so it can
be taken outside the divergence) *and* $\nabla \cdot \mathbf{u} = 0$ (so
the transpose term vanishes). A future variable-viscosity or
variable-density model would have to restore the general form rather than
simply changing the value of $\mu$ -- worth recording, since the
simplified term is easy to mistake for the definition of viscous
transport rather than a special case of it.

## Pressure and Its Relationship to Velocity

Pressure in an incompressible flow plays a fundamentally different role
than in a compressible one: it is not related to density or temperature
by any equation of state, and has no evolution equation of its own. It
exists purely to **enforce** the incompressibility constraint --
instantaneously adjusting throughout the domain so that whatever velocity
field the momentum equation would otherwise produce is corrected to
satisfy $\nabla \cdot \mathbf{u} = 0$. This is why pressure is best
understood as a Lagrange multiplier for the divergence-free constraint,
not as a directly transported physical quantity the way velocity or
temperature are, and it is exactly the property
`docs/handbook/numerical-methods/pressure-velocity-coupling.md` (KA-023)
exists to explain the numerical treatment of.

One physical consequence of that role is worth stating explicitly,
because it has direct numerical teeth: since only $\nabla p$ appears
anywhere in the equations, **incompressible pressure is physically
meaningful only up to an additive constant** unless some boundary fixes
its level. A closed domain driven entirely by prescribed velocities has
no such boundary, so its pressure field is determined only as a
difference from cell to cell -- which is why the discrete pressure system
such a case produces is singular and needs explicit handling
(`docs/handbook/numerical-methods/pressure-velocity-coupling.md`,
`docs/handbook/numerical-methods/boundary-conditions.md`). Related, and
often confused with it: what appears as $p$ in a constant-density solver
is frequently the *kinematic* pressure $p/\rho$, and gravity is often
absorbed into it as a hydrostatic reference rather than carried in
$\mathbf{f}$ (`docs/handbook/physics/buoyancy.md`). Neither is a physical
statement about the fluid; both are conventions a reader comparing this
document with an implementation needs to have been told about.

## Incompressibility Constraint: Implications for Numerical Solution

The continuity equation contains no time-derivative term for
pressure -- unlike a genuinely evolving field, pressure cannot simply be
advanced forward in time the way velocity or temperature can. This is
the central numerical difficulty incompressible-flow solvers exist to
resolve, and it is why pressure-velocity coupling
(`docs/handbook/numerical-methods/pressure-velocity-coupling.md`) is a
distinct numerical layer in its own right
(`docs/architecture/engine.md`), rather than something that falls out
automatically from discretising the momentum equation alone. It is also
why the choice of where velocity and pressure are stored relative to the
mesh (`docs/handbook/numerical-methods/variable-placement.md`) has real
numerical consequences specific to incompressible flow -- the
checkerboard pressure problem that entry describes arises directly from
pressure's constraint-enforcing role having no independent equation to
anchor it.

## Relationship to PyFlow's Other Physics

This document describes the base incompressible-flow model; every later
physics entry in this handbook extends it by adding a transported field
that couples back into the momentum equation through the body-force term
$\mathbf{f}$ or through density itself:
`docs/handbook/physics/heat-transfer.md` (temperature as a transported
field), `density.md` (relaxing the constant-density assumption for
buoyancy-driven flows), `humidity.md` (species transport), and
`buoyancy.md` (how density variation feeds back into $\mathbf{f}$). None
of these change the continuity/momentum equations above; they add to
what $\mathbf{f}$ contains and, eventually, relax which quantities are
held constant.

## References

- Kundu, P.K., Cohen, I.M., and Dowling, D.R., *Fluid Mechanics*, 6th
  ed., Academic Press, 2015. Ch. 4 and Ch. 9 derive the continuity and
  Navier–Stokes equations and the incompressible limit directly.
- Batchelor, G.K., *An Introduction to Fluid Dynamics*, Cambridge
  University Press, 1967. A classic, rigorous treatment of the governing
  equations and the physical assumptions behind them.
- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  3 presents the governing equations specifically in the context that
  motivates their FVM discretisation.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E4a), the first physics
handbook entry -- written first per the backlog's own ordering, since it
is the MVP's physical model and several numerical-methods entries
(`pressure-velocity-coupling.md`, `boundary-conditions.md`) already
forward-reference it.

Reviewed 2026-08-18: the viscous term's Laplacian form is now stated as a
consequence of constant $\mu$ *and* incompressibility rather than as the
definition of viscous transport; pressure's determination only up to an
additive constant is stated, since it is the physical origin of the
singular discrete system the numerical entries handle; and the Mach-0.3
criterion is scoped to pressure-driven density change, which is what it
actually bounds.
