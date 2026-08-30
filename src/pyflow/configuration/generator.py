"""Generates a valid `PyFlowConfig` YAML scaffold from the schema itself
(TASK-039).

`loader.py` validates YAML *after* it's written; this is the schema's
other direction -- YAML generated *from* the dataclasses -- so a config
author starts from something already correct rather than hand-typing
section and field names from memory against `schema.py` and discovering
a mistake only when `load_config` rejects it.

Reuses `dataclasses.asdict()` rather than a hand-written serialiser:
every config section is already a plain `@dataclass`, and `asdict()`
recursively converts a `PyFlowConfig` instance (nested dataclasses
included) into plain dicts with no extra code, the same "don't restate a
fact the schema already knows" reasoning `docs/CLAUDE.md` states for
generated documentation. One real gap `asdict()` leaves: it preserves
Python `tuple`s (`MeshConfig.origin`, `RenderingConfig.pan`), and
`yaml.safe_dump` has no representer for a bare tuple (`SafeDumper`
deliberately excludes the `!!python/tuple` tag the full `Dumper` would
use) -- `_tuples_to_lists` closes that gap before dumping, the
config-generation mirror of `MeshConfig.__post_init__`'s existing
list-to-tuple normalisation on the read side.
"""

from __future__ import annotations

import dataclasses

import yaml

from pyflow.configuration.schema import PyFlowConfig


def generate_config_yaml(config: PyFlowConfig | None = None) -> str:
    """YAML text for `config` (defaulting to `PyFlowConfig()`, i.e. the
    schema's own defaults), suitable for a user to save and edit.

    `sort_keys=False` so the output's section order matches
    `PyFlowConfig`'s own declared field order (`logging`, `rendering`,
    `mesh`), not an alphabetised one a reader has to re-map against the
    schema.
    """
    if config is None:
        config = PyFlowConfig()
    data = _tuples_to_lists(dataclasses.asdict(config))
    return yaml.safe_dump(data, sort_keys=False)


def _tuples_to_lists(value: object) -> object:
    """`value`, with every `tuple` at any nesting depth converted to a
    `list`. Everything else is returned unchanged.

    The `list` case was dead code -- no field in `schema.py` was
    list-typed -- until `PyFlowConfig.fields: list[FieldConfig]`
    (TASK-042, added 2026-08-30): `dataclasses.asdict()` turns each
    declaration into a plain dict, nested inside a real Python `list`,
    so this function now has to recurse into one. None of `FieldConfig`'s
    own fields are tuple-typed today, so the recursion currently finds
    nothing to convert -- kept anyway, on the same "don't wait for a
    field to need it" reasoning this project uses everywhere else a
    generic pass exists.
    """
    if isinstance(value, tuple):
        return [_tuples_to_lists(item) for item in value]
    if isinstance(value, list):
        return [_tuples_to_lists(item) for item in value]
    if isinstance(value, dict):
        return {key: _tuples_to_lists(item) for key, item in value.items()}
    return value
