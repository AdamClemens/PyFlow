"""Makes `numerics` a package rather than a bare directory -- same
reasoning as `tests/unit/__init__.py`: pytest and mypy identify test
modules by dotted path, and this subpackage sits one level below
`tests/unit/` for TASK-018's five operator interfaces
(`src/pyflow/engine/numerics/`).
"""
