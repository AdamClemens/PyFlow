"""CollocatedField (TASK-015): the shared cell-centred storage,
initialisation, and value-access logic every collocated `Field` needs,
regardless of arity (scalar, vector, ...). Concrete everywhere except
`component_shape`, `value_at` and `set_value_at`, which a leaf class
(`ScalarField`, `VectorField`) supplies -- see `docs/planning/
roadmap.md` TASK-014/015 for the full design rationale.

Deliberately separate from `Field` itself (`field.py`, TASK-014), which
carries no storage at all.
"""

from __future__ import annotations

from abc import abstractmethod

import torch

from pyflow.engine.field import Field
from pyflow.engine.mesh import InvalidMeshEntityError, Mesh


class CollocatedField[T](Field):
    """A `Field` stored one value per mesh cell.

    `component_shape` is the shape of a single cell's value -- `()` for
    a scalar, `(n,)` for an n-component vector -- and, together with
    `value_at`/`set_value_at`, is what a concrete leaf class supplies.
    Storage allocation, initialisation, and the id-checked tensor access
    every leaf builds its own `value_at`/`set_value_at` on
    (`_tensor_at`/`_set_tensor_at`) are implemented here, once, so they
    can't drift between leaf classes.

    `value_at`/`set_value_at` are left abstract here, typed generically
    (`T`, PEP 695 syntax -- this project targets Python 3.14), rather
    than implemented directly returning a `torch.Tensor` -- that lets
    `ScalarField` return a plain `float` and a future `VectorField` a
    `tuple[float, ...]` without either violating the override-
    compatibility check `mypy --strict` applies to a concretely-typed
    base method.
    """

    def __init__(self, mesh: Mesh, name: str, *, initial_value: object | None = None) -> None:
        super().__init__(mesh, name)
        self._values = torch.zeros((mesh.num_cells, *self.component_shape), dtype=torch.float64)
        if initial_value is not None:
            self._apply_initial_value(initial_value)

    @property
    @abstractmethod
    def component_shape(self) -> tuple[int, ...]:
        """The shape of a single cell's value."""

    @property
    def values(self) -> torch.Tensor:
        """The full backing tensor, shape `(mesh.num_cells, *component_shape)`."""
        return self._values

    @abstractmethod
    def value_at(self, cell: int) -> T:
        """This field's value at `cell`.

        Raises `InvalidMeshEntityError` if `cell` is out of range.
        """

    @abstractmethod
    def set_value_at(self, cell: int, value: T) -> None:
        """Set this field's value at `cell`.

        Raises `InvalidMeshEntityError` if `cell` is out of range.
        """

    def _tensor_at(self, cell: int) -> torch.Tensor:
        """The raw tensor slice at `cell`, shape `component_shape` --
        the shared implementation every leaf's `value_at` converts to
        its own ergonomic return type.
        """
        self._check_cell(cell)
        return self._values[cell]

    def _set_tensor_at(self, cell: int, value: object) -> None:
        """Set the raw tensor slice at `cell` from `value` (anything
        `torch.as_tensor` accepts) -- the shared implementation every
        leaf's `set_value_at` builds on.
        """
        self._check_cell(cell)
        self._values[cell] = torch.as_tensor(value, dtype=torch.float64)

    def _check_cell(self, cell: int) -> None:
        if not 0 <= cell < self.mesh.num_cells:
            raise InvalidMeshEntityError(
                f"cell {cell} is out of range for a mesh with {self.mesh.num_cells} cells"
            )

    def _apply_initial_value(self, initial_value: object) -> None:
        # The constant case is the callable case's degenerate form, not
        # a second code path: a constant is simply never called.
        if callable(initial_value):
            for cell in range(self.mesh.num_cells):
                x, y = self.mesh.cell_centroid(cell)
                self._values[cell] = torch.as_tensor(initial_value(x, y), dtype=torch.float64)
        else:
            self._values[:] = torch.as_tensor(initial_value, dtype=torch.float64)
