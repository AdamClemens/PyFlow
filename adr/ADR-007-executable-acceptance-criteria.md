# ADR-007: Acceptance Criteria for Simulation Work Are Executable Gherkin Scenarios

**Status:** Accepted

---

# Context

This repository has an unusually good record of writing acceptance
criteria and an unusually bad record of them meaning anything.

Every significant defect found so far was green in CI when it landed:

| Defect | The criterion that should have caught it |
|---|---|
| Pan tracked the pointer 1.78x too slowly | "pan tracks the pointer under the cursor" |
| `face_neighbours(9999)` returned cells 3330 and 3333 | "geometrically correct, **not merely plausible**" |
| `extent: [10.9, 3.99]` silently became `(10, 3)` | "`PyFlowConfig` alone **determines** the mesh" |
| The contract suite proved strictly less than it claimed | "any future implementation (e.g. a staggered placement) must pass unchanged" |

The 2026-08-22 retro-audit named the drafting half of this ("The intent
lives in the qualifier", `docs/practices.md`): intent gets written as a
qualifying clause, and a strictly weaker bullet gets tested. But it left
the structural half untouched.

**The structural half is that a criterion and its test are two
artifacts.** The criterion lives in `docs/planning/roadmap.md` as prose.
The test lives in `tests/` and *claims* to implement it. Nothing checks
the claim, in either direction: a test can assert less than its
criterion says (TASK-015, TASK-016), and a criterion can have no test at
all (TASK-017's legend criterion, which cannot currently fail).

Every other place this repository found the same shape -- one fact
restated in two places -- it applied P-011 and made the restatement
impossible rather than merely discouraged: `docs/index.md` is generated
from the doc tree, `dependency-tree.md` from the component graph,
`repository-inventory.md` from `git ls-files`. Acceptance criteria were
the significant remaining hand-restated pair.

The maintainer's requirement, 2026-08-22: a passing suite should give as
close to full confidence as possible that the software works **as
intended**, and "ready to merge" must mean the intent is met, not that
the pipeline is green.

---

# Decision

**For simulation work, a Gherkin `.feature` file under
`tests/features/` is the acceptance criteria.** Not a restatement of
them, not a test that implements them -- the criteria themselves, in the
only form that executes.

1. **Scope: Stage 4 onward** (`docs/planning/roadmap.md` TASK-023
   onward), which is where physics begins and therefore where "real
   simulation work" begins. Plus the three existing golden demos, which
   were retrofitted when this decision was taken so that the mechanism
   was proven on work that already existed rather than first attempted
   on unbuilt physics.
2. **Stage 3 is exempt, deliberately.** It defines interfaces and
   computes nothing; its criteria are about architecture (can an
   implementation be swapped without editing a caller) and have no
   user-observable behaviour to describe. Writing Gherkin for them would
   produce ceremony, not clarity. Stage 3 keeps contract suites in plain
   pytest, which is what they are good at.
3. **The roadmap links, it does not restate.** A Stage 4+ task's
   Acceptance Criteria section names its feature file. Closed tasks keep
   their prose criteria as the historical record of what they were
   closed against, with a pointer added where a retrofit happened --
   rewriting a closed record to look tidier is the opposite of an
   institutional memory.
4. **`make check-scenarios` gates.** A `.feature` file nothing binds
   does not error, skip, or warn in pytest -- it silently never runs,
   while reading exactly like a criterion that passes. That failure mode
   would make this whole decision worthless, so it is a CI gate rather
   than a convention.
5. **Step vocabulary stays small and demo-independent**
   (`tests/golden/conftest.py`). Stage 4's scenarios inherit it; a
   vocabulary that has grown demo-specific is one they cannot reuse.

---

# Consequences

**Positive**

- A criterion cannot be weaker than its test, because there is no second
  artifact to be weaker than. The TASK-015 defect -- preamble claiming
  "every concrete `Field`", bullets asserting collocated storage -- is
  not expressible in this form: the scenario either runs against a
  staggered implementation or does not exist.
- A criterion with no test becomes visible rather than plausible.
  TASK-017's legend criterion reads as a passing check in prose; as a
  scenario, "prove it shares the field's colour function" has to be
  written as steps that could fail, and the fact that they cannot
  (a linear ramp is indistinguishable from an identical linear ramp)
  becomes obvious at drafting time.
- Physics criteria get a vocabulary suited to them. "Given a lid-driven
  cavity at Reynolds number 100 / When the solver runs to steady state /
  Then the centreline velocity profile matches Ghia et al. within 2%"
  is both the acceptance criterion and the test.
- A reader who is not reading Python can check what the software
  promises.

**Negative, and one is a real risk rather than a cost**

- **`pytest-bdd` 8.1.0 -- the latest release -- already warns under
  pytest 9**, calling `_register_fixture`/`FixtureDef` with
  `nodeid`/`baseid`, which pytest reports as `PytestRemovedIn10Warning`.
  Verified directly, not inferred: a probe scenario run under `-W error`
  fails rather than warns. It passes today only because warnings are not
  errors here. `pyproject.toml` therefore pins `pytest<10`, with the
  reason and the unpin trigger stated at the pin. **This is the one
  thing about this decision that could go wrong on its own timetable**,
  and if pytest 10 arrives before pytest-bdd fixes it, the options are
  to stay pinned, to vendor a minimal Gherkin runner (the subset used
  here is small), or to reverse this ADR -- in that order of preference.
- A new dependency, and with it `gherkin-official`, `Mako`, `parse`,
  `parse-type`, `six`.
- Step definitions are indirection. A reader now follows scenario ->
  step -> helper instead of reading one function. That is the trade for
  the criterion being readable by someone who does not read Python.
- Two test styles coexist: BDD for behaviour, plain pytest for contract
  suites and unit logic. Deliberate -- see the Stage 3 exemption -- but
  it does mean "where is this checked?" has two answers.

---

# Alternatives Considered

## Keep prose criteria, add a traceability check

Rejected. A validator asserting "every criterion cites a test" makes the
restatement *checkable* but leaves it a restatement -- and the failures
above were not missing tests, they were tests that asserted less than
their criterion. Traceability would have passed all four.

## Behaviour-shaped pytest with a Given/When/Then convention, no dependency

Rejected, and it was close. It carries none of the dependency risk
above, and the existing test names are already behaviour-shaped
(`test_field_display_zero_vector_at_the_centre_renders_no_arrow`). But
the criterion stays Python, so the prose-versus-test gap survives in the
docstring, which is exactly where TASK-015's did.

Worth revisiting if the pytest-bdd risk above actually materialises: this
is the fallback, and the scenario text would survive the move largely
intact.

## Vendor a minimal Gherkin runner

Rejected for now, on the root `CLAUDE.md`'s "avoid unnecessary
complexity" -- writing a parser and step registry when a maintained
library exists is not justified by a deprecation warning that has not
bitten yet. Named here as the second fallback rather than dismissed.

## Apply BDD to everything, including Stage 3 and the unit suite

Rejected. `tests/unit/test_field_contract.py` asserts that `Field`
cannot be instantiated and that a subclass missing `copy` cannot either.
There is no user, no behaviour, and no reader who benefits from that
being three Gherkin lines. Using a form where it does not fit is how a
form gets abandoned.
