# Advection

Per `docs/planning/knowledge-architecture.md` KA-020. Advection
discretisation -- how a transported field's face value is estimated for
the advective part of a face flux (`fluxes.md`) -- and PyFlow's planned
interchangeable advection strategy.

This is the numerical-scheme entry corresponding to
`docs/architecture/engine.md`'s "Advection" layer and
`docs/architecture/icds.md`'s Advection ICD; this document explains what
each scheme *is* and why it behaves the way it does, not PyFlow's
specific interface.

---

## The Problem

Advection transports a field $\phi$ at the local flow velocity. FVM needs
the face value $\phi_{\text{face}}$ to multiply against the face's mass
flux (`fluxes.md`), but $\phi$ is only known at cell centres -- so
$\phi_{\text{face}}$ must be *estimated* from the neighbouring
cell-centred values. Every advection scheme is a rule for making that
estimate, and the schemes below differ in how many neighbouring cells
they use and how they weight them.

## Upwind

The simplest and most robust rule: $\phi_{\text{face}}$ equals the
cell-centred value of whichever neighbour the flow is coming *from* (the
upstream, or "upwind," cell), determined by the sign of the face's mass
flux.

**Stability:** unconditionally bounded -- the face value is always one of
the two actual neighbouring cell values, so it can never overshoot or
introduce a value outside the range already present in the solution.

**Accuracy:** only first-order accurate. Because the scheme effectively
ignores the field's gradient across the face (using a single upstream
value regardless of how $\phi$ is actually varying there), it introduces
**numerical diffusion** -- an artificial smoothing effect, mathematically
equivalent to adding an extra diffusion term the true physics does not
have, whose magnitude grows with the local flow velocity and cell size.
This is what "first-order upwind is numerically diffusive" means
concretely, and it is PyFlow's MVP choice
(`docs/implementation/mvp.md`) precisely because unconditional
boundedness makes it the safest starting point to validate the rest of
the engine architecture against, even though it is the least accurate
option on the upgrade path.

## Central Difference

$\phi_{\text{face}}$ is estimated by linear interpolation between the two
neighbouring cell-centred values, weighted by distance to the face.

**Accuracy:** second-order accurate on a uniform mesh -- it does account
for the field's local gradient, unlike upwind, and so introduces
substantially less numerical diffusion.

**Stability:** *not* unconditionally bounded. Central differencing can
produce a face value outside the range of its two neighbours when the
flow is advection-dominated relative to diffusion (a high cell **Péclet
number**, the ratio of advective to diffusive transport at the scale of
one cell) -- manifesting as non-physical oscillation near sharp
gradients. This is the direct accuracy-vs-boundedness trade-off
`fluxes.md` describes: central buys accuracy at the cost of the
guarantee upwind provides for free.

## Higher-Order and TVD Schemes

**QUICK** (Quadratic Upstream Interpolation for Convective Kinematics)
fits a quadratic curve through the upwind and downwind neighbours plus
one further upstream cell, giving third-order accuracy on a uniform
mesh -- more accurate than central differencing, but with a wider
stencil (three cells instead of two) and no boundedness guarantee of its
own.

**TVD (Total Variation Diminishing)** schemes are not a single scheme but
a *design constraint*: a TVD scheme is constructed so that the total
variation of the discrete solution (informally, the sum of all its
up-and-down swings) cannot increase from one timestep to the next, which
rules out the spurious new oscillations central differencing and QUICK
can introduce near sharp gradients. TVD schemes typically achieve this by
**flux limiting** -- blending between a low-order bounded scheme
(upwind) and a higher-order scheme (central or QUICK) based on the local
smoothness of the solution, using the higher-order scheme where the field
is smooth and falling back toward upwind exactly where a sharp gradient
would otherwise cause oscillation. This is what makes TVD schemes able to
combine boundedness with better-than-first-order accuracy almost
everywhere, at the cost of the extra logic needed to detect local
smoothness and blend accordingly.

## Numerical Diffusion, Stability, Boundedness

Three properties recur across every scheme above and are worth naming
precisely, since they are exactly what
`docs/architecture/icds.md`'s Advection ICD's "expected behaviour" and
"limitations" sections summarise per scheme:

- **numerical diffusion** -- artificial smoothing a scheme introduces
  beyond the true physical diffusion, largest for upwind, smallest for
  higher-order schemes;
- **stability** -- whether small errors grow or decay over successive
  timesteps (distinct from boundedness, though related);
- **boundedness** -- whether a scheme can produce a face/cell value
  outside the physically sensible range implied by its neighbours,
  which is what causes visible oscillation near sharp gradients.

No scheme surveyed here maximises all three simultaneously; a TVD scheme
is the closest to achieving both boundedness and good accuracy, at the
cost of implementation complexity.

## Computational Cost

Cost per face grows with stencil width: upwind and central both use only
the two immediate neighbours (cheapest), QUICK needs one additional
upstream cell, and TVD schemes need the same wider stencil plus the
limiter computation itself. None of these change the *asymptotic* cost
scaling described in `fluxes.md` (still linear in face count) -- the
difference is a constant-factor cost per face, not a different scaling
regime.

## Upgrade Paths

`docs/implementation/upgrade-paths.md`'s "Advection" entry: upwind →
central difference → QUICK → TVD → WENO. This is a genuine complexity/
accuracy progression, not an arbitrary list -- WENO (Weighted Essentially
Non-Oscillatory) schemes generalise the same flux-limiting idea behind
TVD to still-higher formal order while retaining boundedness near sharp
features, at further implementation cost (`overview.md`'s note that
very-high-order WENO is more naturally expressed in
finite-difference-adjacent formulations is the same reason
`adr/ADR-002-fvm-first.md` treats it as a possible future capability
level rather than an FVM-native extension).

## References

- Versteeg, H.K. and Malalasekera, W., *An Introduction to Computational
  Fluid Dynamics: The Finite Volume Method*, 2nd ed., Pearson, 2007. Ch.
  5 covers upwind, central, QUICK and TVD/flux-limiter schemes with
  worked stability analysis.
- Leonard, B.P., "A stable and accurate convective modelling procedure
  based on quadratic upstream interpolation", *Computer Methods in
  Applied Mechanics and Engineering*, 19(1), 1979, pp. 59-98. The
  original QUICK scheme.
- Sweby, P.K., "High resolution schemes using flux limiters for
  hyperbolic conservation laws", *SIAM Journal on Numerical Analysis*,
  21(5), 1984, pp. 995-1011. The standard reference for TVD flux
  limiters and the boundedness criteria they satisfy.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E3e), against `fvm.md`
and `fluxes.md`.
