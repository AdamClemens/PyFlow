# Engine Architecture

Per `docs/planning/knowledge-architecture.md` KA-029. A conceptual map of
the CFD engine's replaceable layers, meant to orient a future developer
*before* they open individual implementation files.

This document describes target architecture, not current implementation.
As of Stage 0, `src/pyflow/engine/`, `src/pyflow/physics/` hold only
package initialisation (`docs/planning/roadmap.md` TASK-000) -- none of
the layers below exist as code yet. They arrive incrementally through
Stages 1-5; see each layer's "Arrives via" note below.

This is not the place for numerical theory -- what upwind advection *is*,
mathematically, belongs in `docs/handbook/numerical-methods/advection.md`
(currently an empty stub, per `docs/planning/backlog.md` E3). This
document is about the *shape* of the engine: what the layers are, why
each is independently replaceable, and how a simulation is assembled from
them. For the interfaces those layers actually expose to configuration,
see `docs/architecture/icds.md` (KA-030) -- that document, not this one,
is the contract's formal definition.

---

## The Core Principle

Per `docs/glossary.md` ("Interface Contract") and
`adr/ADR-003-modular-numerical-strategies.md`:

> Every implementation exposes the same interface. The timestepper
> doesn't care which one it has.

Concretely, this means four things hold for every layer below:

1. **Each layer has a contract** -- a stable interface describing inputs,
   outputs, behaviour and guarantees, independent of which concrete
   scheme implements it.
2. **Implementations are replaceable** -- a new scheme can be added by
   writing a new implementation of an existing contract, not by changing
   the contract or the code that depends on it.
3. **The timestepper depends on contracts, not concrete schemes** -- the
   orchestration code driving a simulation forward in time calls "the
   configured advection scheme," never "upwind advection" by name.
4. **Construction selects implementations; execution operates through
   contracts** -- which concrete scheme is used for a given run is
   decided once, when the simulation is assembled from configuration
   (`adr/ADR-003`, `src/pyflow/configuration/`), and is fixed for the
   rest of that run. The per-timestep code path never branches on which
   implementation was chosen.

This is what makes Capability Level 4's "compare numerical schemes by
changing configuration only" golden demo possible, and what every entry
in `docs/implementation/upgrade-paths.md` assumes when it describes a
layer's simpler MVP choice evolving into a more sophisticated one without
touching the other layers.

---

## The Nine Layers

The same nine layers appear in three places that must stay in agreement:
`docs/glossary.md` ("Layer"), `docs/implementation/upgrade-paths.md`
(each layer's simplicity-to-sophistication path), and this document
(what each layer *is*, architecturally). If a layer is added, renamed, or
removed, update all three in the same change (Blast Radius,
`docs/practices.md`).

### Mesh

**Represents:** the discretised spatial domain -- the control volumes FVM
integrates the governing equations over.

**Contract:** exposes cell geometry, adjacency/neighbour lookup, and
boundary identification, independent of whether the mesh is structured or
unstructured.

**MVP implementation:** 2D structured Cartesian, uniform spacing
(`docs/implementation/mvp.md`).

**Arrives via:** Stage 1 (`docs/planning/roadmap.md` TASK-011 Coordinate
System, TASK-012 Structured Cartesian Mesh).

**Upgrade path:** structured 2D → structured 3D → unstructured → arbitrary
geometry → adaptive refinement (`upgrade-paths.md` "Mesh").

### Variables

**Represents:** how field values (pressure, velocity, and any other
transported quantity) are associated with the mesh.

**Contract:** a common `Field` abstraction -- storage, metadata, and mesh
association -- shared by every physical quantity the engine transports,
regardless of arrangement.

**MVP implementation:** collocated arrangement (all variables stored at
cell centres).

**Arrives via:** Stage 2 (TASK-014 Field Interface, TASK-015 Scalar
Field, TASK-016 Vector Field).

**Upgrade path:** collocated → alternative placement schemes (e.g.
staggered) where required (`upgrade-paths.md` "Variables").

### Flux

**Represents:** the quantity of a transported field crossing a control
volume's face per unit time -- the term FVM's conservation form is built
from, and what actually gets summed over each control volume's faces to
update its value.

**Contract:** a face value derived from the mesh's face geometry, the
field's cell values, and the configured advection/diffusion schemes.

**Arrives via:** no single roadmap task builds "Flux" as its own
interface -- it is the conceptual layer that the Advection, Diffusion,
Gradient and Divergence operator interfaces (Stage 3, TASK-018) jointly
compute. Naming it as its own layer (per `docs/glossary.md` and
`upgrade-paths.md`) matters because a face flux is what those operators'
outputs mean physically, even though no single class named `Flux` need
exist in the implementation.

**Upgrade path:** simple flux formulation → more sophisticated
formulations (`upgrade-paths.md` "Flux").

### Advection

**Represents:** transport of a field by the flow's own velocity.

**Contract:** given a field and a velocity field, produces the
advective contribution to that field's flux at each face.

**MVP implementation:** first-order upwind.

**Arrives via:** Stage 3 interface (TASK-018 Operator Interfaces), Stage
4 concrete implementation (TASK-023 First-order Upwind Advection).

**Upgrade path:** upwind → central difference → QUICK → TVD → WENO
(`upgrade-paths.md` "Advection").

### Diffusion

**Represents:** transport of a field down its own gradient (viscous
momentum diffusion, thermal conduction, species diffusion).

**Contract:** given a field, produces the diffusive contribution to that
field's flux at each face.

**MVP implementation:** central-difference.

**Arrives via:** Stage 3 interface (TASK-018), Stage 4 concrete
implementation.

**Upgrade path:** simple central formulation → improved geometric/
non-orthogonal handling (`upgrade-paths.md` "Diffusion").

### Time Integration

**Represents:** advancing every transported field from one timestep to
the next, given the flux/source contributions computed for the current
state.

**Contract:** given a state and its time derivative (from the other
layers), produces the next state -- independent of which fields exist or
how many.

**MVP implementation:** RK4.

**Arrives via:** Stage 3 interface (TASK-020 Time Integrator Interface),
later stage for the concrete RK4 implementation.

**Upgrade path:** Euler → RK2 → RK4 → adaptive RK → implicit
(`upgrade-paths.md` "Time Integration").

### Pressure–Velocity Coupling

**Represents:** enforcing the incompressibility constraint (zero
divergence) by relating the pressure field back to the velocity field --
the step that makes an FVM incompressible-flow solver more than
independent per-field advection-diffusion.

**Contract:** given a provisional (not-yet-divergence-free) velocity
field, produces a corrected velocity field and the pressure field
consistent with it.

**MVP implementation:** PISO.

**Arrives via:** Stage 3 interface (TASK-021 Pressure Coupling
Interface), later stage for the concrete PISO implementation.

**Upgrade path:** PISO → SIMPLE / SIMPLEC / other strategies depending on
transient-vs-steady-state regime (`upgrade-paths.md`
"Pressure–Velocity Coupling" -- note the path does not treat these as
strictly "more advanced" than PISO, only as suited to different regimes).

### Linear Solvers

**Represents:** solving the linear systems pressure-velocity coupling
(and any other implicit step) produces.

**Contract:** given a linear system, produces its solution, independent
of the system's origin.

**MVP implementation:** Conjugate Gradient.

**Arrives via:** Stage 3 interface (TASK-022 Linear Solver Interface),
later stage for the concrete CG implementation.

**Upgrade path:** Conjugate Gradient → BiCGSTAB → GMRES → multigrid /
preconditioned methods (`upgrade-paths.md` "Linear Solvers").

### Boundary Conditions

**Represents:** how a field behaves at the edges of the simulated domain,
where no neighbouring control volume exists to supply a flux.

**Contract:** given a boundary face and the field's interior state,
produces the face value or flux the interior scheme needs, independent of
condition type.

**MVP implementation:** Dirichlet, Neumann, periodic (where practical).

**Arrives via:** Stage 3 interface (TASK-019 Boundary Condition
Interface).

**Upgrade path:** basic edge boundaries → mixed conditions → internal
boundaries → arbitrary surfaces/geometries (`upgrade-paths.md` "Boundary
Conditions").

---

## Construction and Configuration

Which concrete implementation fills each layer is decided once, at
simulation construction, through PyFlow's configuration system
(`src/pyflow/configuration/`, `docs/planning/roadmap.md` TASK-005). The
mechanism already exists for Stage 0's own configuration needs
(`RenderingConfig`, `src/pyflow/configuration/schema.py`); extending it
with per-layer strategy selection is Stage 3+ work, not yet done -- see
`docs/architecture/icds.md` for what a user actually selects among, once
those interfaces exist.

This is deliberately the same mechanism, not a parallel one: Stage 0's
`RenderingConfig.backend` (`"glfw"` vs `"offscreen"`) is already an
instance of "construction selects an implementation behind a stable
interface" (`src/pyflow/rendering/canvas.py`'s `create_canvas`) --
the numerical layers above will follow the same pattern once they exist,
not invent a new one.

---

## Relationship to Other Architecture Documents

- **`docs/architecture/icds.md`** (KA-030) is the formal contract
  definition for the layers marked as user-configurable above
  (Advection, Diffusion, Time Integration, Pressure–Velocity Coupling,
  Linear Solvers, Boundary Conditions, per `adr/ADR-003`) -- what a user
  actually chooses and what each choice guarantees. This document is the
  conceptual map; that one is the contract.
- **`docs/planning/dependency-tree.md`** is a hand-maintained ASCII tree
  of the same subsystems, structured around implementation-level
  operators (Gradient, Divergence, Sources as children of "Numerical
  Operators") rather than this document's nine conceptual layers -- the
  two do not describe identical trees (this document has no separate
  "Field Storage" node; the tree has no separate "Flux", "Variables" or
  "Boundary Conditions" node). Whether the tree should instead be
  *derived* from this document was left open pending this document's
  existence (`docs/planning/backlog.md`); it now exists, so that
  decision is unblocked -- not made here, since it's a decision about
  which of two hand-maintained documents becomes the source of truth,
  not something this document should resolve by fiat.
- **`docs/handbook/numerical-methods/`** holds the domain theory behind
  each layer's concrete schemes (what upwind advection *is*), largely
  unwritten as of this document (`docs/planning/backlog.md` E3). This
  document links out to those entries by name rather than duplicating
  their eventual content.

---

## Definition of Done

This document is complete when a future developer can read it, before
opening any `src/pyflow/engine/` or `src/pyflow/physics/` file, and
understand what the nine layers are, why each is independently
replaceable, and where in the roadmap each one arrives -- without needing
to reconstruct that from Stage-by-Stage task descriptions scattered
across `roadmap.md`.

## Maintenance

Written 2026-08-17 against `adr/ADR-002-fvm-first.md`,
`adr/ADR-003-modular-numerical-strategies.md`, `docs/implementation/
mvp.md`, `docs/implementation/upgrade-paths.md`, `docs/glossary.md`
("Layer"), and `docs/planning/roadmap.md`'s actual Stage 1-4 task
numbers -- not re-derived from general CFD knowledge (the same caution
`prompts/features/adr.md` gives for ADRs applies here: prefer what the
project has already decided over generic domain reasoning).

Update the relevant layer's entry the moment its roadmap task actually
lands -- "Arrives via" should read as "implemented in" once true, per
`docs/practices.md`'s "write prospective language as retrospective the
moment it's true."
