"""Every gate in `make ci` must fail when it examines nothing.

**"A rule that matches nothing reports nothing" is this repository's own
phrase**, written into `check_dates.py`, `check_documents.py`,
`check_stages.py` and -- as a twelve-line comment explaining the failure
mode after it had already cost the project once -- `check_references.py`.
Four validators stated the principle. Four implemented it. They were not
the same four.

A gate that returns success while discovering zero files is
indistinguishable, in CI output, from a gate that discovered everything
and found no problems. That is worse than having no gate: the pipeline
reports a check that did not happen.

This sweep is the enforcement, because the alternative is remembering.
Each validator is imported, the function it discovers work through is
replaced with one returning nothing, and `main()` must return non-zero.
`test_every_validator_is_covered` keeps the map honest -- a new
`check_*.py` with no entry fails here rather than being silently
exempt, which is the mistake this whole file exists to stop being
possible (`tests/unit/test_boundary_field_reachability.py` has the same
shape, for the same reason).
"""

from __future__ import annotations

import importlib
import io
import sys
from collections.abc import Callable
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import pytest

_VALIDATOR_DIR = Path(__file__).resolve().parents[2] / "tools" / "validators"

if str(_VALIDATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_DIR))


# Validator module -> (the attribute it discovers work through, a
# replacement returning "nothing found"). Each discovery point is named
# explicitly because there is no way to infer it: a validator's own
# glob, `git ls-files` call, or document parse is the thing being
# emptied, and those have no common shape.
_DISCOVERY: dict[str, tuple[str, Callable[..., Any]]] = {
    "check_dates": ("tracked_files", lambda *a, **k: []),
    "check_docs": ("iter_markdown_files", lambda *a, **k: []),
    "check_documents": ("tracked_markdown", lambda *a, **k: []),
    "check_duplicate_blocks": ("_tracked_markdown_files", lambda *a, **k: []),
    "check_graph": ("_data_files", lambda *a, **k: []),
    "check_manifest": ("_tracked_files", lambda *a, **k: []),
    "check_references": ("tracked_paths", lambda *a, **k: (set(), set())),
    "check_scenarios": ("feature_files", lambda *a, **k: []),
    "check_stages": ("parse_stages", lambda *a, **k: []),
}

# `check_claims.py` is deliberately advisory and exits 0 even with
# findings (root `CLAUDE.md`), so "returns non-zero" is not a property it
# has. It is excluded by name, with that reason, rather than by being
# absent from the map -- an unexplained omission is how the gap above
# happened.
_ADVISORY = {"check_claims"}


def _run_with_nothing_found(module_name: str) -> tuple[int, str]:
    attribute, blank = _DISCOVERY[module_name]
    module = importlib.import_module(module_name)
    assert hasattr(module, attribute), (
        f"{module_name}.{attribute} no longer exists -- this sweep is patching a "
        "name that is gone, so it proves nothing about the real discovery path"
    )
    original = getattr(module, attribute)
    setattr(module, attribute, blank)
    try:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = int(module.main())
        return code, buffer.getvalue()
    finally:
        setattr(module, attribute, original)


@pytest.mark.parametrize("module_name", sorted(_DISCOVERY))
def test_a_validator_that_finds_nothing_fails(module_name: str) -> None:
    code, output = _run_with_nothing_found(module_name)

    assert code != 0, (
        f"{module_name} returned success while examining nothing at all. In CI that is "
        f"indistinguishable from a clean run. Its output was: {output.strip()!r}"
    )


@pytest.mark.parametrize("module_name", sorted(_DISCOVERY))
def test_a_validator_that_finds_nothing_says_so(module_name: str) -> None:
    """Failing is necessary but not sufficient -- a validator that fails
    with a message about some unrelated problem sends whoever reads CI
    looking in the wrong place. The message has to name the real cause.
    """
    _, output = _run_with_nothing_found(module_name)

    assert output.strip(), f"{module_name} failed silently when it found nothing"
    assert any(phrase in output.lower() for phrase in ("nothing", "no ", "not find", "empty")), (
        f"{module_name} failed, but its message does not say it found nothing: {output.strip()!r}"
    )


def test_every_validator_is_covered() -> None:
    """The guard on the sweep itself.

    Without this, adding `tools/validators/check_something_new.py` with
    no entry in `_DISCOVERY` leaves it unswept and every test above still
    green -- a sweep that covers less than it appears to, which is the
    exact shape of the defect being fixed.
    """
    on_disk = {path.stem for path in _VALIDATOR_DIR.glob("check_*.py")}

    assert on_disk, f"no validators found under {_VALIDATOR_DIR} -- has the layout changed?"

    unswept = on_disk - set(_DISCOVERY) - _ADVISORY
    assert not unswept, (
        f"{sorted(unswept)} are gates nothing here sweeps. Add each to _DISCOVERY with "
        "the function it discovers work through, or to _ADVISORY with the reason it "
        "cannot return non-zero."
    )

    stale = set(_DISCOVERY) - on_disk
    assert not stale, f"{sorted(stale)} are in _DISCOVERY but no longer exist on disk"
