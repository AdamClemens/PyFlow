# Free-Surface Methods

This entry has no `docs/planning/knowledge-architecture.md` KA number --
the KA spec was written before Capability Level 10 existed and does not
anticipate it (root `CLAUDE.md`'s planning-completion gate closed
2026-08-15; new post-gate handbook content is added without a
retroactive KA slot, the same way `adr/ADR-004` through `ADR-006` exist
outside the KA numbering). It fills the gap
`docs/planning/backlog.md` recorded on 2026-08-21: `overview.md`
(KA-007) rates every method family's "Free surface" suitability but no
entry in this directory explained *how* a method actually represents a
moving fluid interface, and `compatibility.md` (KA-008) recorded only
one route to free-surface capability -- FVM↔SPH coupling, under "Coupled
methods". That is a real second gap this entry also closes: VOF and the
level-set method are not couplings between two solvers at all, and
filing them as if they were would have been the wrong classification,
not merely a missing one.

For the method families themselves and their free-surface ratings, see
`overview.md`. For how a coupled particle method (SPH) or an embedded
one differs structurally from what follows here, see `compatibility.md`.
For FVM's own control-volume machinery that both techniques below build
on top of, see `fvm.md`.

---

## The Problem

A free surface is the interface between two immiscible fluids (typically
a liquid and a gas) whose position is not known in advance and moves as
part of the solution -- Dam Break is the canonical example. On a fixed
Eulerian mesh (`meshes.md`), the interface generally does not align with
cell or face boundaries, so a method needs some way to say, at every
instant, which cells (or which fraction of each cell) hold which fluid,
and to advance that description consistently with the flow velocity.
**Volume of Fluid (VOF)** and the **level-set method** are the two
Eulerian techniques in general use for this; both add a single scalar
field to an otherwise ordinary FVM (or FDM) solve rather than
introducing a second solver, which is what separates them structurally
from the FVM↔SPH coupling `compatibility.md` describes.

## Volume of Fluid (VOF)

VOF represents the interface indirectly, through a **volume fraction**
field $\alpha$ defined on the same control volumes FVM already uses:
$\alpha = 1$ in a cell entirely full of the reference fluid (say,
liquid), $\alpha = 0$ in a cell entirely full of the other fluid (gas),
and $0 < \alpha < 1$ in a cell the interface currently passes through.
$\alpha$ is transported by the flow like any other scalar field
(`advection.md`):

$$
\frac{\partial \alpha}{\partial t} + \nabla \cdot (\alpha \mathbf{u}) = 0
$$

with no diffusive or source term -- the interface is advected, not
diffused or generated. Because $\alpha$ is a volume fraction integrated
exactly over each control volume, and the advection equation above is in
conservative form, **VOF conserves the volume of each fluid to machine
precision by construction**, the same structural guarantee `fvm.md`
attributes to FVM's own conservation form.

That conservation strength comes at a cost: a standard advection scheme
(`advection.md`) applied directly to $\alpha$ smears the sharp step
between $\alpha=0$ and $\alpha=1$ over several cells within a few
timesteps, exactly the numerical-diffusion behaviour `advection.md`
describes for any scheme -- and here it destroys the interface's
sharpness, not merely its accuracy. Practical VOF implementations
therefore reconstruct an explicit geometric interface within each
partially-filled cell before advecting it, most commonly with **PLIC**
(Piecewise Linear Interface Calculation): approximate the interface
within a cell as a single straight line (a plane, in 3D) oriented by the
local gradient of $\alpha$, positioned so it encloses exactly the cell's
$\alpha$ volume fraction, then advect that reconstructed geometry through
the velocity field for one timestep and re-derive $\alpha$ in each
affected cell from the swept volume. This keeps the interface within
roughly one cell width at all times, at the cost of a real geometric
computation every timestep (a plane-fitting and volume-clipping
calculation per interface cell) that a plain scalar-advection scheme does
not need.

**Curvature and surface tension.** Surface tension forcing needs the
interface's local curvature, and $\alpha$ is only piecewise-constant-ish
data (or, with PLIC, a set of independent per-cell planes with no shared
global representation) -- differentiating it directly to get curvature is
noisy. The standard workaround, **Continuum Surface Force (CSF)**
(Brackbill, Kothe and Zemach, 1992), smooths $\alpha$ before
differentiating it and converts the surface-tension force into an
equivalent volumetric body force concentrated near the interface, rather
than an exact boundary condition applied at a sharp geometric surface.

## The Level-Set Method

The level-set method represents the interface implicitly as the
zero contour of a smooth scalar field $\psi$, conventionally the
**signed distance function**: $\psi(\mathbf{x}) > 0$ in one fluid,
$\psi(\mathbf{x}) < 0$ in the other, $\psi = 0$ exactly on the interface,
and $|\psi(\mathbf{x})|$ equal to the distance from $\mathbf{x}$ to the
nearest point on the interface. $\psi$ is advected the same way $\alpha$
is:

$$
\frac{\partial \psi}{\partial t} + \mathbf{u} \cdot \nabla \psi = 0
$$

Because $\psi$ is smooth by construction rather than a near-discontinuous
volume fraction, its gradient is well-behaved everywhere, and curvature
and the interface normal follow directly from it with no reconstruction
step:

$$
\mathbf{n} = \frac{\nabla \psi}{|\nabla \psi|}, \qquad
\kappa = \nabla \cdot \mathbf{n} = \nabla \cdot \left(\frac{\nabla
\psi}{|\nabla \psi|}\right)
$$

This is the level-set method's central strength relative to VOF: smooth,
directly differentiable curvature, which is exactly what surface-tension
forcing needs and what VOF has to approximate through CSF smoothing.

The cost is on the conservation side, and it is the mirror image of
VOF's trade-off. Plain advection does not preserve the signed-distance
property ($|\nabla\psi| = 1$ everywhere) -- $\psi$ tends to flatten or
steepen away from it under a general velocity field, which degrades the
curvature calculation above and, uncorrected, the location of the
zero contour itself. Standard practice periodically **reinitializes**
$\psi$ back toward a true signed-distance function by solving a separate
steady-state PDE toward that property (Sussman, Smereka and Osher, 1994)
without moving the zero level set it already has. Reinitialization is not
optional bookkeeping; skipping it is the standard failure mode reported
for level-set implementations. Even with it, the classical level-set
method is **not exactly volume-conservative** the way VOF is: numerical
error in the advection and reinitialization steps can slowly leak volume
across the interface, most visibly for small, thin structures (droplets,
thin films) relative to the mesh spacing -- Dam Break's initial column
face and its later splash fragments are exactly this regime.

## VOF vs. Level-Set: The Trade-off Compactly

| Property | VOF | Level-set |
| --- | --- | --- |
| Mass/volume conservation | Exact, by construction | Approximate; needs care, degrades for small structures |
| Interface sharpness | Needs geometric reconstruction (PLIC) to stay sharp | Naturally smooth; no reconstruction step |
| Curvature / surface tension | Approximate (CSF smoothing) | Direct and accurate from $\nabla\psi$ |
| Extra machinery required | PLIC reconstruction each timestep | Periodic reinitialization |
| Implementation complexity | Moderate-to-high (geometric clipping) | Moderate (an extra PDE solve, but no geometry) |

Neither dominates the other, which is why production codes commonly hybridise them --
**Coupled Level-Set/VOF (CLSVOF)** (Sussman and Puckett, 2000) advects
both fields and uses $\psi$ for curvature while using $\alpha$ to enforce
conservation, trading the added cost of maintaining two fields for both
methods' strengths at once. This handbook records CLSVOF as the
existence of that trade-off, not as a PyFlow implementation decision --
which of VOF, level-set or CLSVOF (if any) PyFlow adopts for Level 10 is
an implementation choice for that Stage to make, informed by this
comparison, not one this survey makes on its behalf (the same posture
`overview.md` takes toward the eight method families it surveys).

## Relation to FVM and to the FVM↔SPH Coupling Route

Both techniques above are **field extensions of FVM**, not separate
solvers: $\alpha$ or $\psi$ is one more transported quantity stored on
the same control volumes as velocity and pressure, advected by the same
machinery `advection.md` describes, and coupled to the momentum equation
only through the surface-tension body force and through
density/viscosity that jump (VOF) or blend smoothly (level-set) across
the interface. No second mesh, timestep, or synchronisation boundary is
involved, which is precisely why this is not filed under
`compatibility.md`'s "Coupled methods": that category is for two
methods, each owning a distinct physical subdomain, exchanging boundary
data across an interface every timestep -- FVM↔SPH coupling fits that
description exactly, since SPH's dispersed phase is a genuinely separate
particle solver. VOF and level-set fit none of `compatibility.md`'s
seven kinds, because there is only ever one solver here; they are best
read as belonging to the same family of "numerical component that
extends FVM" as `pressure-velocity-coupling.md` or
`boundary-conditions.md`, applied to the free-surface problem
specifically.

The practical consequence for PyFlow: choosing VOF or level-set (or
CLSVOF) is not a choice between two frameworks the way FVM-vs-SPH is --
it is a choice of *which extra field and reconstruction/reinitialization
machinery* to add to the existing FVM core. FVM↔SPH coupling remains the
right description for a genuinely separate dispersed-phase solver
(droplets, spray, granular material suspended in a carrier flow); VOF and
level-set are the right description for a single continuous interface
between two bulk fluids, which is what Dam Break is.

## References

- Hirt, C.W. and Nichols, B.D., "Volume of fluid (VOF) method for the
  dynamics of free boundaries", *Journal of Computational Physics*,
  39(1), 1981, pp. 201-225. The original VOF formulation.
- Youngs, D.L., "Time-dependent multi-material flow with large fluid
  distortion", in *Numerical Methods for Fluid Dynamics*, Academic
  Press, 1982, pp. 273-285. The original PLIC interface-reconstruction
  scheme.
- Brackbill, J.U., Kothe, D.B. and Zemach, C., "A continuum method for
  modeling surface tension", *Journal of Computational Physics*, 100(2),
  1992, pp. 335-354. The Continuum Surface Force (CSF) model.
- Osher, S. and Sethian, J.A., "Fronts propagating with curvature-
  dependent speed: algorithms based on Hamilton-Jacobi formulations",
  *Journal of Computational Physics*, 79(1), 1988, pp. 12-49. The
  original level-set formulation.
- Sussman, M., Smereka, P. and Osher, S., "A level set approach for
  computing solutions to incompressible two-phase flow", *Journal of
  Computational Physics*, 114(1), 1994, pp. 146-159. The standard
  reinitialization procedure and its application to two-phase flow.
- Sussman, M. and Puckett, E.G., "A coupled level set and volume-of-
  fluid method for computing 3D and axisymmetric incompressible
  two-phase flows", *Journal of Computational Physics*, 162(2), 2000,
  pp. 301-337. CLSVOF.
- Osher, S. and Fedkiw, R., *Level Set Methods and Dynamic Implicit
  Surfaces*, Springer, 2003. The standard level-set textbook, covering
  reinitialization and curvature computation in depth.

## Maintenance

Written 2026-08-21, closing the gap `docs/planning/backlog.md` recorded
the same day (found while moving free surface to Capability Level 10):
this directory had no VOF entry, no level-set entry, and no free-surface
entry of any kind, leaving `docs/practices.md`'s physical-correctness
rule with no documented method properties to validate Dam Break against.
Cross-referenced from `overview.md` and `compatibility.md`; see both
documents' own Maintenance sections for the pointers added there in the
same change.
