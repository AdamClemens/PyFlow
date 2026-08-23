"""Fail if prose names a repository path that does not exist.

``check_docs.py`` validates Markdown *links*. This project barely uses
them: it cross-references itself with backticked paths --
``docs/practices.md``, ``src/pyflow/engine/mesh.py`` -- hundreds of
times, and nothing checked any of them until 2026-08-22, when a manual
sweep found real dangling references among them.

Tuned deliberately for signal over completeness. A backticked span is
checked only when it contains a ``/`` and ends in a known source or
document extension. It resolves if it matches a tracked path from the
repository root, relative to the containing file (``..`` included), by
prefix (``adr/ADR-003`` matches ``adr/ADR-003-modular-...md``), or as a
**path-component suffix** of a tracked file. That last rule is what
makes the check usable: this repository routinely names a path relative
to the section it is writing about rather than to the file it is writing
in -- ``golden-demos/empty_window.yaml`` inside a passage about
``examples/``, ``rendering/canvas.py`` from a sibling package's
``CLAUDE.md``. Everything else is left alone: the alternative is a
checker that cries wolf, which is worse than no checker because people
stop reading it.

**Deliberate exclusions**, each for a stated reason rather than to make
the output green:

* ``docs/CHANGELOG-DESIGN.md`` -- a dated historical record whose job
  includes naming files that were later retired.
* Paths a document explicitly says do not exist. This script cannot read
  that intent, so a genuine "there is no ``X``" sentence would be a
  false positive; ``ALLOWED_MISSING`` names those, each with a comment.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Documents whose job includes naming things that no longer exist.
# `check_manifest.py` learned this the expensive way: a rule asserting
# "every path the manifest names exists" was written, run against the
# real tree, produced 44 findings that were essentially all false, and
# was dropped before shipping -- see `tools/validators/CLAUDE.md` and
# `tests/unit/test_check_manifest.py::test_a_retired_path_the_manifest_still_names_is_not_reported`,
# which pins that decision so nobody re-adds it without seeing why it
# went. This script is that rule returning in a narrower form, and it
# stays narrow by excluding the three documents that made the original
# unworkable rather than by growing an exemption list until it means
# nothing.
EXCLUDED_FILES = {
    # A dated historical record; naming retired files is its function.
    "docs/CHANGELOG-DESIGN.md",
    # Records what was retired and why, in section-relative prose.
    "docs/repository-manifest.md",
    # Part III is an audit archive quoting inventories that were wrong
    # at the time -- including a handbook structure that never existed.
    "docs/planning/backlog.md",
}

# Paths named in prose precisely to say they are absent, or as templates.
ALLOWED_MISSING = {
    # `docs/repository-manifest.md` and `backlog.md` both state the
    # handbook README asymmetry as an open item: these two do not exist
    # and the documents say so.
    "docs/handbook/README.md",
    "numerical-methods/README.md",
    # A naming template, not a file (`adr/README.md`).
    "adr/ADR-00N-title.md",
    # KA-034's superseded artifact: the roadmap records that this file
    # was specified and deliberately never created.
    "docs/implementation/stages/stage-0.md",
    # Retired 2026-08-15, named in the backlog's record of the decision.
    "docs/planning/glossary.md",
    "docs/handbook.md",
    "docs/planning/numerical-frameworks.md",
    "examples/golden-demos/empty_window.py",
    "prompts/code/CLAUDE.md",
    "prompts/docs/CLAUDE.md",
}

# Artifacts a roadmap task promises but has not built yet. Each entry is
# a *checked promise*, not an exemption: when its task lands, delete the
# entry -- and if the implementation named the file something else, this
# check fails and one of the two is wrong. Keep the task id on every
# line so the trigger for removing it is unmissable.
PLANNED: dict[str, str] = {
    "src/pyflow/engine/numerics/linear_solver.py": "TASK-022",
    "tests/unit/numerics/test_linear_solver_contract.py": "TASK-022",
    "src/pyflow/engine/numerics/pressure_coupling.py": "TASK-021",
    "src/pyflow/engine/numerics/assembly.py": "TASK-021",
    "examples/golden-demos/numerics_assembly.yaml": "TASK-021",
    "tests/golden/test_numerics_assembly.py": "TASK-021",
    "tests/features/numerics_assembly.feature": "TASK-021",
}

EXTS = (".md", ".py", ".yaml", ".yml", ".toml", ".cfg", ".txt", ".lock", ".json", ".ini")
SPAN = re.compile(r"`([^`\n]+)`")
CANDIDATE = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./{},-]*$")
BRACE = re.compile(r"^(.*)\{([^}]*)\}(.*)$")


def tracked_paths() -> tuple[set[str], set[str]]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.replace("\r", "")
    files = {line for line in out.split("\n") if line}
    dirs: set[str] = set()
    for f in files:
        parts = f.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    return files, dirs


def expand_braces(path: str) -> list[str]:
    """``a/{b,c}.py`` -> ``a/b.py``, ``a/c.py`` -- a shorthand this
    repository's prose uses constantly.
    """
    match = BRACE.match(path)
    if not match:
        return [path]
    pre, inner, post = match.groups()
    out: list[str] = []
    for piece in inner.split(","):
        out.extend(expand_braces(pre + piece.strip() + post))
    return out


def _normalise(path: str) -> str:
    """Collapse ``a/b/../c`` to ``a/c`` without touching the filesystem."""
    parts: list[str] = []
    for piece in path.split("/"):
        if piece in ("", "."):
            continue
        if piece == "..":
            if parts:
                parts.pop()
            continue
        parts.append(piece)
    return "/".join(parts)


def resolves(path: str, containing_dir: str, files: set[str], dirs: set[str]) -> bool:
    path = path.rstrip("/")
    candidates = [path]
    if containing_dir:
        candidates.append(_normalise(f"{containing_dir}/{path}"))

    for base in candidates:
        if base in files or base in dirs:
            return True
        # Prefix: `adr/ADR-003` -> `adr/ADR-003-modular-...md`.
        if any(f.startswith(base) for f in files):
            return True

    # Path-component suffix: `golden-demos/empty_window.yaml` names
    # `examples/golden-demos/empty_window.yaml`. Anchored on "/" so
    # `mesh.py` cannot match `structured_mesh.py`.
    suffix = "/" + path
    return any(f == path or f.endswith(suffix) for f in files) or any(
        d == path or d.endswith(suffix) for d in dirs
    )


def check_file(md: Path, rel: str, files: set[str], dirs: set[str]) -> list[tuple[int, str]]:
    containing = "/".join(rel.split("/")[:-1])
    found: list[tuple[int, str]] = []
    seen: set[str] = set()
    for lineno, line in enumerate(md.read_text(encoding="utf-8").split("\n"), 1):
        for span in SPAN.findall(line):
            candidate = span.strip()
            if not CANDIDATE.match(candidate):
                continue
            for expanded in expand_braces(candidate):
                if "/" not in expanded or not expanded.endswith(EXTS):
                    continue
                if expanded in ALLOWED_MISSING or expanded in PLANNED or expanded in seen:
                    continue
                if not resolves(expanded, containing, files, dirs):
                    seen.add(expanded)
                    found.append((lineno, expanded))
    return found


def main() -> int:
    files, dirs = tracked_paths()
    total = 0
    for rel in sorted(f for f in files if f.endswith(".md")):
        if rel in EXCLUDED_FILES:
            continue
        for lineno, path in check_file(REPO_ROOT / rel, rel, files, dirs):
            print(f"{rel}:{lineno}: names '{path}', which does not exist")
            total += 1

    landed = sorted(name for name in PLANNED if name in files)
    for name in landed:
        print(
            f"PLANNED['{name}'] ({PLANNED[name]}) now exists -- "
            f"delete the entry so the path is checked like any other"
        )
        total += 1

    if total:
        print(
            f"\n{total} path-reference problem(s) found. If a missing path is "
            f"deliberate -- prose stating a file is absent -- add it to "
            f"ALLOWED_MISSING with a comment saying why, rather than rewording "
            f"the prose. If it is an artifact a task has not built yet, add it to "
            f"PLANNED with its task id."
        )
        return 1

    print(
        f"Every path named in prose resolves "
        f"({len(PLANNED)} planned artifact(s) awaiting their task)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
