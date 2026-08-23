# CLAUDE

Gherkin feature files. **These are acceptance criteria, not tests of
them** -- `adr/ADR-007-executable-acceptance-criteria.md` is the
decision and its scope.

The distinction is the entire point, so it is worth stating plainly:
there is no prose criterion elsewhere that a scenario here implements.
The scenario is the criterion. If a scenario is weaker than what the
task meant, the task's criteria are weaker -- there is no second
artifact to be right while this one is wrong, which is precisely the gap
every defect this repository has found fell into.

## Writing one

- **Phrase a scenario as what a user or a physical result would
  observe**, not as what the code does. "A cell whose vector is exactly
  zero draws no arrow at all" is a criterion; "`build_vector_field_arrows`
  returns `None`" is an implementation detail wearing a criterion's
  clothes.
- **A scenario must be able to fail.** Before writing the steps, ask
  what a wrong implementation would look like and whether this scenario
  catches it. TASK-017's legend criterion is the worked counterexample:
  "proves it shares the field's colour function" cannot fail while the
  colour map is a two-stop linear ramp, because an identical linear ramp
  *is* the same function.
- **Put the qualifier in the scenario name.** "Cells with different
  values are visibly different, not merely unequal" says what a weaker
  check would miss; "cells render different colours" does not.
- Comments belong in the feature file where the reason is part of the
  criterion (why the scalar-only variant exists, why a midpoint is
  sampled rather than an endpoint). A reader deciding whether a
  criterion is strong enough needs that reasoning next to it.

## Where the steps live

`tests/golden/conftest.py` holds the demo-independent vocabulary --
run the demo, render a frame, compare two frames. Steps only one feature
could ever use live in that demo's own binding module. Keep that split:
Stage 4's physics scenarios inherit the shared vocabulary, and one that
has grown demo-specific is one they cannot reuse.

## The gate

`make check-scenarios` fails if a scenario exists that nothing binds.
That is not a style rule -- pytest does not error, skip, or warn for a
`.feature` file no module runs. It silently never runs, while reading
exactly like a criterion that passes, which would make every claim in
this directory worthless.
