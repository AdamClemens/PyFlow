# ADR-005: Compute-and-Rendering Stack — Instance Decision

**Status:** Accepted

---

# Context

`adr/ADR-004-compute-rendering-class.md` fixed Class 2: a GPU-capable,
NumPy-shaped array library paired with a general-purpose renderer, host
round-trip accepted as the default coupling. It deliberately left two
narrower decisions open -- the specific array library, and the specific
renderer -- as `docs/planning/backlog.md` A2c.

`docs/architecture/compute-and-rendering-stack.md` §6a and §5/§7 lay out
the comparison in full; this ADR records the decision and its rationale,
not the full evidence trail.

**Array library**, narrowed to CuPy vs. PyTorch (JAX set aside: its
immutable-array model is real, ongoing friction against a mutable
per-timestep FVM loop, and its ROCm support was unverified rather than
confirmed at parity with the other two -- not a maintenance or
Python-support concern, both checked fine).

**Renderer**, narrowed to wgpu/pygfx vs. VisPy on live-checked headless
support (the hard requirement from `docs/implementation/golden-demos.md`
via D5). VTK/PyVista and ModernGL/pyglet/glfw were not re-verified live
and were not preferred over the two that were.

---

# Decision

**Array library: PyTorch.**

**Renderer: wgpu/pygfx** (the `pygfx` package, built on `wgpu-py`).

Coupled via a host round-trip, per `ADR-004`. PyTorch's DLPack support
and wgpu's compute-shader access on the same device as rendering are a
documented, but unconfirmed, path to a future zero-copy optimisation --
not relied upon now, and not required by this decision.

---

# Consequences

## Positive

- **Broadest verified hardware reach of any array-library candidate.**
  Official first-class ROCm (2.7+) and Apple MPS, both confirmed live --
  matches or exceeds CuPy, and clearly exceeds JAX's unverified ROCm
  story.
- **The best-resourced, most durable project of the three array
  candidates** (Meta-backed) -- lowest maintenance risk of the options
  considered.
- **Latent optionality toward differentiable simulation** (gradient-based
  inverse design, ML-based closures) -- a live direction in CFD research
  and exactly the kind of thing `docs/planning/dreams.md` exists to hold
  speculatively, available without an architecture change if ever wanted.
- **The strongest confirmed headless/CI story of any renderer surveyed.**
  wgpu/pygfx's own CI runs on LavaPipe (software rendering) as standard
  practice, not merely documented as possible -- directly and confidently
  satisfies D5's hard requirement.
- **Offscreen rendering needs no canvas, GUI toolkit, or event loop** --
  `wgpu`'s offscreen canvas returns frames as a NumPy array directly,
  which composes cleanly with a golden-demo regression test.
- Both PyTorch and wgpu/pygfx are independently, currently
  well-maintained (verified live, 2026-08-15).

## Negative

- **Does not most closely embody the NumPy-shape argument that won Class
  2 the A2b decision in the first place.** `torch.Tensor`'s API is
  NumPy-*like*, not identical (different names, some indexing
  differences) -- real, if modest, translation cost writing and reading
  the operator layer, and a step away from `ADR-003`'s
  replaceable-interface ideal compared with what CuPy would have offered.
- **Heaviest install of the three array-library candidates** (hundreds of
  MB with CUDA wheels) -- a real, if modest, tax on Stage 0's
  reproducibility criterion, `make install` time, and CI cache size.
- **wgpu/pygfx is pre-1.0** (targeting 1.0 around July 2026) -- younger
  and less battle-tested than VTK, though its headless story and
  maintenance cadence are both strong on their own terms.
- **No turnkey scientific-visualisation chrome.** Colour maps, vector
  glyphs and legends -- which VTK/PyVista would have provided largely for
  free -- become PyFlow's own implementation work, directly affecting
  TASK-013 (Mesh Visualiser) and TASK-017 (Field Rendering).
- **True zero-copy GPU coupling between PyTorch and wgpu/pygfx remains
  unconfirmed**, same finding as `ADR-004` -- accepted risk, not resolved
  by choosing these specific instances either.

---

# Alternatives Considered

## CuPy (array library)

Rejected, closely. The more literal expression of Class 2's own
NumPy-shape rationale, and the lighter dependency of the two. Rejected
in favour of PyTorch's broader verified hardware reach, larger and
better-resourced ecosystem, and latent differentiable-simulation
optionality -- judged to outweigh CuPy's closer architectural fit for a
project still deciding its long-term direction.

## JAX (array library)

Rejected. Immutable-array semantics are real, ongoing friction against a
mutable per-timestep loop, in tension with P-008/P-009 (maintainability
and clarity over cleverness). ROCm support exists via a separate plugin
but was not verified at parity with CuPy/PyTorch.

## VTK / PyVista (renderer)

Not rejected on verified grounds -- not re-checked live with the same
rigour as wgpu/pygfx and VisPy. Not preferred, given wgpu/pygfx's
directly confirmed, strong headless story against D5's hard requirement,
and VTK's own axis-2 characterisation as oriented more toward a viewer
than a tight real-time loop. Revisit if wgpu/pygfx's instance choice
needs to change later -- VTK's turnkey scientific-visualisation chrome
(colour maps, glyphs) remains a real advantage this decision gives up.

## VisPy (renderer)

Rejected. Headless support is real, with genuine engineering investment
in an EGL backend, but a headless-rendering-without-sudo issue has sat
open and unaddressed on VisPy's own issue tracker since 2023, and other
EGL-related issues recur through its history. Maintenance cadence is
also the least regular of the renderer candidates checked live.

## ModernGL / pyglet / glfw (renderer)

Not rejected on verified grounds -- not re-checked live. Not preferred,
for the same reason as VTK: no verified advantage over wgpu/pygfx's
confirmed headless story, and every scientific-visualisation convenience
(colour maps, glyphs, legends, zoom, pan) would be entirely PyFlow's own
implementation work under this option, more than under any other
candidate surveyed.

---

# Notes

This decision is at the *instance* level. Per `ADR-004`, both should sit
behind the interface boundary already established for the array library
(so a future swap, e.g. to CuPy, is an implementation change rather than
an architectural one) and, per `ADR-003`, the renderer should sit behind
a stable interface selected at construction, so a second renderer or a
different instance remains a configuration-level change.

Colour maps, vector glyphs and legends are not provided by wgpu/pygfx the
way they would have been by VTK/PyVista -- TASK-013 and TASK-017 should
budget for this as real implementation work, not assume it is free.

Re-evaluate the DLPack-based zero-copy path between PyTorch and
wgpu/pygfx if profiling ever shows the host round-trip has become a real
bottleneck -- per `ADR-004`, most likely at Stage 10's 3D scale, not
before.
