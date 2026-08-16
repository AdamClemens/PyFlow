"""Entry point for `python -m pyflow`.

Stage 0 placeholder (TASK-000/backlog C1a) -- confirms the package is
importable and executable, and gives a stable place to hang real CLI
arguments later. The real bootstrap (load configuration, initialise
logging, open the rendering window, enter the loop, exit cleanly) is
TASK-010 and does not exist yet.
"""

import argparse

from pyflow import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pyflow",
        description="PyFlow: a modular, field-centric computational fluid "
        "dynamics engine. Stage 0 skeleton -- no simulation "
        "functionality yet.",
    )
    parser.parse_args()
    print(f"pyflow {__version__}")
    parser.print_help()


if __name__ == "__main__":
    main()
