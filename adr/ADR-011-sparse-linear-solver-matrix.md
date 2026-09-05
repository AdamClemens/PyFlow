# ADR-011: LinearSolver's matrix Parameter Widens to Permit Sparse Tensors

**Status:** Accepted

---

# Context

TASK-022 (Stage 3, done 2026-08-23) gave `LinearSolver` this contract
(`src/pyflow/engine/numerics/linear_solver.py`):

> `matrix` is a dense `(n, n)` tensor, not sparse or matrix-free -- an
> explicit choice, not a gap: nothing in `icds.md`/the handbook mandates
> a code-level representation, MVP meshes are small enough that a dense
> matrix is a real option, and nothing under `src/` depends on this
> choice yet (Criterion 1), so it stays reversible until TASK-026's
> concrete Conjugate Gradient implementation needs to revisit it (per
> the handbook's own "large, sparse" framing of the real
> pressure-correction system).

TASK-026 (Stage 4, 2026-08-27) closed that note "did not need to" --
MVP mesh sizes stayed small enough that the dense representation
remained a non-issue -- but named its own reopening condition directly:
**"revisit if a later stage's mesh sizes make the dense representation
impractical."**

That condition fired on 2026-09-05. Generating a higher-resolution
variant of the smoke-transport demo
(`examples/experiments/smoke_transport_high_res.yaml`, 16x16 -> 32x32
cells, 4x the cell count) measured a ~10x slowdown for the same five
rendered frames -- steeper than the 4x cell-count increase alone
predicts. The initial diagnosis pointed at `PISO`'s
`ConjugateGradientSolver`, which does `matrix @ direction` every CG
iteration against a **dense** `(N, N)` tensor even though the underlying
discretisation is a 5-point stencil (~5 nonzeros per row) -- dense matvec
is `O(N^2)`, and the matrix's condition number also grows with `N`, so
CG needs more iterations at higher resolution too.

**That diagnosis was only partly right, found by isolated measurement
after implementing, not assumed correct in advance.** Timed separately:
the CG solve alone *is* meaningfully faster sparse than dense at 1024
cells (2.56x, dense vs. sparse, same solver, same problem, identical
iteration counts -- confirming no numerical change), and that gap should
keep growing with resolution. But `PISO._poisson_matrix`'s own
`O(num_cells * num_faces)` construction cost -- unchanged in complexity
by this decision, since the accepted approach (below) keeps the existing
per-column probe loop -- measured at 3.5s (16x16) and 52s (32x32) on the
same mesh, against 0.003s and 0.02s for the solve itself. **The build,
not the solve, is what dominated the originally-measured ~10x/4x-cells
demo slowdown**, by roughly three orders of magnitude at these mesh
sizes; that cost is real, already flagged (Alternatives, below), and
deliberately not addressed by this decision. This ADR records a genuine,
verified improvement to the solve's own scaling -- necessary for a
long-running simulation where the build cost is amortised across many
timesteps and the solve comes to dominate -- not a fix for the specific
symptom that motivated looking at this in the first place.

This is a direct revisit of TASK-026's own reversible decision, not a
new roadmap task -- `docs/planning/roadmap.md`'s TASK-022/TASK-026
entries carry the full record.

---

# Decision

**`LinearSolver.solve`'s `matrix` parameter widens to permit either a
dense (`torch.strided`) or sparse (`torch.sparse_coo`/`torch.sparse_csr`)
tensor.** Any concrete implementation must accept both.

`PISO._poisson_matrix` (`src/pyflow/engine/numerics/pressure_coupling.py`)
is the first, and so far only, producer of a sparse matrix: its existing
per-column probe loop (`self._diffusion.flux(basis)` +
`accumulate_flux_to_cells`, unchanged) now collects each column's
nonzero rows as sparse `(row, col, value)` triples instead of writing into a dense `(N,N)`
tensor, assembled once via `torch.sparse_coo_tensor(...).coalesce().to_sparse_csr()`.

`ConjugateGradientSolver`'s arithmetic needed exactly one change:
`torch.linalg.matrix_norm(matrix)` raises `NotImplementedError` on a
sparse layout (verified directly against this repository's pinned
`torch==2.13.0+cpu`), replaced by a new `_frobenius_norm(matrix)` helper
that branches on `matrix.layout` -- dense: the same call, unchanged;
sparse: `sqrt(sum(values()**2))`, confirmed to match the dense result to
full float64 precision. Everything else in `solve` -- `matrix @
direction`, the null-space row-sum check (`matrix @ torch.ones(...)`),
the residual/direction updates -- needed no change: sparse-times-dense-vector
matmul is already identical to dense for a 1-D right-hand side.

Three test-only doubles across the contract suites call a dense-only
`torch.linalg` operation on `matrix` and needed a `.to_dense()` guard
before that call: `_ExactSolver`/`_JacobiSolver`
(`tests/unit/numerics/test_linear_solver_contract.py`, `torch.linalg.solve`/
`torch.diagonal`), `_StubLinearSolver`
(`tests/unit/numerics/test_pressure_coupling_contract.py`,
`torch.linalg.lstsq`), and `_HalvingSolver`
(`tests/unit/test_pressure_correction_loop.py`, `torch.linalg.lstsq`).
None of these are performance-sensitive -- they exist to prove
correctness on small fixtures, not to be fast.

---

# Alternatives Considered

## Hide sparsity behind `torch.sparse.mm` internally, keep `matrix` nominally dense-typed

Rejected. `matrix`'s type hint is already the plain `torch.Tensor` both
layouts share, so nothing forces this -- but describing the parameter as
"always dense" in the class docstring while a real producer hands it a
sparse tensor would be dishonest about what the contract actually
permits, exactly the kind of restated fact this repository's own
practices warn against.

## A sibling `SparseLinearSolver` ABC

Rejected, for the identical reason `adr/ADR-008` rejected the analogous
split for `TimeIntegrator`: it would mean two interfaces for "solve a
linear system", with a caller needing to know out of band which one a
configured strategy implements -- `adr/ADR-003-modular-numerical-
strategies.md`'s "one interface, interchangeable implementations"
premise breaks the moment that's true.

## Direct per-face O(num_faces) Poisson-matrix construction, bypassing the probe loop

Considered as the more asymptotically efficient build (this
discretisation's sparsity pattern is knowable per-face, without probing
column by column), and rejected **for now, not because it wouldn't
help** -- measurement after the fact showed the build, not the solve, is
what actually dominates a short run (Context, above), so this
alternative would likely have mattered more than what was built. Set
aside anyway because it would duplicate the central-difference stencil
formula in a second place and hard-code two facts that are only true of
`PISO`'s *current* wiring -- a zero-gradient pressure boundary on every
wall, and uniform cell volume -- with nothing asserting they stay true
if either changes; that is a real correctness risk this decision chose
not to take in the same change as a first sparse-representation change,
not a judgment that the build doesn't matter. Revisit directly, now that
the build's real cost is measured rather than assumed amortised-away.

## Keep dense, add a preconditioner instead

Rejected. A preconditioner can reduce CG's iteration count, but does
nothing about the `O(N^2)` cost of each dense matvec, or the `O(N^2)`
memory floor (a 128x128 mesh needs roughly 2.1GB dense at float64) --
it treats a symptom of the representation choice, not the choice itself.

---

# Consequences

**Positive**

- Removes the `O(N^2)` memory floor entirely (`O(nnz)` instead), and
  turns each CG matvec from `O(N^2)` to `O(nnz)` -- measured directly as
  a 2.56x solve-only speedup at 1024 cells (16x16 solve was, if
  anything, marginally slower sparse than dense -- sparse overhead loses
  to dense BLAS below some crossover size not yet located), with the gap
  expected to grow further at higher resolution. This matters for a
  long-running simulation, where the (unchanged-by-this-decision) build
  cost amortises across many timesteps and the solve comes to dominate.
- Closes the gap between `docs/handbook/numerical-methods/
  linear-solvers.md`'s own performance model (already stated as "per-
  iteration cost is dominated by the sparse matrix-vector product,
  proportional to mesh face count") and what the code actually did.
- Any future `LinearSolver` implementation inherits the honest,
  already-proven-generic contract (`tests/unit/numerics/
  test_linear_solver_contract.py`'s sparse scenario runs against every
  registered factory, not only `ConjugateGradientSolver`).

**Negative**

- **Does not fix the ~10x-per-4x-cells slowdown that motivated looking
  at this at all.** That symptom is dominated by `PISO._poisson_matrix`'s
  own `O(num_cells * num_faces)` build cost (measured at 3.5s/52s for
  16x16/32x32, against 0.003s/0.02s for the solve alone on the same
  mesh) -- three orders of magnitude larger than the solve at these
  sizes, and unchanged in complexity by this decision. A short-running
  demo like `examples/experiments/smoke_transport_high_res.yaml` (five
  frames) pays this build cost once and barely reaches the solve at all;
  this fix is invisible there. Fixing the build itself is the rejected
  Alternative above (a per-face `O(num_faces)` construction), not
  attempted here.
- A real, one-time migration cost: four test-only doubles across three
  files needed a `.to_dense()` guard before calling a dense-only
  `torch.linalg` operation.
- The widened contract is not something `mypy --strict` can fully
  enforce -- both layouts share the same `torch.Tensor` type, so a
  future implementation that silently assumes dense (e.g. calling
  `torch.diagonal` without guarding) would only be caught by the
  contract suite's sparse scenario at runtime, not by the type checker.
- A small, unmeasured one-time cost from `coalesce()`/`to_sparse_csr()`
  conversion when the matrix is first built per mesh -- amortised the
  same way the dense construction cost already was, but not separately
  profiled.

---

# Notes

Recorded against `docs/planning/roadmap.md`'s TASK-022 (a short
correction pointer, not a rewrite of that closed record) and TASK-026
(the full revisit, in context, including the measured before/after
timing). `src/pyflow/engine/CLAUDE.md`'s own `linear_solver.py`/
`pressure_coupling.py` entries and `src/pyflow/engine/numerics/CLAUDE.md`
are updated in the same change.
