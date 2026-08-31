"""Unit tests for `src/pyflow/rendering/hud.py` (Stage 7, Rendering
Annotations).

Pure geometry/content-construction checks, the same split
`test_field_visualization.py` already establishes for this package: no
actual GPU render here (`tests/golden/test_field_display.py`'s own
shape is where an annotated demo's rendered pixels get checked).

`gfx.Text` has no public way to read back the string it was built with --
confirmed directly against the installed `pygfx==0.17.0` (`uv.lock`)
before relying on it, not assumed: `text._text_blocks[i]._input` is a
private `(kind, string)` pair pygfx's own `TextBlock.set_text` stores
internally. `_text_content` below is the one place that reaches into it,
so a future pygfx upgrade that changes this shape only needs fixing
here.
"""

from __future__ import annotations

import pygfx as gfx

from pyflow.rendering.hud import build_legend_labels, build_stats_text, build_title_text


def _text_content(text_obj: gfx.Text) -> str:
    return "\n".join(block._input[1] for block in text_obj._text_blocks)


# -- build_title_text -------------------------------------------------------


def test_build_title_text_content() -> None:
    obj = build_title_text("Thermal Buoyancy", (1.0, 2.0))
    assert _text_content(obj) == "Thermal Buoyancy"


def test_build_title_text_position_and_anchor() -> None:
    obj = build_title_text("PyFlow", (3.5, -1.5))
    assert tuple(obj.local.position)[:2] == (3.5, -1.5)
    assert obj.anchor == "bottom-center"


def test_build_title_text_uses_configured_color() -> None:
    obj = build_title_text("PyFlow", (0.0, 0.0), color="#4477aa")
    assert tuple(round(c, 4) for c in obj.material.color)[:3] == (
        round(0x44 / 255, 4),
        round(0x77 / 255, 4),
        round(0xAA / 255, 4),
    )


def test_build_title_text_uses_configured_font_size() -> None:
    obj = build_title_text("PyFlow", (0.0, 0.0), font_size=2.5)
    assert obj.font_size == 2.5


# -- build_stats_text ---------------------------------------------------


def test_build_stats_text_joins_lines_with_newlines() -> None:
    obj = build_stats_text(["step 12", "t = 0.120", "dx = 0.100"], (0.0, 0.0))
    assert _text_content(obj) == "step 12\nt = 0.120\ndx = 0.100"


def test_build_stats_text_position_and_anchor() -> None:
    obj = build_stats_text(["a"], (2.0, 3.0))
    assert tuple(obj.local.position)[:2] == (2.0, 3.0)
    assert obj.anchor == "top-left"


def test_build_stats_text_single_line() -> None:
    obj = build_stats_text(["only one line"], (0.0, 0.0))
    assert _text_content(obj) == "only one line"


# -- build_legend_labels -----------------------------------------------------


def test_build_legend_labels_min_and_max_content_with_no_field_label() -> None:
    labels = build_legend_labels("0.0", "10.0", None, bounds=(0.0, 0.0, 4.0, 1.0))
    assert [_text_content(label) for label in labels] == ["0.0", "10.0"]


def test_build_legend_labels_includes_field_label_when_given() -> None:
    labels = build_legend_labels("0.0", "10.0", "Temperature (K)", bounds=(0.0, 0.0, 4.0, 1.0))
    assert [_text_content(label) for label in labels] == ["0.0", "10.0", "Temperature (K)"]


def test_build_legend_labels_min_label_sits_at_the_bounds_bottom_left() -> None:
    labels = build_legend_labels("0.0", "10.0", None, bounds=(1.0, 2.0, 5.0, 3.0))
    min_label = labels[0]
    assert tuple(min_label.local.position)[:2] == (1.0, 2.0)
    assert min_label.anchor == "top-left"


def test_build_legend_labels_max_label_sits_at_the_bounds_bottom_right() -> None:
    labels = build_legend_labels("0.0", "10.0", None, bounds=(1.0, 2.0, 5.0, 3.0))
    max_label = labels[1]
    assert tuple(max_label.local.position)[:2] == (5.0, 2.0)
    assert max_label.anchor == "top-right"


def test_build_legend_labels_field_label_sits_centered_above_the_bounds() -> None:
    labels = build_legend_labels("0.0", "10.0", "Speed", bounds=(1.0, 2.0, 5.0, 3.0))
    field_label = labels[2]
    assert tuple(field_label.local.position)[:2] == (3.0, 3.0)
    assert field_label.anchor == "bottom-center"
