"""Reference data for the Lid-Driven Cavity validation (TASK-034, Stage
5 Completion Criterion 5): U. Ghia, K. N. Ghia and C. T. Shin, "High-Re
Solutions for Incompressible Flow Using the Navier-Stokes Equations and
a Multigrid Method", Journal of Computational Physics 48, 387-411
(1982), Table I, Reynolds number 100.

`docs/planning/roadmap.md` TASK-034's own Criterion 5 bullet requires
the reference values to be "committed data with their citation attached,
not literals typed into an assertion" and "read off the paper itself,
not from memory or a secondary source". **The honest limit on that
second half, stated here rather than left implicit**: this environment
has no direct access to the original 1982 print journal. The two tables
below were cross-checked against two independent public reproductions of
the paper's own Table I (not each other) before being committed --
<https://gist.github.com/ivan-pi/3e9326d18a366ffe6a8e5bfda6353219> (u
along the vertical centreline) and
<https://gist.github.com/ivan-pi/caa6c6737d36a9140fbcf2ea59c78b3c> (v
along the horizontal centreline), both explicitly labelled as
transcriptions of Ghia, Ghia & Shin (1982)'s own published table -- and
agree with each other to every digit. `PRIMARY_VORTEX_CENTER` is the
figure this paper's own results are most commonly cited by (cross-
checked the same way, via web search rather than a single source) and
matches this module's own docstring note below on what that figure
means. Nothing here is typed from memory alone.

**`PRIMARY_VORTEX_CENTER` is the widely-quoted approximate figure for
this paper's own Re = 100 result, used as a sanity check on this
fixture's own scale (`docs/planning/roadmap.md` TASK-034's own
Criterion 5 bullet says so explicitly), not a literal digit-for-digit
transcription of a table cell the way the two velocity profiles above
are** -- the original paper reports it via a streamfunction/vorticity
contour plot and an accompanying table of local extrema, not as a single
coordinate pair printed in text.

**Secondary corner vortices are checked for presence, not against
Ghia's own tabulated coordinates** -- `docs/planning/roadmap.md`
TASK-034's own Criterion 5 bullet asks only that "both downstream
secondary corner vortices [are] present" at the finest resolution, which
this fixture does not need a number for: the validating scenario detects
a genuine local recirculation near each bottom corner directly from
PyFlow's own computed velocity field.
"""

from __future__ import annotations

# u-velocity along the vertical centreline (x = 0.5 in unit-cavity
# coordinates), y from the moving lid (y=1) down to the stationary floor
# (y=0). 17 points, Table I.
U_VELOCITY_ALONG_VERTICAL_CENTERLINE: tuple[tuple[float, float], ...] = (
    (1.0000, 1.00000),
    (0.9766, 0.84123),
    (0.9688, 0.78871),
    (0.9609, 0.73722),
    (0.9531, 0.68717),
    (0.8516, 0.23151),
    (0.7344, 0.00332),
    (0.6172, -0.13641),
    (0.5000, -0.20581),
    (0.4531, -0.21090),
    (0.2813, -0.15662),
    (0.1719, -0.10150),
    (0.1016, -0.06434),
    (0.0703, -0.04775),
    (0.0625, -0.04192),
    (0.0547, -0.03717),
    (0.0000, 0.00000),
)

# v-velocity along the horizontal centreline (y = 0.5 in unit-cavity
# coordinates), x from the right wall (x=1) to the left wall (x=0). 17
# points, Table I.
V_VELOCITY_ALONG_HORIZONTAL_CENTERLINE: tuple[tuple[float, float], ...] = (
    (1.0000, 0.00000),
    (0.9688, -0.05906),
    (0.9609, -0.07391),
    (0.9531, -0.08864),
    (0.9453, -0.10313),
    (0.9063, -0.16914),
    (0.8594, -0.22445),
    (0.8047, -0.24533),
    (0.5000, 0.05454),
    (0.2344, 0.17527),
    (0.2266, 0.17507),
    (0.1563, 0.16077),
    (0.0938, 0.12317),
    (0.0781, 0.10890),
    (0.0703, 0.10091),
    (0.0625, 0.09233),
    (0.0000, 0.00000),
)

# (x, y) in unit-cavity coordinates -- see this module's own docstring
# for what this figure is and is not.
PRIMARY_VORTEX_CENTER: tuple[float, float] = (0.6172, 0.7344)
