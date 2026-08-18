# CLAUDE

Numerical Component Handbook entries, per
`docs/planning/knowledge-architecture.md` KA-016 through KA-025. These
explain numerical concepts independently of their eventual PyFlow
implementation.

`overview.md` (KA-007, the numerical method survey) and
`compatibility.md` (KA-008) hold real content -- they lived at
`docs/planning/numerical-frameworks.md` until 2026-08-15, when they were
moved to the KA-specified paths and split, and remain the natural source
the per-method entries draw from.

All ten KA-016..025 entries were written 2026-08-17
(`docs/planning/backlog.md` E3), in the dependency order the backlog
laid out: `fvm.md` first (since `adr/ADR-002-fvm-first.md` already
referenced it), then `meshes.md`, `variable-placement.md`, `fluxes.md`,
`advection.md`, `diffusion.md`, `time-integration.md`,
`pressure-velocity-coupling.md`, `linear-solvers.md`, and
`boundary-conditions.md` last. Every entry cites authoritative sources,
per the standing caution below -- same caution as
`docs/handbook/physics/`. Do not write numerical-methods content without
citing authoritative sources; this is exactly the kind of domain content
where a confident-sounding but wrong claim is costly.

**Reviewed for scientific accuracy 2026-08-18** (maintainer's request:
review the Handbook and architecture documents for scientific accuracy,
relevance and readability). Every entry here changed; each one's own
Maintenance section records what and why. Three conventions were settled
in that pass and bind anything written here afterwards:

- **One notation, fixed by `fvm.md`.** $\phi$ is a specific (per unit
  mass) quantity and $\Gamma$ is a density-weighted diffusivity, with the
  constant-density divided-through form named as the alternative. The
  entries previously disagreed about whether $\rho$ appeared, which made
  `fvm.md`'s and `fluxes.md`'s flux expressions dimensionally
  inconsistent with each other. A new entry either follows `fvm.md`'s
  convention or says at the top which one it uses.
- **Boundedness, stability and accuracy are three properties, not one.**
  Upwind is unconditionally *bounded*; it is not unconditionally stable,
  because stability depends on the time integrator too. Second-order
  *accurate* does not mean bounded. `fluxes.md`'s "Stability and Accuracy
  Implications" states the distinction and is the place to point at
  rather than restate.
- **Attribute a claim to the document that actually makes it.** The WENO
  paragraph in `advection.md` cited `overview.md` for a point `overview.md`
  never makes (it comes from `adr/ADR-002-fvm-first.md`). A cross-reference
  reads as authoritative whether or not it is; check the target says what
  is claimed, especially when the claim is one this handbook's own
  citations do not otherwise cover.

The standing caution above was also borne out concretely: the errors this
review found were confident, plausible sentences, not obviously shaky
ones. Prefer stating a limit of the model, or the scope of a guarantee,
over a clean claim that overreaches.

A fourth rule came out of `compatibility.md` specifically, on the second
pass: **when content is doubtful, re-read the KA entry's Content
Requirements before deciding what to do with it.** That document's
inherited frequency groupings were first annotated with a caution,
because rewriting unsourced labels would only have substituted one
judgement for another. Re-reading KA-008 settled it properly -- the spec
asks the document to distinguish seven kinds of compatibility and states
that it "should not collapse these into one compatibility label," which
is exactly what a frequency band does. The groupings were not merely
unsourced, they were against the spec, and the right action was to remove
them rather than caveat them. An honest caution is better than a silent
error, but it is not the ceiling; check whether the specification already
answers the question.
