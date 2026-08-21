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

**`RenderingConfig.show_mesh`/`grid_color`/`zoom`/`pan`/`zoom_min`/
`zoom_max`** (TASK-013, added 2026-08-20): `show_mesh` asks for the
configured mesh to be drawn, `grid_color` says what colour to draw it
in. These were one field until 2026-08-21, when `grid_color` was
`str | None` and followed `background_color`'s `None`-means-off pattern
-- which read as consistent but wasn't the same case. `background_color`
being `None` means "add no background object at all", a rendering state
pygfx genuinely distinguishes; `grid_color` being `None` meant "don't
draw the mesh", which is not a property of a colour. The practical cost
was that you could not ask for the mesh in the default colour, or record
a preferred colour without also switching the mesh on. Separating a
switch from the thing it configures is the general rule; watch for the
same shape in any later `*_color` field. `zoom`/`pan` are the camera's *initial*
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

**Malformed input produces a field-named error, always** (added
2026-08-21, repository audit). A field's declared type says what valid
input produces; it guarantees nothing about what `load_config` is
handed, because the input is YAML. Three cases were escaping as raw
Python errors: `width: "wide"` raised `TypeError: '<=' not supported
between instances of 'str' and 'int'` from inside `validate()`, which
ran *outside* `loader.py`'s `try` and so was neither caught nor
prefixed; `origin: [1.0, 2.0, 3.0]` raised "too many values to unpack";
and `extent: [10.9, 3.99]` was not an error at all -- `int()` truncated
it to `(10, 3)` and built a different mesh than the one asked for,
silently.

Two rules came out of it. **`schema.py`'s `_number_pair`/`_integer_pair`/
`_require_*` helpers are how a field is normalised**, not bare unpacking
or `int()`/`float()` -- they name the field in every message, and
`_integer_pair` refuses a fractional cell count rather than rounding on
the user's behalf (`[10.0, 4.0]` is fine; a whole number written as a
float is unambiguous). **And `validate()` belongs inside `loader.py`'s
`try`**, not after it: construction is not the only step that can fail
on bad input, and putting it inside is also what attaches the file's
name to every error, including the hand-written checks that know their
field but not their file.
