# PyFlow Knowledge Architecture

Checked-by: stage-boundary

**Status:** Initial complete planning baseline
**Purpose:** Define the repository knowledge required to complete the design phase of PyFlow and provide sufficient context to generate each artifact and its associated task prompt.
**Source of truth:** This document is the authoritative inventory and specification of planned knowledge artifacts during the initial planning phase.

**Maintenance note (2026-08-15):** each artifact's `Name:` is the
artifact's *actual* repository path and its `Status:` is its *actual*
current state. Both had drifted -- six `Name:` paths named locations the
project never used, and nine `Status:` fields still read `planned` for
artifacts that had been written. Both were corrected on 2026-08-15. If a
future decision moves an artifact or changes its state, update it here in
the same change; a spec that describes a repository which does not exist
is worse than no spec. `docs/repository-manifest.md` tracks the same
artifacts from the inventory side and must be updated with it.

---

# 1. Purpose

This document describes **what knowledge the PyFlow repository must contain**, why that knowledge exists, how the artifacts relate to one another, and what information is required to produce each artifact.

It is intentionally a **flat document**.

The relationships between artifacts are represented explicitly rather than through document nesting. This allows views such as:

* dependency trees;
* knowledge graphs;
* capability trees;
* documentation indexes;
* implementation dependencies;
* prompt-generation order;
* planning progress.

to be generated from this document later.

The document is therefore both:

1. a durable checklist for completing the planning system; and
2. the source material from which individual document-generation prompts can be constructed.

The planning phase is considered complete when all required first-version artifacts have reached their stated Definition of Done and the resulting knowledge is sufficient to begin implementation without relying on undocumented conversation history.

---

# 2. Project Context

## 2.1 Project

**PyFlow** is a Python project intended to become a modular computational fluid dynamics simulation engine.

The initial scope is fluid dynamics, with an architecture capable of extending toward additional interacting physical fields and, eventually, other classes of physics.

The project is intended to remain understandable and maintainable by a single competent developer returning to it after a significant absence.

The repository therefore acts as the project's institutional memory.

Nothing important should need to remain in an individual's memory for the project to remain understandable.

---

## 2.2 Core vision

PyFlow should allow a user to describe a simulation in terms of:

* physical fields;
* physical processes;
* material properties;
* boundary and surface conditions;
* numerical methods;
* and configuration choices.

The engine should execute those descriptions through interchangeable numerical components.

The user should ultimately be able to construct rich CFD simulations according to their interests without modifying the engine's internal timestep loop merely to change a numerical method.

For example, conceptually:

```text
velocity = advection.apply(...)
```

rather than:

```text
# timestep implementation contains a particular
# hard-coded advection scheme
```

Changing from one numerical scheme to another should ultimately be a configuration/construction decision rather than a deep implementation edit.

---

## 2.3 Field-centric philosophy

PyFlow is **field-centric rather than phenomenon-centric**.

The engine should primarily provide mechanisms for representing and evolving fields.

Physical phenomena are combinations of fields, processes and governing equations rather than hard-coded simulation types.

Examples of fields include:

* velocity;
* mass;
* temperature;
* heat;
* density;
* humidity;
* convection.

This distinction is important when designing both the capability map and the engine architecture.

---

# 3. Engineering Context

The following principles have been adopted by the project and should inform every artifact.

## 3.1 Core principles

* Everything that can be generated should be generated.
* Knowledge should be captured so that project progress never depends on individual memory.
* Nothing important should have to live in a developer's head.
* Prefer reversible decisions until understanding justifies commitment.
* Implement the simplest valid version of each layer, then improve them independently.
* Every implementation should expose the same or a compatible interface.
* Separate construction from execution.
* Prefer configuration of interchangeable components over hard-coded implementation choices.
* Build a working demonstration at every project stage after Stage 0. (Read "simulation" until 2026-08-22; P-004 in `docs/engineering-principles.md` is authoritative and says demonstration.)
* Prefer complete vertical slices over disconnected infrastructure.
* Do not canonise the first implementation merely because it was implemented first.
* Prefer approaches demonstrated to work in completed real projects over theoretically optimal approaches with little evidence of practical success.
* Stop descending the initial capability tree when the next level would introduce implementation decisions.
* Keep the architecture capable of extension without prematurely implementing every possible extension.
* A document should have one primary job.
* The repository is the authoritative source of project knowledge.

---

# 4. Planning Context

The planning system exists to design PyFlow before substantial implementation begins.

It consists conceptually of several related but distinct knowledge structures:

* capability map;
* knowledge graph;
* implementation dependency tree;
* numerical-method compatibility information;
* architecture decisions;
* implementation roadmap;
* handbook;
* documentation guidance;
* agent guidance.

These are **different views of related knowledge**, not necessarily separate sources of truth.

The long-term objective is that sufficiently structured source information can generate useful views rather than requiring the same information to be maintained manually in multiple places.

---

# 5. Artifact Record Schema

Every artifact described below has the following conceptual properties.

### Name

Repository path and filename.

### Purpose

Why the artifact exists.

### Scope

What belongs in it and, where useful, what explicitly does not.

### Depends On

Artifacts whose information is required to create this artifact correctly.

### Enables

Artifacts or activities that become easier or possible once this artifact exists.

### References

Related artifacts which should be linked or consulted but which do not form a hard generation dependency.

### Audience

Who should be able to use the artifact.

### Intent

The intended effect of the document: what a reader should understand or be able to do after reading it.

### Content Requirements

The substantive information the generated document must contain.

### Definition of Done

Objective conditions indicating that the artifact is sufficiently complete for its current project phase.

### Status

Current state of the artifact:

* `planned` — specified here, not yet written.
* `draft` — exists, with purpose and structure settled and core content
  present.
* `complete` — satisfies its Definition of Done for the current project
  phase.
* `superseded` — the artifact's *purpose* is now served elsewhere, and
  the file described by its `Name:` will not be written. The entry is
  kept rather than deleted so the record survives; it must say what
  supersedes it and where the responsibility went. Added 2026-08-15,
  taking the term from the ADR lifecycle in `adr/README.md`, which
  already uses it. Over a twelve-stage project artifacts will be
  replaced, and without this status the only options are deleting the
  entry (losing the record, against P-001) or marking it `complete`
  (sending a reader after a file that does not exist).

---

# 6. Required Artifacts

---

## KA-001 — Project README

**Name:** `README.md`

**Purpose:** Provide the first-entry overview of PyFlow and direct readers toward the repository's important knowledge.

**Scope:** High-level project orientation.

The README should not become the detailed technical handbook or implementation plan.

**Depends On:**

* engineering principles;
* capability map;
* current project description.

**Enables:**

* project orientation;
* onboarding;
* navigation to the documentation.

**References:**

* handbook;
* implementation plan;
* capability map;
* repository structure.

**Audience:**

* developers;
* contributors;
* curious users;
* coding agents.

**Intent:**

A person unfamiliar with PyFlow should be able to understand what it is, why it exists, its broad direction, and where to find deeper information without reading the entire repository.

**Content Requirements:**

* project name;
* concise project description;
* project vision;
* current development status;
* high-level architecture direction;
* documentation entry points;
* development instructions when implementation begins;
* statement that the repository contains the project's authoritative knowledge.

**Definition of Done:**

* accurately describes the project;
* does not contain detailed design material that belongs elsewhere;
* links to the important documentation;
* makes the current state clear;
* remains useful to a future developer returning after a long absence.

**Status:** `draft`

---

## KA-002 — Engineering Principles

**Name:** `docs/engineering-principles.md`

**Purpose:** Record enduring engineering principles that guide PyFlow development.

**Scope:** Principles and their rationale.

It should not become a collection of project decisions, implementation instructions or temporary practices.

**Depends On:** None.

**Enables:**

* CLAUDE.md guidance;
* documentation guidelines;
* implementation planning;
* prompt context;
* future architectural decisions.

**Audience:**

* developers;
* coding agents;
* future contributors.

**Intent:**

Make the project's engineering philosophy explicit enough that a future developer can make reasonable decisions without needing the original conversations.

**Content Requirements:**

Each principle should include:

* concise statement;
* rationale;
* useful interpretation;
* examples where necessary.

Known principles include:

* Everything that can be generated should be generated.
* Knowledge should be captured so project progress never depends on individual memory.
* Prefer reversible decisions until understanding justifies commitment.
* Implement the simplest valid version of each layer, then improve them independently.
* Every implementation exposes the same or compatible interface.
* Separate construction from execution.
* Prefer configuration over hard-coded numerical choices.
* Working simulation at every stage after Stage 0.
* Build vertical slices.
* Prefer proven practical approaches.
* Do not over-design.
* Stop capability decomposition before implementation details.
* Preserve the ability to change our minds.

**Definition of Done:**

* principles are implementation-independent;
* principles have rationales;
* no unnecessary duplication with practices;
* principles represent enduring project philosophy;
* document is useful to a future developer without conversation history.

**Status:** `draft`

---

## KA-003 — Practices

**Name:** `docs/practices.md`

**Purpose:** Record the project's recurring working practices.

**Scope:** How project work is conducted.

**Depends On:**

* engineering principles.

**Enables:**

* consistent project maintenance;
* future-agent behaviour;
* repeatable design sessions.

**Audience:**

* developer;
* coding agents.

**Intent:**

Make recurring project habits explicit so they do not depend on remembering how previous sessions were conducted.

**Content Requirements:**

At minimum:

* every design session begins by reading the Project Specification/current authoritative design state;
* every design session ends by updating the authoritative design state;
* repository documentation is treated as institutional memory;
* **blast radius**: before making a change, determine what else references, restates, tracks or depends on the thing being changed, and update all of it in the same change; where something in the radius cannot be updated now, record the divergence explicitly rather than leaving it silent (added 2026-08-15, after four separate instances of this failure were found by audit);
* changes to decisions are recorded in the appropriate artifact;
* generated content is not manually edited where regeneration is available;
* design proceeds according to dependency/knowledge order rather than arbitrary file order;
* maintain a working vertical slice after Stage 0;
* use Git as the primary historical record;
* avoid unnecessary process intended for multi-person teams while the project remains single-developer.

**Definition of Done:**

* practices are actionable;
* practices are clearly distinguished from principles.

**Status:** `complete` (`docs/planning/backlog.md` F1, closed 2026-08-19).
The "use Git as the primary historical record" content requirement
above had never been made concrete -- branch naming, commit granularity,
message form and what must pass before a commit were all previously
implicit. F1 added a Version Control section stating all four, plus a
tooling dependency update policy generalising the existing Python
version policy. Still a living document by design (new practices get
added as gaps are found, per its own header) -- `complete` means it
currently satisfies its Definition of Done, not that nothing will be
added to it again.

---

## KA-004 — Documentation Guidelines

**Name:** `docs/documentation-guidelines.md`

**Purpose:** Define how project documentation should be written and maintained.

**Scope:** Documentation quality and structure.

**Depends On:**

* engineering principles;
* practices.

**Enables:**

* handbook;
* ADRs;
* implementation plan;
* README;
* CLAUDE.md files;
* generated prompts.

**Audience:**

* developer;
* coding agents.

**Intent:**

Ensure that documentation remains useful to a future developer rather than becoming a collection of stale notes.

**Content Requirements:**

* one job per document;
* appropriate abstraction level;
* avoid duplicating authoritative information;
* link rather than duplicate where practical;
* distinguish decisions from facts;
* distinguish stable knowledge from temporary planning;
* explain enough context to make documents understandable independently;
* preserve rationale where it matters;
* update affected documentation when decisions change;
* avoid unnecessary metadata;
* Definition of Done for documentation.

**Documentation Definition of Done should include:**

* purpose is clear;
* scope is clear;
* content is current;
* terminology is consistent;
* relevant links work;
* no stale placeholders remain;
* document does not contradict authoritative project knowledge;
* examples/demos are present where appropriate;
* generated content is not manually modified if a generator exists.

**Status:** `draft`

---

## KA-005 — Glossary

**Name:** `docs/glossary.md`

**Purpose:** Define project-specific terminology.

**Scope:** Terms whose ambiguity could cause misunderstanding.

**Depends On:**

* engineering principles;
* capability map terminology.

**Enables:**

* handbook;
* ADRs;
* implementation plan;
* prompts;
* onboarding.

**Audience:**

* everyone working with the project.

**Intent:**

Prevent important concepts from acquiring inconsistent meanings over time.

**Content Requirements:**

Include definitions for terms such as:

* capability;
* field;
* phenomenon;
* process;
* solver;
* numerical method;
* scheme;
* flux;
* advection;
* diffusion;
* pressure–velocity coupling;
* timestepper;
* boundary condition;
* interface contract;
* upgrade path;
* golden demo;
* knowledge graph;
* capability map.

Definitions should be concise and link to deeper documents where appropriate.

**Definition of Done:**

* terms used repeatedly in the project have clear definitions;
* definitions agree with the handbook and architecture;
* no glossary entry attempts to replace substantive technical documentation.

**Status:** `draft`

---

# 7. Capability and Knowledge Architecture

---

## KA-006 — Capability Map

**Name:** `docs/planning/capability-map.md`

**Purpose:** Define what PyFlow is intended to be capable of independently of how those capabilities are implemented.

**Scope:** Capability decomposition only.

The initial map should stop before implementation decisions.

**Depends On:**

* project vision;
* glossary.

**Enables:**

* knowledge graph;
* implementation planning;
* handbook structure;
* capability-based browsing.

**Audience:**

* developer;
* future contributors;
* coding agents.

**Intent:**

Provide the conceptual territory of PyFlow without prematurely deciding how each capability will be implemented.

**Content Requirements:**

Initial branches:

1. Simulation
2. Physics
3. Analysis
4. Rendering
5. Planning System

The map should be decomposed approximately one or more levels where meaningful, but must stop before implementation decisions initially. Implementation decisions will be taken at the feature level and actioned at the task level.

### Simulation

Should describe things PyFlow intends to simulate, including relevant fields and processes.

Initial concepts include:

* velocity;
* mass;
* heat;
* temperature;
* density;
* humidity;
* convection;
* cloud formation;
* other fluid properties/processes as identified.

Simulation may also contain the conceptual need for solver families because the numerical methods available fundamentally constrain what can be simulated.

### Physics

Should describe:

* physical theory;
* governing equations;
* relationships between phenomena;
* assumptions;
* explanation of the equations being solved.

It is not intended to become a textbook containing exhaustive derivations, just enough information to aid in understanding the codebase.

### Analysis

Includes:

* derived quantities;
* inspection;
* measurement;
* comparison;
* statistical analysis;
* visual/quantitative interpretation.

### Rendering

Includes:

* visual representation of simulation state;
* progression from basic visualisation to high-quality rendering.

### Planning System

Describes capabilities required to maintain the project's knowledge and planning infrastructure.

This branch is deliberately separate from the CFD engine.

**Definition of Done:**

* every capability is implementation-agnostic;
* every capability can be described clearly in the handbook;
* the map does not encode premature architecture;
* capability decomposition stops before implementation details;
* the map can serve as a source for generated graph/tree views.

**Status:** `draft`

---

## KA-007 — Numerical Method Survey

**Name:** `docs/handbook/numerical-methods/overview.md`

**Purpose:** Survey established numerical methods capable of contributing to CFD and determine their domains, characteristics, compatibility and practical trade-offs.

**Scope:** Numerical-method territory rather than PyFlow implementation.

**Depends On:**

* capability map;
* scientific references;
* existing numerical-method descriptions.

**Enables:**

* FVM-first architecture decision;
* solver architecture;
* upgrade paths;
* handbook numerical-method entries.

**Intent:**

Ensure that PyFlow's numerical architecture is based on understanding the available methods rather than accidentally choosing the first familiar approach.

**Content Requirements:**

For relevant numerical method families:

* what equations they can address;
* physical domains;
* field representation;
* strengths;
* weaknesses;
* accuracy characteristics;
* stability characteristics;
* computational requirements;
* memory requirements;
* geometric flexibility;
* suitability for multiphysics;
* suitability for transient problems;
* suitability for different scales;
* compatibility with other methods;
* whether methods are alternatives, composable, nested or hybridisable;
* practical examples of established projects using them.

Methods considered include at least:

* FVM;
* FEM;
* FDM;
* spectral methods;
* LBM;
* SPH;
* particle approaches;
* other established CFD-relevant methods identified during the survey.

**Definition of Done:**

* major established CFD numerical families relevant to PyFlow's goals have been considered;
* their major properties are documented;
* compatibility relationships are clear;
* conclusions distinguish established practice from speculation.

**Status:** `draft`

---

## KA-008 — Numerical Method Compatibility View

**Name:** `docs/handbook/numerical-methods/compatibility.md`

**Purpose:** Describe which numerical method families can be combined and in what sense.

**Scope:** Compatibility relationships.

**Depends On:**

* numerical method survey.

**Enables:**

* choice of PyFlow primary architecture;
* future FEM extension;
* possible hybrid methods;
* architecture upgrade paths.

**Intent:**

Prevent PyFlow from choosing an architecture that makes future physically useful combinations unnecessarily difficult.

**Content Requirements:**

Distinguish:

* mutually exclusive alternatives;
* interchangeable implementations;
* methods that can coexist at different layers;
* coupled methods;
* hybrid approaches;
* post-processing-only combinations;
* methods requiring separate simulation engines.

The document should make clear that "can be used together" can mean several different things and should not collapse these into one compatibility label.

**Definition of Done:**

* major compatibility relationships relevant to PyFlow are documented;
* incompatibilities are explicit;
* future extension requirements are identified;
* no compatibility claim is made merely because two methods can theoretically coexist.

**Status:** `complete`

---

# 8. Physics Handbook

---

## KA-009 — Physics Handbook Structure

**Name:** `docs/handbook/physics/README.md`

**Purpose:** Define how physical knowledge is represented in the handbook.

**Scope:** Structure and conventions.

**Depends On:**

* capability map;
* documentation guidelines;
* glossary.

**Enables:**

* individual physics entries.

**Intent:**

Provide a stable place for future developers to understand both the physical phenomena PyFlow models and the equations governing them.

**Content Requirements:**

Physics entries should generally contain:

* phenomenon/process;
* physical interpretation;
* assumptions;
* governing equations;
* meaning of important terms;
* relationship to other phenomena;
* numerical implications;
* references to more detailed authoritative texts.

Derivations should be concise unless they are necessary for understanding.

**Definition of Done:**

* clearly separates physical knowledge from implementation;
* supports cross-referencing between phenomena;
* does not become an unnecessarily exhaustive textbook.

**Status:** `draft`

---

## KA-010 — Incompressible Flow

**Name:** `docs/handbook/physics/incompressible-flow.md`

**Purpose:** Describe the physical model underlying the initial CFD prototype.

**Depends On:**

* physics handbook structure;
* numerical-method survey.

**Enables:**

* MVP physics implementation;
* pressure–velocity coupling documentation.

**Intent:**

Give a future developer enough physical understanding to understand why the initial solver requires the chosen equations and pressure treatment.

**Content Requirements:**

* assumptions;
* conservation equations;
* continuity;
* momentum;
* pressure;
* relationship to velocity;
* incompressibility constraint;
* implications for numerical solution.

**Definition of Done:**

* equations are clearly explained;
* implementation choices are not embedded as physical facts;
* references to authoritative sources are provided.

**Status:** `draft`

---

## KA-011 — Heat Transport

**Name:** `docs/handbook/physics/heat-transfer.md`

**Purpose:** Describe heat transport as a future additional field/process.

**Depends On:**

* physics handbook structure;
* incompressible flow.

**Enables:**

* thermal extension planning.

**Intent:** Explain how temperature/heat becomes another transported field and what coupling it introduces.

**Content Requirements:**

* temperature;
* heat transport;
* conduction;
* convection;
* sources/sinks;
* coupling with fluid flow;
* relevant equations;
* numerical implications.

**Definition of Done:**

* physical model is clear;
* extension requirements are identifiable;
* no premature implementation decision is embedded.

**Status:** `draft`

---

## KA-012 — Density

**Name:** `docs/handbook/physics/density.md`

**Purpose:** Define density as a field/property and explain its physical role.

**Depends On:**

* physics handbook structure.

**Enables:**

* compressible-flow planning;
* buoyancy;
* multiphysics.

**Status:** `draft`

---

## KA-013 — Humidity and Species Transport

**Name:** `docs/handbook/physics/humidity.md`

**Purpose:** Describe humidity/species concentration as transported fields.

**Depends On:**

* heat transfer;
* physics handbook structure.

**Enables:**

* atmospheric/cloud-related extensions.

**Status:** `draft`

---

## KA-014 — Buoyancy

**Name:** `docs/handbook/physics/buoyancy.md`

**Purpose:** Describe buoyancy and its coupling to fluid motion.

**Depends On:**

* incompressible flow;
* density;
* heat transfer.

**Enables:**

* natural-convection simulation.

**Status:** `draft`

---

## KA-015 — Cloud Formation

**Name:** `docs/handbook/physics/cloud-formation.md`

**Purpose:** Describe the physical processes required to represent cloud formation as a future capability.

**Depends On:**

* humidity;
* heat transfer;
* density;
* buoyancy.

**Enables:**

* advanced atmospheric simulation planning.

**Status:** `draft`

---

# 9. Numerical Component Handbook

These documents explain the numerical concepts independently of their eventual PyFlow implementation.

---

## KA-016 — Finite Volume Method

**Name:** `docs/handbook/numerical-methods/fvm.md`

**Purpose:** Provide the canonical explanation of FVM, which is the selected initial numerical framework.

**Depends On:**

* numerical method survey;
* documentation guidelines.

**Enables:**

* FVM-first ADR;
* implementation architecture;
* mesh/field/operator documentation.

**Intent:**

A future developer should understand what FVM does, why PyFlow uses it initially, what its important concepts are, and where its limitations/extensions lie.

**Content Requirements:**

* control volumes;
* conservation;
* integral formulation;
* face fluxes;
* discretisation;
* cell-centred variables;
* gradients/divergence;
* boundary treatment;
* relation to governing equations;
* strengths and weaknesses;
* computational considerations;
* compatibility with FEM extension.

**Definition of Done:**

* comprehensive but not textbook-length;
* implementation-independent where possible;
* includes references;
* clearly explains concepts needed by later architecture documents.

**Status:** `draft`

---

## KA-017 — Meshes

**Name:** `docs/handbook/numerical-methods/meshes.md`

**Purpose:** Describe mesh concepts relevant to PyFlow.

**Depends On:**

* FVM.

**Enables:**

* mesh architecture;
* boundary representation;
* future geometry support.

**Content Requirements:**

* structured meshes;
* unstructured meshes;
* cells;
* faces;
* neighbours;
* geometry;
* internal boundaries;
* external boundaries;
* future arbitrary geometry;
* adaptive refinement.

**Definition of Done:**

* clearly separates conceptual mesh requirements from implementation;
* explains why structured mesh is suitable for MVP;
* identifies upgrade path to more general geometries.

**Status:** `draft`

---

## KA-018 — Collocated and Staggered Variables

**Name:** `docs/handbook/numerical-methods/variable-placement.md`

**Purpose:** Explain variable placement choices.

**Depends On:**

* FVM;
* pressure–velocity coupling.

**Enables:**

* variable representation architecture.

**Content Requirements:**

* collocated arrangement;
* staggered arrangement;
* advantages;
* disadvantages;
* pressure–velocity implications;
* numerical stability implications;
* upgrade path.

**Status:** `draft`

---

## KA-019 — Fluxes

**Name:** `docs/handbook/numerical-methods/fluxes.md`

**Purpose:** Explain numerical fluxes and their role in FVM.

**Depends On:**

* FVM;
* advection.

**Enables:**

* flux interface;
* advection schemes.

**Content Requirements:**

* physical flux;
* numerical flux;
* face flux;
* mass flux;
* relationship to advection;
* candidate flux formulations;
* computational cost;
* stability/accuracy implications.

**Status:** `draft`

---

## KA-020 — Advection

**Name:** `docs/handbook/numerical-methods/advection.md`

**Purpose:** Explain advection discretisation and the planned interchangeable advection strategy.

**Depends On:**

* FVM;
* fluxes.

**Enables:**

* advection interface;
* MVP advection;
* future scheme upgrades.

**Content Requirements:**

* upwind;
* central;
* higher-order schemes;
* TVD;
* numerical diffusion;
* stability;
* boundedness;
* computational cost;
* upgrade paths.

**Status:** `draft`

---

## KA-021 — Diffusion

**Name:** `docs/handbook/numerical-methods/diffusion.md`

**Purpose:** Explain diffusion discretisation.

**Depends On:**

* FVM.

**Enables:**

* diffusion interface;
* thermal and scalar transport.

**Content Requirements:**

* physical diffusion;
* gradient approximation;
* central differencing;
* non-orthogonal considerations;
* accuracy;
* stability;
* future upgrade options.

**Status:** `draft`

---

## KA-022 — Time Integration

**Name:** `docs/handbook/numerical-methods/time-integration.md`

**Purpose:** Explain explicit and implicit time integration and establish the conceptual upgrade path.

**Depends On:**

* FVM;
* implementation planning.

**Enables:**

* RK4 MVP;
* implicit future implementation.

**Content Requirements:**

* explicit integration;
* implicit integration;
* stability;
* CFL considerations;
* computational cost;
* memory;
* code complexity;
* RK4;
* future implicit methods.

**Definition of Done:**

The relative complexity, compute requirements and implementation implications of explicit versus implicit integration are clearly described.

**Status:** `draft`

---

## KA-023 — Pressure–Velocity Coupling

**Name:** `docs/handbook/numerical-methods/pressure-velocity-coupling.md`

**Purpose:** Explain how pressure and velocity are coupled in incompressible CFD.

**Depends On:**

* incompressible flow;
* FVM.

**Enables:**

* PISO implementation;
* pressure solver architecture.

**Content Requirements:**

* pressure correction;
* coupling problem;
* PISO;
* SIMPLE;
* SIMPLEC;
* relevant alternatives;
* convergence;
* computational cost;
* suitability for transient simulations.

**Status:** `draft`

---

## KA-024 — Linear Solvers

**Name:** `docs/handbook/numerical-methods/linear-solvers.md`

**Purpose:** Explain the role of linear-system solvers and identify candidates for interchangeable implementation.

**Depends On:**

* pressure–velocity coupling;
* FVM.

**Enables:**

* linear solver interface;
* MVP pressure solution;
* future solver selection.

**Content Requirements:**

* linear systems;
* iterative versus direct methods;
* Conjugate Gradient;
* BiCGSTAB;
* multigrid;
* preconditioning;
* convergence criteria;
* memory;
* computational cost;
* applicability.

**Status:** `draft`

---

## KA-025 — Boundary Conditions

**Name:** `docs/handbook/numerical-methods/boundary-conditions.md`

**Purpose:** Define the conceptual and numerical role of boundary conditions.

**Depends On:**

* FVM;
* physics.

**Enables:**

* MVP boundaries;
* arbitrary boundary composition;
* internal surfaces.

**Content Requirements:**

* Dirichlet;
* Neumann;
* periodic;
* Robin;
* internal boundaries;
* external boundaries;
* mixing boundary conditions;
* future arbitrary geometries;
* numerical implications.

**Status:** `draft`

---

# 10. Architecture Decisions

---

## KA-026 — ADR-0001: Knowledge/Capability Graph

**Name:** `adr/ADR-001-knowledge-graph.md`

**Purpose:** Record the decision to model project capabilities and relationships as a graph-like conceptual structure from which multiple views can be generated.

**Depends On:**

* engineering principles;
* capability map.

**Enables:**

* capability trees;
* knowledge graph views;
* dependency views;
* generated planning views.

**Intent:**

Record why PyFlow does not treat a single tree as the complete representation of its capabilities.

**Content Requirements:**

* context;
* problem;
* decision;
* capability graph concept;
* relationship types;
* distinction between capability and implementation;
* rationale;
* alternatives;
* consequences.

**Definition of Done:**

* decision is explicit;
* capability is distinguished from implementation;
* graph relationships are sufficiently defined to support future generated views;
* no unnecessary graph-theory complexity is introduced.

**Status:** `complete`

---

## KA-027 — ADR-0002: FVM First

**Name:** `adr/ADR-002-fvm-first.md`

**Purpose:** Record the decision to use FVM as the initial numerical framework.

**Depends On:**

* numerical method survey;
* numerical compatibility analysis.

**Enables:**

* engine architecture;
* implementation plan;
* MVP.

**Intent:**

Record why FVM provides the best initial balance between generality, conservation, established practice and future extensibility.

**Content Requirements:**

* alternatives;
* comparison;
* decision;
* FEM extension requirement;
* practical evidence;
* consequences;
* reversibility/upgrade path.

**Status:** `complete`

---

## KA-028 — ADR-0003: Modular Numerical Strategies

**Name:** `adr/ADR-003-modular-numerical-strategies.md`

**Purpose:** Record the architectural decision that numerical components should expose uniform/compatible interfaces and be replaceable independently.

**Depends On:**

* FVM-first decision;
* engineering principles;
* implementation plan.

**Enables:**

* component architecture;
* configuration;
* upgrade paths.

**Intent:**

Make explicit that numerical method choice is a construction/configuration concern rather than something embedded in the timestep implementation.

**Content Requirements:**

* strategy boundaries;
* interfaces;
* construction versus execution;
* replacement;
* configuration;
* upgrade path;
* consequences.

**Status:** `complete`

---

# 11. Implementation Architecture Knowledge

---

## KA-029 — Engine Architecture

**Name:** `docs/architecture/engine.md`

**Purpose:** Describe the conceptual architecture of the CFD engine.

**Depends On:**

* FVM-first ADR;
* modular strategies ADR;
* numerical component handbook.

**Enables:**

* implementation plan;
* Stage 0;
* prototype implementation.

**Intent:**

Provide a future developer with a clear conceptual map of the engine before looking at individual implementation files.

**Content Requirements:**

Initial conceptual layers:

```text
Mesh
Variables
Flux
Advection
Diffusion
Time Integration
Pressure–Velocity Coupling
Linear Solvers
Boundary Conditions
```

The architecture should explain that:

* each layer has a contract;
* implementations are replaceable;
* the timestepper depends on contracts rather than concrete schemes;
* construction selects implementations;
* execution operates through those contracts.

**Status:** `draft`

---

## KA-030 — Interface Contract Definitions

**Name:** `docs/architecture/icds.md`

**Purpose:** Define the user-facing interfaces/contracts by which PyFlow's configurable simulation components are selected and described.

**Depends On:**

* engine architecture;
* implementation plan.

**Enables:**

* implementation;
* configuration;
* UI labelling;
* future plugin/component discovery.

**Important Scope Decision:**

The primary ICDs are the interfaces exposed to users/configuration rather than every internal Python interface.

Internal interfaces may be documented where useful, but they should not become a documentation exercise for its own sake.

**Intent:**

Define the stable conceptual contract a user relies upon when choosing and composing numerical components.

**Content Requirements:**

For each user-configurable component:

* what it represents;
* what choices exist;
* what configuration controls;
* compatibility requirements;
* expected behaviour;
* limitations.

Potential later internal contracts include:

* mesh;
* field;
* flux;
* advection;
* diffusion;
* timestepper;
* pressure coupling;
* linear solver;
* boundary condition.

**Status:** `draft`

---

# 12. MVP and Upgrade Paths

---

## KA-031 — MVP Definition

**Name:** `docs/implementation/mvp.md`

**Purpose:** Define the minimum complete PyFlow that establishes the architecture and produces a useful simulation.

**Depends On:**

* capability map;
* FVM-first ADR;
* engine architecture;
* numerical component knowledge.

**Enables:**

* implementation plan;
* Stage 1 implementation.

**Intent:**

Define a deliberately small but complete PyFlow rather than a collection of partially implemented numerical components.

**MVP Components:**

* structured 2D mesh;
* collocated variables;
* simplest reasonable flux treatment;
* simplest reasonable advection;
* simplest reasonable diffusion;
* RK4 time integration;
* PISO pressure–velocity coupling;
* simple linear solver;
* Dirichlet boundary conditions;
* Neumann boundary conditions;
* periodic boundary conditions where practical;
* 2D air-current simulation;
* visualisation of the resulting flow.

**Non-negotiable condition:**

The MVP must produce a working simulation.

**Definition of Done:**

* simulation runs end-to-end;
* physical fields evolve;
* boundary conditions operate;
* pressure/velocity coupling works;
* numerical solution is measurable;
* visualisation shows the result;
* golden demo exists;
* documentation describes the implemented functionality;
* tests verify the core behaviour.

**Status:** `draft`

---

## KA-032 — Upgrade Paths

**Name:** `docs/implementation/upgrade-paths.md`

**Purpose:** Define how each MVP numerical component can later be replaced or extended.

**Depends On:**

* MVP definition;
* engine architecture;
* numerical component handbook;
* ICDs.

**Enables:**

* chronological implementation roadmap;
* future work planning.

**Intent:**

Make the MVP intentionally simple without allowing simplicity to become architectural dead-end.

**Upgrade paths include:**

### Mesh

Structured 2D → structured 3D → unstructured → arbitrary geometry → adaptive refinement.

### Variables

Collocated → alternative placement schemes where required.

### Flux

Simple flux → more sophisticated formulations.

### Advection

Simple upwind → central/higher-order → TVD/other bounded schemes.

### Diffusion

Simple central formulation → improved geometric/non-orthogonal handling.

### Time Integration

RK4 → alternative explicit schemes → implicit integration.

### Pressure–Velocity Coupling

PISO → SIMPLE/SIMPLEC/other appropriate strategies.

### Linear Solvers

Simple iterative solver → BiCGSTAB → multigrid/preconditioned methods.

### Boundary Conditions

Basic edge boundaries → mixed conditions → internal boundaries → arbitrary surfaces/geometries.

### Physics

Velocity/flow → heat → density/buoyancy → humidity/species → cloud formation → additional fields.

### Numerical Framework

FVM → future FEM-compatible architecture.

### Physics Scope

CFD → broader multiphysics, potentially including electromagnetic phenomena, without requiring the initial implementation to support them.

**Definition of Done:**

* each major MVP component has an identifiable upgrade path;
* upgrade does not require redesigning unrelated components;
* upgrade boundaries correspond to interfaces;
* complexity and motivation are recorded where useful.

**Status:** `draft`

---

# 13. Implementation Plan

---

## KA-033 — Master Implementation Plan

**Name:** `docs/planning/implementation-plan.md`

**Purpose:** Define the chronological path from an empty repository to a fully realised modular CFD engine.

**Depends On:**

* capability map;
* MVP definition;
* upgrade paths;
* engine architecture;
* ICDs.

**Enables:**

* implementation work;
* release planning;
* task generation.

**Intent:**

A future developer should be able to stop development for months, return to the repository, and determine what should be implemented next without reconstructing the project from memory.

**Required Structure:**

Top-level:

```text
# List of Tasks
```

Each task should link to a comprehensive description containing:

* purpose;
* dependencies;
* artefacts produced;
* implementation;
* measurable verification conditions;
* definition of done.

The plan should be chronological.

The initial implementation should use the simplest reasonable implementation for every layer simultaneously.

The roadmap should then provide concrete upgrade paths.

**Non-negotiable rule:**

After Stage 0, every stage must leave PyFlow with a working
demonstration. (This read "a working simulation" until 2026-08-22.
P-004, `docs/engineering-principles.md`, is the authoritative wording
and says demonstration; `README.md` corrected its own copy on
2026-08-21.)

**Stage progression:**

**Superseded 2026-08-22 -- the three bullets below describe a stage
scheme the project does not use**, and this document's own maintenance
note ("a spec that describes a repository which does not exist is worse
than no spec") is the reason to say so rather than leave them. They were
written before `docs/planning/roadmap.md` existed, when the plan was
three stages. The roadmap now defines fourteen (Stage 0 through Stage
13), Stage 1 is *Representing Space* and Stage 2 is *Representing
Fields*, and the "first working 2D air-current simulation" below is
Stage 5, the MVP. `docs/planning/implementation-plan.md` -- the artifact
KA-033 specifies -- carries the Capability Level view, and
`roadmap.md` the Stage view; neither is structured as these bullets ask.

Preserved as written, because they record what the plan was:

* Stage 0 — Infrastructure and repository foundations.
* Stage 1 — First working 2D air-current simulation.
* Stage 2 — Visualisation/complete thin slice.
* Subsequent stages — independently upgrade and extend numerical capabilities while maintaining a working simulation.

For the current progression, read `docs/planning/roadmap.md`'s "Stages
and Capability Levels" table, which is authoritative for both axes and
records every renumbering the project has made.

**Status:** `draft`

---

## KA-034 — Stage 0 Specification

**Name:** ~~`docs/implementation/stages/stage-0.md`~~ — never created and
will not be. Superseded 2026-08-15; see the resolution note below. The
responsibility now sits with `docs/planning/roadmap.md` (the "Stage 0 —
Engineering Infrastructure" section) and `docs/planning/backlog.md`
(Part I, the ordered queue that executes it).

**Purpose:** Define repository and development infrastructure required before simulation implementation.

**Depends On:**

* master implementation plan;
* practices;
* documentation guidelines.

**Enables:**

* Stage 1 implementation.

**Content Requirements:**

Stage 0 includes at minimum:

* Python project setup using `uv`;
* repository/package skeleton;
* test framework;
* linting/formatting;
* type checking where adopted;
* documentation structure;
* basic CI;
* development commands;
* root CLAUDE.md;
* nested CLAUDE.md files;
* documentation guidelines;
* initial project tooling;
* baseline example/test conventions.

**Special task: CLAUDE.md hierarchy**

Every existing `CLAUDE.md` from the repository root down should receive concise essential local context/instructions.

Each file should:

* inherit higher-level instructions;
* contain only local additions;
* remain compact;
* tell an agent what matters in that directory;
* direct agents to report apparent violations of project rules.

**Definition of Done:**

* fresh checkout can be developed using documented commands;
* test suite executes;
* lint/format checks execute;
* CI executes;
* documentation structure exists;
* agents have sufficient local instructions;
* Stage 0 infrastructure is reproducible.

**Resolution (2026-08-15, maintainer's call): superseded.**

This artifact's *purpose* -- "define repository and development
infrastructure required before simulation implementation" -- is now
served by two documents that already exist:

* `docs/planning/roadmap.md`, "Stage 0 — Engineering Infrastructure",
  which specifies TASK-000..010 with Purpose / Dependencies / Artifacts /
  Implementation / Acceptance Criteria each, plus the Stage 0 Completion
  Criteria. This is the **specification**.
* `docs/planning/backlog.md` Part I, the ordered, dependency-respecting
  queue that executes it, with each item stating what it produces and how
  completion is checked. This is the **execution plan**.

Writing a separate `stage-0.md` would duplicate the first and compete
with it, against P-011 (single authoritative source), and the implied
`stages/` directory would set up a parallel structure competing with the
roadmap as Stages 1-12 arrive.

**Nothing from the Definition of Done above was dropped.** It was
compared against `roadmap.md`'s Stage 0 Completion Criteria before
retiring this entry. Five items were already covered. Two were stated
here but only *implied* there -- "CI executes" and "Stage 0
infrastructure is reproducible" -- and both have been added to
`roadmap.md`'s criteria explicitly, so the stricter reading survives the
retirement.

Note for future readers comparing the two: this entry's DoD is the
**weaker** of the two on documentation, requiring only that
"documentation structure exists", where `roadmap.md` requires a complete
first draft (fixed in 2026-08-15's A3 decision to mean: no file tracked
in `docs/repository-manifest.md` is empty). It is also silent on
rendering, where `roadmap.md` requires the engine to bootstrap into a
window. The roadmap's is the binding definition.

**Status:** `superseded`

---

# 14. Golden Demos

---

## KA-035 — Golden Demo Specification

**Name:** `docs/implementation/golden-demos.md`

**Purpose:** Define executable demonstrations that prove important PyFlow capabilities work end-to-end.

**Depends On:**

* MVP definition;
* implementation plan;
* documentation guidelines.

**Enables:**

* functional regression testing;
* demonstrations;
* onboarding;
* release verification.

**Intent:**

A golden demo should be both a useful demonstration and a functional test of a meaningful vertical slice.

**Initial golden demo:**

A 2D air-current simulation that:

* constructs the domain;
* configures the numerical components;
* executes timesteps;
* produces measurable velocity fields;
* renders the result.

Future demos should be added when new capabilities are implemented.

**Definition of Done:**

* executable;
* deterministic or appropriately controlled;
* verifies meaningful behaviour;
* produces useful visual output where applicable;
* documented;
* included in regression testing.

**Status:** `draft`

---

# 15. Dreams

---

## KA-036 — Dreams

**Name:** `docs/planning/dreams.md`

**Purpose:** Preserve interesting future possibilities without allowing them to contaminate the committed architecture or roadmap.

**Depends On:** None.

**Enables:**

* capture of speculative ideas;
* future planning.

**Intent:**

Prevent good ideas from being lost while making it explicit that they are not commitments.

**Potential topics include:**

* 3D simulation;
* arbitrary geometry;
* adaptive mesh refinement;
* advanced turbulence;
* multiphysics;
* electromagnetic fields;
* particle methods;
* hybrid Eulerian/Lagrangian approaches;
* GPU acceleration;
* distributed computing;
* advanced rendering;
* interactive simulation;
* atmospheric/cloud modelling.

**Definition of Done:**

* ideas are clearly speculative;
* no dream is accidentally represented as a project commitment;
* ideas can be promoted into the capability map or roadmap when justified.

**Status:** `draft`

---

# 16. Agent Guidance

---

## KA-037 — Root CLAUDE.md

**Name:** `CLAUDE.md`

**Purpose:** Give coding agents the minimum essential project-wide instructions.

**Depends On:**

* engineering principles;
* practices;
* documentation guidelines.

**Enables:**

* consistent agent behaviour.

**Intent:**

An agent entering the repository should understand the project's non-negotiable rules without consuming a large context window.

**Content Requirements:**

* read relevant documentation before changing it;
* preserve repository principles;
* use local CLAUDE.md files;
* report apparent violations of project rules;
* do not edit generated content directly;
* keep documentation current;
* respect working-simulation requirement;
* prefer existing interfaces over bypassing them;
* keep changes scoped.

**Definition of Done:**

* compact;
* actionable;
* does not duplicate the entire documentation system;
* directs agents to authoritative documents.

**Status:** `complete`

---

## KA-038 — Nested CLAUDE.md Files

**Name:** `CLAUDE.md` at appropriate directory levels.

**Purpose:** Provide local context without repeating global instructions.

**Depends On:**

* root CLAUDE.md.

**Enables:**

* context-efficient agent operation.

**Intent:**

Agents should receive progressively more specific context as they descend into the repository.

**Definition of Done:**

Every relevant directory has local instructions where those instructions materially improve correctness.

Each file:

* is concise;
* assumes inheritance from its parent;
* contains only local information;
* identifies important files/subsystems;
* identifies local validation requirements.

**Status:** `complete` (`docs/planning/backlog.md` E9, closed 2026-08-19).
This entry's own Definition of Done already said "where those
instructions materially improve correctness," not "at every leaf" --
E9's revised *Done when* only made that explicit: a directory with no
real content yet has nothing for local instructions to materially
improve on, so the generic placeholder is correct there, not a gap.

---

# 17. Prompt Architecture

---

## KA-039 — Prompt Global Context

**Name:** `prompts/global/project.md`

**Purpose:** Provide durable, project-wide context for document-generation agents.

**Depends On:**

* engineering principles;
* documentation guidelines;
* README/project description.

**Enables:**

* every document-generation prompt.

**Intent:**

A fresh agent with no conversation history should understand PyFlow's enduring purpose and philosophy.

**Content Requirements:**

Include:

* what PyFlow is;
* project vision;
* field-centric philosophy;
* institutional-memory philosophy;
* engineering principles;
* documentation philosophy;
* quality expectations;
* distinction between knowledge and implementation;
* instruction to rely on local context for current project state.

It should **not** contain:

* current numerical architecture;
* current stage;
* current implementation status;
* task-specific decisions.

Those belong to local/task context.

**Definition of Done:**

* stable across major implementation changes;
* sufficient to orient a fresh agent;
* does not encode temporary project state.

**Status:** `draft`

---

## KA-040 — Handbook Prompt Context

**Name:** `prompts/features/handbook.md`

**Purpose:** Define how handbook documents should be generated.

**Depends On:**

* documentation guidelines;
* handbook structure.

**Enables:**

* handbook task prompts.

**Intent:**

Tell an agent what role handbook knowledge plays and what quality of explanation is expected.

**Content Requirements:**

Handbook entries should:

* explain concepts;
* establish terminology;
* explain why concepts matter;
* describe relationships;
* distinguish theory from implementation;
* provide sufficient technical depth;
* avoid becoming exhaustive textbooks;
* link to authoritative deeper sources;
* identify numerical implications where relevant.

The handbook should be useful independently to a future developer.

**Definition of Done:**

* provides actionable writing guidance;
* does not repeat project-specific task requirements.

**Status:** `draft`

---

## KA-041 — ADR Prompt Context

**Name:** `prompts/features/adr.md`

**Purpose:** Define how ADRs should be generated.

**Depends On:**

* documentation guidelines;
* ADR-0001.

**Enables:**

* ADR task prompts.

**Intent:**

Ensure ADRs capture decisions and reasoning rather than becoming general technical essays.

**Content Requirements:**

ADRs should include:

* context;
* problem;
* decision;
* alternatives;
* rationale;
* consequences;
* reversibility where relevant.

They should record what was decided and why, not prescribe every implementation detail.

**Definition of Done:**

* concise;
* decision-oriented;
* explicit about alternatives and consequences.

**Status:** `draft`

---

## KA-042 — Implementation Plan Prompt Context

**Name:** `prompts/features/implementation-plan.md`

**Purpose:** Define how implementation-plan documents and tasks should be generated.

**Depends On:**

* implementation plan;
* documentation guidelines;
* engineering principles.

**Enables:**

* task prompts.

**Intent:**

Make implementation tasks sufficiently concrete that a fresh agent can execute them without conversation history.

**Content Requirements:**

Each task should describe:

* purpose;
* place in overall project;
* dependencies;
* artefacts;
* implementation approach;
* verification;
* Definition of Done;
* upgrade implications where relevant.

**Definition of Done:**

A task is executable by a competent developer without needing undocumented historical context.

**Status:** `draft`

---

## KA-043 — Agent Prompt Context

**Name:** `prompts/features/agents.md`

**Purpose:** Define how CLAUDE.md files should be generated.

**Depends On:**

* engineering principles;
* practices;
* documentation guidelines.

**Enables:**

* root/nested CLAUDE.md prompts.

**Intent:**

Produce compact, actionable agent guidance rather than duplicating the documentation system.

**Content Requirements:**

* inherited instructions;
* local scope;
* important commands/files;
* local validation;
* violations to report.

**Status:** `draft`

---

# 18. Prompt Task Specifications

The following task prompts should be generated only after the relevant global and feature contexts exist.

Initial task prompt set:

1. README
2. Engineering Principles
3. Practices
4. Documentation Guidelines
5. Glossary
6. Capability Map
7. Numerical Method Survey
8. Numerical Method Compatibility
9. Physics Handbook Structure
10. FVM Handbook Entry
11. Physics Entries
12. Numerical Component Handbook Entries
13. ADR-0001
14. ADR-0002
15. ADR-0003
16. Engine Architecture
17. ICDs
18. MVP Definition
19. Upgrade Paths
20. Implementation Plan
21. Stage 0
22. Golden Demos
23. Dreams
24. Root CLAUDE.md
25. Nested CLAUDE.md

Each task prompt should contain:

* global context include;
* relevant feature context include;
* task-specific context;
* intent;
* concrete requirements;
* output location;
* quality checklist;
* explicit instruction to preserve existing project decisions;
* explicit instruction to report apparent contradictions rather than silently inventing a resolution.

---

# 19. Dependency Relationships

The initial dependency structure is conceptually:

```text
Engineering Principles
        │
        ├──────────────┐
        ▼              ▼
Practices       Documentation Guidelines
        │              │
        ├──────┬───────┤
        │      │       │
        ▼      ▼       ▼
      README  ADRs   Handbook
        │      │       │
        └──────┴───────┤
                       ▼
                 Capability Map
                       │
                       ▼
              Numerical Method Survey
                       │
                       ▼
            Numerical Compatibility
                       │
              ┌────────┴────────┐
              ▼                 ▼
          ADR: FVM          Physics Handbook
              │
              ▼
      Modular Architecture
              │
       ┌──────┴───────┐
       ▼              ▼
      ICDs       Engine Architecture
       │              │
       └──────┬───────┘
              ▼
         MVP Definition
              │
              ▼
         Upgrade Paths
              │
              ▼
      Implementation Plan
              │
              ▼
            Stage 0
              │
              ▼
            Stage 1
              │
              ▼
       Working Simulation
              │
              ▼
       Visualisation Thin Slice
```

This is a **derived view**, not the source of truth.

The source of truth remains the flat artifact records above.

---

# 20. Planning Completion Criteria

**Read the checkboxes below as the original list, unticked, not as
current state** (clarified 2026-08-22, by a repository consistency
sweep). The planning phase they gate finished long ago: Stage 0 closed
against its own nine completion criteria on 2026-08-19, Stage 1 on
2026-08-21, Stage 2 on 2026-08-22, and the repository has an
implemented mesh, field and rendering stack with 337 tests behind it.
Nothing ever came back and ticked these forty-two boxes, so a fresh
agent reading this section cold would conclude that substantial
implementation should not yet have begun -- which is the exact trap
`docs/planning/backlog.md`'s Part III got a caveat for on 2026-08-21,
in a document with the same problem. This one did not get one until now.

They are left unticked rather than ticked in bulk, for the reason this
repository leaves closed criteria alone everywhere else: ticking
forty-two boxes in a single pass would assert forty-two verifications
that did not happen. Several are also judgement calls that deserve a
real reading rather than a mark ("FEM extension remains architecturally
plausible", "Capability map is complete to the agreed abstraction
boundary"), and at least one is knowably still open -- "First-pass task
prompts exist for all planning documents" was never true and
`prompts/` has not grown since Stage 0.

**Where the live version of this now lives:** `docs/planning/roadmap.md`
carries per-stage Completion Criteria with a per-criterion exit audit at
each stage boundary (`docs/practices.md`, "A stage gets completion
criteria before its first task"), which is the mechanism that replaced
this one in practice. Treat §20 as the record of what the planning phase
set out to achieve, and the roadmap as what is actually gated on.

A reconciliation pass -- reading each box against the current
repository and recording the answer -- is on `docs/planning/backlog.md`,
alongside the related KA `Status:` field mismatches found in the
2026-08-19 F2 sweep.

The initial planning phase is complete when:

### Project understanding

* [ ] README exists and accurately describes PyFlow.
* [ ] Engineering principles are documented.
* [ ] Practices are documented.
* [ ] Documentation guidelines are documented.
* [ ] Glossary contains the important terminology.

### Capability understanding

* [ ] Capability map is complete to the agreed abstraction boundary.
* [ ] Capabilities remain implementation-agnostic.
* [ ] Future/dream capabilities are separated from commitments.

### Scientific understanding

* [ ] Relevant CFD numerical method families have been surveyed.
* [ ] Physical domains are mapped to numerical-method capabilities.
* [ ] Method compatibility is understood.
* [ ] Compute/complexity trade-offs are documented.
* [ ] FVM-first reasoning is recorded.

### Architecture

* [ ] Modular numerical-layer architecture is documented.
* [ ] Component boundaries are understood.
* [ ] Replaceable interfaces are defined conceptually.
* [ ] User-facing ICDs are defined sufficiently for implementation.
* [ ] Construction is separated from execution.
* [ ] Configuration can select numerical implementations.

### MVP

* [ ] MVP is explicitly defined.
* [ ] Every MVP layer has a simplest reasonable implementation.
* [ ] MVP produces a working 2D air-current simulation.
* [ ] Visualisation produces a complete thin slice.
* [ ] Golden demo is defined.

### Upgrade planning

* [ ] Every major MVP component has a documented upgrade path.
* [ ] Upgrade paths do not require unnecessary architectural churn.
* [ ] FEM extension remains architecturally plausible.
* [ ] Future multiphysics remains architecturally plausible.

### Implementation

* [ ] Chronological implementation plan exists.
* [ ] Every task has dependencies.
* [ ] Every task identifies produced artefacts.
* [ ] Every task has measurable verification.
* [ ] Every task has an explicit Definition of Done.
* [ ] Stage 0 is fully specified.
* [ ] Stage 1 is sufficiently specified to begin implementation.

### Agent support

* [ ] Root CLAUDE.md exists.
* [ ] Relevant nested CLAUDE.md files exist.
* [ ] Agent instructions are compact.
* [ ] Apparent project-rule violations are explicitly reportable.
* [ ] Prompt global context exists.
* [ ] Feature prompt contexts exist.
* [ ] First-pass task prompts exist for all planning documents.

---

# 21. Final Planning Gate

**Passed, and nothing recorded it until 2026-08-22.** Substantial
implementation began at TASK-011 on 2026-08-20 and three stages have
since closed against their own criteria, so this gate was cleared in
practice without anyone writing down that it had been -- the same
failure `docs/planning/roadmap.md`'s Stage 1 entry records for that
stage ("nothing anywhere recorded that Stage 1 was finished at all"),
one level up. The question below is still the right question, and the
honest answer today is **yes**, on the evidence of Stage 0's own exit
audit (`roadmap.md`, "Status as of 2026-08-19") and the two stage
audits after it. See §20 above for what is left unreconciled.

Before beginning substantial implementation, perform one final check:

> Can a competent developer who has never participated in the preceding design conversations read the repository and determine what PyFlow is, what it is intended to simulate, why the chosen numerical framework was selected, what the MVP is, how its components fit together, what should be implemented first, how success will be measured, and where each component can be upgraded?

If the answer is **yes**, planning has succeeded.

If the answer is **no**, identify the missing knowledge artifact and add it to this document before beginning implementation.

The objective is not to eliminate uncertainty.

The objective is to ensure that uncertainty is **explicit, located, and recoverable** rather than hidden in someone's memory.
