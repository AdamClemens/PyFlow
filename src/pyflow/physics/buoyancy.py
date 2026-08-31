"""BoussinesqBuoyancy (TASK-035): a body force turning a field's own
difference from a reference value into a force on momentum -- the first
concrete implementation of `src/pyflow/engine/numerics/source.py`'s
`SourceTerm`, and the first implementation of any numerics interface in
this repository to live outside `engine/numerics/` (`src/pyflow/
physics/CLAUDE.md` records why: the interface is machinery, this is
physics).

**The expression, and the sign, derived in advance rather than left to
the implementer** (`docs/planning/roadmap.md` TASK-035's own "The sign,
derived here" section): `f = c * (phi - phi_0) * g`, with `g` the
configured gravitational acceleration vector and `c = -beta` for a
temperature field or `c = +1/rho_0` for a density field (TASK-036) --
one expression, one sign convention, reused unchanged by both couplings
this stage and the next need. With `g = (0, -9.81)`: a warm parcel has
`phi > phi_0`, so `f = -beta(phi - phi_0)(0, -9.81)` points up -- warm
fluid rises. `phi_0`/`c` are `FieldConfig.buoyancy_reference_value`/
`buoyancy_coefficient` (`src/pyflow/configuration/schema.py`), read
generically here as "reference value" and "coefficient" -- this module
has no idea, and does not need to know, whether the field driving a
given coupling is called temperature or density.

**Self-registers under `"boussinesq_buoyancy"` at import time (module
scope, below), the same pattern every other concrete scheme in this
project uses -- not a call inside `bootstrap()`'s own function body.**
The first version of this module left the `register_source_term` call in
`bootstrap.py`'s function body instead, on the reasoning that `engine/
numerics/assembly.py` cannot import this module (`engine/CLAUDE.md`'s
"independent of any specific physics") and `bootstrap.py` already
composes `configuration`/`engine`/`rendering`. That reasoning about
*where* the call may live was right; leaving it inside a function was
not -- it made `"boussinesq_buoyancy"` resolvable only *after* `bootstrap()`
had actually run once in the process, unlike every one of `adr/ADR-003`'s
six components, which self-register the moment `assembly.py` is
imported. `assemble_numerics(NumericsConfig(source_term=
"boussinesq_buoyancy"))`, called directly with no prior `bootstrap()`
call, raised `UnknownSchemeError` -- a real gap, found by a direct
question about the consequences of this design rather than by a test,
and fixed the same way every other scheme avoids it: register at import
time. `bootstrap.py` imports this module for that side effect alone -- a
bare `import pyflow.physics.buoyancy`, marked `noqa: F401`, referencing
no name in it -- so that import is what triggers registration, not a
separate call. **Said precisely here, and in the three other places that
describe it, after the Stage 6 exit audit (2026-08-31) found all four
claiming `bootstrap.py` imported `BoussinesqBuoyancy` "to get the class
itself".** It does not, and the difference matters in one direction: a
contributor who goes looking for that name and does not find it has an
import that looks unused and safe to delete.
`tests/integration/test_boussinesq_buoyancy_registration.py` pins this
in a fresh subprocess -- the only way to genuinely prove "resolvable
without `bootstrap()` ever running", the same reasoning `tests/
integration/test_import_order.py` already uses for import-order claims.
"""

from __future__ import annotations

from collections.abc import Mapping

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.field import Field
from pyflow.engine.numerics.assembly import register_source_term
from pyflow.engine.numerics.source import SourceTerm
from pyflow.engine.vector_field import VectorField

_VELOCITY_COMPONENT_NAMES = (
    VectorField.component_name("velocity", 0),
    VectorField.component_name("velocity", 1),
)


class BoussinesqBuoyancy(SourceTerm):
    """One Boussinesq body-force coupling, driven by any number of
    declared fields at once (Stage 6 Criterion 4: "one coupling, not one
    per field" -- TASK-036 reuses this class unchanged for density,
    rather than needing a second implementation).

    `gravity` is the run's own fixed acceleration vector
    (`FluidConfig.gravity`). `couplings` maps a driving field's own name
    to its `(reference_value, coefficient)` pair
    (`bootstrap.py` builds this from every `FieldConfig` that declares
    both, keyed by `declared.name`) -- this class stays field-name-
    agnostic about which phenomenon each coupling belongs to, the same
    "constructed with it, not handed it after the fact" pattern every
    other per-field mechanism in this project already follows.
    """

    def __init__(
        self, gravity: tuple[float, float], couplings: Mapping[str, tuple[float, float]]
    ) -> None:
        self._gravity = gravity
        self._couplings = couplings

    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        assert isinstance(field, CollocatedField)
        zeros = torch.zeros((field.mesh.num_cells, *field.component_shape), dtype=torch.float64)
        if field.name not in _VELOCITY_COMPONENT_NAMES:
            return zeros
        axis = _VELOCITY_COMPONENT_NAMES.index(field.name)
        gravity_component = self._gravity[axis]
        if gravity_component == 0.0:
            return zeros

        total = zeros
        for driving_name, (reference_value, coefficient) in self._couplings.items():
            driving_field = state.get(driving_name)
            if driving_field is None:
                continue
            assert isinstance(driving_field, CollocatedField)
            total = total + coefficient * (driving_field.values - reference_value) * (
                gravity_component
            )
        return total


register_source_term("boussinesq_buoyancy", BoussinesqBuoyancy)
