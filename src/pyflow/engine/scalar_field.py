"""ScalarField (TASK-015): a single value per cell -- the collocated
scalar leaf of the `Field` hierarchy. See `collocated_field.py` for the
shared storage/initialisation/access logic this builds on.

**`PressureField` (TASK-032, added 2026-08-29)** is a thin marker
subclass -- see its own docstring below for why it exists and why it
lives here rather than in `engine/numerics/pressure_coupling.py`.
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


class PressureField(ScalarField):
    """A `ScalarField` that is specifically pressure -- solved from the
    incompressibility constraint, never transported (Stage 5 Completion
    Criterion 2, `docs/planning/roadmap.md` TASK-032: "pressure is not
    among the fields `step` advances, and handing `step` a `fields`
    mapping that contains the pressure field raises a named error").

    Carries no behaviour of its own beyond `ScalarField`'s -- purely a
    type marker `simulation.step` can `isinstance`-check, the "stated at
    the API level deliberately, not the configuration level" shape
    Criterion 2 asks for: there is no configuration surface that names
    which fields are transported, so the guard has to live where a real
    `Field` object is actually in hand.

    **Lives here, not in `engine/numerics/pressure_coupling.py` (this
    class's one real producer, `PISO.correct`), because `simulation.py`
    needs to import it and cannot import from `pressure_coupling.py`
    without a circular import** -- that module already imports
    `accumulate_flux_to_cells` from `simulation.py`. The same reasoning
    `IncompatibleVelocityFieldError`'s own TASK-031a move to
    `vector_field.py` used (`src/pyflow/engine/CLAUDE.md`'s
    `vector_field.py` entry).

    `PressureCoupling.correct`'s own abstract signature is unchanged
    (`-> tuple[VectorField, ScalarField]`) -- no Stage 3 interface
    change, since a `PressureField` instance already satisfies it
    (covariant return narrowing, valid under `mypy --strict`). Only
    `PISO`'s own concrete implementation constructs one.
    """
