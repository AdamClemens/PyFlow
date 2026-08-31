"""Generate a visual project status report from `docs/planning/roadmap.md`
and the repository's own live state.

The roadmap is authoritative for execution (root `CLAUDE.md`, ADR-006 rule
2) and stays prose -- there is deliberately no `status` field anywhere in
`planning/data/*.yaml` for exactly that reason. This script does not add
one. It reads the prose that already exists (`## TASK-NNN` headings,
`**Status: Done, DATE.**` markers, the Stage 0 status table, each stage's
`Completion Criteria` list and its `Status as of DATE: ... N of M criteria
met` line) and renders two views from it:

- `docs/planning/status.md` -- committed, Mermaid-charted, `--check`-gated
  like every other generated document (root `CLAUDE.md`: never hand-edit).
- an HTML dashboard under `build/` (gitignored, regenerated on demand,
  never committed and never `--check`-gated).

**It is also a validator, and that is the point.** A status report that
only renders whatever the roadmap currently claims would just be a nicer
font on the same staleness this repository has hit repeatedly -- the
337-tests paragraph that was already off by 136 real tests and 5 real
scenarios the day this script was first run (`docs/CHANGELOG-DESIGN.md`,
2026-08-26), the CLAUDE.md count restated in three places with one file
added and the count not touched (TASK-009's own row), Criterion 8's
overstated verdict (`cc53f7f`). So before rendering anything, it
cross-checks a small set of *structural* facts against the live
repository -- a stage's claimed criteria total against the actual count
of criteria it lists, a claimed test/CLAUDE.md/scenario count against
`git ls-files` and `pytest --collect-only` -- and refuses to render at
all while any of them disagree. `make status-report` and `make
check-status` both fail in that case, with the disagreement printed, not
just `make check-status`: unlike ordinary staleness (this file doesn't
match what the generator would currently produce, the same failure mode
every other `--check` here reports) a drift finding means the *source*
documents disagree with reality, and regenerating a status page from a
source that disagrees with reality would just launder the staleness into
a nicer format.

**Scoped deliberately narrow, the same way `check_references.py` and
`check_docs.py` are** (`tools/validators/CLAUDE.md`): every drift rule
here is a definite structural fact -- a count of list items, a count of
tracked files, a count of collected tests -- never a judgement call about
whether prose is still accurate. That is also why it does not attempt to
verify the "W of X criteria *met*" half of a stage's status line: which
criteria are met is exactly the kind of per-criterion reading
`check_claims.py` stays advisory over, and the verdict tables that would
back it are shaped differently stage to stage (a Markdown table for some,
plain numbered prose for others) with no structural invariant to check.
The claimed *met* count is rendered as stated; only the claimed *total*
is cross-checked, against the one thing that's unambiguous regardless of
verdict-table shape: how many criteria the stage actually lists.

Coverage percentage is deliberately not cross-checked either --
`pyproject.toml`'s `[tool.coverage.report]` has no fail-under threshold
yet ("there is one real test... Set one once there's enough real code for
a number to mean something"), so treating a coverage percentage as a
gated structural fact would be gating on a number the project has
explicitly decided isn't meaningful yet. The test *count* is a fact
regardless; the percentage is not.

Run via `make status-report` to write both views, or `make check-status`
(part of `make ci`) to fail if `docs/planning/status.md` is stale *or* if
a drift finding exists. Per root `CLAUDE.md`, the committed output must
never be hand-edited -- change `docs/planning/roadmap.md`, or fix
whatever's actually wrong in the repository, and regenerate.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROADMAP_PATH = Path("docs") / "planning" / "roadmap.md"
README_PATH = Path("README.md")
STATUS_MD_PATH = REPO_ROOT / "docs" / "planning" / "status.md"
STATUS_HTML_PATH = REPO_ROOT / "build" / "status.html"

_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def word_or_digit_to_int(token: str) -> int | None:
    """Parse "nine" or "9" to 9; None if `token` isn't a recognised number.

    The roadmap spells small counts out in prose ("all nine criteria
    met", "eight of eight") rather than using digits, and does so
    inconsistently enough (word-word, "all word") that both forms need
    handling -- see the module docstring's note on stage status lines.
    """
    cleaned = token.strip().lower()
    if cleaned.isdigit():
        return int(cleaned)
    return _WORD_NUMBERS.get(cleaned)


# --- Parsing docs/planning/roadmap.md ---------------------------------

STAGE_HEADING = re.compile(r"^# Stage (\d+) [—-] (.+?)\s*$", re.MULTILINE)
ANY_HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)
CRITERIA_HEADING = re.compile(r"^#{2,3}.*Completion Criteria\s*$", re.MULTILINE)
CRITERIA_ITEM = re.compile(r"^(?:\d+\.|-)\s+", re.MULTILINE)
STATUS_LINE = re.compile(
    r"^#{2,3}\s+Status as of (?P<date>\d{4}-\d{2}-\d{2}):\s*Stage\s+\d+\s+"
    r"(?P<state>complete|in progress|incomplete)"
    r"(?:,\s*(?:all\s+(?P<all>\w+)|(?P<met>\w+)\s+of\s+(?P<total>\w+)))?",
    re.MULTILINE,
)
TASK_HEADING = re.compile(r"^## (TASK-\d+)(?:\s*[—-]\s*(.+?))?\s*$", re.MULTILINE)
INLINE_STATUS = re.compile(r"\*\*Status:\s*(Done|In Progress|Blocked)[,.]?\s*(\d{4}-\d{2}-\d{2})?")
BACKTICK_PATH = re.compile(r"`([\w./{}-]+\.[a-zA-Z]{1,10})`")
STAGE0_TABLE_ROW = re.compile(
    r"^\|\s*(TASK-\d+)\s+([^|]*?)\s*\|\s*\*\*(Done|In Progress|Blocked)\*\*"
    r"\s*(\d{4}-\d{2}-\d{2})?",
    re.MULTILINE,
)


@dataclass(frozen=True)
class TaskStatus:
    task_id: str
    title: str
    done: bool
    date: str | None
    artifact: str | None


@dataclass(frozen=True)
class StageStatus:
    number: int
    name: str
    criteria_claimed_total: int | None
    criteria_claimed_met: int | None
    criteria_actual_total: int
    complete_claimed: bool | None
    status_date: str | None
    tasks: list[TaskStatus] = field(default_factory=list)


def _next_heading_start(text: str, after: int) -> int:
    match = ANY_HEADING.search(text, pos=after)
    return match.start() if match else len(text)


def _criteria_actual_total(stage_text: str) -> int:
    heading = CRITERIA_HEADING.search(stage_text)
    if heading is None:
        return 0
    block_end = _next_heading_start(stage_text, heading.end())
    block = stage_text[heading.end() : block_end]
    return len(CRITERIA_ITEM.findall(block))


def _parse_status_line(stage_text: str) -> tuple[str | None, bool | None, int | None, int | None]:
    match = STATUS_LINE.search(stage_text)
    if match is None:
        return None, None, None, None
    complete = match.group("state") == "complete"
    if match.group("all"):
        total = word_or_digit_to_int(match.group("all"))
        return match.group("date"), complete, total, total
    if match.group("total"):
        total = word_or_digit_to_int(match.group("total"))
        met = word_or_digit_to_int(match.group("met"))
        return match.group("date"), complete, total, met
    return match.group("date"), complete, None, None


def _stage0_table(stage_text: str) -> dict[str, tuple[str, bool, str | None]]:
    """`{task_id: (title, done, date)}` from Stage 0's `| Task | Status |` table.

    Stage 0's eleven tasks (TASK-000..010) carry no inline `**Status:**`
    marker under their own heading -- their only recorded status is this
    table, written once as a status summary rather than repeated per task.
    """
    rows: dict[str, tuple[str, bool, str | None]] = {}
    for task_id, title, state, date in STAGE0_TABLE_ROW.findall(stage_text):
        rows[task_id] = (title.strip(), state == "Done", date or None)
    return rows


def _parse_tasks(
    stage_text: str, stage0_rows: dict[str, tuple[str, bool, str | None]]
) -> list[TaskStatus]:
    tasks: list[TaskStatus] = []
    headings = list(TASK_HEADING.finditer(stage_text))
    for index, heading_match in enumerate(headings):
        task_id = heading_match.group(1)
        heading_title = (heading_match.group(2) or "").strip()
        block_end = headings[index + 1].start() if index + 1 < len(headings) else len(stage_text)
        block = stage_text[heading_match.end() : block_end]

        inline = INLINE_STATUS.search(block)
        if inline is not None:
            done = inline.group(1) == "Done"
            date = inline.group(2)
            artifact_match = BACKTICK_PATH.search(block, pos=inline.end())
            artifact = artifact_match.group(1) if artifact_match else None
            title = heading_title
        elif task_id in stage0_rows:
            row_title, done, date = stage0_rows[task_id]
            artifact = None
            title = heading_title or row_title
        else:
            done, date, artifact = False, None, None
            plain_title_match = re.search(r"^([A-Z][^\n*`#]{2,80})$", block.strip(), re.MULTILINE)
            title = heading_title or (
                plain_title_match.group(1).strip() if plain_title_match else ""
            )

        tasks.append(
            TaskStatus(task_id=task_id, title=title, done=done, date=date, artifact=artifact)
        )
    return tasks


def parse_roadmap(text: str) -> list[StageStatus]:
    stage_matches = list(STAGE_HEADING.finditer(text))
    stages: list[StageStatus] = []
    for index, stage_match in enumerate(stage_matches):
        number = int(stage_match.group(1))
        name = stage_match.group(2).strip()
        block_end = (
            stage_matches[index + 1].start() if index + 1 < len(stage_matches) else len(text)
        )
        stage_text = text[stage_match.end() : block_end]

        stage0_rows = _stage0_table(stage_text) if number == 0 else {}
        date, complete, claimed_total, claimed_met = _parse_status_line(stage_text)

        stages.append(
            StageStatus(
                number=number,
                name=name,
                criteria_claimed_total=claimed_total,
                criteria_claimed_met=claimed_met,
                criteria_actual_total=_criteria_actual_total(stage_text),
                complete_claimed=complete,
                status_date=date,
                tasks=_parse_tasks(stage_text, stage0_rows),
            )
        )
    return stages


# --- Live repository facts ---------------------------------------------


def live_claude_md_count(root: Path = REPO_ROOT) -> int:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    return sum(1 for path in result.stdout.split() if Path(path).name == "CLAUDE.md")


def live_test_count(root: Path = REPO_ROOT) -> int:
    """Collected test count via `pytest --collect-only`, not a full run.

    Deliberately the fast collection count, not `make test`'s pass/fail
    run -- this only needs a structural fact (how many tests exist), and
    `make check-status` runs as part of `make ci`, after `test` has
    already run once; re-running the whole suite here would just be
    seconds spent proving the same thing twice.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    if match is None:
        raise RuntimeError(
            "could not determine the live test count from `pytest --collect-only` output:\n"
            + result.stdout[-2000:]
        )
    return int(match.group(1))


def live_scenario_count(root: Path = REPO_ROOT) -> int:
    features_dir = root / "tests" / "features"
    total = 0
    for feature_file in sorted(features_dir.glob("*.feature")):
        text = feature_file.read_text(encoding="utf-8")
        total += len(re.findall(r"^\s*Scenario(?: Outline)?:", text, re.MULTILINE))
    return total


@dataclass(frozen=True)
class LiveFacts:
    claude_md_count: int
    test_count: int
    scenario_count: int


def gather_live_facts(root: Path = REPO_ROOT) -> LiveFacts:
    return LiveFacts(
        claude_md_count=live_claude_md_count(root),
        test_count=live_test_count(root),
        scenario_count=live_scenario_count(root),
    )


# --- Drift detection -----------------------------------------------------

# Every literal space in these three patterns is `\s+`, not " ".
# `docs/planning/roadmap.md` is hard-wrapped prose, so any of these
# phrases can acquire a line break in the middle at any edit -- and a
# pattern that stops matching does not report drift, it reports *nothing
# to check*, which reads identically to a clean pass. That is exactly
# what happened to `SCENARIO_CLAIM`: it matched when this script was
# first written, a later edit wrapped the line between "653" and "are",
# and the rule was silently inert until the Stage 5 exit audit
# (2026-08-29) found the roadmap claiming 79 scenarios against a live 94.
CLAUDE_MD_CLAIM = re.compile(r"(\d+)\s+files\s+exist\s+as\s+of\s+\d{4}-\d{2}-\d{2}")
TEST_COUNT_CLAIM = re.compile(r"(\d+)\s+tests\s+at\s+\d+%\s+as\s+of\s+(\d{4}-\d{2}-\d{2})")
SCENARIO_CLAIM = re.compile(r"(\w+)\s+of\s+(?:those\s+)?\d+\s+are\s+Gherkin\s+scenarios")


README_CURRENT_PHASE = re.compile(
    r"^##\s+Current Phase\s*$(?P<body>.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL
)
README_PHASE_STAGE = re.compile(r"\bStage\s+(\d+)\b")


def _readme_phase_findings(readme_text: str, stages: list[StageStatus]) -> list[str]:
    """`README.md`'s "Current Phase" section against the roadmap's own
    first stage not marked complete.

    **Why this is checked at all**: that section has gone a full stage
    stale twice -- the Stage 2 exit audit found it saying the project "is
    beginning Stage 2", and the Stage 5 exit audit (2026-08-29) found it
    saying Stage 5 was "not yet started" on the day Stage 5 closed. Both
    passed `make ci`. Reads the *first* `Stage N` in the section, which is
    the phase sentence's own subject; the per-stage recap below it names
    every earlier stage too, and is deliberately not what this matches
    against.

    This adds no second source of truth: which stage is current still
    comes from `docs/planning/roadmap.md`'s own status headings, via
    `_frontier_stage`. README is checked *against* it, never consulted for
    it.
    """
    section = README_CURRENT_PHASE.search(readme_text)
    if section is None:
        return [
            "README.md has no `## Current Phase` section, so nothing states which stage "
            "the project is on where a reader arrives first."
        ]
    current = _frontier_stage(stages)
    if current is None:
        return []
    named = README_PHASE_STAGE.search(section.group("body"))
    if named is None:
        return [
            "README.md's Current Phase section names no stage at all; the roadmap's own "
            f"first stage not marked complete is Stage {current.number} ({current.name})."
        ]
    if int(named.group(1)) != current.number:
        return [
            f"README.md's Current Phase section names Stage {named.group(1)}, but the "
            f"roadmap's own first stage not marked complete is Stage {current.number} "
            f"({current.name})."
        ]
    return []


def find_drift(
    stages: list[StageStatus],
    live: LiveFacts,
    roadmap_text: str,
    readme_text: str | None = None,
) -> list[str]:
    """Every disagreement between `docs/planning/roadmap.md` and the live
    repository, as human-readable strings. Empty means clean.

    `readme_text` is optional and `None` means "not checked" -- the shape
    every unit test in `tests/unit/test_generate_status_report.py` that
    predates it relies on. `main()` always passes the real file.
    """
    findings: list[str] = []
    if readme_text is not None:
        findings.extend(_readme_phase_findings(readme_text, stages))

    for stage in stages:
        if stage.criteria_claimed_total is None:
            continue
        if stage.criteria_claimed_total != stage.criteria_actual_total:
            findings.append(
                f"Stage {stage.number} ({stage.name}): status line claims "
                f"{stage.criteria_claimed_total} completion criteria, but "
                f"{stage.criteria_actual_total} are actually listed under its "
                "Completion Criteria section."
            )

    claude_match = CLAUDE_MD_CLAIM.search(roadmap_text)
    if claude_match is not None:
        claimed = int(claude_match.group(1))
        if claimed != live.claude_md_count:
            findings.append(
                f"roadmap.md claims {claimed} CLAUDE.md files, but "
                f"{live.claude_md_count} exist in the repository (`git ls-files`)."
            )

    test_matches = list(TEST_COUNT_CLAIM.finditer(roadmap_text))
    if test_matches:
        latest = max(test_matches, key=lambda m: m.group(2))
        claimed = int(latest.group(1))
        if claimed != live.test_count:
            findings.append(
                f"roadmap.md's most recent test count claims {claimed} tests "
                f"(as of {latest.group(2)}), but {live.test_count} are collected "
                "by `pytest --collect-only` today."
            )

    scenario_match = SCENARIO_CLAIM.search(roadmap_text)
    if scenario_match is not None:
        claimed_scenarios = word_or_digit_to_int(scenario_match.group(1))
        if claimed_scenarios is not None and claimed_scenarios != live.scenario_count:
            findings.append(
                f"roadmap.md claims {claimed_scenarios} Gherkin scenarios, but "
                f"{live.scenario_count} exist across tests/features/*.feature."
            )

    return findings


# --- Rendering: docs/planning/status.md ---------------------------------


def _task_counts(tasks: list[TaskStatus]) -> tuple[int, int]:
    return sum(1 for t in tasks if t.done), len(tasks)


def _overall_task_counts(stages: list[StageStatus]) -> tuple[int, int]:
    done = sum(1 for s in stages for t in s.tasks if t.done)
    total = sum(len(s.tasks) for s in stages)
    return done, total


def _progress_bar(done: int, total: int, width: int = 10) -> str:
    """A `total`-agnostic 0-100% bar, in block characters.

    Deliberately not "criteria met" (the chart this replaced): a stage's
    completion-criteria count is arbitrary prose, decoupled from its task
    count on purpose (Stage 1's own Completion Criteria section says so
    directly), so comparing criteria counts *across* stages compared
    nothing meaningful. A percentage of real implementation tasks is.
    """
    if total == 0:
        return "-" * width
    filled = round(width * done / total)
    return "█" * filled + "░" * (width - filled)


def _completed_stages(stages: list[StageStatus]) -> list[StageStatus]:
    return [stage for stage in stages if stage.complete_claimed]


def _frontier_stage(stages: list[StageStatus]) -> StageStatus | None:
    """The first stage not marked complete, in roadmap order.

    `None` (all complete) is representable but not expected any time
    soon -- Stage 14 is the last one currently in the roadmap.
    """
    for stage in stages:
        if not stage.complete_claimed:
            return stage
    return None


def _mermaid_task_pie(done: int, total: int) -> str:
    return "\n".join(
        [
            "```mermaid",
            "pie showData",
            '    title "Tasks across the roadmap"',
            f'    "Done" : {done}',
            f'    "Not started" : {total - done}',
            "```",
        ]
    )


def _milestones_lines(stages: list[StageStatus]) -> list[str]:
    completed = _completed_stages(stages)
    if not completed:
        return ["No stage has been marked complete yet."]
    return [
        f"- **Stage {stage.number} -- {stage.name}** complete"
        + (f" ({stage.status_date})" if stage.status_date else "")
        for stage in completed
    ]


def _next_up_text(stage: StageStatus | None) -> str:
    if stage is None:
        return "Every planned stage is marked complete."
    pending = [task for task in stage.tasks if not task.done]
    if not stage.tasks:
        return (
            f"**Stage {stage.number} -- {stage.name}** is next, and has not "
            "been broken into tasks yet."
        )
    if not pending:
        return (
            f"**Stage {stage.number} -- {stage.name}** has no pending tasks "
            "recorded, but isn't marked complete -- likely awaiting its exit audit."
        )
    first = pending[0]
    first_label = first.task_id + (f" ({first.title})" if first.title else "")
    remaining = len(pending) - 1
    tail = f", {remaining} more not yet started in this stage" if remaining else ""
    return f"**Stage {stage.number} -- {stage.name}** is next, starting with {first_label}{tail}."


def render_status_md(stages: list[StageStatus], live: LiveFacts) -> str:
    done_total, task_total = _overall_task_counts(stages)
    pct = round(100 * done_total / task_total) if task_total else 0
    frontier = _frontier_stage(stages)

    lines = [
        "# Project Status",
        "",
        "**Generated by `tools/generators/generate_status_report.py` from",
        "`docs/planning/roadmap.md` and the live repository. Do not edit by",
        "hand** -- per root `CLAUDE.md`, generated documentation is never",
        "edited manually, and `make check-status` fails if this file is stale",
        "or if the sources it reads disagree with reality. To change what",
        "appears here, change `docs/planning/roadmap.md`, or fix whatever the",
        "drift check names.",
        "",
        "For the richer interactive view (per-task tables, live counts, an",
        "actual generation timestamp), run `make status-report` and open the",
        "dashboard it writes under `build/` -- gitignored, regenerated on",
        "demand, not part of this file.",
        "",
        "## Progress",
        "",
        f"**{done_total}/{task_total} tasks complete ({pct}%)** across "
        f"{len(stages)} planned stages. For the full plan, including",
        "stages below not yet broken into tasks: [roadmap.md](roadmap.md).",
        "",
        _mermaid_task_pie(done_total, task_total),
        "",
        "### Milestones",
        "",
        *_milestones_lines(stages),
        "",
        "### Up next",
        "",
        _next_up_text(frontier),
        "",
        "## Live repository facts",
        "",
        f"- **{live.claude_md_count}** `CLAUDE.md` files",
        f"- **{live.test_count}** tests collected",
        f"- **{live.scenario_count}** Gherkin scenarios (`tests/features/*.feature`)",
        "",
        "## Stages",
        "",
    ]

    for stage in stages:
        state = (
            "complete"
            if stage.complete_claimed
            else "in progress"
            if stage.complete_claimed is False
            else "no status recorded"
        )
        criteria = (
            f"{stage.criteria_claimed_met}/{stage.criteria_claimed_total} criteria met"
            if stage.criteria_claimed_total is not None
            else f"{stage.criteria_actual_total} criteria defined, no status line yet"
        )
        done, total = _task_counts(stage.tasks)
        tasks_summary = (
            f"`{_progress_bar(done, total)}` {done}/{total} tasks"
            if total
            else "not yet broken into tasks"
        )

        lines.append(f"### Stage {stage.number} -- {stage.name}")
        lines.append("")
        as_of = f", as of {stage.status_date}" if stage.status_date else ""
        lines.append(f"**{state}{as_of}** -- {tasks_summary}; {criteria}")
        lines.append("")
        if stage.tasks:
            lines.append("| Task | Status | Date | Artifact |")
            lines.append("|------|--------|------|----------|")
            for task in stage.tasks:
                status_text = "Done" if task.done else "Not started"
                title = f" -- {task.title}" if task.title else ""
                artifact = f"`{task.artifact}`" if task.artifact else ""
                lines.append(
                    f"| {task.task_id}{title} | {status_text} | {task.date or ''} | {artifact} |"
                )
            lines.append("")

    lines += [
        "## About this snapshot",
        "",
        "This file is current as of when it was last regenerated and",
        "committed -- run `git log -1 docs/planning/status.md` for exactly",
        "when. No generation timestamp is embedded in this file itself: it's",
        "committed and `--check`-gated, so a wall-clock stamp would make it",
        "go stale the instant time passed, for no real reason. For the",
        "state right now, run `make status-report` and open the dashboard",
        "under `build/` -- it stamps its own generation time, because",
        "nothing checks it.",
        "",
    ]

    return "\n".join(lines)


# --- Rendering: build/status.html (uncommitted dashboard) ---------------


def render_status_html(
    stages: list[StageStatus], live: LiveFacts, sha: str, generated_at: str
) -> str:
    done_total, task_total = _overall_task_counts(stages)
    pct = round(100 * done_total / task_total) if task_total else 0
    frontier = _frontier_stage(stages)
    next_up = (
        f"Stage {frontier.number} -- {frontier.name}" if frontier is not None else "nothing left"
    )

    stage_rows = []
    for stage in stages:
        stage_done, stage_total = _task_counts(stage.tasks)
        stage_pct = round(100 * stage_done / stage_total) if stage_total else 0
        state_class = "complete" if stage.complete_claimed else "in-progress"
        stage_rows.append(
            f'<section class="stage {state_class}">'
            f"<h2>Stage {stage.number} -- {stage.name}</h2>"
            f'<div class="bar"><div class="fill" style="width:{stage_pct}%"></div></div>'
            f"<p>{stage_done}/{stage_total} tasks done"
            + (
                f", {stage.criteria_claimed_met}/{stage.criteria_claimed_total} criteria met"
                if stage.criteria_claimed_total is not None
                else ""
            )
            + "</p>"
            "<table><thead><tr><th>Task</th><th>Title</th><th>Status</th>"
            "<th>Date</th><th>Artifact</th></tr></thead><tbody>"
            + "".join(
                f"<tr class='{'done' if t.done else 'pending'}'>"
                f"<td>{t.task_id}</td><td>{t.title}</td>"
                f"<td>{'Done' if t.done else 'Not started'}</td>"
                f"<td>{t.date or ''}</td><td><code>{t.artifact or ''}</code></td></tr>"
                for t in stage.tasks
            )
            + "</tbody></table></section>"
        )

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>PyFlow Project Status</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto;
    padding: 0 1rem; }}
  h1 {{ font-size: 1.5rem; }}
  .meta {{ color: #888; font-size: 0.85rem; margin-bottom: 2rem; }}
  .facts {{ display: flex; gap: 1.5rem; margin-bottom: 2rem; }}
  .fact {{ border: 1px solid #8883; border-radius: 8px; padding: 0.75rem 1rem; }}
  .fact .n {{ font-size: 1.4rem; font-weight: 600; display: block; }}
  .progress {{ border: 1px solid #8883; border-radius: 8px; padding: 1rem;
    margin-bottom: 1.5rem; }}
  .progress .bar {{ height: 14px; }}
  section.stage {{ border: 1px solid #8883; border-radius: 8px; padding: 1rem;
    margin-bottom: 1rem; }}
  .bar {{ background: #8882; border-radius: 4px; height: 8px; overflow: hidden;
    margin: 0.5rem 0; }}
  .bar .fill {{ background: #4a9; height: 100%; }}
  .complete .bar .fill {{ background: #4a9; }}
  .in-progress .bar .fill {{ background: #d90; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 0.5rem; }}
  th, td {{ text-align: left; padding: 0.25rem 0.5rem; border-bottom: 1px solid #8882; }}
  tr.pending {{ opacity: 0.6; }}
  code {{ font-size: 0.8em; }}
</style>
</head>
<body>
<h1>PyFlow Project Status</h1>
<div class="meta">Generated from docs/planning/roadmap.md and the live repository at
  {generated_at}, commit {sha} -- not committed, regenerate with `make status-report`</div>
<div class="progress">
  <strong>{done_total}/{task_total} tasks complete ({pct}%)</strong> across {len(stages)}
  planned stages -- next up: {next_up}
  <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
</div>
<div class="facts">
  <div class="fact"><span class="n">{live.claude_md_count}</span>CLAUDE.md files</div>
  <div class="fact"><span class="n">{live.test_count}</span>tests collected</div>
  <div class="fact"><span class="n">{live.scenario_count}</span>Gherkin scenarios</div>
</div>
{"".join(stage_rows)}
</body>
</html>
"""


def _current_sha(root: Path = REPO_ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"


def main() -> int:
    check_only = "--check" in sys.argv[1:]

    roadmap_text = (REPO_ROOT / ROADMAP_PATH).read_text(encoding="utf-8")
    readme_text = (REPO_ROOT / README_PATH).read_text(encoding="utf-8")
    stages = parse_roadmap(roadmap_text)
    live = gather_live_facts()

    drift = find_drift(stages, live, roadmap_text, readme_text=readme_text)
    if drift:
        print(
            "Status report refused: roadmap.md or README.md disagrees with the live repository.\n"
        )
        for finding in drift:
            print(f"- {finding}")
        print(
            "\nFix docs/planning/roadmap.md (or whatever's actually wrong) and "
            "re-run -- a status page generated from a source that disagrees "
            "with reality would just be reformatted staleness."
        )
        return 1

    md_content = render_status_md(stages, live)

    if check_only:
        current = STATUS_MD_PATH.read_text(encoding="utf-8") if STATUS_MD_PATH.exists() else None
        if current == md_content:
            print("docs/planning/status.md is up to date.")
            return 0
        print(
            "docs/planning/status.md is stale -- roadmap.md or the live "
            "repository changed without regenerating it.\n"
            "Run 'make status-report' and commit the result."
        )
        return 1

    with STATUS_MD_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(md_content)
    print(f"Wrote {STATUS_MD_PATH.relative_to(REPO_ROOT)}")

    STATUS_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    html_content = render_status_html(stages, live, _current_sha(), generated_at)
    with STATUS_HTML_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(html_content)
    print(f"Wrote {STATUS_HTML_PATH.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
