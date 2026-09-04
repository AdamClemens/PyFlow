"""Fail if any tracked file records a date that has not happened yet.

``make check-dates``. Part of ``make ci``.

**Why this exists.** On 2026-09-04, 23 tracked files -- `CLAUDE.md`, the
roadmap, four graph files, six validators and their tests -- dated that
day's work as the day after. Two consecutive sessions wrote it, `make ci` was
green over it, and it was found only because somebody happened to
compare a document against `git log`. This repository dates almost
everything it records; a wrong date makes the record wrong in the one
dimension nothing else can reconstruct.

The end-of-session review's step 2 (`docs/practices.md`) already says to
grep for every restatement of a date -- but it is scoped to a fact the
session *knew* it was changing, and nobody knew. Step 8 of that list
asks for a new rule whenever a drift gets past it, which is this.

**Why it can gate, when "is this date right?" is obviously a
judgement.** It does not ask that. It asks only whether a date is in the
future, which is a definite fact about the calendar, and a record of
something that has not happened is wrong under any reading.

**How to write a genuinely future date.** In prose, without the ISO
form: "targeting December 2026", "early next year". This checks the full
`YYYY-MM-DD` form only, which this repository uses exclusively to record
things that have already happened -- so the question "is this future
date legitimate?" never arises, and the gate never needs a judgement.
That is the bar `tools/validators/CLAUDE.md` sets for anything in
`make ci`; a check needing a reader trains people to route around it.

**One thing to know before writing about a wrong date: prose that quotes
one trips the check.** Both documents describing this drift originally
named the bad date in the ISO form, and `check-dates` failed on its own
documentation the first time it ran -- correctly, since it cannot tell a
record from a quotation, and teaching it to would be teaching it
judgement. The fix is to reword ("dated it as the day after"), never to
add an exemption: an exemption list is where a gate goes to stop
mattering, and this one has exactly one escape by design -- write a
genuinely future point as prose, without the ISO form.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# `2026-09-04`, the only date form this repository records facts in.
# A bare month and year ("December 2026") is deliberately not matched --
# see the module docstring.
ISO_DATE = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")

RULES = ["no-future-dates"]


def tracked_files(root: Path = REPO_ROOT) -> list[str]:
    """What `git` says is in the repository, not what is on the disk.

    The same choice `generate_repository_inventory.py` makes and for the
    same reason: a directory walk describes the machine it runs on --
    `.venv/`, caches, scratch files -- so two clones of one commit would
    check different things.
    """
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    return result.stdout.splitlines()


def find_future_dates(
    root: Path,
    names: list[str],
    today: date | None = None,
) -> list[str]:
    """Every ISO date in `names` that lies after `today`.

    Every occurrence, not the first -- the drift that prompted this
    spanned 23 files, and a checker reporting one at a time turns one
    fix into twenty runs.
    """
    now = today or date.today()
    problems: list[str] = []
    for name in names:
        path = root / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError, UnicodeDecodeError:
            # `git ls-files` lists images and binaries too, and can name
            # a file already deleted from the working tree.
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in ISO_DATE.finditer(line):
                try:
                    found = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                except ValueError:
                    # `2026-13-45` is wrong, but it is not this check's
                    # finding, and claiming it would be claiming to have
                    # found something this never looked for.
                    continue
                if found > now:
                    problems.append(
                        f"no-future-dates: {name}:{line_number} records {found}, "
                        f"which is after today ({now}) -- a record of something "
                        "that has not happened"
                    )
    return problems


def main() -> int:
    names = tracked_files()
    if not names:
        print("No tracked files found -- a check that matches nothing reports nothing.")
        return 1

    problems = find_future_dates(REPO_ROOT, names)
    for problem in problems:
        print(problem)

    if problems:
        print(f"\n{len(problems)} future date(s) found.")
        print("A date this repository writes records something that happened. To name a")
        print('genuinely future point, write it as prose without the ISO form -- "targeting')
        print('December 2026" -- which this check deliberately does not match.')
        return 1

    print(f"No tracked file records a future date ({len(names)} files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
