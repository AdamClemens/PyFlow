"""Makes `unit` a package rather than a bare directory.

Needed so pytest and mypy can tell `unit.test_bootstrap` apart from
`integration.test_bootstrap` -- without this, both tools identify test
modules by bare basename and collide the moment two subdirectories
happen to have a same-named test file (found 2026-08-16, adding
`tests/unit/test_bootstrap.py` alongside the existing
`tests/integration/test_bootstrap.py`).
"""
