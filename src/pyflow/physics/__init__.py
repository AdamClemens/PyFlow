"""Phenomena the engine transports -- temperature, density, humidity,
passive tracers (Stage 6, docs/planning/roadmap.md TASK-035..038) and
the couplings between them, such as buoyancy.

Empty on purpose; see CLAUDE.md in this directory for the boundary this
package defends (phenomena here, numerical machinery in
engine/numerics/) and why adr/ADR-003-modular-numerical-strategies.md's
swappability claim depends on it.

This docstring read "Physical models governing the fields the engine
transports -- incompressible flow first" until 2026-08-28, which named
Stage 5's own subject and so read as a promise that Stage 5 would fill
this package. It contradicted CLAUDE.md's "empty until Stage 6, and
empty on purpose" in the same directory, and the contradiction had gone
unnoticed since TASK-000 because nothing had ever had cause to ask.
Resolved when Stage 5's completion criteria were drafted (that stage's
own design question seven, maintainer's call): Stage 5 stays entirely in
engine/, because what it writes is discretisation and orchestration,
which is the half CLAUDE.md excludes. Describing this package by the
physics PyFlow simulates, rather than by the code that belongs in it, is
what made the two disagree.
"""
