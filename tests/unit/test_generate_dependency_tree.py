"""Unit tests for tools/generators/generate_dependency_tree.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.
"""

import sys
from pathlib import Path
from typing import Any

import pytest

TOOLS_GENERATORS = Path(__file__).resolve().parents[2] / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_dependency_tree import dependency_levels, render  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _components(**deps: list[str]) -> list[dict[str, Any]]:
    """A component list from `{id: [dependency ids]}`."""
    return [
        {
            "id": name,
            "name": name.replace("-", " ").title(),
            "edges": [{"type": "depends_on", "to": target} for target in targets],
        }
        for name, targets in deps.items()
    ]


def test_components_with_no_dependencies_are_the_first_level() -> None:
    levels = dependency_levels(_components(mesh=[], solver=[], variables=["mesh"]))

    assert levels[0] == ["mesh", "solver"]
    assert levels[1] == ["variables"]


def test_a_component_appears_after_everything_it_depends_on() -> None:
    """The property that makes the output meaningful, asserted directly
    rather than by matching an expected layout -- the layout can change,
    this cannot.
    """
    components = _components(
        mesh=[],
        variables=["mesh"],
        advection=["variables", "mesh"],
        flux=["advection", "variables", "mesh"],
        time_integration=["flux"],
    )

    levels = dependency_levels(components)
    position = {name: index for index, level in enumerate(levels) for name in level}

    for component in components:
        for edge in component["edges"]:
            assert position[component["id"]] > position[edge["to"]]


def test_each_level_is_sorted_so_output_is_stable() -> None:
    """Two runs over the same graph must produce byte-identical output,
    or `make check-dependency-tree` would fail at random. Dictionary
    order is not a guarantee worth relying on here.
    """
    forward = dependency_levels(_components(zulu=[], alpha=[], mike=[]))
    backward = dependency_levels(_components(mike=[], alpha=[], zulu=[]))

    assert forward == backward == [["alpha", "mike", "zulu"]]


def test_a_cycle_raises_rather_than_looping_or_dropping_nodes() -> None:
    """`make check-graph` catches cycles first and with a better message.
    This is the backstop: a generator handed a cyclic graph must fail
    loudly, never silently emit a tree missing the cyclic components.
    """
    with pytest.raises(ValueError, match="cycle"):
        dependency_levels(_components(a=["b"], b=["a"]))


def test_rendered_output_names_every_component_and_its_dependencies() -> None:
    output = render(_components(mesh=[], variables=["mesh"]))

    assert "Mesh" in output
    assert "Variables" in output
    # The dependency is stated, not merely implied by ordering.
    assert "mesh" in output.split("Variables", 1)[1]


def test_rendered_output_says_it_is_generated() -> None:
    """Root CLAUDE.md: generated documentation must never be edited
    manually. A generated file that doesn't say so invites exactly that.
    """
    output = render(_components(mesh=[]))

    assert "generated" in output.lower()
    assert "planning/data/components.yaml" in output


def test_the_committed_dependency_tree_is_up_to_date() -> None:
    """The same assertion `make check-dependency-tree` makes, run as part
    of the ordinary suite so a stale file fails fast rather than only at
    the end of `make ci`.
    """
    from generate_dependency_tree import OUTPUT_PATH, load_components

    expected = render(load_components(REPO_ROOT))

    assert OUTPUT_PATH.read_text(encoding="utf-8") == expected
