"""Unit tests for `pyflow.engine.numerics.assembly` (TASK-021) --
`assemble_numerics` and the six registries it resolves configured names
through. Isolated logic, in-process -- no CLI/subprocess boundary, which
`tests/golden/test_numerics_assembly.py` covers separately.

Covers Stage 3 Completion Criteria 3 (adding an implementation edits no
existing function body) and 4 (selection fixed at construction, not
re-read).
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest
import torch

from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    NumericsConfig,
)
from pyflow.engine.field import Field
from pyflow.engine.mesh import StructuredCartesianMesh
from pyflow.engine.numerics.advection import AdvectionScheme, FirstOrderUpwindAdvection
from pyflow.engine.numerics.assembly import (
    AssembledNumerics,
    DuplicateSchemeError,
    UnknownSchemeError,
    assemble_numerics,
    register_advection_scheme,
    register_diffusion_scheme,
    register_pressure_coupling,
)
from pyflow.engine.numerics.boundary_condition import (
    BoundaryCondition,
    DirichletBoundaryCondition,
    NeumannBoundaryCondition,
)
from pyflow.engine.numerics.diffusion import CentralDifferenceDiffusion, DiffusionScheme
from pyflow.engine.numerics.linear_solver import ConjugateGradientSolver, LinearSolver
from pyflow.engine.numerics.pressure_coupling import PISO, PressureCoupling
from pyflow.engine.numerics.time_integrator import RK4Integrator
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


class _TestOnlyAdvection(AdvectionScheme):
    """A scheme no `src/` module has ever heard of, registered directly
    by this test -- Criterion 3's own scenario.

    Accepts (and ignores) the boundary-conditions mapping every
    advection factory now receives (TASK-040's Design decision).
    """

    def __init__(self, boundary_conditions: Mapping[str, object]) -> None:
        del boundary_conditions

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        return torch.ones(field.mesh.num_faces, dtype=torch.float64)


class _OtherTestOnlyAdvection(AdvectionScheme):
    """A second test-only scheme, distinct from `_TestOnlyAdvection`, so
    "a different factory under the same name" is expressible.
    """

    def __init__(self, boundary_conditions: Mapping[str, object]) -> None:
        del boundary_conditions

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        return torch.full((field.mesh.num_faces,), 2.0, dtype=torch.float64)


class _CapturingAdvection(AdvectionScheme):
    """Records the exact `boundary_conditions` mapping it was constructed
    with -- every other test-only scheme in this module discards it, so
    nothing here would fail if `assemble_numerics` silently passed an
    empty mapping (or the wrong one) to the advection factory instead of
    the one it just resolved.
    """

    def __init__(self, boundary_conditions: Mapping[str, BoundaryCondition]) -> None:
        self.received_boundary_conditions = boundary_conditions

    def flux(self, field: Field, velocity: VectorField) -> torch.Tensor:
        self._check_velocity(velocity)
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


class _CapturingPressureCoupling(PressureCoupling):
    """Records the exact `boundary_conditions` mapping it was constructed
    with -- the pressure-coupling analogue of `_CapturingAdvection`/
    `_CapturingDiffusion` above (TASK-027).
    """

    def __init__(
        self, linear_solver: LinearSolver, boundary_conditions: Mapping[str, BoundaryCondition]
    ) -> None:
        super().__init__(linear_solver)
        self.received_boundary_conditions = boundary_conditions

    def correct(
        self, provisional_velocity: VectorField, dt: float
    ) -> tuple[VectorField, ScalarField]:
        del dt
        return provisional_velocity.copy(), ScalarField(provisional_velocity.mesh, "pressure")


class _CapturingDiffusion(DiffusionScheme):
    """Records the exact `boundary_conditions` mapping and
    `diffusion_coefficient` it was constructed with -- the diffusion
    analogue of `_CapturingAdvection` above, proving `assemble_numerics`
    actually threads both resolved values into the diffusion factory,
    not stale or empty ones.
    """

    def __init__(
        self, boundary_conditions: Mapping[str, BoundaryCondition], diffusion_coefficient: float
    ) -> None:
        self.received_boundary_conditions = boundary_conditions
        self.received_diffusion_coefficient = diffusion_coefficient

    def flux(self, field: Field) -> torch.Tensor:
        return torch.zeros(field.mesh.num_faces, dtype=torch.float64)


@pytest.fixture
def registered_test_only_advection() -> str:
    name = "test_only_advection_for_assembly_test"
    register_advection_scheme(name, _TestOnlyAdvection)
    return name


def _mesh() -> StructuredCartesianMesh:
    return StructuredCartesianMesh(origin=(0.0, 0.0), spacing=(1.0, 1.0), extent=(3, 2))


def test_registering_a_new_name_resolves_without_editing_assembly(
    registered_test_only_advection: str,
) -> None:
    config = NumericsConfig(advection=registered_test_only_advection)  # type: ignore[arg-type]

    assembled = assemble_numerics(config)

    assert isinstance(assembled.advection, _TestOnlyAdvection)


def test_default_config_assembles_successfully() -> None:
    assembled = assemble_numerics(NumericsConfig())

    assert isinstance(assembled, AssembledNumerics)
    assert assembled.names["advection"] == "first_order_upwind"
    assert assembled.names["diffusion"] == "central_difference"
    assert assembled.names["time_integration"] == "rk4"
    assert assembled.names["linear_solver"] == "conjugate_gradient"
    assert assembled.names["pressure_coupling"] == "piso"
    for face in ("north", "south", "east", "west"):
        assert assembled.names[f"boundary_conditions.{face}"] == "dirichlet"
        assert face in assembled.boundary_conditions


def test_mutating_the_config_after_assembly_changes_nothing(
    registered_test_only_advection: str,
) -> None:
    config = NumericsConfig(advection=registered_test_only_advection)  # type: ignore[arg-type]

    assembled = assemble_numerics(config)
    original_advection = assembled.advection
    config.advection = "central_difference"  # type: ignore[assignment]  # nonsense, deliberately

    assert assembled.advection is original_advection
    assert isinstance(assembled.advection, _TestOnlyAdvection)


def test_unknown_advection_name_raises_named() -> None:
    config = NumericsConfig(advection="does_not_exist")  # type: ignore[arg-type]

    with pytest.raises(UnknownSchemeError, match="does_not_exist"):
        assemble_numerics(config)


def test_unknown_diffusion_name_raises_named() -> None:
    # Diffusion gained its own inline resolution (TASK-040, boundary-
    # conditions-first reordering) rather than sharing advection's --
    # its own rejection path needs its own test.
    config = NumericsConfig(diffusion="does_not_exist")  # type: ignore[arg-type]

    with pytest.raises(UnknownSchemeError, match="does_not_exist"):
        assemble_numerics(config)


def test_unknown_time_integration_name_raises_named() -> None:
    # time_integration/linear_solver are the only two components still
    # resolved through the shared `_resolve` helper (TASK-040) -- this is
    # what actually exercises its own rejection path now that advection
    # and diffusion no longer do.
    config = NumericsConfig(time_integration="does_not_exist")  # type: ignore[arg-type]

    with pytest.raises(UnknownSchemeError, match="does_not_exist"):
        assemble_numerics(config)


def test_unknown_linear_solver_name_raises_named() -> None:
    # linear_solver's own rejection path, for symmetry with every other
    # component's dedicated test in this module -- previously untested on
    # its own, only ever exercised incidentally through whichever
    # component's test happened to hit `_resolve`'s shared line first.
    config = NumericsConfig(linear_solver="does_not_exist")  # type: ignore[arg-type]

    with pytest.raises(UnknownSchemeError, match="does_not_exist"):
        assemble_numerics(config)


def test_unknown_pressure_coupling_name_raises_named() -> None:
    config = NumericsConfig(pressure_coupling="does_not_exist")  # type: ignore[arg-type]

    with pytest.raises(UnknownSchemeError, match="does_not_exist"):
        assemble_numerics(config)


def test_periodic_boundary_faces_are_omitted_from_the_assembled_map() -> None:
    # `BoundaryCondition` has no periodic shape (TASK-019's own scope) --
    # `assemble_numerics` reports the configured type but does not
    # fabricate an object for it.
    config = NumericsConfig(
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="periodic", velocity=None, pressure=None),
            south=BoundaryFaceConfig(type="periodic", velocity=None, pressure=None),
        )
    )

    assembled = assemble_numerics(config)

    assert assembled.names["boundary_conditions.north"] == "periodic"
    assert "north" not in assembled.boundary_conditions
    assert "south" not in assembled.boundary_conditions
    assert "east" in assembled.boundary_conditions
    assert "west" in assembled.boundary_conditions


def test_dirichlet_and_neumann_faces_report_the_configured_value() -> None:
    config = NumericsConfig(
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=2.5, pressure=None),
            east=BoundaryFaceConfig(type="neumann", velocity=None, pressure=None),
        )
    )

    assembled = assemble_numerics(config)

    assert assembled.boundary_conditions["north"].kind == "value"
    assert assembled.boundary_conditions["east"].kind == "gradient"


def test_boundary_conditions_is_a_mapping() -> None:
    assembled = assemble_numerics(NumericsConfig())
    assert isinstance(assembled.boundary_conditions, Mapping)


def test_boundary_conditions_is_immutable() -> None:
    # TASK-040's own review cycle: `assemble_numerics` now hands the same
    # mapping to two different factories before returning it on a frozen
    # dataclass -- genuinely read-only (`MappingProxyType`), not just
    # conventionally so.
    assembled = assemble_numerics(NumericsConfig())
    with pytest.raises(TypeError):
        assembled.boundary_conditions["north"] = None  # type: ignore[index]


def test_advection_and_diffusion_factories_receive_the_resolved_boundary_conditions() -> None:
    # Every other test-only scheme in this module discards its
    # `boundary_conditions` argument -- this is the one that proves
    # `assemble_numerics` actually threads the mapping it just resolved
    # into the advection factory, not an empty or stale one.
    name = "test_only_capturing_advection_for_assembly_test"
    register_advection_scheme(name, _CapturingAdvection)
    config = NumericsConfig(
        advection=name,  # type: ignore[arg-type]
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=2.5, pressure=None),
        ),
    )

    assembled = assemble_numerics(config)

    assert isinstance(assembled.advection, _CapturingAdvection)
    assert assembled.advection.received_boundary_conditions == assembled.boundary_conditions
    assert assembled.advection.received_boundary_conditions["north"].kind == "value"


def test_diffusion_factory_receives_the_resolved_boundary_conditions_and_coefficient() -> None:
    # Every other test-only scheme in this module discards its
    # constructor arguments -- this is the one that proves
    # `assemble_numerics` actually threads the resolved boundary
    # conditions *and* `config.diffusion_coefficient` into the diffusion
    # factory, not stale or default ones.
    name = "test_only_capturing_diffusion_for_assembly_test"
    register_diffusion_scheme(name, _CapturingDiffusion)
    config = NumericsConfig(
        diffusion=name,  # type: ignore[arg-type]
        diffusion_coefficient=3.5,
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=2.5, pressure=None),
        ),
    )

    assembled = assemble_numerics(config)

    assert isinstance(assembled.diffusion, _CapturingDiffusion)
    assert assembled.diffusion.received_boundary_conditions == assembled.boundary_conditions
    assert assembled.diffusion.received_diffusion_coefficient == 3.5


# -- The reference ("null") implementations' own behaviour -----------------
#
# `assemble_numerics` only proves these construct; the module docstring's
# "computes nothing" claim about each is itself a claim worth checking,
# not just asserting.


def test_default_config_resolves_a_real_advection_scheme() -> None:
    # Stage 4 Completion Criterion 2: a configured name resolves to the
    # new real class, checked by asserting the resolved instance's type,
    # not just that the name still validates.
    assembled = assemble_numerics(NumericsConfig())
    assert isinstance(assembled.advection, FirstOrderUpwindAdvection)


def test_default_config_resolves_a_real_diffusion_scheme() -> None:
    # Stage 4 Completion Criterion 2, diffusion's own share (TASK-024):
    # same shape as advection's version above.
    assembled = assemble_numerics(NumericsConfig())
    assert isinstance(assembled.diffusion, CentralDifferenceDiffusion)


def test_default_config_resolves_a_real_time_integrator() -> None:
    # Stage 4 Completion Criterion 2, time integration's own share
    # (TASK-025): same shape as advection's/diffusion's versions above.
    assembled = assemble_numerics(NumericsConfig())
    assert isinstance(assembled.time_integration, RK4Integrator)


def test_default_config_resolves_a_real_linear_solver() -> None:
    # Stage 4 Completion Criterion 2, linear solver's own share
    # (TASK-026): same shape as advection's/diffusion's/time
    # integration's versions above.
    assembled = assemble_numerics(NumericsConfig())
    assert isinstance(assembled.linear_solver, ConjugateGradientSolver)


def test_default_config_resolves_a_real_pressure_coupling() -> None:
    # Stage 4 Completion Criterion 2, pressure-velocity coupling's own
    # share (TASK-027): same shape as advection's/diffusion's/time
    # integration's/linear solver's versions above.
    assembled = assemble_numerics(NumericsConfig())
    assert isinstance(assembled.pressure_coupling, PISO)


def test_default_config_resolves_a_real_dirichlet_boundary_condition() -> None:
    # Stage 4 Completion Criterion 2, Dirichlet's own share (TASK-028):
    # every default face is "dirichlet" (`schema.py`'s own default), so
    # all four resolve to the real class, same shape as the five checks
    # above.
    assembled = assemble_numerics(NumericsConfig())
    for face in ("north", "south", "east", "west"):
        assert isinstance(assembled.boundary_conditions[face], DirichletBoundaryCondition)


def test_a_neumann_typed_config_resolves_a_real_neumann_boundary_condition() -> None:
    # Stage 4 Completion Criterion 2, Neumann's own share (TASK-029): the
    # default config has no "neumann" face to check by default (every
    # default face is "dirichlet"), so this configures one explicitly,
    # same shape as `test_dirichlet_and_neumann_faces_report_the_
    # configured_value` above.
    config = NumericsConfig(
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="neumann", velocity=None, scalar_gradient=0.0)
        )
    )
    assembled = assemble_numerics(config)
    assert isinstance(assembled.boundary_conditions["north"], NeumannBoundaryCondition)


def test_pressure_coupling_factory_receives_the_resolved_boundary_conditions() -> None:
    # Every other test-only strategy in this module discards its
    # `boundary_conditions` argument -- this is the one that proves
    # `assemble_numerics` actually threads the mapping it just resolved
    # into the pressure_coupling factory too, not just advection/diffusion.
    name = "test_only_capturing_pressure_coupling_for_assembly_test"
    register_pressure_coupling(name, _CapturingPressureCoupling)
    config = NumericsConfig(
        pressure_coupling=name,  # type: ignore[arg-type]
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=2.5, pressure=None),
        ),
    )

    assembled = assemble_numerics(config)

    assert isinstance(assembled.pressure_coupling, _CapturingPressureCoupling)
    assert assembled.pressure_coupling.received_boundary_conditions == assembled.boundary_conditions
    assert assembled.pressure_coupling.received_boundary_conditions["north"].kind == "value"


def test_boundary_conditions_evaluate_the_configured_value() -> None:
    # "north"/"west" are real `DirichletBoundaryCondition`s (TASK-028):
    # each reads `scalar_value`, not `velocity`/`pressure` -- those two
    # are reserved for the momentum/pressure system `GreenGaussDivergence`/
    # PISO read through this same mapping (`schema.py`'s own
    # `BoundaryFaceConfig.scalar_value` docstring). "east" is a real
    # `NeumannBoundaryCondition` (TASK-029): reads `scalar_gradient`, its
    # own Dirichlet-side counterpart -- given a `velocity` deliberately
    # distinct from `scalar_gradient` here (`docs/practices.md`'s
    # "distinct factors" rule), so a regression reading the wrong field
    # cannot pass by coincidence the way a shared `0.0` would let it.
    config = NumericsConfig(
        boundary_conditions=BoundaryConditionsConfig(
            north=BoundaryFaceConfig(type="dirichlet", velocity=None, scalar_value=3.0),
            east=BoundaryFaceConfig(type="neumann", velocity=9.0, scalar_gradient=4.0),
            west=BoundaryFaceConfig(
                type="dirichlet", velocity=None, pressure=1.5, scalar_value=1.5
            ),
        )
    )
    assembled = assemble_numerics(config)

    mesh = _mesh()
    field = ScalarField(mesh, "temperature")
    boundary_face = next(f for f in range(mesh.num_faces) if mesh.is_boundary_face(f))

    assert assembled.boundary_conditions["north"].evaluate(field, boundary_face) == 3.0
    assert assembled.boundary_conditions["east"].evaluate(field, boundary_face) == 4.0
    assert assembled.boundary_conditions["west"].evaluate(field, boundary_face) == 1.5


# -- Duplicate registration -----------------------------------------------
#
# The registries are module-level and populated by import side effect, so
# "last import wins" would otherwise be silent. Stage 4's specific hazard:
# a real scheme (TASK-023 onward) registered under an MVP name while
# `assembly.py`'s reference registration for that name is still in place.


def test_registering_a_different_factory_under_an_existing_name_raises() -> None:
    name = "test_only_duplicate_registration_probe"
    register_advection_scheme(name, _TestOnlyAdvection)

    with pytest.raises(DuplicateSchemeError, match=name):
        register_advection_scheme(name, _OtherTestOnlyAdvection)


def test_registering_over_a_reference_implementation_raises() -> None:
    # The Stage 4 case, stated directly: whoever lands a real scheme must
    # remove `assembly.py`'s reference registration in the same change,
    # rather than shadowing it and depending on import order.
    with pytest.raises(DuplicateSchemeError, match="first_order_upwind"):
        register_advection_scheme("first_order_upwind", _TestOnlyAdvection)


def test_reregistering_the_identical_factory_is_allowed() -> None:
    # Registering the same factory twice is a no-op, not a conflict --
    # a module imported twice in one session must not raise.
    name = "test_only_idempotent_registration_probe"
    register_advection_scheme(name, _TestOnlyAdvection)
    register_advection_scheme(name, _TestOnlyAdvection)

    config = NumericsConfig(advection=name)  # type: ignore[arg-type]
    assert isinstance(assemble_numerics(config).advection, _TestOnlyAdvection)
