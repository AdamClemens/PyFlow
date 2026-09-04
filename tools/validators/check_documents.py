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

**Obligations are checked too** (added 2026-09-05, at the maintainer's
direction: "if something is asking for a task to update it then that
*needs* to make its way into the relevant task specification"). A
document that owes an update when some task lands declares it::

    Updated-by: TASK-030 -- Section 4's ``on_frame`` note
    Updated-by: unassigned -- Section 3's checkpointing placeholder

and this script checks three things a reader cannot: that the task
exists, that **the task's own roadmap entry names this document**, and
-- the one with teeth -- that the task is **not already Done**, because
an obligation on a finished task is overdue by definition.

**That last rule is the whole point.** ``docs/architecture/sequences.md``
asked in prose to be updated "once TASK-030 wires a live timestep loop
through it"; TASK-030 landed on 2026-08-28 and the note sat there
describing a seam nothing used for six days, on the same page as two
live paths through it. A note naming the task that will invalidate it is
not a trigger anything checks -- and nobody touches a closed task, so
"re-read it when that task is touched" never fires either.

``unassigned`` is a real obligation with no task yet, and is allowed:
recording one is better than leaving it in prose where no inventory
reaches it. It is reported rather than silently accepted, so the set is
visible.

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

# The inline marker each roadmap task carries when it is finished.
TASK_DONE = re.compile(r"\*\*Status:\s*Done\b")

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


# `Updated-by: TASK-030 -- why` or `Updated-by: unassigned -- why`.
OBLIGATION = re.compile(
    r"^Updated-by:\s*(?P<task>TASK-\d+|unassigned)\s*(?:--\s*(?P<why>.*?))?\s*$",
    re.MULTILINE,
)
ROADMAP = Path("docs/planning/roadmap.md")


def obligations_of(path: Path) -> list[tuple[str, str]]:
    """Every `(task, why)` this document declares it owes.

    Read from the whole file, not just its head: an obligation belongs
    beside the paragraph that owes it, which is wherever that paragraph
    happens to be. That is the opposite of the `Checked-by:` rule above,
    and deliberately so -- a document has one honesty mechanism, and may
    owe several updates in several places.
    """
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    return [
        (match.group("task"), (match.group("why") or "").strip())
        for match in OBLIGATION.finditer(text)
    ]


def task_entries(roadmap_text: str) -> dict[str, str]:
    """Each `TASK-NNN`'s own roadmap section, keyed by id."""
    headings = [
        (match.start(), match.group(1))
        for match in re.finditer(r"^## (TASK-\d+)\b", roadmap_text, re.MULTILINE)
    ]
    entries: dict[str, str] = {}
    for index, (start, task) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(roadmap_text)
        entries[task] = roadmap_text[start:end]
    return entries


def find_obligation_problems(paths: list[Path]) -> list[str]:
    """The three checks described in this module's docstring."""
    problems: list[str] = []
    roadmap_path = REPO_ROOT / ROADMAP
    if not roadmap_path.is_file():
        return [f"{ROADMAP.as_posix()}: not found, so no obligation can be checked"]
    roadmap_text = roadmap_path.read_text(encoding="utf-8")
    entries = task_entries(roadmap_text)

    for path in paths:
        for task, why in obligations_of(path):
            if task == "unassigned":
                if not why:
                    problems.append(
                        f"{path.as_posix()}: an unassigned obligation must say what it "
                        "owes -- write 'Updated-by: unassigned -- <what>'"
                    )
                continue
            entry = entries.get(task)
            if entry is None:
                problems.append(
                    f"{path.as_posix()}: declares an obligation on {task}, which has no "
                    "entry in docs/planning/roadmap.md"
                )
                continue
            if path.as_posix() not in entry:
                problems.append(
                    f"{path.as_posix()}: declares an obligation on {task}, but that task's "
                    "own roadmap entry never names this document -- an obligation only one "
                    "side records is one the task will not honour"
                )
            if TASK_DONE.search(entry):
                problems.append(
                    f"{path.as_posix()}: declares an obligation on {task}, which is already "
                    "Done. The update is overdue: discharge it and delete the line. "
                    "(This is the rule sequences.md needed -- it asked to be updated when "
                    "TASK-030 landed and then described a dead seam for six days.)"
                )
    return problems


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

    problems = find_problems(paths) + find_obligation_problems(paths)
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

    # Reported rather than left silent, the same way `check_references.py`
    # prints its planned-artifact count: an empty set is a fact worth
    # stating, not an absence to be assumed.
    declared = [(path, task, why) for path in paths for task, why in obligations_of(path)]
    print(f"{len(declared)} documented update obligation(s):")
    for path, task, why in declared:
        print(f"  {path.as_posix()}: {task} -- {why}")

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
