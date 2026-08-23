"""DivergenceScheme (TASK-018): computes the cell-centred divergence of
a field -- one of the three operators (with Gradient and Source) that
get an interface but no configuration field, per `docs/planning/
roadmap.md` TASK-018's design decisions.

No concrete scheme lives here -- Stage 3 Completion Criterion 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from pyflow.engine.field import Field


class DivergenceScheme(ABC):
    """Computes the cell-centred divergence of a (typically vector) field."""

    @abstractmethod
    def divergence(self, field: Field) -> torch.Tensor:
        """`field`'s divergence at every cell centre.

        Returns a tensor of shape `(field.mesh.num_cells,)`.
        """
