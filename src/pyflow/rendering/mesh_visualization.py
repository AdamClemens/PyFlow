"""Mesh grid-line visualisation and camera framing (TASK-013).

Builds a `pygfx` representation of a `Mesh`'s grid lines and frames a
camera on it. Deliberately mesh-specific -- unlike `window.py`'s camera
controls (zoom/pan), which are generic and reusable by anything rendered
in a `RenderWindow`, this module only knows how to turn a `Mesh` into
line geometry.
"""

from __future__ import annotations

import numpy as np
import pygfx as gfx

from pyflow.engine.mesh import Mesh

# Fraction of the mesh's bounding-box width/height added as a margin on
# each side when framing a camera on it -- without this, a boundary grid
# line sits exactly on the viewport edge and gets partially clipped by
# antialiasing, found empirically while writing this module's own tests.
_VIEW_MARGIN_FRACTION = 0.1


def face_vertex_positions(mesh: Mesh) -> np.ndarray:
    """Every face's two endpoints, as an `(num_faces * 2, 2)` array of
    `(x, y)` in face order -- the one traversal of the mesh that both
    functions below are built on.

    `float64`, not `float32`: this is also what `mesh_bounding_box`
    measures, and camera framing should not be quantised by the
    precision the *renderer* happens to want. The cast to `float32`
    happens once, in `build_mesh_grid_line`, where the GPU actually needs
    it.

    Accumulates into a flat Python list and converts once, rather than
    assigning into a preallocated array element by element -- each of
    those assignments is a separate NumPy scalar-conversion round trip.

    Measured 2026-08-21 on a 500x500 mesh (501,000 faces), best of three:
    `build_mesh_grid_line` 0.59 s -> 0.37 s. Stated plainly, because the
    same measurement says two less flattering things. `mesh_bounding_box`
    got about 11% *slower* (0.37 s -> 0.41 s): it previously tracked
    min/max in a pure-Python loop with no list to build, and now pays for
    the shared array. And the floor under all of this is 0.34 s of
    `Mesh.face_vertices` calls -- 90% of what is left, and untouchable
    from here, because one Python call per face is what the generic
    `Mesh` interface costs.

    Kept anyway, for the reason that outlives the numbers: one traversal
    function instead of two hand-rolled loops, so a bulk accessor on
    `Mesh` (or a structured-mesh override of one) would speed up both
    callers at once instead of one of them. Not building that accessor
    now -- no consumer needs it, this is startup cost rather than
    per-frame, and TASK-012's own note is explicit about not adding
    `Mesh` methods ahead of a real consumer. TASK-017 (Field Rendering)
    is the likely trigger: it traverses the same geometry per frame.
    """
    flat: list[float] = []
    for face in range(mesh.num_faces):
        (x0, y0), (x1, y1) = mesh.face_vertices(face)
        flat.extend((x0, y0, x1, y1))
    return np.asarray(flat, dtype=np.float64).reshape(-1, 2)


def build_mesh_grid_line(mesh: Mesh, color: str) -> gfx.Line:
    """A single `gfx.Line` (`LineSegmentMaterial`) with one disconnected
    segment per face -- every internal cell boundary and every domain
    edge, matching TASK-013's "draw grid" / "display cell boundaries".

    One object for the whole mesh, not one per face: `LineSegmentMaterial`
    treats each consecutive pair of points as its own segment, so
    `mesh.num_faces` segments render in a single draw call.
    """
    xy = face_vertex_positions(mesh)
    positions = np.zeros((len(xy), 3), dtype=np.float32)
    positions[:, :2] = xy

    geometry = gfx.Geometry(positions=positions)
    material = gfx.LineSegmentMaterial(thickness=2.0, color=color)
    return gfx.Line(geometry, material)


def mesh_bounding_box(mesh: Mesh) -> tuple[float, float, float, float]:
    """`(min_x, min_y, max_x, max_y)` over every face's vertices --
    works for any `Mesh`, not just a structured one, since it only uses
    `face_vertices`.
    """
    xy = face_vertex_positions(mesh)
    min_x, min_y = xy.min(axis=0)
    max_x, max_y = xy.max(axis=0)
    return (float(min_x), float(min_y), float(max_x), float(max_y))


def fit_camera_to_mesh(camera: gfx.OrthographicCamera, mesh: Mesh) -> None:
    """Frame `camera` on `mesh`'s bounding box, centred, with a margin
    so boundary grid lines aren't clipped at the viewport edge.

    Sets `camera.width`/`camera.height` -- the "zoom == 1" reference
    view -- and `camera.local.position`. Callers applying configured
    zoom/pan on top (`RenderWindow.apply_camera_config`) should do so
    *after* calling this, since `apply_camera_config` treats the
    camera's position as the pan origin to offset from.
    """
    min_x, min_y, max_x, max_y = mesh_bounding_box(mesh)
    width = max_x - min_x
    height = max_y - min_y

    camera.width = width * (1 + 2 * _VIEW_MARGIN_FRACTION)
    camera.height = height * (1 + 2 * _VIEW_MARGIN_FRACTION)
    camera.local.position = ((min_x + max_x) / 2, (min_y + max_y) / 2, 1.0)
