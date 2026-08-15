# ADR-004: Compute-and-Rendering Stack — Class Decision

**Status:** Accepted

---

# Context

PyFlow needs two closely related decisions: what holds field data and
executes the numerical operators (the array/numerics library), and what
visualises it (the rendering library). `docs/planning/backlog.md` A2
found these are not independent -- the array library determines what a
renderer can read without a copy, and the renderer determines what
layout and device the array library needs to produce -- so they are
decided together, as a **class** of solution first (this ADR), with the
specific array-library and renderer *instances* chosen afterward (A2c, a
separate, cheaper decision).

`docs/architecture/compute-and-rendering-stack.md` surveys the field and
groups viable combinations into four architecturally distinct classes:

1. **CPU arrays (NumPy), general-purpose renderer.** Fully decoupled and
   reversible, but no path to GPU execution (Capability Level 9) without
   a later migration.
2. **GPU arrays, NumPy-shaped (CuPy/PyTorch/JAX), general-purpose
   renderer.** Coupled via a host round-trip by default; true zero-copy
   GPU-to-renderer sharing is possible but unproven for any candidate.
3. **Taichi for both compute and render.** The only class with a
   first-class, zero-copy, native real-time renderer -- but Taichi's
   latest release is over a year old as of the 2026-08-15 verification,
   with widening gaps beforehand, and its Python ceiling (3.13) conflicts
   with the Python version already chosen (3.14, decided 2026-08-15).
4. **NVIDIA Warp for compute, general-purpose or bridged renderer.**
   Materially better maintained than Taichi and validated at production
   scale via NVIDIA's own Newton physics engine, but carries the same
   kernel-DSL cost against `ADR-003`'s replaceable-interface principle as
   Taichi, without Taichi's native-rendering payoff -- Warp's own
   renderer is documented by NVIDIA as debug-grade, not production. Also
   CUDA-only.

Full findings, including live-verified maintenance data, hardware
portability checks, a quantified cost estimate for the host round-trip,
and domain-specific validation, are in
`docs/architecture/compute-and-rendering-stack.md`. This ADR records the
decision and its rationale; it does not repeat that evidence in full.

---

# Decision

PyFlow adopts **Class 2**: a GPU-capable, NumPy-shaped array library
(one of CuPy, PyTorch or JAX -- the specific instance is A2c, not decided
here) paired with a general-purpose rendering library, coupled via a
host round-trip as the default, with true zero-copy GPU-renderer
interop left as a future optimisation rather than a day-one requirement.

This explicitly rejects Class 3 (Taichi) and Class 4 (Warp) as the
primary compute-and-rendering architecture, for the reasons in
Alternatives Considered below.

---

# Consequences

## Positive

- **Best verified hardware portability of any class surveyed.** CuPy and
  PyTorch both have official, mature multi-vendor GPU support (ROCm;
  PyTorch adds Apple MPS) -- confirmed live, not assumed. Neither Taichi
  (multi-vendor in principle, but stale) nor Warp (CUDA-only) matches
  this.
- **All three candidate instances are independently, currently
  well-maintained** (verified live 2026-08-15) -- none carries Taichi's
  maintenance risk.
- **No Python version conflict.** PyFlow stays at Python 3.14 as already
  chosen (2026-08-15); Class 3 would have forced reopening that decision
  down to 3.13.
- **NumPy-shaped operator code is the closest fit to `ADR-003`'s
  replaceable-interface principle** of any GPU-capable class -- an
  operator implementation is far closer to a drop-in strategy object than
  a Taichi or Warp kernel is, and the same code can plausibly run on
  plain NumPy (no GPU required) for local development and CI, which
  directly supports D5's headless testing requirement.
- **Keeps the renderer decision decoupled and multi-renderer cheap.** Any
  renderer reads NumPy natively; GPU-array-specific coupling is an
  optimisation applied later, not a precondition for the architecture to
  work at all.
- **The host round-trip's cost is quantified and found acceptable at
  this project's actual near/medium-term scale**
  (`docs/architecture/compute-and-rendering-stack.md` §4.1):
  sub-millisecond to low-single-digit milliseconds against a 60fps
  budget for the MVP's 2D structured grid, using measured PCIe
  bandwidths rather than assumption.
- **The swappable-backend pattern is independently validated for fluid
  simulation specifically** by JAX-Fluids and PhiFlow, even though
  PyFlow depends on neither package directly.

## Negative

- **Does not deliver a first-class, zero-copy, native real-time render
  loop.** True zero-copy GPU-array-to-renderer coupling (DLPack into
  wgpu, CUDA-GL interop) remains unproven for every candidate in this
  class and is accepted as a known, deferred risk, not resolved by this
  decision. If profiling ever shows the round-trip has become a real
  bottleneck (most likely at Stage 10's 3D scale, where cost scales as
  N³ rather than N²), that interop engineering will need to be done
  then.
- **No production-scale validation as strong as Warp's Newton/Isaac Lab
  pedigree exists for any Class 2 instance** doing real-time-rendered
  fluid simulation specifically. JAX-Fluids and PhiFlow are research-grade
  evidence for the compute pattern; neither solves or even attempts the
  native-rendering question this project cares about.
- **No kernel-level per-thread control** the way Taichi/Warp offer --
  most valuable for irregular, sparse or conditional workloads (adaptive
  mesh refinement, immersed boundaries, unstructured meshes), which are
  later capability levels, not the MVP's uniform structured grid. If that
  control is needed later, it will have to be added within this class
  (e.g. Numba-JIT'd hot loops) rather than inherited for free.

---

# Alternatives Considered

## Class 1 — CPU arrays only (NumPy)

Not rejected outright -- remains available as a fallback/dev mode within
Class 2's own array-library choice -- but not adopted as the primary
class, since it forecloses Capability Level 9's GPU-execution ambitions
entirely rather than deferring the cost of pursuing them.

## Class 3 — Taichi for both compute and render

Rejected. Taichi's native, zero-copy render property was the strongest
architectural case of any class surveyed -- the only one with a
verified, first-class real-time renderer. Rejected anyway because its
upstream maintenance shows clear signs of having stalled (latest release
2025-07-31, over a year before this decision, with widening gaps in the
releases before that) and its Python ceiling (3.13) directly conflicts
with the Python version already chosen. Reopening the Python decision to
accommodate an upstream project that may be abandoned was judged not
worth the architectural payoff.

## Class 4 — NVIDIA Warp for compute, bridged renderer

Rejected, more closely than Class 3. Warp is the best-maintained
GPU-capable candidate surveyed and the only one with real production
validation (NVIDIA's own Newton physics engine, including MPM fluid
simulation). Rejected because it carries Class 3's kernel-DSL cost
against `ADR-003` without Class 3's native-rendering payoff -- Warp's own
renderer is documented by NVIDIA as intended for debugging, not
production visualisation -- and because it is CUDA-only, narrower
hardware scope than Class 2's verified multi-vendor support. Once the
host round-trip's cost was quantified and found acceptable
(`docs/architecture/compute-and-rendering-stack.md` §4.1), Class 4's
main remaining advantage over Class 2 -- avoiding that round trip --
stopped being decisive.

---

# Notes

This decision fixes the **class**, not the instance. A2c
(`docs/planning/backlog.md`) still needs to choose the specific array
library (CuPy, PyTorch or JAX) and the specific renderer, and should
weigh the differences recorded in
`docs/architecture/compute-and-rendering-stack.md` §2 -- CuPy is closest
to a transparent NumPy/CPU swap, PyTorch has the broadest hardware reach
and ecosystem, JAX's immutable-array model is a real (not fatal) friction
against a mutable timestep loop.

Per `ADR-003`, the array-library instance should sit behind a stable
interface so a future swap (e.g. if the Array API standard matures
further, or if a specific instance's GPU story regresses) is an
implementation change, not an architectural one.

Re-profile the host round-trip's cost before Stage 10 (3D) rather than
assuming §4.1's 2D-scale estimate still holds -- that is the point at
which this decision's accepted risk was identified as most likely to
need revisiting.
