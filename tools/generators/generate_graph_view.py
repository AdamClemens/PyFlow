"""Render the knowledge graph as a browsable page under ``build/``.

``make graph``. Nothing this writes is committed, and nothing checks it
for staleness, because there is nothing committed to be stale against --
it is regenerated on demand from ``planning/data/*.yaml``, the same
arrangement the HTML half of ``make status-report`` already has.

**Why this is not a generated document.**
``adr/ADR-006-knowledge-graph-scope.md`` rule 3 asks that generating a
document be cheaper than maintaining the duplicate *and* checkable in
CI, which is a high bar and deliberately so. That rule governs
committing a *document*: a second copy of a fact, which drifts. This
commits nothing and duplicates nothing, so the bar does not apply. Rule
4's "the graph's primary product is validation, not generation" still
holds -- ``make check-graph`` is what makes the graph trustworthy, and
this only makes it legible.

**Why it exists.** On 2026-09-04 the graph reached 102 entities and 257
edges across six categories, of which exactly 17 edges -- the nine
engine layers in ``components.yaml`` -- had any rendered form at all
(``docs/planning/dependency-tree.md``). The graph could tell you it was
*wrong*; it could not show you what it *was*. Asked how to look at it,
the honest answer was that you read the YAML.

The first thing rendering it turned up was that 33 of the roadmap's 45
task entries named themselves by number alone, their titles orphaned on
the line below the heading -- fixed in the same change, and now held by
``check-stages``'s ``task-heading-carries-title``.
"""

from __future__ import annotations

import html
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "planning" / "data"
OUTPUT_PATH = REPO_ROOT / "build" / "graph.html"

# Edge direction reads "<entity> <type> <target>", so an incoming edge
# reads backwards. These are the phrasings that make the reverse
# direction a sentence; an unlisted type falls back to "<type> by".
REVERSE_PHRASING = {
    "depends_on": "needed by",
    "serves": "served by",
    "belongs_to": "contains",
    "realised_by": "realises",
    "validates": "validated by",
    "builds_on": "built on by",
    "documented_in": "documents",
}


@dataclass
class Entity:
    """One node, and the edges it declares."""

    id: str
    name: str
    category: str
    edges: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Graph:
    """Every entity, indexed the three ways the page needs them."""

    entities: dict[str, Entity] = field(default_factory=dict)
    by_category: dict[str, list[Entity]] = field(default_factory=dict)
    incoming: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    dangling: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def edge_count(self) -> int:
        return sum(len(entity.edges) for entity in self.entities.values())

    @property
    def edge_types(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entity in self.entities.values():
            for edge_type, _ in entity.edges:
                counts[edge_type] = counts.get(edge_type, 0) + 1
        return dict(sorted(counts.items()))


def load_graph(root: Path = REPO_ROOT) -> Graph:
    """Read every populated data file into one graph.

    An empty file contributes no category: several are empty on purpose,
    each with a trigger recorded in `planning/model/entities.yaml`, and
    an empty heading on the page would read as a category that lost its
    content rather than one deliberately not started.

    A dangling edge is collected rather than raised on. `check-graph`
    gates those, so one should never reach here -- but a viewer that
    refuses to open is useless at exactly the moment somebody wants it
    to *find* the dangle.
    """
    graph = Graph()
    for path in sorted((root / "planning" / "data").glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        entities = raw.get("entities") or []
        if not entities:
            continue
        category = str(raw.get("category") or path.stem)
        loaded = [
            Entity(
                id=str(item["id"]),
                name=str(item.get("name") or item["id"]),
                category=category,
                edges=[
                    (str(edge["type"]), str(edge["to"]))
                    for edge in (item.get("edges") or [])
                    if edge.get("to")
                ],
            )
            for item in entities
        ]
        graph.by_category[category] = loaded
        for entity in loaded:
            graph.entities[entity.id] = entity

    for entity in graph.entities.values():
        graph.incoming.setdefault(entity.id, [])
    for entity in graph.entities.values():
        for edge_type, target in entity.edges:
            if target in graph.entities:
                graph.incoming[target].append((edge_type, entity.id))
            else:
                graph.dangling.append((entity.id, edge_type, target))
    return graph


def _reverse(edge_type: str) -> str:
    return REVERSE_PHRASING.get(edge_type, f"{edge_type} by")


def _entity_html(graph: Graph, entity: Entity) -> str:
    """One entity, with both directions of every edge it touches.

    The incoming half is the whole point: an entity's own YAML lists
    what it points at, and nothing anywhere lists what points back.
    """
    out = "".join(
        f'<li><span class="rel">{html.escape(edge_type)}</span> '
        + (
            f'<a href="#{html.escape(target)}">{html.escape(graph.entities[target].name)}</a>'
            if target in graph.entities
            else f'<span class="dangling">{html.escape(target)} (missing)</span>'
        )
        + "</li>"
        for edge_type, target in entity.edges
    )
    back = "".join(
        f'<li><span class="rel">{html.escape(_reverse(edge_type))}</span> '
        f'<a href="#{html.escape(source)}">{html.escape(graph.entities[source].name)}</a></li>'
        for edge_type, source in graph.incoming.get(entity.id, [])
    )
    columns = ""
    if out:
        columns += f"<div><h4>points at</h4><ul>{out}</ul></div>"
    if back:
        columns += f"<div><h4>pointed at by</h4><ul>{back}</ul></div>"
    if not columns:
        columns = '<div class="isolated">No edges in either direction.</div>'
    return (
        f'<article class="entity" id="{html.escape(entity.id)}">'
        f"<h3>{html.escape(entity.name)} <code>{html.escape(entity.id)}</code></h3>"
        f'<div class="edges">{columns}</div></article>'
    )


def render_html(graph: Graph, generated_at: str, sha: str) -> str:
    """The whole page, self-contained.

    No CDN, no external stylesheet, no font: it has to open from
    `build/` on a machine with no network, the same as the status
    dashboard beside it.
    """
    facts = "".join(
        f'<div class="fact"><span class="n">{value}</span>{label}</div>'
        for label, value in (
            ("entities", len(graph.entities)),
            ("edges", graph.edge_count),
            ("categories", len(graph.by_category)),
            ("edge types", len(graph.edge_types)),
        )
    )
    legend = ", ".join(f"{name} ({count})" for name, count in graph.edge_types.items())
    warning = ""
    if graph.dangling:
        items = "".join(
            f"<li><code>{html.escape(source)}</code> {html.escape(edge_type)} "
            f"<code>{html.escape(target)}</code></li>"
            for source, edge_type, target in graph.dangling
        )
        warning = (
            f'<div class="warn"><strong>{len(graph.dangling)} dangling edge(s)</strong> -- '
            f"<code>make check-graph</code> gates these, so seeing one here means it is "
            f"failing too.<ul>{items}</ul></div>"
        )

    sections = "".join(
        f'<section class="category"><h2>{html.escape(category)} '
        f'<span class="count">{len(entities)}</span></h2>'
        + "".join(_entity_html(graph, entity) for entity in entities)
        + "</section>"
        for category, entities in sorted(graph.by_category.items())
    )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>PyFlow Knowledge Graph</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto;
    padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .meta {{ color: #888; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  .facts {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem; }}
  .fact {{ border: 1px solid #8883; border-radius: 8px; padding: 0.6rem 0.9rem;
    font-size: 0.85rem; }}
  .fact .n {{ font-size: 1.3rem; font-weight: 600; display: block; }}
  .legend {{ font-size: 0.85rem; color: #888; margin-bottom: 1.5rem; }}
  .warn {{ border: 1px solid #d905; background: #d901; border-radius: 8px;
    padding: 0.75rem 1rem; margin-bottom: 1.5rem; font-size: 0.9rem; }}
  section.category {{ margin-bottom: 2rem; }}
  section.category > h2 {{ font-size: 1.1rem; border-bottom: 1px solid #8883;
    padding-bottom: 0.25rem; text-transform: capitalize; }}
  .count {{ color: #888; font-weight: 400; font-size: 0.85rem; }}
  article.entity {{ border: 1px solid #8883; border-radius: 8px; padding: 0.75rem 1rem;
    margin-bottom: 0.6rem; scroll-margin-top: 1rem; }}
  article.entity:target {{ border-color: #4a9; background: #4a91; }}
  article.entity h3 {{ font-size: 0.95rem; margin: 0 0 0.4rem; font-weight: 600; }}
  article.entity h3 code {{ font-weight: 400; color: #888; font-size: 0.8em; }}
  .edges {{ display: flex; flex-wrap: wrap; gap: 1.5rem; font-size: 0.85rem; }}
  .edges h4 {{ margin: 0 0 0.2rem; font-size: 0.75rem; text-transform: uppercase;
    letter-spacing: 0.04em; color: #888; font-weight: 600; }}
  .edges ul {{ margin: 0; padding-left: 1.1rem; }}
  .rel {{ color: #888; }}
  .dangling {{ color: #d33; }}
  .isolated {{ color: #888; font-size: 0.85rem; }}
  code {{ font-size: 0.85em; }}
</style>
</head>
<body>
<h1>PyFlow Knowledge Graph</h1>
<div class="meta">Generated from planning/data/*.yaml at {generated_at}, commit {sha}
  -- not committed, regenerate with `make graph`. What keeps the graph itself honest is
  `make check-graph`; this only makes it legible.</div>
<div class="facts">{facts}</div>
<div class="legend">Edge types: {legend}</div>
{warning}
{sections}
</body>
</html>
"""


def _current_sha(root: Path = REPO_ROOT) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except OSError, subprocess.CalledProcessError:
        return "unknown"


def main() -> int:
    graph = load_graph()
    if not graph.entities:
        print(f"No entities found under {DATA_DIR.relative_to(REPO_ROOT)} -- nothing to render.")
        return 1

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_html(graph, generated_at, _current_sha()))

    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(
        f"{len(graph.entities)} entities, {graph.edge_count} edges, "
        f"{len(graph.by_category)} categories."
    )
    if graph.dangling:
        print(
            f"{len(graph.dangling)} dangling edge(s) shown on the page -- make check-graph fails."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
