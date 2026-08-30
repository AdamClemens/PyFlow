"""SourceTerm (TASK-018): computes the per-cell source contribution to a
field's governing equation -- the last of the three operators (with
Gradient and Divergence) that get an interface but no configuration
field, per `docs/planning/roadmap.md` TASK-018's design decisions.

Unlike Gradient/Divergence, a source term applies to any transported
quantity regardless of arity, so its output shape follows whichever
field it's handed rather than a fixed one.

No concrete scheme lives here -- Stage 3 Completion Criterion 1.

**Still no concrete scheme after Stage 5, and that is a decision rather
than an oversight** (2026-08-28, maintainer's call -- Stage 5's own
design question six, `docs/planning/roadmap.md`). This is the only Stage
3 interface with no implementation, no registry entry and no consumer,
and the obvious candidate was the momentum equation's pressure gradient.
It is not one: Stage 5 applies the pressure correction as a projection
after the momentum predictor (design question five, resolved the same
day), so the correction *is* that gradient's effect on the velocity
field and there is nothing left for a source term to contribute. Had the
projection been placed inside the time integrator's own stages instead,
the gradient would have had to enter the derivative evaluation, which is
exactly where a source term belongs -- the two answers are linked, and
the other pairing would have given this interface its first consumer.

**Its first concrete implementation lands in Stage 6 (TASK-035,
2026-08-30): a Boussinesq buoyancy body force, `src/pyflow/physics/
buoyancy.py`'s `BoussinesqBuoyancy` -- the first implementation of any
numerics interface in this repository to live outside `engine/
numerics/` (`src/pyflow/physics/CLAUDE.md` records why).** Self-registers
under `"boussinesq_buoyancy"` at its own module scope (this module
cannot register it, since importing that class here would be exactly the
"engine depends on physics" direction `engine/CLAUDE.md`'s opening line
forbids), alongside a permanent `"none"` no-op registered here directly
(`NumericsConfig.source_term`, `_NoSourceTerm`, `engine/numerics/
assembly.py`) that contributes zero to every field -- not a `_Null*`
reference implementation destined for replacement, a genuinely supported
configuration.

**The signature below widened for that consumer, from `source(self,
field: Field)` to `source(self, field: Field, state: Mapping[str,
Field])` -- the one interface signature change Stage 6 permits itself
(that stage's own Completion Criterion 2), recorded as
`adr/ADR-010-source-term-state.md`.** Buoyancy contributes to momentum's
own `velocity.1` and is computed from the *temperature* field; the
original signature handed a source term only the field being advanced,
with no way to read what drives it. Chosen over binding the term to a
state inside `simulation.step` (a concept this repository has no
precedent for, hiding the dependency in a closure) and over constructing
it with the driving field once per step (a stale reference across RK4's
four stages, a first-order splitting). `simulation.py`'s own `derivative`
closure already has `state` in scope at every evaluation, so passing it
costs nothing and a source term sees each RK4 stage's own intermediate
value of whatever field it reads.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

import torch

from pyflow.engine.field import Field


class SourceTerm(ABC):
    """Computes the per-cell source contribution to a field's governing
    equation.
    """

    @abstractmethod
    def source(self, field: Field, state: Mapping[str, Field]) -> torch.Tensor:
        """`field`'s source contribution at every cell, given `state` --
        every field currently being transported, by name (the same
        mapping `simulation.py`'s `derivative` closure is itself
        evaluating), so a term can read a *different* field's own
        current value than the one it contributes to.

        Returns a tensor of shape `(field.mesh.num_cells,
        *component_shape)`, where `component_shape` matches `field`'s
        own storage -- `()` for a scalar field, `(n,)` for an
        n-component vector field. Returns zeros for a field this term
        has no contribution to -- there is no separate "not applicable"
        return, since a zero contribution and no contribution are the
        same thing to a caller accumulating it into a derivative.
        """
