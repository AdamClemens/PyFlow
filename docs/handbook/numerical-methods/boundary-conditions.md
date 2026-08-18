# Boundary Conditions

Per `docs/planning/knowledge-architecture.md` KA-025. The conceptual and
numerical role of boundary conditions in FVM.

Depends on `fvm.md` (boundary treatment as a special case of face-flux
computation) and, for what a boundary condition physically represents in
a given case, the relevant `docs/handbook/physics/` entry.

---

## Why FVM Needs Boundary Conditions

`fvm.md`'s "Boundary Treatment" section notes that a face on the domain's
exterior has no neighbouring cell to supply a value or gradient, so the
flux there must come from somewhere else -- a boundary condition is
exactly that "somewhere else": a rule for producing the face value,
face-normal gradient, or flux a boundary face needs, in place of the
missing neighbour interior faces get automatically. Every boundary
condition type below is a different rule for filling that gap, and FVM
treats the result the same way regardless of which rule produced it --
the boundary face's contribution is added to the owning cell's flux
balance exactly like any interior face's would be.

## Dirichlet

Fixes the field's **value** directly at the boundary -- $\phi = \phi_0$
on the boundary face. Physically, this represents a boundary whose state
is externally imposed and known: a wall held at a fixed temperature, an
inlet with prescribed velocity. Numerically, the boundary face value is
simply $\phi_0$, and the face's diffusive gradient is computed from
$\phi_0$ and the adjacent cell-centred value exactly as an interior
face's gradient would be, using the (known, fixed) distance to the
boundary in place of a neighbour's centroid distance.

## Neumann

Fixes the field's **gradient** normal to the boundary --
$\partial\phi/\partial n = g_0$. Physically, this represents a specified
flux across the boundary; a zero-gradient Neumann condition, in
particular, represents no flux at all -- an insulated wall, or an outlet
far enough downstream that the field has stopped changing along the flow
direction. A **symmetry plane** is closely related but not identical, and
the difference matters for vector fields: symmetry means zero gradient for
*scalars* and for the velocity components *tangential* to the plane, but a
hard zero (Dirichlet) for the velocity component *normal* to it, since
nothing may cross a symmetry plane. Treating symmetry as blanket
zero-gradient on every field is a standard way to let a small leak through
a boundary that should be impermeable. Numerically, the boundary's diffusive flux is computed directly
from $g_0$ (no cell-centred/boundary-value difference is needed, since
the gradient is already given), while the boundary's advective face value
is typically extrapolated from the adjacent cell-centred value.

## Periodic

Identifies one boundary face with a corresponding face on the *opposite*
side of the domain, so that flow leaving through one is treated as
entering through the other -- physically representing a domain that
repeats infinitely in that direction, used when the true domain is much
larger than what is practical to simulate directly but the flow is
expected to be statistically similar across repetitions. Numerically,
this is closer to an interior face than either Dirichlet or Neumann: the
periodic face pair supplies each other's "neighbour" value directly, the
same way two interior cells do, just across a computational rather than
geometric gap. A periodic condition requires its paired boundary to also
be periodic (`docs/architecture/icds.md`'s Boundary Condition ICD notes
this explicitly) -- a periodic condition on only one side of a domain has
no physical meaning, since there would be nothing for it to be paired
with.

## Robin

A **Robin** (or mixed) condition specifies a linear combination of value
and gradient, $\alpha \phi + \beta \, \partial\phi/\partial n = \gamma$,
generalising Dirichlet ($\beta = 0$) and Neumann ($\alpha = 0$) as special
cases. Physically, this represents boundaries where neither the value nor
the flux alone is known but some relationship between them is -- a
convective heat-transfer boundary, for instance, where the heat flux
depends on the difference between the boundary temperature and an
external ambient temperature (`docs/handbook/physics/heat-transfer.md`
covers this physical case directly). Numerically, a Robin condition
combines elements of both the Dirichlet and Neumann treatments above,
solving for the boundary face value that simultaneously satisfies the
specified linear relationship, given the adjacent cell-centred value.

## Velocity and Pressure Are Not Given Boundary Conditions Independently

The types above are stated for a generic transported field $\phi$, which
is the right level for FVM in general. Incompressible flow adds a
constraint the generic statement does not capture: **velocity and pressure
cannot be prescribed independently on the same boundary**, because
pressure has no equation of its own and exists only to enforce continuity
(`docs/handbook/physics/incompressible-flow.md`). In practice the two come
in fixed pairs -- a no-slip wall or a prescribed inlet fixes velocity
(Dirichlet) and leaves pressure to a zero-gradient Neumann condition; an
outlet more often fixes pressure and lets velocity be extrapolated.
Prescribing both on the same boundary over-determines the problem.

Two consequences follow, both of which decide whether a case is solvable
at all rather than merely how accurate it is:

- **Global mass conservation must be satisfied by the boundary data
  itself.** With velocity prescribed on every boundary, the prescribed
  values must satisfy $\oint_{\partial V} \mathbf{u} \cdot \mathbf{n} \,
  dA = 0$: a constant-density fluid in a fixed domain has nowhere to put a
  net inflow. Boundary values violating this describe a physically
  impossible flow, and the pressure equation derived from them has no
  solution.
- **Pressure's level is then undetermined**, since no boundary anchors it,
  leaving the discrete pressure system singular. The remedies belong to
  the coupling and solver layers rather than here --
  `pressure-velocity-coupling.md`'s "When the Pressure Equation Has No
  Unique Solution" and `linear-solvers.md`'s Conjugate Gradient caveat.

Both apply directly to PyFlow's MVP: the lid-driven cavity
(`docs/implementation/mvp.md`) prescribes velocity on all four boundaries
and is exactly this case.

## Internal vs. External Boundaries

`meshes.md` distinguishes internal boundaries (faces inside the domain
needing special treatment -- a thin wall, a material interface) from
external ones (the domain's true edge). The boundary-condition types
above apply naturally to external boundaries; an internal boundary
typically needs a *pair* of boundary conditions, one on each side, since
flow or a scalar field can behave differently approaching the same
physical surface from either direction (an insulated internal wall, for
example, is a zero-flux Neumann condition applied from both sides
independently, rather than a single shared condition).

## Mixing Boundary Conditions

A real domain typically needs different condition types on different
edges simultaneously (a fixed-velocity inlet, a zero-gradient outlet, a
no-slip wall, and a periodic spanwise pair, for example, on the same
mesh) -- this is why `docs/architecture/icds.md`'s Boundary Condition ICD
is deliberately per-boundary-face rather than a single simulation-wide
choice, unlike the other five ADR-003-named components. Nothing in FVM's
treatment requires uniformity across boundaries; each boundary face's
flux is computed independently once its own condition type and value are
known.

## Future: Arbitrary Geometries

PyFlow's MVP restricts boundaries to the simple, axis-aligned edges of a
structured Cartesian mesh (`docs/implementation/mvp.md`). Extending to
arbitrary-geometry boundaries (a curved wall, an internal obstacle of
general shape) is architecturally a consequence of the Mesh layer's own
upgrade path (`meshes.md`, `upgrade-paths.md`) rather than a separate
boundary-condition capability -- the condition *types* above apply
identically on a curved boundary face; what changes is the mesh's ability
to represent that face's geometry accurately in the first place.

## Numerical Implications

Boundary conditions interact with every layer that touches a boundary
face: advection schemes typically need special one-sided treatment at a
boundary (no downstream/upstream-plus-one cell exists to extrapolate
from, for schemes with a wider stencil, `advection.md`); diffusion's
gradient calculation at a boundary uses the fixed boundary distance
rather than a cell-to-cell centroid distance; and a poorly chosen
boundary condition (for example, the over-constrained or
mass-inconsistent combinations the section above describes) can make the
discrete linear system pressure-velocity coupling produces ill-posed or
poorly conditioned (`linear-solvers.md`), independent of anything about
the interior discretisation.

## References

- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  9 covers boundary condition implementation in FVM, including inlet,
  outlet, wall and symmetry treatments.
- Ferziger, J.H., Perić, M., and Street, R.L., *Computational Methods for
  Fluid Dynamics*, 4th ed., Springer, 2020. Ch. 7 covers Dirichlet,
  Neumann and mixed boundary condition discretisation on general meshes.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3j, closing Group E3),
against `fvm.md` and `meshes.md`, and forward-referencing
`docs/handbook/physics/heat-transfer.md` (written later the same session,
per the backlog's stated E4 order) for the Robin-condition physical
example.

Reviewed 2026-08-18: added "Velocity and Pressure Are Not Given Boundary
Conditions Independently", covering the pairing rule and the global
mass-conservation condition prescribed-velocity boundaries must satisfy --
both of which decide whether a case is solvable at all, and neither of
which follows from the generic per-field treatment above. Symmetry planes
were also separated from plain zero-gradient Neumann conditions, since
they differ for the velocity component normal to the plane.
