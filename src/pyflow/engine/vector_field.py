"""VectorField (TASK-016): a fixed number of values per cell -- the
collocated vector leaf of the `Field` hierarchy, built on
`CollocatedField` (TASK-015) the same way `ScalarField` is.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.mesh import Mesh


class VectorField(CollocatedField[tuple[float, ...]]):
    """A fixed-arity (`num_components`-per-cell) `Field`."""

    def __init__(
        self,
        mesh: Mesh,
        name: str,
        num_components: int = 2,
        *,
        initial_value: object | None = None,
    ) -> None:
        if num_components <= 0:
            raise ValueError(f"num_components must be positive, got {num_components}")
        self._num_components = num_components
        super().__init__(mesh, name, initial_value=initial_value)

    @property
    def component_shape(self) -> tuple[int, ...]:
        return (self._num_components,)

    def value_at(self, cell: int) -> tuple[float, ...]:
        """This field's value at `cell`, as a plain `tuple[float, ...]`
        of length `num_components`.

        Raises `InvalidMeshEntityError` if `cell` is out of range.
        """
        return tuple(self._tensor_at(cell).tolist())

    def set_value_at(self, cell: int, value: Sequence[float]) -> None:
        """Set this field's value at `cell` from a sequence of length
        `num_components`.

        Raises `InvalidMeshEntityError` if `cell` is out of range, or
        `ValueError` if `value`'s length doesn't match `num_components`.
        """
        if len(value) != self._num_components:
            raise ValueError(f"value must have length {self._num_components}, got {len(value)}")
        self._set_tensor_at(cell, value)

    def component(self, index: int) -> torch.Tensor:
        """Every cell's value at component `index`, shape `(num_cells,)`.

        Raises `IndexError` if `index` is out of range.
        """
        if not 0 <= index < self._num_components:
            raise IndexError(
                f"component index {index} is out of range for a "
                f"{self._num_components}-component field"
            )
        return self.values[:, index]

    def magnitude(self) -> torch.Tensor:
        """The Euclidean norm of each cell's value, shape `(num_cells,)`."""
        # `torch.linalg.vector_norm`'s stub returns `Any`, unlike the
        # rest of the module's torch calls -- the `cast` documents that
        # this is a stub gap, not an intentionally loose return type.
        return cast("torch.Tensor", torch.linalg.vector_norm(self.values, dim=-1))

    def copy(self) -> VectorField:
        clone = VectorField(self.mesh, self.name, self._num_components)
        clone._values = self._values.clone()
        return clone
