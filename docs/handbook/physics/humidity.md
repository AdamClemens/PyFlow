# Humidity and Species Transport

Per `docs/planning/knowledge-architecture.md` KA-013. Humidity and
species concentration as transported fields, building on
`docs/handbook/physics/heat-transfer.md`.

---

## Humidity as a Species Transport Problem

Humidity -- the concentration of water vapour in air -- is a specific
instance of a more general phenomenon: **species transport**, the
movement of one chemical or physical constituent (a species) through a
fluid, alongside and distinct from the fluid's bulk motion. Water vapour
in air is the species PyFlow's atmospheric target domain cares about
directly, but the transport mechanics below are general -- the same
treatment covers any passive or near-passive species a future capability
might need.

## Governing Equation

Like temperature (`heat-transfer.md`), a species concentration $Y$
(commonly expressed as a mass fraction, or as **specific humidity** for
water vapour specifically -- mass of vapour per unit mass of moist air)
obeys an advection-diffusion equation of exactly the same structure:

$$
\frac{\partial Y}{\partial t} + \mathbf{u} \cdot \nabla Y = D \nabla^2 Y
+ \dot{S}
$$

where $D$ is the species' molecular diffusivity (mass diffusivity, the
species-transport analogue of thermal diffusivity in `heat-transfer.md`'s
equation) and $\dot{S}$ a source/sink term -- for water vapour, most
significantly evaporation (a source, where liquid water is present) and
condensation (a sink, the process `cloud-formation.md` covers in detail).
As with temperature, this confirms species transport needs no new
numerical machinery: it is another instance of the Advection and
Diffusion layers (`docs/architecture/engine.md`) applied to a new field,
with a species-specific diffusivity in place of momentum's viscosity or
temperature's thermal diffusivity.

## Relationship to Temperature

Humidity and temperature are not independent in the atmosphere: the
maximum water vapour concentration air can hold before condensing (its
**saturation** point) rises steeply with temperature (the Clausius–
Clapeyron relation) -- warm air can hold much more water vapour than cold
air at the same relative humidity. This is why `heat-transfer.md`
(temperature) is a stated dependency of this entry rather than the two
being independent additions: humidity's physically interesting behaviour
(condensation, `cloud-formation.md`) is inseparable from the temperature
field it is transported alongside.

## Relationship to Density

Water vapour is less dense than the dry air it displaces at the same
temperature and pressure (its molecular weight, ≈18 g/mol, is lower than
dry air's ≈29 g/mol average) -- humid air is measurably less dense than
dry air at the same temperature and pressure, not more, which is
counter-intuitive relative to everyday intuition about "heavy," humid
air. This is the mechanism `docs/handbook/physics/density.md` names
under "Density's Physical Determinants," and it is what makes humidity
dynamically significant rather than a purely passive tracer once density
is allowed to feed back into the momentum equation
(`docs/handbook/physics/buoyancy.md`) -- moist, buoyant air rising is a
real atmospheric mechanism this coupling represents.

## Numerical Implications

Identical to temperature's (`heat-transfer.md`'s "Numerical
Implications"): humidity needs a `Field`, a diffusivity, and whichever
boundary conditions the specific scenario needs (a fixed-humidity inlet
is Dirichlet; an impermeable wall is a zero-flux Neumann condition) --
all already-general infrastructure. The one genuinely new numerical
consideration specific to humidity, rather than shared with temperature,
is condensation as a **coupled, non-linear source term**: unlike a
typical fixed or externally-imposed source, condensation depends on the
current state of both the humidity and temperature fields simultaneously
(whether the local state exceeds saturation) -- `cloud-formation.md`
covers this coupling directly, since it is the process that makes
humidity transport atmospherically interesting rather than a simple
passive-scalar exercise.

## Extension Requirements

Adding humidity transport requires: a humidity `Field` (existing generic
infrastructure), a water-vapour mass diffusivity, and -- only once
temperature is already transported (`heat-transfer.md`) -- the
saturation relationship needed to make evaporation/condensation
physically meaningful. Without temperature already present, humidity can
still be added as a purely passive scalar (transported, but with no
condensation physics), which is a reasonable, smaller intermediate step.

## References

- Bird, R.B., Stewart, W.E., and Lightfoot, E.N., *Transport Phenomena*,
  2nd ed., Wiley, 2007. Ch. 17-19 develop the general species-transport
  (advection-diffusion-reaction) equation this document specialises to
  humidity.
- Wallace, J.M. and Hobbs, P.V., *Atmospheric Science: An Introductory
  Survey*, 2nd ed., Academic Press, 2006. Ch. 3 covers atmospheric
  humidity, specific humidity, and the temperature-dependence of
  saturation directly.
- Rogers, R.R. and Yau, M.K., *A Short Course in Cloud Physics*, 3rd ed.,
  Butterworth-Heinemann, 1989. Ch. 2 covers the thermodynamics of moist
  air and the Clausius–Clapeyron relation in the atmospheric context.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E4d), against
`heat-transfer.md` and `density.md`, forward-referencing
`buoyancy.md` and `cloud-formation.md` (written later the same session,
per the backlog's stated E4 order).
