"""HUD text (Stage 7, Rendering Annotations): title, legend numeric
labels, and a timestep/time/cell-size/domain-size stats block.

Same split `mesh_visualization.py`/`field_visualization.py` already
establish (`rendering/CLAUDE.md`'s own instruction for this exact
situation): this module only turns plain values -- strings, positions,
bounds -- into `pygfx` `Text` objects. It owns no camera, no render
loop, and no unit/number formatting -- `bootstrap.py` is the one place
that already holds `config.mesh`, `config.numerics.timestep` and the
`units:` section together, so it is where a raw number becomes the
string this module renders, not here.

World-space, camera-following, not a fixed screen-space overlay --
`gfx.Text` does have a `screen_space=True` mode (confirmed live against
the installed `pygfx==0.17.0`), which would keep HUD text a constant
pixel size regardless of zoom; deliberately not used yet, since the
maintainer's own choice for this iteration was the lower-risk option
that reuses the legend strip's existing bounds-extension/camera-framing
pattern. Worth revisiting as a fast-follow now that `screen_space` is
verified to exist and work, not speculative.

`gfx.Text.set_text(...)`, confirmed live, mutates a `Text` object's
content in place and is reflected in the next render -- no
remove-from-scene-and-rebuild needed for the per-frame stats update,
unlike `bootstrap.py`'s own field-mesh rebuild-per-frame pattern (which
exists because *positions*, not just text, change every frame there).
"""

from __future__ import annotations

from collections.abc import Sequence

import pygfx as gfx

_Bounds = tuple[float, float, float, float]


def _build_text(
    content: str,
    position: tuple[float, float],
    anchor: str,
    font_size: float,
    color: str,
    max_width: float,
) -> gfx.Text:
    """Shared construction every function below uses -- one place that
    sets `local.position`/`material`, so every HUD text object is built
    the same way.

    `max_width` (world units; `0`, pygfx's own default, means unbounded)
    wraps text at word boundaries instead of letting it overflow past
    the mesh's own width -- confirmed live before relying on it: pygfx
    wraps cleanly, word by word, at any `max_width` tried. Found
    necessary, not anticipated: a long `field_display.vector_label` on a
    narrow demo canvas overflowed the frame entirely before this.
    """
    obj = gfx.Text(
        text=content,
        font_size=font_size,
        anchor=anchor,
        max_width=max_width,
        material=gfx.TextMaterial(color=color),
    )
    obj.local.position = (position[0], position[1], 0.0)
    return obj


def build_title_text(
    title: str,
    position: tuple[float, float],
    *,
    font_size: float = 1.0,
    color: str = "#ffffff",
    max_width: float = 0,
) -> gfx.Text:
    """`title` anchored `bottom-center` at `position` -- callers place
    `position` at the top-centre of whatever it should sit above (the
    mesh's own bounding box, typically), so the title grows upward from
    there rather than overlapping it.
    """
    return _build_text(title, position, "bottom-center", font_size, color, max_width)


def build_stats_text(
    lines: Sequence[str],
    position: tuple[float, float],
    *,
    font_size: float = 1.0,
    color: str = "#ffffff",
    max_width: float = 0,
) -> gfx.Text:
    """One `gfx.Text` block, `lines` joined with `\\n`, anchored
    `top-left` at `position` -- the timestep/elapsed-time/cell-size/
    domain-size readout. One object, not one per line, so a per-frame
    update (timestep/time) is a single `set_text` call.
    """
    return _build_text("\n".join(lines), position, "top-left", font_size, color, max_width)


def build_legend_labels(
    low_label: str,
    high_label: str,
    field_label: str | None,
    bounds: _Bounds,
    *,
    font_size: float = 1.0,
    color: str = "#ffffff",
    max_width: float = 0,
) -> list[gfx.Text]:
    """`low_label`/`high_label` placed at the legend strip's own bottom
    corners (`bounds`, the same `(x0, y0, x1, y1)` shape
    `build_field_legend` already takes) -- `low_label` bottom-left,
    anchored `top-left` so it hangs below the strip; `high_label`
    bottom-right, anchored `top-right`. `field_label`, if given, is
    centred above the strip's top edge, anchored `bottom-center`, and
    appended third. Two labels are returned when `field_label` is
    `None`, three otherwise -- always in this order (low, high, field),
    never field-first, so a caller destructuring the result doesn't have
    to branch on whether the list has two or three elements before the
    first two.
    """
    x0, y0, x1, y1 = bounds
    labels = [
        _build_text(low_label, (x0, y0), "top-left", font_size, color, max_width),
        _build_text(high_label, (x1, y0), "top-right", font_size, color, max_width),
    ]
    if field_label is not None:
        labels.append(
            _build_text(
                field_label, ((x0 + x1) / 2, y1), "bottom-center", font_size, color, max_width
            )
        )
    return labels
