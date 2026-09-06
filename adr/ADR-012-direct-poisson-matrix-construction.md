# ADR-012: PISO's Poisson Matrix Is Built Directly Per Face, Not Probed Per Cell

**Status:** Accepted

Narrows `adr/ADR-011-sparse-linear-solver-matrix.md`, which stays
Accepted -- ADR-011's own decision (sparse CSR storage) is unchanged
here; only its named, deferred Alternative is now adopted. Read together,
per `adr/CLAUDE.md`'s own precedent for this shape (ADR-004/ADR-005,
ADR-001/ADR-006).

---

# Context

ADR-011 measured `PISO._poisson_matrix`'s own probe-based construction
-- one full `self._diffusion.flux(basis)` + `accumulate_flux_to_cells`
call per cell, `O(num_cells * num_faces)` -- dominating a short run: ~52s
of a 1024-cell build against ~0.02s to solve, three orders of magnitude
apart. It named a direct, per-face `O(num_faces)` construction as the
fix and explicitly deferred it, citing a real correctness risk: it would
hard-code two facts true only of `PISO`'s own current wiring -- a
zero-gradient pressure boundary on every wall, and uniform cell volume
-- "with nothing asserting they stay true if either changes." Its own
closing line: "Revisit directly, now that the build's real cost is
measured rather than assumed amortised-away."

That revisit is this ADR. A separate seven-fix vectorisation arc
(`docs/planning/roadmap.md` TASK-022/026/040/024/023/027 x2) landed
between ADR-011 and this one, vectorising every per-face Python loop
this session's investigation found -- but every one of those fixes made
a *single* `flux`/`accumulate_flux_to_cells` call faster, not how many
times `_poisson_matrix` called them. Profiling the same five-frame demo
(`examples/experiments/smoke_transport_high_res.yaml`) after that arc
found the probe loop still dominating: ~2.15s of a ~5.6s post-import run
(38%), one-time per mesh (cached by identity since TASK-034), the single
largest remaining cost in the engine.

**Both invariants ADR-011 flagged were verified against the real code
before being relied on, not assumed:**

- `PISO.__init__` always builds an internal, non-configurable
  `_ZeroGradientPressureCondition` (`kind="gradient"`, `evaluate` always
  `0.0`) for all four named edges -- there is no constructor argument
  that could change this today.
- `StructuredCartesianMesh.cell_volume` is unconditionally `dx * dy`,
  mesh-wide -- structurally guaranteed by the current `Mesh` hierarchy,
  not merely usually true.

**A third subtlety was found and only confirmed correct by numerical
testing, not by re-deriving on paper a second time.**
`accumulate_flux_to_cells`'s own geometry cache (`simulation.
_flux_geometry`) has no knowledge of `periodic_pairs` at all -- a
periodic boundary face and its mesh-reported "no neighbour" look
identical to it. So a periodic face's flux contributes to only its
owner's row; the paired face on the opposite domain edge supplies the
other half independently, rather than the two sharing one symmetric
contribution the way a genuine interior face does. A first hand
derivation, made while planning this change, assumed the full symmetric
stencil applied to periodic faces too and was wrong -- caught by testing
a mesh where the periodic connection does *not* coincide with an
existing interior one (a mesh where it does happen to coincide passed
either way, which is what let the wrong version look right at first).

---

# Decision

**`PISO._poisson_matrix` walks `mesh.num_faces` once, building sparse
`(row, col, value)` triples directly, instead of probing `mesh.num_cells`
basis vectors through the full diffusion/accumulation pipeline.**

For each face:

- **Interior** (`mesh.face_neighbours(face)` returns a real neighbour):
  `c = gamma * mesh.face_area(face) / (mesh.face_centroid_distance(face)
  * volume)`. Contributes the standard symmetric compact-Laplacian
  stencil: `[owner,owner] += c`, `[neighbour,neighbour] += c`,
  `[owner,neighbour] -= c`, `[neighbour,owner] -= c`.
- **Periodic** (`mesh.boundary_face_name(face) in self._periodic_pairs`):
  same `c` formula with `wrapped = mesh.wrapped_neighbour_cell(face)` and
  `distance = 2 * mesh.face_centroid_distance(face)`. Contributes
  **one-sided**: `[owner,owner] += c`, `[owner,wrapped] -= c` -- nothing
  written to `wrapped`'s own row from this face id.
- **Genuine boundary** (neither of the above): contributes nothing
  (zero-gradient, verified above) -- skipped entirely, no
  `BoundaryCondition.evaluate` call at all.

`coalesce()` is still required, and now does real work it did not
before: a periodic pair coinciding with an existing interior connection
(e.g. a mesh only two cells tall wrapping north/south) produces two
contributions at the same `(row, col)` that must be summed -- verified
this actually occurs, unlike the old code's own comment claiming no
duplicates ever arise (true there, since each probed column touched each
row at most once; not true here, where two different faces can touch the
same cell pair).

**Both invariants become loud runtime assertions**, checked once per
mesh (on a cache miss only, so they cost nothing on the hot path):

- `_assert_uniform_cell_volume` raises `NonUniformCellVolumeError` if
  `{mesh.cell_volume(c) for c in range(mesh.num_cells)}` has more than
  one distinct value. `O(num_cells)`, negligible next to the build this
  replaces.
- `_assert_zero_gradient_pressure_boundary` raises
  `UnsupportedPressureBoundaryConditionError` if any of the four named
  pressure boundary conditions isn't zero-gradient. At most 4
  `evaluate` calls, against any one real boundary face of the mesh.

No new geometry-cache dataclass: unlike `PISO._rhie_chow_geometry`,
nothing else needs this exact stencil, so the sparse `(row, col, value)`
triples are built directly inside `_poisson_matrix`, still cached under the existing
`self._cached_poisson_mesh`/`self._cached_poisson_matrix` attribute
names (three existing tests read `piso._cached_poisson_matrix` directly
and needed no change). `simulation._flux_geometry` is deliberately not
reused -- its periodic-blind `has_neighbour` is exactly the subtlety
above, and every other numerics class (diffusion, gradient, divergence)
already owns its own face geometry independently rather than sharing one.

---

# Alternatives Considered

## Keep the probe loop, vectorise it via a batched basis-vector pass

Considered: run all `num_cells` basis vectors through `flux`/
`accumulate_flux_to_cells` at once with an added batch dimension, rather
than one Python-level call per cell. Rejected -- `DiffusionScheme.flux`
and `accumulate_flux_to_cells` are the interfaces every field in the
engine goes through; adding batch-dimension support to both for this one
caller would either speculatively widen a public interface (P-016) or
need a parallel, batched-only code path duplicating the same formula a
third time. The direct construction below duplicates the stencil formula
once, not the whole operator pipeline.

## Assert the invariants but keep hard-coded constants instead of reading mesh geometry

Considered, then dropped once face area and cell volume turned out to be
cheap and already available per-mesh (`mesh.face_area`, `mesh.
cell_volume`) -- reading them directly from the mesh, rather than
assuming `dx`/`dy` values, means the construction is correct for any
uniform-volume structured mesh's actual spacing, not only a
hard-coded shape. The assertions guard the two facts that genuinely
cannot vary today (pressure's own boundary treatment, and whether every
cell shares one volume), not the mesh's numeric dimensions, which the
construction reads rather than assumes.

---

# Consequences

**Positive**

- The Poisson-matrix build drops from `O(num_cells * num_faces)` to
  `O(num_faces)` -- measured directly: ~52s -> ~0.012s at 1024 cells
  (roughly 4200x), and the build now scales linearly with cell count
  rather than quadratically (0.005s / 0.012s / 0.046s at 256 / 1024 /
  4096 cells).
- The five-frame demo this whole investigation is anchored to drops from
  ~6.85s to ~5.46s at 32x32, now within ordinary run-to-run noise of the
  ~5.1-5.6s 16x16 baseline -- the original ~10x-for-4x-cells gap ADR-011
  could only partly explain is closed.
- Both invariants ADR-011 flagged as a correctness risk are now checked,
  not assumed -- a future PISO change that makes pressure's own boundary
  treatment configurable, or a future `Mesh` variant with non-uniform
  cell volumes, fails loudly building the matrix instead of silently
  producing a wrong one.
- `tests/unit/test_piso_pressure_coupling.py`'s own matrix-comparison
  tests (an independent reference-formula construction, parametrised
  over four periodicity configurations, plus a hand-derived-by-hand
  minimal case) are now a permanent regression guard against this exact
  class of subtle sign/coincidence error, not only a one-time check
  during planning.

**Negative**

- The direct construction duplicates the central-difference stencil
  formula in a second place (`_poisson_matrix` itself, alongside
  `CentralDifferenceDiffusion.flux`) -- exactly the cost ADR-011's own
  Alternatives named as the reason to defer this. Mitigated, not
  eliminated: the two new assertions mean a future change to either
  invariant fails loudly rather than silently, but a future change to
  the *stencil formula itself* (e.g. a non-orthogonal mesh) would still
  need this construction updated by hand, in step with `diffusion.py`'s
  own formula, with nothing mechanical enforcing that they stay in sync.
- The periodic-face contribution's own asymmetry (one-sided, relying on
  the paired face to supply the other half) is a genuinely subtle piece
  of reasoning, verified here but not obvious from reading
  `_poisson_matrix` alone without also reading `accumulate_flux_to_cells`
  and `simulation._flux_geometry` -- a future contributor changing either
  needs to re-read this ADR, not just the function they are editing.
- A small, unmeasured migration risk in the assertion's own performance:
  `_assert_uniform_cell_volume` is `O(num_cells)`, run once per mesh --
  negligible today, but would need revisiting if `Mesh.cell_volume`
  itself ever became expensive to call per cell.

---

# Notes

Recorded against `docs/planning/roadmap.md`'s TASK-026 (a revisit
paragraph in context, alongside ADR-011's own, with the full measured
before/after) rather than a new roadmap task -- this is a direct
completion of the alternative ADR-011 already named and deferred, the
same "revisit, not a new task" shape ADR-011 itself used for TASK-026's
own dense-matrix decision. `src/pyflow/engine/CLAUDE.md`'s own `PISO`
entry, `examples/experiments/CLAUDE.md`'s running investigation tally,
and `adr/ADR-011-sparse-linear-solver-matrix.md`'s own Negative
consequence (a one-line pointer) are updated in the same change.
