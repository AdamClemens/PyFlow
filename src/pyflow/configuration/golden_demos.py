"""A curated, stable registry of the golden demos shipped under
`examples/golden-demos/` (TASK-043), and `--demos <name-or-number>`'s
own resolution logic.

**An explicit registry, not derived from the directory listing --
deliberately, and a real trade-off, not an oversight.** A first design
sorted `examples/golden-demos/*.yaml` alphabetically and used each file's
own stem as its name: simpler, and self-updating, but it makes the
*number* unstable (a new demo inserted alphabetically ahead of existing
ones reshuffles every number after it) and ties the exposed *name* to
whatever a YAML file happens to be called, with no guarantee it is short
or memorable. The maintainer asked for both a stable number and a name
that is deliberately short-but-descriptive, which a derived list cannot
promise. `_GOLDEN_DEMOS` below is an ordered, hand-maintained list
instead: a demo's number is its position, fixed once assigned (a new demo
is appended, never inserted), and its name is chosen independently of the
underlying filename.

**This makes `_GOLDEN_DEMOS` a second source of truth for "what demos
exist" -- the real cost of that choice.** `test_registry_matches_
golden_demos_directory` (`tests/unit/test_golden_demos.py`) is the
mechanical guard against it drifting from the real directory, the same
`check-manifest`/`check-inventory` shape this repository already uses for
every other generated/derived-data pair: it fails `make test` the moment
a `*.yaml` lands under `examples/golden-demos/` with nobody adding it
here, or a registered filename stops existing.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

# name -> filename, in stable, curated order. Append new demos at the
# end -- inserting one earlier would renumber every demo after it, which
# is exactly the instability this registry exists to avoid. Names are
# deliberately short, independent of the YAML filename where the filename
# itself is longer than a name needs to be (`numerics_assembly` ->
# `numerics`, `passive_scalar_transport` -> `passive_scalar`).
_GOLDEN_DEMOS: tuple[tuple[str, str], ...] = (
    ("empty_window", "empty_window.yaml"),
    ("empty_mesh", "empty_mesh.yaml"),
    ("field_display", "field_display.yaml"),
    ("numerics", "numerics_assembly.yaml"),
    ("passive_scalar", "passive_scalar_transport.yaml"),
    ("lid_driven_cavity", "lid_driven_cavity.yaml"),
    ("heat_diffusion", "heat_diffusion.yaml"),
    ("heat_transport", "heat_transport.yaml"),
    ("thermal_buoyancy", "thermal_buoyancy.yaml"),
    ("smoke_transport", "smoke_transport.yaml"),
    ("multi_field_plume", "multi_field_plume.yaml"),
)

_DEFAULT_GOLDEN_DEMOS_DIR = Path("examples/golden-demos")


class UnknownGoldenDemoError(ValueError):
    """`identifier` (as typed on the command line) matched neither a
    registered name nor a valid 1-indexed number. `available` is
    `list_golden_demos()`'s own output at the time of the error, so the
    message is actionable without a separate `--demos` (bare) run.
    """

    def __init__(self, identifier: str, available: Sequence[str]) -> None:
        super().__init__(
            f"unknown golden demo {identifier!r}; available demos: {', '.join(available)}"
        )
        self.identifier = identifier
        self.available = tuple(available)


def list_golden_demos() -> tuple[str, ...]:
    """Every registered demo's name, in registry order."""
    return tuple(name for name, _ in _GOLDEN_DEMOS)


def resolve_golden_demo(identifier: str, base_dir: Path = _DEFAULT_GOLDEN_DEMOS_DIR) -> Path:
    """`identifier` (from `--demos`) resolved to a config path under
    `base_dir` -- a 1-indexed number (`"1"` .. `"{len(_GOLDEN_DEMOS)}"`)
    or a registered name, matched exactly. `base_dir` defaults to
    `examples/golden-demos/`, resolved relative to the current working
    directory -- the same convention `--config examples/golden-demos/
    <name>.yaml` already uses (`pyflow run` is documented as run from the
    repository root via `uv run`), so this shortcut behaves identically to
    the long form it replaces, only shorter to type.

    Raises `UnknownGoldenDemoError` for an out-of-range number or an
    unmatched name.
    """
    try:
        index = int(identifier)
    except ValueError:
        index = None

    if index is not None:
        if 1 <= index <= len(_GOLDEN_DEMOS):
            _, filename = _GOLDEN_DEMOS[index - 1]
            return base_dir / filename
        raise UnknownGoldenDemoError(identifier, list_golden_demos())

    for name, filename in _GOLDEN_DEMOS:
        if name == identifier:
            return base_dir / filename

    raise UnknownGoldenDemoError(identifier, list_golden_demos())


def format_golden_demos_listing() -> str:
    """The human-readable listing `pyflow run --demos` (with no value)
    prints: one `"<number>  <name>"` line per registered demo, in
    registry order. Index and curated name only, deliberately -- no
    one-line description per demo, which would need either parsing
    `docs/implementation/golden-demos.md` or a new config field, neither
    of which this feature has a real need for yet.
    """
    return "\n".join(f"{index}  {name}" for index, name in enumerate(list_golden_demos(), start=1))
