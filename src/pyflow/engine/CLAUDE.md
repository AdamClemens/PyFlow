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
entirely. `tests/unit/test_field_contract.py` (TASK-014's deferred
contract suite, now real) types its parametrised fixture as
`type[CollocatedField[Any]]` specifically so one suite can call
`value_at`/`set_value_at` generically across every concrete
implementation without per-implementation casts.
`tests/unit/test_scalar_field.py` covers `ScalarField`'s own specific
claims (plain `float` return, exact formula, copy independence for its
own storage).

**`vector_field.py`** (TASK-016, done 2026-08-21) is `VectorField
(CollocatedField[tuple[float, ...]])`, added to
`test_field_contract.py`'s `_IMPLEMENTATIONS` rather than a second
suite, per TASK-014's own stated pattern. `num_components` (default 2,
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
