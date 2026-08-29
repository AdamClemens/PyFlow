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

**`FieldDisplayConfig`** (TASK-017, added 2026-08-21): `scalar_pattern`/
`vector_pattern` select from a small, closed set of built-in
initial-condition patterns (`"radial_gradient"`/`"rotational"`) for the
Field Rendering golden demo only -- `None` (the default for both) means
"don't display that field." Deliberately narrower than `Field`'s own
general-callable Python API (TASK-015/016's `initial_value`): YAML
cannot carry a Python callable, and this schema exists only so the
golden demo can satisfy the public-API rule, not to become a general
expression language nobody else has asked for. `low_color`/`high_color`/
`value_range` parameterise the scalar colour ramp
(`src/pyflow/rendering/field_visualization.py`); `arrow_color`/
`arrow_scale` the vector arrows; `show_legend` toggles the legend strip.
The legend's screen position is deliberately *not* a config field --
`bootstrap.py` computes it from the mesh's own bounding box, keeping
this schema to the fields a demo author actually needs to vary, not
every rendering parameter that happens to exist.

**`SimulationConfig`** (TASK-030, added 2026-08-28): `PyFlowConfig.
simulation`, seeding a real, repeatedly `simulation.step()`-advanced run
-- deliberately a separate section from `FieldDisplayConfig` above, not
a widening of it, since the two answer different questions
(`FieldDisplayConfig` seeds one static rendered frame; this seeds a live
one, driven from `RenderWindow.run(on_frame=...)` via `bootstrap.py`).
`scalar_pattern`/`velocity_pattern` follow `FieldDisplayConfig`'s own
closed-`Literal`-pattern-names precedent (`"gaussian_blob"`/`"uniform"`),
each `None` by default meaning "no live simulation" -- every existing
demo (`field_display`, `numerics_assembly`) is unaffected. Colouring the
live field reuses `field_display.low_color`/`high_color`/`value_range`
as-is; this section has no colour fields of its own, since "how a scalar
field is coloured" is a question `FieldDisplayConfig` already answers
and this section has no reason to answer twice. Shape parameters (the
blob's own center, width) are deliberately not configurable here either,
derived from the mesh's own bounds in `bootstrap.py` instead -- the same
"derived from mesh bounds, not a config field" precedent
`_scalar_display_initializer`'s own `center` already set for
`FieldDisplayConfig`'s "radial_gradient" pattern. `velocity` is a
prescribed (not solved) constant vector, `_number_pair`-normalised the
same way `RenderingConfig.pan`/`MeshConfig.origin` are -- Stage 5 is what
eventually solves Navier-Stokes for real, so a prescribed field is the
only kind of "velocity" any Stage 4 demo can legitimately have.

**`velocity_solved: bool` (TASK-031, added 2026-08-29) is the
solved-vs-prescribed control Stage 5 adds -- a separate field, not a
widened `velocity_pattern`.** `velocity_pattern` says what shape the
initial condition has; `velocity_solved` says what happens to it
afterward (transported by `step`, or held fixed every frame like every
Stage 4 demo). Folding the two together was considered and rejected --
the identical mistake this project already made and corrected once
(`RenderingConfig.show_mesh`/`grid_color`, above): there would be no way
to ask for a non-uniform *solved* initial condition without inventing a
second closed set, and no way to record a preferred pattern without also
deciding whether it's solved. Defaults `False`, matching every existing
demo's own behaviour exactly. `bootstrap.py`'s own
`_add_passive_scalar_transport` reads it: when `True`, `velocity`'s two
components (`VectorField.decompose`) join the live loop's `state`
alongside any transported scalar and are reassembled
(`VectorField.assemble`) after every frame -- still requires a
`scalar_pattern` too, since there is no velocity-only live rendering
path yet (`docs/planning/roadmap.md` TASK-031's own Status note).
**That gap is closed by TASK-034 (Stage 5, 2026-08-29)**:
`bootstrap.py`'s new `_add_solved_velocity_rendering` is the
velocity-only path this note anticipated, selected when `velocity_solved`
is `True` and `scalar_pattern` is `None` -- the Lid-Driven Cavity demo's
own shape. Uses `navier_stokes_step`, not plain `step`, so this path is
genuinely pressure-corrected every frame; `_add_passive_scalar_transport`'s
own `velocity_solved` path (a scalar *and* a solved velocity together)
is unaffected and still uses plain `step`, a real, pre-existing gap this
task did not close, since nothing before TASK-034 had a corrector loop
to call there either.

**`ScalarTransportPattern` gained a second value, `"sinusoidal_mode"`
(TASK-034, added 2026-08-29)** -- the Heat Diffusion demo's own initial
condition: a single spatial Fourier mode, one full wavelength across the
mesh's own x-extent (`wavenumber = 2*pi / domain_width`, the same
"derived from mesh bounds" precedent every other pattern here follows),
with no y-dependence. The one initial condition PyFlow's diffusion
equation has a closed-form decay-rate answer for at all -- P-016 permits
this addition directly, per Criterion 12's own "a member is added [to a
pattern set] precisely because a demo needs it".

**`generator.py`'s `generate_config_yaml` (TASK-039, added 2026-08-21)
is `loader.py` run in reverse**: `load_config` turns YAML into a
validated `PyFlowConfig`; `generate_config_yaml` turns a `PyFlowConfig`
(defaulting to `PyFlowConfig()`, i.e. every field's own default) back
into YAML a config author starts from, rather than hand-typing section
and field names from memory against this file and finding out about a
mistake only when `load_config` rejects it. Reuses
`dataclasses.asdict()` rather than a hand-written serialiser -- every
section here is already a plain `@dataclass`, and `asdict()` already
knows how to walk it, the same "don't restate a fact the schema already
knows" reasoning `docs/CLAUDE.md` states for generated documentation.
The one gap `asdict()` leaves is tuples: it preserves them exactly
(`MeshConfig.origin`, `RenderingConfig.pan`), and `yaml.safe_dump` (via
`SafeDumper`) has no representer for a bare `tuple` -- unlike the full
`Dumper`, which would tag it `!!python/tuple` and produce YAML
`load_config` couldn't read back. `_tuples_to_lists`, a small recursive
pass run before dumping, closes that gap; it is this package's
list-to-tuple normalisation (`MeshConfig.__post_init__`, above) run in
the opposite direction, for the same reason -- YAML's data model has no
tuple, only a list.

**A CLI subcommand (`pyflow generate-config`), not a `tools/
generators/` script**, unlike this repository's other generators
(`generate_docs_index.py`, `generate_dependency_tree.py`,
`generate_repository_inventory.py`). Those regenerate *committed
repository artifacts* that `make ci` checks for staleness -- documentation
about the repository itself. A generated config file is not a repository
artifact; it is something a user or golden-demo author produces for
their *own* run and then edits, the same category of thing `pyflow run`
already is. `src/pyflow/__main__.py` wires it in as `pyflow
generate-config [--output PATH]`, printing to stdout by default
(pipeable) or writing straight to `PATH`.

**Deliberately scoped to a scaffold, not a wizard.** No per-field CLI
overrides, no inline YAML comments (`PyYAML`'s `safe_dump` cannot
produce them -- comments aren't part of the YAML data model it
round-trips). "So we don't need to write configs by hand" is satisfied
by a correct starting file a user then edits; anything past that has no
real consumer yet and is deferred, not forgotten, the same
reversible-decisions preference already applied to `CoordinateSystem`'s
second implementation and `rendering/canvas.py`'s third backend.

**`NumericsConfig`** (TASK-018, added 2026-08-23; completed TASK-021,
2026-08-23): the full six-field `numerics` section
(`docs/architecture/icds.md`'s six `adr/ADR-003-modular-numerical-
strategies.md` components). `advection`/`diffusion`/`time_integration`/
`linear_solver`/`pressure_coupling` are each `Literal`-typed against a
single valid name (`"first_order_upwind"`, `"central_difference"`,
`"rk4"`, `"conjugate_gradient"`, `"piso"`) -- `icds.md`'s sole named MVP
choice for each, not a speculative list of future ones, following the
same pattern `ScalarDisplayPattern`/`VectorDisplayPattern` already
established for a closed, currently-one-member set. **A name that
validates here resolved only to a trivial, non-physical reference
implementation under `src/`, not a real scheme, through Stage 3**
(Stage 3 Completion Criterion 1 forbade any *real* concrete scheme
shipping that stage); Stage 4 replaces each reference implementation in
turn as its own task lands, `advection` first (TASK-023, 2026-08-27) --
`"first_order_upwind"` now resolves to `FirstOrderUpwindAdvection`, a
real scheme. `engine/numerics/assembly.py`'s `assemble_numerics` is what
resolves a name; see that module's own docstring for why the remaining
four still resolve to a reference class, and for which ones. TASK-019/020/022/021 each added their own field(s) to
this same dataclass as Stage 3 proceeded -- see `docs/planning/
roadmap.md`'s Stage 3 discharge map for which task added which field,
and in what order (TASK-022 before TASK-021, despite the number, because
Pressure–Velocity Coupling's interface needs `LinearSolver`'s type to
exist first).

This is the first schema addition made without a corresponding
`Artifacts Produced` bullet in its own roadmap task entry -- TASK-018's
entry named the change only in its **Discharges** section ("adds
`numerics.advection` and `numerics.diffusion` to the new
`NumericsConfig`"), which every task after it (TASK-019/020/022) states
directly under `Artifacts Produced` for its own share. Treated as a
drafting gap in TASK-018's own entry, not
a reason to skip the work: the Discharges section is precisely what
`docs/practices.md`'s "every task names the stage criteria it
discharges" rule exists to make an unmissable claim, and a claim it
makes should not go unbuilt because a sibling section forgot to repeat
it.

**`time_integration`/`timestep`** (TASK-020, added 2026-08-23):
`time_integration` follows the same closed-`Literal` pattern as
`advection`/`diffusion` -- `"rk4"` is `icds.md`'s sole named MVP choice,
and, like `diffusion` (though no longer `advection`, since TASK-023),
only a reference implementation resolves it under `src/` for now.
`timestep` is different in kind from every other field this
dataclass has added so far: a plain positive `float`, not a name from a
closed set, because `docs/planning/roadmap.md` TASK-020 records "a fixed
timestep is configured directly; no automatic stability limit" as the
MVP position rather than a scheme choice. `0.01` is an arbitrary
default -- no golden demo or handbook page names a specific value yet --
and `validate()` rejects `timestep <= 0` directly, the one acceptance
criterion this field carries on its own.

**`linear_solver`/`linear_solver_tolerance`/`linear_solver_max_iterations`**
(TASK-022, added 2026-08-23): `linear_solver` is the same closed-`Literal`
pattern again -- `"conjugate_gradient"` is `icds.md`'s sole named MVP
choice, only a reference implementation resolves it under `src/`. The other two follow
`timestep`'s precedent (plain positive numbers, not names) rather than
being folded into the scheme name, because they are the solver's own
tunables (how tight, how patient), not a choice between solvers --
`docs/planning/roadmap.md` TASK-022 names both fields directly and
requires each to reject `<= 0` at `load_config` time, independently.
`1e-6`/`1000` are arbitrary MVP defaults, the same reasoning as
`timestep`'s `0.01`.

**`pressure_coupling`** (TASK-021, added 2026-08-23, Stage 3's last
field): the same closed-`Literal` pattern one final time --
`"piso"` is `icds.md`'s sole named MVP choice, and, same as the other
two scheme-name fields still awaiting their own Stage 4 task
(`time_integration`, `linear_solver` -- `advection`/`diffusion` no
longer among them, since TASK-023/024), only a reference implementation
resolves it under `src/`. Completes the six-field `numerics` section
`adr/ADR-003-modular-numerical-strategies.md` names.

**`pressure_correction_tolerance`/`pressure_correction_max_iterations`**
(TASK-033, added 2026-08-29, Stage 5's fourth task): the *outer*
corrector loop's own tunables, following `linear_solver_tolerance`/
`linear_solver_max_iterations`'s own precedent exactly (plain positive
numbers, `validate()` rejects `<= 0` for each independently) but
naming a genuinely different thing -- `linear_solver_tolerance` governs
each pass's *inner* linear solve, these two govern how many passes the
corrector loop itself takes and how small the recorded divergence must
get before it stops. Stage 5's own design question three ("outer-loop
state the strategy owns," `docs/planning/roadmap.md` TASK-033) is why
these live in `numerics:` as two more scalar fields rather than as a
`PressureCoupling.correct` parameter -- the split TASK-041 already drew
between `numerics:` (numerical parameters) and `fluid:` (physical
properties) put these on the `numerics:` side without a new question,
since a corrector loop's own iteration budget is exactly the kind of
thing `linear_solver_tolerance`/`linear_solver_max_iterations` already
established belongs there. `1e-6`/`50` are arbitrary MVP defaults, the
same reasoning as `timestep`'s `0.01` -- `50` deliberately smaller than
`linear_solver_max_iterations`'s own `1000`, since an outer corrector
pass is far more expensive than one CG iteration.

**`diffusion_coefficient`** (TASK-024, added 2026-08-27; **migrated to
`FluidConfig.diffusion_coefficient` by TASK-041, 2026-08-28 -- no longer
a `NumericsConfig` field**): originally followed `timestep`'s own
pattern here -- a plain positive `float`, not a name from a closed set,
because this is Gamma (`docs/handbook/numerical-methods/diffusion.md`),
a physical property of what's being transported, not a choice between
schemes -- which is exactly why it moved out of the section that selects
schemes. `loader.py`'s `_numerics_config_from_raw` rejects a
configuration still setting `numerics.diffusion_coefficient` with a
named error pointing at its new home, rather than silently ignoring it
or resolving it via `NumericsConfig`'s ordinary unknown-field path. See
`FluidConfig`, below, for where it lives now.

**`FluidConfig`** (`PyFlowConfig.fluid`, TASK-041, added 2026-08-28,
Stage 5's first task): `viscosity` and `diffusion_coefficient`, physical
properties of the simulated fluid, deliberately separated from
`NumericsConfig` -- a numerical scheme is a discretisation choice, a
fluid property is not, and the two do not belong in one section (Stage
5's design question four, `docs/planning/roadmap.md`). `diffusion_
coefficient` migrated here from `NumericsConfig` (previous entry, above);
`viscosity` is new, and nothing reads it yet -- momentum's own diffusion
coefficient, threaded into velocity's diffusive flux once TASK-031b
lands. Both default to `1.0`, `validate()` rejects `<= 0` for either, the
same plain-positive-number pattern `timestep`/`diffusion_coefficient`
already established. **A real, unplanned engine-side consequence of the
migration, not just a schema move**: `engine/numerics/assembly.py`'s
`assemble_numerics` already read `NumericsConfig.diffusion_coefficient`
directly (TASK-024) -- moving the field out from under it needed a real
signature change (`assemble_numerics` gained its own `diffusion_
coefficient: float = 1.0` parameter), not just a schema and a config
file. See `src/pyflow/engine/CLAUDE.md`'s `assembly.py` entry for the
mechanical detail, and `docs/planning/roadmap.md` TASK-041's own Status
note for why this task's own Dependencies section ("no engine dependency
at all") was wrong as drafted.

**`BoundaryFaceConfig`/`BoundaryConditionsConfig`** (TASK-019, added
2026-08-23): `NumericsConfig.boundary_conditions`, one
`BoundaryFaceConfig` per domain edge (`north`/`south`/`east`/`west`).
The first nested-dataclass-within-a-dataclass field this schema has --
`dataclasses.asdict()` (`generator.py`) already handles the recursion
for free, but `loader.py`'s read direction does not get the same free
ride: a plain `BoundaryConditionsConfig(**raw.get("boundary_conditions",
{}))` would hand each boundary's raw `dict` straight to a
`BoundaryFaceConfig` parameter expecting an instance, not construct one.
`loader.py`'s `_numerics_config_from_raw`/
`_boundary_conditions_config_from_raw` do that reconstruction by hand,
one level at a time -- the same shape of gap `MeshConfig`'s tuple
normalisation and `generator.py`'s `_tuples_to_lists` each close for
their own type mismatch between what YAML gives and what the dataclass
declares, applied here to nesting depth instead of tuples.

`BoundaryFaceConfig.velocity`/`.pressure` are independent
`float | None` fields, not a single quantity-tagged value -- this
task's own Acceptance Criteria need "both prescribed on one boundary"
to be a real, rejectable state, which a single `quantity` field would
make inexpressible rather than checked. `velocity` is the
boundary-normal component only, positive outward; see
`docs/planning/roadmap.md` TASK-019 for why a richer per-component
value is deferred rather than built now.

**`BoundaryFaceConfig.scalar_value: float = 0.0` (TASK-028, added
2026-08-28) is a third, independent quantity, deliberately not
`float | None` like `velocity`/`.pressure`.** It carries none of their
mutual-exclusivity or net-flux relation (`icds.md`'s Compatibility
requirements are specifically about the momentum/pressure system), so it
needs no "not prescribed" sentinel -- it defaults to `0.0` for the same
reason `velocity` does, so every existing default `NumericsConfig` stays
valid without a config author naming it. This closes a real gap TASK-040's
own drafting found and deliberately left for TASK-028 to resolve: nothing
in `BoundaryFaceConfig` could express an arbitrary transported scalar's
own Dirichlet boundary value at all, which TASK-030's Passive Scalar
Transport demo needs to configure -- `assembly.py`'s
`_NullValueBoundaryCondition` (the Stage 3 reference implementation
TASK-028 retires) had been reading `velocity` instead, silently correct
only because Stage 3's own golden demo never advects anything. Full
reasoning, including why the general "two different fields need two
different values at one wall" problem stays deliberately out of scope:
`docs/planning/roadmap.md` TASK-028's own Design decision.

**`BoundaryFaceConfig.scalar_gradient: float = 0.0` (TASK-029, added
2026-08-28) is `scalar_value`'s exact Neumann mirror** -- same reasoning
throughout, resolving the gap TASK-028's own drafting had already named
in advance for this task (`docs/planning/roadmap.md` TASK-029's own
Intent), not rediscovered here. `assembly.py`'s
`_NullGradientBoundaryCondition` (the Stage 3 reference implementation
this task retires, the last `_Null*` boundary-condition class) had been
reading `velocity`/`pressure`/`0.0` the same way its Dirichlet-side
sibling did. With this field's addition, every one of the six
`adr/ADR-003` components now has a real concrete scheme.

**`BoundaryFaceConfig.field_values`/`field_gradients: dict[str, float]`
(TASK-031c, added 2026-08-29) are per-field-name overrides of
`scalar_value`/`scalar_gradient` respectively** -- the general mechanism
"one global set of boundary conditions... does not yet express two
fields' own values at once" (TASK-040's own note, above) needed: two
fields transported in one run can each be given their own prescribed
value at the same wall (`u = U`, `v = 0` at a moving lid, the motivating
example, but general -- any field name). A field name absent from either
dict falls back to `scalar_value`/`scalar_gradient`, so every existing
config (which sets neither) is unaffected; both default to `{}`.
`DirichletBoundaryCondition`/`NeumannBoundaryCondition`
(`src/pyflow/engine/numerics/boundary_condition.py`) read these as their
own widened `overrides` constructor parameter, dispatched by
`field.name` at `evaluate()` time -- `assembly.py`'s
`_dirichlet_boundary_condition`/`_neumann_boundary_condition` adapters
thread them through, not this schema itself.

**Whole-configuration validation is a module-level function
(`_validate_boundary_conditions_jointly`), called from
`PyFlowConfig.validate()`, not a method on `BoundaryConditionsConfig`**
-- this task's own design decision: no individual boundary can see the
others, and all three checks (periodic pairing, no dual prescription,
zero net flux) are relations *between* boundaries. The net-flux check
weights each boundary's prescribed velocity by its edge length
(`mesh.extent`/`mesh.spacing`) before summing -- "sum to zero net
flux" means the flux integrated over each edge, not the raw values, and
a rectangular (non-square) mesh has different north/south and east/west
lengths. `tests/unit/test_configuration.py`'s zero-weighted-net-flux
test deliberately uses a fixture whose *unweighted* sum is nonzero
(`docs/practices.md`'s "distinct factors" rule, applied to a
conservation check rather than a geometric one), so a future regression
to summing raw values fails loudly instead of passing by coincidence on
a square mesh.

**One real repository-tooling finding surfaced while implementing
this, not predicted in advance:** `.pre-commit-config.yaml`'s `mypy`
hook (`pre-commit/mirrors-mypy`) runs mypy in its own isolated
environment, separate from the one `uv sync` builds -- and that isolated
environment had no `additional_dependencies` at all, so it had no
`types-pyyaml` (a `pyproject.toml` dev dependency `uv run mypy` gets for
free). `uv run mypy --strict` on this file passed clean; `make lint`'s
pre-commit hook failed the same file with `Returning Any from function
declared to return "str"` on the `yaml.safe_dump(...)` call, because its
isolated mypy fell back to a looser bundled stub for `yaml.safe_dump`'s
overloads instead of `types-pyyaml`'s precise ones. Nothing in this
package's own code was wrong; the two `make` targets that are supposed
to be the same check (`docs/practices.md`'s "single authoritative
source") were silently checking against two different sets of type
stubs. Fixed at the actual gap -- `additional_dependencies:
[types-pyyaml]` added to the `mypy` hook in `.pre-commit-config.yaml` --
rather than papering over the symptom with a `cast` in `generator.py`
that the project's own `uv run mypy` would never have needed. Watch for
the same shape if a future module is the first in `src/pyflow` to lean
on a third-party library's stubs precisely: `make lint`'s isolated mypy
environment only knows the stub packages listed as `additional_dependencies`
for that hook, not the whole `dev` dependency group.

**`docs/implementation/config-template.yaml` must be kept current with
this file** (rule added 2026-08-28, at a user's direct request for an
annotated example config that stays up to date "as the code evolves").
It is generated by `tools/generators/generate_config_template.py` from
the live `PyFlowConfig` tree, one comment per field explaining what
counts as a valid value and what does not -- `pyflow generate-config`
(TASK-039) already produces a loadable scaffold from this same schema,
but `PyYAML`'s `safe_dump` cannot emit comments, so it carries no
explanation of *why* a value is accepted or rejected. Hand-writing that
explanation straight into a committed YAML file would only relocate the
restated-fact problem this package already avoids everywhere else (this
file's own repeated "not restated, derived" reasoning); generating it
from a comment map kept next to the schema it describes is the same fix
applied here.

Concretely: **whenever a field is added, removed, renamed, or has its
valid range/`Literal` options changed in `schema.py`, update
`FIELD_COMMENTS` (or `SECTION_COMMENTS`, for a new top-level section) in
the same change, then run `make config-template`.** This is enforced by
a test, not only remembered, the same shape `src/pyflow/CLAUDE.md`'s CLI
help-text rule uses for the same reason: `tests/unit/
test_generate_config_template.py::test_every_live_config_field_has_a_comment`
walks the real `PyFlowConfig` dataclass tree and fails a plain `make
test` the moment a field exists with no matching comment, regardless of
whether anyone remembered to regenerate the committed file; `make
check-config-template` (part of `make ci`) additionally fails if the
committed file is stale relative to what the schema and comments
together would currently generate. What neither check can verify is
covered by `docs/practices.md`'s Blast Radius rule instead, the same as
everywhere else in this project: whether a comment's *wording* is still
an accurate description of the field's real constraint is a judgement
call for whoever changes that constraint, not something either test can
see.
