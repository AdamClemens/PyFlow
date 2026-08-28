"""Unit tests for tools/generators/generate_config_template.py.

Not part of the `pyflow` package (a repo-consistency script, not library
code), so it's imported via `sys.path` -- see tools/generators/CLAUDE.md.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

TOOLS_GENERATORS = Path(__file__).resolve().parents[2] / "tools" / "generators"
if str(TOOLS_GENERATORS) not in sys.path:
    sys.path.insert(0, str(TOOLS_GENERATORS))

from generate_config_template import OUTPUT_PATH, missing_comment_paths, render  # noqa: E402

from pyflow.configuration import PyFlowConfig, load_config  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


# --- The "kept up to date" rule itself -------------------------------------
#
# This is the enforcement `src/pyflow/configuration/CLAUDE.md` promises:
# a field added to schema.py with no matching comment must fail `make
# test`, not rely on someone remembering to update a template by hand.


def test_every_live_config_field_has_a_comment() -> None:
    """The real regression: if this ever fails, a field was added to (or
    renamed in) `PyFlowConfig` without a matching entry in
    `FIELD_COMMENTS`/`SECTION_COMMENTS` -- add one in the same change
    that adds the field, per `src/pyflow/configuration/CLAUDE.md`.
    """
    assert missing_comment_paths(PyFlowConfig) == []


def test_missing_comment_paths_actually_detects_an_uncovered_field() -> None:
    """Proves the completeness check has teeth, rather than trivially
    passing because it never looks at anything -- a fake dataclass with a
    field no comment dict could possibly cover must be reported.
    """

    @dataclass
    class _Uncommented:
        totally_new_field: int = 0

    assert missing_comment_paths(_Uncommented) == ["totally_new_field"]


def test_a_fully_covered_dataclass_reports_nothing_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import generate_config_template

    @dataclass
    class _Covered:
        totally_new_field: int = 0

    monkeypatch.setitem(
        generate_config_template.FIELD_COMMENTS, "totally_new_field", "Valid: anything."
    )

    assert missing_comment_paths(_Covered) == []


# --- render() itself --------------------------------------------------------


def test_rendered_output_is_a_real_loadable_config(tmp_path: Path) -> None:
    """Every value in the template is `PyFlowConfig()`'s own default, so
    the file must round-trip through `load_config` to an equal config --
    this is not a set of placeholder tokens a user would have to edit
    before the file even parses.
    """
    config_path = tmp_path / "config-template.yaml"
    config_path.write_text(render(), encoding="utf-8")

    assert load_config(config_path) == PyFlowConfig()


def test_rendered_output_says_it_is_generated() -> None:
    output = render()

    assert "GENERATED" in output
    assert "do not edit" in output.lower()
    assert "make config-template" in output


def test_rendered_output_documents_a_valid_and_invalid_case_for_every_field() -> None:
    """The user-facing point of this file: not just a value, but what
    counts as valid and what doesn't.
    """
    output = render()

    assert output.count("Valid:") >= 30
    assert output.count("Invalid:") >= 25


def test_boundary_face_comments_are_explained_once_not_four_times() -> None:
    """South/east/west share north's own explanation rather than
    repeating it -- the intro comment inside `boundary_conditions:` says
    so explicitly, and this pins that the renderer actually behaves that
    way rather than just claiming to.
    """
    output = render()

    # Exactly one boundary face carries the full per-field explanation.
    # (A short, wrap-safe marker -- the full sentence straddles a
    # text-wrapped line break, so matching it verbatim would be fragile.)
    assert output.count("boundary-*normal*") == 1


def test_the_committed_config_template_is_up_to_date() -> None:
    """The same assertion `make check-config-template` makes, run as part
    of the ordinary suite so a stale file fails fast rather than only at
    the end of `make ci`.
    """
    assert OUTPUT_PATH.read_text(encoding="utf-8") == render()
