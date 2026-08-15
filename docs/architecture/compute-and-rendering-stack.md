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
| **CuPy** | GPU (**CUDA and ROCm** -- verified 2026-08-15: mature official ROCm wheels, e.g. `cupy-rocm-7-0`, not experimental) | near-drop-in NumPy replacement | Closest thing to "NumPy but on the GPU," and the strongest CPU/GPU code-path flexibility surveyed -- the same array code frequently runs unmodified against NumPy (CPU) or CuPy (GPU). Supports DLPack and `__cuda_array_interface__` for zero-copy exchange with other CUDA-aware libraries. **Maintenance verified live 2026-08-15:** latest v14.1.1 (2026-06-01), regular releases through the prior year -- healthy, no Taichi-style stall. |
| **PyTorch** (`torch.Tensor`) | CPU/GPU (**CUDA, and official first-class ROCm** as of PyTorch 2.7 -- verified 2026-08-15, not a preview; plus Apple MPS, auto-detected but still experimental in coverage) | NumPy-*like*, not identical (different function names/semantics in places) | Primarily a deep-learning library repurposed here as a GPU array library. Very mature GPU support, widest hardware reach of any candidate surveyed, very heavy dependency (hundreds of MB with CUDA wheels). DLPack support. Autograd is unneeded baggage for this project, not a cost beyond install size. **Maintenance verified live 2026-08-15:** latest v2.13.0 (2026-07-08), releases roughly every 4-6 weeks -- one of the best-resourced OSS projects surveyed (Meta-backed). |
| **JAX** | CPU/GPU/TPU (**ROCm support exists via a separate plugin; not verified this session -- do not assume parity with CuPy/PyTorch's ROCm story without checking**) | NumPy-*like* (`jax.numpy`), functional/immutable | Arrays are immutable -- in-place field mutation, the natural pattern for a timestep loop, needs a functional-update style (`.at[idx].set(...)`) or a wrapper library (e.g. Equinox). Real friction against a straightforward CFD loop, not fatal, but a genuine architectural cost. JIT-compiled via XLA; strong autodiff if ever wanted for optimisation/inverse problems. **Maintenance verified live 2026-08-15:** latest v0.11.0 (2026-07-16), releases almost exactly monthly for the prior five months -- the most regular cadence of any array library surveyed. |
| **Numba** | CPU JIT; CUDA JIT target | not an array library itself -- compiles Python/NumPy-shaped code | Sits *on top of* NumPy arrays rather than replacing them. Good option for compiling hot operator loops while staying in NumPy semantics on CPU. The CUDA target requires writing more explicit kernel-style code, closer to Warp/Taichi than to CuPy's transparency. |
| **Taichi** | CPU/CUDA/Vulkan/Metal, portable | Python-embedded DSL, not NumPy-shaped -- has its own `ti.field` concept | **Purpose-built for exactly this domain** -- grid/particle physics simulation is Taichi's primary use case, not an adaptation. Ships **GGUI**, a real-time GPU renderer (Vulkan-backed) that reads Taichi fields directly with no host round-trip, because compute and rendering are the same runtime. This collapses the "how do the two axes couple" question for one candidate class entirely -- see §4. **Verified 2026-08-15 (live, not snapshot):** latest release **1.7.4**, published **2025-07-31** -- over a year old as of this writing, and release gaps have been widening (Aug'24→Dec'24 ~4mo, Dec'24→Jul'25 ~7mo, then 13+ months and counting). Wheels exist for **cp39-cp313 only -- no Python 3.14 wheel**; `taichi-nightly` on PyPI is an unrelated, long-dead legacy package (0.5.11, Python 3.6-era) and not an escape hatch. GGUI's headless mode is real and documented: `ti.ui.Window(..., show_window=False)`, then `window.save_image()` instead of `window.show()` -- resolves the ❔ in §5. |
| **NVIDIA Warp** | CPU (x86-64/ARMv8/Apple Silicon) + CUDA GPU only, no ROCm/Metal | Python-embedded kernel DSL, aimed at simulation/robotics/ML | Explicitly pitched at physics simulation; CFD is a documented use case (2D incompressible turbulence, Navier-Stokes examples), not merely adjacent. **Verified 2026-08-15 (live, not snapshot):** latest release **1.16.0, published 2026-08-03** -- 12 days before this check, with roughly monthly releases for months prior (Apr→May→Jun→Jul→Aug 2026). The opposite maintenance profile from Taichi. **Apache-2.0** licensed. Wheels confirmed for **cp310 through cp314** -- supports the Python version already chosen, no version tension. **But the rendering story is not a Taichi equivalent:** ships `warp.render.OpenGLRenderer` (built on **pyglet**, an axis-2 thin-layer candidate) with confirmed headless support via EGL on Linux -- but NVIDIA's own docs describe it as intended for *debugging and interactive playback*, not production visualization. The path the docs actually recommend is `UsdRenderer`, an **offline USD export** for playback in Omniverse/Blender/usdview -- not an in-process real-time loop. Whether `OpenGLRenderer` can consume Warp GPU arrays without a host round-trip is **undocumented, genuinely unconfirmed** rather than merely unlikely. Net: excellent, current, well-maintained compute; a debug-grade renderer, not a first-class one -- closer to a Class 2 candidate than a Class 3 rival to Taichi. |
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
| **Warp `OpenGLRenderer`** | Ships with Warp; confirmed headless via EGL on Linux (`pyglet.options["headless"]`). Built on pyglet -- so architecturally this *is* the ModernGL/pyglet/glfw row above, wrapped by Warp. | **Verified 2026-08-15:** NVIDIA's own docs position it for *debugging and interactive playback*, not production visualization -- the documented "real" path is `UsdRenderer`, an offline USD export for external tools (Omniverse/Blender/usdview), not an in-process real-time loop. Whether it takes Warp arrays without a host round-trip is undocumented -- **❔, unconfirmed**, not merely unlikely. Only usable if Warp is the axis-1 choice. |
| **matplotlib** | Universal, well understood. | Too slow for a real-time timestep loop. Likely wanted *alongside* whichever renderer wins, for validation plots and golden-demo regression images -- not a competitor for the primary role. |

---

## 4. The coupling matrix

For each axis-1 × axis-2 pairing that is not obviously nonsensical, what
actually couples them. Legend: ✅ direct/native, 🟡 possible via an
interop layer (extra work, extra failure surface), ❌ effectively no
practical path, ❔ genuinely uncertain at this snapshot -- verify.

| Array \ Renderer | VTK/PyVista | VisPy | wgpu/pygfx | ModernGL/thin | Taichi GGUI | Warp `OpenGLRenderer` |
|---|---|---|---|---|---|---|
| **NumPy** | ✅ native input format | ✅ native | ✅ native (host upload each frame) | ✅ native | ❌ wrong ecosystem | 🟡 plausible (most such tools accept plain arrays) but **not verified** for this specific class |
| **CuPy** | 🟡 via `.get()` host round-trip, or VTK's CUDA interop (niche, **❔**) | 🟡 host round-trip typical; direct GPU path **❔** | 🟡 DLPack → wgpu buffer interop exists but is non-trivial to wire up, **❔ confidence low** | 🟡 CUDA-GL interop is a known but fiddly pattern | ❌ | ❌ wrong ecosystem |
| **PyTorch** | 🟡 host round-trip (`.cpu().numpy()`) is the reliable path | 🟡 same | 🟡 same DLPack caveat as CuPy | 🟡 CUDA-GL interop, same caveat | ❌ | ❌ |
| **JAX** | 🟡 via `.device_get()`/host round-trip | 🟡 same | 🟡 **❔ lowest confidence of the GPU options** -- JAX's device buffer interop is the least well-trodden path here | 🟡 possible in principle, uncertain in practice | ❌ | ❌ |
| **Taichi fields** | 🟡 export to NumPy first, loses the point | 🟡 same | 🟡 same | 🟡 same | ✅ **native, zero-copy, same runtime** | ❌ |
| **Warp arrays** | 🟡 host round-trip, same shape as CuPy's row | 🟡 same | 🟡 same, **❔** | 🟡 CUDA-GL interop, same caveat as CuPy | ❌ | **❔ genuinely unconfirmed** -- see the Axis 2 row above; this is Warp's own tool and still undocumented on the zero-copy question |

**Reading this table honestly:** every GPU-array-library × general-purpose-renderer
cell is 🟡 or ❔. None of them is a solved, well-worn path at this
snapshot -- they range from "known pattern, some plumbing" to "uncertain,
needs a spike before committing." The only ✅ cells off the NumPy row
belong to Taichi paired with its own renderer -- and Taichi's own
maintenance findings (§2) weigh heavily against leaning on that as of
2026-08-15. **With Taichi's advantage discounted, every remaining
GPU-capable candidate is in the same 🟡/❔ position on rendering**, which
makes the fallback's actual cost -- estimated next -- the load-bearing
question for the whole survey rather than a footnote.

### 4.1 How expensive is the 🟡 fallback, actually?

Every 🟡 cell above falls back to a **host round-trip**: copy the GPU
array to CPU memory, hand it to the renderer as NumPy. This was treated
in the first survey pass as a real but unquantified cost. It is
quantifiable, at least approximately, and the answer changes how alarming
the 🟡/❔ rows above should read.

**Back-of-envelope, not a verified benchmark of PyFlow code -- a real
profile is still warranted once code exists (flagged in §7).** Measured
PCIe copy bandwidths found this session: ~12.5 GB/s (PCIe Gen3 x16,
conservative/older hardware) up to ~32 GB/s (Gen4 x16), and transfers can
overlap with compute using pinned-memory staging buffers rather than
blocking the frame.

For the MVP's actual scope (`docs/implementation/mvp.md`: 2D, structured,
uniform grid) at a generous 2048×2048 cells with four `float32` fields
(u, v, pressure, one scalar) -- **~67 MB/frame**:

| PCIe generation | Transfer time | Against a 16.7 ms (60 fps) budget |
|---|---|---|
| Gen3 x16 (~12.5 GB/s) | ~5.4 ms | a meaningful slice, but well inside budget |
| Gen4 x16 (~32 GB/s) | ~2.1 ms | negligible |

At a more MVP-realistic 512×512 with the same four fields (~4.2 MB), the
cost is **sub-millisecond either way** -- not a real constraint at all.

**Where this changes:** 3D (Stage 10) scales as N³, not N². A 512³ grid
with the same four fields is ~4.3 GB/frame -- the same fallback would be
disqualifying at that scale, not merely slow. That is explicitly future
work, not a Stage 0-5 concern, and is exactly why keeping the operator
layer swappable (the Array API standard, §2) matters: the round-trip
decision taken now does not have to be the one still in force at Stage
10.

**Consequence for the classes in §6:** the 🟡 fallback in Class 2 and
Class 4 is very likely a non-issue at the scale this project will
actually be running at for several stages. The "defeats much of the
point of a GPU array library" framing in Class 2's original *Costs*
entry was true in principle but overstated in practice for this
project's near/medium-term scope -- revised there.

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
| **Proven for this domain specifically** | Checked live, 2026-08-15, for the Class 2 array libraries. **JAX-Fluids** (differentiable compressible/two-phase CFD, runs CPU/GPU/TPU) and **PhiFlow** (multi-backend differentiable PDE/fluid framework -- "the exact same code runs a 2D NumPy sim or a 3D GPU PyTorch/JAX sim") both exist and validate the *compute-side* pattern -- swappable NumPy-shaped backends genuinely work for fluid simulation, not just in theory. **Caveats, checked rather than assumed:** both are themselves stale as dependencies would be judged in this survey -- JAX-Fluids' latest release is 2025-03-21 (~17 months old), PhiFlow's is 2025-08-02 (~1 year old) -- though this matters less here than Taichi's staleness does, since PyFlow would not depend on either package, only take them as evidence the architecture works. **More importantly: neither resolves the rendering-coupling question above.** PhiFlow's own answer to visualization is a web-based interactive UI (`view()`), not a native desktop render loop -- architecturally different from what `roadmap.md` TASK-007 specifies (window, render loop, clean shutdown). These projects prove the compute pattern; they sidestep the native-rendering question rather than answering it. **Also checked and explicitly ruled out as evidence: JAX-CFD**, Google's own earlier CFD-in-JAX project, carries an explicit "no longer maintained" notice from Google in its own commit history (2026-02-24) -- it very nearly went into this survey as a positive data point before that was found; JAX-Fluids and PhiFlow are the sources actually being cited here. |

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
- *Costs:* the true zero-copy interop in §4 is real engineering risk, not
  yet spiked. **Revised 2026-08-15 after §4.1's estimate:** the
  host-round-trip fallback, initially assumed to "defeat much of the
  point of a GPU array library," is very likely a non-issue at this
  project's near/medium-term scale (sub-millisecond at MVP grid sizes,
  single-digit milliseconds even at a generous 2048×2048) -- a real cost
  only reappears at Stage 10's 3D scale, later work. This meaningfully
  de-risks Class 2 relative to the first survey pass.
- *Proven for the domain:* CuPy, PyTorch and JAX are all independently
  and currently well-maintained (verified live, §2), and the
  array-library-with-swappable-backend *pattern itself* is validated for
  fluid simulation specifically by JAX-Fluids and PhiFlow -- with the
  caveat that neither of those reference projects is itself current, and
  neither proves out native-renderer coupling (§5, "Proven for this
  domain specifically").
- *Hardware portability:* CuPy and PyTorch both have genuine,
  **official** multi-vendor GPU support (ROCm; PyTorch adds Apple MPS) --
  verified live, not assumed. This is real versatility no GPU-capable
  candidate outside Class 1/2 offers; Class 3 and Class 4 are both locked
  to a single vendor's hardware.
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
- *Reversibility:* lowest of the classes surveyed -- this is a full-stack
  commitment, not a swappable instance.

### Class 4 — Warp for compute, general-purpose or bridged renderer
**Warp kernels** + VTK/VisPy/wgpu/ModernGL (host round-trip, or its own
`OpenGLRenderer` as an unconfirmed possible shortcut). *Added 2026-08-15
after live verification; not part of the survey's first pass.*
- *Forecloses:* the same as Class 3 on the operator side and worse --
  Warp's kernel-DSL model is, like Taichi's, not NumPy-shaped, so it
  carries the same cost against `ADR-003`'s replaceable-interface
  principle **without** Class 3's payoff of a first-class native
  renderer. Warp's own renderer is documented as debug-grade, so this
  class most likely still needs the same interop work as Class 2 for a
  production render path.
- *Enables:* the best-maintained GPU-capable option surveyed (monthly
  releases, latest 12 days old at verification), full Python 3.14
  support with no version conflict, and CFD explicitly demonstrated as a
  target domain by the project itself -- a real edge over CuPy/PyTorch/
  JAX, which are general-purpose libraries repurposed for this rather
  than built for it. **Also found 2026-08-15:** Warp is the compute
  layer under NVIDIA's own **Newton** physics engine (via Isaac Lab),
  which explicitly includes MPM for fluid and granular-material
  simulation -- real, large-scale production validation of Warp for
  physics simulation generally, from the vendor's own flagship robotics
  stack, not merely a documented example.
- *Costs:* CUDA-only -- no ROCm, no Metal, narrower hardware portability
  than Taichi's stated multi-backend support or than a NumPy-based Class
  1/2 (§6, Class 2's now-verified ROCm/MPS support makes this contrast
  sharper than the first survey pass had it). The rendering-side interop
  uncertainty is the same open risk as Class 2, but **§4.1's round-trip
  cost estimate applies here too** -- the fallback via a general-purpose
  renderer is very likely inexpensive at this project's near-term scale,
  which narrows Class 4's practical disadvantage against Class 2 to
  mainly the DSL cost and the hardware constraint, not raw feasibility.
- *Reversibility:* low on the compute side (kernel DSL lock-in, same as
  Class 3); the renderer instance is comparatively swappable since it is
  not bundled the way Taichi's is.
- *In short:* this class inherits Class 3's architectural commitment
  cost without fully inheriting its rendering payoff, in exchange for
  materially better maintenance, no Python-version conflict, and
  real large-scale production validation (Newton). Whether that trade is
  worth it depends on how much the native-render property was actually
  valued versus the DSL cost itself -- and, now, on how much CUDA-only
  hardware scope matters against Class 2's verified multi-vendor support.

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
3. ~~NVIDIA Warp's current ecosystem maturity relative to Taichi~~ --
   **resolved 2026-08-15, verified live.** Warp is materially better
   maintained than Taichi (monthly releases, latest 12 days old at
   verification vs. Taichi's 1yr+) and supports Python 3.14 with no
   conflict. But it is not a like-for-like substitute: its own renderer
   is documented as debug-grade, not production, so it does not deliver
   Taichi's "compute and render share a runtime" property. See Class 4
   and §2's Warp entry. Two things from this check remain genuinely
   open: whether Warp's `OpenGLRenderer` can consume Warp arrays without
   a host round-trip (undocumented), and whether CUDA-only is an
   acceptable hardware constraint for this project.
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
