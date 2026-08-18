"""Report documentation claims that a file or directory is empty when it isn't.

`docs/practices.md` ("Completeness claims belong only in the two documents
that track completeness") exists because the same drift was found nine times
in one review: a document saying some *other* file was empty, unwritten, or a
stub, long after that file was written. A stale completeness claim reads
exactly as confidently as a true one, which is what makes it dangerous.

This script mechanises the checkable half of that rule. It does **not**
pattern-match prose and guess: it finds lines making a completeness claim,
resolves the paths named on the same line, and reports only where the claim
contradicts what is actually on disk. "`foo.md` is empty" is reported when
`foo.md` has content; it is not reported when `foo.md` really is empty, or
does not exist.

Deliberately advisory, not a `make ci` gate -- see `tools/validators/CLAUDE.md`.
It reports candidates for a human to confirm, because a document legitimately
quoting the rule, or describing its own directory, is indistinguishable from a
violation without judgement. Run it via `make check-claims`, and as step 10 of
the end-of-session consistency review in `docs/practices.md`.

Exit code is 0 even when findings exist, so it never blocks a commit; a
non-zero exit means the script itself failed.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
}

# Files whose job is to record how complete things are, or to teach/quote this
# very rule. A claim in one of these is not drift. Keep this list short and
# justified -- every addition weakens the check.
EXCLUDED_FILES = {
    # These two track completeness; that is what they are for.
    "docs/repository-manifest.md",
    "docs/planning/backlog.md",
    # Append-only history: past entries describe the state at the time, and are
    # corrected by appending rather than by editing.
    "docs/CHANGELOG-DESIGN.md",
    # These state the rule and quote real past violations verbatim.
    "docs/practices.md",
    "prompts/features/agents.md",
    "tools/validators/CLAUDE.md",
}

# Instantiated task prompts are a record of what was asked for at the time,
# deliberately not updated afterwards (`prompts/common/CLAUDE.md`), so a
# claim inside one describes the state when it was written.
EXCLUDED_GLOBS = ("prompts/common/task-*.md",)

CLAIM_PATTERN = re.compile(
    r"\b("
    r"is empty|are empty|currently empty|still empty"
    r"|not yet written|yet to be written|unwritten"
    r"|is a stub|empty stub"
    r"|still (?:a )?(?:generic )?placeholder"
    r"|remains? (?:a )?(?:generic )?placeholder"
    r"|remain (?:generic )?placeholders"
    r")\b",
    re.IGNORECASE,
)

# Backticked tokens that look like a repository path: `foo.md`, `docs/bar/`,
# `src/pyflow/baz.py`. Trailing punctuation inside the backticks is stripped.
PATH_TOKEN_PATTERN = re.compile(r"`([^`\s]+)`")

# A reporting verb before the claim means the document is describing someone
# else's claim, not making one: "engine.md still described the handbook as
# unwritten". Deliberately narrow -- see is_reported().
# Spelled out rather than stemmed. A truncated verb stem followed by a
# wildcard reads as a misspelling to the codespell hook -- which flagged this
# very line when it was written the other way -- and the explicit list is
# easier to audit anyway.
REPORTING_VERB_PATTERN = re.compile(
    r"\b(describe|describes|described|describing|say|says|said|read|reads|"
    r"call|calls|called|claim|claims|claimed|state|states|stated|wrote|"
    r"record|records|recorded|report|reports|reported)\b",
    re.IGNORECASE,
)

# A file with no more than this many non-blank lines counts as effectively
# empty -- a bare `# CLAUDE` heading, say, is not content a claim contradicts.
EMPTY_LINE_THRESHOLD = 1

# Never counted when deciding whether a directory holds anything.
DIRECTORY_NOISE = {"CLAUDE.md", "__init__.py", "README.md"}


def iter_markdown_files() -> list[Path]:
    return sorted(
        p for p in REPO_ROOT.rglob("*.md") if not any(part in EXCLUDED_DIRS for part in p.parts)
    )


def looks_like_path(token: str) -> bool:
    """True for tokens plausibly naming a repository file or directory."""
    if token.startswith(("http://", "https://", "#")):
        return False
    return "/" in token or token.endswith((".md", ".py", ".yaml", ".yml", ".toml"))


def resolve(token: str, relative_to: Path) -> Path | None:
    """Resolve a backticked path token against the repo root, then the
    mentioning file's own directory. Returns None if neither exists.

    Each base confines its own result: a token is only accepted if it stays
    inside the base it was resolved against, so "../../etc/passwd" resolves to
    nothing rather than escaping. The per-base confinement (rather than a
    single repo-root check) is also what lets these functions be tested
    against a tmp_path fixture.
    """
    candidate = token.rstrip("/.,;:")
    for base in (REPO_ROOT, relative_to.parent):
        resolved = (base / candidate).resolve()
        try:
            resolved.relative_to(base.resolve())
        except ValueError:
            continue
        if resolved.exists():
            return resolved
    return None


def file_has_content(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return False
    return len([line for line in text.splitlines() if line.strip()]) > EMPTY_LINE_THRESHOLD


def directory_has_content(path: Path) -> bool:
    """True when the directory holds at least one non-empty file that isn't
    scaffolding. `planning/data/` full of empty `.yaml` files is *not* content;
    `tests/unit/` full of real test modules is."""
    for child in path.rglob("*"):
        if not child.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in child.parts):
            continue
        if child.name in DIRECTORY_NOISE:
            continue
        if child.stat().st_size > 0:
            return True
    return False


def has_content(path: Path) -> bool:
    if path.is_dir():
        return directory_has_content(path)
    return file_has_content(path)


def is_reported(before: str) -> bool:
    """True when a reporting verb precedes the claim.

    "`engine.md` still described the handbook as unwritten" narrates a claim
    rather than making one -- the same distinction the quotation check draws,
    for prose that reports without quotation marks. Maintenance notes recording
    a past drift are the common case, and they are exactly the sentences a
    naive checker flags most.
    """
    return REPORTING_VERB_PATTERN.search(before) is not None


def is_quoted(before: str) -> bool:
    """True when the claim phrase sits inside quotation marks."""
    for opener, closer in (('"', '"'), ("“", "”"), ("‘", "’")):
        opens = before.count(opener)
        if opener == closer:
            if opens % 2 == 1:
                return True
        elif opens > before.count(closer):
            return True
    return False


def findings_for(md_file: Path) -> list[tuple[int, str, str]]:
    """Return (line number, referenced path, line text) for each contradicted
    claim in one Markdown file."""
    try:
        rel = md_file.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        # A file outside the repository (a test fixture, typically): no
        # exclusion list applies, so scan it.
        rel = ""
    if rel and rel in EXCLUDED_FILES:
        return []
    if rel and any(PurePosixPath(rel).match(pattern) for pattern in EXCLUDED_GLOBS):
        return []

    try:
        text = md_file.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return []

    results: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    for number, line in enumerate(lines, start=1):
        match = CLAIM_PATTERN.search(line)
        if match is None:
            continue
        # These documents hard-wrap at ~72 characters, so a sentence routinely
        # spans two lines: the path a claim is about, and any opening quote
        # qualifying it, are often on the line above. Both real drifts this was
        # built from wrapped that way, so a single-line window misses them.
        previous = lines[number - 2] if number >= 2 else ""
        before = f"{previous} {line[: match.start()]}"
        if is_quoted(before) or is_reported(before):
            continue
        window = f"{previous}\n{line}"
        for token in PATH_TOKEN_PATTERN.findall(window):
            if not looks_like_path(token):
                continue
            target = resolve(token, md_file)
            if target is None or target == md_file:
                continue
            if has_content(target):
                results.append((number, token, line.strip()))
    return results


def main() -> int:
    findings: list[tuple[str, int, str, str]] = []
    for md_file in iter_markdown_files():
        rel = md_file.relative_to(REPO_ROOT).as_posix()
        for number, token, line in findings_for(md_file):
            findings.append((rel, number, token, line))

    if not findings:
        print("No contradicted completeness claims found.")
        return 0

    print(f"{len(findings)} completeness claim(s) to confirm:")
    print()
    for rel, number, token, line in findings:
        print(f"{rel}:{number}")
        print(f"  claims `{token}` is empty/unwritten, but it has content")
        print(f"  {line}")
        print()
    print(
        "Advisory only -- confirm each before acting. A document quoting this "
        "rule, or\ndescribing its own directory, can legitimately look like a "
        "violation.\nSee docs/practices.md and tools/validators/CLAUDE.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
