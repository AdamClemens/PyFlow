"""Makes `fixtures` a package rather than a bare directory.

Needed so `mypy` can resolve `from fixtures.ghia_1982_re100 import ...`
(`tests/unit/test_navier_stokes_timestep.py`) without ambiguity --
without this, `mypy` finds `ghia_1982_re100.py` under two different
module names (`ghia_1982_re100` and `fixtures.ghia_1982_re100`) and
refuses to proceed, the same "no `__init__.py`" collision
`tests/unit/__init__.py`'s own docstring records for pytest/mypy module
identification generally.
"""
