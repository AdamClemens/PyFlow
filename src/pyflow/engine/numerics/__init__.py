"""The six `adr/ADR-003-modular-numerical-strategies.md` numerical
strategy interfaces, plus Gradient/Divergence/Source (the operators that
jointly compute `docs/architecture/engine.md`'s Flux layer) -- one
subpackage rather than living directly in `engine/` or `physics/`, per
`docs/planning/roadmap.md` TASK-018's design decisions: these six
interfaces share one purpose (configuration-selected numerical
machinery) and, from TASK-019 onward, one configuration section, which
is what a subpackage is for. `physics/` is deliberately not the home --
it is reserved for phenomena, not numerical schemes.

No concrete implementation lives here this stage (Stage 3 Completion
Criterion 1) -- every class below is an `ABC` with zero subclasses under
`src/`.
"""

from pyflow.engine.numerics.advection import AdvectionScheme, IncompatibleVelocityFieldError
from pyflow.engine.numerics.diffusion import DiffusionScheme
from pyflow.engine.numerics.divergence import DivergenceScheme
from pyflow.engine.numerics.gradient import GradientScheme
from pyflow.engine.numerics.source import SourceTerm

__all__ = [
    "AdvectionScheme",
    "DiffusionScheme",
    "DivergenceScheme",
    "GradientScheme",
    "IncompatibleVelocityFieldError",
    "SourceTerm",
]
