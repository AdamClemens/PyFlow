"""Stage 9 Completion Criterion 3: no `BoundaryFaceConfig` field is
validated and then ignored (`docs/planning/roadmap.md` TASK-055).

**A sweep over `dataclasses.fields(BoundaryFaceConfig)`, not a hand-kept
list**, so a field added later is covered without anybody remembering.
That distinction is not theoretical here: the audit that opened this
stage named `velocity` as the one validated-then-ignored field, and
`pressure` was dead in exactly the same way. A hand-kept list would have
held exactly the one field somebody happened to notice.

**"Reaches a scheme" is measured as "`assemble_numerics` actually reads
the attribute"**, recorded by substituting a proxy that logs its own
reads -- not by grepping the assembly module's source. A grep would pass
for a field named in a docstring and never read, which is close to the
failure being guarded against. `assemble_numerics` is the whole bridge
from configuration to scheme: a field it never reads cannot reach one.

**Its stated limit**: this proves consumption at the assembly seam, not
that the resolved condition is then used correctly downstream. That half
is `tests/features/boundary_velocity.feature`'s own behavioural
scenarios, which measure what the schemes do with the number.
"""

from __future__ import annotations

import dataclasses
from typing import Any, cast

from pyflow.configuration.schema import (
    BoundaryConditionsConfig,
    BoundaryFaceConfig,
    NumericsConfig,
)
from pyflow.engine.numerics.assembly import assemble_numerics

_BOUNDARY_NAMES = ("north", "south", "east", "west")

# Every boundary type a face may declare. The union of what assembly
# reads across all three is what "reachable at all" means -- a Dirichlet
# face never reads `scalar_gradient`, and a periodic face reads only
# `type`, so no single configuration exercises every field.
_BOUNDARY_TYPES = ("dirichlet", "neumann", "periodic")

_FIELD_NAMES = frozenset(field.name for field in dataclasses.fields(BoundaryFaceConfig))


class _ReadRecordingFace:
    """A `BoundaryFaceConfig` that records which of its own dataclass
    fields were read.

    Deliberately a proxy rather than a subclass: a dataclass subclass
    overriding `__getattribute__` also intercepts the machinery's own
    internal reads, which would record fields nobody asked for and make
    the sweep pass vacuously.
    """

    def __init__(self, face: BoundaryFaceConfig, seen: set[str]) -> None:
        object.__setattr__(self, "_face", face)
        object.__setattr__(self, "_seen", seen)

    def __getattr__(self, name: str) -> Any:
        face = object.__getattribute__(self, "_face")
        if name in _FIELD_NAMES:
            object.__getattribute__(self, "_seen").add(name)
        return getattr(face, name)


def _fields_read_by_assembly(boundary_type: str) -> set[str]:
    seen: set[str] = set()
    boundary_conditions = BoundaryConditionsConfig()
    for name in _BOUNDARY_NAMES:
        face = BoundaryFaceConfig(type=cast(Any, boundary_type))
        setattr(boundary_conditions, name, cast(Any, _ReadRecordingFace(face, seen)))

    assemble_numerics(NumericsConfig(boundary_conditions=boundary_conditions))
    return seen


def test_every_boundary_face_field_is_read_by_the_assembly_that_builds_the_schemes() -> None:
    reached: set[str] = set()
    for boundary_type in _BOUNDARY_TYPES:
        reached |= _fields_read_by_assembly(boundary_type)

    ignored = _FIELD_NAMES - reached
    assert not ignored, (
        f"{sorted(ignored)} are validated by BoundaryFaceConfig.validate() and then "
        "read by no scheme -- either wire each one through assemble_numerics or "
        "remove it from the schema (Stage 9 Completion Criterion 3)"
    )


def test_the_reachability_sweep_actually_reaches_something() -> None:
    """The guard `tests/unit/test_golden_demo_annotations.py` established:
    a sweep over an empty set passes silently, and would keep passing if
    the proxy stopped recording or the field list came back empty.
    """
    assert _FIELD_NAMES, "BoundaryFaceConfig declares no dataclass fields to sweep"

    reached = _fields_read_by_assembly("dirichlet")

    assert "type" in reached, "the recording proxy observed no reads at all"
    assert reached < _FIELD_NAMES or reached == _FIELD_NAMES
