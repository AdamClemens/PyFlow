"""Entry point for `python -m pyflow`.

With no arguments: prints version and help (backlog C1a) -- unchanged
from Stage 0's placeholder behaviour, still what
`tests/integration/test_cli.py` checks.

`pyflow run`: the real bootstrap (TASK-010, backlog D4) -- load
configuration, initialise logging, open the rendering window, run the
loop, exit cleanly. Kept as a subcommand rather than the bare-invocation
default so the existing no-args contract doesn't change underneath it.
"""

import argparse
from pathlib import Path

from pyflow import __version__
from pyflow.bootstrap import bootstrap


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pyflow",
        description="PyFlow: a modular, field-centric computational fluid "
        "dynamics engine. Stage 0 skeleton -- no simulation "
        "functionality yet.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Bootstrap the engine: load configuration, initialise logging, "
        "open the rendering window, and run until it's closed.",
    )
    run_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a YAML configuration file (default: built-in defaults).",
    )
    run_parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Exit automatically after this many rendered frames, instead of "
        "waiting for the window to be closed. For automated/headless runs.",
    )

    args = parser.parse_args()

    if args.command == "run":
        bootstrap(args.config, max_frames=args.max_frames)
        return

    print(f"pyflow {__version__}")
    parser.print_help()


if __name__ == "__main__":
    main()
