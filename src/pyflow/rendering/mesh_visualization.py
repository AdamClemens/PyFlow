"""Mesh grid-line visualisation and camera framing (TASK-013).

Builds a `pygfx` representation of a `Mesh`'s grid lines and frames a
camera on it. Deliberately mesh-specific -- unlike `window.py`'s camera
controls (zoom/pan), which are generic and reusable by anything rendered
in a `RenderWindow`, this module only knows how to turn a `Mesh` into
line geometry.
"""

from __future__ import annotations

import math

import numpy as np
import pygfx as gfx

from pyflow.engine.mesh import Mesh

# Fraction of the mesh's bounding-box width/height added as a margin on
# each side when framing a camera on it -- without this, a boundary grid
# line sits exactly on the viewport edge and gets partially clipped by
# antialiasing, found empirically while writing this module's own tests.
_VIEW_MARGIN_FRACTION = 0.1


def build_mesh_grid_line(mesh: Mesh, color: str) -> gfx.Line:
    """A single `gfx.Line` (`LineSegmentMaterial`) with one disconnected
    segment per face -- every internal cell boundary and every domain
    edge, matching TASK-013's "draw grid" / "display cell boundaries".

    One object for the whole mesh, not one per face: `LineSegmentMaterial`
    treats each consecutive pair of points as its own segment, so
    `mesh.num_faces` segments render in a single draw call.
    """
    positions = np.empty((mesh.num_faces * 2, 3), dtype=np.float32)
    for face in range(mesh.num_faces):
        (x0, y0), (x1, y1) = mesh.face_vertices(face)
        positions[2 * face] = (x0, y0, 0.0)
        positions[2 * face + 1] = (x1, y1, 0.0)

    geometry = gfx.Geometry(positions=positions)
    material = gfx.LineSegmentMaterial(thickness=2.0, color=color)
    return gfx.Line(geometry, material)


def mesh_bounding_box(mesh: Mesh) -> tuple[float, float, float, float]:
    """`(min_x, min_y, max_x, max_y)` over every face's vertices --
    works for any `Mesh`, not just a structured one, since it only uses
    `face_vertices`.
    """
    min_x = min_y = math.inf
    max_x = max_y = -math.inf
    for face in range(mesh.num_faces):
        for x, y in mesh.face_vertices(face):
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
    return (min_x, min_y, max_x, max_y)


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
