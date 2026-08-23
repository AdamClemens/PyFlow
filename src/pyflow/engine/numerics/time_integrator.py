"""TimeIntegrator (TASK-020): the interface that advances every
transported field from one timestep to the next, given the state and
each field's time derivative from the other numerics layers
(`docs/architecture/engine.md`'s Time Integrator contract: "given the
full simulation state and its time derivative, advances it by one
timestep").

Consumes a time derivative, not the schemes that produced it -- the
consequence `docs/architecture/icds.md` states explicitly: the
integrator is "independent of which advection/diffusion/pressure-
coupling schemes are configured, by construction". Advances a *mapping*
of fields, not one -- `engine.md`: "independent of which fields exist or
how many" -- so a caller never has to loop, and coupled systems (Stage
5's velocity/pressure) can express themselves through one call.

No concrete integrator lives here -- Stage 3 Completion Criterion 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

import torch

from pyflow.engine.field import Field


class TimeIntegrator(ABC):
    """Advances a named set of fields forward by `dt`, given each
    field's time derivative.
    """

    @abstractmethod
    def advance(
        self,
        fields: Mapping[str, Field],
        derivatives: Mapping[str, torch.Tensor],
        dt: float,
    ) -> dict[str, Field]:
        """Return a new set of fields, one per key in `fields`, each
        advanced by `dt` from its current state using its entry in
        `derivatives`.

        Must not mutate `fields`, any field in it, or `derivatives`.
        """
