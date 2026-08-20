# CLAUDE

Configuration package: separates engine construction from engine
execution, per `docs/planning/roadmap.md` TASK-005. Simulation components
should be selected and parameterised through configuration here, not by
editing engine code.

**Implemented 2026-08-16 (D1).** `schema.py` defines `PyFlowConfig`
(nested dataclasses: `LoggingConfig`, `RenderingConfig`), every field
defaulted so `PyFlowConfig()` alone is a complete, valid configuration --
that's what lets the application start with no config file at all.
`loader.py`'s `load_config(path)` reads YAML (`pyyaml`) and constructs the
dataclasses from it; unknown sections or fields raise `ValueError`
immediately rather than being silently ignored, and each dataclass's own
`validate()` checks value ranges (e.g. `rendering.backend` must be a
known canvas backend, width/height must be positive).

Deliberately simple, per TASK-005's own instruction: no schema-inference
library, no partial-merge-with-defaults logic beyond what dataclass field
defaults already give for free.

**`rendering.backend`** (`"glfw"` | `"offscreen"`) is the seam between
this package and `src/pyflow/rendering/`: it selects which canvas backs
the render window without the renderer code ever hardcoding a windowing
library. See `rendering/CLAUDE.md`.

**`rendering.background_color`** (`"#RRGGBB"` or `None`, added
2026-08-16 D5) exists specifically so golden demos can have distinctive,
verifiable visual content *as configuration* rather than demo-specific
Python code -- `docs/implementation/golden-demos.md`'s public-API rule
requires exactly this: if a demo needs something the config schema
doesn't expose, that's a reason to extend the schema, not to write a
one-off script that reaches around it. Validated as a strict
`#RRGGBB` hex string; `None` (the default) leaves the background unset,
matching pygfx's own default.

Import via `from pyflow.configuration import load_config, PyFlowConfig`
-- `__init__.py` re-exports the public API rather than requiring callers
to know the internal `schema`/`loader` module split.

**`RenderingConfig.grid_color`/`zoom`/`pan`/`zoom_min`/`zoom_max`**
(TASK-013, added 2026-08-20): `grid_color` follows `background_color`'s
exact `None`-means-off pattern -- a config that doesn't mention it
renders exactly as before. `zoom`/`pan` are the camera's *initial*
state; `zoom_min`/`zoom_max` bound *live* zoom (mouse wheel) at runtime,
not just the initial value -- `validate()` checks `zoom_min > 0`,
`zoom_max > zoom_min`, and that the initial `zoom` actually falls within
`[zoom_min, zoom_max]`, so a config can't start already out of its own
declared bounds. `pan` is the second tuple-typed field in this package
(after `MeshConfig`'s below) and gets the same `__post_init__`
normalisation for the same reason -- YAML gives a `list`, the dataclass
declares a `tuple`.

**`MeshConfig`** (TASK-012, added 2026-08-20): `origin`, `spacing`,
`extent` (`(nx, ny)`), everything `StructuredCartesianMesh.from_config`
needs to build a mesh with no bespoke code -- the same reasoning as
`background_color` above, applied to Mesh. First config section with
tuple-typed fields, which needed one new piece of handling the others
didn't: YAML parses `origin: [1.5, -2.25]` as a `list`, not a `tuple`, so
`MeshConfig.__post_init__` normalises every field to its declared tuple
type regardless of whether it came from YAML or was constructed directly
in code -- otherwise the field's runtime type would silently disagree
with its declared one for any config loaded from a file.
