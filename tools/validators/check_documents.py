"""Fail if a maintained document does not declare what keeps it honest.

Every document under the covered roots carries one ``Checked-by:`` line
naming the mechanism that keeps it true. The mechanisms are the three
this repository actually has, and the point of naming them is that they
are not equally strong:

``generated``
    The document is written by a tool from the repository's own state
    and a stale copy fails ``make ci``. It cannot drift. Never edit by
    hand.

``gated``
    Hand-written, but some specific claim in it is machine-compared
    against reality (``make check-status`` reads the roadmap's counts;
    ``make check-stages`` reads its stage structure). The gated claim
    cannot drift; everything else in the document still can.

``stage-boundary``
    Hand-written, nothing mechanical checks its meaning, and it must be
    re-read at every stage boundary. **This is not a reliable
    mechanism** and declaring it says so out loud.

**Why this exists.** Stage 7's exit audit found two documents stale for
days -- ``docs/architecture/rendering.md`` describing a package that had
gained a module, and ``docs/architecture/sequences.md`` describing a seam
whose only caller had changed -- and both were stale for the same
reason: nobody knew they were in the blast radius. The Blast Radius rule
says to work out what a change affects, and answering that from memory
is what failed. This turns "which documents does anybody check, and
how?" from tribal knowledge into an enumerated, checked inventory.

**The declaration lives in the document, not in a register file.** A
central list of documents and their mechanisms would be a second copy of
a fact, which is the exact failure mode this repository keeps finding --
and it would drift from the tree the moment a document was added. A line
inside a document cannot drift from that document.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Roots whose documents must declare a mechanism. Deliberately not every
# Markdown file in the repository: a `CLAUDE.md` is directory-local
# guidance maintained by whoever works in that directory (the root
# `CLAUDE.md`'s own standing rule), and an ADR records a decision as it
# was taken rather than describing the world today.
COVERED_ROOTS = (
    Path("docs/planning"),
    Path("docs/architecture"),
    Path("docs/implementation"),
)

MECHANISMS = ("generated", "gated", "stage-boundary")

# `Checked-by: gated (make check-status)` -- the mechanism, then an
# optional parenthetical naming the target or generator responsible.
DECLARATION = re.compile(
    r"^Checked-by:\s*(?P<mechanism>[a-z-]+)\s*(?:\((?P<by>[^)]*)\))?\s*$",
    re.MULTILINE,
)


def tracked_markdown() -> list[Path]:
    """Documents under the covered roots, from `git ls-files`.

    Tracked files rather than a filesystem walk, for the reason
    `check_claims.py` records: `.claude/worktrees/` holds a full second
    checkout while a worktree is open, and a walk reports this
    repository's own documents twice.
    """
    out = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    paths = [Path(p) for p in out]
    return sorted(
        path
        for path in paths
        if path.name != "CLAUDE.md" and any(root in path.parents for root in COVERED_ROOTS)
    )


def declaration_of(path: Path) -> tuple[str | None, str | None]:
    """The declared mechanism and its parenthetical, or `(None, None)`.

    Only the first 40 lines are scanned: a declaration belongs at the
    top of a document where a reader meets it, and scanning the whole
    file would let one hide in the middle.
    """
    head = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()[:40],
    )
    match = DECLARATION.search(head)
    if match is None:
        return None, None
    return match.group("mechanism"), (match.group("by") or "").strip() or None


def find_problems(paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        mechanism, by = declaration_of(path)
        if mechanism is None:
            problems.append(
                f"{path.as_posix()}: no 'Checked-by:' line in its first 40 lines. "
                f"Declare one of {', '.join(MECHANISMS)} -- see "
                "docs/documentation-guidelines.md for what each means."
            )
            continue
        if mechanism not in MECHANISMS:
            problems.append(
                f"{path.as_posix()}: declares unknown mechanism {mechanism!r}; "
                f"expected one of {', '.join(MECHANISMS)}"
            )
            continue
        if mechanism in ("generated", "gated") and not by:
            problems.append(
                f"{path.as_posix()}: declares {mechanism!r} but names nothing responsible. "
                f"Write 'Checked-by: {mechanism} (make <target>)' -- a mechanism with no "
                "named owner cannot be verified to exist, which is how a check goes inert."
            )
    return problems


def main() -> int:
    paths = tracked_markdown()
    if not paths:
        print("No documents found under the covered roots -- has the layout changed?")
        print("A rule that matches nothing reports nothing.")
        return 1

    problems = find_problems(paths)
    for problem in problems:
        print(problem)

    if problems:
        print(f"\n{len(problems)} undeclared document(s).")
        return 1

    counts: dict[str, list[Path]] = {}
    for path in paths:
        mechanism, _ = declaration_of(path)
        assert mechanism is not None
        counts.setdefault(mechanism, []).append(path)

    summary = ", ".join(f"{len(counts[m])} {m}" for m in MECHANISMS if m in counts)
    print(f"All {len(paths)} document(s) declare how they are kept honest ({summary}).")

    # The list an exit audit actually needs: the documents nothing
    # mechanical checks. Printed rather than restated anywhere, so it
    # cannot go stale.
    reread = counts.get("stage-boundary", [])
    if reread:
        print("\nRe-read at every stage boundary (nothing checks these mechanically):")
        for path in reread:
            print(f"  {path.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
