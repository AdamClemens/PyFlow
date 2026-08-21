# CLAUDE

`post_edit_format.py` -- a `PostToolUse` hook (wired in `../settings.json`)
that runs `ruff check --fix` and `ruff format` on the single file an
Edit/Write tool call just touched, scoped to `.py` files only. Narrower
than `make lint`: no `--all-files` sweep, no whitespace/YAML/large-file/
codespell/mypy checks -- those still run at commit time via the
`pre-commit` git hook (`make install`, `.pre-commit-config.yaml`). This
hook exists purely to keep a file readable between edits within a
session, not as a substitute for `make lint`/`make ci`.

Reads the tool payload from stdin as JSON; a payload that fails to parse,
or names a non-`.py`/nonexistent file, is a silent no-op (`return 0`),
deliberately -- a formatting convenience should never fail the tool call
it's attached to.

If this script is ever extended, keep it fast: it runs synchronously
after every matching Edit/Write, so anything slower than a per-file ruff
pass adds latency to every edit in the session, not just this one.

**Scripts here run outside the project's interpreter, and fail
silently.** Both halves of that matter, and together they cost this hook
four days of being completely dead (2026-08-17 to 2026-08-21, found by a
repository audit). It was written with PEP 758's unparenthesised
`except A, B:` -- valid Python 3.14, which is what `requires-python`
says the project needs -- while `../settings.json` invoked it with a
bare `python`, meaning whatever is on `PATH`. On a machine where that
resolved to 3.10 it was a `SyntaxError` on every single edit, and
because Claude Code reports nothing when a hook exits non-zero, the only
symptom was files quietly not being formatted.

Three standing rules follow, and all three are now enforced rather than
just written down:

1. **Invoke hooks through `uv run`** (`../settings.json`), so the
   project's pinned interpreter is the one that runs them, not whatever
   `PATH` offers.
2. **Write to the older-interpreter floor anyway**, belt and braces --
   `tests/integration/test_claude_hooks.py` compiles every script here
   at a fixed `feature_version` and fails if it uses newer syntax. Rule 1
   alone would not have been caught by any test that happened to run
   where `python` was already 3.14.

   `ruff.toml` in this directory is what makes rule 2 hold. Simply
   writing the older syntax was not enough: ruff inherits
   `pyproject.toml`'s `target-version = "py314"`, and `ruff format`
   *actively rewrote* `except (A, B):` back into PEP 758's
   `except A, B:` -- so the repository's own formatter was reintroducing
   the bug on every `make lint`, and the first fix for it lasted exactly
   one CI run. The scoped config sets `target-version = "py39"` for this
   directory only, `extend`ing everything else from the root, which both
   stops the rewrite and makes `ruff check` flag newer syntax here as an
   error in its own right. Worth remembering generally: a formatter
   configured for one language level will happily upgrade syntax in a
   file that runs at another.
3. **Never fail invisibly.** A formatting convenience must not fail the
   tool call it is attached to (still `return 0` on every path), but it
   must say so on stderr when a subprocess it runs fails. This hook
   discarded ruff's output entirely, which is the direct reason nothing
   ever surfaced.

`make typecheck` covers this directory as of the same date. Note that
neither mypy nor ruff could have found the original bug *as they were
then configured*: both read the file at the project's own target
version, under which it was valid. Pinning the floor in `ruff.toml`
is what changes that, and the parse test is what proves it.
