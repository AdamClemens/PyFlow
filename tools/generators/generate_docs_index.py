"""Generate docs/index.md: a navigable map of every documentation page.

The repository has plenty of documentation but, until this script, no
single page a reader could follow to get from "I don't know what exists"
to "here's the specific page I need." `README.md`'s "Where to Start"
section is the curated first-read path and stays hand-written; this
script produces the comprehensive map behind it, grouped by directory,
so it can't go stale the way a hand-maintained index would (see the open
question in docs/repository-manifest.md about that document's own
hand-maintenance, and P-002, docs/engineering-principles.md: "everything
that can reasonably be generated should be generated").

Each entry's link text is that file's first `#` heading, so the index
reflects what a page actually says it's about, not a name chosen only
for this list. A file with no heading yet (rare -- most docs open with
one) falls back to its filename. Empty files (0 bytes -- a reserved but
unwritten page, e.g. docs/architecture/overview.md) are skipped: there
is nothing yet to navigate to. Once such a file gets real content, the
next regeneration picks it up automatically -- nothing else to update.

Run via `make docs` to write docs/index.md, or `make check-docs-index`
(also part of `make ci`) to fail if the committed file doesn't match
what the current doc tree would generate -- the mechanism that keeps
this from becoming another repository-manifest.md v0.1 (docs/
repository-manifest.md: it once described ~35 files that never existed).

This file is itself generated documentation input in reverse: it reads
the tree rather than writing into it by hand, so per docs/CLAUDE.md and
root CLAUDE.md's "Generated documentation must never be edited manually"
rule, docs/index.md must never be hand-edited -- change what it lists by
adding/moving/removing the underlying doc files, then regenerate.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "docs" / "index.md"

HEADING_PATTERN = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)

# (directory relative to REPO_ROOT, section heading, recurse into subdirs?)
# Order matches docs/repository-manifest.md's directory ordering. Only
# directories holding human-facing documentation are listed here --
# prompts/ (agent-briefing material) and planning/ (machine-readable
# graph data) are deliberately excluded, per the same distinction
# docs/repository-manifest.md draws between them and docs/.
SECTIONS: list[tuple[str, str]] = [
    ("docs", "Meta"),
    ("docs/planning", "Planning"),
    ("docs/architecture", "Architecture"),
    ("docs/handbook/numerical-methods", "Handbook — Numerical Methods"),
    ("docs/handbook/physics", "Handbook — Physics"),
    ("docs/implementation", "Implementation"),
    ("docs/references", "References"),
    ("docs/tutorials", "Tutorials"),
    ("adr", "Architectural Decisions (ADRs)"),
]

EXCLUDED_NAMES = {"CLAUDE.md", "index.md"}


def title_for(md_file: Path) -> str:
    text = md_file.read_text(encoding="utf-8")
    match = HEADING_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return md_file.stem.replace("-", " ").replace("_", " ").title()


def entries_for(section_dir: str) -> list[tuple[str, Path]]:
    """Return (title, path) pairs for one section, sorted by filename."""
    directory = REPO_ROOT / section_dir
    if not directory.is_dir():
        return []
    files = sorted(
        p for p in directory.glob("*.md") if p.name not in EXCLUDED_NAMES and p.stat().st_size > 0
    )
    return [(title_for(p), p) for p in files]


def render() -> str:
    lines = [
        "# Documentation Index",
        "",
        "<!-- GENERATED FILE -- do not edit by hand.",
        "     Regenerate with `make docs` (tools/generators/generate_docs_index.py).",
        "     `make check-docs-index` fails CI if this file is stale. -->",
        "",
        "Every documentation page in the repository, grouped by directory. "
        "Link text is each page's own heading.",
        "",
        "For a curated first-read order instead of the full map, see "
        '[README.md](../README.md)\'s "Where to Start" section. For '
        "completion status per file, see "
        "[repository-manifest.md](repository-manifest.md).",
        "",
    ]

    for section_dir, heading in SECTIONS:
        lines.append(f"## {heading}")
        lines.append("")
        entries = entries_for(section_dir)
        if not entries:
            lines.append("*(no pages yet)*")
        else:
            for title, path in entries:
                rel = Path(os.path.relpath(path, start=INDEX_PATH.parent)).as_posix()
                lines.append(f"- [{title}]({rel})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    content = render()
    check_only = "--check" in sys.argv[1:]

    if check_only:
        current = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else None
        if current == content:
            print("docs/index.md is up to date.")
            return 0
        print(
            "docs/index.md is stale -- a documentation page was added, "
            "removed, renamed, or re-titled without regenerating the index.\n"
            "Run 'make docs' and commit the result."
        )
        return 1

    # newline="\n" so the output is byte-identical on every platform. Without
    # it, Python's text mode translates "\n" to "\r\n" on Windows, which made
    # docs/index.md the one file in the repository with CRLF endings on disk
    # (git's `eol=lf` normalised it away on commit, so it never showed in a
    # diff) and contradicted .editorconfig's `end_of_line = lf`.
    with INDEX_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print(f"Wrote {INDEX_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
