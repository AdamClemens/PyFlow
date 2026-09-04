"""Unit tests for tools/validators/check_stages.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.

**One test per rule id in `docs/planning/stage-shape.yaml`**, the same
discipline `test_check_graph.py` holds for the knowledge graph. Adding a
rule means touching the shape file, the specification document, and this
module.

Every test but the last builds a miniature roadmap in a string rather
than asserting against the real `docs/planning/roadmap.md`: a test
reading the real document fails whenever the roadmap legitimately
changes, for reasons unrelated to the rule it covers. The one test that
does read the real tree is deliberately separate and named so a failure
reads as "the roadmap is wrong", never as "a rule is broken".
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS_VALIDATORS = Path(__file__).resolve().parents[2] / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_stages import (  # noqa: E402
    ROADMAP_PATH,
    SPEC_PATH,
    _buried_between_tasks,
    _required_here,
    _section_line,
    explain_gaps,
    find_problems,
    load_shape,
    parse_stages,
)

SHAPE = load_shape()

# A stage with every section a `complete` stage owes, used as the base
# each test below removes exactly one thing from -- so a failure names
# the rule under test rather than whatever else happened to be missing.
COMPLETE_STAGE = """# Stage 3 — A Complete Stage

Goal

Do a thing.

Serves

Capability Level 1 (Simulation Engine).

Use cases

- Do the thing from a configuration file.

Golden Demo

The thing, demonstrated.

### Completion Criteria

1. The thing is done.

### Discharge map

| Criterion | Discharged by |
|-----------|---------------|
| 1 | TASK-001 |

### Status as of 2026-09-03: Stage 3 complete, one of one criteria met

Met.

---

## TASK-001 — Do The Thing

**Status: Done, 2026-09-03.**
"""


def problems_for(roadmap: str) -> list[str]:
    return find_problems(parse_stages(roadmap), SHAPE)


def test_a_stage_with_every_required_section_reports_nothing() -> None:
    """The control. Without this, every test below could pass because
    the checker reports nothing under any circumstances.
    """
    assert problems_for(COMPLETE_STAGE) == []


# --- stage-heading-well-formed --------------------------------------------


def test_a_stage_heading_with_no_name_is_reported() -> None:
    roadmap = COMPLETE_STAGE.replace("# Stage 3 — A Complete Stage", "# Stage 3 —")
    assert any("heading has no name" in p for p in problems_for(roadmap))


# --- stage-numbers-unique -------------------------------------------------


def test_two_stages_with_the_same_number_are_reported() -> None:
    """A duplicate makes every cross-reference to that number ambiguous,
    and this roadmap renumbers routinely -- three times so far.
    """
    roadmap = COMPLETE_STAGE + "\n" + COMPLETE_STAGE.replace("A Complete Stage", "A Clashing Stage")
    assert any("stage numbers must be unique" in p for p in problems_for(roadmap))


# --- stage-numbers-contiguous ---------------------------------------------


def test_a_gap_in_the_stage_numbers_is_reported() -> None:
    """A gap means a renumber reached some headings and not others --
    the failure mode `docs/practices.md`'s "Name a Stage when you cite
    its number" exists for.
    """
    roadmap = COMPLETE_STAGE + "\n" + COMPLETE_STAGE.replace("# Stage 3 —", "# Stage 5 —")
    assert any("Stage 4: no heading" in p for p in problems_for(roadmap))


# --- required-section-present ---------------------------------------------


@pytest.mark.parametrize(
    ("section_id", "heading"),
    [
        ("goal", "Goal"),
        ("serves", "Serves"),
        ("use-cases", "Use cases"),
        ("golden-demo", "Golden Demo"),
        ("completion-criteria", "### Completion Criteria"),
        ("discharge-map", "### Discharge map"),
        ("status", "### Status as of 2026-09-03: Stage 3 complete, one of one criteria met"),
    ],
)
def test_each_required_section_is_reported_when_missing(section_id: str, heading: str) -> None:
    """One case per section, each removing exactly that section from an
    otherwise complete stage.
    """
    roadmap = COMPLETE_STAGE.replace(f"{heading}\n", "", 1)
    problems = problems_for(roadmap)
    assert any(f"no {section_id!r} section" in p for p in problems), problems


def test_a_sketched_stage_owes_no_criteria() -> None:
    """The lifecycle's whole point: a stage nobody has designed is not
    missing a discharge map, it simply does not have one yet. Demanding
    filler from it would make this check worse than nothing.
    """
    sketched = """# Stage 9 — A Sketch

Goal

Do a later thing.

Tasks include

- Something

Golden Demo

To be decided.
"""
    assert problems_for(sketched) == []


def test_a_stage_with_one_task_and_no_criteria_is_reported() -> None:
    """**The rule this whole mechanism exists for.** Stage 7 reached its
    exit audit with no completion criteria and `make ci` stayed green.
    It fires at the first *task entry*, not the first Done task, because
    "before its first task" is what `docs/practices.md` asks for.
    """
    opened = """# Stage 9 — An Opened Stage

Goal

Do a thing.

Serves

Capability Level 4.

Use cases

- Do it.

Golden Demo

Demonstrated.

---

## TASK-100

**Status: In Progress.**
"""
    problems = problems_for(opened)
    assert any("no 'completion-criteria' section" in p for p in problems), problems


def test_intended_work_is_not_required_once_tasks_exist() -> None:
    """`required_until: sketched`. A "Tasks include" sketch surviving
    beside real task entries is a second, staler copy of the same fact.
    """
    assert not any("intended-work" in p for p in problems_for(COMPLETE_STAGE))


def test_stage_0_is_exempt_from_needing_a_golden_demo() -> None:
    """`since_stage: 1`, because `docs/planning/implementation-plan.md`
    exempts Capability Level 0 in as many words. Not a grandfather
    clause -- an exemption another document already states.
    """
    stage_0 = COMPLETE_STAGE.replace("# Stage 3 —", "# Stage 0 —").replace(
        "Golden Demo\n\nThe thing, demonstrated.\n\n", ""
    )
    assert not any("golden-demo" in p for p in problems_for(stage_0))


# --- section-not-buried-between-tasks -------------------------------------


def test_a_section_between_two_tasks_is_reported() -> None:
    """Stage 6's real defect: its demo list sat between TASK-038 and
    TASK-043, where two other documents had already misread it as
    TASK-038's. A heading was added to fix that and was not enough,
    because position is what a reader goes by.
    """
    buried = (
        COMPLETE_STAGE.replace("Golden Demo\n\nThe thing, demonstrated.\n\n", "")
        + """
Golden Demo

The thing, demonstrated.

## TASK-002 — Another Thing

**Status: Done, 2026-09-03.**
"""
    )
    problems = problems_for(buried)
    wanted = "sits between TASK-001 — Do The Thing and TASK-002 — Another Thing"
    assert any(wanted in p for p in problems), problems


def test_a_section_after_the_last_task_is_not_reported() -> None:
    """The narrowing that keeps this rule meaningful. Stages 0-6 put some
    sections after their last task, and moving seven closed stages'
    sections would be churn against historical records. Burial between
    two tasks is the defect; a trailing block is only a habit worth not
    continuing (`docs/planning/stage-specification.md`).
    """
    trailing = (
        COMPLETE_STAGE.replace("Golden Demo\n\nThe thing, demonstrated.\n\n", "")
        + "\nGolden Demo\n\nThe thing, demonstrated.\n"
    )
    assert not any("sits between" in p for p in problems_for(trailing))


def test_buried_helper_needs_two_tasks_to_report_anything() -> None:
    stage = parse_stages(COMPLETE_STAGE)[0]
    assert _buried_between_tasks(stage, len(stage.lines) - 1) is None


# --- every-section-is-explained -------------------------------------------


def test_a_section_the_specification_never_explains_is_reported() -> None:
    """Two artifacts describe one thing -- the shape file says which
    sections exist, the specification says what each is for -- and two
    artifacts describing one thing is the shape that drifts here.
    """
    shape = {"sections": [{"id": "a-section-nobody-wrote-about"}]}
    assert explain_gaps(shape, "some specification text") != []


def test_a_section_the_specification_does_explain_is_not_reported() -> None:
    shape = {"sections": [{"id": "use-cases"}]}
    assert explain_gaps(shape, "the use-cases section is for ...") == []


# --- the matcher ----------------------------------------------------------


def test_a_bare_label_must_match_exactly() -> None:
    """Prose opening with a section's name is not that section.

    Matching a bare line by prefix would make "Goal setting is out of
    scope here" count as the Goal, which is a checker reporting success
    for the wrong reason -- the failure mode this repository has met five
    times (`docs/practices.md`, "A rule that matches nothing reports
    nothing").
    """
    stage = parse_stages("# Stage 1 — X\n\nGoal setting is out of scope here.\n")[0]
    assert _section_line(stage, ["Goal"]) is None


def test_a_heading_may_carry_qualifiers_on_either_side() -> None:
    """`## Stage 0 Completion Criteria` and `### Status as of 2026-08-29:
    ...` are both live in the corpus, one qualified before the label and
    one after.
    """
    stage = parse_stages(
        "# Stage 0 — X\n\n## Stage 0 Completion Criteria\n\n### Status as of 2026-01-01: done\n"
    )[0]
    assert _section_line(stage, ["Completion Criteria"]) is not None
    assert _section_line(stage, ["Status as of"]) is not None


def test_required_here_honours_all_three_gates() -> None:
    stage = parse_stages(COMPLETE_STAGE)[0]
    assert stage.lifecycle == "complete"
    assert _required_here({"required_from": "opened"}, stage)
    assert not _required_here({"required_from": "sketched", "required_until": "sketched"}, stage)
    assert not _required_here({"required_from": "sketched", "since_stage": 99}, stage)


# --- the real roadmap -----------------------------------------------------


def test_the_real_roadmap_has_the_shape_it_declares() -> None:
    """The one test that reads the real tree. A failure here means the
    roadmap is wrong, not that a rule is broken -- every rule above is
    covered against a fixture.
    """
    stages = parse_stages(ROADMAP_PATH.read_text(encoding="utf-8"))
    assert stages, "no stages parsed -- has the roadmap's heading format changed?"
    problems = find_problems(stages, SHAPE)
    problems += explain_gaps(SHAPE, SPEC_PATH.read_text(encoding="utf-8"))
    assert problems == []


def test_every_declared_rule_id_is_covered_by_a_test_in_this_module() -> None:
    """The guard against this module and the shape file drifting apart.

    `tools/validators/CLAUDE.md`'s standing rule is that adding a rule
    means touching the declaration, the script and the tests. This is
    what makes "and the tests" mechanical rather than remembered: a rule
    id with no `# --- <id> ---` banner in this file fails here.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    declared = {rule["id"] for rule in SHAPE["rules"]}
    # `no-unknown-stage-in-status-report` is covered by
    # `tests/unit/test_generate_status_report.py`, which owns that
    # generator -- named here so its absence reads as a decision.
    external = {"no-unknown-stage-in-status-report"}
    uncovered = sorted(r for r in declared - external if f"--- {r} " not in source)
    assert not uncovered, f"rule id(s) with no test banner in this module: {uncovered}"


# --- task-heading-carries-title -------------------------------------------


def test_a_task_heading_with_no_title_is_reported() -> None:
    """A bare `## TASK-NNN` names the task by number alone.

    Nothing downstream can render or index it: the number is an
    identifier, not a name, and every view of the roadmap -- the
    knowledge graph's `features.yaml`, a generated index, a reader
    scanning the file -- is left with a label carrying no meaning.
    """
    roadmap = COMPLETE_STAGE.replace("## TASK-001 — Do The Thing", "## TASK-001")
    assert any("carries no title" in p for p in problems_for(roadmap))


def test_a_title_orphaned_below_its_heading_is_named_as_such() -> None:
    """The specific shape all 33 untitled entries had on 2026-09-05.

    The title was written, then separated from its heading by a blank
    line, so it reads as the entry's opening sentence instead. Worth its
    own message: "add a title" sends a reader to write one that already
    exists two lines down.
    """
    roadmap = COMPLETE_STAGE.replace("## TASK-001 — Do The Thing", "## TASK-001\n\nDo The Thing")
    problems = problems_for(roadmap)
    assert any("carries no title" in p and "Do The Thing" in p for p in problems)


def test_a_task_heading_keeps_its_title_when_the_dash_is_a_double_hyphen() -> None:
    """Both dash forms are live in this corpus, as `STAGE_HEADING`
    already allows for stage headings. A rule that accepted only the em
    dash would report a well-formed entry as broken.
    """
    roadmap = COMPLETE_STAGE.replace("## TASK-001 — Do The Thing", "## TASK-001 -- Do The Thing")
    assert not any("carries no title" in p for p in problems_for(roadmap))


def test_the_real_roadmap_gives_every_task_entry_a_title() -> None:
    """Reads the committed roadmap, so a failure means the roadmap is
    wrong, not that a rule is broken -- the same split the module
    docstring describes.
    """
    stages = parse_stages(ROADMAP_PATH.read_text(encoding="utf-8"))
    untitled = [p for p in find_problems(stages, SHAPE) if "carries no title" in p]
    assert untitled == []
