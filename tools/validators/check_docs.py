"""Fail if any Markdown file links to a local file/anchor that doesn't exist.

Scans every ``*.md`` file in the repository for Markdown links
(``[text](target)``) and image references (``![alt](target)``). A target is
checked when it's a relative path (not ``http(s)://``, ``mailto:``, or a
bare ``#fragment`` within the same file) -- it's resolved relative to the
linking file's own directory and must exist on disk.

**Heading fragments are checked too** (added 2026-09-05). A target of
the form ``file.md#some-heading``, or a bare ``#some-heading`` naming a
heading in the linking file itself, is resolved against that file's own
headings. This was a recorded gap for a fortnight -- both this docstring
and ``tools/validators/CLAUDE.md`` said "verifying a heading exists
would need parsing every target file's heading slugs, which is a
different, heavier check" -- and it became worth building the moment
prose started linking *into generated documents*, whose headings a
generator can change without anyone noticing.

That is the point of it, and worth stating plainly: a cross-reference
into a generated document is only safe if something checks the anchor.
Without this, adding one would have traded a stale restatement for a
silently broken link, which is not an improvement.

The Markdown Definition of Done is in docs/documentation-guidelines.md;
this script mechanizes the parts of it -- broken relative links, and now
broken anchors -- that stayed a purely manual grep before.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
}

LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")
# GitHub's slug rule, as far as this repository's headings exercise it:
# lower-case, drop everything that is not a word character, space or
# hyphen, then hyphenate the spaces. Verified against real headings from
# the generated documents these links point at, not taken from a spec --
# `tests/unit/test_check_docs.py` pins the cases that matter.
_SLUG_STRIP = re.compile(r"[^\w\s-]")
_SLUG_SPACES = re.compile(r"\s")


def slugify(heading: str) -> str:
    """The anchor a Markdown heading gets."""
    text = heading.lstrip("#").strip().lower()
    return _SLUG_SPACES.sub("-", _SLUG_STRIP.sub("", text))


def heading_slugs(md_file: Path) -> set[str]:
    """Every anchor `md_file` offers.

    Repeated heading text gets `-1`, `-2` suffixes, which is what GitHub
    does and therefore what a link to the second occurrence has to say.
    Headings inside fenced code blocks are skipped: a `#` there is a
    comment or a shell prompt, and an anchor nobody can navigate to would
    make this check pass for the wrong reason.
    """
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in md_file.read_text(encoding="utf-8").splitlines():
        if FENCE_PATTERN.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_PATTERN.match(line)
        if match is None:
            continue
        base = slugify(match.group(2))
        if not base:
            continue
        count = seen.get(base, 0)
        slugs.add(base if count == 0 else f"{base}-{count}")
        seen[base] = count + 1
    return slugs


def iter_markdown_files() -> list[Path]:
    return sorted(
        p for p in REPO_ROOT.rglob("*.md") if not any(part in EXCLUDED_DIRS for part in p.parts)
    )


def is_local_target(target: str) -> bool:
    """A bare `#fragment` counts: it names a heading in the linking file
    itself, which is checkable now that headings are parsed. It was
    excluded while only paths were resolved, so a self-link to a renamed
    section was invisible.
    """
    return not target.startswith(("http://", "https://", "mailto:"))


def check_file(md_file: Path) -> list[tuple[int, str, str]]:
    """Return (line_number, target, reason) for every broken link in md_file."""
    broken: list[tuple[int, str, str]] = []
    text = md_file.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        # Strip inline code spans first -- prose describing Markdown syntax
        # itself (e.g. "a link looks like `[text](target)`") would otherwise
        # be flagged as a broken link to a literal file named "target".
        scanned_line = INLINE_CODE_PATTERN.sub("", line)
        for match in LINK_PATTERN.finditer(scanned_line):
            target = match.group(1).strip()
            if not is_local_target(target):
                continue
            path_part, _, fragment = target.partition("#")
            path_part = path_part.strip()
            fragment = fragment.strip()
            if not path_part:
                # A bare `#fragment`: the linking file's own headings.
                if fragment and fragment not in heading_slugs(md_file):
                    broken.append((lineno, target, "no such heading in this file"))
                continue
            resolved = (md_file.parent / path_part).resolve()
            if resolved.exists() and fragment and resolved.suffix == ".md":
                # Only Markdown has headings this script can resolve. A
                # fragment on anything else is somebody else's addressing
                # scheme (a line number, a YAML path) and not a claim to
                # check.
                if fragment not in heading_slugs(resolved):
                    try:
                        shown = str(resolved.relative_to(REPO_ROOT))
                    except ValueError:
                        shown = str(resolved)
                    broken.append((lineno, target, f"no such heading in {shown}"))
            if not resolved.exists():
                # A link can legitimately (or by mistake) climb above
                # REPO_ROOT via enough "../" segments -- relative_to() raises
                # ValueError rather than resolving in that case, so fall back
                # to the absolute path instead of assuming containment.
                try:
                    shown = str(resolved.relative_to(REPO_ROOT))
                except ValueError:
                    shown = str(resolved)
                broken.append((lineno, target, f"no such file: {shown}"))
    return broken


def main() -> int:
    total_broken = 0
    for md_file in iter_markdown_files():
        for lineno, target, reason in check_file(md_file):
            rel = md_file.relative_to(REPO_ROOT)
            print(f"{rel}:{lineno}: broken link '{target}' ({reason})")
            total_broken += 1

    if total_broken:
        print(f"\n{total_broken} broken relative link(s) found.")
        return 1

    print("No broken relative links found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
