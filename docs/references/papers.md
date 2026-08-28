# Paper References

Per `docs/planning/backlog.md` E6. Full citations for every journal
article/paper referenced from `docs/handbook/`. Populated from what the
Handbook entries actually cite (`docs/planning/backlog.md` E3/E4) -- see
`books.md` for the same convention applied to books/monographs.

**Scope extended 2026-08-28: also every paper a *completion criterion*
depends on.** Ghia, Ghia & Shin (1982) below is the first -- no Handbook
entry cites it, but `docs/planning/roadmap.md`'s Stage 5 Completion
Criterion 5 requires the lid-driven cavity's centreline profiles to be
compared against that paper's tabulated data, which makes finding the
paper a prerequisite for closing a stage rather than a nicety. Three
documents named it by author and year and none gave the volume, issue or
pages. The narrow rule this file was written under ("not somewhere to
add a reference that no Handbook entry cites yet",
`docs/references/CLAUDE.md`) is amended in the same change rather than
quietly broken.

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
- Saad, Y. and Schultz, M.H. (1986). "GMRES: A generalized minimal
  residual algorithm for solving nonsymmetric linear systems." *SIAM
  Journal on Scientific and Statistical Computing*, 7(3), 856-869. Cited
  by: `linear-solvers.md`. The original GMRES method -- added 2026-08-18
  with `linear-solvers.md`'s GMRES section, which closed a gap against
  `docs/implementation/upgrade-paths.md`'s Linear Solvers path naming
  GMRES where the handbook entry did not cover it.

## Validation Benchmarks

Papers whose published results a PyFlow acceptance or completion
criterion is checked against. Section added 2026-08-28 with its first
entry; see the scope note at the top of this file for why these belong
here despite not being Handbook citations.

- Ghia, U., Ghia, K.N., and Shin, C.T. (1982). "High-Re solutions for
  incompressible flow using the Navier-Stokes equations and a multigrid
  method." *Journal of Computational Physics*, 48(3), 387-411. Cited by:
  `docs/planning/roadmap.md` (Stage 5 Completion Criterion 5),
  `docs/planning/implementation-plan.md` (Level 2),
  `adr/ADR-007-executable-acceptance-criteria.md` (worked example),
  `docs/glossary.md` ("Validation"). The tabulated lid-driven-cavity
  centreline velocity profiles PyFlow's MVP golden demo is validated
  against. **Stage 5 adopts its Reynolds number 100 case but not
  ADR-007's illustrative 2% tolerance** -- see that criterion for why.

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
