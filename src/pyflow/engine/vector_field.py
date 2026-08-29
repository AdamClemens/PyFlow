"""VectorField (TASK-016): a fixed number of values per cell -- the
collocated vector leaf of the `Field` hierarchy, built on
`CollocatedField` (TASK-015) the same way `ScalarField` is.

**`decompose`/`assemble` (TASK-031a, added 2026-08-29)** are design
question one's own answer, made concrete: momentum is transported as one
`ScalarField` per component, with a `VectorField` assembled for the
consumers that need one -- no Stage 3 interface change, since a
component is a real `ScalarField`, usable by any existing scheme with no
adapter. The naming convention (`component_name`) is fixed and stated
once, here, rather than re-derived per caller.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import torch

from pyflow.engine.collocated_field import CollocatedField
from pyflow.engine.mesh import Mesh
from pyflow.engine.scalar_field import ScalarField

_SPATIAL_DIMENSIONS = 2
"""PyFlow is 2D-only for now -- the same locally-duplicated constant
`advection.py`/`gradient.py`/`divergence.py` each carry, named here
rather than repeated as a bare `2` (`docs/implementation/upgrade-paths.md`
"Mesh"). `assemble`'s own component-count rejection is checked against
this, not against `Mesh`, which exposes no dimensionality accessor.
"""


class IncompatibleVelocityFieldError(ValueError):
    """Raised when a velocity field's `component_shape` does not match
    the mesh's spatial dimensionality.

    Lives here, not in `advection.py`, as of TASK-031a (2026-08-29):
    `advection.py` already imports `VectorField` from this module, so
    the reverse import direction this class used to need would be
    circular. Co-located with `VectorField` instead -- the class
    describes a property of a `VectorField`'s own shape, which is
    exactly as much this module's concern as `advection.py`'s.
    `advection.py` imports it from here.
    """


class ComponentCountMismatchError(ValueError):
    """Raised by `VectorField.assemble` when the number of components
    handed to it does not match the mesh's own spatial dimensionality --
    the same reasoning `IncompatibleVelocityFieldError` states, applied
    to reassembly instead of a velocity field handed to a scheme.
    """


class ComponentMeshMismatchError(ValueError):
    """Raised by `VectorField.assemble` when its components are not all
    defined over the same mesh -- mixing components from different
    meshes would either crash confusingly deep inside a mismatched-shape
    tensor operation or, on a coincidentally same-sized mesh, silently
    combine values from unrelated cells (the same reasoning
    `simulation.py`'s `MismatchedMeshError` states).
    """


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

    @staticmethod
    def component_name(vector_name: str, index: int) -> str:
        """The fixed naming convention for one component of a vector
        field named `vector_name` -- stated once, here, so `decompose`
        and any caller that needs to predict a component's name (e.g.
        `bootstrap.py`, keying a per-field diffusion-coefficient
        override by the name a decomposed component will actually have)
        agree by construction rather than by convention re-derived at
        each call site.
        """
        return f"{vector_name}.{index}"

    def decompose(self) -> list[ScalarField]:
        """One real `ScalarField` per component, in index order, named
        by `component_name` -- design question one's own answer (TASK-031a,
        `docs/planning/roadmap.md`): momentum is transported as one
        `ScalarField` per component, usable by any existing scheme with
        no adapter, not a new kind of field.
        """
        return [
            ScalarField(
                self.mesh, self.component_name(self.name, i), initial_value=self.component(i)
            )
            for i in range(self._num_components)
        ]

    @staticmethod
    def assemble(components: Sequence[ScalarField], name: str) -> VectorField:
        """The inverse of `decompose`: one `VectorField` named `name`
        from `components`, in index order.

        Raises `ComponentCountMismatchError` if `len(components)` does
        not match the mesh's own spatial dimensionality (2, for now --
        `_SPATIAL_DIMENSIONS` above), and `ComponentMeshMismatchError` if
        the components are not all defined over the same mesh (Criterion
        6, `docs/planning/roadmap.md` TASK-031a).
        """
        if len(components) != _SPATIAL_DIMENSIONS:
            raise ComponentCountMismatchError(
                f"expected {_SPATIAL_DIMENSIONS} components (the mesh's own spatial "
                f"dimensionality), got {len(components)}"
            )
        mesh = components[0].mesh
        for component in components[1:]:
            if component.mesh is not mesh:
                raise ComponentMeshMismatchError(
                    "components are not all defined over the same mesh"
                )
        result = VectorField(mesh, name, num_components=len(components))
        for i, component in enumerate(components):
            result.values[:, i] = component.values
        return result
