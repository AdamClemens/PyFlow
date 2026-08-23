"""GradientScheme (TASK-018): computes the cell-centred gradient of a
field -- one of the three operators (with Divergence and Source) that
jointly compute `docs/architecture/engine.md`'s Flux layer alongside
Advection/Diffusion, but get no configuration field of their own:
`adr/ADR-003-modular-numerical-strategies.md` names exactly six
configuration-selected components and Gradient is not one of them, per
`docs/planning/roadmap.md` TASK-018's design decisions.

No concrete scheme lives here -- Stage 3 Completion Criterion 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from pyflow.engine.field import Field

_SPATIAL_DIMENSIONS = 2
"""PyFlow is 2D-only for now (`docs/implementation/mvp.md`) -- see
`advection.py`'s identical constant for the full reasoning.
"""


class GradientScheme(ABC):
    """Computes the cell-centred gradient of a (typically scalar) field."""

    @abstractmethod
    def gradient(self, field: Field) -> torch.Tensor:
        """`field`'s gradient at every cell centre.

        Returns a tensor of shape `(field.mesh.num_cells,
        _SPATIAL_DIMENSIONS)` -- one gradient vector per cell.
        """
