"""Unit tests for `pyflow.configuration.golden_demos` (TASK-043).

Isolated logic, no process boundary -- `resolve_golden_demo`/
`list_golden_demos`/`format_golden_demos_listing` are pure functions over
the module's own `_GOLDEN_DEMOS` registry and (for path resolution) a
`base_dir` a test can point anywhere. The one test that does touch the
real filesystem, `test_registry_matches_golden_demos_directory`, is the
staleness check described in `src/pyflow/configuration/CLAUDE.md`'s own
entry for this module: it resolves `examples/golden-demos/` relative to
this file, not the working directory, so it behaves the same regardless
of where `pytest` is invoked from.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pyflow.configuration.golden_demos import (
    _GOLDEN_DEMOS,
    UnknownGoldenDemoError,
    format_golden_demos_listing,
    list_golden_demos,
    resolve_golden_demo,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_DEMOS_DIR = _REPO_ROOT / "examples" / "golden-demos"


def test_registry_matches_golden_demos_directory() -> None:
    """Every real `*.yaml` under `examples/golden-demos/` is registered
    exactly once, and every registered filename actually exists -- the
    mechanical cross-check that keeps `_GOLDEN_DEMOS` (a second source of
    truth, chosen deliberately for stable numbers and curated names) from
    silently drifting from the directory it describes, the same
    `check-manifest`/`check-inventory` shape this repository already uses
    for every other generated/derived-data pair.
    """
    real_filenames = {path.name for path in _GOLDEN_DEMOS_DIR.glob("*.yaml")}
    registered_filenames = [filename for _, filename in _GOLDEN_DEMOS]

    assert len(registered_filenames) == len(set(registered_filenames)), (
        "a filename is registered more than once"
    )
    assert set(registered_filenames) == real_filenames

    registered_names = [name for name, _ in _GOLDEN_DEMOS]
    assert len(registered_names) == len(set(registered_names)), (
        "a name is registered more than once"
    )


def test_list_golden_demos_returns_names_in_registry_order() -> None:
    assert list_golden_demos() == tuple(name for name, _ in _GOLDEN_DEMOS)


def test_resolve_golden_demo_by_number_is_one_indexed(tmp_path: Path) -> None:
    first_name, first_filename = _GOLDEN_DEMOS[0]

    assert resolve_golden_demo("1", base_dir=tmp_path) == tmp_path / first_filename


def test_resolve_golden_demo_by_number_matches_its_position(tmp_path: Path) -> None:
    last_index = len(_GOLDEN_DEMOS)
    _, last_filename = _GOLDEN_DEMOS[-1]

    assert resolve_golden_demo(str(last_index), base_dir=tmp_path) == tmp_path / last_filename


def test_resolve_golden_demo_by_name(tmp_path: Path) -> None:
    name, filename = _GOLDEN_DEMOS[0]

    assert resolve_golden_demo(name, base_dir=tmp_path) == tmp_path / filename


def test_resolve_golden_demo_rejects_out_of_range_number(tmp_path: Path) -> None:
    with pytest.raises(UnknownGoldenDemoError) as exc_info:
        resolve_golden_demo(str(len(_GOLDEN_DEMOS) + 1), base_dir=tmp_path)

    assert str(len(_GOLDEN_DEMOS) + 1) in str(exc_info.value)
    for name in list_golden_demos():
        assert name in str(exc_info.value)


def test_resolve_golden_demo_rejects_zero_and_negative_numbers(tmp_path: Path) -> None:
    with pytest.raises(UnknownGoldenDemoError):
        resolve_golden_demo("0", base_dir=tmp_path)
    with pytest.raises(UnknownGoldenDemoError):
        resolve_golden_demo("-1", base_dir=tmp_path)


def test_resolve_golden_demo_rejects_unknown_name(tmp_path: Path) -> None:
    with pytest.raises(UnknownGoldenDemoError) as exc_info:
        resolve_golden_demo("not_a_real_demo", base_dir=tmp_path)

    assert "not_a_real_demo" in str(exc_info.value)


def test_format_golden_demos_listing_lists_every_demo_in_order() -> None:
    listing = format_golden_demos_listing()
    lines = listing.splitlines()

    assert len(lines) == len(_GOLDEN_DEMOS)
    for index, (name, _) in enumerate(_GOLDEN_DEMOS, start=1):
        assert lines[index - 1] == f"{index}  {name}"
