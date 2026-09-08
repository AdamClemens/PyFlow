"""Fail if docs/repository-manifest.md and the repository disagree.

The manifest states its own contract: "Every maintained file should
appear here exactly once, either as its own row or under an explicitly
stated collective rule." Nothing enforced that, and it failed twice --
v0.1 described roughly 35 handbook files that never existed while
omitting most of the repository, and `.claude/` sat unrecorded from
early in Stage 0 until a hand sweep found it on 2026-08-19.

This checks the half of the manifest that is a fact. The other half --
what each artifact is *for*, and how complete it is -- is judgement and
institutional memory, stays hand-written, and is not checked here.
`docs/repository-inventory.md` is the generated companion listing what
the repository contains; this validator is what keeps the hand-written
document honest about the same set of files.

RULES (one test each in tests/unit/test_check_manifest.py):

- manifest-covers-every-file: every tracked file is named in the
  manifest -- by full path or by basename, since the tables list bare
  filenames -- or matched by a declared collective rule.
- collective-rule-matches-something: every declared collective rule
  globs at least one tracked file. A rule matching nothing is a typo or
  a leftover, and either way it silently widens an exemption list.
- not-started-is-empty: a row marked with the "Not Started" symbol names
  a file that is absent or genuinely empty, per the manifest's own
  legend.
- ka-name-matches-manifest: where a manifest row cites `(KA-NNN)` and
  that id exists as a heading in `docs/planning/knowledge-architecture.md`
  with a `**Name:**` field, the row's own filename cell must name the
  same file (by final path segment) as that field. Says nothing about
  completeness in either direction -- a KA entry no manifest row cites,
  or a citation naming a KA-NNN with no such heading, are not flagged by
  this rule. A narrower "every KA cited, every citation resolves" rule
  was considered and rejected for the same reason the fourth rule below
  was: `docs/planning/knowledge-architecture.md` retires entries in prose
  on purpose (KA-034, KA-038 among them), the same way this manifest
  retires paths on purpose, so either completeness direction would very
  likely reproduce that rule's own false-positive failure. Scoping to
  "both sides already agree the id exists" keeps every finding a
  structural fact instead.
- claude-md-count-matches-live: this document's own "CLAUDE.md files"
  section states "As of DATE: **N files exist**"; N must equal the live
  count of tracked files named `CLAUDE.md`. Added 2026-09-08
  (failure-mode audit) after finding, by hand, that this exact claim had
  drifted two updates behind `docs/planning/roadmap.md`'s own copy of the
  same fact -- `tools/generators/generate_status_report.py`'s
  `check-status` already cross-checks the roadmap's copy against the live
  count, but nothing checked this document's *separate* restatement of
  it, so the two could (and did) disagree silently. Deliberately narrow,
  the same shape as `ka-name-matches-manifest` above: this is the one
  claim in this document phrased consistently enough (a fixed "As of
  DATE: **N files exist**" form) to extract and check by regex without
  needing a reader, not a general "every count in this document is
  checked" rule.

**A fourth rule was built and removed rather than shipped** (2026-08-21):
"every path the manifest names exists". It produced 44 findings on the
real manifest and essentially all were false. The manifest deliberately
names things that no longer exist -- `tools/planner/`,
`assets/textures/`, `docs/planning/numerical-frameworks.md` -- because
recording *what was retired and why* is a large part of its value. It
also names paths relative to the section they appear under (`data/
capabilities.yaml` inside the `planning/` section), and `ADR-00N-title.md`
as a naming template. Telling those apart from a genuinely stale
reference needs a reader, and this validator gates; a gate whose output
needs interpretation is the thing `tools/validators/CLAUDE.md` warns
against. `check_docs.py` already covers the checkable subset -- broken
Markdown *links*.

Collective rules are declared in the manifest itself, inside a fenced
```text collective-coverage block, rather than in this script -- so the
document's own statement of the rule and the mechanism enforcing it
cannot drift apart (P-011).

Run via `make check-manifest`, part of `make ci`. It gates rather than
advising, for the reason `tools/validators/CLAUDE.md` records: every
rule here is a definite structural fact, not a judgement call.
"""

from __future__ import annotations

import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path("docs") / "repository-manifest.md"
KA_DOC_PATH = Path("docs") / "planning" / "knowledge-architecture.md"

NOT_STARTED = "⬜"

COLLECTIVE_BLOCK = re.compile(r"```text collective-coverage\n(.*?)```", re.DOTALL)
# A row's leading cell, for `| name | status | ... |` tables.
TABLE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|(.*)$")
# `## KA-NNN — Title`, and that entry's `**Name:** \`path\`` field. The
# `~{0,2}` tolerates a strikethrough (KA-034's retired entry) without
# needing to special-case it -- the backtick pair survives intact either
# way.
KA_HEADING = re.compile(r"^## (KA-\d{3})\b", re.MULTILINE)
KA_NAME = re.compile(r"\*\*Name:\*\*\s*~{0,2}`([^`]+)`")
KA_CITATION = re.compile(r"\(KA-(\d{3})\)")
# The manifest's own "CLAUDE.md files" section states this in a fixed form
# -- see the RULES docstring's claude-md-count-matches-live entry.
MANIFEST_CLAUDE_MD_CLAIM = re.compile(r"As of \d{4}-\d{2}-\d{2}:\s*\*\*(\d+)\s+files exist")


def _ka_names(ka_doc: str) -> dict[str, str]:
    """`{KA-NNN: name_path}` for every entry with a `**Name:**` field.

    Scoped per-entry (heading to next heading) rather than document-wide,
    so a `**Name:**` field can never be attributed to the wrong id.
    """
    headings = list(KA_HEADING.finditer(ka_doc))
    names: dict[str, str] = {}
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(ka_doc)
        name_match = KA_NAME.search(ka_doc[start:end])
        if name_match is not None:
            names[heading.group(1)] = name_match.group(1)
    return names


def _tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    return sorted(result.stdout.split())


def _collective_rules(manifest: str) -> list[str]:
    rules: list[str] = []
    for block in COLLECTIVE_BLOCK.findall(manifest):
        for line in block.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                rules.append(stripped)
    return rules


def check_manifest(root: Path = REPO_ROOT) -> list[str]:
    """Every rule violation, as `<rule-id>: <detail>` strings.

    `root` is a parameter so tests can build miniature repositories in
    `tmp_path` -- a test asserting against the real manifest would fail
    every time the manifest legitimately changed.
    """
    findings: list[str] = []
    manifest_file = root / MANIFEST_PATH
    if not manifest_file.is_file():
        return [f"manifest-covers-every-file: {MANIFEST_PATH.as_posix()} does not exist"]

    manifest = manifest_file.read_text(encoding="utf-8")
    tracked = _tracked_files(root)
    rules = _collective_rules(manifest)

    # -- manifest-covers-every-file, collective-rule-matches-something --
    used_rules: set[str] = set()
    for path in tracked:
        if path in manifest or Path(path).name in manifest:
            continue
        matched = next((rule for rule in rules if fnmatch(path, rule)), None)
        if matched is None:
            findings.append(
                f"manifest-covers-every-file: {path} is not named in "
                f"{MANIFEST_PATH.as_posix()} and matches no collective rule"
            )
        else:
            used_rules.add(matched)

    # A rule is "used" only when it covers a file the manifest does not
    # name outright -- so a rule kept alongside individual rows still
    # counts, as long as something matches its glob.
    for rule in rules:
        if rule not in used_rules and not any(fnmatch(path, rule) for path in tracked):
            findings.append(f"collective-rule-matches-something: '{rule}' matches no tracked file")

    # -- not-started-is-empty -------------------------------------------
    for line in manifest.splitlines():
        if NOT_STARTED not in line:
            continue
        row = TABLE_ROW.match(line)
        if row is None or NOT_STARTED not in row.group(2):
            # Prose mentioning the symbol (the legend itself, for one) is
            # not a status claim about a file.
            continue
        name = row.group(1).strip().strip("`")
        matches = [path for path in tracked if Path(path).name == name or path == name]
        for path in matches:
            if (root / path).stat().st_size > 0:
                findings.append(
                    f"not-started-is-empty: row '{name}' is marked Not Started, "
                    f"but {path} has content"
                )

    # -- ka-name-matches-manifest ----------------------------------------
    # Silent, not a finding, if the KA document is absent: this rule only
    # has something to say where both documents already agree an id
    # exists, and a repository (or test fixture) without the KA document
    # has nothing to compare.
    ka_doc_file = root / KA_DOC_PATH
    if ka_doc_file.is_file():
        ka_names = _ka_names(ka_doc_file.read_text(encoding="utf-8"))
        for line in manifest.splitlines():
            row = TABLE_ROW.match(line)
            if row is None:
                continue
            row_name = row.group(1).strip().strip("`")
            for number in KA_CITATION.findall(row.group(2)):
                ka_id = f"KA-{number}"
                name_path = ka_names.get(ka_id)
                if name_path is None or Path(row_name).name == Path(name_path).name:
                    continue
                findings.append(
                    f"ka-name-matches-manifest: {ka_id} names {name_path} in "
                    f"{KA_DOC_PATH.as_posix()}, but the manifest row citing it "
                    f"names {row_name}"
                )

    # -- claude-md-count-matches-live ------------------------------------
    claim = MANIFEST_CLAUDE_MD_CLAIM.search(manifest)
    if claim is not None:
        claimed = int(claim.group(1))
        live = sum(1 for path in tracked if Path(path).name == "CLAUDE.md")
        if claimed != live:
            findings.append(
                f"claude-md-count-matches-live: manifest claims {claimed} CLAUDE.md "
                f"files, but {live} exist in the repository (`git ls-files`)"
            )

    return findings


def main() -> int:
    findings = check_manifest()
    if findings:
        for finding in findings:
            print(finding)
        print(f"\n{len(findings)} manifest inconsistency/inconsistencies found.")
        return 1

    print("Repository manifest matches the repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
