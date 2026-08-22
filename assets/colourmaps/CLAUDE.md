# CLAUDE

Intended for named colour ramps that field rendering would load rather
than hard-code. **Empty, and deliberately so as of 2026-08-22.**

The reasoning, so the emptiness reads as a decision rather than a gap:
`adr/ADR-005-compute-rendering-instances.md` records that wgpu/pygfx
provides no turnkey colour maps, so PyFlow has to supply its own -- and
this directory was created against that expectation, gated on the Stage
2 field-rendering task (roadmap TASK-017). That task landed 2026-08-21
and chose **one built-in two-stop gradient** instead: `low_color` ->
`high_color`, both configurable through `FieldDisplayConfig`,
interpolated by `_map_values_to_colors` in
`src/pyflow/rendering/field_visualization.py`. A perceptually-uniform
library (viridis, plasma, ...) was deferred under P-016 until a real
need exceeds a two-stop ramp, and adding one later is a colour-mapping
function plus data, not an architecture change.

So the trigger for filling this directory is **a real need for a named
ramp** -- a demo or user asking for one, a scientific-communication
requirement for perceptual uniformity -- not the next stage number.
Whoever fills it should also decide the file format here, in this file,
before writing the first one.

Carved out of `docs/planning/backlog.md` A3's "no file tracked here is
empty" rule on those terms; `docs/repository-manifest.md`'s `assets/`
row states the same thing from the inventory side.
