"""ScalarField (TASK-015): a single value per cell -- the collocated
scalar leaf of the `Field` hierarchy. See `collocated_field.py` for the
shared storage/initialisation/access logic this builds on.
"""

from __future__ import annotations

from pyflow.engine.collocated_field import CollocatedField


class ScalarField(CollocatedField[float]):
    """A scalar (single-value-per-cell) `Field`."""

    @property
    def component_shape(self) -> tuple[int, ...]:
        return ()

    def value_at(self, cell: int) -> float:
        """This field's value at `cell`, as a plain `float`.

        Raises `InvalidMeshEntityError` if `cell` is out of range.
        """
        return float(self._tensor_at(cell))

    def set_value_at(self, cell: int, value: float) -> None:
        """Set this field's value at `cell`.

        Raises `InvalidMeshEntityError` if `cell` is out of range.
        """
        self._set_tensor_at(cell, value)

    def copy(self) -> ScalarField:
        clone = ScalarField(self.mesh, self.name)
        clone._values = self._values.clone()
        return clone
