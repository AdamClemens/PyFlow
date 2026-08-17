# Meshes

Per `docs/planning/knowledge-architecture.md` KA-017. Mesh concepts
relevant to PyFlow, independent of implementation.

Depends conceptually on `fvm.md` (KA-016) -- a mesh's job, in FVM terms,
is to define the control volumes the method integrates over and the
faces through which flux is exchanged between them.

---

## What a Mesh Provides

A mesh discretises the physical domain into a finite set of
non-overlapping control volumes (**cells**). For FVM, a mesh must supply,
at minimum:

- **cell geometry** -- each cell's volume (area, in 2D) and centroid;
- **faces** -- the shared boundary between two adjacent cells, or between
  a cell and the domain exterior, each with its own area (length, in 2D)
  and outward-pointing normal direction;
- **neighbour connectivity** -- which cells share which faces, so a
  flux computed at a face can be added to one cell's balance and
  subtracted from the other's;
- **boundary identification** -- which faces lie on the domain exterior
  (and so need a boundary condition, `boundary-conditions.md`) versus
  which are interior (and so need a face-flux computed from two
  neighbouring cells).

Nothing about FVM itself constrains how this information is produced or
stored -- a mesh's *conceptual* requirements (the four items above) are
separate from any specific data structure that satisfies them.

## Structured Meshes

A structured mesh indexes cells by a regular, typically Cartesian, index
tuple (`(i, j)` in 2D), so that a cell's neighbours are implicit in its
index (`(i+1, j)` is always the neighbour in one direction) rather than
requiring an explicit adjacency list. This makes neighbour lookup,
storage layout, and memory access pattern extremely predictable --
exactly the property `overview.md`'s FDM/FVM "GPU suitability" and
"cache locality" ratings depend on.

PyFlow's MVP uses a **2D structured Cartesian mesh with uniform grid
spacing** (`docs/implementation/mvp.md`). This is the right starting
choice for the reasons `adr/ADR-002-fvm-first.md` and this project's
engineering principles both point at: it validates the full engine
architecture (mesh, fields, operators, boundary conditions, coupling)
with the simplest possible mesh representation, deferring the added
complexity of general connectivity until the simpler case is working
end-to-end (`docs/engineering-principles.md` P-018: implement the
simplest valid version of each layer, then improve independently).
Uniform spacing additionally means every cell has identical geometry,
which removes non-uniform-geometry considerations (see "Geometry" below)
from the MVP entirely.

## Unstructured Meshes

An unstructured mesh represents cells and faces with explicit
connectivity -- typically an array of cells, an array of faces, and
index lists relating each face to its one or two adjacent cells -- rather
than relying on a regular index. This is strictly more general: any
structured mesh can be represented this way, but not vice versa. The
price is exactly what structure gives up: neighbour lookup becomes an
indirect array access rather than an index-arithmetic operation, and
cache/memory-access locality is no longer guaranteed by construction.

Unstructured meshes are what make **arbitrary geometry** practical --
cells need not be axis-aligned quadrilaterals/hexahedra, and mesh density
can vary smoothly to resolve small geometric features without forcing
fine resolution everywhere. This is the property `docs/implementation/
upgrade-paths.md`'s Mesh upgrade path (structured 2D → structured 3D →
unstructured → arbitrary geometry → adaptive refinement) is building
toward.

## Geometry

Cell volume/area, centroid location, and face area/normal are all
**geometric** quantities computed from a mesh's vertex coordinates, not
physical or numerical quantities in their own right -- but they enter
directly into FVM's discretisation (a face flux is multiplied by the
face's area; a cell's rate-of-change term is divided by its volume). On a
uniform Cartesian mesh these are trivial (every cell identical, every
face axis-aligned); on a general unstructured mesh they require real
computation, and a non-orthogonal mesh (where a face normal is not
parallel to the vector between the two cell centroids it separates)
introduces the correction terms `diffusion.md` and `fluxes.md` describe.

## Internal and External Boundaries

An **external boundary** face lies on the edge of the simulated domain
and needs a boundary condition (`boundary-conditions.md`) to supply the
flux a missing neighbour would otherwise provide. An **internal
boundary** is a face inside the domain that nonetheless needs
special treatment -- a thin wall, a material interface, or a
mesh-refinement interface between regions of different resolution.
PyFlow's MVP has only external boundaries (`docs/implementation/mvp.md`);
internal boundaries are explicitly future work
(`docs/architecture/icds.md`'s Boundary Condition ICD limitations note,
and `upgrade-paths.md`'s Boundary Conditions entry).

## Future: Arbitrary Geometry and Adaptive Refinement

Two distinct upgrades sit beyond unstructured meshes, and are worth
distinguishing since they solve different problems:

- **Arbitrary geometry** means the mesh can conform to a complex domain
  shape (e.g. an obstacle, a curved boundary) -- a *shape* upgrade.
- **Adaptive refinement** means mesh resolution can vary over the domain,
  and potentially change during a simulation to track a moving feature
  (a sharp gradient, a shock, a free surface) -- a *resolution* upgrade,
  orthogonal to whether the mesh is structured or not (a structured mesh
  can be locally refined; an unstructured mesh does not automatically
  imply adaptivity).

Both require unstructured connectivity as a prerequisite (a structured
index cannot represent either), which is why they sit later on the
upgrade path than "unstructured" itself.

## References

- Ferziger, J.H., Perić, M., and Street, R.L., *Computational Methods for
  Fluid Dynamics*, 4th ed., Springer, 2020. Ch. 8 covers structured and
  unstructured mesh generation and the geometric quantities a
  finite-volume discretisation needs from a mesh.
- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  11 covers unstructured/body-fitted mesh treatment and non-orthogonality
  corrections.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3b), against `fvm.md`
(written first, per the backlog's own ordering) and
`docs/implementation/{mvp,upgrade-paths}.md`.
