# The acceptance criteria for Prescribed Boundary Velocity Reaches The
# Schemes (TASK-052, Stage 9's first task). Not a golden demo -- no
# config file under `examples/golden-demos/`, no CLI run;
# `tests/unit/test_boundary_velocity.py` binds these scenarios directly,
# per `tests/unit/CLAUDE.md`'s own scope. The stage's visible
# demonstration is Sealed Box (`tests/features/sealed_box.feature`),
# which shows the same claim through the public CLI.
#
# **Every number below was measured against the pre-fix engine before
# these scenarios were written**, so each is a claim about a real
# difference rather than a bound chosen to pass. The headline: the
# sealed-box scenario loses 14.27% of the field on the shipped
# `smoke_transport.yaml` geometry before the fix, against the exact
# conservation pure advection in a closed domain must give.

Feature: Prescribed Boundary Velocity
  Stage 9 Completion Criteria 1 and 2. A boundary face's *transporting*
  velocity comes from what the configuration prescribes there, not from
  whichever cell happens to be inside it -- and every operator that needs
  that number gets it from the same place, so two of them cannot disagree
  about whether a wall is solid.

  # -- Criterion 1: one source, checked structurally.
  #
  # This is the scenario that would have caught the original defect, and
  # it is deliberately a source-level check rather than a behavioural
  # one. `FirstOrderUpwindAdvection` and `GreenGaussDivergence` agreed
  # about walls for every fixture in the repository at the moment they
  # were written, and disagreed for every fixture with motion near one --
  # so a behavioural check has to guess which fixture exposes the
  # difference. This one cannot be passed by two implementations that
  # happen to coincide today.

  Scenario: Both operators resolve a boundary's normal velocity through the same function
    Given the advection scheme's source and the divergence scheme's source
    Then both call boundary_normal_velocity, and neither decides a boundary's normal velocity for itself

  # -- Criterion 1: the physical claim, on a sealed domain.
  #
  # Pure advection in a closed domain must conserve exactly: with zero
  # normal velocity on every wall, every boundary face's flux is zero,
  # and interior faces cancel pairwise inside `accumulate_flux_to_cells`.
  # "Exactly" means to floating-point tolerance, not to a loose bound --
  # a bound is what let the original defect hide for sixteen days.

  Scenario: A sealed domain conserves a purely advected field exactly
    Given a closed no-slip cavity carrying a tracer, with the tracer's diffusion switched off
    When the simulation is advanced for many timesteps
    Then the tracer's domain integral is unchanged to floating-point tolerance

  # The negative control for the scenario above. Without it, "the
  # integral did not change" is also satisfied by a tracer that never
  # moved at all -- which is the shape of vacuous pass the Stage 4 exit
  # audit found in this claim's own predecessor
  # (`first_order_upwind_advection.feature`'s closed-domain scenario; see
  # `docs/practices.md`'s "When a test is found weak, ask why its fixture
  # had to be that shape").

  Scenario: The same sealed domain genuinely moves the tracer it conserves
    Given a closed no-slip cavity carrying a tracer, with the tracer's diffusion switched off
    When the simulation is advanced for many timesteps
    Then the tracer's own spatial distribution has measurably changed

  # -- Criterion 1: the wall itself, measured rather than inferred.
  # The second Then is what stops the first being satisfied by a flow
  # that simply stopped: the cells behind those walls still move.

  Scenario: No advective flux crosses a wall whose prescribed normal velocity is zero
    Given a closed no-slip cavity carrying a tracer, with the tracer's diffusion switched off
    When the simulation is advanced for many timesteps
    Then every wall face's advective flux is exactly zero
    And the cells behind those walls still carry real motion

  # -- Criterion 2: a prescribed velocity reaches the solver, and the
  # scalar's own boundary value is not mistaken for one.

  Scenario: A prescribed inflow carries the boundary's own value into the domain
    Given a boundary prescribing an inward normal velocity, and a different boundary value for the transported field
    When the advective flux is computed
    Then that boundary's advective flux is the prescribed velocity times the prescribed field value

  Scenario: The same boundary without a prescribed normal velocity transports nothing through itself
    Given a boundary prescribing no normal velocity, and a boundary value for the transported field
    When the advective flux is computed
    Then that boundary's advective flux is exactly zero

  Scenario: A prescribed outflow carries the interior cell's own value out of the domain
    Given a boundary prescribing an outward normal velocity, and a different boundary value for the transported field
    When the advective flux is computed
    Then that boundary's advective flux uses the interior cell's own value, not the boundary's

  # -- Criterion 2: the divergence operator reads the same number, so a
  # prescribed inflow is a real divergence rather than a wall.

  Scenario: The divergence operator sees a prescribed inflow as a real divergence
    Given a boundary prescribing an inward normal velocity, and a different boundary value for the transported field
    When the velocity field's divergence is computed
    Then the cell behind that boundary reports the prescribed inflow, not its own interior velocity

  # -- Criterion 2: a gradient face still extrapolates, and says so.
  # A zero-gradient velocity boundary is how an outlet is expressed: the
  # normal velocity is whatever the interior brings to it. This is the
  # one case where reading the owner cell is correct, and it has to
  # survive the fix rather than be swept up by it.

  Scenario: A boundary prescribing a velocity gradient extrapolates from the interior
    Given a boundary prescribing a velocity gradient rather than a value
    When the advective flux is computed
    Then that boundary's normal velocity is the interior cell's own
