"""Regression test: `"boussinesq_buoyancy"` must resolve without
`bootstrap()` ever having run (TASK-035, found by a direct question
about the consequences of where its registration call lived, not by a
test).

A first version registered it inside `bootstrap()`'s own function body,
reasoning that `engine/numerics/assembly.py` cannot import
`BoussinesqBuoyancy` (`engine/CLAUDE.md`'s "independent of any specific
physics") and `bootstrap.py` is the one place allowed to know about both
the registry and a concrete phenomenon. That reasoning about *where* the
call may live was right; putting it inside a function was not -- it made
the name resolvable only *after* `bootstrap()` had actually run once in
the process, unlike every one of `adr/ADR-003`'s six components, which
self-register the moment `assembly.py` is imported. Fixed by moving the
registration to `physics/buoyancy.py`'s own module scope, the same
self-registering pattern those six use.

Within a single process, Python caches every import in `sys.modules`, so
importing `pyflow.physics.buoyancy` (directly or via `pyflow.bootstrap`)
anywhere earlier in a test session would make this pass even if the
underlying bug were reintroduced -- each case here runs in a fresh
subprocess instead, the only way to genuinely prove "resolvable without
`bootstrap()` ever running", the same reasoning `test_import_order.py`
already uses for import-order claims.
"""

from __future__ import annotations

import subprocess
import sys

# `bare assemble_numerics`: nothing here imports `pyflow.bootstrap` or
# `pyflow.physics.buoyancy` -- if either import path stops triggering
# the self-registration, this raises `UnknownSchemeError` and the
# subprocess exits nonzero.
_ASSEMBLE_DIRECTLY = (
    "from pyflow.configuration.schema import NumericsConfig\n"
    "from pyflow.engine.numerics.assembly import assemble_numerics\n"
    "assemble_numerics(NumericsConfig(source_term='boussinesq_buoyancy'))\n"
)


def test_boussinesq_buoyancy_resolves_via_bootstrap_import_alone() -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import pyflow.bootstrap\n{_ASSEMBLE_DIRECTLY}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_boussinesq_buoyancy_resolves_via_direct_physics_import() -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import pyflow.physics.buoyancy\n{_ASSEMBLE_DIRECTLY}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_boussinesq_buoyancy_does_not_resolve_with_neither_imported() -> None:
    """The other half of the claim: this name is not, say, registered as
    a side effect of importing `pyflow.configuration` or `pyflow.engine`
    alone -- it genuinely depends on `physics.buoyancy` having been
    imported by *something*. Without this, the two tests above could
    both be passing for an unrelated reason (e.g. a stray import
    elsewhere in `assembly.py` itself).
    """
    result = subprocess.run(
        [sys.executable, "-c", _ASSEMBLE_DIRECTLY],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "UnknownSchemeError" in result.stderr
    assert "boussinesq_buoyancy" in result.stderr
