# CLAUDE

TASK-018's five operator interfaces: `advection.py`, `diffusion.py`,
`gradient.py`, `divergence.py`, `source.py` -- one `ABC` each, no
concrete implementation under `src/` (Stage 3 Completion Criterion 1,
`docs/planning/roadmap.md`). `boundary_condition.py` (TASK-019, done
2026-08-23), `time_integrator.py` (TASK-020, done 2026-08-23) and
`linear_solver.py` (TASK-022, done 2026-08-23, built before TASK-021
despite the number) join them the same way. `pressure_coupling.py`
(TASK-021, done 2026-08-23, Stage 3's last task) completes the seven
interfaces.

**`assembly.py`** (TASK-021) is different in kind from the seven above:
not an interface, but the registry (`register_advection_scheme` and five
siblings) and `assemble_numerics(NumericsConfig) -> AssembledNumerics`
that resolve a configured name to a live instance of one. It is also
this subpackage's **one exception to "no concrete implementation under
`src/`"** -- a small set of trivial, non-physical reference classes,
registered by default under the exact MVP names, exist solely so a real
`pyflow run` subprocess has something to assemble into for Stage 3's
golden demo. Named and documented as reference implementations
throughout, never as real ones -- see the module's own docstring and
`src/pyflow/engine/CLAUDE.md`'s `numerics/` entry for the full reasoning
and the exception's own record against Stage 3 Completion Criterion 1.

Full design rationale -- why a subpackage, why every operator takes
`Field` rather than a concrete subclass, why the return shapes split
face-valued (Advection/Diffusion) from cell-valued
(Gradient/Divergence/Source), the `_check_velocity`/`_check_boundary_face`
rejection pattern, `BoundaryCondition`'s `kind`-property design, why
`TimeIntegrator.advance` takes a `Mapping[str, Field]` with no analogous
`_check_...` helper, why `LinearSolver.solve` takes a plain dense
`matrix`/`rhs` pair rather than a dedicated "system" type, and
`PressureCoupling`'s real `isinstance` guard on its constructor argument
-- lives in the parent `src/pyflow/engine/CLAUDE.md`'s `numerics/` entry,
not repeated here.
