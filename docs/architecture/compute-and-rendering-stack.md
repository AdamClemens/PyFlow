# Compute-and-Rendering Stack

Survey and compatibility matrix for A2a
(`docs/planning/backlog.md`), informing the class decision (A2b) and
instance decision (A2c). Not itself an ADR -- this is decision support.

**Knowledge snapshot: to approximately May 2026**, accepted as the basis
for this survey per the maintainer's instruction of 2026-08-15 (see
`docs/CHANGELOG-DESIGN.md`). Specific version numbers, release maturity
and exact interop status should be treated as **a starting point for
discussion, not verified fact** -- confidence is flagged per claim below,
and anything marked uncertain should be checked directly before A2b/A2c
finalise on it. **Status: DRAFT, first pass, written for discussion --
not yet reviewed against the maintainer's priorities.**

**Verified update, 2026-08-15 (live check, not snapshot memory):** the
Taichi entries below were checked directly against PyPI and the GitHub
API after Taichi emerged as the front-runner in discussion. Two findings
changed a ❔ to a settled answer and raised a risk this survey's first
pass had not surfaced. See §2 and §7.1/§7.5.

---

## 1. Why this is one document, not two

The array library determines what a renderer can read without a copy;
the renderer determines what memory layout and device the array library
needs to produce. Chosen independently, each choice is made against
assumptions about the other that may not hold. See
`docs/planning/backlog.md` A2a-c for the full reasoning.

---

## 2. Axis 1 — array / numerics libraries

What holds field data (mesh cell values: velocity, pressure, scalar
fields) and executes the numerical operators (advection, diffusion,
gradient, divergence) against it.

| Library | Device | API shape | Notes |
|---|---|---|---|
| **NumPy** | CPU only | the baseline everyone else imitates | No GPU story of its own. Universal interop. |
| **CuPy** | GPU (CUDA) | near-drop-in NumPy replacement | Closest thing to "NumPy but on the GPU." Supports the DLPack protocol and `__cuda_array_interface__` for zero-copy exchange with other CUDA-aware libraries. |
| **PyTorch** (`torch.Tensor`) | CPU/GPU (CUDA, ROCm, and Apple MPS) | NumPy-*like*, not identical (different function names/semantics in places) | Primarily a deep-learning library repurposed here as a GPU array library. Very mature GPU support, very heavy dependency (hundreds of MB with CUDA wheels). DLPack support. Autograd is unneeded baggage for this project, not a cost beyond install size. |
| **JAX** | CPU/GPU/TPU | NumPy-*like* (`jax.numpy`), functional/immutable | Arrays are immutable -- in-place field mutation, the natural pattern for a timestep loop, needs a functional-update style (`.at[idx].set(...)`) or a wrapper library (e.g. Equinox). Real friction against a straightforward CFD loop, not fatal, but a genuine architectural cost. JIT-compiled via XLA; strong autodiff if ever wanted for optimisation/inverse problems. |
| **Numba** | CPU JIT; CUDA JIT target | not an array library itself -- compiles Python/NumPy-shaped code | Sits *on top of* NumPy arrays rather than replacing them. Good option for compiling hot operator loops while staying in NumPy semantics on CPU. The CUDA target requires writing more explicit kernel-style code, closer to Warp/Taichi than to CuPy's transparency. |
| **Taichi** | CPU/CUDA/Vulkan/Metal, portable | Python-embedded DSL, not NumPy-shaped -- has its own `ti.field` concept | **Purpose-built for exactly this domain** -- grid/particle physics simulation is Taichi's primary use case, not an adaptation. Ships **GGUI**, a real-time GPU renderer (Vulkan-backed) that reads Taichi fields directly with no host round-trip, because compute and rendering are the same runtime. This collapses the "how do the two axes couple" question for one candidate class entirely -- see §4. **Verified 2026-08-15 (live, not snapshot):** latest release **1.7.4**, published **2025-07-31** -- over a year old as of this writing, and release gaps have been widening (Aug'24→Dec'24 ~4mo, Dec'24→Jul'25 ~7mo, then 13+ months and counting). Wheels exist for **cp39-cp313 only -- no Python 3.14 wheel**; `taichi-nightly` on PyPI is an unrelated, long-dead legacy package (0.5.11, Python 3.6-era) and not an escape hatch. GGUI's headless mode is real and documented: `ti.ui.Window(..., show_window=False)`, then `window.save_image()` instead of `window.show()` -- resolves the ❔ in §5. |
| **NVIDIA Warp** | CPU/CUDA | Python-embedded kernel DSL, aimed at simulation/graphics | Explicitly pitched at physics simulation and differentiable simulation. Newer and narrower ecosystem than Taichi at this snapshot -- **confidence: low-medium** on current maturity/community size, worth checking directly. NVIDIA-centric (CUDA-first); portability to non-NVIDIA GPUs is a real question, unlike Taichi's stated multi-backend design. |
| **PyOpenCL** | GPU (vendor-neutral, via OpenCL) | low-level, array-ish but not NumPy-shaped | Vendor-neutral is the main draw over CUDA-locked options. Considerably lower-level/more manual than the above; ergonomics cost is real. |
| **Dask Array** | CPU, distributed/out-of-core | NumPy-shaped, chunked | Solves a different problem -- larger-than-memory and distributed scale -- rather than GPU/rendering coupling. More relevant to Capability Level 9 (distributed execution) than to Stage 0-5's single-machine MVP. Listed for completeness, not a serious Stage 0 candidate. |

**Cross-cutting note -- the Python Array API standard.** NumPy, CuPy,
PyTorch and JAX all have some degree of conformance to a shared array API
standard. Writing the operator layer against that standard, rather than
against one library's specific API, is a way to reduce how tightly A2c's
*instance* choice locks in -- worth weighing against A2b's "which classes
keep swapping cheap" axis. Confidence: **medium** on exact current
conformance levels per library; verify at decision time.

---

## 3. Axis 2 — rendering libraries

Carried over from the earlier single-axis pass, unchanged in substance.

| Library | What it gives for free | Cost |
|---|---|---|
| **VTK / PyVista** | Colour maps, vector glyphs, legends, mesh handling -- the OpenFOAM/ParaView lineage, built for exactly this kind of data. 3D from day one. | Heavy dependency; its natural model is a viewer more than a tight real-time loop. |
| **VisPy** | GPU-accelerated (OpenGL), scene-graph, built for large fast-updating datasets. | Less turnkey than VTK for scientific-specific chrome (colour maps, glyphs) -- more assembly required. |
| **wgpu-py / pygfx** | Modern GPU API (WebGPU), compute shaders available on the same device as rendering. | Newer, less battle-tested at this snapshot -- **confidence: low-medium** on current maturity; worth checking. Compute-shader access is the interesting property for GPU-array coupling. |
| **ModernGL / pyglet / glfw+PyOpenGL** | Maximum control, smallest dependency footprint. | Colour maps, glyphs, legends, zoom, pan: all ours to write. |
| **PySide6/Qt + OpenGL widget** | Full GUI toolkit, if interactive parameter editing becomes a real goal (see `dreams.md`). | Brings a whole widget toolkit for a capability not yet committed to. |
| **Taichi GGUI** | Reads Taichi fields directly, GPU-resident, no host round-trip. | Only usable if Taichi is also the axis-1 choice -- not a general-purpose renderer for other array types. |
| **matplotlib** | Universal, well understood. | Too slow for a real-time timestep loop. Likely wanted *alongside* whichever renderer wins, for validation plots and golden-demo regression images -- not a competitor for the primary role. |

---

## 4. The coupling matrix

For each axis-1 × axis-2 pairing that is not obviously nonsensical, what
actually couples them. Legend: ✅ direct/native, 🟡 possible via an
interop layer (extra work, extra failure surface), ❌ effectively no
practical path, ❔ genuinely uncertain at this snapshot -- verify.

| Array \ Renderer | VTK/PyVista | VisPy | wgpu/pygfx | ModernGL/thin | Taichi GGUI |
|---|---|---|---|---|---|
| **NumPy** | ✅ native input format | ✅ native | ✅ native (host upload each frame) | ✅ native | ❌ wrong ecosystem |
| **CuPy** | 🟡 via `.get()` host round-trip, or VTK's CUDA interop (niche, **❔**) | 🟡 host round-trip typical; direct GPU path **❔** | 🟡 DLPack → wgpu buffer interop exists but is non-trivial to wire up, **❔ confidence low** | 🟡 CUDA-GL interop is a known but fiddly pattern | ❌ |
| **PyTorch** | 🟡 host round-trip (`.cpu().numpy()`) is the reliable path | 🟡 same | 🟡 same DLPack caveat as CuPy | 🟡 CUDA-GL interop, same caveat | ❌ |
| **JAX** | 🟡 via `.device_get()`/host round-trip | 🟡 same | 🟡 **❔ lowest confidence of the GPU options** -- JAX's device buffer interop is the least well-trodden path here | 🟡 possible in principle, uncertain in practice | ❌ |
| **Taichi fields** | 🟡 export to NumPy first, loses the point | 🟡 same | 🟡 same | 🟡 same | ✅ **native, zero-copy, same runtime** |

**Reading this table honestly:** every GPU-array-library × general-purpose-renderer
cell is 🟡 or ❔. None of them is a solved, well-worn path at this
snapshot -- they range from "known pattern, some plumbing" to "uncertain,
needs a spike before committing." The only ✅ cells off the NumPy row
belong to Taichi paired with its own renderer. That is the single most
important finding of this survey and should weigh heavily on A2b.

---

## 5. Other assessment axes (from A2a's brief)

| Axis | Notes |
|---|---|
| **Python 3.14 support** | Confidence varies per library at this snapshot and needs a direct check before A2c, not assumed from this document -- new-release lag is exactly the pattern the version-review policy in `docs/practices.md` exists to catch. |
| **Licence vs. BSD-3-Clause** | All candidates above are permissively licensed at this snapshot to the best of this survey's knowledge (BSD/MIT/Apache-2.0-family) -- **confidence: medium**, worth a direct check per final candidate rather than trusted wholesale. |
| **Headless / CI capable** | Hard requirement, from `docs/implementation/golden-demos.md` via D5. NumPy/CuPy/PyTorch/JAX/Taichi's *compute* side is unaffected (no display needed). On the *rendering* side: VTK has established offscreen/headless rendering support; ModernGL/glfw-family can run headless via offscreen contexts (EGL/OSMesa) with known extra setup; VisPy and wgpu/pygfx headless paths are **still ❔, not checked**; **Taichi GGUI's headless support is confirmed (verified 2026-08-15, live check)** -- `show_window=False` plus `window.save_image()` is documented, official behaviour, not inferred. This removes what would have been the most likely disqualifier for Class 3. |
| **2D now, 3D at Stage 10 without a rewrite** | VTK/PyVista strongest here (3D-native). VisPy, wgpu/pygfx and Taichi GGUI all support 3D. Thin layers (ModernGL) support it but every capability (camera, projection) is ours to build. |
| **Capability Level 9 (GPU execution)** | Only the GPU-capable axis-1 candidates are relevant at all; among those, Taichi's story is the most coherent *because* compute and render already share a device and runtime. The others would need the interop work in §4 regardless of whether Level 9 is pursued, if a GPU array library is chosen now for compute alone. |
| **Multiple renderers (maintainer's stated ambition)** | The NumPy row is renderer-agnostic almost by definition -- any renderer can consume it, which is what keeps a second renderer cheap. Every 🟡/❔ cell above represents *renderer-specific* plumbing that would need re-doing per additional renderer if a GPU array library couples tightly to one. Taichi GGUI is the extreme case: choosing it as the primary renderer effectively forecloses easily adding a second, different renderer for the *same* field data, because the coupling **is** the point of that class. |

---

## 6. Candidate classes

Grouping the matrix into architecturally distinct options, per A2b's
instruction to compare classes rather than individual products.

### Class 1 — CPU arrays, general-purpose renderer
**NumPy** (optionally Numba-JIT'd hot loops) + any renderer from §3.
- *Forecloses:* nothing about renderer choice; keeps multi-renderer
  cheap (every renderer reads NumPy natively).
- *Costs:* no path to Capability Level 9 GPU execution without a later,
  separate migration of the compute layer.
- *Reversibility:* highest of all classes -- the renderer decision and
  the compute decision are fully decoupled.

### Class 2 — GPU arrays (NumPy-shaped), general-purpose renderer
**CuPy or PyTorch or JAX** + VTK/VisPy/wgpu/ModernGL, accepting a host
round-trip (or spiking the DLPack/CUDA-GL interop path from §4).
- *Forecloses:* nothing about renderer choice per se, but the coupling
  work in §4 is renderer-specific, so a second renderer means redoing it.
- *Costs:* the interop uncertainty in §4 is real engineering risk, not
  yet spiked. A host-round-trip fallback works but defeats much of the
  point of a GPU array library for a per-frame-updating render.
- *Reversibility:* medium -- swapping the array library instance (CuPy
  ↔ PyTorch ↔ JAX) is plausible if the operator layer is written against
  the Array API standard (§2); swapping the renderer instance is not
  cheap once the interop plumbing is built for one.

### Class 3 — Taichi for both compute and render
**Taichi fields** + **Taichi GGUI**.
- *Forecloses:* the multi-renderer ambition for this data path, and
  locks the numerical-operator implementation into Taichi's DSL rather
  than NumPy-shaped code (a real cost against `ADR-003`'s "uniform,
  replaceable interface" principle -- Taichi kernels are not drop-in
  replaceable with a NumPy implementation the way CuPy is). **Also
  forecloses Python 3.14 as chosen 2026-08-15** -- confirmed no wheel
  exists past cp313 (verified live, not snapshot). Choosing this class
  means either reopening the Python version decision down to 3.13, or
  ruling Taichi out on that basis alone.
- *Enables:* the only ✅-throughout path to GPU execution with rendering
  that is genuinely native rather than bridged, and the least
  engineering risk of the GPU-capable classes, precisely because there
  is no interop layer to build or debug. Headless rendering is confirmed
  working, not merely hoped for.
- *New risk, found verifying this class rather than assumed at the
  survey's first pass:* release cadence has been slowing and the latest
  release is over a year old as of 2026-08-15, with widening gaps between
  releases beforehand. Worth weighing against the "least engineering
  risk" point above -- low interop risk today is not the same as low risk
  over the life of a multi-year project if upstream maintenance is
  slowing. Not necessarily disqualifying; a single point-in-time repo
  check cannot distinguish "quiet because stable" from "quiet because
  stalled" -- but it is a real data point that the first survey pass did
  not have.
- *Reversibility:* lowest of the three classes -- this is a full-stack
  commitment, not a swappable instance.

---

## 7. Open questions for discussion

Marked ❔ above and collected here as the concrete things this survey
could not settle from a knowledge snapshot alone:

1. ~~Current headless/offscreen rendering support for VisPy, wgpu/pygfx,
   and Taichi GGUI specifically~~ -- **Taichi GGUI resolved 2026-08-15,
   confirmed working** (`show_window=False` + `save_image()`, documented
   official behaviour). VisPy and wgpu/pygfx remain open -- only checked
   for the class that reached active discussion first.
2. Actual maturity of DLPack-based CuPy/PyTorch/JAX → wgpu buffer
   sharing as of now, versus this survey's May-2026 snapshot.
3. NVIDIA Warp's current ecosystem maturity relative to Taichi --
   flagged low-medium confidence throughout, and it was not built into
   the matrix or class list above because of that uncertainty. Worth a
   look before treating Taichi as the only serious native-GPU-simulation
   candidate.
4. Whether the Array API standard's conformance across NumPy/CuPy/
   PyTorch/JAX is mature enough to actually write the operator layer
   against it, or whether that is aspirational at this snapshot.
5. **New, found 2026-08-15 verifying Taichi rather than anticipated in
   the first pass: Taichi's Python ceiling is 3.13, and the project's
   release cadence has been slowing for over a year.** Neither is
   disqualifying by itself. Together they are the actual decision in
   front of A2b if Class 3 is the direction: accept 3.13 as the chosen
   Python version (reopening the 2026-08-15 3.14 decision under its own
   policy -- a real dependency constraint is exactly what the periodic
   review exists to weigh), or let this rule Taichi out. This survey does
   not resolve it -- that is a maintainer decision, and it is the reason
   this document's Taichi findings are marked "verified" rather than
   folded silently into the class recommendation.

---

## 8. Not yet decided here

This document surveys and compares; it does not choose. A2b (class) and
A2c (instance) are separate backlog items with their own ADRs. The
biggest single lever in this survey is §4's finding that almost every
GPU pairing outside Class 3 is unproven at this snapshot -- that is the
fact most worth weighing before anything else.
