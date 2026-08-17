# Density

Per `docs/planning/knowledge-architecture.md` KA-012. Density as a
field/property, and its physical role once
`docs/handbook/physics/incompressible-flow.md`'s constant-density
assumption is relaxed.

---

## Density as a Field, Not Just a Constant

`incompressible-flow.md` treats density $\rho$ as a fixed constant --
the assumption that makes the continuity equation reduce to a pure
divergence-free constraint on velocity. In reality, a fluid's density
depends on its local state: temperature, pressure, and composition
(dissolved or suspended species, humidity) all affect it. Treating
density as its own transported field -- $\rho(\mathbf{x}, t)$, varying in
space and time -- is the step that reconnects PyFlow's simulation to that
reality, and is what `docs/handbook/physics/buoyancy.md` and
`docs/implementation/upgrade-paths.md`'s "Physics" entry (density/
buoyancy as the step after heat) both build on.

## Physical Role

Density enters the governing equations in two distinct places, and it is
worth keeping them separate:

- **Continuity.** The full, compressible continuity equation is
  $\partial\rho/\partial t + \nabla \cdot (\rho \mathbf{u}) = 0$ --
  density itself obeys a conservation law, transported by the flow the
  same way any other field is. `incompressible-flow.md`'s divergence-free
  constraint is the special case where $\rho$ is constant and can be
  factored out; a variable-density flow generally does not reduce this
  way.
- **Momentum (buoyancy).** Even when density variation is small enough
  that its effect on mass conservation can still be neglected (see
  "Boussinesq Approximation" below), density variation still matters
  enormously for the momentum equation's body-force term, because
  gravity acts on mass: a parcel of fluid less dense than its
  surroundings experiences a net upward force, and vice versa. This is
  buoyancy, covered in its own entry
  (`docs/handbook/physics/buoyancy.md`) since it deserves treatment in
  its own right; this document covers only density itself as a field.

## The Boussinesq Approximation

A common and physically well-justified simplification -- not assumed by
this document to be PyFlow's eventual implementation choice, but worth
recording as the standard bridge between the constant-density and
fully-compressible pictures -- treats density variation as negligible
*everywhere except* in the gravity term of the momentum equation, where
even a small fractional density difference produces a physically
significant buoyant force. Under this approximation, the flow remains
effectively incompressible (continuity stays divergence-free) while still
capturing buoyancy-driven motion -- exactly the regime natural-convection
and atmospheric flows (PyFlow's ultimate target domain) typically operate
in, since temperature-driven density variations in air are usually a
small fraction of the total density even when the resulting buoyant
motion is significant.

## Density's Physical Determinants

What actually determines density, for the fluids PyFlow's scope
concerns, are:

- **Temperature** -- for most fluids, density decreases as temperature
  increases (thermal expansion), the mechanism underlying
  temperature-driven buoyancy and natural convection.
- **Composition** -- humid air is *less* dense than dry air at the same
  temperature and pressure, because water vapour's molecular weight is
  lower than that of the nitrogen/oxygen it displaces -- the physical
  link `docs/handbook/physics/humidity.md` develops.
- **Pressure** -- for a genuinely compressible flow, density depends
  directly on pressure through an equation of state; outside PyFlow's
  current incompressible/Boussinesq scope, but the reason "compressible
  flow" and "variable density" are related but not identical upgrade
  directions (`docs/implementation/upgrade-paths.md`'s "Physics Scope"
  entry).

## Relationship to Other Phenomena

Density is the physical bridge between three other entries in this
handbook: it is what `buoyancy.md` is a body-force consequence of, it is
what makes `humidity.md`'s species transport dynamically significant
rather than a passive tracer, and it is what a future compressible-flow
capability would need to solve for directly via an equation of state
rather than treating as an input.

## Numerical Implications

Under the Boussinesq approximation, density enters the simulation only
as a coefficient in the momentum equation's buoyancy term, computed from
temperature (and, later, humidity) at each cell -- it does not itself
need a separate advection-diffusion solve distinct from whatever field
(temperature, humidity) actually determines it. A fully variable-density
treatment, by contrast, would need density transported like any other
field (`docs/handbook/numerical-methods/advection.md`,
`diffusion.md`) and would reopen the constant-density assumption
`incompressible-flow.md`'s continuity equation relies on -- a
significantly larger architectural change than adding a passive scalar,
which is why the Boussinesq approximation is the natural first upgrade
step rather than full compressibility.

## References

- Kundu, P.K., Cohen, I.M., and Dowling, D.R., *Fluid Mechanics*, 6th
  ed., Academic Press, 2015. Ch. 4 covers the general (variable-density)
  continuity equation this document's "Physical Role" section derives
  the incompressible special case from.
- Boussinesq, J., *Théorie Analytique de la Chaleur*, Vol. 2,
  Gauthier-Villars, 1903. The original approximation, still in standard
  use for buoyancy-driven flow.
- Turner, J.S., *Buoyancy Effects in Fluids*, Cambridge University Press,
  1973. Ch. 1 gives a clear physical derivation of the Boussinesq
  approximation and when it is (and is not) valid.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E4c), against
`incompressible-flow.md`, forward-referencing `buoyancy.md` and
`humidity.md` (written later the same session, per the backlog's stated
E4 order).
