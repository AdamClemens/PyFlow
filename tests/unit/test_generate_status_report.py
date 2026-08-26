"""Unit tests for tools/generators/generate_status_report.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

TOOLS_GENERATORS = Path(__file__).resolve().parents[2] / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_status_report import (  # noqa: E402
    ROADMAP_PATH,
    STATUS_MD_PATH,
    LiveFacts,
    StageStatus,
    TaskStatus,
    _frontier_stage,
    _milestones_lines,
    _next_up_text,
    _overall_task_counts,
    _progress_bar,
    find_drift,
    gather_live_facts,
    parse_roadmap,
    render_status_html,
    render_status_md,
    word_or_digit_to_int,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# --- word_or_digit_to_int -------------------------------------------------


def test_word_numbers_are_recognised() -> None:
    assert word_or_digit_to_int("nine") == 9
    assert word_or_digit_to_int("Eight") == 8


def test_digit_strings_are_recognised() -> None:
    assert word_or_digit_to_int("10") == 10


def test_unrecognised_tokens_return_none() -> None:
    assert word_or_digit_to_int("dozen") is None


# --- parse_roadmap: stage status line -------------------------------------


def test_all_n_phrasing_sets_met_equal_to_total() -> None:
    """Stage 0's own phrasing ("all nine criteria met") states no separate
    met count -- the whole point is that everything listed was met.
    """
    text = """# Stage 0 — Infra

## Stage 0 Completion Criteria

- One.
- Two.

### Status as of 2026-08-19: Stage 0 complete, all two criteria met
"""
    stages = parse_roadmap(text)
    assert stages[0].criteria_claimed_total == 2
    assert stages[0].criteria_claimed_met == 2
    assert stages[0].complete_claimed is True
    assert stages[0].status_date == "2026-08-19"


def test_word_of_word_phrasing_can_differ() -> None:
    text = """# Stage 1 — Space

### Completion Criteria

1. **One.**
2. **Two.**
3. **Three.**

### Status as of 2026-08-21: Stage 1 in progress, two of three criteria met
"""
    stages = parse_roadmap(text)
    assert stages[0].criteria_claimed_total == 3
    assert stages[0].criteria_claimed_met == 2
    assert stages[0].complete_claimed is False


def test_a_stage_with_no_status_line_yet_has_no_claimed_total() -> None:
    """Stage 4 onward writes Completion Criteria before the stage opens
    (`docs/practices.md`) but has no status line until it closes."""
    text = """# Stage 4 — Numerics

### Completion Criteria

1. **One.**
"""
    stages = parse_roadmap(text)
    assert stages[0].criteria_claimed_total is None
    assert stages[0].criteria_actual_total == 1
    assert stages[0].complete_claimed is None


def test_bullet_style_criteria_are_counted_same_as_numbered() -> None:
    text = """# Stage 0 — Infra

## Stage 0 Completion Criteria

- One.
- Two.
- Three.

### Exit audit

1. **One.** Met.
2. **Two.** Met.
3. **Three.** Met.
"""
    stages = parse_roadmap(text)
    # The numbered "Exit audit" list is a *different* heading, not part of
    # the Completion Criteria block -- counting it too would double the
    # total. Boundary is "stop at the very next heading of any level".
    assert stages[0].criteria_actual_total == 3


# --- parse_roadmap: tasks --------------------------------------------------


def test_inline_status_marker_marks_a_task_done_with_its_date() -> None:
    text = """# Stage 1 — Space

## TASK-011 — Coordinate System

**Status: Done, 2026-08-20.** `src/pyflow/engine/coordinate_system.py`
implements it.
"""
    stages = parse_roadmap(text)
    task = stages[0].tasks[0]
    assert task.task_id == "TASK-011"
    assert task.title == "Coordinate System"
    assert task.done is True
    assert task.date == "2026-08-20"
    assert task.artifact == "src/pyflow/engine/coordinate_system.py"


def test_a_task_with_no_status_marker_and_no_table_row_is_not_started() -> None:
    text = """# Stage 4 — Numerics

## TASK-023

First-order Upwind Advection

**Intent:** boundedness.
"""
    stages = parse_roadmap(text)
    task = stages[0].tasks[0]
    assert task.done is False
    assert task.date is None
    assert task.title == "First-order Upwind Advection"


def test_stage_0_tasks_are_read_from_the_status_table_not_an_inline_marker() -> None:
    """TASK-000..010 carry no `**Status:**` line under their own heading --
    their only status is the `| Task | Status |` table (see the module
    docstring's `_stage0_table`)."""
    text = """# Stage 0 — Infra

| Task | Status |
|------|--------|
| TASK-000 Engine Skeleton | **Done** 2026-08-15 -- details |

## TASK-000 — Create Engine Skeleton

### Purpose

No inline status marker here at all.
"""
    stages = parse_roadmap(text)
    task = stages[0].tasks[0]
    assert task.done is True
    assert task.date == "2026-08-15"


def test_a_stage0_table_row_marked_in_progress_is_not_done() -> None:
    text = """# Stage 0 — Infra

| Task | Status |
|------|--------|
| TASK-001 Something | **In Progress** |

## TASK-001 — Something
"""
    stages = parse_roadmap(text)
    assert stages[0].tasks[0].done is False


# --- find_drift -------------------------------------------------------


def _stages_with_criteria(claimed_total: int, actual_total: int) -> list[StageStatus]:
    return [
        StageStatus(
            number=0,
            name="Infra",
            criteria_claimed_total=claimed_total,
            criteria_claimed_met=claimed_total,
            criteria_actual_total=actual_total,
            complete_claimed=True,
            status_date="2026-08-19",
        )
    ]


def test_matching_criteria_totals_produce_no_drift() -> None:
    stages = _stages_with_criteria(claimed_total=9, actual_total=9)
    live = LiveFacts(claude_md_count=45, test_count=473, scenario_count=19)
    assert find_drift(stages, live, "") == []


def test_a_mismatched_criteria_total_is_reported() -> None:
    stages = _stages_with_criteria(claimed_total=9, actual_total=8)
    live = LiveFacts(claude_md_count=45, test_count=473, scenario_count=19)
    findings = find_drift(stages, live, "")
    assert len(findings) == 1
    assert "9" in findings[0] and "8" in findings[0]


def test_claude_md_count_mismatch_is_reported() -> None:
    live = LiveFacts(claude_md_count=44, test_count=473, scenario_count=19)
    roadmap_text = "some text, 45 files exist as of 2026-08-23, more text"
    findings = find_drift([], live, roadmap_text)
    assert any("CLAUDE.md" in f for f in findings)


def test_claude_md_count_match_produces_no_finding() -> None:
    live = LiveFacts(claude_md_count=45, test_count=473, scenario_count=19)
    roadmap_text = "45 files exist as of 2026-08-23"
    assert find_drift([], live, roadmap_text) == []


def test_test_count_drift_uses_the_most_recently_dated_claim() -> None:
    """The roadmap accumulates historical test counts in the same
    paragraph; only the latest-dated one is "the present" (its own stated
    rule) and the one this check should hold to."""
    live = LiveFacts(claude_md_count=0, test_count=473, scenario_count=0)
    roadmap_text = "297 tests at 99% as of 2026-08-20. Later, 337 tests at 99% as of 2026-08-22."
    # Neither claim is 473, so this should report against 337 (the later
    # one), not 297.
    findings = find_drift([], live, roadmap_text)
    assert any("337" in f for f in findings)
    assert not any("297 tests" in f and "473" in f and "337" not in f for f in findings)


def test_scenario_claim_with_intervening_words_is_still_matched() -> None:
    """roadmap.md phrases this as "Fourteen of those 337 are Gherkin
    scenarios" -- "those N" sits between "of" and the count phrase."""
    live = LiveFacts(claude_md_count=0, test_count=0, scenario_count=19)
    roadmap_text = "Fourteen of those 337 are Gherkin scenarios rather than pytest functions"
    findings = find_drift([], live, roadmap_text)
    assert any("14" in f and "19" in f for f in findings)


def test_matching_scenario_claim_produces_no_finding() -> None:
    live = LiveFacts(claude_md_count=0, test_count=0, scenario_count=19)
    roadmap_text = "Nineteen of those 473 are Gherkin scenarios"
    assert find_drift([], live, roadmap_text) == []


# --- render_status_md -----------------------------------------------------


def test_rendered_output_says_it_is_generated() -> None:
    live = LiveFacts(claude_md_count=45, test_count=473, scenario_count=19)
    content = render_status_md(parse_roadmap("# Stage 0 — Infra\n"), live)
    assert "Do not edit by" in content
    assert "make check-status" in content


def test_rendered_output_carries_no_wall_clock_timestamp() -> None:
    """status.md is committed and `--check`-gated -- a wall-clock stamp
    would make it disagree with its own generator the instant time
    passed. `render_status_md` must be a pure function of its arguments,
    not of when it happens to run.
    """
    live = LiveFacts(claude_md_count=45, test_count=473, scenario_count=19)
    stages = parse_roadmap("# Stage 0 — Infra\n")
    assert render_status_md(stages, live) == render_status_md(stages, live)


def test_progress_section_states_the_overall_task_fraction() -> None:
    text = """# Stage 0 — Infra

## TASK-000 — Alpha

**Status: Done, 2026-08-15.**

## TASK-001 — Beta
"""
    live = LiveFacts(claude_md_count=0, test_count=0, scenario_count=0)
    content = render_status_md(parse_roadmap(text), live)
    assert "1/2 tasks complete (50%)" in content


# --- render_status_md / render_status_html: overall vs per-stage percentage


def _two_stages_one_empty() -> list[StageStatus]:
    """A completed stage with tasks, followed by a stage with none --
    the shape that exposed the `pct`/`done`/`total` shadowing bug: the
    per-stage loop ran *after* the overall percentage was computed, and
    a same-named local inside that loop silently overwrote it before the
    final f-string read it back."""
    return [
        StageStatus(
            number=0,
            name="Infra",
            criteria_claimed_total=None,
            criteria_claimed_met=None,
            criteria_actual_total=0,
            complete_claimed=True,
            status_date="2026-08-15",
            tasks=[
                TaskStatus(task_id="TASK-000", title="A", done=True, date=None, artifact=None),
                TaskStatus(task_id="TASK-001", title="B", done=True, date=None, artifact=None),
            ],
        ),
        StageStatus(
            number=1,
            name="Not yet planned",
            criteria_claimed_total=None,
            criteria_claimed_met=None,
            criteria_actual_total=0,
            complete_claimed=None,
            status_date=None,
            tasks=[],
        ),
    ]


def test_overall_percentage_survives_a_later_stage_with_no_tasks() -> None:
    """Regression test for the shadowing bug above: the last stage in
    iteration order has 0 tasks (a 0% stage), which must not leak into
    the overall summary computed before the per-stage loop runs."""
    stages = _two_stages_one_empty()
    live = LiveFacts(claude_md_count=0, test_count=0, scenario_count=0)

    md = render_status_md(stages, live)
    assert "2/2 tasks complete (100%)" in md

    html = render_status_html(stages, live, sha="abc123", generated_at="2026-08-26 00:00 UTC")
    assert "2/2 tasks complete (100%)" in html
    # The empty second stage's own (correctly 0%) bar must still render --
    # this isn't testing that stages stop affecting each other, only that
    # the *overall* figure computed before the loop is immune to it.
    assert "0/0 tasks done" in html


# --- small render_status_md helpers ----------------------------------------


def test_progress_bar_is_proportional() -> None:
    assert _progress_bar(0, 4, width=4) == "░░░░"
    assert _progress_bar(4, 4, width=4) == "████"
    assert _progress_bar(2, 4, width=4) == "██░░"


def test_progress_bar_with_no_tasks_is_a_dashed_placeholder() -> None:
    assert _progress_bar(0, 0, width=4) == "----"


def test_overall_task_counts_sums_across_stages() -> None:
    stages = _two_stages_one_empty()
    assert _overall_task_counts(stages) == (2, 2)


def test_frontier_is_the_first_stage_not_marked_complete() -> None:
    stages = _two_stages_one_empty()
    frontier = _frontier_stage(stages)
    assert frontier is not None
    assert frontier.number == 1


def test_frontier_is_none_when_every_stage_is_complete() -> None:
    stages = _two_stages_one_empty()
    stages[1] = replace(stages[1], complete_claimed=True)
    assert _frontier_stage(stages) is None


def test_milestones_lists_only_completed_stages_with_their_dates() -> None:
    stages = _two_stages_one_empty()
    lines = _milestones_lines(stages)
    assert lines == ["- **Stage 0 -- Infra** complete (2026-08-15)"]


def test_milestones_says_so_when_nothing_is_complete_yet() -> None:
    assert _milestones_lines([]) == ["No stage has been marked complete yet."]


def test_next_up_names_the_first_pending_task_and_a_remaining_count() -> None:
    stage = StageStatus(
        number=4,
        name="Numerics",
        criteria_claimed_total=None,
        criteria_claimed_met=None,
        criteria_actual_total=0,
        complete_claimed=False,
        status_date=None,
        tasks=[
            TaskStatus(task_id="TASK-023", title="Upwind", done=False, date=None, artifact=None),
            TaskStatus(task_id="TASK-024", title="Diffusion", done=False, date=None, artifact=None),
        ],
    )
    text = _next_up_text(stage)
    assert "TASK-023 (Upwind)" in text
    assert "1 more" in text


def test_next_up_notes_a_stage_not_yet_broken_into_tasks() -> None:
    stage = StageStatus(
        number=7,
        name="Better Numerics",
        criteria_claimed_total=None,
        criteria_claimed_met=None,
        criteria_actual_total=0,
        complete_claimed=None,
        status_date=None,
        tasks=[],
    )
    assert "not been broken into tasks yet" in _next_up_text(stage)


def test_next_up_when_every_stage_is_complete() -> None:
    assert _next_up_text(None) == "Every planned stage is marked complete."


# --- Real repository sanity checks ----------------------------------------


def test_the_real_roadmap_parses_without_drift() -> None:
    """The property that actually matters: parsing the real roadmap.md
    produces no disagreement with the live repository. A test reading the
    real roadmap fails whenever the roadmap legitimately changes, which is
    expected here -- unlike the synthetic-fixture tests above, this one is
    meant to break the moment roadmap.md's counts drift again, the same
    day `make check-status` would.
    """

    roadmap_text = (REPO_ROOT / ROADMAP_PATH).read_text(encoding="utf-8")
    stages = parse_roadmap(roadmap_text)
    live = gather_live_facts(REPO_ROOT)
    assert find_drift(stages, live, roadmap_text) == []


def test_stage_0_has_all_eleven_tasks() -> None:

    roadmap_text = (REPO_ROOT / ROADMAP_PATH).read_text(encoding="utf-8")
    stages = parse_roadmap(roadmap_text)
    stage0 = next(s for s in stages if s.number == 0)
    assert len(stage0.tasks) == 11
    assert all(task.done for task in stage0.tasks)


def test_the_committed_status_report_is_up_to_date() -> None:

    roadmap_text = (REPO_ROOT / ROADMAP_PATH).read_text(encoding="utf-8")
    stages = parse_roadmap(roadmap_text)
    live = gather_live_facts(REPO_ROOT)
    expected = render_status_md(stages, live)
    actual = STATUS_MD_PATH.read_text(encoding="utf-8")
    assert actual == expected
