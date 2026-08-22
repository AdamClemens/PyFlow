"""Empty Mesh golden demo (TASK-013).

The acceptance criteria are `tests/features/empty_mesh.feature`; this
module binds them and `conftest.py` supplies every step. See
`test_empty_window.py` for the pattern and
`adr/ADR-007-executable-acceptance-criteria.md` for why the feature file
is the criteria rather than a restatement of them.
"""

from __future__ import annotations

from pytest_bdd import scenarios

scenarios("empty_mesh.feature")
