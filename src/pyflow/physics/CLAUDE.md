# CLAUDE

**No longer empty as of TASK-035 (Stage 6, 2026-08-30): `buoyancy.py`
is this package's first real module.** Everything below this paragraph
describes the boundary that made this package worth having *before* it
held any code -- read it as still-current design intent, not as a
description of an empty directory. This file was the generic placeholder
the root `CLAUDE.md` allows "only until something specific is known
about that directory" until 2026-08-22, when drafting Stage 3 made the
boundary below specific, and stayed empty through Stage 5 on purpose
(next paragraph).

**Confirmed against Stage 5 on 2026-08-28, which is the first stage that
could plausibly have filled this package.** `__init__.py`'s own
docstring said the package was for physical models, "incompressible flow
first" -- Stage 5's exact subject -- and so contradicted this file's
opening sentence for as long as both existed, unnoticed because nothing
had cause to ask. Stage 5's own design question seven put it to the
maintainer: everything that stage builds stays in `engine/`, because
what it writes is discretisation and orchestration, which is the half
the boundary below excludes. `__init__.py` was corrected in the same
change. The line stands, now with a stage's worth of evidence behind it
rather than an assumption.

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

**Where a `SourceTerm` implementation goes, settled 2026-08-30 before
Stage 6's first task** (that stage's own design question four,
`docs/planning/roadmap.md`): the *interface* stays in
`src/pyflow/engine/numerics/source.py`, and the concrete phenomenon
implementing it -- Boussinesq buoyancy, TASK-035 -- lives here. That
makes it the first implementation of a numerics interface in this
repository to sit outside `engine/numerics/`, which is surprising enough
that a reader meeting it needs the reason: it is exactly what the
boundary above claims. The interface is machinery; a body force computed
from a temperature difference is physics. The question was raised
because a body force has a foot in both halves, and the answer was
already half-written -- "buoyancy coupling" is in this file's own list
above, and had been since 2026-08-22.

The distinction is worth defending rather than treating as filing
preference: `adr/ADR-003-modular-numerical-strategies.md`'s whole claim
is that a numerical scheme can be swapped without the physics noticing,
and `docs/planning/roadmap.md`'s Stage 6 goal ("demonstrate field-centric
architecture") is that a phenomenon can be added without the numerics
noticing. Both claims become untestable the moment the two live in the
same package. **The moment a discretisation lands here, or a phenomenon
lands in `numerics/`, say so explicitly rather than letting the
directories quietly stop meaning anything.**

**`buoyancy.py` (TASK-035, done 2026-08-30) is `BoussinesqBuoyancy`,
this package's first module and the phenomenon this file's own list has
named since 2026-08-22.** One Boussinesq body-force coupling,
`f = c * (phi - phi_0) * g`, computed generically over whichever fields
`FieldConfig.buoyancy_reference_value`/`buoyancy_coefficient` declare a
coupling for -- Stage 6 Criterion 4's own "one coupling, not one per
field" made real: TASK-036 (Density) reuses this exact class, with
`c = +1/rho_0` instead of `-beta`, rather than needing its own
implementation. `gravity`/the per-field coupling map are both threaded
in at construction (`bootstrap.py`), the same "constructed with it, not
handed it after the fact" pattern every other per-field mechanism in
this project follows -- this module never learns which phenomenon a
coupling belongs to, only a driving field's own name.

**`engine/numerics/assembly.py` cannot import this module, and that
constraint shaped where the registration call itself lives.**
`buoyancy.py` self-registers under `"boussinesq_buoyancy"` at its own
module scope (`register_source_term("boussinesq_buoyancy",
BoussinesqBuoyancy)`, imported from `assembly.py`, called at import
time), not from `assembly.py` alongside the other six registrations --
`engine/CLAUDE.md`'s own opening line ("independent of any specific
physics") means `engine/numerics/assembly.py` must not import a concrete
phenomenon, even to register it. `bootstrap.py` already composes
`configuration`/`engine`/`rendering`, and its own existing import of
`BoussinesqBuoyancy` is what triggers this module's self-registration --
**not a call inside `bootstrap()`'s own function body**, which a first
version used and which made the name resolvable only after `bootstrap()`
had actually run once (found by a direct question about the consequences
of that placement, not by a test). See `bootstrap.py`'s own docstring,
and `engine/numerics/assembly.py`'s/`source.py`'s own module docstrings,
for the same finding recorded where each reader meets it, and `tests/
integration/test_boussinesq_buoyancy_registration.py` for the regression
test pinning it in a fresh subprocess.

**`ScalarTransportPattern`-shaped fields (temperature, density,
humidity, tracers) still contribute no code of their own here or
anywhere else** -- Stage 6 Criterion 1's own "the last two tasks add
zero lines under `src/pyflow/`" is a claim about `FieldConfig`
(`configuration/`) being sufficient, not about this package growing a
module per field. `buoyancy.py` is the *coupling*, not the field; a
plain transported field with no coupling needs nothing here at all.
