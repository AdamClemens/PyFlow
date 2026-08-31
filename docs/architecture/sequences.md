# Runtime Sequences

`overview.md` answers "what are the pieces." `engine.md` answers "why is
each layer independently replaceable." Neither answers "in what order do
things actually happen when PyFlow runs" -- that is this document's only
job. Read it after `overview.md`, alongside `engine.md` and `rendering.md`
for the pieces each sequence below moves through.

Four sequences, each grounded directly in the module that implements it,
not re-derived from general engine-design knowledge. Where a sequence
covers something not yet built, that subsection is marked **Planned** and
says so plainly, rather than describing a mechanism that doesn't exist yet
as though it did.

---

## 1. Simulation Setup

What happens between a user running `pyflow run` (or calling `bootstrap()`
directly, PyFlow's actual public API -- see `overview.md`) and a window
appearing on screen. Matches `src/pyflow/bootstrap.py`'s `bootstrap()`
exactly, including the two orderings that matter: `assemble_numerics` runs
on every call regardless of whether the run needs it yet, and
`fit_camera_to_bounds` must run before `apply_camera_config` so configured
zoom/pan apply on top of the base framing, not the other way round.

```mermaid
sequenceDiagram
    participant Caller
    participant bootstrap as bootstrap()
    participant Config as configuration.load_config
    participant Window as RenderWindow
    participant Assembly as assemble_numerics
    participant Mesh as StructuredCartesianMesh
    participant Viz as mesh_visualization /<br/>field_visualization

    Caller->>bootstrap: bootstrap(config_path, backend=...)
    bootstrap->>Config: load_config(config_path)
    Config-->>bootstrap: PyFlowConfig
    opt backend override given
        bootstrap->>bootstrap: config.rendering.backend = backend<br/>config.rendering.validate()
    end
    bootstrap->>bootstrap: configure_logging(config.logging)
    bootstrap->>Window: RenderWindow(config.rendering)
    Window-->>bootstrap: window (canvas, renderer, scene, camera)
    bootstrap->>Assembly: assemble_numerics(config.numerics, config.fluid.diffusion_coefficient)
    Assembly-->>bootstrap: AssembledNumerics (6 live instances)
    bootstrap->>Window: window.assembled_numerics = ...
    alt show_mesh or a field_display pattern is configured
        bootstrap->>Mesh: StructuredCartesianMesh.from_config(config.mesh)
        Mesh-->>bootstrap: mesh
        opt show_mesh
            bootstrap->>Viz: build_mesh_grid_line(mesh, grid_color)
            bootstrap->>Window: scene.add(grid_line)
        end
        opt scalar_pattern or vector_pattern configured
            bootstrap->>Viz: build_scalar_field_mesh / build_vector_field_arrows / build_field_legend
            bootstrap->>Window: scene.add(...)
        end
        bootstrap->>Viz: fit_camera_to_bounds(camera, bounds)
    end
    bootstrap->>Window: apply_camera_config()
    bootstrap->>Window: window.run(max_frames=...)
    Window-->>Caller: window (returned once run() exits)
```

Grounded in `bootstrap.py:150-220`. `RenderWindow` itself constructs
nothing simulation-related (`rendering/CLAUDE.md`'s "no simulation
content" scope) -- every arrow into `Assembly`/`Mesh`/`Viz` above is
`bootstrap()`'s own composition, not something `RenderWindow` does on its
own.

---

## 2. Timestep Loop Operations

### Built today

`engine/simulation.py`'s `step()` is the mechanism `engine.md`'s Flux
entry describes ("jointly compute[d]" by the Advection/Diffusion/
Gradient/Divergence interfaces) but assigns to no module. It is real,
unit-tested (`tests/unit/test_simulation.py`), and callable directly --
the sequence below is exactly what it does.

```mermaid
sequenceDiagram
    participant Caller
    participant Step as simulation.step()
    participant Adv as numerics.advection
    participant Diff as numerics.diffusion
    participant Src as numerics.source_term
    participant Accum as accumulate_flux_to_cells
    participant TI as numerics.time_integration

    Caller->>Step: step(fields, velocity, numerics, dt)
    Step->>Step: verify every field shares velocity's mesh<br/>(raises MismatchedMeshError otherwise)
    loop for each field in fields
        Step->>Adv: advection.flux(field, velocity)
        Adv-->>Step: advective_flux (per face)
        Step->>Diff: diffusion.flux(field)
        Diff-->>Step: diffusive_flux (per face)
        Step->>Src: source_term.source(field, state)
        Src-->>Step: source (per cell)
        Step->>Accum: accumulate_flux_to_cells(mesh, diffusive_flux - advective_flux)
        Accum-->>Step: flux derivative (per cell)
        Step->>Step: derivative = flux derivative + source
    end
    Step->>TI: time_integration.advance(fields, derivatives, dt)
    TI-->>Step: new fields (fields/velocity/numerics untouched)
    Step-->>Caller: new fields
```

The advective term is *subtracted* and the diffusive term *added* when
building each cell's derivative -- `step()`'s own docstring resolves this
directly from the FVM conservation equation
(`docs/handbook/numerical-methods/fvm.md`): `d/dt \int_V \rho\phi\,dV =
-\oint_{\partial V} \rho\phi\mathbf{u}\cdot\mathbf{n}\,dA + \oint_{\partial V}
\Gamma\nabla\phi\cdot\mathbf{n}\,dA + \text{source}` -- quoted directly
from `simulation.py`'s own `step()` docstring, not re-derived.

**The `+ source` on the end of that equation became a real call in
Stage 6** (TASK-035, 2026-08-30): `numerics.source_term.source(field,
state)`, added to every field's own derivative, is where a Boussinesq
body force reaches momentum (`src/pyflow/physics/buoyancy.py`,
`adr/ADR-010-source-term-state.md`). It is passed the whole `state`
this evaluation is already computing over, not only the field being
advanced, precisely so a term can read a *different* field's own
current value than the one it contributes to -- which is what a
buoyancy term does, reading temperature and contributing to
`velocity.1`. **The diagram above did not show this call until
2026-08-31, when this stage's exit audit found it**: the same defect,
in the same document, that the *Stage 5* exit audit found and wrote
`docs/practices.md`'s fourth grep against ("for each capability a stage
adds, name the document that would have to describe it if it had
existed from the start"). A run naming no source term
(`numerics.source_term: "none"`, the default) gets an exact zero from
that call and advances identically to before it existed.

`accumulate_flux_to_cells`
is the discrete Gauss theorem: a face's owner cell sees its value with
sign `+1`, its neighbour (if any) with sign `-1`
(`Mesh.face_normal`'s own canonical direction), summed and divided by
cell volume. `step()` never branches on `Mesh.is_boundary_face` anywhere
in its own code -- a concrete Advection/Diffusion scheme is constructed
with the boundary conditions it needs and handles a boundary face itself,
so the orchestrator above doesn't need to know which faces are boundary
faces at all.

Every call into `Adv`/`Diff`/`TI` above goes through the *contract*, never
a concrete scheme by name -- `engine.md`'s Core Principle ("the
timestepper doesn't care which one it has") is what makes this sequence
identical regardless of which of the six `adr/ADR-003-modular-numerical-
strategies.md` components `assemble_numerics` resolved. See `engine.md`
for why that's true and what it buys; this document only shows that it's
true, in sequence.

### Built today: driving `step()` from a live run

**Built 2026-08-28, TASK-030 -- Stage 4's own Passive Scalar Transport
golden demo.** `bootstrap.py`'s `_add_declared_field_transport` is the
caller Section 2's earlier "Planned" note above described in advance: it
builds one `ScalarField` per `config.fields` declaration and a
prescribed velocity from `config.simulation`, renders the first frame,
and returns a closure that `RenderWindow.run(on_frame=...)`
(`rendering/window.py`) calls once per rendered frame thereafter -- the
exact seam that subsection's own docstring anticipated ("exactly what a
future real-time simulation loop will need").

**This function was called `_add_passive_scalar_transport`, and
transported exactly one field hardcoded as `"tracer"`, until TASK-042
(Stage 6, 2026-08-30) generalised it to `config.fields`' own
declarations.** This document still used the old name in four places --
including as a participant in the diagram below -- until 2026-08-31,
when this stage's exit audit grepped for it: `make check-references`
resolves repository *paths* named in prose, not function names, so a
renamed helper goes stale here behind a green gate.

**When `simulation.velocity_solved` is set, this same closure calls
`navier_stokes_step` rather than the `step()` shown below** (Stage 5
exit audit, 2026-08-29) -- Section 2's third subsection is that
sequence. The diagram here is the prescribed-velocity path, which is
what the demo it was drawn for configures.

```mermaid
sequenceDiagram
    participant bootstrap as bootstrap()
    participant Add as _add_declared_field_transport
    participant Window as RenderWindow.run()
    participant Advance as on_frame closure
    participant Step as simulation.step()
    participant Viz as field_visualization

    bootstrap->>Add: _add_declared_field_transport(window, mesh, config)
    Add->>Viz: build_scalar_field_mesh(scalar_field, colors)
    Viz-->>Add: gfx.Mesh (frame 0)
    Add->>Window: scene.add(rendered_object)
    Add-->>bootstrap: on_frame closure
    bootstrap->>Window: window.run(max_frames, on_frame)
    loop each rendered frame
        Window->>Advance: on_frame()
        Advance->>Step: step(state, velocity, numerics, dt)
        Step-->>Advance: new state
        Advance->>Window: simulation_fields = new state
        Advance->>Viz: scalar_field_colors(new render_field, low, high, range)
        Viz-->>Advance: per-cell RGBA colors
        Advance->>Window: scene.remove(old object); scene.add(new object)
    end
```

**Each frame's rendered `gfx.Mesh` is rebuilt from scratch, not mutated
in place.** `build_scalar_field_mesh`/`scalar_field_colors` are already
proven correct (TASK-017); an in-place colour-buffer mutation
(`geometry.colors.data[:] = ...`) would be new, unverified pygfx-API
surface for a small win on a small demo mesh -- a deliberate, recorded
deferral (`docs/planning/roadmap.md` TASK-030's own Design decision), not
an oversight. `gfx.Scene.remove` was verified directly (add then remove
leaves `len(scene.children) == 0`) before being relied on.

`RenderWindow.simulation_fields` is what lets a caller -- the golden
demo's own regression test, most directly -- read back the real field
state a rendered frame came from, the same "`bootstrap()` populates it,
`RenderWindow` itself holds no simulation content" shape
`assembled_numerics` already established (Section 3, below).

### Built today: one incompressible Navier-Stokes timestep

**Built 2026-08-29, TASK-034 -- Stage 5's own assembled timestep, and
the sequence the two above are no longer the whole of.** Everything
before this subsection describes `step()`, which advances transported
fields through a velocity it treats as external input. A run that
*solves* for velocity (`simulation.velocity_solved: true`) does not call
`step()` from `on_frame` at all -- it calls
`simulation.navier_stokes_step`, which calls `step()` as its own
momentum predictor and then corrects the result.

**Added by the Stage 5 exit audit, not by TASK-034 itself.** This
document's only stated job is "in what order do things actually happen
when PyFlow runs", and for a full day after the coupled solve landed it
contained no mention of pressure, predictor or corrector -- the exact
drift its own Maintenance section below asks a reader to grep for.

```mermaid
sequenceDiagram
    participant Caller
    participant NS as simulation.navier_stokes_step()
    participant Step as simulation.step()
    participant PC as numerics.pressure_coupling
    participant LS as numerics.linear_solver

    Caller->>NS: navier_stokes_step(fields, velocity_field_name, numerics, dt)
    NS->>NS: assemble u/v components into a VectorField
    Note over NS,Step: Predictor -- momentum advanced with no pressure term
    NS->>Step: step(fields, current_velocity, numerics, dt)
    Step-->>NS: predicted fields (velocity components and any scalars alike)
    NS->>NS: reassemble the predicted components: provisional velocity
    Note over NS,LS: Corrector -- a loop, not a single pass (TASK-033)
    NS->>PC: correct(provisional_velocity, dt)
    loop until max divergence <= tolerance, else raise
        PC->>PC: Rhie-Chow-corrected divergence, recorded in last_divergence_history
        PC->>LS: solve(poisson_matrix, -divergence / dt)
        LS-->>PC: pressure correction
        PC->>PC: pressure += correction; velocity -= dt * grad(correction)
    end
    PC-->>NS: (corrected_velocity, pressure)
    NS-->>Caller: NavierStokesStepResult(fields, provisional, corrected, pressure)
```

**Three things this sequence makes visible that prose does not.**
`step()` is reused unchanged as the momentum predictor -- velocity's own
components go through the same `AdvectionScheme`/`DiffusionScheme`/
`TimeIntegrator` path a transported scalar does, which is Stage 5
Completion Criterion 1's whole claim. The corrector is a *loop* whose
per-pass divergence is recorded, not a single correction (`PISO`,
genuinely multi-pass since TASK-033). And `numerics.linear_solver`
reaches the timestep only through `numerics.pressure_coupling` -- never
called directly by `navier_stokes_step`, which is why proving the
*configured* solver is the one that runs needed its own substitution
scenario (`tests/features/navier_stokes_timestep.feature`, added by that
stage's exit audit).

Pressure is never a member of `fields`: `step()` raises
`PressureFieldTransportError` if a `PressureField` appears there, and
`navier_stokes_step` returns the solved pressure alongside the fields
rather than among them. That is Criterion 2's "solved from the
constraint, not transported", expressed structurally.

The live-run wiring is `bootstrap.py`'s `_add_solved_velocity_rendering`
-- the same `on_frame` seam `_add_declared_field_transport` attaches to
above, calling `navier_stokes_step` once per rendered frame and redrawing
the corrected velocity as arrows (`examples/golden-demos/
lid_driven_cavity.yaml`).

---

## 3. Data Flow: Where State Lives

### Built today

Simulation state exists only as objects held in process memory for the
lifetime of one `bootstrap()` call -- there is nothing else to a "data
flow" today beyond what's constructed and where it's referenced from.

```mermaid
sequenceDiagram
    participant bootstrap as bootstrap()
    participant Mesh as StructuredCartesianMesh
    participant Field as ScalarField / VectorField
    participant Numerics as AssembledNumerics
    participant Window as RenderWindow

    bootstrap->>Mesh: StructuredCartesianMesh.from_config(config.mesh)
    Note over Mesh: cell/face geometry, no field values
    bootstrap->>Field: ScalarField(mesh, name, initial_value=...)
    Note over Field: CollocatedField allocates a<br/>torch.float64 tensor, (num_cells, *component_shape)
    bootstrap->>Numerics: assemble_numerics(config.numerics, config.fluid.diffusion_coefficient)
    Note over Numerics: 6 live scheme instances,<br/>constructed once, held for the run
    bootstrap->>Window: window.scene.add(...), window.assembled_numerics = ...
    Note over Window: process memory only --<br/>nothing here is written to disk
```

Grounded in `collocated_field.py` (`CollocatedField.__init__` allocates
the tensor) and `assembly.py` (`AssembledNumerics` construction). Closing
the window or exiting the process discards all of it -- verified by
reading `src/pyflow` for any save/load/checkpoint/persistence code: there
is none. The only thing PyFlow reads or writes on disk today is YAML
*configuration* (`configuration/loader.py`), which is input, not
simulation output.

### Planned: checkpointing

**Not built yet, and not an open design question either.**
`docs/planning/roadmap.md`'s TASK-034 entry already records the intended
shape, raised by the maintainer while scoping TASK-013's live zoom/pan and
deliberately deferred until a real timestepping loop exists to pause:

> checkpoint-based -- periodic full-state snapshots plus deterministic
> replay between them, not storing every frame, which gets expensive fast
> for field-rich simulations

This leans on the determinism `docs/implementation/golden-demos.md`'s
Definition of Done already requires of every demo: replay-from-checkpoint
is only cheap if re-running the same steps reproduces the same state,
which is a standing requirement already, not a new one checkpointing would
add. That requirement is now *checked* rather than only stated, in two
places: `navier_stokes_timestep.feature`'s own determinism scenario
(bit-identical corrected velocity and pressure across two runs) and
`lid_driven_cavity.feature`'s own, through the real demo.

**Re-anchored 2026-08-29 by the Stage 5 exit audit.** This paragraph
used to end "Update this subsection with the real sequence once
**TASK-034** lands". TASK-034 landed on 2026-08-29 and **deliberately
did not build checkpointing** -- Stage 5 Completion Criterion 4 excludes
it in as many words ("Checkpoint/pause/rewind is explicitly not a
criterion of this stage", with this placeholder named as what stays
accurate if it is not built). So nothing is owed on the content, and the
placeholder above is still true; what was not true any longer was its
own trigger, which pointed at a task that had already closed. **There is
no task assigned to build this today.** It reactivates when one is:
whoever writes it re-reads this subsection in the same change, the same
obligation TASK-030 and TASK-034 both carried on their own roadmap
entries.

---

## 4. Rendering Pipeline

How mesh/field data becomes pixels. Two phases, and the boundary between
them matters: geometry is built and added to the scene *once*, during
setup; the render loop then redraws the same scene every frame regardless
of whether its contents changed.

```mermaid
sequenceDiagram
    participant bootstrap as bootstrap()
    participant Viz as field_visualization
    participant Window as RenderWindow
    participant Renderer as pygfx.WgpuRenderer

    Note over bootstrap,Viz: Setup (once)
    bootstrap->>Viz: scalar_field_colors(scalar_field, low, high, range)
    Viz-->>bootstrap: per-cell RGBA colors
    bootstrap->>Viz: build_scalar_field_mesh(scalar_field, colors)
    Viz-->>bootstrap: gfx.Mesh (one quad per cell)
    bootstrap->>Viz: build_vector_field_arrows(vector_field, color, scale)
    Viz-->>bootstrap: gfx.Line (one segment per non-zero cell)
    bootstrap->>Window: scene.add(mesh), scene.add(arrows), scene.add(legend)

    Note over Window,Renderer: Render loop (every frame)
    loop until window closes
        Window->>Renderer: renderer.render(scene, camera)
        Window->>Window: frame_count += 1
        opt on_frame callback given
            Window->>Window: on_frame()
        end
    end
```

Grounded in `field_visualization.py` (the four builder functions) and
`window.py`'s `_draw`/`run` (the render loop itself). Every function in
`field_visualization.py` takes a `Field`, never a `Field` plus a separate
`Mesh` argument -- a `Field` already carries its own mesh
(`field.mesh`), so there is no second reference for the two to drift out
of sync (`rendering/CLAUDE.md`'s Stage 2 exit-audit rule). See
`rendering.md`'s "The Layering" section for how the canvas backend
(`glfw` vs `offscreen`) is selected underneath `RenderWindow` -- this
diagram is unaffected by that choice either way.

**The `on_frame` hook drawn above is the same seam Section 2's Planned
subsection names.** Today its only real caller is the interactive-window
test suite (`tests/integration/test_interactive_window.py`), which
mutates `scene` between frames to prove distinct frames are actually
presented. Once TASK-030 wires a live timestep loop through it
(Section 2), this is also where updated field data will need to reach the
scene -- rebuilding (or updating in place) the `gfx.Mesh`/`gfx.Line`
objects this section builds, once per frame instead of once at setup.
Update this note alongside Section 2's when that lands.

---

## Maintenance

Written 2026-08-27, grounded directly in `src/pyflow/bootstrap.py`,
`src/pyflow/engine/simulation.py`, `src/pyflow/rendering/window.py`,
`src/pyflow/rendering/field_visualization.py`,
`src/pyflow/engine/collocated_field.py`, and the existing `engine.md`/
`overview.md`/`rendering.md` and their `CLAUDE.md` companions -- not
re-derived from general engine-design knowledge.

**One subsection is still marked Planned: Section 3's checkpointing.**
Section 2's live-loop wiring was too, until TASK-030 landed it on
2026-08-28 and this file was updated in the same change -- the mechanism
working exactly as intended.

**The mechanism then failed once, and how it failed is the useful part.**
Both Planned subsections were anchored to a specific roadmap task rather
than an open-ended "future work" (TASK-030, TASK-034), with a note on
each task's own roadmap entry asking for this file to be updated in the
same change. TASK-034 landed on 2026-08-29 without building
checkpointing -- which Stage 5 Completion Criterion 4 explicitly allows
-- and *nothing* here was re-read, so the anchor sat pointing at a
closed task for a day. Worse, the same pass left this document with no
sequence for `navier_stokes_step` at all, which was TASK-034's actual
subject; both were found by that stage's exit audit, not by this
mechanism.

**The lesson recorded rather than the fix improvised:** an anchor to a
task is only as good as the reader who greps for it, and "the task
landed but did not build the thing" is a case a task anchor does not
cover on its own. When a task with a note here closes, re-read this
file whether or not it built what the note names -- what it *did* build
usually belongs here too. Grep this file's own TASK-NNN mentions the
next time any named task is touched.
