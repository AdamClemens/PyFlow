# Glossary

This glossary records terms whose meaning has been explicitly clarified for PyFlow. It is not intended to define every technical term used by the project.

## Capability

An ability that PyFlow possesses, described independently of how that ability is implemented.

A capability answers **what PyFlow can do**, not which algorithm, data structure, library, or implementation provides it.

For example:

* "Model heat transport" is a capability.
* "Use a finite-volume discretisation" is not a capability; it is an implementation choice.

Capabilities should remain implementation-agnostic so that the capability map remains useful as the implementation evolves.

---

## Capability Map

The complete collection of PyFlow's capabilities and their relationships.

The capability map is conceptually a **graph**, not necessarily a tree. Different useful trees or views—such as capability trees, technology trees, dependency trees, or implementation views—may be projections of the same underlying information.

The capability map should therefore be maintained as a sufficiently rich source of truth from which those views can eventually be generated.

---

## Feature

A deliverable implementing part of a capability.

---

## Golden Demo

A demonstration proving a capability works end-to-end.

---

## Thin Slice

A complete vertical implementation from simulation through rendering to user interaction.

---

## Technology Tree

A hierarchical view of technologies, methods, or approaches relevant to achieving a capability.

There may be multiple technology trees covering different aspects of PyFlow. They are views of related knowledge rather than necessarily being the fundamental representation of the project.

---

## Knowledge Graph

The conceptual graph describing entities and relationships relevant to PyFlow.

The graph may contain capabilities, physical phenomena, equations, numerical methods, solvers, compatibility relationships, dependencies, and other useful concepts.

The important property is that the underlying knowledge is represented independently of any particular visualisation. Trees, tables, compatibility diagrams, and other views can then be derived from it.

---

## Field-Centric

An approach in which PyFlow is organised around the physical fields and quantities being represented rather than around individual physical phenomena.

For example, velocity, mass, temperature, and humidity are treated as fields that can participate in multiple physical processes.

This is intended to allow additional physical processes to be composed onto an existing simulation rather than requiring each phenomenon to become a separate simulation system.

---

## Phenomenon

A physical process or effect that PyFlow may model, such as convection, heat transport, or cloud formation.

A phenomenon describes **what happens physically**. It is distinct from both the fields involved and the numerical methods used to model it.

---

## Physics

Within PyFlow's documentation, Physics describes the physical theory underlying the phenomena being simulated.

It includes:

* the relevant physical concepts;
* the relationships between physical quantities;
* governing equations;
* assumptions and approximations;
* explanations of the equations sufficient to understand their role in the simulation.

It is not intended to become a comprehensive physics textbook. Detailed derivations can be delegated to established references where appropriate.

---

## Simulation

The set of physical properties and processes that a particular PyFlow simulation is intended to represent.

Examples include:

* velocity / flow;
* mass transport;
* heat transport;
* density;
* humidity;
* convection;
* cloud formation.

Simulation therefore describes **what we want to simulate**, while Physics describes the theory and equations governing those things.

---

## Solver

A numerical method or algorithm used to obtain a solution to the equations governing a simulation.

The term is used broadly enough to encompass the major numerical approaches PyFlow may employ, while recognising that a complete simulation will generally involve several cooperating numerical components.

A solver is therefore not necessarily synonymous with the entire simulation engine.

---

## Numerical Method

A mathematical/computational approach for representing or solving a physical problem numerically.

Examples relevant to PyFlow include:

* Finite Volume Method (FVM);
* Finite Element Method (FEM);
* particle-based methods;
* spectral methods.

Numerical methods describe approaches at a higher level than individual schemes or algorithms.

---

## Finite Volume Method (FVM)

The numerical framework selected as PyFlow's initial foundation.

FVM divides the simulation domain into control volumes and formulates the governing equations in terms of quantities and fluxes across the boundaries of those volumes.

PyFlow will initially implement FVM while maintaining an architecture that permits a future FEM extension.

---

## Finite Element Method (FEM)

A numerical method based on representing the solution using basis functions over elements of a discretised domain.

FEM is **not** the initial PyFlow implementation, but the architecture should avoid unnecessarily preventing its future addition.

---

## Scheme

A particular numerical approximation used within a numerical framework.

For example, an advection scheme determines how advective transport is discretised.

Schemes are therefore generally replaceable implementations within a larger numerical framework rather than defining the entire simulation approach.

---

## Advection

Transport of a quantity by the motion of a fluid.

In PyFlow, advection is expected to be a replaceable numerical component, allowing different advection schemes to be selected without modifying the surrounding timestep/execution machinery.

---

## Diffusion

Transport or spreading caused by gradients in a quantity, such as momentum diffusion or thermal conduction.

In PyFlow, diffusion is expected to be a replaceable numerical component.

---

## Flux

The rate at which a conserved quantity crosses a surface or control-volume boundary.

In FVM, fluxes are fundamental to expressing conservation laws because the governing equations are evaluated through exchanges across control-volume faces.

Flux calculation is therefore an important numerical layer, rather than merely an optional implementation detail.

---

## Boundedness

The property that a scheme cannot produce a value outside the range implied by the data it interpolates between—it can never manufacture a new maximum or minimum.

First-order upwind advection is unconditionally bounded, because the face value it produces is always one of the two neighbouring cell values. Central differencing is not, above a cell Péclet number of 2.

This term is recorded here because it is routinely confused with stability, below, and because PyFlow's own interface contracts (`docs/architecture/icds.md`) describe scheme behaviour in terms of it. See `docs/handbook/numerical-methods/fluxes.md` for the full treatment.

---

## Numerical Stability

The property that errors decay rather than grow over successive timesteps.

**Stability and boundedness are different properties, and conflating them is the specific error this pair of entries exists to prevent.** Boundedness belongs to the spatial discretisation alone. Stability belongs to the spatial discretisation *and* the time integrator together: first-order upwind is unconditionally bounded but still diverges above its CFL limit when advanced explicitly, and the same scheme solved implicitly is stable at any timestep.

"Unconditionally stable" is therefore a claim about a spatial-scheme-and-integrator pair, never about a scheme alone. PyFlow's documentation said otherwise in two places until 2026-08-18 (`docs/CHANGELOG-DESIGN.md`).

---

## Collocated Variables

A variable arrangement in which the primary simulation variables are stored at the same spatial locations, typically the centres of control volumes.

PyFlow will initially use a collocated arrangement.

The architecture should permit alternative arrangements to be introduced later without requiring fundamental changes to the rest of the simulation engine.

---

## Staggered Variables

A variable arrangement in which different variables are stored at different spatial locations—for example, velocity components at cell faces and pressure at cell centres.

This is a potential future alternative to the initial collocated arrangement.

---

## Pressure–Velocity (P–V) Coupling

The numerical machinery used to enforce the relationship between pressure and velocity in incompressible or approximately incompressible flow.

Pressure and velocity are coupled because the pressure field must enforce the appropriate continuity constraint while the velocity field responds to pressure gradients.

PyFlow will initially use PISO, while treating P–V coupling as a replaceable layer where practical.

---

## PISO

**Pressure-Implicit with Splitting of Operators.**

A pressure–velocity coupling algorithm commonly used for transient CFD.

PISO will be the initial PyFlow P–V coupling approach.

It is selected as a practical starting point rather than being treated as a permanent architectural commitment.

---

## Linear Solver

A numerical algorithm used to solve the linear systems that arise during discretisation of the governing equations.

Linear solvers are expected to be replaceable components because different problems may benefit from different approaches.

---

## Explicit Time Integration

A time-integration approach in which the state at the next timestep is calculated directly from known current-state information.

PyFlow will initially use explicit RK4.

---

## Implicit Time Integration

A time-integration approach in which the unknown future state appears in the equations being solved for that timestep.

Implicit methods can permit larger timesteps or improve stability for some stiff problems, but generally introduce substantially more computational and implementation complexity.

PyFlow should have a clear upgrade path toward implicit integration without requiring the initial explicit architecture to be discarded.

---

## RK4

The classical fourth-order **Runge–Kutta** method for numerical time integration.

RK4 is the initial PyFlow timestep integration method because it is relatively simple, well established, and provides a reasonable starting point before more sophisticated approaches are required.

---

## Boundary Condition

A constraint describing how the solution behaves at a boundary of the simulation domain or at an internal surface.

PyFlow ultimately needs to support multiple boundary-condition types and arbitrary combinations of them across different boundaries.

Initial candidates include:

* Dirichlet;
* Neumann;
* periodic.

Internal boundaries are part of the intended eventual capability, even though the MVP initially uses a simple 2D domain.

---

## Dirichlet Boundary Condition

A boundary condition that specifies the value of a field at the boundary.

For example, specifying a fixed temperature along a wall.

---

## Neumann Boundary Condition

A boundary condition that specifies the derivative or flux of a field at the boundary.

For example, specifying a heat flux through a wall.

---

## Periodic Boundary Condition

A boundary condition that connects one boundary of a domain to another such that the solution leaving one side re-enters through the corresponding side.

Periodic boundaries are useful for representing repeating or effectively unbounded domains.

---

## Structured Mesh

A mesh whose cells follow a regular, implicitly organised arrangement.

A structured mesh is the initial PyFlow mesh implementation because it provides a comparatively simple foundation for the first working simulation.

It does not imply that PyFlow will permanently be restricted to structured meshes.

---

## Layer

A replaceable conceptual component of the numerical execution pipeline.

Examples include:

* mesh;
* variable arrangement;
* flux;
* advection;
* diffusion;
* time integration;
* pressure–velocity coupling;
* linear solvers;
* boundary conditions.

A layer should expose a stable or compatible interface so that its implementation can be replaced without requiring unrelated layers to change.

---

## Interface Contract

The externally observable contract governing how a component is used.

For PyFlow's internal numerical architecture, this means the inputs, outputs, behaviour, and guarantees that allow one implementation of a layer to be substituted for another.

The core principle is:

> Every implementation exposes the same interface. The timestepper doesn't care which one it has.

---

## ICD

**Interface Contract Definition.**

PyFlow's term for a formal definition of an interface contract.

ICDs may describe interfaces exposed to users as well as, where useful, internal interfaces between replaceable numerical components.

---

## Configuration

The mechanism by which a PyFlow simulation selects and constructs its replaceable components.

For example, a configuration may eventually specify which advection, diffusion, pressure-coupling, and linear-solver implementations should be used.

Configuration is deliberately a relatively small concern in the MVP; the architecture should support it without requiring a sophisticated configuration system from the outset.

---

## MVP

The **Minimum Viable Product** of PyFlow: the smallest complete implementation that demonstrates the fundamental architecture working as a coherent CFD simulation.

The MVP is intended to use the simplest reasonable implementation of each required layer simultaneously rather than selecting sophisticated implementations independently.

The MVP is therefore a working simulation, not merely a collection of implemented components.

---

## Upgrade Path

A documented route from an existing implementation to a more capable or sophisticated implementation.

An upgrade path should describe how a component can be improved or replaced while preserving the surrounding architecture.

This deliberately does not imply that the more advanced implementation has already been designed or that the initial choice is permanent.

---

## Drop-In

An implementation that can replace another implementation of the same layer without requiring changes to unrelated parts of the system.

"Drop-in" does not necessarily mean byte-for-byte or perfectly behaviourally identical; it means that the surrounding architecture interacts with it through the established interface contract.

---

## Physics Dependency Tree

A representation of how physical capabilities and phenomena depend upon one another.

It describes relationships in the **physical problem space**, rather than the software implementation.

For example, a more sophisticated physical capability may depend on several underlying fields or processes.

---

## Implementation Dependency Tree

A representation of how PyFlow's software components depend upon one another in order to execute a simulation.

This is distinct from the physics dependency tree.

The physics tree can be regarded as a projection of what the implemented architecture is capable of representing; the two trees should not be assumed to be identical.

---

## Planning System

The separate system used to capture, organise, relate, and derive the knowledge required to design PyFlow.

The planning system is intentionally separate from the CFD engine.

Its purpose is to ensure that the design does not depend on an individual's memory and to provide a sufficiently structured source of information from which useful views—such as capability maps and technology trees—can eventually be generated.

The planning system is intended to be sufficiently well designed that it could potentially be reused for another software project.

---

## Stage

A numbered step in `docs/planning/roadmap.md`, the unit PyFlow's work is actually planned and executed in.

Stages run from Stage 0 (Engineering Infrastructure, no CFD functionality) upward. Each stage contains numbered `TASK-XXX` items with explicit dependencies and acceptance criteria, and every stage after Stage 0 must leave PyFlow with a working simulation.

Stage is the operative term: when asking "what am I working on," the answer is a task within a stage.

---

## Capability Level

A numbered band of capability in `docs/planning/implementation-plan.md`, describing the long-range shape of PyFlow's growth rather than its execution order.

Levels run 0-10 and answer "what can PyFlow do once this is finished," where Stages answer "what do I build next." The two are deliberately different views, and they are **not** a one-to-one mapping — several Stages contribute to one Level, and at least one Level currently has no corresponding Stage at all. See the Stage/Level correspondence table in `docs/planning/roadmap.md`.

---

## Release

A published increment of PyFlow, versioned in `pyproject.toml`.

Releases are currently the least developed of the project's three progression concepts: no release process is defined and the knowledge architecture has no entry specifying one. The project is at version 0.0.1 and has made no release.

`docs/planning/releases.md` records why that is a deliberate deferral rather than an oversight, and the concrete conditions that would trigger defining a process. (This entry said that file "is empty" until 2026-08-18; it was written on 2026-08-17 and the description was left stale — the two documents reference each other, so a change to either needs checking against the other.)

The recurring project rule about working demonstrations is stated in terms of Stages, not Releases (`docs/engineering-principles.md` P-004). Do not infer a release cadence from it; there is not one yet.

---

## Institutional Memory

The principle that project knowledge should be captured in durable project artifacts rather than relying on an individual's memory.

For PyFlow, this means that important decisions, terminology, relationships, constraints, design reasoning, and implementation knowledge should live in the repository where future contributors—including a future version of the original developer who has forgotten the details—can recover it.

This is a core project goal rather than merely a documentation preference.

---

## Project Specification

The current agreed design and intent of PyFlow.

There is no single file with this name. The specification is distributed across a small set of authoritative documents, each with one job:

- `docs/planning/roadmap.md` — what to build next, and what done means for it
- `docs/planning/backlog.md` — outstanding work, open decisions, known gaps
- `docs/CHANGELOG-DESIGN.md` — what was decided, when, and why

The working rule is:

> Every design session begins by reading the current design state and ends by updating it.

Those documents therefore act as the primary continuity mechanism between design sessions. See `docs/practices.md` for the session workflow itself.

---

## Docs

The collection of repository documentation forming PyFlow's durable project knowledge.

The documentation is intended to be maintained as part of the engineering process rather than treated as supplementary prose.

The documentation should make the project understandable and maintainable by a single competent developer who may have forgotten most of its details.

---

## Dreams

The deliberately non-committal collection of interesting capabilities, technologies, or directions that PyFlow may explore in the future.

Items in `dreams.md` are **not commitments or roadmap items**. They are retained so that potentially valuable ideas are not lost merely because they are not currently justified.

---

## Reversible Decision

A design decision that can be changed later without disproportionate cost.

PyFlow favours reversible decisions where understanding is insufficient to justify a permanent commitment.

The corresponding principle is:

> Prefer reversible decisions until understanding justifies commitment.

---

## Simplest Valid Implementation

The least sophisticated implementation that is technically sound and sufficient for the current stage.

This does not mean the quickest hack or the implementation with the fewest lines of code. It means an implementation that genuinely satisfies the relevant contract and provides a sound foundation for later improvement.

The core implementation principle is:

> Implement the simplest valid version of each layer, then improve them independently.

---

## Verification

Confirming that an implementation satisfies its own stated contract --
does the code do what its interface and acceptance criteria say it
does. A unit test passing is verification.

Added 2026-08-20 after `docs/planning/implementation-plan.md`'s
Definition of Done was found to list "Verification completed" as a
requirement for every task without either term being defined anywhere
in the project -- an untestable acceptance criterion by construction,
exactly what `docs/practices.md`'s "Acceptance criteria must be
testable" rule now exists to prevent. See Validation, below, for the
distinct property verification does not cover.

---

## Validation

Confirming that an implementation is *physically correct* -- not just
internally consistent with its own interface, but consistent with the
governing equations and physical laws it claims to solve. Conservation
(mass, momentum, energy) holding to within solver tolerance is
validation; a velocity field matching a published reference solution
(e.g. Ghia et al. 1982 for lid-driven cavity) is validation; a scheme's
measured order of accuracy matching its theoretical order is
validation. Code can pass every unit test (verification) while being
physically wrong -- a sign error in a source term reads as perfectly
coherent code and passes every software-correctness check that doesn't
know what the answer should be.

This is not a hypothetical risk for PyFlow specifically: the 2026-08-18
scientific-accuracy review (`docs/CHANGELOG-DESIGN.md`) found the
Boussinesq buoyancy term's sign inverted in `docs/handbook/physics/
buoyancy.md` -- an error that, written as code instead of prose, would
have made warm fluid sink. Nothing in the test suite as it existed then
would have caught a code equivalent of that error, because nothing
checked the physics, only whether the code ran. `docs/planning/
backlog.md` (Part II, "physical correctness validation") is where this
gap is tracked as scheduled work, not left as a standing risk.
