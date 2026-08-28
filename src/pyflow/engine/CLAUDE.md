# CLAUDE

Core numerical engine: mesh, field storage, operator interfaces, time
integration, pressure-velocity coupling, linear solvers, boundary
conditions -- the reusable simulation machinery, independent of any
specific physics.

As of 2026-08-15, this package's scope also covers what were briefly
separate, undocumented `interaction/`, `io/`, `simulation/`, and `util/`
packages before that day's structural reconciliation (see
`docs/planning/backlog.md` §1 "TASK-000 package structure mismatch" and
`docs/CHANGELOG-DESIGN.md`): simulation-state I/O, the orchestration/
run-loop tying mesh+fields+time-stepping together, and shared low-level
utilities all live here for now. Split any of these back out into their
own package only once they've grown large enough to justify it -- don't
pre-emptively recreate the split without a documented reason next time.

**`logging_setup.py`** (TASK-006, done 2026-08-16, D2) is the first
occupant of that "shared low-level utilities" scope: `configure_logging`
sets up the `pyflow` logger once at startup (level + formatting), and
every subsystem gets its own logger via `get_logger(__name__)` -- a
child of `pyflow` that inherits level and handler through the normal
logging hierarchy, so "every subsystem logs through the common
framework" is a naming convention, not a mechanism each module has to
opt into.

**`coordinate_system.py`** (TASK-011, done 2026-08-20) is the first
occupant of this package's actual numerical-engine scope (mesh, fields,
operators, ...), not just shared utilities. `CoordinateSystem` is the
layer beneath `Mesh` (TASK-012): index-to-physical and
physical-to-index conversion only, deliberately assuming nothing about
spacing or vertex-vs-cell-center placement -- see
`docs/planning/roadmap.md` TASK-011 for the full design rationale.
`UniformVertexCoordinateSystem` is the first concrete implementation,
matching the MVP (`docs/implementation/mvp.md`: 2D structured Cartesian,
uniform spacing). Built test-first per `docs/practices.md`'s TDD rule,
except the interface/implementation itself was drafted a beat before its
tests rather than strictly after -- worth naming rather than quietly
presenting as clean red-green, even though the tests were written and
verified against it in the same session before anything was called done.
Two test modules cover it, per TASK-011's own Acceptance Criteria split:
`tests/unit/test_coordinate_system_contract.py` (the shared,
implementation-independent contract suite -- parametrised, so a future
`CoordinateSystem` implementation joins by adding a factory there, not by
writing new tests) and `tests/unit/test_uniform_vertex_coordinate_system.py`
(this implementation's own specific claims: exact formula, uniform
spacing, its own error condition). `OffGridCoordinateError` is the
one exception class every implementation's `to_index` raises for a
coordinate that doesn't lie on the grid (renamed 2026-08-21 from
`CoordinateOutOfBoundsError`, which named a condition that doesn't
exist here -- a `CoordinateSystem` has no extent, so nothing can be out
of its bounds; `Mesh` is the layer with bounds, and its own
`InvalidMeshEntityError` is what covers those) -- shared, not per-implementation, so calling code
catches one type regardless of which concrete `CoordinateSystem` it
holds.

A cell-center-based implementation is deliberately not built yet --
planned for when Stage 1+ actually needs it (TASK-011's own note in
`docs/planning/roadmap.md`), following this package's `src/pyflow/
rendering/CLAUDE.md` sibling's same reasoning for not building a third
canvas backend ahead of a real consumer.

**`mesh.py`** (TASK-012, done 2026-08-20) is `Mesh` (cell/face geometry,
neighbour lookup, boundary identification -- independent of structured
vs. unstructured, per `docs/architecture/engine.md`'s own contract) and
`StructuredCartesianMesh`, the first concrete implementation. Same
interface-first pattern as `coordinate_system.py`, same TDD-first
process this time (tests written and confirmed red before any
implementation code, unlike TASK-011 -- see that entry above and
`docs/CHANGELOG-DESIGN.md`, 2026-08-20, for why this one is different).

Cells and faces are identified by a flat integer id, not `(i, j)` --
`StructuredCartesianMesh.cell_id`/`cell_index` convert between the two,
but the `Mesh` interface itself only knows flat ids, since an
unstructured implementation has no `(i, j)` to expose. `face_normal`
returns one canonical normal per face (pointing from owner to
neighbour, or outward for a boundary face); `face_normal_from(face,
cell)` -- a concrete method on `Mesh`, not abstract -- derives the
sign relative to whichever cell is asked, so every implementation only
has to define one normal per face, not two.

`StructuredCartesianMesh` owns its own `UniformVertexCoordinateSystem`
(built internally from the same `origin`/`spacing` passed to its
constructor) rather than accepting an externally constructed one. This
is deliberate, not an oversight: `cell_volume`/`face_area` are computed
directly as `dx * dy`/`dx`/`dy` from that one stored spacing, which is
what makes them bit-exact per TASK-012's Acceptance Criteria --
deriving them instead by subtracting two `to_physical` vertex positions
would be mathematically equivalent but not guaranteed bit-exact for a
non-trivial origin (floating-point subtraction of two nearby
moderately-large floats doesn't reliably reproduce the exact spacing
that produced them). Vertex positions are still used, and are the only
source, for `cell_centroid` (the average of a cell's four corners),
which the Acceptance Criteria require to come from the coordinate
system rather than a shortcut formula.

Contract suite: `tests/unit/test_mesh_contract.py` (round-trip-free this
time -- geometric closure, boundary exhaustiveness/exclusivity,
neighbour symmetry). Implementation-specific:
`tests/unit/test_structured_cartesian_mesh.py`.

**Every accessor validates its id (added 2026-08-21, repository audit).**
`InvalidMeshEntityError` -- an `IndexError` subclass, one shared type for
every implementation, the same reasoning as `OffGridCoordinateError`
above -- is raised for a cell or face id outside its range. Before this,
a flat id that overran returned a plausible wrong answer instead:
`cell_centroid(999)` on a six-cell mesh gave `(0.5, 333.5)`, and
`face_neighbours(9999)` named two cells that don't exist. Nothing about
a flat integer distinguishes a real id from arithmetic that overran,
which is exactly the failure Stage 3's operator loops will produce, and
it would surface as a wrong number rather than an exception. `Mesh`
provides `_check_cell`/`_check_face` so implementations don't each write
the check; the contract suite is what actually holds them to it.
`StructuredCartesianMesh.cell_id` validates the *structured* `(i, j)`
rather than the flat id it produces -- `(nx, 0)` and `(0, 1)` flatten to
the same integer, so checking after flattening would accept a column
overrun as a valid cell in the next row, silently, right at the domain
edge where boundary handling lives.

**`face_vertices`, added 2026-08-20 once TASK-013 actually needed it.**
The note directly above this one (written for TASK-012, before TASK-013
started) said not to build a vertex accessor ahead of a real consumer --
TASK-013 is that consumer. Added the minimal thing it actually needed:
`face_vertices(face) -> (vertex0, vertex1)`, a face's two endpoints (a
face *is* a line segment in 2D), not a general cell-corner accessor. The
contract suite gained one more implementation-independent invariant for
it: a face's two vertices are exactly `face_area(face)` apart, since
that's just what "area" means for a line segment, true for any `Mesh`.
2D-specific, like every other `Mesh`/`CoordinateSystem` method so far --
expected to need revisiting once Stage 11 (Three Dimensions) arrives,
not a gap being
worked around now.

**`boundary_face_name`, added 2026-08-27 (TASK-023), additive on
`StructuredCartesianMesh` only, not the abstract `Mesh`.** The first
concrete Advection scheme needed to map a boundary face to which of
`NumericsConfig.boundary_conditions`'s four named edges
(`north`/`south`/`east`/`west`, typed once as `BoundaryFaceName` and
reused rather than repeated) it lies on, in order to pick the right
`BoundaryCondition` -- `is_boundary_face`/`face_neighbours` only say
*whether* a face is a boundary face, never *which* edge. Kept off the
abstract interface for the same reason `face_vertices` above stays
2D-specific rather than speculative: only a structured, axis-aligned
mesh has a natural north/south/east/west concept to expose, and nothing
has yet needed one from an unstructured implementation. The same shape
TASK-030's own periodic wrapped-neighbour lookup independently commits
to for its own `StructuredCartesianMesh`-specific need -- see that
task's own Design decision, below, once it lands. Tested in
`tests/unit/test_structured_cartesian_mesh.py` (the implementation-
specific suite, not the shared `Mesh` contract), checked against the
`(i, j)` index a face was built from rather than `mesh.py`'s own
internal face-id encoding.

**`face_centroid_distance`, added 2026-08-27 (TASK-024), concrete on the
abstract `Mesh` itself -- deliberately not additive on
`StructuredCartesianMesh` only, unlike `boundary_face_name` above.** The
first concrete Diffusion scheme needed the distance between the two
cell-centred values its central-difference formula differences --
interior face: the distance between the two neighbouring cells' own
centroids; boundary face: the owner-centroid-to-face distance, via the
owner-to-face-midpoint vector projected onto `face_normal`. Kept
*concrete*, not additive-and-abstract or additive-and-concrete-only,
because the underlying quantity is meaningful for any FVM mesh
(structured or not) -- the same category as `cell_volume`/`face_area`/
`face_vertices`, all already abstract -- unlike `boundary_face_name`'s
own "north/south/east/west", which is specifically an axis-aligned
structured-mesh concept. Built entirely from already-abstract accessors
(`cell_centroid`, `face_neighbours`, `face_vertices`, `face_normal`), the
same "concrete helper built from existing primitives" shape
`is_boundary_face`/`face_normal_from` already establish, so every `Mesh`
implementation gets it for free without overriding anything.
`tests/unit/test_mesh_contract.py` gained two new implementation-
independent invariants (positive for every face; an interior face's
value agrees with the straightforward centroid-to-centroid Euclidean
distance); `tests/unit/test_structured_cartesian_mesh.py` checks the
exact formula against known grid spacing (full spacing for an interior
face, half for a boundary one).

**`field.py`** (TASK-014, done 2026-08-21) is `Field`, the abstract base
every physical quantity the engine transports will share -- Variables,
in `docs/architecture/engine.md`'s terms. Deliberately carries no
storage at all: only `mesh`, `name` (both immutable after construction,
read-only properties over private attributes) and an abstract `copy()`.
The restraint is the point -- an earlier draft of this task put
cell-count-shaped tensor allocation directly on `Field`, which would
have silently committed the interface to collocated (cell-centred)
storage despite its own stated promise not to assume any particular
arrangement; caught before landing, not after (`docs/CHANGELOG-DESIGN.md`,
2026-08-21). `CollocatedField` (TASK-015, not yet built) is where actual
storage, generic callable-based initialisation, and value access will
live, shared by `ScalarField` and `VectorField` alike.

No contract test suite yet -- `tests/unit/test_field.py` exercises
`Field` directly through two minimal test-only subclasses defined in
that file (`_CompleteField`, `_IncompleteField`), since there is no real
concrete implementation for a parametrised suite to run against. That
suite starts at TASK-015, the same way `test_coordinate_system_contract.py`
and `test_mesh_contract.py` each arrived alongside their layer's first
implementation, not before it.

**`collocated_field.py`/`scalar_field.py`** (TASK-015, done 2026-08-21)
are `CollocatedField` (still abstract) and `ScalarField` (concrete) --
`Field`'s first real storage. `CollocatedField.__init__` allocates
`(mesh.num_cells, *component_shape)` as a `torch.float64` tensor and
applies `initial_value` generically (a constant, broadcast to every
cell, or a callable of a cell's `mesh.cell_centroid`, evaluated once per
cell -- the constant case is simply the callable case never being
called, not a second code path). `_tensor_at`/`_set_tensor_at` are the
shared, id-checked tensor access every leaf's `value_at`/`set_value_at`
builds on; `_check_cell` reuses `Mesh`'s own `InvalidMeshEntityError`
rather than a new exception type, since a field's cell id has exactly
`Mesh`'s own valid range.

**`value_at`/`set_value_at` are abstract on `CollocatedField`, typed
generically over a PEP 695 type parameter, not concretely implemented
returning a tensor.** Found while implementing, not while planning: a
concrete `CollocatedField.value_at(self, cell: int) -> torch.Tensor`
would make `ScalarField.value_at(self, cell: int) -> float` an
incompatible override under `mypy --strict` -- `float` and `Tensor`
aren't related types, so narrowing the return type on override is not
the covariant case mypy allows. `class CollocatedField[T](Field):`
declares `value_at`/`set_value_at` abstract over `T` instead (PEP 695
class-level type parameter syntax -- `ruff`'s `UP046` rule prefers this
over `Generic[T]` at this project's `py314` target; a first draft used
`Generic[T]`/`TypeVar("T")` and `ruff` flagged it during commit);
`ScalarField` (`CollocatedField[float]`) satisfies them by converting
through `_tensor_at`/`_set_tensor_at`. The same fix needed `Field.copy`
typed `-> Self` rather than `-> Field` (`typing.Self`) -- otherwise
`field.copy()` on a `CollocatedField[Any]`-typed value returns the
abstract base's own type, losing access to `.values`/`.set_value_at`
entirely. `tests/unit/test_collocated_field_contract.py` (TASK-014's
deferred contract suite, now real) types its parametrised fixture as
`type[CollocatedField[Any]]` specifically so one suite can call
`value_at`/`set_value_at` generically across every concrete
implementation without per-implementation casts.
`tests/unit/test_scalar_field.py` covers `ScalarField`'s own specific
claims (plain `float` return, exact formula, copy independence for its
own storage).

**There are two contract suites here, one per interface, and the split
is load-bearing** (2026-08-22, Stage 2 exit audit -- `docs/planning/
roadmap.md`). `field.py` deliberately carries no storage so that a
staggered placement can satisfy it; a contract suite that asserts
`values`/`component_shape` therefore cannot be `Field`'s, however
generically it is parametrised. Until this audit there was only one
suite, named `test_field_contract.py`, and it asserted exactly that --
so the only mechanical check of the interface required the very
assumption the interface exists to avoid. Now:

- `tests/unit/test_field_contract.py` -- `Field`'s own: mesh
  association, name, copy independence, nothing else. Parametrised over
  **factories**, not classes, so an implementation whose constructor
  needs more than `(mesh, name)` joins without editing a test.
- `tests/unit/test_collocated_field_contract.py` -- the collocated half
  (the file above, renamed), parametrised over
  `_IMPLEMENTATIONS: list[type[CollocatedField[Any]]]`.

A collocated implementation must pass both. A future alternative
placement passes the first alone -- and if you find yourself wanting to
add a `values`-shaped assertion to the first suite to make something
convenient, that is the bug this split exists to prevent, not a gap in
it.

**`vector_field.py`** (TASK-016, done 2026-08-21) is `VectorField
(CollocatedField[tuple[float, ...]])`, added to the collocated contract
suite's `_IMPLEMENTATIONS` rather than a second suite, per TASK-014's
own stated pattern. `num_components` (default 2,
matching the MVP's 2D velocity) is set on the instance *before*
`super().__init__()` runs, since `CollocatedField.__init__` reads
`self.component_shape` to size storage and `component_shape` here is
`(self._num_components,)` -- ordering that matters and is easy to get
backwards. `value_at`/`set_value_at` convert through
`_tensor_at`/`_set_tensor_at` to a plain `tuple[float, ...]`, the vector
analogue of `ScalarField`'s `float`; `set_value_at` is typed to accept
any `Sequence[float]`, not only a `tuple` -- a deliberately *wider*
parameter type than the base's `T` (contravariant widening is a valid
override under `mypy --strict`, unlike the narrower-return problem
`value_at` itself hit). `component(index)` and `magnitude()` exist
specifically because `TASK-017` (Field Rendering) needs a per-cell
scalar array to feed its colour-map/arrow code, computed once here
rather than `TASK-017` reaching into `.values` directly.
`torch.linalg.vector_norm`'s stub returns `Any` (unlike every other
`torch` call in this package) -- wrapped in an explicit `cast`, the one
place this module needed one, rather than let `mypy --strict`'s
`no-any-return` check pass silently.

**Not the application bootstrap** -- that's `src/pyflow/bootstrap.py`,
deliberately *not* in this package. See `src/pyflow/CLAUDE.md` for why
(a real circular import, found 2026-08-16). The "orchestration/run-loop"
mentioned above is the future simulation run-loop (mesh+fields+
time-stepping, once physics exist), a different thing from startup
bootstrap.

**`numerics/`** (TASK-018, done 2026-08-23) is a subpackage, not five
modules directly here -- `docs/planning/roadmap.md` TASK-018's own
design decision: the six `adr/ADR-003-modular-numerical-strategies.md`
components share one purpose and, from TASK-019 on, one configuration
section, which is what a subpackage is for. `physics/` is deliberately
*not* the home -- it is reserved for phenomena (temperature, buoyancy,
Stage 6), not numerical machinery. TASK-018 itself contributes five
interfaces: `AdvectionScheme`, `DiffusionScheme` (the two of
`ADR-003`'s six this task covers) and `GradientScheme`,
`DivergenceScheme`, `SourceTerm` (interfaces with no configuration
field -- nothing has yet identified a second implementation a user
would choose between, per P-016). **No concrete scheme lives under
`src/` for any of the five** -- Stage 3 Completion Criterion 1 requires
every implementation to live under `tests/` until Stage 4; every class
here is an `ABC` with zero subclasses in this package.

**Every operator's primary argument is typed `Field`, not a concrete
subclass, even where the physics only makes sense for one arrangement**
(Gradient/Divergence/Source). Kept uniform deliberately, so a single
`inspect.signature`-based check works identically across all five
contract suites, and so the interfaces stay usable by a future
non-collocated `Field` per `field.py`'s own storage-independence
promise. The consequence: since `Field` itself carries no storage
(`field.py`), a concrete implementation that actually needs numeric
values -- every test-only implementation in
`tests/unit/numerics/test_*_contract.py` does -- narrows with `assert
isinstance(field, CollocatedField)` before touching `.values`/
`.component_shape`. This is the same shape of narrowing `Field.copy`'s
`Self` return type exists to avoid needing elsewhere, applied here
because an operator's *input* can't use that trick the way a
constructor's return type can.

**`AdvectionScheme.flux`/`DiffusionScheme.flux` return a
`(mesh.num_faces,)` tensor; `GradientScheme.gradient` returns
`(mesh.num_cells, 2)`; `DivergenceScheme.divergence` returns
`(mesh.num_cells,)`; `SourceTerm.source` returns `(mesh.num_cells,
*field.component_shape)`.** Not stated anywhere in `engine.md`/`icds.md`
beyond Advection/Diffusion's own "flux at each face" contract sentences
-- a genuine design decision made during implementation, not transcribed
from a document: Advection/Diffusion are naturally face-valued
(`engine.md`'s Flux layer is explicitly face-based), while
Gradient/Divergence/Source are naturally cell-valued, matching how a
real FVM accumulates face fluxes back onto a cell via the discrete
Gauss theorem. `_SPATIAL_DIMENSIONS = 2` (duplicated as a named constant
in `advection.py`, `gradient.py`, and `divergence.py` -- the last two
since TASK-027's own concrete schemes -- rather than read off `Mesh`,
which exposes no dimensionality accessor) records that this project is
2D-only for now, matching every other `Mesh`/`CoordinateSystem` method
-- revisit both when Stage 11 (Three Dimensions) arrives.

**`AdvectionScheme._check_velocity`** is a concrete helper every
implementation must call itself, the same `_check_cell`/`_check_face`
pattern `Mesh` establishes -- raises `IncompatibleVelocityFieldError`
(a `ValueError`) if the velocity field's `component_shape` isn't
`(2,)`. The contract suite is what actually holds implementations to
calling it, not the base class.

**Contract suites, one per interface** (`tests/unit/numerics/
test_advection_contract.py`, `test_diffusion_contract.py`,
`test_gradient_contract.py`, `test_divergence_contract.py`,
`test_source_contract.py`), each with two test-only implementations for
the parametrised suite (one trivial, one that varies with its input)
plus a third, deliberately inert implementation -- not part of the
parametrised fixture -- whose "varies with input" check is asserted to
raise `AssertionError`, per Stage 3 Completion Criterion 2's "checked by
a deliberately-inert third implementation asserted to fail" requirement.
Discharges Stage 3 Completion Criteria 1 (five interfaces, no `src/`
implementations) and 2 (contract suite, two implementations, teeth
proven) for these five; criterion 5's `numerics.advection`/
`numerics.diffusion` config fields were added in the same task
(`src/pyflow/configuration/CLAUDE.md`'s `NumericsConfig` entry).

**`FirstOrderUpwindAdvection`** (TASK-023, done 2026-08-27, Stage 4's
second task) is `advection.py`'s first real concrete scheme, and the
first real implementation of any of the six `adr/ADR-003` components
anywhere in the project. Constructed with `boundary_conditions:
Mapping[str, BoundaryCondition]` (TASK-040's own Design decision), it
picks the upstream cell's own value at every face -- the actual value,
never a blend, which is exactly what "unconditionally bounded" means
concretely (`docs/handbook/numerical-methods/advection.md`). The
face-normal velocity that decides which side is upstream is the average
of owner and neighbour velocities for an interior face (exact on
PyFlow's uniform MVP mesh, where both are equidistant from the shared
face) or the owner's own velocity alone for a boundary face, dotted with
`Mesh.face_normal`'s own canonical direction; `velocity_normal >= 0`
means the owner is upstream (flow moving along the canonical direction,
owner toward neighbour or outward at a boundary), matching how
`accumulate_flux_to_cells`'s own sign convention reads that same
direction (`simulation.py`'s `CLAUDE.md` entry, above).

**At a boundary face with inflow, the exterior value comes from this
scheme's own `boundary_conditions`, keyed by
`StructuredCartesianMesh.boundary_face_name` (TASK-023's own Design
decision, `docs/planning/roadmap.md`).** A Dirichlet (`kind == "value"`)
condition's prescribed value is used directly; a Neumann (`kind ==
"gradient"`) condition is *not* read numerically for this scheme's own
advective term -- its face value is the owner's own, zero-order
extrapolation, per `docs/handbook/numerical-methods/
boundary-conditions.md`'s "typically extrapolated from the adjacent
cell-centred value". Inflow at a boundary whose named edge has no
`BoundaryCondition` at all (the periodic case -- `boundary_condition.py`
resolves no object for it) raises `UnconfiguredBoundaryFaceError` rather
than silently extrapolating, which would be a plausible-looking wrong
answer for a periodic boundary specifically (it needs the wrapped
neighbour's actual value, not an extrapolation). Outflow at the same
face never raises it or reads the boundary condition at all -- the
upstream value is simply the owner's.

`FirstOrderUpwindAdvection` joins `test_advection_contract.py`'s
existing parametrised suite (Stage 4 Completion Criterion 3) with no
edit to any existing test body there; its own physical-correctness
claims (boundedness, the CFL-limit stable/unstable pair, conservation on
a closed domain) are `tests/features/first_order_upwind_advection.feature`,
bound by `tests/unit/test_first_order_upwind_advection.py` -- not a
golden demo, the same "lives in `tests/unit/`, not `tests/golden/`"
shape `simulation_orchestrator.feature`/`test_simulation.py` (TASK-040)
already established.

**`CentralDifferenceDiffusion`** (TASK-024, done 2026-08-27, Stage 4's
third task) is `diffusion.py`'s first real concrete scheme, the second
of the six `adr/ADR-003` components to go real. Constructed with
`boundary_conditions: Mapping[str, BoundaryCondition]` (the same
TASK-040 pattern advection uses) *and* `diffusion_coefficient: float`
(Gamma -- `NumericsConfig.diffusion_coefficient`, TASK-024's own Design
decision: a real config field, not a hardcoded constant, since it's a
physical property of what's transported, not a discretisation choice).
At every interior face, the flux is Gamma times the difference between
the two neighbouring cells' own values, divided by
`Mesh.face_centroid_distance` -- the central-difference formula exactly
(`docs/handbook/numerical-methods/diffusion.md`), un-negated, matching
`simulation.py`'s own `diffusion_flux - advection_flux` sign convention
(above).

**At a boundary face, the formula splits by the condition's own `kind`
-- a real difference from advection's Neumann handling, not just a
mirror of it.** A Dirichlet (`kind == "value"`) condition gives the
ordinary central difference between the prescribed value and the
owner's own, over the owner-to-face distance. A Neumann (`kind ==
"gradient"`) condition's numeric value **is read directly** (`Gamma *
condition.evaluate(...)`) -- unlike `FirstOrderUpwindAdvection`, whose
own Neumann case never reads the gradient number at all (zero-order
extrapolation only). The difference is what each interface's own Neumann
shape actually means physically: advection's boundary value is
extrapolated because advection has no natural use for a prescribed
*gradient*, while diffusion's whole boundary contribution at a Neumann
face *is* the prescribed gradient. No condition configured (the periodic
case) raises `UnconfiguredBoundaryFaceError` -- `diffusion.py`'s own
class, not shared with `advection.py`'s identically-named one (each
numerics interface module owns its own exception vocabulary). Unlike
advection, there is no inflow/outflow carve-out: diffusion has no flow
direction, so every boundary face needs a configured condition
unconditionally.

`CentralDifferenceDiffusion` joins `test_diffusion_contract.py`'s
existing parametrised suite (Stage 4 Completion Criterion 3) with no
edit to any existing test body there; its own physical-correctness
claims (the interior and boundary flux formulas, second-order accuracy
under mesh refinement, conservation under zero-flux boundaries) are
`tests/features/central_difference_diffusion.feature`, bound by
`tests/unit/test_central_difference_diffusion.py`. **Its own convergence-
order scenario measures the discrete Laplacian
(`accumulate_flux_to_cells(mesh, diffusion.flux(field))`) against a
known exact one, over *strictly interior* cells only** -- a cell whose
own faces are all interior faces, so its Laplacian estimate depends only
on the (second-order) interior formula, never the boundary formula
above, whose own local truncation error is first-order by direct Taylor
expansion (a one-sided difference against an exact prescribed value) and
carries no second-order claim anywhere in the handbook. Verified
directly, not assumed: deliberately mutating the boundary formula alone
left the convergence scenario passing, confirming the measurement is
genuinely isolated (`docs/planning/roadmap.md` TASK-024's own Design
Decision Four).

**`boundary_condition.py`** (TASK-019, done 2026-08-23) is
`BoundaryCondition` -- two abstract members, not one: `evaluate(field,
face) -> float` and a `kind: Literal["value", "gradient"]` property
telling the caller which shape the number is (Dirichlet vs Neumann).
One abstract method per shape was considered and rejected: every
implementation only ever has one shape, so a second method everyone
must still fill in (raising for the shape they don't have) says the
same thing more awkwardly than a property read once. `icds.md`'s third
shape (periodic, "a wrapped-neighbour reference") fits neither `value`
nor `gradient` and is deliberately not modelled -- this task's own scope
is "the Dirichlet/Neumann shapes without being them", and building an
interface for periodic ahead of a concrete implementation to check it
against is exactly the speculation P-016 refuses. `_check_boundary_face`
follows the same "base class provides the helper, subclass must call
it, contract suite holds them to it" pattern as `Mesh._check_cell` and
`AdvectionScheme._check_velocity` -- raises `NotABoundaryFaceError` (a
`ValueError`) for a face the mesh doesn't classify as boundary.
Contract suite: `tests/unit/numerics/test_boundary_condition_contract.py`,
two test-only implementations (one per shape), plus
`DirichletBoundaryCondition` itself (TASK-028) as a real third factory.
Discharges Criteria 1 and 2 for Boundary Condition; the
whole-configuration validation (Criterion 7) lives in
`src/pyflow/configuration/schema.py`, not here -- see that package's own
`CLAUDE.md`.

**`DirichletBoundaryCondition`** (TASK-028, done 2026-08-28, Stage 4's
seventh task) is `boundary_condition.py`'s first real concrete
implementation, sharing the module with the interface the same way
every other Stage 4 concrete scheme does. `evaluate` ignores `field`
entirely and returns its own stored value regardless -- a Dirichlet
condition's prescribed value never depends on interior state, the same
shape `test_boundary_condition_contract.py`'s own `_FixedValueCondition`
test double already established. No interface change (unlike Time
Integration's/Pressure-Velocity Coupling's own widenings), so no new
ADR.

**A genuine config-surface gap, found and closed in the same task, not
left implicit.** `BoundaryFaceConfig` (`src/pyflow/configuration/
schema.py`) had `velocity`/`pressure` fields only, both reserved for the
momentum/pressure system (`icds.md`'s Compatibility requirements) -- the
`_NullValueBoundaryCondition` reference this task retires returned
`face_config.velocity` regardless of which field asked, which would have
handed a velocity-shaped number to a real advected scalar's own boundary
the first time TASK-030's Passive Scalar Transport demo exercised it, a
plausible-looking wrong answer rather than a crash. Verified this was
live before drafting the fix, not assumed. **Resolved: `BoundaryFaceConfig.
scalar_value: float = 0.0`**, a plain `float` (not `float | None` like
`velocity`/`pressure`, since it carries neither field's mutual-exclusivity
or net-flux relation), defaulting to `0.0` for the same reason `velocity`
does -- every existing default `NumericsConfig` stays valid.
`assembly.py`'s own `_dirichlet_boundary_condition(face_config)` adapter
reads only this field. Full reasoning, including why a `DirichletBoundary
Condition` and PISO's own `GreenGaussDivergence` reading the same
resolved condition for two different fields at one wall stays
deliberately out of scope: `docs/planning/roadmap.md` TASK-028's own
Design decision.

Its own physical-correctness claim -- a real interior scheme
(`FirstOrderUpwindAdvection`, `CentralDifferenceDiffusion`), not a
hand-written double, computes the right thing when wired with the real
condition, per this task's own Intent -- is `tests/features/
dirichlet_boundary.feature`, bound by `tests/unit/test_dirichlet_boundary.py`.

**`time_integrator.py`** (TASK-020, done 2026-08-23) is `TimeIntegrator`
-- one abstract method, `advance(fields: Mapping[str, Field], derivative:
Callable[[Mapping[str, Field]], Mapping[str, torch.Tensor]], dt: float)
-> dict[str, Field]`. Takes a *mapping* of fields, not a single `Field`,
per `engine.md`'s "independent of which fields exist or how many" and
`docs/planning/roadmap.md` TASK-020's design decisions -- a single-field
interface would force a caller to loop and would push Stage 5's coupled
velocity/pressure advance outside the interface entirely. No
`_check_...` helper here, unlike Advection/BoundaryCondition: nothing
about `advance`'s arguments is meaningless the way a velocity field's
wrong arity or a non-boundary face is -- a mismatched key between
`fields` and what `derivative` returns is a plain `KeyError` from a
concrete implementation reading the mapping, not a condition this
interface itself needs to name and reject.

**`derivative` is a re-evaluatable callable, not a precomputed
`Mapping[str, torch.Tensor]` (widened 2026-08-27, TASK-025, `adr/
ADR-008-time-integrator-derivative-callable.md`).** TASK-020's original
signature offered a single derivative snapshot -- everything an
Euler-shaped scheme needs, but not enough for RK4 (below), which
evaluates the derivative three more times at intermediate states within
the step that a fixed value cannot supply. Found before any TASK-025
implementation code was written, not during it -- `simulation.py`'s own
entry, below, records the calling-side half of this same change. Still
the same "consumes a derivative, not a scheme" split `icds.md` states as
the reason the integrator is independent of which advection/diffusion/
pressure-coupling strategy is configured, by construction -- a function
of state reveals no more about which scheme produced it than a fixed
value did.

`RK4Integrator` (TASK-025, done 2026-08-27, Stage 4's fourth task) is
`time_integrator.py`'s first real concrete scheme, sharing the module
with the interface the same way `FirstOrderUpwindAdvection`/
`CentralDifferenceDiffusion` share theirs. Classical fourth-order
Runge-Kutta: `k1 = derivative(fields)`, then three more evaluations at
successively refined intermediate states (`fields + dt/2*k1`, `fields +
dt/2*k2`, `fields + dt*k3`), combined as `fields + dt/6*(k1 + 2*k2 +
2*k3 + k4)`. `_advanced_by(fields, deltas)`, a small module-level
helper, builds each intermediate stage and the final combination alike
-- the same `.copy()`-then-`.values[:] =` shape `_EulerIntegrator`
already used, reused four times rather than duplicated. No rejection
path of its own, the same reasoning as Euler/DoubleStep below. **Its own
two acceptance-criteria scenarios were verified to have teeth by
deliberate mutation, not merely written and trusted**
(`docs/planning/roadmap.md` TASK-025's own Design decisions): a
weakened "at least one recorded state differs" check was found, via a
stale-intermediate-state mutation, to pass even when three of the four
evaluations reused the same state -- tightened to require every pair of
the four recorded states pairwise distinct, re-verified against the same
mutation (now correctly fails), and against a second mutation (correct
evaluations, wrong final combination weights) that fails the accuracy
scenario alone, confirming each scenario catches the specific defect it
claims to.

Contract suite: `tests/unit/numerics/test_time_integrator_contract.py`,
two test-only implementations with genuinely different arithmetic
(`_EulerIntegrator`, `_DoubleStepIntegrator`) plus, since TASK-025,
`RK4Integrator` itself as a real third factory -- no separate,
deliberately inert implementation this time. Unlike the five TASK-018
suites, this one's own acceptance criteria already supply that check's
two halves directly: "a zero derivative advances the state by nothing"
is the boundary case an inert (ignores-its-input) implementation would
also pass, and "the same derivative values give the same result
regardless of source" is run with a genuinely nonzero derivative, which
that same inert implementation would fail -- adding a third class would
only restate what these two tests already prove. Discharges Criterion 1
and 2 for Time Integrator (TASK-020) and Criterion 2's real-scheme share
(TASK-025); Criterion 5's `numerics.time_integration`/`numerics.timestep`
config fields were added in TASK-020
(`src/pyflow/configuration/CLAUDE.md`'s `NumericsConfig` entry).

**`linear_solver.py`** (TASK-022, done 2026-08-23) is `LinearSolver` --
one abstract method, `solve(matrix: torch.Tensor, rhs: torch.Tensor) ->
LinearSolverResult`, plus `LinearSolverResult` itself (a frozen
dataclass: `solution`, `converged`, `iterations`). Built before
TASK-021 despite the number, per the Stage 3 discharge map: Criterion 6
makes Pressure-Velocity Coupling structurally dependent on this type, so
it has to exist first.

**No dedicated "system" type, unlike `LinearSolverResult`.** This task's
own Artifacts Produced bullet names only one new type ("the ABC, and the
result type") -- `matrix`/`rhs` stay the two plain tensors the contract
actually needs, read literally off `engine.md`'s own Contract sentence
("given a linear system, produces its solution"): the system *is* the
pair, not a wrapper around it. `matrix` is a dense `(n, n)` tensor, not
sparse or matrix-free -- an explicit choice, not a gap: nothing in
`icds.md`/the handbook mandates a code-level representation, MVP meshes
are small enough that a dense matrix is a real option, and nothing under
`src/` depends on this choice yet (Criterion 1), so it stays reversible
until TASK-026's concrete Conjugate Gradient implementation needs to
revisit it (per the handbook's own "large, sparse" framing of the real
pressure-correction system). **Closed 2026-08-27, TASK-026: did not need
to.** `ConjugateGradientSolver` (below) uses the dense tensor as-is --
MVP mesh sizes stayed small enough that this remained a non-issue, per
the note's own stated condition; revisit if a later stage's mesh sizes
make the dense representation impractical.

**`solve` takes only `matrix`/`rhs`, no `tolerance`/`max_iterations`
parameters** -- those are `numerics.linear_solver_tolerance`/
`numerics.linear_solver_max_iterations` (below), and a concrete solver's
own tunables, bound at its construction rather than passed per call.
`engine.md`'s Contract sentence names exactly two inputs; this task does
not have to decide how tolerance/iterations *reach* a solver instance,
only that they exist as configuration and are validated -- TASK-021's
`_NullLinearSolver` (`engine/numerics/assembly.py`) ignores both
entirely, since it computes nothing; a real solver (TASK-026) is what
will actually read them, however it ends up doing so.

Contract suite: `tests/unit/numerics/test_linear_solver_contract.py`,
two test-only implementations with genuinely different strategies
(`_ExactSolver`, a direct `torch.linalg.solve`; `_JacobiSolver`, a
diagonal iterative scheme tunable via constructor
`tolerance`/`max_iterations` to fail to converge on demand -- an exact
solve can't, by definition, so proving the non-convergence criteria
needs a second, iterative-shaped implementation). No third inert class,
same reasoning as `TimeIntegrator`: "returns the known solution" and
"reports non-convergence" together already prove both the varies-with-
input and boundary-case halves. Discharges Criterion 1 and 2 for Linear
Solver, and the first half of Criterion 6 (the type TASK-021's interface
will require exists); Criterion 5's `numerics.linear_solver`/
`numerics.linear_solver_tolerance`/`numerics.linear_solver_max_iterations`
config fields were added in the same task
(`src/pyflow/configuration/CLAUDE.md`'s `NumericsConfig` entry).

**`ConjugateGradientSolver`** (TASK-026, done 2026-08-27, Stage 4's fifth
task) is `linear_solver.py`'s first real concrete scheme, sharing the
module with the interface the same way `FirstOrderUpwindAdvection`/
`CentralDifferenceDiffusion`/`RK4Integrator` share theirs. Standard CG
from `x0 = 0`, with one addition: null-space handling is *gated*, not
unconditional. `matrix @ ones` close to zero relative to `matrix`'s own
norm signals the constant vector is in the null space (the lid-driven
cavity's own pressure system, `icds.md`'s Linear Solver ICD); when true,
the constant mode is projected out of the residual after every update.
**Verified before being written, not assumed:** a throwaway numerical
prototype confirmed unconditional projection reports `converged=True`
after one iteration with a wrong answer on a generic well-conditioned
system -- exactly the "plausible-looking wrong answer" failure mode
`docs/practices.md` names repeatedly -- which is why the gate exists at
all. A degenerate-direction guard (curvature below a tiny epsilon stops
the loop) is marked `# pragma: no cover` with a comment explaining why
this repository's own fixtures cannot realistically reach it -- the same
directive `src/pyflow/bootstrap.py` already uses for a structurally
unreachable branch.

**An honest finding from mutation testing, recorded rather than
smoothed over: the projection's own necessity could not be demonstrated
at any fixture size this repository can realistically test** (up to 225
cells / ~72 CG iterations) -- disabling it entirely left both of this
task's own acceptance scenarios passing unchanged, because `x0 = 0` with
a consistent `rhs` already keeps every CG iterate in `range(matrix)` in
exact arithmetic, and the roundoff drift the projection defends against
turned out to be around machine epsilon at MVP mesh scale. The *gate*
itself is what mutation testing actually proved matters (caught
immediately by the existing generic contract-suite systems when
projection was applied unconditionally). The projection code stays --
cheap, matches the handbook's explicit recommendation, and is expected
to matter once a later stage's mesh sizes and iteration counts grow --
but `docs/planning/roadmap.md` TASK-026's own Design decisions record
this precisely rather than presenting an unverified claim as verified.

No rejection path of its own, the same reasoning as every other concrete
`TimeIntegrator`/`LinearSolver` in this repository.

`ConjugateGradientSolver` joins `test_linear_solver_contract.py`'s
existing parametrised suite (Stage 4 Completion Criterion 3) with no
edit to any existing test body there -- unlike TASK-025's own join, since
this interface's `solve` signature needed no change. `register_linear_
solver`'s factory type widened from zero-arg to `Callable[[float, int],
LinearSolver]` (mirrors `register_diffusion_scheme`'s own
`diffusion_coefficient` widening, reusing `assembly.py`'s existing
`_resolve_with_two_arguments` helper rather than adding a new one). Its
own physical-correctness claims (convergence on the positive-semi-definite
system, non-convergence distinguishability) are `tests/features/
conjugate_gradient_solver.feature`, bound by `tests/unit/
test_conjugate_gradient_solver.py` -- its semi-definite fixture is built
from the real `CentralDifferenceDiffusion`/`accumulate_flux_to_cells`
on a zero-gradient-everywhere mesh, not a hand-typed matrix, verified
directly (symmetric, one ~0 eigenvalue, the rest strictly positive)
before being written into a test.

**`pressure_coupling.py`** (TASK-021, done 2026-08-23, Stage 3's last
task) is `PressureCoupling` -- one abstract method, `correct`, plus a
real `__init__(self, linear_solver: LinearSolver)` that raises
`TypeError` if `linear_solver` isn't a genuine `LinearSolver` instance.
This is Stage 3 Completion Criterion 6's second half made structural:
`icds.md` names Pressure-Velocity Coupling's dependency on a configured
Linear Solver as "the one real cross-layer dependency among the six",
and a runtime `isinstance` check is what makes "cannot be built without
one" a real guarantee rather than something only `mypy` enforces (a type
hint alone is not a runtime guarantee -- a caller can still pass
`None`). No dedicated result type, same reasoning as `LinearSolver`: this
task's own Artifacts Produced bullet names only the ABC, so `correct`
returns a plain `tuple[VectorField, ScalarField]`.

**`correct` gained a second parameter, `dt: float` (TASK-027,
`adr/ADR-009-pressure-coupling-dt.md`)** -- `PISO` (below) is the first
concrete strategy to need it; see that ADR for why `dt` and not a
constructor-bound value, and why not density too.

Contract suite: `tests/unit/numerics/test_pressure_coupling_contract.py`,
two test-only strategies (`_PassthroughCoupling`, unchanged velocity and
zero pressure; `_ScaledCoupling`, halved velocity and a nonzero constant
pressure), each constructed with a local test-only `LinearSolver`, plus
`PISO` itself (TASK-027) as a real third factory, constructed with a
local test-only `BoundaryCondition` too since `correct`'s own widened
constructor needs one. No third *inert* class: this task's own
Acceptance Criteria name no "varies with input" case, unlike
`TimeIntegrator`/`LinearSolver`, whose own criteria explicitly needed
one. Discharges Criterion 1 and 2 for Pressure-Velocity Coupling, and
the second half of Criterion 6 (the construct-without-a-solver rejection
test).

**`PISO`** (TASK-027, done 2026-08-27, Stage 4's sixth task) is
`pressure_coupling.py`'s first real concrete scheme, sharing the module
with the interface the same way `FirstOrderUpwindAdvection`/
`CentralDifferenceDiffusion`/`RK4Integrator`/`ConjugateGradientSolver`
share theirs. A single `dt`-scaled correction pass: solves
`Laplacian(p) = div(u*) / dt` for the pressure correction (matrix built
via `CentralDifferenceDiffusion`, gamma=1, an internally-constructed
zero-gradient `BoundaryCondition` on every wall -- the impermeable-wall
assumption, not read from config since pressure has no boundary
representation in `NumericsConfig`), then returns `u* - dt *
grad(pressure)`. `GreenGaussDivergence`/`GreenGaussGradient` (below)
compute `div(u*)` and the returned correction's own gradient
respectively -- real, necessary, exercised uses, not decorative.

**Registered under `"piso"`, but not the full multi-pass Issa
algorithm -- an honestly-scoped limitation, found and resolved before
any implementation code was written, not discovered afterward.**
Composing this task's own `GreenGaussGradient`/`GreenGaussDivergence`
into a Poisson matrix (the mathematically obvious way to build one)
produces a matrix that is provably not symmetric -- proven algebraically
via the discrete integration-by-parts identity, confirmed numerically --
so `ConjugateGradientSolver` cannot even be asked to solve it. Genuinely
suppressing pressure-velocity decoupling under *repeated* correction on
PyFlow's collocated mesh needs Rhie-Chow interpolation, which needs
momentum-equation coefficients `correct`'s own interface has no way to
obtain; three correction strategies (naive Green-Gauss, a compact
face-derivative reconstruction, multi-pass Rhie-Chow) were tried and
measured against a real mesh before settling on the single-pass,
compact-Laplacian design actually shipped -- full numerical record:
`docs/planning/roadmap.md` TASK-027's own Design decision Two. The
stronger, fully-converged claim is Stage 5 TASK-033's own (Pressure
Correction Loop), which has real momentum-coupled state to iterate
against; `docs/practices.md`'s "A criterion whose strong reading depends
on a later task must say so when drafted" is the standing rule this
finding produced, so the next task drafted with this shape states its
own boundary the first time.

Raises `PressureSolveDidNotConvergeError` (its own class, this module)
if the pressure solve does not converge, rather than returning an
unconverged solve's velocity correction as if it were trustworthy -- the
same "convergence is reported, not assumed" discipline
`ConjugateGradientSolver`'s own `LinearSolverResult.converged` already
established, extended to a caller that consumes it.

`PISO` joins `test_pressure_coupling_contract.py`'s existing
parametrised suite (Stage 4 Completion Criterion 3) with no edit to any
existing test body there -- unlike TASK-025's own join, since this
interface's `correct` signature change was already paid for by
`adr/ADR-009` before the join, not caused by it.
`register_pressure_coupling`'s factory type widened from `Callable[
[LinearSolver], PressureCoupling]` to `Callable[[LinearSolver,
Mapping[str, BoundaryCondition]], PressureCoupling]` (mirrors
`register_diffusion_scheme`'s own `diffusion_coefficient` widening,
reusing `assembly.py`'s existing `_resolve_with_two_arguments` helper).
Its own physical-correctness claim (a single pass measurably and
boundedly reduces divergence; non-convergence is reported, not returned
as a plausible answer) is `tests/features/piso_pressure_coupling.feature`,
bound by `tests/unit/test_piso_pressure_coupling.py`.

**`gradient.py`/`divergence.py`** (TASK-018, Stage 3, interface-only
until TASK-027) hold `GradientScheme`/`DivergenceScheme` -- two of the
three operators (with `source.py`) that jointly compute the Flux layer
but get no `NumericsConfig` field of their own (`docs/planning/
roadmap.md` TASK-018's design decision: nothing has identified a second
implementation of either a user would choose between). **Both stopped
being interface-only in TASK-027 (Stage 4, 2026-08-27)**:
`GreenGaussGradient`/`GreenGaussDivergence` are the first real concrete
schemes, built and owned by `PISO` directly rather than resolved through
`assemble_numerics` -- there is no registry for either, and building one
now would be P-016 speculation, since nothing has anticipated a second
Gradient or Divergence implementation. Both apply the discrete Gauss
theorem to a field's own face values (`GreenGaussGradient`, componentwise
via `accumulate_flux_to_cells`) or face-normal component
(`GreenGaussDivergence`, reusing `accumulate_flux_to_cells` directly,
`simulation.py`'s own TASK-040 helper) -- exact for a linear field on
PyFlow's uniform orthogonal MVP mesh, verified directly before being
written. Both are boundary-condition-aware by construction, the same
pattern `CentralDifferenceDiffusion`/`FirstOrderUpwindAdvection`
establish, and both raise their own `UnconfiguredBoundaryFaceError` for
the periodic case (mirroring `advection.py`'s/`diffusion.py`'s
identically-named exceptions -- each numerics interface owns its own
exception vocabulary); `GreenGaussDivergence` additionally raises
`IncompatibleVectorFieldError` for a field whose `component_shape`
doesn't match the mesh's spatial dimensionality (`advection.py`'s
`IncompatibleVelocityFieldError`, generalised since `divergence` is not
velocity-specific). Each joins its own contract suite
(`test_gradient_contract.py`/`test_divergence_contract.py`) as a real
third fixture, with dedicated tests for its own exact-for-a-linear-field
claim and both rejection paths, since neither test-only fixture already
in either suite has this logic to exercise generically.

**A real circular import found while wiring this in, not predicted in
advance**: `pressure_coupling.py`/`gradient.py`/`divergence.py` all need
`accumulate_flux_to_cells` from `simulation.py`, but `simulation.py`
imports `AssembledNumerics` from `assembly.py`, which imports
`PressureCoupling`/`PISO` from `pressure_coupling.py` -- a genuine cycle,
the same shape `bootstrap.py`'s own placement hit in Stage 0 (`src/pyflow/
CLAUDE.md`). Fixed the same way: `simulation.py`'s own `AssembledNumerics`
import moved behind `if TYPE_CHECKING:`, since it is only ever used as a
type annotation there and `from __future__ import annotations` already
makes that lazy -- costs nothing at runtime, and `accumulate_flux_to_cells`
itself did not need to move.

**`assembly.py`** (TASK-021) is `assemble_numerics(NumericsConfig) ->
AssembledNumerics` and the six independent registries
(`register_advection_scheme` and five siblings) it resolves a configured
name through -- Stage 3 Completion Criterion 3's mechanism: adding a
name means calling a `register_*` function, never editing
`assemble_numerics`'s own body, which the
`tests/unit/numerics/test_assembly.py` suite checks directly by
registering a name no `src/` module knows and getting it back.
`AssembledNumerics` carries the six live instances plus `names`, a flat
`Mapping[str, str]` echo of the configured name each was resolved from
-- what `bootstrap()` reports as "the assembled set" (Criterion 8),
since comparing name strings against a YAML file is direct where
comparing live objects would not be.

**Registers one trivial, non-physical reference implementation per
component under `src/`, despite Criterion 1 saying no concrete scheme
ships there this stage -- an explicit, maintainer-decided exception
(2026-08-23), not an oversight.** A real `pyflow run` subprocess
(Criterion 8's golden demo) imports only `src/pyflow`, so without
*something* registered under the exact MVP names `NumericsConfig`'s
defaults already validate, assembly would raise for every real run.
Every `_Null*` class computes nothing (zero flux, an unconverged no-op
solve, a pass-through velocity correction) and is named and documented
as a reference, never as a first real implementation -- see the
module's own docstring for the full reasoning, and `docs/planning/
roadmap.md`'s Stage 3 Completion Criterion 1 for where the exception is
recorded against the criterion it narrows.
`_NullLinearSolver` reports `converged=False`, deliberately: it solves
nothing, and `linear_solver.py`'s whole contract is that a solver must
not report an answer it did not reach.

**`_NullAdvectionScheme` is retired (TASK-023, 2026-08-27) -- the first
of the six to go.** `register_advection_scheme("first_order_upwind",
...)` now names `FirstOrderUpwindAdvection`
(`src/pyflow/engine/numerics/advection.py`), a real scheme; the class it
used to name is deleted from this module, not left unregistered
alongside it. **`_NullDiffusionScheme` followed the same day (TASK-024)
-- the second.** `register_diffusion_scheme("central_difference", ...)`
now names `CentralDifferenceDiffusion`
(`src/pyflow/engine/numerics/diffusion.py`); same deletion, not
unregistration. **`_NullTimeIntegrator` followed the next day
(TASK-025) -- the third.** `register_time_integrator("rk4", ...)` now
names `RK4Integrator` (`src/pyflow/engine/numerics/time_integrator.py`);
same deletion, not unregistration. **`_NullLinearSolver` followed the
next day (TASK-026) -- the fourth.** `register_linear_solver(
"conjugate_gradient", ...)` now names `ConjugateGradientSolver`
(`src/pyflow/engine/numerics/linear_solver.py`); same deletion, not
unregistration. **`_NullPressureCoupling` followed the next day
(TASK-027) -- the fifth.** `register_pressure_coupling("piso", ...)`
now names `PISO` (`src/pyflow/engine/numerics/pressure_coupling.py`);
same deletion, not unregistration. **`_NullValueBoundaryCondition`
followed the next day (TASK-028) -- the sixth.**
`register_boundary_condition_type("dirichlet", ...)` now names
`_dirichlet_boundary_condition` (`assembly.py`'s own small adapter,
constructing a real `DirichletBoundaryCondition` from a
`BoundaryFaceConfig`'s new `scalar_value` field --
`src/pyflow/engine/numerics/boundary_condition.py`); same deletion, not
unregistration. One `_Null*` reference implementation remains
(`_NullGradientBoundaryCondition`), for Boundary Condition's own Neumann
half, Stage 4's last component not yet reached (TASK-029).

**Registration refuses to overwrite a different factory**
(`DuplicateSchemeError`, added 2026-08-24). The registries are
module-level and filled by import side effect, so "last import wins"
would be silent and order-dependent. Stage 4's specific hazard is a real
scheme registered under an MVP name while that name's reference
registration is still present -- the run would report
`first_order_upwind` and compute zero flux, and since
`AssembledNumerics.names` echoes the configured name, no name-based
check could tell. The task landing a real scheme therefore deletes that
name's reference registration in the same change (`first_order_upwind`
is the worked example, immediately above); the guard makes forgetting an
import-time error. Re-registering the *identical* factory stays a
no-op, so a module imported twice does not raise.

`periodic` boundary faces resolve no `BoundaryCondition` instance --
`boundary_condition.py`'s own scope (TASK-019) covers only the
Dirichlet/Neumann shapes, so `assemble_numerics` reports a periodic
face's configured type in `.names` but omits it from
`.boundary_conditions` entirely, rather than fabricating an object the
interface has no shape for.

**`assemble_numerics` now resolves `boundary_conditions` before
advection/diffusion, and `register_advection_scheme`/
`register_diffusion_scheme`'s factory type gained a `boundary_conditions`
parameter (TASK-040, done 2026-08-27).** Stage 4's own Design decision
(`docs/planning/roadmap.md` TASK-040): a concrete advection/diffusion
scheme is constructed *with* the boundary conditions it needs, the same
pattern `PressureCoupling.__init__(linear_solver)` already established,
rather than the orchestrator substituting a boundary value into a
scheme's output after the fact (rejected -- boundary treatment is
genuinely scheme-specific, and an orchestrator that "corrected" it would
have to know each scheme's own interpolation logic, leaking exactly the
knowledge `adr/ADR-003` exists to keep generic). `_NullAdvectionScheme`/
`_NullDiffusionScheme` now take (and ignore) this parameter at
construction, matching the new registered shape.
`test_advection_and_diffusion_factories_receive_the_resolved_boundary_conditions`
(`tests/unit/numerics/test_assembly.py`) is the test that actually
proves the mapping reaches a factory intact -- every other test-only
scheme in that module discards its `boundary_conditions` argument, so
none of them would have failed had `assemble_numerics` silently passed
an empty or stale mapping instead (found during TASK-040's own review
cycle).

**The resolved `boundary_conditions` mapping is a `MappingProxyType`,
not a plain `dict` (TASK-040's own review cycle).** It is handed to two
different factories (advection, diffusion) and then retained on the
returned, `frozen` `AssembledNumerics` -- three holders of one mutable
object with no defensive copy, before this fix. `frozen` stops a caller
reassigning `AssembledNumerics`'s own *fields*; it does nothing to stop
a scheme mutating the mapping one of those fields refers to.
`test_boundary_conditions_is_immutable` pins this down directly.
Advection/diffusion/pressure_coupling's near-identical
get-factory/raise-if-missing/call blocks were also generalised into one
shared `_resolve_with_argument` helper in the same pass, the same
relationship `_resolve` already had to `time_integration`/
`linear_solver`'s zero-argument factories. **Pressure-coupling's own
resolution moved from `_resolve_with_argument` to
`_resolve_with_two_arguments` in TASK-027**, once `register_pressure_
coupling`'s own factory widened to take `boundary_conditions` too (below)
-- this paragraph's own "advection/diffusion/pressure_coupling" grouping
describes TASK-040's state, not the current one; see TASK-027's own
paragraph below for what changed.

**`register_diffusion_scheme`'s factory type gained a second parameter,
`diffusion_coefficient: float` (TASK-024, done 2026-08-27).** Gamma
(`NumericsConfig.diffusion_coefficient`, TASK-024's own Design decision:
a real config field, not a hardcoded constant) is a physical property of
what's being transported, not a scheme choice, but `CentralDifference
Diffusion` still needs it at construction, the same "constructed with
it, not handed it after the fact" reasoning `boundary_conditions` already
established. Diffusion alone among the six components now needs two
constructor arguments (advection/pressure_coupling still only needed one
each, at the time -- pressure_coupling followed in TASK-027, below), so
a new `_resolve_with_two_arguments[T, A, B]` helper sits alongside
`_resolve_with_argument` rather than widening that one -- a shared
two-argument signature would have forced advection to pass an unused
second argument. `test_diffusion_factory_receives_the_resolved_boundary_
conditions_and_coefficient` (`tests/unit/numerics/test_assembly.py`) is
the test proving both arguments reach a factory intact, the diffusion
analogue of `test_advection_and_diffusion_factories_receive_the_
resolved_boundary_conditions` above.

**`register_pressure_coupling`'s factory type gained a second parameter,
`boundary_conditions: Mapping[str, BoundaryCondition]` (TASK-027, done
2026-08-27).** `PISO`'s own `GreenGaussDivergence` needs velocity's
boundary conditions at construction, the same "constructed with it, not
handed it after the fact" reasoning every other widening on this page
follows -- reuses `_resolve_with_two_arguments` directly (no new helper
needed, unlike diffusion's own join, since the generic two-argument
shape already fits). `test_pressure_coupling_factory_receives_the_
resolved_boundary_conditions` (`tests/unit/numerics/test_assembly.py`)
is the test proving the mapping reaches the factory intact, the
pressure-coupling analogue of diffusion's own capture test above.

**`simulation.py`** (TASK-040, done 2026-08-27, Stage 4's first task
despite its number -- built before TASK-023..030 because they depend on
it structurally, not the reverse) is `accumulate_flux_to_cells(mesh,
face_values) -> torch.Tensor` and `step(fields, velocity, numerics, dt)
-> dict[str, Field]` -- the per-timestep state-advance mechanism
`docs/architecture/engine.md`'s Flux entry describes ("jointly
compute[d]" by Advection/Diffusion/Gradient/Divergence) but assigns to
no module, and this package's own `CLAUDE.md` had called "the future
simulation run-loop... once physics exist" since before any physics
existed, without ever scheduling it. A concrete module, not a seventh
`adr/ADR-003` component (P-016) -- nothing has anticipated a second way
to do Gauss-theorem flux accumulation.

`accumulate_flux_to_cells` is the discrete Gauss theorem, generic over
any `(mesh.num_faces,)` array: `sum(value * area * outward_normal_sign)
/ volume` per cell, where a face's owner sees `+1` and its neighbour (if
any) sees `-1` -- `Mesh.face_normal`'s own canonical direction, owner
toward neighbour or outward for a boundary face. TASK-027 reuses this
directly for its own concrete `DivergenceScheme` rather than
reimplementing the same geometric arithmetic.

**Combining an advective and a diffusive face flux into one derivative
is a real design decision `step` had to make, not one `engine.md`/
`icds.md` pins down** -- `AdvectionScheme`/`DiffusionScheme`'s own
docstrings promise only "the ... contribution to that field's flux at
each face", no sign. Resolved directly from
`docs/handbook/numerical-methods/fvm.md`'s own conservation equation:
the advective face flux is *subtracted* from the rate of change, the
diffusive face flux *added*, so `step` accumulates `diffusion_flux -
advection_flux`, not their sum. Recorded in `simulation.py`'s own `step`
docstring and in `docs/planning/roadmap.md` TASK-040, rather than left
for whichever of TASK-023/024 happened to land first to improvise a
convention the other would then have to match.

`step` never branches on `Mesh.is_boundary_face` anywhere in its own or
`accumulate_flux_to_cells`'s code -- Stage 4 Completion Criterion 1's own
bullet, checked directly (`tests/unit/test_simulation.py`'s own
`inspect.getsource` assertion) rather than only exercised behaviourally.
This is what "the orchestrator does not know, and must not need to know,
which faces are boundary faces" means concretely: a concrete scheme
(constructed with its own boundary conditions, above) is what actually
special-cases a boundary face, not `step`.

**`step` builds `derivative` as a closure, not a precomputed dict
(2026-08-27, TASK-025, `adr/ADR-008-time-integrator-derivative-
callable.md`).** `numerics`, `velocity`, and `mesh` are captured once, at
the top of `step`; `derivative(state)` re-runs
`numerics.advection.flux`/`numerics.diffusion.flux`/
`accumulate_flux_to_cells` for whatever `state` mapping it's given, so a
multi-stage `TimeIntegrator` (`RK4Integrator`) can ask for the derivative
again at an intermediate state it constructs -- the calling-side half of
the interface widening `time_integrator.py`'s own entry, above, records.
`velocity` stays fixed across every evaluation within one `step` call:
`step` only ever advances `fields`, treating `velocity` as external input
(Stage 5's pressure coupling is what will eventually advance it), so
nothing about RK4's own sub-stages needed to change that. The
`MismatchedMeshError` check stays exactly where it was, run once against
the original `fields`/`velocity` before the closure is built -- an
intermediate state `RK4Integrator` builds is always derived from `fields`
via `.copy()`, so it shares the same mesh by construction and needs no
re-check.

**`MismatchedMeshError`** is raised when a field in `step`'s `fields`
mapping is not defined over the same mesh (by identity) as `velocity`.
`AssembledNumerics` carries no mesh of its own, so Stage 4 Completion
Criterion 5's phrasing ("a field whose mesh disagrees with the one the
numerics were assembled against") cannot be checked literally; this is
the buildable reading chosen instead, stated explicitly per root
`CLAUDE.md`'s Integrity section -- see TASK-040's own entry in
`docs/planning/roadmap.md` for the full reasoning.

**`simulation_orchestrator.feature` is not a golden demo** -- no config
file under `examples/golden-demos/`, no CLI subprocess run, since this
is the mechanism a future demo (TASK-030) is built on top of, not a demo
itself. `tests/unit/test_simulation.py` binds it directly, per
`tests/unit/CLAUDE.md`'s own scope, rather than living under
`tests/golden/`.
