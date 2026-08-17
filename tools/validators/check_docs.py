"""Fail if any Markdown file links to a local file/anchor that doesn't exist.

Scans every ``*.md`` file in the repository for Markdown links
(``[text](target)``) and image references (``![alt](target)``). A target is
checked when it's a relative path (not ``http(s)://``, ``mailto:``, or a
bare ``#fragment`` within the same file) -- it's resolved relative to the
linking file's own directory and must exist on disk.

Only existence is checked, not intra-file heading anchors (``file.md#some-
heading``) -- verifying a heading exists would need parsing every target
file's heading slugs, which is a different, heavier check. The Markdown
Definition of Done is in docs/documentation-guidelines.md; this script only
mechanizes the one part of it -- broken relative links -- that stayed a
purely manual grep before.
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


def iter_markdown_files() -> list[Path]:
    return sorted(
        p for p in REPO_ROOT.rglob("*.md") if not any(part in EXCLUDED_DIRS for part in p.parts)
    )


def is_local_target(target: str) -> bool:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return False
    return True


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
            path_part = target.split("#", 1)[0].strip()
            if not path_part:
                continue
            resolved = (md_file.parent / path_part).resolve()
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
