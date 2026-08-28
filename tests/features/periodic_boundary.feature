# The acceptance criteria for Periodic Boundary (TASK-030, Stage 4's
# ninth and last task). Not a golden demo -- no config file under
# `examples/golden-demos/`, no CLI run; `tests/unit/
# test_periodic_boundary.py` binds these scenarios directly, per that
# directory's own scope (isolated logic, no process boundary).

Feature: Periodic Boundary
  Periodic bypasses `BoundaryCondition` entirely (`docs/planning/
  roadmap.md` TASK-030's own Design decision): a wrapped-neighbour cell
  is mesh geometry, not a prescribed value, so a real Advection/Diffusion
  scheme wired with a periodic pairing must consult the opposite edge's
  own owner cell directly -- through the same formula it already uses for
  a genuine interior neighbour -- rather than any `BoundaryCondition`.

  Background:
    Given a small, non-square, non-trivially-origined mesh whose cells each hold a distinct value

  Scenario: A real periodic pairing wired into advection reads the wrapped neighbour's own value, not a boundary condition
    Given a west boundary face configured periodic with its east partner
    And no boundary condition configured for that face at all
    When the advective flux is computed with inflow at that face
    Then the inflow boundary face's implied value is the wrapped neighbour's own value, not the owner's

  Scenario: A real periodic pairing wired into diffusion computes the gradient across the wrapped neighbour at one full cell width
    Given a west boundary face configured periodic with its east partner
    And no boundary condition configured for that face at all
    When the diffusive flux is computed at that face
    Then that boundary face's flux equals the diffusion coefficient times the difference between the wrapped neighbour's and the owner's own value, divided by one full grid spacing

  Scenario: A field advected once fully around a periodic domain converges toward its starting distribution as the mesh is refined
    # Advection alone, not diffusion -- diffusion's own periodic wiring is
    # already checked directly above, and diffusion is a genuinely
    # irreversible process with no reason to undo itself over one lap, so
    # it would falsify this specific claim rather than test it.
    #
    # "Matches exactly" is not the right claim at any one fixed, cheap
    # mesh: first-order upwind's own O(dx) numerical diffusion smooths a
    # field over the distance it travels regardless of how correctly the
    # wrap itself is implemented, verified numerically (not assumed)
    # before writing this scenario. What a *wrong* wrap (mirrored or
    # clamped to the owner's own cell at the periodic boundary, instead
    # of the opposite edge) cannot reproduce is refinement actually
    # closing the gap: measured directly, a real wrap's own round-trip
    # error drops by roughly 62% over a 4x mesh refinement, while a
    # mirrored/clamped one drops by only roughly 16% and stays several
    # times larger throughout -- the discriminating property this
    # scenario checks.
    Given a mesh whose east and west edges are both periodic
    And a uniform velocity field that carries the domain's own scalar field once fully around it in a whole number of real timesteps
    When the field is advected for exactly that many real timesteps, at two mesh resolutions four times apart
    Then the round-trip error at the finer resolution is well under two thirds of the error at the coarser one
