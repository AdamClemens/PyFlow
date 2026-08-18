# Variable Placement: Collocated and Staggered Arrangements

Per `docs/planning/knowledge-architecture.md` KA-018. How field values
are positioned relative to a mesh's cells and faces, and why the choice
matters specifically for incompressible flow.

Depends conceptually on `fvm.md` (KA-016) and interacts directly with
`pressure-velocity-coupling.md` (KA-023) -- this entry explains *why*
that interaction exists; the coupling algorithms themselves are covered
there.

---

## The Placement Question

FVM (`fvm.md`) stores one representative value per field per control
volume, but says nothing about exactly *where within* that scheme every
field must live relative to every other. Two conventions dominate
practice, and the choice is not cosmetic -- it changes which numerical
pathologies a solver is exposed to.

## Collocated Arrangement

Every field -- pressure, and every velocity component -- is stored at
the same location, conventionally the cell centre. This is PyFlow's MVP
choice (`docs/implementation/mvp.md`).

**Advantages:** a single mesh/storage layout serves every field, which
simplifies implementation substantially -- one `Field` abstraction
(`docs/architecture/engine.md`'s "Variables" layer) works uniformly for
scalars and vector components alike, boundary conditions are applied the
same way regardless of which field they belong to, and extending the
simulation with an additional transported field (temperature, a species
concentration) requires no change to how existing fields are stored.

**Disadvantage -- the checkerboard problem:** estimating the pressure
gradient *at* a cell centre from the pressures at the *neighbouring* cell
centres gives the natural central-difference stencil

$$
\left(\frac{\partial p}{\partial x}\right)_i \approx
\frac{p_{i+1} - p_{i-1}}{2\Delta x}
$$

which skips $p_i$ entirely and spans two cell widths. That is exactly the
defect: a **checkerboard** pressure field -- one alternating
high/low/high/low from cell to cell -- has $p_{i+1} = p_{i-1}$ at every
cell, so this stencil returns a gradient of precisely **zero** everywhere.
The momentum equation cannot feel such a field at all; it lies in the null
space of the discrete gradient operator, and can therefore be added to any
solution, at any amplitude, without changing the velocity the momentum
equation produces.

The same 2$\Delta x$ stencil creates the dual problem on the continuity
side: if face velocities are obtained by plain linear interpolation of the
neighbouring cell-centred velocities, the discrete divergence at a cell
also reduces to a two-cell-wide difference, so a checkerboard *velocity*
field registers as exactly divergence-free. A solver enforcing only that
the discrete divergence vanish has no means of rejecting either mode. A
naive collocated discretisation is therefore prone to a decoupled,
oscillatory pressure field passing undetected through the
pressure-velocity coupling step -- not because the pressure is wrongly
computed, but because nothing in the discretisation constrains it.

**The fix, briefly:** the standard remedy is **Rhie-Chow interpolation**
-- computing the face velocity used in the continuity equation from a
momentum-equation-consistent interpolation (one that includes the
pressure gradient's effect at the face itself, not just an average of the
two neighbouring cell-centred velocities) rather than simple linear
interpolation of the two adjacent cell-centred velocities. This restores
the coupling between adjacent cells' pressures that naive collocated
interpolation loses, at the cost of an extra interpolation step every
timestep. `pressure-velocity-coupling.md` covers how this interacts with
PISO specifically.

## Staggered Arrangement

Velocity components are instead stored at the centres of the faces they
are normal to (the u-component at east/west faces, the v-component at
north/south faces, in 2D), with pressure remaining at the cell centre.
This is the classical remedy for the checkerboard problem, historically
predating Rhie-Chow interpolation: because a velocity component lives
exactly at the face the corresponding pressure-gradient term needs, the
pressure gradient driving that velocity is computed from the two
*immediately adjacent* cell-centred pressures -- a genuinely local
stencil that cannot support a checkerboard pattern, since such a pattern
would now produce a non-zero, directly-felt pressure difference at every
face.

**Advantages:** avoids the checkerboard problem structurally, without
needing an interpolation correction; historically the more common choice
in classical incompressible-flow solvers (Patankar's SIMPLE algorithm was
originally formulated on a staggered grid).

**Disadvantages:** every field needs its own storage location relative to
the mesh (three separate layouts in 2D: cell-centred pressure, u at
vertical faces, v at horizontal faces), which complicates implementation
-- especially for a field-centric engine meant to transport arbitrary
additional fields (`prompts/global/project.md`), since each new
vector-valued field would need the same staggering treatment worked out
again. Staggering also becomes substantially more complex to generalise
to unstructured or non-orthogonal meshes, where "the face normal to this
velocity component" is not always well defined the way it is on a
Cartesian grid.

## Why PyFlow's MVP Uses Collocated

The collocated arrangement's implementation simplicity aligns directly
with the MVP's purpose -- "correctness, understandability, and
architectural validation, not maximum numerical accuracy"
(`docs/implementation/mvp.md`) -- and with the project's field-centric
architecture, where treating every transported field uniformly is a
first-class goal, not an incidental convenience. The checkerboard problem
is a known, well-understood pathology with a standard fix
(Rhie-Chow interpolation), not an open research question, so choosing
collocated does not trade away correctness -- it trades a small,
well-characterised amount of implementation complexity (the
interpolation step) for a much larger reduction in storage/architecture
complexity across every other layer.

## Numerical Stability Implications

Beyond the checkerboard problem, variable placement also affects which
face values are directly available versus interpolated for advection and
diffusion flux calculations (`fluxes.md`) -- a staggered grid gets some
face velocities "for free" (no interpolation needed, since that is
exactly where they are stored), while a collocated grid must interpolate
every face value from cell-centred data, including for the fields whose
placement does not itself cause a stability problem. This is a modest,
uniform overhead rather than a stability concern in its own right.

## Upgrade Path

`docs/implementation/upgrade-paths.md`'s "Variables" entry: collocated →
alternative placement schemes (e.g. staggered) where required. In
practice this is more likely to mean adopting Rhie-Chow-style corrections
more rigorously, or supporting a hybrid arrangement for a specific
numerical method, than switching wholesale to staggered storage -- the
architectural cost of staggering (described above) is exactly what
collocated storage was chosen to avoid, so a full reversal would need a
strong, specific justification.

## References

- Rhie, C.M. and Chow, W.L., "Numerical study of the turbulent flow past
  an airfoil with trailing edge separation", *AIAA Journal*, 21(11),
  1983, pp. 1525-1532. The original collocated-grid interpolation
  correction.
- Patankar, S.V., *Numerical Heat Transfer and Fluid Flow*, Hemisphere
  Publishing, 1980. Ch. 6 develops the staggered-grid formulation and the
  checkerboard-pressure problem it was designed to avoid.
- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. §6.7
  covers collocated-grid Rhie-Chow interpolation directly.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3c), against `fvm.md`
and forward-referencing `pressure-velocity-coupling.md` (written later
the same session, per the backlog's stated E3 order) for the coupling
algorithms themselves.

Reviewed 2026-08-18: the checkerboard explanation was rewritten. The
previous version said the spurious pressure field "produces no net
velocity divergence at any cell," which describes the dual (velocity)
mode rather than the mechanism that lets a checkerboard *pressure* field
survive -- the $2\Delta x$ central-difference stencil returning exactly
zero gradient for it. Both modes are now stated, with the stencil shown
explicitly.
