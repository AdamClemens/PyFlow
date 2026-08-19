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
