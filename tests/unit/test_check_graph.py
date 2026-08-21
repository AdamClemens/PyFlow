"""Unit tests for tools/validators/check_graph.py.

One test per rule id in `planning/model/validation.yaml` -- that file
states what is checked, this file proves each check works, and the
script is the mechanism. If a rule is added there, a test belongs here.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/validators/CLAUDE.md.

Every test builds a complete miniature graph in `tmp_path` rather than
asserting against the real `planning/` tree: a test that reads the real
graph would fail for reasons unrelated to the rule it covers, every time
the graph legitimately changes. The real tree is checked once, at the
bottom, which is a different assertion and says so.
"""

import sys
from pathlib import Path

import pytest

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_graph import check_graph  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]

_MODEL_RELATIONSHIPS = """\
version: 1
relationships:
  - type: depends_on
    from: components
    to: components
  - type: realised_by
    from: capabilities
    to: components
  - type: validates
    from: demos
    to: capabilities
"""


def _graph(tmp_path: Path, **data_files: str) -> Path:
    """Build a miniature graph rooted at `tmp_path`.

    Each keyword names a `planning/data/<name>.yaml` file and gives its
    body. The model is fixed; only the data varies, which is where every
    rule below actually bites.
    """
    model = tmp_path / "planning" / "model"
    model.mkdir(parents=True)
    (model / "relationships.yaml").write_text(_MODEL_RELATIONSHIPS, encoding="utf-8")

    data = tmp_path / "planning" / "data"
    data.mkdir(parents=True)
    for name, body in data_files.items():
        (data / f"{name}.yaml").write_text(body, encoding="utf-8")
    return tmp_path


def _findings(tmp_path: Path) -> str:
    return "\n".join(check_graph(tmp_path))


def test_a_well_formed_graph_has_no_findings(tmp_path: Path) -> None:
    _graph(
        tmp_path,
        components="category: components\nentities:\n  - id: mesh\n    name: Mesh\n",
        capabilities=(
            "category: capabilities\n"
            "entities:\n"
            "  - id: level-1\n"
            "    name: Level 1\n"
            "    edges:\n"
            "      - type: realised_by\n"
            "        to: mesh\n"
        ),
        demos=(
            "category: demos\n"
            "entities:\n"
            "  - id: demo-a\n"
            "    name: Demo A\n"
            "    edges:\n"
            "      - type: validates\n"
            "        to: level-1\n"
        ),
    )

    assert check_graph(tmp_path) == []


def test_category_must_match_filename(tmp_path: Path) -> None:
    _graph(tmp_path, components="category: capabilities\nentities: []\n")

    assert "category-matches-filename" in _findings(tmp_path)


def test_entity_ids_must_be_unique_across_the_whole_graph(tmp_path: Path) -> None:
    """Uniqueness is global, not per-file: an edge's `to:` addresses the
    graph, so the same id in two files makes the target ambiguous.
    """
    _graph(
        tmp_path,
        components="category: components\nentities:\n  - id: shared\n    name: A\n",
        capabilities=(
            "category: capabilities\n"
            "entities:\n"
            "  - id: shared\n"
            "    name: B\n"
            "    unresolved: nothing realises this\n"
        ),
    )

    assert "entity-id-unique" in _findings(tmp_path)


@pytest.mark.parametrize("bad_id", ["Mesh", "mesh face", "mesh_face"])
def test_entity_ids_must_be_lowercase_and_hyphenated(bad_id: str, tmp_path: Path) -> None:
    _graph(tmp_path, components=f"category: components\nentities:\n  - id: {bad_id}\n    name: X\n")

    assert "entity-id-well-formed" in _findings(tmp_path)


def test_entity_must_have_a_name(tmp_path: Path) -> None:
    _graph(tmp_path, components="category: components\nentities:\n  - id: mesh\n")

    assert "entity-has-name" in _findings(tmp_path)


def test_edge_type_must_be_declared(tmp_path: Path) -> None:
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: mesh\n"
            "    name: Mesh\n"
            "  - id: flux\n"
            "    name: Flux\n"
            "    edges:\n"
            "      - type: invented_by\n"
            "        to: mesh\n"
        ),
    )

    assert "edge-type-declared" in _findings(tmp_path)


def test_edge_endpoints_must_match_the_declared_types(tmp_path: Path) -> None:
    """`depends_on` is components -> components. A component pointing at
    a capability is the wrong shape even though both ends exist, which is
    the difference between a typed graph and a pile of links.
    """
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: mesh\n"
            "    name: Mesh\n"
            "    edges:\n"
            "      - type: depends_on\n"
            "        to: level-1\n"
        ),
        capabilities=(
            "category: capabilities\n"
            "entities:\n"
            "  - id: level-1\n"
            "    name: Level 1\n"
            "    unresolved: nothing realises this\n"
        ),
    )

    assert "edge-endpoints-typed" in _findings(tmp_path)


def test_dangling_edge_is_reported(tmp_path: Path) -> None:
    """The rule the whole model exists for."""
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: flux\n"
            "    name: Flux\n"
            "    edges:\n"
            "      - type: depends_on\n"
            "        to: no-such-component\n"
        ),
    )

    findings = _findings(tmp_path)
    assert "edge-target-exists" in findings
    assert "no-such-component" in findings


def test_dependency_cycle_is_reported_with_the_cycle(tmp_path: Path) -> None:
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: a\n"
            "    name: A\n"
            "    edges:\n"
            "      - type: depends_on\n"
            "        to: b\n"
            "  - id: b\n"
            "    name: B\n"
            "    edges:\n"
            "      - type: depends_on\n"
            "        to: a\n"
        ),
    )

    findings = _findings(tmp_path)
    assert "no-dependency-cycles" in findings
    # The cycle itself, not just that one exists -- a bare "cycle found"
    # leaves the reader to do the search the checker already did.
    assert "a" in findings and "b" in findings


def test_referenced_files_must_exist(tmp_path: Path) -> None:
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: mesh\n"
            "    name: Mesh\n"
            "    documented_in: docs/does-not-exist.md\n"
        ),
    )

    assert "referenced-files-exist" in _findings(tmp_path)


def test_referenced_file_that_exists_is_not_reported(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "real.md").write_text("# Real\n", encoding="utf-8")
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: mesh\n"
            "    name: Mesh\n"
            "    documented_in: docs/real.md\n"
        ),
    )

    assert check_graph(tmp_path) == []


def test_capability_without_realised_by_must_declare_unresolved(tmp_path: Path) -> None:
    _graph(
        tmp_path,
        components="category: components\nentities: []\n",
        capabilities="category: capabilities\nentities:\n  - id: level-7\n    name: Level 7\n",
    )

    assert "capability-realised-or-unresolved" in _findings(tmp_path)


def test_capability_with_a_declared_unresolved_is_accepted(tmp_path: Path) -> None:
    """A declared gap is a visible open question, not an error -- ADR-006
    rule 5. This is what makes Capability Level 7 representable instead
    of merely absent.
    """
    _graph(
        tmp_path,
        components="category: components\nentities: []\n",
        capabilities=(
            "category: capabilities\n"
            "entities:\n"
            "  - id: level-7\n"
            "    name: Level 7\n"
            "    unresolved: No roadmap Stage corresponds to this Level.\n"
        ),
    )

    assert check_graph(tmp_path) == []


def test_demo_must_validate_something(tmp_path: Path) -> None:
    _graph(
        tmp_path,
        demos="category: demos\nentities:\n  - id: demo-a\n    name: Demo A\n",
    )

    assert "demo-validates-something" in _findings(tmp_path)


def test_the_repositorys_own_graph_passes(tmp_path: Path) -> None:
    """A different assertion from every test above: those prove the rules
    fire, this proves the real `planning/` tree satisfies them. Kept
    separate and named so a failure here reads as "the graph is wrong",
    never as "a rule is broken".
    """
    assert check_graph(REPO_ROOT) == []


def test_must_appear_in_requires_the_name_as_a_heading(tmp_path: Path) -> None:
    """`must_appear_in` checks the entity's *name* is a heading in each
    listed document, not merely that the document exists.

    This mechanises a Blast Radius requirement
    `docs/architecture/engine.md` states and nothing enforced: the nine
    layers "appear in four places that must stay in agreement". Renaming
    a layer in one document and not the others is exactly the drift the
    2026-08-21 audit kept finding by hand.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "engine.md").write_text("# Engine\n\n### Mesh\n", encoding="utf-8")
    (docs / "upgrade-paths.md").write_text("# Upgrades\n\n## Something Else\n", encoding="utf-8")
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: mesh\n"
            "    name: Mesh\n"
            "    must_appear_in:\n"
            "      - docs/engine.md\n"
            "      - docs/upgrade-paths.md\n"
        ),
    )

    findings = _findings(tmp_path)
    assert "entity-name-appears-in-sources" in findings
    assert "upgrade-paths.md" in findings
    # engine.md has the heading, so it must not be reported.
    assert "docs/engine.md" not in findings


def test_must_appear_in_accepts_a_heading_at_any_level(tmp_path: Path) -> None:
    """`engine.md` uses `###` for its layers and `upgrade-paths.md` uses
    `##`. Both are the layer's own section; the level is a formatting
    choice, not a semantic one.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("### Pressure–Velocity Coupling\n", encoding="utf-8")
    (docs / "b.md").write_text("## Pressure–Velocity Coupling\n", encoding="utf-8")
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: pressure-velocity-coupling\n"
            "    name: Pressure–Velocity Coupling\n"
            "    must_appear_in:\n"
            "      - docs/a.md\n"
            "      - docs/b.md\n"
        ),
    )

    assert check_graph(tmp_path) == []


def test_a_name_mentioned_only_in_prose_does_not_count(tmp_path: Path) -> None:
    """A passing mention is not a section. The requirement is that each
    document actually *covers* the layer, and a heading is the checkable
    proxy for that -- matching anywhere in the text would pass for any
    document that merely refers to it.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("Mesh is discussed elsewhere in this document.\n", encoding="utf-8")
    _graph(
        tmp_path,
        components=(
            "category: components\n"
            "entities:\n"
            "  - id: mesh\n"
            "    name: Mesh\n"
            "    must_appear_in:\n"
            "      - docs/a.md\n"
        ),
    )

    assert "entity-name-appears-in-sources" in _findings(tmp_path)
