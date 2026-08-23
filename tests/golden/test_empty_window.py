"""Empty Window golden demo (backlog D5).

The acceptance criteria are `tests/features/empty_window.feature`, not
this file -- see `adr/ADR-007-executable-acceptance-criteria.md`. This
module only binds them, and the steps live in `conftest.py`. If a
criterion needs changing, change the feature file; if a criterion cannot
be expressed in the shared vocabulary, add a step here rather than
weakening the scenario to fit.
"""

from __future__ import annotations

from pytest_bdd import scenarios

scenarios("empty_window.feature")
