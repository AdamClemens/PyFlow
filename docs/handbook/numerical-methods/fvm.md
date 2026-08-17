# The Finite Volume Method

Per `docs/planning/knowledge-architecture.md` KA-016. The canonical
explanation of the Finite Volume Method (FVM) -- PyFlow's selected
initial numerical framework (`adr/ADR-002-fvm-first.md`).

This entry explains what FVM *is*, independent of PyFlow's eventual
implementation. For why PyFlow chose it, see `adr/ADR-002-fvm-first.md`.
For FVM's place among other method families and how it compares to them,
see `overview.md` (KA-007) and `compatibility.md` (KA-008).

---

## What FVM Does

FVM solves a partial differential equation by dividing the physical
domain into a finite number of non-overlapping **control volumes** (also
called cells) and enforcing the governing equation's **integral,
conservation form** over each one individually, rather than approximating
the equation's derivatives pointwise (as the Finite Difference Method
does) or projecting the solution onto basis functions over elements (as
the Finite Element Method does).

The starting point is always a conservation law written in integral form
over an arbitrary volume $V$ with boundary $\partial V$:

$$
\frac{d}{dt}\int_V \phi \, dV + \oint_{\partial V} \phi \mathbf{u} \cdot
\mathbf{n} \, dA = \oint_{\partial V} \Gamma \nabla\phi \cdot \mathbf{n}
\, dA + \int_V S_\phi \, dV
$$

for a transported quantity $\phi$ (e.g. a velocity component, temperature,
or a scalar concentration), where the four terms are, in order: the rate
of change of $\phi$ within the volume, the net flux of $\phi$ carried out
by the flow (advection), the net flux of $\phi$ diffusing across the
boundary, and any volumetric source or sink. Applying this equation to
each control volume, rather than deriving it once for the whole domain
and then discretising derivatives, is what gives FVM its defining
property: **the equation being solved is exactly a statement of
conservation for every individual cell**, and summing it over all cells
in the domain exactly reproduces the domain-wide conservation statement
(interior face contributions cancel in pairs, since each interior face is
shared by exactly two cells and contributes with opposite sign to each).
This is what "conservation is guaranteed by construction" (`adr/ADR-002`)
means concretely -- it is a structural property of the discretisation,
not something separately proven for each scheme built on top of it.

## Control Volumes and Cell-Centred Variables

The domain is partitioned into control volumes -- for PyFlow's MVP, the
cells of a structured 2D Cartesian mesh (`docs/implementation/mvp.md`),
though FVM itself places no such restriction (see `meshes.md`, KA-017).
Each cell stores a single representative value for each transported
field, conventionally located at the cell's geometric centre (the
**cell-centred** convention) -- the value is treated as the cell's
volume-averaged value, not a value defined at a single point the way an
FDM grid point is. Which physical quantities share the same cell-centred
location, versus being staggered onto face centres, is itself a design
choice with real consequences for stability -- covered separately in
`variable-placement.md` (KA-018), since it interacts with
pressure-velocity coupling in a way that deserves its own treatment.

## Face Fluxes and Discretisation

Because the volume integral's flux terms are surface integrals over
$\partial V$, and a control volume's boundary in a mesh is exactly the
set of faces it shares with its neighbours (plus any domain-boundary
faces), FVM's central computational task is: **given the cell-centred
values on either side of a face, estimate the flux of $\phi$ through that
face.** This single idea -- computing something at a face from
information at cell centres -- is what `fluxes.md` (KA-019) treats in
its own right, and it is also exactly the point at which FVM's
implementation splits into independently replaceable pieces: the
advective contribution to a face flux is computed by whichever advection
scheme is configured (`advection.md`, KA-020), and the diffusive
contribution by whichever diffusion scheme is configured (`diffusion.md`,
KA-021). A cell's total flux balance sums these face-flux estimates over
every face of the cell, with an outward-pointing sign convention so that
what leaves one cell through a shared face is exactly what enters its
neighbour.

Computing a face's diffusive flux requires the field's **gradient** at
that face (Fick's- or Fourier's-law-type diffusion is proportional to a
gradient), and computing higher-order advective fluxes typically also
requires cell-centred gradient estimates. Gradient (and, dually,
**divergence** -- the net outward flux per unit volume, which is exactly
what the discretised conservation equation computes once every face flux
is known) are therefore basic FVM operators that the higher-level
advection/diffusion/flux machinery is built on top of, not something
specific to any one scheme.

## Boundary Treatment

At a face on the domain's exterior boundary, there is no neighbouring
cell to supply a value, so the flux must instead be determined by the
boundary condition itself -- a Dirichlet condition fixes the face value
directly, a Neumann condition fixes the face's gradient (and hence its
diffusive flux) directly, and so on. See `boundary-conditions.md`
(KA-025) for the full treatment; the point relevant here is that FVM
handles a boundary condition the same structural way it handles an
interior face -- by supplying (or computing) a face flux -- rather than
needing a fundamentally different mechanism at the domain edge.

## Relation to the Governing Equations

FVM does not itself specify which physical equations are being solved --
it is a discretisation strategy applicable to any conservation law
expressible in the integral form above. PyFlow's initial governing
equations (incompressible continuity and momentum) are described in
`docs/handbook/physics/incompressible-flow.md` (KA-010); this document
covers only how FVM turns *any* such equation into a solvable, discrete
system, not the specific equations PyFlow solves.

## Strengths and Weaknesses

**Strengths:** conservation is exact at the discrete level for any mesh,
structured or unstructured, which is why FVM dominates production CFD
software for engineering flows (OpenFOAM, ANSYS Fluent, SU2 among them);
it generalises naturally to complex geometry, since a control volume can
be any polyhedron and the flux-balance idea does not depend on a
structured index space.

**Weaknesses:** achieving high-order spatial accuracy is more involved
than in FDM, because face values and gradients must be reconstructed from
cell-centred data rather than read directly off a grid stencil, and this
reconstruction becomes more delicate on skewed or highly non-orthogonal
meshes (non-orthogonality corrections are a recurring theme across
`diffusion.md` and `fluxes.md`). Bookkeeping cost (storing and traversing
face/neighbour connectivity, rather than a simple index offset) is higher
than FDM's for the same reason.

## Computational Considerations

Per-timestep cost scales with the number of faces (each contributing one
flux evaluation) rather than the number of cells directly, though the two
are proportional for a fixed mesh topology. Unstructured meshes trade
FDM/structured-FVM's predictable memory-access pattern for the
flexibility of arbitrary geometry -- a real cost on GPU-oriented
architectures, where structured-grid memory access is much more
cache/coalescing-friendly than indirect neighbour lookups
(`overview.md`'s computational-characteristics ratings for FVM reflect
this: strong parallel scaling, but a step down from FDM's GPU rating).

## Compatibility with an FEM Extension

FVM and FEM are not mutually exclusive at the level of a single project:
`overview.md` records them as commonly coupled in multiphysics codes, and
`adr/ADR-002-fvm-first.md` treats FEM as deferred rather than rejected
specifically because FVM's control-volume/face-flux structure does not
foreclose an FEM-compatible architecture being added later for problems
FEM suits better (e.g. structural coupling, arbitrary-order accuracy on
smooth domains) -- see `docs/implementation/upgrade-paths.md`'s
"Numerical Framework" entry.

## References

- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. The
  standard introductory FVM textbook; §2-4 cover the control-volume
  integration and discretisation ideas summarised above in much greater
  depth, with worked derivations for each term.
- Patankar, S.V., *Numerical Heat Transfer and Fluid Flow*, Hemisphere
  Publishing, 1980. An earlier, highly influential treatment of
  control-volume discretisation, particularly for diffusion and
  advection-diffusion problems.
- Ferziger, J.H., Perić, M., and Street, R.L., *Computational Methods for
  Fluid Dynamics*, 4th ed., Springer, 2020. Broader coverage including
  unstructured/non-orthogonal mesh treatment and comparison with FDM/FEM.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3a), the first
numerical-methods handbook entry -- written first per the backlog's own
ordering, since `adr/ADR-002-fvm-first.md` already references it and
several later entries (`meshes.md`, `fluxes.md`, `advection.md`,
`diffusion.md`) depend on it conceptually. Update this entry if PyFlow's
FVM implementation surfaces a concept not anticipated here, but keep it
implementation-independent -- implementation-specific detail belongs in
`docs/architecture/engine.md` or the code itself, not here.
