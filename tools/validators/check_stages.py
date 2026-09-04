"""Fail if a Stage in ``docs/planning/roadmap.md`` is missing part of the
shape a well-defined stage has.

The shape itself is declared in ``docs/planning/stage-shape.yaml``, not
here: this script is the mechanism, that file is the statement of what
is checked, and ``tests/unit/test_check_stages.py`` has one test per rule
id it declares. The prose explaining what each section is *for* is
``docs/planning/stage-specification.md``.

**Why this exists.** Stage 7 (Rendering Annotations) reached its exit
audit with no completion criteria, no discharge map and no status line.
``make ci`` was green throughout, and nothing anywhere noticed, because
there was no declared shape for the stage to be missing from --
``docs/practices.md``'s "A stage gets completion criteria before its
first task" was a rule enforced by memory, and it had already failed once
before (Stage 1, which is why the rule exists at all).

**What it deliberately does not check.** Whether a criterion is any
*good* -- whether it would fail if the intent were violated, whether its
qualifiers are checkable, whether the Goal is falsifiable. None of that
is a structural fact, and a check that guessed at it would be the kind of
judgement-shaped gate ``adr/ADR-006-knowledge-graph-scope.md`` keeps out
of ``make ci``. That job belongs to the exit audit under
``prompts/common/AUDITOR.md``'s stance. This script only ensures the
audit has something to read.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ROADMAP_PATH = REPO_ROOT / "docs" / "planning" / "roadmap.md"
SHAPE_PATH = REPO_ROOT / "docs" / "planning" / "stage-shape.yaml"
SPEC_PATH = REPO_ROOT / "docs" / "planning" / "stage-specification.md"

# `# Stage 7 — Rendering Annotations`. Both dash forms, since the file
# uses an em dash in headings and a double hyphen in prose.
STAGE_HEADING = re.compile(r"^# Stage (\d+)\s*[—-]\s*(.*?)\s*$")
# `## TASK-044` -- a task entry, with or without a trailing title.
TASK_HEADING = re.compile(r"^## (TASK-\d+)\b")
# The same heading *with* its title: `## TASK-044 -- Rendering HUD`.
# Both dash forms, as `STAGE_HEADING` above allows, because both are
# live in this corpus and neither is more correct than the other.
TASK_TITLED = re.compile(r"^## TASK-\d+\s*[\u2014-]{1,2}\s*\S")
# The inline `**Status: Done, 2026-08-31, ...` marker each task carries.
TASK_DONE = re.compile(r"\*\*Status:\s*Done\b")

LIFECYCLE_ORDER = ["sketched", "opened", "complete"]

# The shape file's own structure, as far as this script reads it: a
# mapping of lists of mappings, values left `Any` because a `note:`
# is prose and a `since_stage:` is an int.
Section = dict[str, Any]
Shape = dict[str, list[Section]]


@dataclass
class Stage:
    """One stage section of the roadmap, and where its parts sit."""

    number: int
    name: str
    start: int
    end: int
    lines: list[str] = field(default_factory=list)
    task_lines: list[int] = field(default_factory=list)
    done_tasks: int = 0

    @property
    def label(self) -> str:
        return f"Stage {self.number} ({self.name})"

    @property
    def first_task_line(self) -> int | None:
        """Index (within `lines`) of the first task heading, or `None`.

        Everything a *stage* declares sits above this: a section found
        below it belongs to a task, which is exactly how Stage 6's
        Golden Demos went missing from the stage while being present in
        the file.
        """
        return self.task_lines[0] if self.task_lines else None

    @property
    def lifecycle(self) -> str:
        if not self.task_lines:
            return "sketched"
        if self.done_tasks == len(self.task_lines):
            return "complete"
        return "opened"


def load_shape(path: Path = SHAPE_PATH) -> Shape:
    loaded: Shape = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded


def parse_stages(text: str) -> list[Stage]:
    """Split the roadmap into stage sections.

    A stage runs from its own `# Stage N` heading to the next one (or to
    the end of the file), so a section carries its own tasks with it.
    """
    lines = text.splitlines()
    starts: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = STAGE_HEADING.match(line)
        if match:
            starts.append((index, int(match.group(1)), match.group(2)))

    stages: list[Stage] = []
    for position, (index, number, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        body = lines[index:end]
        task_lines = [i for i, line in enumerate(body) if TASK_HEADING.match(line)]
        done = 0
        for order, task_line in enumerate(task_lines):
            stop = task_lines[order + 1] if order + 1 < len(task_lines) else len(body)
            if any(TASK_DONE.search(line) for line in body[task_line:stop]):
                done += 1
        stages.append(
            Stage(
                number=number,
                name=name,
                start=index,
                end=end,
                lines=body,
                task_lines=task_lines,
                done_tasks=done,
            )
        )
    return stages


def _section_line(stage: Stage, labels: list[str]) -> int | None:
    """The line a section's label sits on, or `None` if absent.

    Two forms are live in the corpus and both are accepted, but they are
    matched differently, which matters:

    * a **heading** (`## Goal`, `### Completion Criteria`,
      `## Stage 0 Completion Criteria`, `### Status as of 2026-08-29:
      ...`) matches if its text equals, starts with, or ends with the
      label -- headings carry qualifiers on both sides in this corpus;
    * a **bare line** (`Goal`, `Golden Demo`) must equal the label
      exactly.

    The bare case is strict on purpose. Matching a bare line by prefix
    makes any prose sentence opening with "Goal" or "Completion
    Criteria" count as the section, which is a checker reporting success
    for the wrong reason -- the failure mode this repository has now met
    five times (`docs/practices.md`, "A rule that matches nothing
    reports nothing").
    """
    for index, raw in enumerate(stage.lines):
        line = raw.strip()
        if not line:
            continue
        is_heading = line.startswith("#")
        text = line.lstrip("#").strip() if is_heading else line
        for label in labels:
            wanted = label.lstrip("#").strip()
            if is_heading:
                if text == wanted or text.startswith(wanted) or text.endswith(wanted):
                    return index
            elif text == wanted:
                return index
    return None


def _buried_between_tasks(stage: Stage, line: int) -> tuple[str, str] | None:
    """Whether `line` sits between two task entries, and which two.

    A stage's own section belongs in its preamble (before the first
    task) or, by the older convention Stages 0-6 use, after the last
    one. Between two tasks it reads as part of the earlier task's entry,
    which is exactly where Stage 6's Golden Demos went missing while
    being present in the file -- the whole reason presence alone is not
    enough to check.

    Markdown has no nesting, so position is the only signal available.
    `docs/planning/stage-specification.md` records why the preamble is
    the *recommended* placement without this rule demanding it: moving
    seven closed stages' sections would be churn against historical
    records, and the burial is the defect, not the trailing block.
    """
    if len(stage.task_lines) < 2:
        return None
    for order, task_line in enumerate(stage.task_lines[:-1]):
        following = stage.task_lines[order + 1]
        if task_line < line < following:
            return (
                stage.lines[task_line].lstrip("# ").strip(),
                stage.lines[following].lstrip("# ").strip(),
            )
    return None


def _orphaned_title(stage: Stage, task_line: int) -> str | None:
    """The title sitting below a bare task heading, if one is there.

    This was the shape of all 33 untitled entries found on 2026-09-04:
    the title had been written, then separated from its heading by a
    blank line, so it reads as the entry's opening sentence. Reporting
    "add a title" would send a reader to write one that already exists
    two lines down, so the message names the line to join instead.

    Deliberately narrow. It looks at the first non-empty line only, and
    accepts it only if it is short, unformatted prose -- not a heading,
    not a bold **Status:** marker, not a list item or table row. A longer
    or marked-up line is somebody's opening paragraph, and guessing that
    it is a title would produce a confidently wrong instruction.
    """
    for line in stage.lines[task_line + 1 :]:
        text = line.strip()
        if not text:
            continue
        if text.startswith(("#", "*", "-", "|", ">", "`")) or len(text) > 80:
            return None
        return text
    return None


def _required_here(section: Section, stage: Stage) -> bool:
    """Whether `section` is required of `stage` right now.

    Three independent gates, all declared in `stage-shape.yaml`:
    `required_from` (the earliest lifecycle state that needs it),
    `required_until` (the last one -- `intended-work` is a placeholder
    that real task entries supersede), and `since_stage` (a numbered
    exemption for stages that predate a convention, or that another
    document exempts).
    """
    here = LIFECYCLE_ORDER.index(stage.lifecycle)
    if here < LIFECYCLE_ORDER.index(section.get("required_from", "sketched")):
        return False
    until = section.get("required_until")
    if until is not None and here > LIFECYCLE_ORDER.index(until):
        return False
    since = section.get("since_stage")
    return not (since is not None and stage.number < since)


def explain_gaps(shape: Shape, spec_text: str) -> list[str]:
    """Sections the shape declares that the specification never explains.

    Two artifacts describe one thing -- `stage-shape.yaml` says which
    sections a stage has, `stage-specification.md` says what each is for
    -- and two artifacts describing one thing is exactly the shape that
    drifts here. This is the cheap half of keeping them together: adding
    a section to the shape file without writing the paragraph that
    explains it fails `make check-stages`.

    It cannot check that the paragraph is any *good*, only that one
    exists. That is the same bar every other rule here holds.
    """
    return [
        f"{SPEC_PATH.name}: never mentions the {section['id']!r} section, which "
        f"{SHAPE_PATH.name} requires of a stage -- a section nobody explains is a "
        "section nobody knows how to write"
        for section in shape["sections"]
        if section["id"] not in spec_text
    ]


def find_problems(stages: list[Stage], shape: Shape) -> list[str]:
    """Every rule in `stage-shape.yaml`, applied. Returns one message per
    violation; an empty list means the roadmap's stage structure is
    sound.
    """
    problems: list[str] = []
    sections = shape["sections"]

    # stage-heading-well-formed
    for stage in stages:
        if not stage.name:
            problems.append(f"Stage {stage.number}: heading has no name")

    # stage-numbers-unique
    seen: dict[int, int] = {}
    for stage in stages:
        seen[stage.number] = seen.get(stage.number, 0) + 1
    for number, count in sorted(seen.items()):
        if count > 1:
            problems.append(f"Stage {number}: declared {count} times; stage numbers must be unique")

    # stage-numbers-contiguous
    numbers = sorted(seen)
    if numbers:
        expected = list(range(numbers[0], numbers[-1] + 1))
        missing = [n for n in expected if n not in seen]
        for number in missing:
            problems.append(
                f"Stage {number}: no heading, but stages {numbers[0]}-{numbers[-1]} exist -- "
                "a gap means a renumber reached some headings and not others"
            )

    # task-heading-carries-title
    for stage in stages:
        for task_line in stage.task_lines:
            heading = stage.lines[task_line]
            if TASK_TITLED.match(heading):
                continue
            match = TASK_HEADING.match(heading)
            assert match is not None  # `task_lines` holds only matching lines.
            name = match.group(1)
            orphan = _orphaned_title(stage, task_line)
            detail = (
                f"its title appears to be the line below it ({orphan!r}); "
                "join that onto the heading"
                if orphan
                else f"give it one, as `## {name} -- <Title>`"
            )
            problems.append(
                f"{stage.label}: {name} carries no title on its heading line -- {detail}"
            )

    for stage in stages:
        for section in sections:
            if not _required_here(section, stage):
                continue
            labels = section["labels"]
            line = _section_line(stage, labels)

            # required-section-present
            if line is None:
                problems.append(
                    f"{stage.label}: no {section['id']!r} section "
                    f"(expected one of {labels}); it is {stage.lifecycle} and "
                    f"{section['id']!r} is required from {section.get('required_from', 'sketched')}"
                )
                continue

            # section-not-buried-between-tasks
            between = _buried_between_tasks(stage, line)
            if between is not None:
                problems.append(
                    f"{stage.label}: {section['id']!r} sits between {between[0]} and "
                    f"{between[1]}, so it reads as part of {between[0]}'s own entry rather "
                    "than as the stage's -- a reader looking for the stage's section will "
                    "not find it there"
                )

    return problems


def main() -> int:
    shape = load_shape()
    stages = parse_stages(ROADMAP_PATH.read_text(encoding="utf-8"))

    if not stages:
        print(f"No stages found in {ROADMAP_PATH.relative_to(REPO_ROOT)} -- has its heading ")
        print("format changed? A check that matches nothing reports nothing.")
        return 1

    problems = find_problems(stages, shape)
    problems += explain_gaps(shape, SPEC_PATH.read_text(encoding="utf-8"))
    for problem in problems:
        print(problem)

    if problems:
        print(f"\n{len(problems)} stage-shape problem(s) found.")
        print("The shape is declared in docs/planning/stage-shape.yaml; what each")
        print("section is for is docs/planning/stage-specification.md.")
        return 1

    counts: dict[str, int] = {}
    for stage in stages:
        counts[stage.lifecycle] = counts.get(stage.lifecycle, 0) + 1
    summary = ", ".join(f"{counts[state]} {state}" for state in LIFECYCLE_ORDER if state in counts)
    print(f"All {len(stages)} stage(s) have the shape stage-shape.yaml declares ({summary}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
