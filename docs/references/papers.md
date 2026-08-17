# Paper References

Per `docs/planning/backlog.md` E6. Full citations for every journal
article/paper referenced from `docs/handbook/`. Populated from what the
Handbook entries actually cite (`docs/planning/backlog.md` E3/E4) -- see
`books.md` for the same convention applied to books/monographs.

---

## Numerical Methods

- Rhie, C.M. and Chow, W.L. (1983). "Numerical study of the turbulent
  flow past an airfoil with trailing edge separation." *AIAA Journal*,
  21(11), 1525-1532. Cited by: `variable-placement.md`. The original
  collocated-grid interpolation correction.
- Leonard, B.P. (1979). "A stable and accurate convective modelling
  procedure based on quadratic upstream interpolation." *Computer
  Methods in Applied Mechanics and Engineering*, 19(1), 59-98. Cited by:
  `advection.md`. The original QUICK scheme.
- Sweby, P.K. (1984). "High resolution schemes using flux limiters for
  hyperbolic conservation laws." *SIAM Journal on Numerical Analysis*,
  21(5), 995-1011. Cited by: `advection.md`. The standard TVD
  flux-limiter reference.
- Courant, R., Friedrichs, K., and Lewy, H. (1928). "Über die partiellen
  Differenzengleichungen der mathematischen Physik." *Mathematische
  Annalen*, 100(1), 32-74. Cited by: `time-integration.md`. The original
  CFL condition.
- Issa, R.I. (1986). "Solution of the implicit discretised fluid flow
  equations by operator-splitting." *Journal of Computational Physics*,
  62(1), 40-65. Cited by: `pressure-velocity-coupling.md`. The original
  PISO algorithm -- PyFlow's MVP pressure-velocity coupling choice
  (`adr/ADR-002-fvm-first.md`, `docs/implementation/mvp.md`).
- Patankar, S.V. and Spalding, D.B. (1972). "A calculation procedure for
  heat, mass and momentum transfer in three-dimensional parabolic
  flows." *International Journal of Heat and Mass Transfer*, 15(10),
  1787-1806. Cited by: `pressure-velocity-coupling.md`. The original
  SIMPLE algorithm.
- Van Doormaal, J.P. and Raithby, G.D. (1984). "Enhancements of the
  SIMPLE method for predicting incompressible fluid flows." *Numerical
  Heat Transfer*, 7(2), 147-163. Cited by: `pressure-velocity-coupling.md`.
  The original SIMPLEC algorithm.
- Hestenes, M.R. and Stiefel, E. (1952). "Methods of conjugate gradients
  for solving linear systems." *Journal of Research of the National
  Bureau of Standards*, 49(6), 409-436. Cited by: `linear-solvers.md`.
  The original Conjugate Gradient method -- PyFlow's MVP linear-solver
  choice (`adr/ADR-002-fvm-first.md`, `docs/implementation/mvp.md`).
- Van der Vorst, H.A. (1992). "Bi-CGSTAB: A fast and smoothly converging
  variant of Bi-CG for the solution of nonsymmetric linear systems."
  *SIAM Journal on Scientific and Statistical Computing*, 13(2), 631-644.
  Cited by: `linear-solvers.md`. The original BiCGSTAB method.

## Physics

None yet -- every physics-entry citation so far (`docs/planning/
backlog.md` E4) is to a book/monograph (`books.md`), not a journal
article. Add an entry here the moment a physics Handbook entry cites one.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E6b), transcribed
directly from every paper citation in the ten numerical-methods Handbook
entries written the same session (E3) -- not independently researched.
Update this list, not just the citing entry, whenever a Handbook entry's
references section changes (Blast Radius, `docs/practices.md`).
