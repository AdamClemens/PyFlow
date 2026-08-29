# CLAUDE

Committed reference data external to this repository -- published
results, not code. **New as of TASK-034 (Stage 5, 2026-08-29)**: this
repository had no test-data directory before this task needed one, per
`docs/planning/roadmap.md` Stage 5 Completion Criterion 5's own
instruction ("wherever it lands is a new convention... updated in the
same change, per the Blast Radius rule").

Distinct from `tests/unit/_numerics.py`/`tests/golden/_demo.py`: those
are machinery a step definition is *built from* (fixture constants, test
doubles, geometry helpers) and live next to the tests that use them,
each with its own module-level "local by default" scope. What lives here
instead is data with an external citation -- a published paper's own
tabulated numbers, not anything this project derived -- and is imported
by whichever test module needs it (`from fixtures.<module> import ...`,
reachable because `tests/` itself has no `__init__.py` and pytest's own
rootdir insertion puts it on `sys.path`), not copied into each one.

**`ghia_1982_re100.py`** is the first occupant: U. Ghia, K. N. Ghia and
C. T. Shin's own Table I (Re = 100), the Lid-Driven Cavity validation's
reference data (`tests/unit/test_navier_stokes_timestep.py`, `docs/
planning/roadmap.md` TASK-034). Every number carries the paper, table,
and column it came from, per Stage 5 Completion Criterion 5's own "the
reference values are committed data with their citation attached, not
literals typed into an assertion" -- see the module's own docstring for
exactly what was cross-checked against what, and the honest limit
recorded there: this environment has no direct access to the original
1982 print journal, so the tables were cross-checked against two
independent public reproductions of the paper's own Table I rather than
transcribed from it directly.

**A file here should be added only when a real committed reference
value needs a home, the same "real content first" discipline
`tools/CLAUDE.md` states for `generators/`/`validators/`** -- not
speculatively, and not for anything this project derives itself (that
stays local machinery, in `_numerics.py`/`_demo.py`).
