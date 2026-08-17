# Heat Transfer

Per `docs/planning/knowledge-architecture.md` KA-011. Heat transport as a
future additional field/process, building on
`docs/handbook/physics/incompressible-flow.md`.

---

## Temperature as a Transported Field

Temperature $T$ behaves, mathematically, exactly like any other scalar
field PyFlow's field-centric architecture transports
(`prompts/global/project.md`): it is advected by the flow's velocity and
diffuses down its own gradient, the same two mechanisms
`docs/handbook/numerical-methods/advection.md` and `diffusion.md` already
describe in general. This is precisely why PyFlow's architecture treats
temperature (and, later, humidity/species concentration,
`docs/handbook/physics/humidity.md`) as instances of a common transported
field, rather than requiring bespoke transport machinery per physical
quantity.

## Heat Transport Mechanisms

Two distinct physical mechanisms move heat through a fluid, corresponding
directly to advection and diffusion:

- **Convection** -- heat carried along by the bulk motion of the fluid
  itself. This is advection applied to temperature: exactly the same
  mechanism transporting momentum also transports heat, at the same flow
  velocity $\mathbf{u}$.
- **Conduction** -- heat diffusing down a temperature gradient at the
  molecular scale, independent of bulk fluid motion (present even in a
  fluid at rest, or in a solid). This is diffusion applied to
  temperature, governed by Fourier's law, $\mathbf{q} = -k \nabla T$,
  where $k$ is thermal conductivity and $\mathbf{q}$ the heat flux.

(A third mechanism, **radiation**, transports heat via electromagnetic
waves without requiring an intervening medium at all -- physically real,
but outside the advection/diffusion framework the other two mechanisms
share, and not part of PyFlow's currently planned scope.)

## Governing Equation

Temperature is governed by an advection-diffusion equation with the same
structure as the general conservation law `docs/handbook/
numerical-methods/fvm.md` introduces:

$$
\rho c_p \left( \frac{\partial T}{\partial t} + \mathbf{u} \cdot \nabla T
\right) = k \nabla^2 T + \dot{q}
$$

where $c_p$ is specific heat capacity (energy needed to raise a unit mass
by one degree), $k \nabla^2 T$ is conductive diffusion (Fourier's law
combined with energy conservation), and $\dot{q}$ is any volumetric heat
source or sink (below). Dividing through by $\rho c_p$ recovers exactly
the advection-diffusion form `fvm.md`'s general conservation equation
already covers, with **thermal diffusivity** $\alpha = k / (\rho c_p)$ in
place of a generic diffusivity $\Gamma$ -- confirming that temperature
transport needs no new numerical machinery beyond what
`docs/handbook/numerical-methods/advection.md` and `diffusion.md` already
provide, only a different physical coefficient.

## Sources and Sinks

$\dot{q}$ represents any volumetric heating or cooling not otherwise
captured by advection/conduction across the domain's boundaries -- for
example, a heat source embedded within the fluid, viscous dissipation
(kinetic energy converting to heat through friction, generally negligible
at the flow speeds PyFlow's MVP targets), or a chemical/phase-change
process. Whether a specific source is significant enough to model depends
on the specific simulation being built, not on this document, which
records only that the governing equation has a term for it.

## Coupling with Fluid Flow

Heat transport couples to the flow in both directions:

- **Flow → temperature:** the flow's velocity field $\mathbf{u}$ directly
  advects temperature, as above -- a one-way coupling if density and
  viscosity are treated as temperature-independent.
- **Temperature → flow:** in general, a fluid's density depends on its
  temperature, which -- once density is allowed to vary
  (`docs/handbook/physics/density.md`) -- feeds back into the momentum
  equation's body-force term as buoyancy
  (`docs/handbook/physics/buoyancy.md`). Under the constant-density
  assumption `incompressible-flow.md` states, this feedback is absent by
  construction: temperature is a **passive scalar**, transported by the
  flow but not affecting it. Whether temperature is passive or coupled
  back into the flow is precisely the assumption `buoyancy.md`'s
  Boussinesq treatment describes relaxing.

## Numerical Implications

Because temperature transport shares its governing equation's structure
exactly with the general advection-diffusion form, it requires no new
numerical layer -- it is an additional instance of the existing Advection
and Diffusion layers (`docs/architecture/engine.md`) applied to a new
field, with thermal diffusivity in place of momentum's kinematic
viscosity or a species' diffusion coefficient. The one genuinely new
numerical consideration is the **Robin boundary condition**
(`docs/handbook/numerical-methods/boundary-conditions.md`), which
temperature commonly needs where momentum typically does not -- a
convective heat-transfer boundary (heat flux proportional to the
difference between the boundary and an external ambient temperature) is
a Robin condition in the sense that document already defines, not a new
boundary-condition category.

## Extension Requirements

Adding heat transport to PyFlow requires: a temperature `Field` (already
generic infrastructure, per `docs/handbook/numerical-methods/
variable-placement.md`), thermal diffusivity as a material property,
Robin boundary condition support (the one genuinely new piece), and --
only if buoyancy coupling is wanted -- the density/momentum feedback
`buoyancy.md` describes. None of this requires new advection or diffusion
*schemes*; the existing configurable schemes
(`docs/architecture/icds.md`) apply directly.

## References

- Incropera, F.P., DeWitt, D.P., Bergman, T.L., and Lavine, A.S.,
  *Fundamentals of Heat and Mass Transfer*, 7th ed., Wiley, 2011. The
  standard textbook treatment of conduction, convection, and the coupled
  advection-diffusion energy equation.
- Kundu, P.K., Cohen, I.M., and Dowling, D.R., *Fluid Mechanics*, 6th
  ed., Academic Press, 2015. Ch. 4 covers the energy equation's
  derivation alongside continuity and momentum, in the same notation as
  `incompressible-flow.md`.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E4b), against
`incompressible-flow.md`.
