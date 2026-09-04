"""Unit tests for tools/generators/generate_graph_view.py.

Not part of the `pyflow` package (a repo tooling script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.

**This generator writes nothing the repository commits**, so unlike
`generate_docs_index.py` or `generate_dependency_tree.py` there is no
staleness gate to test against, and no `--check` mode. What is left
worth checking is that the page is a faithful and *complete* view of the
graph: an entity the YAML declares and the page silently omits is the
failure mode a viewer has, and it is invisible by inspection -- nobody
notices the node that isn't drawn.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_GENERATORS = REPO_ROOT / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_graph_view import (  # noqa: E402
    Graph,
    load_graph,
    render_html,
)


@pytest.fixture
def miniature(tmp_path: Path) -> Path:
    """Two categories, one edge between them, one isolated entity."""
    data = tmp_path / "planning" / "data"
    data.mkdir(parents=True)
    (data / "stages.yaml").write_text(
        "category: stages\n"
        "entities:\n"
        '  - id: stage-1\n    name: "Stage 1 — Space"\n'
        "    edges:\n      - type: serves\n        to: capability-level-1\n",
        encoding="utf-8",
    )
    (data / "capabilities.yaml").write_text(
        "category: capabilities\n"
        "entities:\n"
        '  - id: capability-level-1\n    name: "Level 1 — Engine"\n'
        '  - id: capability-level-9\n    name: "Level 9 — Nobody Points Here"\n',
        encoding="utf-8",
    )
    (data / "concepts.yaml").write_text("", encoding="utf-8")
    return tmp_path


def test_every_declared_entity_is_loaded(miniature: Path) -> None:
    graph = load_graph(miniature)
    assert set(graph.entities) == {"stage-1", "capability-level-1", "capability-level-9"}


def test_an_empty_data_file_contributes_no_category(miniature: Path) -> None:
    """`concepts.yaml` is deliberately empty and stays that way until its
    recorded trigger fires. A viewer showing an empty "concepts" heading
    would read as a category that lost its content.
    """
    assert "concepts" not in load_graph(miniature).by_category


def test_incoming_edges_are_the_reverse_of_outgoing(miniature: Path) -> None:
    """The one thing the YAML genuinely cannot show. An entity's file
    lists what it points at; nothing anywhere lists what points back,
    and that is the direction a reader asking "what depends on this?"
    needs.
    """
    graph = load_graph(miniature)
    assert graph.incoming["capability-level-1"] == [("serves", "stage-1")]


def test_an_entity_nothing_points_at_has_no_incoming_edges(miniature: Path) -> None:
    assert load_graph(miniature).incoming["capability-level-9"] == []


def test_the_page_names_every_entity(miniature: Path) -> None:
    """The omission a viewer fails at silently: nobody notices the node
    that was never drawn.
    """
    page = render_html(load_graph(miniature), "2026-09-04", "abc1234")
    for entity in load_graph(miniature).entities.values():
        assert entity.name in page


def test_the_page_loads_nothing_from_the_network(miniature: Path) -> None:
    """It has to open from `build/` on a machine with no network, the
    same as the status dashboard beside it. A CDN link would work on the
    machine that generated it and nowhere else.
    """
    page = render_html(load_graph(miniature), "2026-09-04", "abc1234")
    assert "http://" not in page
    assert "https://" not in page


def test_an_edge_to_a_missing_entity_does_not_crash_the_view(tmp_path: Path) -> None:
    """`make check-graph` gates dangling edges, so this should never
    reach the generator -- but a viewer that raises is a viewer nobody
    can use to *find* the dangle, which is exactly when they would want
    it.
    """
    data = tmp_path / "planning" / "data"
    data.mkdir(parents=True)
    (data / "stages.yaml").write_text(
        "category: stages\n"
        "entities:\n"
        '  - id: stage-1\n    name: "Stage 1"\n'
        "    edges:\n      - type: serves\n        to: nowhere\n",
        encoding="utf-8",
    )
    graph = load_graph(tmp_path)
    assert graph.dangling == [("stage-1", "serves", "nowhere")]
    assert "nowhere" in render_html(graph, "2026-09-04", "abc1234")


def test_the_real_graph_renders(tmp_path: Path) -> None:
    """Reads the committed graph, so a failure means the data is wrong
    or the generator cannot cope with it -- not that a unit is broken.
    """
    graph: Graph = load_graph(REPO_ROOT)
    assert graph.dangling == []
    page = render_html(graph, "2026-09-04", "abc1234")
    assert len(graph.entities) > 50
    assert all(entity.id in page for entity in graph.entities.values())
