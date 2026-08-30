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

Stage 6's buoyancy coupling (TASK-035) is the natural first
implementation: a body force is a source term in the way a projection
correction is not.

**And that first consumer does not fit the signature below, which was
found on 2026-08-30 while writing TASK-035's roadmap entry rather than
during its implementation** (Stage 6's own design question six,
`docs/planning/roadmap.md`). Buoyancy contributes to momentum's own
`velocity.1` and is computed from the *temperature* field; `source(self,
field)` is handed only the field being advanced, so the term can never
see what drives it. **Resolved, maintainer's call: the signature widens
to `source(self, field: Field, state: Mapping[str, Field])`** -- the one
interface signature change Stage 6 permits itself, named in that stage's
Criterion 2 in advance. Chosen over binding the term to a state inside
`simulation.step` (a concept this repository has no precedent for, and
one that hides the dependency in a closure) and over constructing it
with the driving field once per step (a stale reference inside RK4's
four stages, so a first-order splitting). `derivative` already receives
the intermediate state, so passing it costs nothing and the term sees
each RK4 stage's own temperature.

**The widening is TASK-035's to make, not this note's.** The signature
below is still the Stage 3 one; this paragraph records the decision
where whoever implements it will meet it, the same way the "no
implementation after Stage 5" decision above was recorded here when it
was taken.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from pyflow.engine.field import Field


class SourceTerm(ABC):
    """Computes the per-cell source contribution to a field's governing
    equation.
    """

    @abstractmethod
    def source(self, field: Field) -> torch.Tensor:
        """`field`'s source contribution at every cell.

        Returns a tensor of shape `(field.mesh.num_cells,
        *component_shape)`, where `component_shape` matches `field`'s
        own storage -- `()` for a scalar field, `(n,)` for an
        n-component vector field.
        """
