# Diffusion

Per `docs/planning/knowledge-architecture.md` KA-021. Diffusion
discretisation -- how the diffusive part of a face flux (`fluxes.md`) is
estimated from cell-centred field values.

Corresponds to `docs/architecture/engine.md`'s "Diffusion" layer and
`docs/architecture/icds.md`'s Diffusion ICD.

---

## Physical Diffusion

Diffusion transports a quantity down its own gradient -- viscous momentum
diffusion, thermal conduction, or species diffusion are all instances of
the same mathematical form, $\text{flux} = -\Gamma \nabla \phi$ for a
diffusion coefficient $\Gamma$. Which coefficient depends on which form
of the transport equation $\phi$ is written in, and the two are easy to
mix up: in `fvm.md`'s density-weighted convention $\Gamma$ is dynamic
viscosity $\mu$ for momentum, $k/c_p$ for temperature, and $\rho D$ for a
species; divide the equation through by a constant $\rho$ and the same
symbol becomes the ordinary kinematic diffusivity -- kinematic viscosity
$\nu$, thermal diffusivity $\alpha = k/(\rho c_p)$, mass diffusivity $D$.
The physical laws underneath are Newton's for viscous stress, Fourier's
$\mathbf{q} = -k\nabla T$ for heat, and Fick's for species. Unlike
advection, diffusion
has no directionality tied to a flow velocity -- it always acts to smooth
out a gradient, regardless of which way the fluid is moving, which is
why diffusion discretisation does not face the same
upstream/downstream-weighting question advection does.

## Gradient Approximation

The diffusive face flux needs the field's **gradient normal to the
face**, $(\nabla\phi \cdot \mathbf{n})_{\text{face}}$ -- how fast $\phi$
is changing in the direction crossing the face, evaluated at the face
itself. Because $\phi$ is only known at cell centres, this gradient must
be approximated from the cell-centred values on either side of the face
(and, for non-orthogonal corrections below, from neighbouring cells'
gradients too).

## Central Differencing

On an **orthogonal** mesh -- one where the line connecting two
neighbouring cell centroids is parallel to the face normal separating
them, true by construction for a uniform Cartesian mesh -- the
face-normal gradient is simply the difference between the two
cell-centred values divided by the distance between their centroids:

$$
(\nabla\phi \cdot \mathbf{n})_{\text{face}} \approx
\frac{\phi_{\text{neighbour}} - \phi_{\text{owner}}}{d}
$$

where $d$ is the distance between the two cell centroids. This is
**second-order accurate** when the face additionally lies midway between
those centroids -- true on a uniform mesh, where the difference quotient
is a centred one about the face itself. On a graded (orthogonal but
non-uniform) mesh the same expression remains a legitimate gradient
estimate but is no longer centred on the face, and its formal order
drops. It is PyFlow's MVP choice (`docs/implementation/mvp.md`), exactly
matched to the MVP's uniform Cartesian mesh, where both conditions the
scheme's second-order accuracy relies on -- orthogonality and a face
midway between centroids -- are exactly satisfied rather than merely
approximated.

## Non-Orthogonal Considerations

**Non-orthogonality and non-uniformity are different defects, and only the
first needs the correction below.** A Cartesian mesh with graded (varying)
spacing is still perfectly orthogonal: the centroid-to-centroid vector
stays parallel to the face normal, and only the *centredness* of the
difference quotient is lost, as noted above. Non-orthogonality is the
distinct situation -- generic on an unstructured mesh, and on any mesh
whose cells are skewed or whose faces are not perpendicular to the line
joining the centroids they separate -- where that parallelism itself
fails. There, the simple central-difference formula above becomes not
merely lower-order but wrong in kind, because the difference quotient
approximates the gradient in the *direction between the centroids*, not
the face-normal direction the flux actually needs.

The standard remedy decomposes the face-normal gradient into an
**orthogonal contribution** (computed the same way as above, along the
direction that *is* available directly) and a **non-orthogonal
correction** (using cell-centred gradient estimates, themselves
reconstructed from surrounding cell values, to account for the remaining
misalignment). This correction is what the MVP's *Cartesian* mesh choice
makes unnecessary (`docs/implementation/mvp.md`) -- orthogonality is the
property that buys it, uniformity being what buys the second-order
accuracy above -- and exactly what the Mesh layer's own upgrade
path (`docs/implementation/upgrade-paths.md`) reintroduces the moment the
mesh generalises beyond it.

## Accuracy

Central differencing is second-order accurate on a uniform orthogonal
mesh, and this accuracy is not in tension with boundedness the way
advection's
central-difference scheme is (`advection.md`) -- diffusion's physical
effect is itself smoothing, so a central-difference diffusion scheme does
not introduce the kind of spurious oscillation a central-difference
*advection* scheme can. This is why diffusion discretisation has
comparatively few competing schemes relative to advection's wide family
-- the accuracy/boundedness tension that motivates advection's TVD/WENO
schemes largely does not apply here.

## Stability

An explicit treatment of diffusion (updating a field using the diffusion
term evaluated at the current timestep, the way PyFlow's MVP's RK4 time
integration does, `time-integration.md`) is subject to a stability limit
on timestep size that scales with the *square* of the cell size. For a
uniform mesh in $d$ dimensions the familiar form of the limit is

$$
\Delta t \lesssim \frac{(\Delta x)^2}{2 d \, \Gamma / \rho}
$$

(the leading constant depends on the time integrator; the $(\Delta x)^2$
scaling does not). Halving the cell size therefore quarters the usable
timestep, against advection's CFL limit merely halving it -- so the
diffusive limit is the more restrictive of the two on fine meshes, which is one of the standard motivations for treating
diffusion implicitly in production solvers (`time-integration.md` covers
this trade-off in more detail).

## Future Upgrade Options

`docs/implementation/upgrade-paths.md`'s "Diffusion" entry: simple
central formulation → improved geometric/non-orthogonal handling. This
tracks the Mesh layer's own upgrade path directly -- diffusion's
upgrade is less about a fundamentally different scheme (unlike
advection's upwind-to-WENO family) and more about correctly handling the
non-orthogonality that a more general mesh introduces, as described
above.

## References

- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  4 and Ch. 11 cover orthogonal central-difference diffusion and
  non-orthogonal correction terms respectively.
- Ferziger, J.H., Perić, M., and Street, R.L., *Computational Methods for
  Fluid Dynamics*, 4th ed., Springer, 2020. Ch. 9 covers diffusion-term
  discretisation on general meshes, including gradient reconstruction
  methods.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3f), against `fvm.md`,
`fluxes.md` and `meshes.md`.

Reviewed 2026-08-18: the diffusion coefficient's meaning is now pinned to
`fvm.md`'s notation rather than left ambiguous between the
density-weighted and kinematic forms; the explicit stability limit is
given as a formula rather than described only as "scales with the square
of the cell size"; and "Non-Orthogonal Considerations" was corrected --
it previously treated non-uniform structured spacing as a cause of
non-orthogonality, which it is not. A graded Cartesian mesh stays
orthogonal and loses only the centredness that makes the difference
quotient second-order. `meshes.md` carries the matching taxonomy.
