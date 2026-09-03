"""Field visualisation (TASK-017): a scalar field as a colour map, a
vector field as arrows, and a legend sharing the exact colour function
the field itself is drawn with.

Deliberately field-specific -- like `mesh_visualization.py`, this module
only knows how to turn a `ScalarField`/`VectorField` into `pygfx`
geometry; it doesn't own a render loop or a camera.

`gfx.Mesh` face/vertex colours are interpreted as **linear**, not sRGB,
and re-encoded to sRGB for the framebuffer -- found empirically, not
assumed: a pure `(255, 0, 0)` round-tripped exactly, but an intermediate
`(100, 150, 200)` came back as `(168, 202, 229)`. `gfx.Line`/
`LineSegmentMaterial` (grid lines, TASK-013; arrows below) does not do
this -- `test_empty_mesh.py`'s own exact-match assertion on an
intermediate hex colour passes with no compensation anywhere. So any
colour meant to appear on screen exactly as specified must be
sRGB-decoded (`_srgb_decode`) before being handed to a `gfx.Mesh` as a
face colour -- done once, here, rather than by every caller.
"""

from __future__ import annotations

import math

import numpy as np
import pygfx as gfx

from pyflow.engine.mesh import Mesh
from pyflow.engine.scalar_field import ScalarField
from pyflow.engine.vector_field import VectorField


def _hex_to_rgba_uint8(hex_color: str) -> np.ndarray:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return np.array([r, g, b, 255], dtype=np.uint8)


def _srgb_decode(color_uint8: np.ndarray) -> np.ndarray:
    """`color_uint8` (..., 4), sRGB `[0, 255]` -> linear `float32 [0, 1]`
    -- what a `gfx.Mesh` face colour must be given for the pixel it
    produces to equal `color_uint8` exactly. See this module's docstring.
    """
    c = color_uint8.astype(np.float64) / 255.0
    linear = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    linear[..., 3] = c[..., 3]  # alpha is not gamma-encoded
    return linear.astype(np.float32)


def _map_values_to_colors(
    values: np.ndarray, low_color: str, high_color: str, value_range: tuple[float, float]
) -> np.ndarray:
    """The one colour ramp every caller below shares: `values` -> per-value
    RGBA `uint8`, linearly interpolated `low_color` -> `high_color` over
    `value_range`, clamped at the ends (not extrapolated). `scalar_field_colors`
    and `build_field_legend` both call this rather than each implementing
    their own gradient, so the legend is provably the same mapping the
    field itself is drawn with, not an independently-tuned copy.
    """
    v_min, v_max = value_range
    if v_max <= v_min:
        raise ValueError(f"value_range must have max > min, got {value_range}")
    t = np.clip((np.asarray(values, dtype=np.float64) - v_min) / (v_max - v_min), 0.0, 1.0)
    low = _hex_to_rgba_uint8(low_color).astype(np.float64)
    high = _hex_to_rgba_uint8(high_color).astype(np.float64)
    colors = low + (high - low) * t[:, np.newaxis]
    return np.round(colors).astype(np.uint8)


def scalar_field_colors(
    field: ScalarField, low_color: str, high_color: str, value_range: tuple[float, float]
) -> np.ndarray:
    """Every cell's colour, `(field.mesh.num_cells, 4)` `uint8` RGBA,
    linearly mapped from `field.values` over `value_range` via
    `_map_values_to_colors`.
    """
    return _map_values_to_colors(field.values.numpy(), low_color, high_color, value_range)


def _cell_corners(mesh: Mesh, cell: int) -> np.ndarray:
    """`cell`'s four corners, `(4, 2)`, ordered bottom-left/bottom-right/
    top-right/top-left -- derived generically from `face_vertices` over
    `cell_faces` (works for any `Mesh` whose cells are axis-aligned
    rectangles, the same generality `mesh_visualization.mesh_bounding_box`
    already relies on), not from `StructuredCartesianMesh`'s own `(i, j)`
    indexing.
    """
    points: set[tuple[float, float]] = set()
    for face in mesh.cell_faces(cell):
        for x, y in mesh.face_vertices(face):
            points.add((round(x, 9), round(y, 9)))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return np.array(
        [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]], dtype=np.float64
    )


def _quads_to_mesh(corners_per_quad: np.ndarray, colors: np.ndarray) -> gfx.Mesh:
    """Shared geometry assembly for `build_scalar_field_mesh` and
    `build_field_legend`: `corners_per_quad` is `(n, 4, 2)` (one quad's
    four corners per row, bottom-left/bottom-right/top-right/top-left),
    `colors` is `(n, 4)` `uint8` RGBA, one per quad. Two triangles per
    quad, each triangle's face colour set to that quad's (sRGB-decoded)
    colour -- see this module's docstring for why the decode is needed.
    """
    n = corners_per_quad.shape[0]
    positions = np.zeros((n * 4, 3), dtype=np.float32)
    positions[:, :2] = corners_per_quad.reshape(n * 4, 2)

    indices = np.zeros((n * 2, 3), dtype=np.int32)
    base = np.arange(n) * 4
    indices[0::2] = np.stack([base, base + 1, base + 2], axis=1)
    indices[1::2] = np.stack([base, base + 2, base + 3], axis=1)

    linear = _srgb_decode(colors)
    face_colors = np.repeat(linear, 2, axis=0)

    geometry = gfx.Geometry(positions=positions, indices=indices, colors=face_colors)
    material = gfx.MeshBasicMaterial(color_mode="face")
    return gfx.Mesh(geometry, material)


def build_scalar_field_mesh(field: ScalarField, colors: np.ndarray) -> gfx.Mesh:
    """One flat-coloured quad per cell of `field`'s own mesh,
    `colors[cell]` for cell `cell` -- the renderable counterpart to
    `scalar_field_colors`'s pure colour computation.

    Takes no separate mesh argument: a `Field` carries the mesh it
    belongs to (Stage 2 Completion Criterion 1), so the geometry is
    drawn over exactly the mesh whose values produced `colors`, rather
    than over a second mesh a caller has to remember to keep in step.

    Raises `ValueError` if `colors`'s shape doesn't match
    `(field.mesh.num_cells, 4)`.
    """
    mesh = field.mesh
    if colors.shape != (mesh.num_cells, 4):
        raise ValueError(f"colors must have shape ({mesh.num_cells}, 4), got {colors.shape}")
    corners = np.stack([_cell_corners(mesh, cell) for cell in range(mesh.num_cells)])
    return _quads_to_mesh(corners, colors)


_ARROWHEAD_ANGLE = math.radians(25)
"""Each arrowhead segment's angle off the reversed shaft direction --
one fixed constant, not configurable: real user feedback on the first
cut of vector rendering was that a bare line segment gives no visual way
to tell direction at all ("neither the direction nor magnitude is
clear"). 25 degrees is a generous, clearly-a-chevron angle, not tuned
precisely -- `tests/unit/test_field_visualization.py`'s own symmetry
test checks a band (10-45 degrees), not this exact value, so this can
change without breaking a test that doesn't actually care about the
precise angle.
"""

_ARROWHEAD_LENGTH_FRACTION = 0.3
"""Each arrowhead segment's length as a fraction of the shaft's own
length -- proportional, not a fixed world-space size, deliberately: a
fixed size would either overstate a tiny (near-zero-magnitude) vector's
apparent importance or dwarf a large one. Below
`_ARROWHEAD_MIN_LENGTH_FRACTION_OF_CELL`'s own floor, though, real user
feedback found this taken too far -- see that constant.
"""

_ARROWHEAD_MIN_LENGTH_FRACTION_OF_CELL = 0.3
"""A floor on each arrowhead segment's length, as a fraction of that
cell's own characteristic size (`sqrt(cell_volume)`) -- independent of
`_ARROWHEAD_LENGTH_FRACTION`'s proportional scaling, and applied in
addition to it (`max` of the two). Real user feedback on the
purely-proportional first cut: "where the magnitude is small the
arrowheads are also small. Too small to see easily." Shrinking the head
in lockstep with an already-tiny shaft doesn't communicate "very little
is happening here" the way the module docstring above used to argue --
it communicates nothing at all, since a head below a few pixels carries
no visible direction. The shaft length is what actually conveys relative
magnitude and is untouched by this floor, so a small vector still reads
as small; only its direction marker gets a legible minimum size, the
same way a compass needle's own head doesn't shrink to nothing just
because the reading is small.
"""


def build_vector_field_arrows(field: VectorField, color: str, scale: float) -> gfx.Line | None:
    """One shaft segment per cell of `field`'s own mesh whose vector is
    non-zero, from that cell's centroid to
    `centroid + scale * value_at(cell)`, plus two short arrowhead
    segments at the tip forming a chevron -- so direction reads visually
    from the line alone, not only from remembering which end is the
    tail. A cell with a zero vector contributes nothing at all -- not a
    zero-length shaft, not a headless dot -- so it renders no arrow.

    Each head's length is the larger of `_ARROWHEAD_LENGTH_FRACTION` of
    its own shaft and `_ARROWHEAD_MIN_LENGTH_FRACTION_OF_CELL` of that
    cell's characteristic size -- see the second constant's own
    docstring for why a purely-proportional head made small vectors
    unreadable.

    Every shaft segment is emitted first, in cell order (`positions[:2*n]`
    for `n` non-zero cells), with every arrowhead segment afterward --
    `LineSegmentMaterial` treats each consecutive point-pair as its own
    independent segment regardless of where in the array it sits, so
    this ordering is a convenience for callers/tests reading the shaft
    back out, not a rendering requirement.

    Takes no separate mesh argument, for the same reason
    `build_scalar_field_mesh` doesn't: an arrow's tail
    (`mesh.cell_centroid`) and its direction (`field.value_at`) must
    describe the same cell, and reading both from `field.mesh` is what
    makes that true by construction rather than by the caller getting it
    right.

    Returns `None` if every cell's vector is zero (nothing to draw);
    callers should skip adding it to a scene in that case.
    """
    mesh = field.mesh
    shaft_points: list[tuple[float, float]] = []
    head_points: list[tuple[float, float]] = []
    for cell in range(mesh.num_cells):
        vx, vy = field.value_at(cell)[:2]
        if vx == 0.0 and vy == 0.0:
            continue
        cx, cy = mesh.cell_centroid(cell)
        tip_x, tip_y = cx + scale * vx, cy + scale * vy
        shaft_points.append((cx, cy))
        shaft_points.append((tip_x, tip_y))

        shaft_length = math.hypot(tip_x - cx, tip_y - cy)
        dx, dy = (tip_x - cx) / shaft_length, (tip_y - cy) / shaft_length
        cell_size = math.sqrt(mesh.cell_volume(cell))
        head_length = max(
            shaft_length * _ARROWHEAD_LENGTH_FRACTION,
            cell_size * _ARROWHEAD_MIN_LENGTH_FRACTION_OF_CELL,
        )
        for sign in (1.0, -1.0):
            angle = sign * _ARROWHEAD_ANGLE
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            # Rotate the reversed shaft direction (-dx, -dy) by `angle`.
            rx = -dx * cos_a - -dy * sin_a
            ry = -dx * sin_a + -dy * cos_a
            head_points.append((tip_x, tip_y))
            head_points.append((tip_x + head_length * rx, tip_y + head_length * ry))

    if not shaft_points:
        return None

    all_points = shaft_points + head_points
    positions = np.zeros((len(all_points), 3), dtype=np.float32)
    positions[:, :2] = all_points
    geometry = gfx.Geometry(positions=positions)
    material = gfx.LineSegmentMaterial(thickness=2.0, color=color)
    return gfx.Line(geometry, material)


def build_field_legend(
    low_color: str,
    high_color: str,
    value_range: tuple[float, float],
    bounds: tuple[float, float, float, float],
    num_samples: int = 32,
) -> gfx.Mesh:
    """A horizontal gradient strip spanning `bounds` (`x0, y0, x1, y1`),
    `num_samples` flat-coloured quads sampled evenly across `value_range`
    through `_map_values_to_colors` -- the same colour function
    `scalar_field_colors` uses, not a second implementation of the
    gradient.

    Raises `ValueError` if `num_samples < 2` (a "gradient" of one colour
    isn't one).
    """
    if num_samples < 2:
        raise ValueError(f"num_samples must be at least 2, got {num_samples}")

    x0, y0, x1, y1 = bounds
    v_min, v_max = value_range
    sample_values = np.linspace(v_min, v_max, num_samples)
    colors = _map_values_to_colors(sample_values, low_color, high_color, value_range)

    edges = np.linspace(x0, x1, num_samples + 1)
    corners = np.zeros((num_samples, 4, 2), dtype=np.float64)
    corners[:, 0] = np.stack([edges[:-1], np.full(num_samples, y0)], axis=1)
    corners[:, 1] = np.stack([edges[1:], np.full(num_samples, y0)], axis=1)
    corners[:, 2] = np.stack([edges[1:], np.full(num_samples, y1)], axis=1)
    corners[:, 3] = np.stack([edges[:-1], np.full(num_samples, y1)], axis=1)

    return _quads_to_mesh(corners, colors)
