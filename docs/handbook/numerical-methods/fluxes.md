# Fluxes

Per `docs/planning/knowledge-architecture.md` KA-019. Numerical fluxes
and their role in FVM -- the concept `fvm.md`'s "Face Fluxes and
Discretisation" section introduces, treated here in its own right since
it is where FVM's advective and diffusive schemes actually plug in.

---

## Physical Flux vs. Numerical Flux

A **physical flux** is the true, continuous rate at which a quantity
crosses a surface -- for example, the true rate of mass or momentum
transport through a geometric plane in a fluid, which exists independent
of any discretisation and is exactly what the governing PDE's flux terms
represent.

A **numerical flux** is the *discrete estimate* of that physical flux at
a specific mesh face, computed from the discrete field values FVM
actually has available (cell-centred values on either side of the face,
and any stored gradients). The numerical flux is what the discretised
scheme actually uses; it is only ever an approximation to the physical
flux, and the quality of that approximation -- its order of accuracy, its
stability properties, whether it introduces spurious oscillation or
excess smoothing -- is precisely what distinguishes one flux scheme
from another.

## Face Flux

FVM's control-volume balance (`fvm.md`) requires exactly one number per
face per transported quantity: the **face flux**, the numerical flux
evaluated at that face, used with the face's outward normal and area to
convert a physical rate into the actual quantity added to or removed from
each of the two cells sharing that face. Every other concept in this
document exists to produce that one number.

A face flux for a transported scalar $\phi$ decomposes into an advective
and a diffusive part, matching the two flux terms in the integral
conservation law (`fvm.md`):

$$
F_{\text{face}} = \underbrace{(\rho \mathbf{u} \cdot \mathbf{n})_{\text{face}} \, \phi_{\text{face}} \, A_{\text{face}}}_{\text{advective}} - \underbrace{\Gamma (\nabla\phi \cdot \mathbf{n})_{\text{face}} \, A_{\text{face}}}_{\text{diffusive}}
$$

The advective part needs a face value of $\phi$ (and, separately, a
value for $\rho \mathbf{u} \cdot \mathbf{n}$, the **mass flux** below);
the diffusive part needs a face-normal gradient of $\phi$. How each is
estimated from cell-centred data is a whole scheme in its own right --
covered by `advection.md` (KA-020) and `diffusion.md` (KA-021)
respectively. This document is about the flux concept and the interface
between them, not either scheme's internal detail.

## Mass Flux

The **mass flux** through a face, $\dot{m}_{\text{face}} = (\rho
\mathbf{u} \cdot \mathbf{n})_{\text{face}} A_{\text{face}}$, deserves its
own name because it appears in *every* advective face flux (it is the
"how much fluid is moving through this face" term that every transported
quantity's advection multiplies by its own face value) and because it is
exactly the quantity the continuity equation constrains to be
divergence-free for an incompressible flow -- linking flux computation
directly to `docs/handbook/physics/incompressible-flow.md`'s continuity
equation and to `pressure-velocity-coupling.md`'s job of enforcing that
constraint. For a collocated grid, the face mass flux is also exactly
where Rhie-Chow interpolation intervenes (`variable-placement.md`) --
the interpolated face velocity used to compute mass flux is not a plain
average of the two neighbouring cell-centred velocities.

## Candidate Flux Formulations

The advective face value $\phi_{\text{face}}$ can be estimated by several
families of scheme, differing in how many neighbouring cells they use and
what accuracy/stability trade-off results:

- upwind schemes (using only the upstream cell's value);
- central schemes (linear interpolation between the two neighbours);
- higher-order/bounded schemes (QUICK, TVD variants) using a wider
  stencil to improve accuracy while limiting spurious oscillation.

`advection.md` covers this family in depth, since it is the dimension
along which PyFlow's advection scheme is explicitly configurable
(`docs/architecture/icds.md`). The diffusive face gradient has a
correspondingly narrower set of standard formulations, covered in
`diffusion.md`.

## Computational Cost

Flux evaluation happens once per face per transported field per
timestep, so its cost scales directly with mesh face count and the
number of transported fields -- the same scaling `fvm.md`'s
"Computational Considerations" section describes for FVM as a whole,
since flux evaluation *is* FVM's dominant per-timestep cost. A wider
stencil (a higher-order scheme touching more neighbouring cells) costs
more per face but not asymptotically more in face count; the real cost
driver of a wider stencil is usually the added complexity of correctly
handling it near domain boundaries and mesh irregularities, not raw
arithmetic.

## Stability and Accuracy Implications

Every flux formulation trades a version of the same tension: a low-order
scheme (upwind) is unconditionally stable but numerically diffusive
(smooths sharp gradients more than the true physics would), while a
higher-order scheme (central, QUICK) is more accurate on smooth solutions
but can produce non-physical oscillation near sharp gradients unless
specifically constructed to avoid it (the "TVD"/"bounded" schemes
`advection.md` covers exist precisely to recover boundedness without
falling back to first-order accuracy everywhere). This tension is why
flux/advection scheme choice is one of the six components PyFlow exposes
as independently configurable (`adr/ADR-003-modular-numerical-strategies.md`,
`docs/architecture/icds.md`) rather than fixed once and for all -- the
right trade-off depends on the specific flow being simulated.

## References

- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  5 develops face-flux discretisation for advection-diffusion problems
  directly.
- LeVeque, R.J., *Finite Volume Methods for Hyperbolic Problems*,
  Cambridge University Press, 2002. A rigorous treatment of numerical
  flux functions and their stability/accuracy properties, focused on the
  advective side.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3d), against `fvm.md`
and `variable-placement.md`, forward-referencing `advection.md` and
`diffusion.md` (written next in the backlog's stated E3 order).
