"""Generate docs/implementation/config-template.yaml: an annotated,
loadable example of every `PyFlowConfig` field, with a comment above
each one stating what counts as a valid value and what does not.

Requested directly by a user reading `src/pyflow/configuration/schema.py`
section by section to answer "what can I configure and what values does
it accept" -- exactly the restated-fact shape root `CLAUDE.md` and
`docs/CLAUDE.md` warn about (`pyflow generate-config`, TASK-039, already
produces a loadable scaffold, but `PyYAML.safe_dump` cannot emit
comments, so it carries no explanation of *why* a value would be
accepted or rejected). Hand-writing that explanation directly into a
committed YAML file would only relocate the restatement problem, not
solve it -- the same failure mode `docs/planning/dependency-tree.md` and
`docs/planning/status.md` each hit before being generated. This script
is the fix applied to configuration documentation: `FIELD_COMMENTS`
below is the one place a field's valid/invalid explanation is written,
and `missing_comment_paths()` walks the live `PyFlowConfig` dataclass
tree to fail loudly the moment a field exists there without a matching
comment -- the structural half of "kept up to date"; the semantic half
(is the *comment's content* still accurate) is the same read-the-diff
discipline `docs/practices.md`'s Blast Radius rule asks of any change to
`schema.py`, not something a script can check.

Two things this script does NOT try to check, on purpose, same reasoning
as `generate_status_report.py`'s own "deliberately does not verify
everything" section: whether a comment's *wording* is still correct
(judgement, not structure -- `check_claims.py`'s territory, and this
script has no equivalent), and whether the example *value* chosen for a
field is the most illustrative one (every value here is `PyFlowConfig()`'s
own default, deliberately -- see `render()`'s docstring for why).

Run via `make config-template` to write the file, or
`make check-config-template` (part of `make ci`) to fail if the
committed copy is stale relative to the live schema. Per root
`CLAUDE.md`, the output must never be edited by hand -- change
`src/pyflow/configuration/schema.py` and this script's `FIELD_COMMENTS`/
`SECTION_COMMENTS` instead.
"""

from __future__ import annotations

import dataclasses
import sys
import textwrap
import typing
from pathlib import Path
from typing import Any

import yaml

from pyflow.configuration.schema import PyFlowConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "docs" / "implementation" / "config-template.yaml"

_COMMENT_WIDTH = 76
_BOUNDARY_FACES = ("north", "south", "east", "west")

# One entry per top-level `PyFlowConfig` section, in declaration order.
# Checked for completeness the same way FIELD_COMMENTS is.
SECTION_COMMENTS: dict[str, str] = {
    "logging": "Logging framework settings.",
    "rendering": "Rendering window/canvas settings.",
    "mesh": (
        "Structured Cartesian mesh: where the domain starts, how big one "
        "cell is, and how many cells there are. There is no single "
        '"domain size" field -- the physical domain is '
        "extent * spacing along each axis."
    ),
    "field_display": (
        "Static field visualisation for one rendered frame (built-in "
        "demo patterns only, not a general initial-condition API)."
    ),
    "simulation": (
        "Live, repeatedly-stepped simulation seeding -- distinct from "
        "field_display above, which renders one static frame."
    ),
    "fluid": (
        "Physical properties of the simulated fluid -- separate from "
        "numerics below, which selects numerical schemes and their "
        "solver tunables, not properties of the fluid those schemes "
        "act on."
    ),
    "numerics": (
        "Numerical scheme selection (adr/ADR-003-modular-numerical-"
        "strategies.md) plus the physical/solver parameters those "
        "schemes take."
    ),
    "units": (
        "Physical-unit display conversion for the HUD (Stage 7, Rendering "
        "Annotations) -- how cell size, domain size and elapsed simulated "
        "time are labelled and scaled on screen. Does not affect the "
        "simulation itself, only how its numbers are displayed."
    ),
}

# One entry per leaf field, keyed by dotted path from PyFlowConfig.
# `numerics.boundary_conditions.<face>.*` covers all four faces
# (north/south/east/west) with one shared comment set, since
# `BoundaryFaceConfig` is structurally identical on every face.
FIELD_COMMENTS: dict[str, str] = {
    "logging.level": (
        "Valid: one of DEBUG, INFO, WARNING, ERROR, CRITICAL "
        '(case-insensitive). Invalid: any other string, e.g. "VERBOSE".'
    ),
    "rendering.backend": (
        'Valid: "glfw" (a real interactive window) or "offscreen" '
        "(renders to an in-memory array, no window -- what CI and golden-"
        "demo regression tests use). Invalid: any other string."
    ),
    "rendering.width": (
        "Valid: a positive integer, in pixels. Invalid: zero, negative, or a float."
    ),
    "rendering.height": (
        "Valid: a positive integer, in pixels. Invalid: zero, negative, or a float."
    ),
    "rendering.title": "Valid: any string. The window's title bar text.",
    "rendering.background_color": (
        "Valid: null (leaves the background unset, pygfx's own default) "
        'or a "#RRGGBB" hex string, e.g. "#1a1a2e". Invalid: a colour '
        'name ("red"), a short hex ("#fff"), or a string missing the "#".'
    ),
    "rendering.show_mesh": (
        "Valid: true or false. Invalid: anything else -- not a colour or a string."
    ),
    "rendering.grid_color": (
        'Valid: a "#RRGGBB" hex string -- unlike background_color, this '
        "one has no null/off state; show_mesh above is the switch. "
        "Invalid: null, or a malformed hex string."
    ),
    "rendering.zoom": (
        "Valid: a positive number, and within [zoom_min, zoom_max] "
        "below. Invalid: zero, negative, or outside that range."
    ),
    "rendering.pan": (
        "Valid: a pair of finite numbers [x, y] -- a world-space offset "
        "from the camera's default centring. Invalid: anything other "
        "than exactly two numbers."
    ),
    "rendering.zoom_min": (
        "Valid: a positive number, less than zoom_max. Invalid: zero, negative, or >= zoom_max."
    ),
    "rendering.zoom_max": ("Valid: a number greater than zoom_min. Invalid: <= zoom_min."),
    "rendering.show_title": (
        "Valid: true or false -- toggles the HUD title text. Invalid: anything else."
    ),
    "rendering.show_stats": (
        "Valid: true or false -- toggles the HUD timestep/elapsed-time/"
        "cell-size/domain-size stats block. Invalid: anything else."
    ),
    "mesh.origin": (
        "Valid: a pair of finite numbers [x, y] -- the mesh's own "
        "lower-left corner in world space. Invalid: anything other than "
        "exactly two numbers."
    ),
    "mesh.spacing": (
        "Valid: a pair of positive numbers [dx, dy] -- the physical "
        "size of one cell along each axis. Invalid: zero or negative."
    ),
    "mesh.extent": (
        "Valid: a pair of positive whole numbers [nx, ny] -- the "
        "*number of cells* along each axis, not a physical size (a "
        "whole number written as a float, e.g. [10.0, 4.0], is fine). "
        "Invalid: zero, negative, or fractional, e.g. [10.9, 3.99] -- "
        "rejected outright rather than rounded, since silently building "
        "a different mesh than the one asked for is worse than refusing."
    ),
    "field_display.scalar_pattern": (
        'Valid: null (draw no scalar field) or "radial_gradient", the '
        "only built-in pattern this field currently accepts. Invalid: "
        "any other string."
    ),
    "field_display.vector_pattern": (
        'Valid: null (draw no vector field) or "rotational", the only '
        "built-in pattern this field currently accepts. Invalid: any "
        "other string."
    ),
    "field_display.low_color": (
        'Valid: a "#RRGGBB" hex string. Invalid: null, or a malformed hex string.'
    ),
    "field_display.high_color": (
        'Valid: a "#RRGGBB" hex string. Invalid: null, or a malformed hex string.'
    ),
    "field_display.value_range": (
        "Valid: a pair [min, max] with max strictly greater than min. Invalid: max <= min."
    ),
    "field_display.arrow_color": (
        'Valid: a "#RRGGBB" hex string. Invalid: null, or a malformed hex string.'
    ),
    "field_display.arrow_scale": "Valid: a positive number. Invalid: zero or negative.",
    "field_display.show_legend": "Valid: true or false.",
    "field_display.render_field": (
        "Valid: null (no live field is coloured) or the name of one field "
        "declared under fields: below -- the renderer never infers which "
        "one to show. Invalid: naming a field fields: does not declare."
    ),
    "field_display.field_label": (
        "Valid: null (fall back to render_field's own name) or any "
        'string -- a human-readable legend caption, e.g. "Temperature '
        '(K)". Invalid: a non-string value.'
    ),
    "field_display.vector_label": (
        "Valid: null (no vector-scale HUD line at all) or any string -- "
        'what the arrow display represents, e.g. "Velocity". When set, '
        "the HUD states this label alongside arrow_scale wherever arrows "
        "are actually drawn. Invalid: a non-string value."
    ),
    "fields": (
        "Valid: a list of per-field declarations, each a mapping with "
        "name (a non-empty string, not reused by another declaration and "
        "not one of the reserved names pressure, velocity.0, velocity.1), "
        "initial_condition (gaussian_blob or sinusoidal_mode), "
        "diffusion_coefficient (a positive number, this field's own "
        "transport coefficient -- distinct from fluid.diffusion_coefficient "
        "below, which backs any field left undeclared), and an optional "
        "buoyancy coupling -- buoyancy_reference_value and "
        "buoyancy_coefficient, both numbers, set together or not at all -- "
        "which requires both simulation.velocity_solved: true and a "
        "numerics.source_term that can compute the body force (anything "
        'but the default "none"). Invalid: a '
        "duplicate or reserved name, an unrecognised initial_condition, a "
        "non-positive diffusion_coefficient, only one of the two buoyancy "
        "fields set, a buoyancy coupling with velocity_solved false, or a "
        'buoyancy coupling with numerics.source_term left at "none" -- '
        "the last of those loaded cleanly and silently produced no force "
        "at all until the Stage 6 exit audit (2026-08-31) rejected it. "
        "Empty (the default) means the run transports no named field."
    ),
    "simulation.velocity_pattern": (
        'Valid: null or "uniform", the only built-in pattern this field '
        "currently accepts. Invalid: any other string."
    ),
    "simulation.velocity": (
        "Valid: a pair of finite numbers [vx, vy] -- the initial "
        "velocity condition either way; whether it stays fixed or is "
        "transported afterward is velocity_solved below, not this "
        "field. Invalid: anything other than exactly two numbers."
    ),
    "simulation.velocity_solved": (
        "Valid: true or false. false (default): velocity is prescribed "
        "-- held at its initial value every frame, Stage 4's own shape. "
        "true: velocity is solved -- transported by step alongside any "
        "scalar, self-advected by its own value."
    ),
    "fluid.viscosity": (
        "Valid: a positive number -- momentum's own diffusion "
        "coefficient, distinct from diffusion_coefficient below (a "
        "transported scalar's own). Invalid: zero or negative."
    ),
    "fluid.diffusion_coefficient": (
        "Valid: a positive number (a transported scalar's own "
        "diffusivity, Gamma) -- distinct from viscosity above. "
        "Invalid: zero or negative. Migrated here from "
        "numerics.diffusion_coefficient (TASK-041); a configuration "
        "still setting the old field is rejected with a named error, "
        "not silently defaulted."
    ),
    "fluid.gravity": (
        "Valid: a pair of finite numbers [gx, gy] -- the run's own "
        "gravitational acceleration vector, only meaningful once a field "
        "declares a buoyancy coupling (fields above). Invalid: anything "
        "other than exactly two finite numbers. Default: [0.0, -9.81], "
        "downward on PyFlow's +y-up convention."
    ),
    "numerics.advection": (
        'Valid: "first_order_upwind" -- the only scheme PyFlow currently '
        "implements for this component. Invalid: any other string."
    ),
    "numerics.diffusion": (
        'Valid: "central_difference" -- the only scheme PyFlow currently '
        "implements for this component. Invalid: any other string."
    ),
    "numerics.time_integration": (
        'Valid: "rk4" -- the only scheme PyFlow currently implements '
        "for this component. Invalid: any other string."
    ),
    "numerics.timestep": (
        "Valid: a positive number. Fixed for the whole run -- PyFlow "
        "applies no automatic stability/CFL limit, so an unstable "
        "choice is not rejected at load time, only at runtime (as "
        "diverging values). Invalid: zero or negative."
    ),
    "numerics.linear_solver": (
        'Valid: "conjugate_gradient" -- the only solver PyFlow currently '
        "implements for this component. Invalid: any other string."
    ),
    "numerics.linear_solver_tolerance": (
        "Valid: a positive number -- the convergence tolerance. Invalid: zero or negative."
    ),
    "numerics.linear_solver_max_iterations": (
        "Valid: a positive integer. Invalid: zero, negative, or a float."
    ),
    "numerics.pressure_coupling": (
        'Valid: "piso" -- the only scheme PyFlow currently implements '
        "for this component. Invalid: any other string."
    ),
    "numerics.source_term": (
        'Valid: "none" (contributes nothing to any field) or '
        '"boussinesq_buoyancy" (the body-force coupling driven by any '
        "declared field's own buoyancy_reference_value/buoyancy_coefficient). "
        'Invalid: any other string, or "none" while any declared field '
        "carries a buoyancy coupling -- that combination has nothing to "
        "compute the force it declares."
    ),
    "numerics.pressure_correction_tolerance": (
        "Valid: a positive number -- the outer corrector loop's own "
        "convergence tolerance (distinct from linear_solver_tolerance "
        "above, which governs each inner linear solve, not how many "
        "corrector passes the outer loop may take). Invalid: zero or "
        "negative."
    ),
    "numerics.pressure_correction_max_iterations": (
        "Valid: a positive integer -- the outer corrector loop's own "
        "iteration limit. Invalid: zero, negative, or a float."
    ),
    "numerics.boundary_conditions.<face>.type": (
        'Valid: "dirichlet", "neumann", or "periodic". If "periodic", '
        "the OPPOSITE face (north<->south, east<->west) must also be "
        '"periodic" -- checked jointly across all four faces, not per-'
        "face. Invalid: any other string, or a lone periodic face whose "
        "pair is not also periodic."
    ),
    "numerics.boundary_conditions.<face>.velocity": (
        "Valid: null (not prescribed here) or a number -- the boundary-"
        "*normal* component only, positive = outward. A face may "
        "prescribe velocity or pressure, never both (see .pressure "
        "below); if every one of the four faces prescribes a velocity, "
        "they must sum to zero net flux, weighted by each face's "
        "physical length. On a periodic face, only null or 0.0 -- a "
        "periodic boundary wraps to its pair and reads no prescribed "
        "value. Invalid: prescribing both velocity and pressure on one "
        "face, a nonzero net flux across all four, or a nonzero "
        "velocity on a periodic face."
    ),
    "numerics.boundary_conditions.<face>.pressure": (
        "Valid: null (not prescribed here) or a number. Mutually "
        "exclusive with .velocity above on the same face, and must be "
        "null on a periodic face. Invalid: any number on a periodic "
        "face."
    ),
    "numerics.boundary_conditions.<face>.scalar_value": (
        "Valid: any finite number -- the Dirichlet value a transported "
        "scalar field is given at this face. Only read when type is "
        '"dirichlet"; harmless but unused when "neumann", and must stay '
        'at its 0.0 default when "periodic", which reads no prescribed '
        "value at all. Invalid: a nonzero value on a periodic face."
    ),
    "numerics.boundary_conditions.<face>.scalar_gradient": (
        "Valid: any finite number -- the Neumann gradient a transported "
        "scalar field is given at this face. Only read when type is "
        '"neumann"; harmless but unused when "dirichlet", and must stay '
        'at its 0.0 default when "periodic", which reads no prescribed '
        "value at all. Invalid: a nonzero value on a periodic face."
    ),
    "numerics.boundary_conditions.<face>.field_values": (
        "Valid: a mapping of field name to a finite number -- a "
        "per-field override of scalar_value above, e.g. {u: 1.0, v: "
        "0.0} for a moving lid's two velocity components. A field name "
        "absent from this mapping falls back to scalar_value. Only read "
        'when type is "dirichlet", and must be empty when "periodic". '
        "Invalid: a non-finite value, or any entry on a periodic face."
    ),
    "numerics.boundary_conditions.<face>.field_gradients": (
        "Valid: a mapping of field name to a finite number -- "
        "field_values' own Neumann counterpart, overriding "
        "scalar_gradient per field name. Only read when type is "
        '"neumann", and must be empty when "periodic". Invalid: a '
        "non-finite value, or any entry on a periodic face."
    ),
    "units.length_unit": (
        "Valid: any string -- the label shown alongside a converted "
        'length (e.g. "mm", "cm"). Purely a display label; changing it '
        "does not itself change any number. Invalid: a non-string value."
    ),
    "units.length_scale": (
        "Valid: a positive number -- how many length_unit units one "
        "simulation length unit is worth (e.g. 0.01 means one "
        "simulation unit is 1 cm if length_unit is m). 1.0 (default) "
        "displays the raw simulation number unchanged. Invalid: zero or "
        "negative."
    ),
    "units.time_unit": (
        "Valid: any string -- the label shown alongside a converted "
        'elapsed time (e.g. "ms"). Invalid: a non-string value.'
    ),
    "units.time_scale": (
        "Valid: a positive number -- how many time_unit units one "
        "simulation time unit is worth. 1.0 (default) displays the raw "
        "simulation number unchanged. Invalid: zero or negative."
    ),
}


def _resolved_field_type(cls: type, name: str) -> Any:
    return typing.get_type_hints(cls)[name]


def _leaf_paths(cls: Any, prefix: str = "") -> list[str]:
    """Every dotted leaf path `FIELD_COMMENTS` must cover, derived from
    the live dataclass tree rather than hand-listed -- so a field added
    to `schema.py` without a matching comment shows up here, not just in
    a human's memory of what the schema used to look like.
    """
    paths: list[str] = []
    for f in dataclasses.fields(cls):
        path = f"{prefix}{f.name}"
        if f.name == "boundary_conditions":
            for leaf in (
                "type",
                "velocity",
                "pressure",
                "scalar_value",
                "scalar_gradient",
                "field_values",
                "field_gradients",
            ):
                paths.append(f"{path}.<face>.{leaf}")
            continue
        resolved = _resolved_field_type(cls, f.name)
        if dataclasses.is_dataclass(resolved):
            paths.extend(_leaf_paths(resolved, prefix=f"{path}."))
        else:
            paths.append(path)
    return paths


def missing_comment_paths(config_cls: type = PyFlowConfig) -> list[str]:
    """Leaf paths (and top-level sections) with no entry in
    `FIELD_COMMENTS`/`SECTION_COMMENTS`. Empty means every field the
    live schema declares has an explanation -- the completeness half of
    "kept up to date"; `tests/unit/test_generate_config_template.py`
    asserts this is always empty, so a forgotten comment fails `make
    test`, not just `make check-config-template`.
    """
    missing: list[str] = []
    if config_cls is PyFlowConfig:
        # SECTION_COMMENTS names PyFlowConfig's own top-level *nested-
        # dataclass* sections -- a bare top-level leaf (`fields`, a plain
        # `list[FieldConfig]`, TASK-042's own addition and the first
        # list-typed field this schema has ever had) is a leaf like any
        # other and is covered by FIELD_COMMENTS below instead, the same
        # split `render()` draws.
        missing += [
            f.name
            for f in dataclasses.fields(config_cls)
            if dataclasses.is_dataclass(_resolved_field_type(config_cls, f.name))
            and f.name not in SECTION_COMMENTS
        ]
    missing += [path for path in _leaf_paths(config_cls) if path not in FIELD_COMMENTS]
    return missing


def _format_value(value: object) -> str:
    if isinstance(value, tuple):
        value = list(value)
    dumped = yaml.safe_dump(value, default_flow_style=True).strip()
    if dumped.endswith("\n..."):
        dumped = dumped[: -len("\n...")]
    return dumped


def _comment_lines(text: str, indent: str) -> list[str]:
    wrapped = textwrap.wrap(text, width=_COMMENT_WIDTH - len(indent) - 2) or [""]
    return [f"{indent}# {line}" for line in wrapped]


def _render_boundary_conditions(boundary_conditions: Any, indent: str) -> list[str]:
    lines = _comment_lines(
        "One entry per domain edge. All four faces share the same shape "
        "(BoundaryFaceConfig) and the same per-field rules, explained "
        "once below under 'north' and not repeated for the other three.",
        indent,
    )
    lines.append(f"{indent}boundary_conditions:")
    for face in _BOUNDARY_FACES:
        lines.append(f"{indent}  {face}:")
        face_config = getattr(boundary_conditions, face)
        for f in dataclasses.fields(face_config):
            if face == "north":
                comment_key = f"numerics.boundary_conditions.<face>.{f.name}"
                lines.extend(_comment_lines(FIELD_COMMENTS[comment_key], indent + "    "))
            lines.append(f"{indent}    {f.name}: {_format_value(getattr(face_config, f.name))}")
    return lines


def _render_fields(instance: Any, prefix: str, indent: str) -> list[str]:
    lines: list[str] = []
    for f in dataclasses.fields(instance):
        path = f"{prefix}{f.name}"
        value = getattr(instance, f.name)
        if f.name == "boundary_conditions":
            lines.extend(_render_boundary_conditions(value, indent))
            continue
        if dataclasses.is_dataclass(value):
            lines.append(f"{indent}{f.name}:")
            lines.extend(_render_fields(value, prefix=f"{path}.", indent=indent + "  "))
            continue
        lines.extend(_comment_lines(FIELD_COMMENTS[path], indent))
        lines.append(f"{indent}{f.name}: {_format_value(value)}")
    return lines


_BANNER = """\
# Configuration template -- every PyFlowConfig field, with a comment
# above each one stating what counts as a valid value and what does
# not.
#
# GENERATED by tools/generators/generate_config_template.py from
# src/pyflow/configuration/schema.py. Do not edit by hand -- per root
# CLAUDE.md, generated documentation is never edited manually, and
# `make check-config-template` fails if this file is stale relative to
# the live schema. To change what appears here, change schema.py (the
# value shown) or this script's FIELD_COMMENTS/SECTION_COMMENTS (the
# explanation), then run `make config-template`.
#
# Every value below is PyFlowConfig()'s own default -- this file is a
# real, loadable configuration (see
# tests/unit/test_generate_config_template.py), not a set of
# placeholder tokens that would fail `pyflow run --config` if used
# as-is. Copy it and edit the fields you actually want to change; a
# field left out of your own config file simply keeps its default.
#
# For a plain scaffold with no comments, `uv run python -m pyflow
# generate-config` produces the same defaults directly from the schema.
"""


def render(config: PyFlowConfig | None = None) -> str:
    """The full annotated template, as text.

    `config` defaults to `PyFlowConfig()` -- every field's own declared
    default -- rather than a hand-picked "more interesting" example
    value, for the same reason `pyflow generate-config` (TASK-039) uses
    `PyFlowConfig()`: a value that isn't the schema's own default is a
    second place that default could drift from, and `PyFlowConfig()` is
    already guaranteed valid (TASK-005's own acceptance criterion).
    """
    config = config if config is not None else PyFlowConfig()
    missing = missing_comment_paths(type(config))
    if missing:
        raise ValueError(
            "generate_config_template: no comment for: " + ", ".join(missing) + " -- add one to "
            "FIELD_COMMENTS/SECTION_COMMENTS in tools/generators/generate_config_template.py"
        )

    lines = [_BANNER.rstrip("\n")]
    for f in dataclasses.fields(config):
        value = getattr(config, f.name)
        lines.append("")
        if dataclasses.is_dataclass(value):
            lines.extend(_comment_lines(SECTION_COMMENTS[f.name], indent=""))
            lines.append(f"{f.name}:")
            lines.extend(_render_fields(value, prefix=f"{f.name}.", indent="  "))
        else:
            # A bare top-level leaf, not a nested-dataclass section --
            # `fields` (TASK-042) is the first field this schema has ever
            # had at this shape. `FIELD_COMMENTS` explains it directly,
            # the same as any other leaf `_render_fields` renders one
            # level down; there is no nested section here to introduce
            # with a `SECTION_COMMENTS` banner first.
            lines.extend(_comment_lines(FIELD_COMMENTS[f.name], indent=""))
            lines.append(f"{f.name}: {_format_value(value)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    content = render()
    check_only = "--check" in sys.argv[1:]

    if check_only:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else None
        if current == content:
            print("docs/implementation/config-template.yaml is up to date.")
            return 0
        print(
            "docs/implementation/config-template.yaml is stale -- the config "
            "schema or this generator's comments changed without regenerating it.\n"
            "Run 'make config-template' and commit the result."
        )
        return 1

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
