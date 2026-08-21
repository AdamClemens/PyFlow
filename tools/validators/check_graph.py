"""Fail if the planning knowledge graph is structurally inconsistent.

Validates `planning/data/*.yaml` against `planning/model/*.yaml`, per
`adr/ADR-006-knowledge-graph-scope.md` rule 4: validation is the graph's
primary product, not generation. The rules are declared in
`planning/model/validation.yaml` and implemented here; each has one test
in `tests/unit/test_check_graph.py`, keyed by the same id.

Unlike `check_claims.py`, this one **gates** -- it is part of `make ci`.
Every rule is a definite structural fact (does this id exist, is this
edge's type declared, does this path resolve) needing no judgement to
tell a real violation from a document legitimately quoting a rule, which
is the only reason `check_claims.py` had to stay advisory.

What it deliberately does not check is recorded in `validation.yaml`'s
closing comment: that a `documented_in` document actually describes its
entity, and that the graph is *complete*. Nothing can check for an entity
nobody wrote.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Fields naming repository paths, and whether the entity's `name` must
# also appear there as a heading. `must_appear_in` is the stronger claim:
# it mechanises the Blast Radius requirement `docs/architecture/engine.md`
# states in prose -- the nine layers "appear in four places that must
# stay in agreement" -- which nothing enforced before 2026-08-21.
_PATH_FIELDS = ("documented_in", "decided_by", "must_appear_in")
_NAME_MUST_APPEAR_FIELD = "must_appear_in"

# Rules whose scope is a single entity category. Declared here rather
# than inlined at the call site so the category-specific rules are
# visible in one place next to the generic ones.
_REQUIRES_REALISED_BY = "capabilities"
_REQUIRES_VALIDATES = "demos"


def _has_heading(path: Path, name: str) -> bool:
    """Whether `name` appears as a Markdown heading in `path`.

    A heading, not a mention anywhere in the text: the requirement is
    that the document actually *covers* the entity, and a passing
    reference would satisfy a substring match in any document that
    merely refers to it. Any heading level counts --
    `docs/architecture/engine.md` uses `###` for its layers and
    `docs/implementation/upgrade-paths.md` uses `##`, which is a
    formatting difference rather than a semantic one.
    """
    pattern = re.compile(r"^#{1,6}\s+" + re.escape(name) + r"\s*$", re.MULTILINE)
    return bool(pattern.search(path.read_text(encoding="utf-8")))


def _load_yaml(path: Path) -> Any:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_relationships(root: Path) -> dict[str, tuple[str, str]]:
    """`{type: (from_category, to_category)}` from `relationships.yaml`."""
    raw = _load_yaml(root / "planning" / "model" / "relationships.yaml") or {}
    declared: dict[str, tuple[str, str]] = {}
    for relationship in raw.get("relationships") or []:
        declared[relationship["type"]] = (relationship["from"], relationship["to"])
    return declared


def _data_files(root: Path) -> list[Path]:
    data_dir = root / "planning" / "data"
    if not data_dir.is_dir():
        return []
    # Empty files are legitimate: `entities.yaml` records, per category,
    # why an unpopulated one is unpopulated and what would trigger
    # filling it (ADR-006 rule 6). An empty file has nothing to check,
    # which is different from having nothing to say about it.
    return sorted(p for p in data_dir.glob("*.yaml") if p.stat().st_size > 0)


def _find_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """A `depends_on` cycle as the actual node sequence, or `None`.

    Returns the cycle itself rather than a bare boolean: a checker that
    says only "there is a cycle" leaves the reader to redo the search it
    has already done.
    """
    visiting: set[str] = set()
    done: set[str] = set()
    stack: list[str] = []

    def walk(node: str) -> list[str] | None:
        if node in done:
            return None
        if node in visiting:
            return stack[stack.index(node) :] + [node]
        visiting.add(node)
        stack.append(node)
        for target in edges.get(node, []):
            cycle = walk(target)
            if cycle is not None:
                return cycle
        stack.pop()
        visiting.discard(node)
        done.add(node)
        return None

    for node in sorted(edges):
        cycle = walk(node)
        if cycle is not None:
            return cycle
    return None


def check_graph(root: Path = REPO_ROOT) -> list[str]:
    """Every rule violation, as `<rule-id>: <detail>` strings.

    `root` is a parameter so the test suite can build miniature graphs in
    `tmp_path`: a test asserting against the real `planning/` tree would
    fail every time the graph legitimately changed, for reasons unrelated
    to the rule under test.
    """
    findings: list[str] = []
    declared_types = _load_relationships(root)

    # -- Pass one: entities, and the rules that need only one entity ----
    entities: dict[str, dict[str, Any]] = {}
    category_of: dict[str, str] = {}

    for path in _data_files(root):
        rel = path.relative_to(root).as_posix()
        raw = _load_yaml(path) or {}
        expected = path.stem
        if raw.get("category") != expected:
            findings.append(
                f"category-matches-filename: {rel} declares category "
                f"{raw.get('category')!r}, expected {expected!r}"
            )

        for entity in raw.get("entities") or []:
            entity_id = entity.get("id")
            if not entity_id:
                findings.append(f"entity-has-name: {rel} has an entity with no id")
                continue
            if not entity.get("name"):
                findings.append(f"entity-has-name: {rel}: {entity_id} has no name")
            if not ID_PATTERN.match(str(entity_id)):
                findings.append(
                    f"entity-id-well-formed: {rel}: {entity_id!r} is not lowercase-hyphen-separated"
                )
            if entity_id in entities:
                findings.append(
                    f"entity-id-unique: {entity_id!r} in {rel} is already "
                    f"defined in {category_of[entity_id]}"
                )
                continue
            entities[entity_id] = entity
            category_of[entity_id] = expected

            for field in _PATH_FIELDS:
                value = entity.get(field)
                paths = [value] if isinstance(value, str) else (value or [])
                for referenced in paths:
                    target = root / referenced
                    if not target.is_file():
                        findings.append(
                            f"referenced-files-exist: {rel}: {entity_id}'s "
                            f"{field} names {referenced}, which does not exist"
                        )
                        continue
                    name = entity.get("name")
                    if field == _NAME_MUST_APPEAR_FIELD and name:
                        if not _has_heading(target, str(name)):
                            findings.append(
                                f"entity-name-appears-in-sources: {rel}: "
                                f"{entity_id} is named {name!r}, but "
                                f"{referenced} has no heading for it"
                            )

    # -- Pass two: edges, which need every entity to be known first -----
    dependency_edges: dict[str, list[str]] = {}

    for entity_id, entity in entities.items():
        source_category = category_of[entity_id]
        edge_types = set()
        for edge in entity.get("edges") or []:
            edge_type = edge.get("type")
            target = edge.get("to")
            edge_types.add(edge_type)

            if edge_type not in declared_types:
                findings.append(
                    f"edge-type-declared: {entity_id} declares edge type "
                    f"{edge_type!r}, which is not in relationships.yaml"
                )
                continue

            if target not in entities:
                findings.append(
                    f"edge-target-exists: {entity_id} --{edge_type}--> "
                    f"{target!r}, which is not an entity in this graph"
                )
                continue

            from_category, to_category = declared_types[edge_type]
            if source_category != from_category or category_of[target] != to_category:
                findings.append(
                    f"edge-endpoints-typed: {entity_id} ({source_category}) "
                    f"--{edge_type}--> {target} ({category_of[target]}); "
                    f"{edge_type} is declared {from_category} -> {to_category}"
                )
                continue

            if edge_type == "depends_on":
                dependency_edges.setdefault(entity_id, []).append(target)

        if source_category == _REQUIRES_REALISED_BY and "realised_by" not in edge_types:
            if not entity.get("unresolved"):
                findings.append(
                    f"capability-realised-or-unresolved: {entity_id} has no "
                    "realised_by edge and does not declare why not"
                )
        if source_category == _REQUIRES_VALIDATES and "validates" not in edge_types:
            findings.append(f"demo-validates-something: {entity_id} validates no capability")

    cycle = _find_cycle(dependency_edges)
    if cycle is not None:
        findings.append("no-dependency-cycles: " + " -> ".join(cycle))

    return findings


def main() -> int:
    findings = check_graph()
    if findings:
        for finding in findings:
            print(finding)
        print(f"\n{len(findings)} graph consistency error(s) found.")
        return 1

    print("Knowledge graph is consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
