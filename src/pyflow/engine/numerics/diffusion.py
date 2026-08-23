"""DiffusionScheme (TASK-018): the interface computing a field's
diffusive flux contribution at each mesh face, given the field alone
(`docs/architecture/engine.md`'s Diffusion contract: "given a field,
produces the diffusive contribution to that field's flux at each
face").

No concrete scheme lives here -- Stage 3 Completion Criterion 1. See
`docs/planning/roadmap.md` TASK-018 for the full design rationale.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch

from pyflow.engine.field import Field


class DiffusionScheme(ABC):
    """Computes a field's diffusive flux at each mesh face."""

    @abstractmethod
    def flux(self, field: Field) -> torch.Tensor:
        """The diffusive contribution to `field`'s flux at each of its
        mesh's faces.

        Returns a tensor of shape `(field.mesh.num_faces,)`.
        """
