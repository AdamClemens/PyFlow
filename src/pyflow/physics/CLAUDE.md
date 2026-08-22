# CLAUDE

**Empty until Stage 6, and empty on purpose.** One docstring-only
`__init__.py`; nothing before Stage 4 needs this package at all
(`docs/repository-manifest.md`'s `src/` row). This file was the generic
placeholder the root `CLAUDE.md` allows "only until something specific
is known about that directory" until 2026-08-22, when drafting Stage 3
made the boundary below specific.

**What belongs here: phenomena. What does not: numerical machinery.**

- Here, eventually: temperature, density, humidity, passive tracers
  (Stage 6, `docs/planning/roadmap.md` TASK-035..038), buoyancy
  coupling, and anything else whose definition is physical rather than
  discretisational -- the code counterpart to `docs/handbook/physics/`.
- Not here: advection schemes, diffusion schemes, time integrators,
  pressure-velocity coupling, linear solvers, boundary conditions.
  Those are `src/pyflow/engine/numerics/`, arriving in Stage 3
  (TASK-018..022) -- see `src/pyflow/CLAUDE.md` for why that subpackage
  exists and where the line is.

The distinction is worth defending rather than treating as filing
preference: `adr/ADR-003-modular-numerical-strategies.md`'s whole claim
is that a numerical scheme can be swapped without the physics noticing,
and `docs/planning/roadmap.md`'s Stage 6 goal ("demonstrate field-centric
architecture") is that a phenomenon can be added without the numerics
noticing. Both claims become untestable the moment the two live in the
same package. **The moment a discretisation lands here, or a phenomenon
lands in `numerics/`, say so explicitly rather than letting the
directories quietly stop meaning anything.**
