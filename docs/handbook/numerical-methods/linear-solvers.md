# Linear Solvers

Per `docs/planning/knowledge-architecture.md` KA-024. The role of
linear-system solvers in PyFlow's engine, and the candidates for
interchangeable implementation.

Depends on `pressure-velocity-coupling.md` (the algorithm producing the
system to be solved) and `fvm.md`.

---

## Where the Linear System Comes From

`pressure-velocity-coupling.md`'s pressure-correction step reduces to a
large, sparse linear system: one equation per cell, relating that cell's
pressure correction to its neighbours' -- structurally a discrete Poisson
equation. Solving this system every pressure-correction pass is the
single most computationally expensive step in an incompressible FVM
timestep, which is why the Linear Solver layer is architecturally
separate from pressure-velocity coupling itself
(`docs/architecture/engine.md`) rather than bundled inside it: the same
solver machinery would also be needed by any future implicit time
integration (`time-integration.md`).

## Iterative vs. Direct Methods

A **direct** method (e.g. Gaussian elimination/LU decomposition) computes
the exact solution (up to floating-point error) in a fixed, predictable
number of operations, but for a large sparse system arising from a 2D or
3D mesh, the intermediate matrix fill-in a direct method produces makes
both its memory and computational cost grow far faster than the
system's sparsity would suggest -- impractical for the mesh sizes CFD
simulations typically use.

An **iterative** method instead starts from an initial guess and
successively refines it, each iteration costing roughly one sparse
matrix-vector multiply (cheap, proportional to the number of non-zero
matrix entries, itself proportional to mesh face count) rather than a
full factorisation. The trade is a solution that is only *approximately*
correct after any finite number of iterations, controlled by an explicit
convergence criterion (below) -- but for the sparse, well-structured
systems FVM produces, iterative methods reach acceptable accuracy far
more cheaply than a direct solve would. This is why every candidate named
here, and PyFlow's MVP choice, is iterative.

## Conjugate Gradient

**Conjugate Gradient (CG)** is an iterative method for systems whose
matrix is **symmetric positive-definite** -- a property the discrete
Poisson-type pressure-correction system genuinely has on PyFlow's MVP
mesh (`docs/architecture/icds.md`'s Linear Solver ICD notes this
explicitly as a real compatibility requirement, not an incidental
detail). CG converges to the exact solution in at most as many iterations
as the system has unknowns in principle, but in practice converges to an
acceptable approximation in far fewer iterations for well-conditioned
systems, with convergence rate governed by the matrix's condition number.

CG is PyFlow's MVP choice, matched exactly to the pressure-correction
system PISO produces on a uniform Cartesian mesh, where the system is
both symmetric positive-definite and comparatively well-conditioned.

## BiCGSTAB

**BiCGSTAB** (Biconjugate Gradient Stabilised) generalises CG's idea to
systems that are **not** symmetric -- a broader class of matrix than CG
can handle, at the cost of a less predictable convergence pattern (it can
stagnate or converge non-monotonically, unlike CG's smoother behaviour on
suitable systems) and roughly double the per-iteration cost. It becomes
relevant the moment a future linear system PyFlow needs to solve is not
symmetric -- a different pressure-coupling formulation, or a system
arising from implicit time integration of a non-self-adjoint operator,
for example.

## Multigrid

**Multigrid** methods take a fundamentally different approach:
smoothing the error on the original (fine) mesh, then transferring the
remaining error to a sequence of coarser meshes where it can be resolved
far more cheaply (fewer unknowns), before interpolating the correction
back up to the fine mesh. Done well, multigrid convergence rate is
*independent of mesh resolution* -- a qualitative advantage over CG and
BiCGSTAB, whose iteration counts grow as the mesh is refined (worsening
condition number). The cost is significant implementation complexity: a
hierarchy of coarser meshes (or an algebraic equivalent that does not
need an explicit geometric hierarchy) must be constructed and
maintained.

## Preconditioning

A **preconditioner** transforms a linear system into an equivalent one
with more favourable convergence properties (typically a better-clustered
eigenvalue spectrum, meaning a lower effective condition number) before
or during an iterative solve -- CG and BiCGSTAB are both commonly paired
with a preconditioner in production use, and the choice of preconditioner
often affects convergence more than the choice between CG-family
algorithms themselves. Multigrid is frequently used *as* a preconditioner
for CG/BiCGSTAB rather than as a standalone solver, combining multigrid's
resolution-independent convergence with CG's robustness on
well-conditioned systems.

## Convergence Criteria

An iterative solver needs an explicit stopping rule -- typically a target
**residual** (how far the current approximate solution is from
satisfying the system exactly, measured in some norm) below which the
solution is considered acceptable, since iterating indefinitely for exact
convergence is neither necessary nor guaranteed to terminate in finite
time for most methods. The appropriate residual tolerance is a genuine
trade-off between solution accuracy and computational cost, and is itself
part of what an implementation of this layer configures.

## Memory and Computational Cost

All three iterative methods here need memory proportional to the number
of non-zero matrix entries plus a small constant number of full-length
vectors (CG: a handful; BiCGSTAB: somewhat more; multigrid: additionally,
storage for the coarser-mesh hierarchy) -- far less than a direct
method's fill-in. Per-iteration cost is dominated by the sparse
matrix-vector product, proportional to mesh face count; total cost is
that per-iteration cost times the number of iterations needed to reach
the convergence criterion, which is where the condition-number
sensitivity described above actually matters in practice.

## Applicability Summary

| Solver       | Requires             | Convergence vs. mesh size | Typical role                        |
| ------------ | --------------------- | -------------------------- | ------------------------------------ |
| CG            | Symmetric positive-definite | Degrades with refinement | PyFlow's MVP; well-conditioned symmetric systems |
| BiCGSTAB      | Any (non-symmetric OK) | Degrades with refinement | Non-symmetric systems CG cannot handle |
| Multigrid     | A mesh hierarchy (geometric or algebraic) | Independent of resolution | Large/fine meshes; often as a preconditioner |

## References

- Saad, Y., *Iterative Methods for Sparse Linear Systems*, 2nd ed., SIAM,
  2003. The standard comprehensive reference for CG, BiCGSTAB,
  preconditioning, and their convergence theory.
- Hestenes, M.R. and Stiefel, E., "Methods of conjugate gradients for
  solving linear systems", *Journal of Research of the National Bureau
  of Standards*, 49(6), 1952, pp. 409-436. The original CG method.
- Van der Vorst, H.A., "Bi-CGSTAB: A fast and smoothly converging variant
  of Bi-CG for the solution of nonsymmetric linear systems", *SIAM
  Journal on Scientific and Statistical Computing*, 13(2), 1992, pp.
  631-644. The original BiCGSTAB method.
- Briggs, W.L., Henson, V.E., and McCormick, S.F., *A Multigrid
  Tutorial*, 2nd ed., SIAM, 2000. An accessible introduction to geometric
  and algebraic multigrid.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3i), against
`pressure-velocity-coupling.md` and `fvm.md`.
