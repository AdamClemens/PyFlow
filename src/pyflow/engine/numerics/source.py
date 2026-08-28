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
