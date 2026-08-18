# Cloud Formation

Per `docs/planning/knowledge-architecture.md` KA-015. The physical
processes required to represent cloud formation as a future capability,
building on every other entry in this handbook
(`docs/handbook/physics/{humidity,heat-transfer,density,buoyancy}.md`).

This is the furthest-out entry in the Physics Handbook -- the capability
it describes sits at the end of `docs/implementation/upgrade-paths.md`'s
"Physics" entry (velocity/flow → heat → density/buoyancy → humidity/
species → cloud formation → additional fields), and nothing in PyFlow's
current roadmap implements it. It exists now so the physical model is
recorded before implementation begins, per this project's institutional-
memory philosophy (`prompts/global/project.md`), not because
implementation is imminent.

---

## The Phenomenon

A cloud forms when moist air is cooled (or otherwise driven) past
**saturation** -- the state in which the water vapour present reaches the
equilibrium vapour pressure for its temperature (`humidity.md`, including
its note on why this is a property of the water, not a "capacity" of the
air) -- causing some of that vapour to condense into liquid droplets (or,
at sufficiently low temperature, deposit directly as ice). This document describes condensation as the physical
process; the fluid motion that typically drives air past saturation
(buoyant rising, `buoyancy.md`) is not itself part of cloud formation,
only its most common atmospheric trigger.

## Saturation and Condensation

The saturation vapour pressure rises steeply with temperature (the
Clausius–Clapeyron relation, `humidity.md`'s "Relationship to
Temperature"). As a parcel of moist air rises, it expands and cools
(adiabatic cooling, a consequence of decreasing ambient pressure with
altitude) -- its actual water vapour content stays roughly fixed while
the saturation vapour pressure falls with the falling temperature, and
once saturation drops below the vapour actually present, the excess
condenses.
This is why clouds so often form at a distinct altitude (the **lifting
condensation level**) rather than gradually: saturation is a threshold
crossing, not a continuous process.

**Why a simple threshold rule is a defensible model here**, despite
condensation being a microphysical process this entry otherwise declines
to model: in the real atmosphere, condensation requires a surface to
condense onto, and **cloud condensation nuclei** (aerosol particles --
dust, sea salt, combustion products) are abundant enough that vapour
begins condensing onto them at supersaturations of well under a percent.
Without them, spontaneous droplet formation would need several hundred
percent relative humidity. The practical consequence is that a parcel
never departs far from saturation before condensing, so a model that
simply removes whatever excess vapour is present above saturation each
timestep -- what atmospheric models call *saturation adjustment* -- is a
good approximation rather than a crude shortcut. That approximation is an
assumption about the aerosol environment, though, not a law: it is
exactly what fails in clean maritime or laboratory conditions, and what a
genuine microphysics scheme (out of scope, below) exists to replace. Condensation itself is exactly the
sink term $\dot{S}$ `humidity.md`'s governing equation already has a
place for -- what cloud formation adds is the physical rule determining
*when* and *how much* condensation occurs, as a function of the current
humidity and temperature state.

## Latent Heat Release

Condensation is not thermally neutral: converting water vapour to liquid
releases **latent heat** (the energy that was absorbed during the
reverse process, evaporation) directly into the surrounding air, warming
it. This is a genuine two-way coupling back into `heat-transfer.md`'s
temperature field -- condensation is simultaneously a sink term for
humidity and a source term for temperature, using the same $\dot{q}$
term `heat-transfer.md`'s governing equation already has a place for.
Because this locally-released heat itself increases buoyancy
(`buoyancy.md`), latent heat release is a major amplifying mechanism in
real atmospheric convection (it is a significant part of why cumulus
clouds can develop the strong, sustained updrafts they do) -- a coupling
loop this document flags explicitly, since it links three other handbook
entries (humidity, heat transfer, buoyancy) into a single physical
process rather than three independent ones.

## Coupling Summary

Cloud formation is not a new independent physical mechanism in the sense
the other entries in this handbook are -- it is what happens when
humidity, heat transfer, and buoyancy are all present simultaneously and
allowed to interact through a threshold (saturation) process:

1. Buoyancy (or another mechanism) drives moist air to rise and cool.
2. Cooling drops the saturation vapour pressure below the vapour actually
   present (`humidity.md`'s temperature-dependence).
3. Excess vapour condenses, releasing latent heat
   (`heat-transfer.md`'s source term) and forming liquid water/ice.
4. The released heat increases local buoyancy (`buoyancy.md`), which can
   further reinforce the rising motion that started the process.

## Numerical Implications

Representing this requires two things beyond what `humidity.md`,
`heat-transfer.md`, and `buoyancy.md` already establish: (1) a
saturation calculation performed each timestep, evaluating the current
humidity against the current temperature's saturation vapour pressure to
determine condensation, and (2) a mechanism for the condensed liquid water/ice
itself -- whether tracked as its own transported field (liquid water
content, itself potentially subject to further processes such as
precipitation) or treated more simply as removed from the simulation
once condensed. Both are genuinely new pieces, not extensions of existing
advection/diffusion machinery the way humidity and temperature transport
themselves are (`humidity.md`'s and `heat-transfer.md`'s "Numerical
Implications" sections) -- the saturation/condensation coupling is a
non-linear, threshold-triggered source term coupling two fields
together, qualitatively different from a simple externally-prescribed
source.

## Scope Note

This entry deliberately stops at the physical processes needed to
represent condensation and its thermal coupling -- it does not cover
precipitation dynamics, droplet microphysics (nucleation, droplet growth,
coalescence), or ice-phase processes, all of which are real further
refinements beyond what "cloud formation" needs at the level this
handbook operates at (conceptual/architectural, not a numerical weather
prediction model's full microphysics scheme). Should PyFlow's scope
extend that far, those processes would be a further, separate extension
of the coupling described here, not a revision of it.

## References

- Rogers, R.R. and Yau, M.K., *A Short Course in Cloud Physics*, 3rd ed.,
  Butterworth-Heinemann, 1989. The standard introductory reference for
  saturation, condensation, latent heat release, and cloud
  microphysics -- Ch. 2-3 cover exactly the coupling this entry
  describes.
- Wallace, J.M. and Hobbs, P.V., *Atmospheric Science: An Introductory
  Survey*, 2nd ed., Academic Press, 2006. Ch. 3-6 cover atmospheric
  thermodynamics, adiabatic cooling, and cloud formation in the broader
  atmospheric-circulation context.

## Maintenance

Written 2026-08-17 (`docs/planning/backlog.md` E4f, closing Group E4),
against `humidity.md`, `heat-transfer.md`, `density.md` and
`buoyancy.md` -- the last of which it depends on most directly, per
KA-015's own dependency list.

Reviewed 2026-08-18: the "air's capacity to hold water vapour" framing was
replaced throughout with saturation vapour pressure (see `humidity.md`'s
note on why). Added the cloud-condensation-nuclei argument for why a
simple saturation-threshold rule is a defensible model rather than a crude
one -- and, equally, what assumption about the aerosol environment that
rule is quietly making.
