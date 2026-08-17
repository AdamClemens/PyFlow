# Book References

Per `docs/planning/backlog.md` E6. Full citations for every book/
monograph referenced from `docs/handbook/`. Populated from what the
Handbook entries actually cite (`docs/planning/backlog.md` E3/E4) --
add an entry here the moment a future Handbook entry cites a new book,
in the same change, rather than letting citations drift out of sync with
this list.

Entries are grouped by which handbook area cites them; a book cited from
both areas is listed once, under the area it was first cited from, with
a note.

---

## Numerical Methods

- Versteeg, H.K. and Malalasekera, W. (2007). *An Introduction to
  Computational Fluid Dynamics: The Finite Volume Method*, 2nd ed.
  Pearson. Cited by: `fvm.md`, `meshes.md`, `variable-placement.md`,
  `fluxes.md`, `advection.md`, `diffusion.md`,
  `pressure-velocity-coupling.md`, `boundary-conditions.md`; also cited
  by `adr/ADR-002-fvm-first.md`. The standard introductory FVM textbook,
  and the closest thing this handbook has to a single core reference.
- Patankar, S.V. (1980). *Numerical Heat Transfer and Fluid Flow*.
  Hemisphere Publishing. Cited by: `fvm.md`, `variable-placement.md`.
- Ferziger, J.H., Perić, M., and Street, R.L. (2020). *Computational
  Methods for Fluid Dynamics*, 4th ed. Springer. Cited by: `fvm.md`,
  `meshes.md`, `diffusion.md`, `time-integration.md`,
  `boundary-conditions.md`.
- Saad, Y. (2003). *Iterative Methods for Sparse Linear Systems*, 2nd
  ed. SIAM. Cited by: `linear-solvers.md`.
- Briggs, W.L., Henson, V.E., and McCormick, S.F. (2000). *A Multigrid
  Tutorial*, 2nd ed. SIAM. Cited by: `linear-solvers.md`.
- Butcher, J.C. (2016). *Numerical Methods for Ordinary Differential
  Equations*, 3rd ed. Wiley. Cited by: `time-integration.md`.
- LeVeque, R.J. (2002). *Finite Volume Methods for Hyperbolic Problems*.
  Cambridge University Press. Cited by: `fluxes.md`.

## Physics

- Kundu, P.K., Cohen, I.M., and Dowling, D.R. (2015). *Fluid Mechanics*,
  6th ed. Academic Press. Cited by: `incompressible-flow.md`,
  `heat-transfer.md`, `density.md`, `buoyancy.md`.
- Batchelor, G.K. (1967). *An Introduction to Fluid Dynamics*. Cambridge
  University Press. Cited by: `incompressible-flow.md`.
- Incropera, F.P., DeWitt, D.P., Bergman, T.L., and Lavine, A.S. (2011).
  *Fundamentals of Heat and Mass Transfer*, 7th ed. Wiley. Cited by:
  `heat-transfer.md`.
- Bird, R.B., Stewart, W.E., and Lightfoot, E.N. (2007). *Transport
  Phenomena*, 2nd ed. Wiley. Cited by: `humidity.md`.
- Turner, J.S. (1973). *Buoyancy Effects in Fluids*. Cambridge
  University Press. Cited by: `density.md`, `buoyancy.md`.
- Rogers, R.R. and Yau, M.K. (1989). *A Short Course in Cloud Physics*,
  3rd ed. Butterworth-Heinemann. Cited by: `humidity.md`,
  `cloud-formation.md`.
- Wallace, J.M. and Hobbs, P.V. (2006). *Atmospheric Science: An
  Introductory Survey*, 2nd ed. Academic Press. Cited by: `humidity.md`,
  `buoyancy.md`, `cloud-formation.md`.
- Boussinesq, J. (1903). *Théorie Analytique de la Chaleur*, Vol. 2.
  Gauthier-Villars. Cited by: `density.md`. The original source of the
  Boussinesq approximation `density.md` and `buoyancy.md` both use;
  listed here as a monograph rather than under Papers since it is a
  multi-volume treatise, not a journal article.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E6a), transcribed
directly from every book citation in the sixteen Handbook entries
written the same session (E3/E4) -- not independently researched. Update
this list, not just the citing entry, whenever a Handbook entry's
references section changes (Blast Radius, `docs/practices.md`).
