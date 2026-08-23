"""SourceTerm (TASK-018): computes the per-cell source contribution to a
field's governing equation -- the last of the three operators (with
Gradient and Divergence) that get an interface but no configuration
field, per `docs/planning/roadmap.md` TASK-018's design decisions.

Unlike Gradient/Divergence, a source term applies to any transported
quantity regardless of arity, so its output shape follows whichever
field it's handed rather than a fixed one.

No concrete scheme lives here -- Stage 3 Completion Criterion 1.
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
