"""Unit tests for tools/validators/check_dates.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.

One test per rule id in the script's own `RULES`, the same discipline
`test_check_graph.py` and `test_check_stages.py` hold.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_VALIDATORS = REPO_ROOT / "tools" / "validators"
if str(TOOLS_VALIDATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_VALIDATORS))

from check_dates import find_future_dates  # noqa: E402

TODAY = date(2026, 9, 4)
# Derived, never written as a literal: this module's own fixtures are
# indistinguishable from real records to the checker it tests, and a
# hardcoded "tomorrow" stops being tomorrow.
TOMORROW = TODAY + timedelta(days=1)
NEXT_MONTH = TODAY + timedelta(days=30)


def _write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --- no-future-dates ------------------------------------------------------


def test_a_date_after_today_is_reported(tmp_path: Path) -> None:
    """The drift this exists for: 23 files dated the day after the day
    `git log` puts the work on, written across two sessions and caught by
    nothing.
    """
    _write(tmp_path, "docs/thing.md", f"Added {TOMORROW}, at the audit.\n")
    problems = find_future_dates(tmp_path, ["docs/thing.md"], TODAY)
    assert len(problems) == 1
    assert str(TOMORROW) in problems[0]
    assert "docs/thing.md" in problems[0]


def test_today_itself_is_not_in_the_future(tmp_path: Path) -> None:
    """The boundary. A session records its own work with today's date,
    which is the overwhelmingly common case -- an off-by-one here would
    fail the build on every correct commit.
    """
    _write(tmp_path, "docs/thing.md", f"Added {TODAY}.\n")
    assert find_future_dates(tmp_path, ["docs/thing.md"], TODAY) == []


def test_a_past_date_is_not_reported(tmp_path: Path) -> None:
    _write(tmp_path, "docs/thing.md", "Decided 2026-08-21, superseding 2026-07-01.\n")
    assert find_future_dates(tmp_path, ["docs/thing.md"], TODAY) == []


def test_a_month_and_year_is_not_a_date_this_checks(tmp_path: Path) -> None:
    """The escape hatch, and the reason this can gate at all.

    A genuinely planned future point -- a target, a deadline -- is
    written as prose ("targeting December 2026"), which this never
    matches. Only the full ISO form is checked, and this repository uses
    that form exclusively to record things that have already happened.
    So "is this future date legitimate?" never has to be judged, which
    is what `tools/validators/CLAUDE.md` requires of anything gating.
    """
    _write(tmp_path, "docs/thing.md", "Targeting December 2026, or early 2027.\n")
    assert find_future_dates(tmp_path, ["docs/thing.md"], TODAY) == []


def test_an_impossible_date_is_not_reported_as_future(tmp_path: Path) -> None:
    """`2026-13-45` is wrong, but it is not *this* check's finding, and
    reporting it here would be a checker claiming to have found a thing
    it did not look for.
    """
    _write(tmp_path, "docs/thing.md", "Version 2026-13-45 of the format.\n")
    assert find_future_dates(tmp_path, ["docs/thing.md"], TODAY) == []


def test_every_occurrence_is_reported_not_only_the_first(tmp_path: Path) -> None:
    """The real drift spanned 23 files and several dates per file. A
    checker reporting one at a time turns one fix into twenty runs.
    """
    _write(tmp_path, "a.md", f"{TOMORROW} and {NEXT_MONTH}.\n")
    _write(tmp_path, "b.md", f"{TOMORROW}.\n")
    assert len(find_future_dates(tmp_path, ["a.md", "b.md"], TODAY)) == 3


def test_a_file_that_cannot_be_read_as_text_is_skipped(tmp_path: Path) -> None:
    """`git ls-files` lists PNGs and `.ico`s too. A validator that dies
    on the first binary file checks nothing at all.
    """
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe binary")
    assert find_future_dates(tmp_path, ["logo.png"], TODAY) == []


def test_a_missing_file_is_skipped(tmp_path: Path) -> None:
    """`git ls-files` can name a file deleted from the working tree."""
    assert find_future_dates(tmp_path, ["gone.md"], TODAY) == []


def test_the_real_repository_claims_no_future_date() -> None:
    """Reads the live tree, so a failure means a document is wrong, not
    that a rule is broken.
    """
    import check_dates

    assert check_dates.find_future_dates(REPO_ROOT, check_dates.tracked_files(REPO_ROOT)) == []
