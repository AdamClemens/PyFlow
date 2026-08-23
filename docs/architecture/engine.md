# Engine Architecture

Per `docs/planning/knowledge-architecture.md` KA-029. A conceptual map of
the CFD engine's replaceable layers, meant to orient a future developer
*before* they open individual implementation files.

This document describes target architecture, not current implementation
in full -- but by the end of Stage 3 (2026-08-23), eight of the nine
layers below are partly real: Mesh and Variables completely
(`docs/planning/roadmap.md` Stages 1/2), and Advection, Diffusion, Time
Integration, Pressure-Velocity Coupling, Linear Solvers and Boundary
Conditions each as an interface with no concrete scheme behind it yet
(Stage 3) -- see each layer's own "Implemented in" note below. Only Flux
still has no roadmap task of its own and remains "Arrives via" throughout
the document. They arrive incrementally through Stages 1-5.

This is not the place for numerical theory -- what upwind advection *is*,
mathematically, belongs in `docs/handbook/numerical-methods/advection.md`
(written 2026-08-17, `docs/planning/backlog.md` E3, along with the other
nine numerical-methods entries). This document is about the *shape* of the
engine: what the layers are, why
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

The same nine layers appear in four places that must stay in agreement:
`docs/glossary.md` ("Layer"), `docs/implementation/upgrade-paths.md`
(each layer's simplicity-to-sophistication path), this document (what
each layer *is*, architecturally), and `planning/data/components.yaml`
(the machine-readable graph, added 2026-08-21). If a layer is added,
renamed, or removed, update all four in the same change (Blast Radius,
`docs/practices.md`).

Three of the four are now checked rather than merely asked for. Each
component in the graph carries a `must_appear_in` list, and
`make check-graph` fails if its name is missing from this document or
from `upgrade-paths.md`. `glossary.md` is named there but not
machine-checked: its "Layer" entry uses lowercase prose bullets with
different wording ("variable arrangement" for Variables), so a name
match would be wrong rather than merely strict. That gap is stated in
`planning/data/components.yaml` rather than left to be discovered.

### Mesh

**Represents:** the discretised spatial domain -- the control volumes FVM
integrates the governing equations over.

**Contract:** exposes cell geometry, adjacency/neighbour lookup, and
boundary identification, independent of whether the mesh is structured or
unstructured.

**MVP implementation:** 2D structured Cartesian, uniform spacing
(`docs/implementation/mvp.md`).

**Implemented in:** Stage 1 (`docs/planning/roadmap.md` TASK-011
Coordinate System, TASK-012 Structured Cartesian Mesh), both done
2026-08-20 -- `src/pyflow/engine/{coordinate_system,mesh}.py`.

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

**Implemented in:** Stage 2 (`docs/planning/roadmap.md` TASK-014 Field
Interface, TASK-015 Scalar Field, TASK-016 Vector Field), all done
2026-08-21 -- `src/pyflow/engine/{field,collocated_field,scalar_field,
vector_field}.py`. The split matters and is the layer's own shape in
code: `Field` carries only mesh association, a name, and the promise of
an independent copy -- no storage at all, precisely so it makes no
collocated-vs-staggered assumption -- and `CollocatedField` adds the
cell-centred storage the MVP arrangement needs, with `ScalarField` and
`VectorField` as its leaves. Each of those two layers has its own
contract suite (`tests/unit/test_field_contract.py`,
`tests/unit/test_collocated_field_contract.py`); an alternative
placement satisfies the first alone.

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

**Implemented in:** Stage 3, the interface only (`docs/planning/
roadmap.md` TASK-018 Operator Interfaces, done 2026-08-23) --
`src/pyflow/engine/numerics/advection.py`. The MVP implementation named
above does not exist yet; that is Stage 4 (TASK-023 First-order Upwind
Advection). A trivial, non-physical reference implementation lives under
`engine/numerics/assembly.py` solely so Stage 3's golden demo has
something to assemble into -- see that module's own docstring; it is not
this layer's MVP implementation and computes nothing.

**Upgrade path:** upwind → central difference → QUICK → TVD → WENO
(`upgrade-paths.md` "Advection").

### Diffusion

**Represents:** transport of a field down its own gradient (viscous
momentum diffusion, thermal conduction, species diffusion).

**Contract:** given a field, produces the diffusive contribution to that
field's flux at each face.

**MVP implementation:** central-difference.

**Implemented in:** Stage 3, the interface only (TASK-018, done
2026-08-23) -- `src/pyflow/engine/numerics/diffusion.py`. The MVP
implementation does not exist yet; that is Stage 4. Same reference-only
caveat as Advection above.

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

**Implemented in:** Stage 3, the interface only (TASK-020 Time
Integrator Interface, done 2026-08-23) --
`src/pyflow/engine/numerics/time_integrator.py`. The concrete RK4
implementation is a later stage. Same reference-only caveat as Advection
above.

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

**Implemented in:** Stage 3, the interface only (TASK-021 Pressure
Coupling Interface, done 2026-08-23) --
`src/pyflow/engine/numerics/pressure_coupling.py`. The concrete PISO
implementation is a later stage. Same reference-only caveat as Advection
above; TASK-021 is also the task that builds `engine/numerics/
assembly.py`, the registry all six of these layers resolve a configured
name through.

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

**Implemented in:** Stage 3, the interface only (TASK-022 Linear Solver
Interface, done 2026-08-23) -- `src/pyflow/engine/numerics/
linear_solver.py`. The concrete CG implementation is a later stage. Same
reference-only caveat as Advection above.

**Upgrade path:** Conjugate Gradient → BiCGSTAB → GMRES → multigrid /
preconditioned methods (`upgrade-paths.md` "Linear Solvers").

### Boundary Conditions

**Represents:** how a field behaves at the edges of the simulated domain,
where no neighbouring control volume exists to supply a flux.

**Contract:** given a boundary face and the field's interior state,
produces the face value or flux the interior scheme needs, independent of
condition type.

**MVP implementation:** Dirichlet, Neumann, periodic (where practical).

**Implemented in:** Stage 3, the interface only (TASK-019 Boundary
Condition Interface, done 2026-08-23) -- `src/pyflow/engine/numerics/
boundary_condition.py`. Concrete conditions are a later stage; the
interface itself covers only the Dirichlet/Neumann shapes -- periodic
fits neither and is not modelled yet (see that module's own docstring).
Same reference-only caveat as Advection above, minus periodic: `engine/
numerics/assembly.py` registers a trivial reference for the
Dirichlet/Neumann shapes only.

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
- **`docs/planning/dependency-tree.md`** is now a *generated view* of
  the layers below, and no longer a second hand-maintained account of
  them. Until 2026-08-21 it was a hand-drawn ASCII tree structured
  around implementation-level operators (Gradient, Divergence, Sources
  as children of "Numerical Operators") rather than this document's nine
  conceptual layers, and the two genuinely disagreed: it had no separate
  "Flux", "Variables" or "Boundary Conditions" node, this document has
  no separate "Field Storage" one. Both documents recorded the
  divergence and neither could fix it, since fixing it by editing one is
  only picking a winner by hand.
  `adr/ADR-006-knowledge-graph-scope.md` picked this document, and made
  the choice structural: `planning/data/components.yaml` holds the nine
  layers with each dependency **quoted from the Contract sentences
  below**, and `make check-dependency-tree` fails if the rendered
  document and the graph disagree.

  **What this asks of anyone editing the layers below**: a layer added,
  renamed, or removed here also needs its entity in
  `planning/data/components.yaml`, and a **Contract** reworded such that
  a quoted dependency no longer matches means one of the two is stale.
  `make check-graph` catches a broken edge; it cannot catch a quote that
  has quietly stopped being accurate, so that stays a reading job.
  One correction to the old framing while we are here: the engine is a
  DAG, not a tree -- Flux alone depends on five other layers -- which is
  part of why the hand-drawn version kept diverging, since an ASCII tree
  can only draw a node once.
- **`docs/handbook/numerical-methods/`** holds the domain theory behind
  each layer's concrete schemes (what upwind advection *is*) -- all ten
  KA-016..025 entries written 2026-08-17 (`docs/planning/backlog.md` E3),
  one corresponding to each layer below except Mesh and Variables, which
  map to `meshes.md` and `variable-placement.md`. This document links out
  to those entries by name rather than duplicating their content. Where
  an entry records a constraint that spans two layers -- the
  advection/time-integration stability pairing
  (`time-integration.md`), or the singular pressure system a
  closed domain produces (`pressure-velocity-coupling.md`,
  `linear-solvers.md`, `boundary-conditions.md`) -- the handbook is the
  authoritative statement of it and this document does not restate it.

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

Reviewed 2026-08-18: two stale references removed. This document
described `docs/handbook/numerical-methods/advection.md` as "currently an
empty stub" and the numerical-methods handbook as "largely unwritten" --
both true when this document was written on 2026-08-17 and false by the
end of the same day, when E3 landed all ten entries. Exactly the
prospective-language drift this document's own Maintenance note warns
about, found by a read-through rather than by any check, which is why the
same pass re-read every document referencing the handbook.
