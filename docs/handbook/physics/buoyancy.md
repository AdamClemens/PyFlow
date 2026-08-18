# Buoyancy

Per `docs/planning/knowledge-architecture.md` KA-014. Buoyancy and its
coupling to fluid motion, building on `docs/handbook/physics/
{incompressible-flow,density,heat-transfer}.md`.

---

## The Phenomenon

Buoyancy is the net upward (or downward) force a fluid parcel experiences
because its density differs from that of its surroundings, under
gravity. A parcel less dense than the surrounding fluid is pushed upward;
a denser parcel sinks. It is the mechanism behind natural convection --
fluid motion driven entirely by density differences (typically from
temperature or composition variation, `density.md`), with no externally
imposed flow required -- and it is the primary driving mechanism for
atmospheric circulation at the scales PyFlow's target domain concerns:
warm, humid air rising; cool, dense air sinking.

## Physical Interpretation: Archimedes' Principle, Applied Locally

Buoyancy is the fluid-dynamics expression of Archimedes' principle: the
net force on a submerged parcel is the difference between gravity acting
on the parcel's own mass and the pressure force the surrounding fluid
exerts on it (equal to the weight of fluid the parcel displaces). Where
the classical statement of the principle concerns a rigid, discrete
object in an otherwise uniform fluid, PyFlow's context needs the same
idea applied *locally and continuously* -- every infinitesimal fluid
parcel, at every point in the domain, experiences this same net force
whenever its local density differs from a reference value, which is
exactly what makes buoyancy a body-force term in the momentum equation
rather than a boundary effect.

## The Boussinesq Buoyancy Term

Under the Boussinesq approximation (`density.md`), buoyancy enters
`incompressible-flow.md`'s momentum equation through the body-force term
$\mathbf{f}$, in the form:

$$
\mathbf{f}_{\text{buoyancy}} = (\rho - \rho_0) \, \mathbf{g} \approx
-\rho_0 \, \beta \, (T - T_0) \, \mathbf{g}
$$

where $\rho_0$ and $T_0$ are reference density and temperature (typically
the domain's ambient or initial state), $\mathbf{g}$ is the gravitational
acceleration **vector, pointing downward**, and $\beta$ is the fluid's
thermal expansion coefficient,

$$
\beta = -\frac{1}{\rho}\left(\frac{\partial \rho}{\partial T}\right)_p
$$

-- how strongly density responds to a temperature change at fixed
pressure, positive for a fluid that expands on heating. For an ideal gas
it takes the particularly simple value $\beta = 1/T$ (with $T$ absolute),
so for air near room temperature $\beta \approx 1/293 \approx 3.4 \times
10^{-3}\ \mathrm{K}^{-1}$: a 10 K excess produces a density deficit of
roughly 3%, which is both small enough to justify the Boussinesq
approximation and more than enough to drive vigorous convection.

**Two sign conventions to check against before implementing this**, since
buoyancy is unusually easy to get backwards and a sign error here produces
a plausible-looking simulation running upside down:

- $\mathbf{g}$ is the *downward* vector, not a magnitude. A parcel lighter
  than its surroundings has $\rho < \rho_0$, so $(\rho - \rho_0)$ is
  negative, and multiplying a negative scalar by a downward vector gives
  an upward force. Warm fluid rises, as it must. Written instead with a
  scalar $g > 0$ and an upward unit vector $\hat{\mathbf{k}}$, the same
  term reads $-(\rho - \rho_0) g \hat{\mathbf{k}}$ -- identical physics,
  opposite-looking sign, which is exactly the confusion worth heading off.
- Only the density *deviation* appears, not $\rho$ itself, because the
  uniform part of gravity is conventionally absorbed into the pressure as
  a hydrostatic reference (`incompressible-flow.md`). The $p$ solved for
  in a Boussinesq solver is therefore the deviation from hydrostatic
  balance, not the absolute pressure -- if the full $\rho \mathbf{g}$ were
  retained, the buoyancy term and the hydrostatic pressure gradient would
  simply cancel wherever the fluid is at its reference state.

The approximation on the right substitutes a linearised temperature
dependence for the true density difference, valid whenever the
temperature (or humidity) variation driving the flow is small relative to
the reference state, exactly the regime the Boussinesq approximation
itself assumes. This is the equation that actually couples
`heat-transfer.md`'s temperature field back into the flow -- without it,
temperature is a passive scalar, transported by the flow but never
influencing it, exactly as `heat-transfer.md`'s "Coupling with Fluid
Flow" section describes.

## Coupling to Fluid Motion

Buoyancy is a genuine two-way coupling, not a one-way forcing: the
temperature (or humidity) field determines the local buoyant force, which
drives fluid motion, which in turn advects the temperature/humidity field
that produced the force in the first place (`heat-transfer.md`'s
advection mechanism). This feedback loop is what produces the
characteristic patterns of natural convection -- rising plumes of buoyant
fluid, and the compensating sinking motion of denser fluid displaced by
them -- rather than a fixed, externally prescribed flow pattern.

## Relationship to Humidity

Where temperature-driven buoyancy depends on thermal expansion, humidity-
driven buoyancy depends on humid air's lower density relative to dry air
at the same temperature (`humidity.md`) -- both act through exactly the
same momentum-equation body-force term, differing only in which field
determines the local density deviation from $\rho_0$. A fully coupled
atmospheric buoyancy term would combine both contributions (temperature
and humidity) rather than treating them as alternatives.

## Numerical Implications

Buoyancy introduces no new numerical layer of its own -- it is a
volumetric source term added directly to the momentum equation's
right-hand side, evaluated from whatever field(s) (temperature, and
later humidity) already exist as transported quantities. What it does
require is that the temperature/humidity field be evaluated at momentum's
own cell locations consistently with the variable-placement convention in
use (`docs/handbook/numerical-methods/variable-placement.md`) -- on a
collocated grid, this is direct (temperature already lives at the same
cell centres momentum does); on a staggered grid, it would require
interpolation. Buoyancy-driven flows are also frequently more numerically
demanding in a specific way: they can be significantly less diffusive/
more oscillatory than a simple imposed-flow case, since the
positive-feedback loop above can amplify small perturbations -- a
consideration for which advection scheme (`docs/handbook/
numerical-methods/advection.md`) is appropriate, though not a change to
which schemes are available.

## References

- Turner, J.S., *Buoyancy Effects in Fluids*, Cambridge University Press,
  1973. The standard comprehensive reference on buoyancy-driven flow,
  covering the Boussinesq formulation and natural-convection regimes
  directly.
- Kundu, P.K., Cohen, I.M., and Dowling, D.R., *Fluid Mechanics*, 6th
  ed., Academic Press, 2015. Ch. 4 and Ch. 13 cover the Boussinesq
  approximation's momentum-equation term and natural-convection examples.
- Wallace, J.M. and Hobbs, P.V., *Atmospheric Science: An Introductory
  Survey*, 2nd ed., Academic Press, 2006. Covers buoyancy as the driving
  mechanism for atmospheric convection specifically.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E4e), against
`incompressible-flow.md`, `density.md` and `heat-transfer.md`.

Reviewed 2026-08-18, correcting a sign. The Boussinesq buoyancy term read
$-(\rho - \rho_0)\mathbf{g} \approx \rho_0 \beta (T - T_0) \mathbf{g}$,
which is upside down for the stated meaning of $\mathbf{g}$ (the downward
gravitational acceleration vector) -- as written it would sink warm fluid.
Both sides are now correct for that convention, with the
scalar-$g$/upward-unit-vector alternative shown beside it, since that
difference is exactly what makes the sign easy to get wrong. $\beta$ is
now defined rather than only described, and the hydrostatic-reference
convention behind using the density *deviation* is stated.
