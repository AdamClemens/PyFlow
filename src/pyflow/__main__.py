"""Entry point for `python -m pyflow`.

Stage 0 placeholder (TASK-000) -- confirms the package is importable and
executable. The real bootstrap (load configuration, initialise logging,
open the rendering window, enter the loop, exit cleanly) is TASK-010 and
does not exist yet.
"""

from pyflow import __version__


def main() -> None:
    print(f"pyflow {__version__} -- Stage 0 skeleton, no simulation functionality yet.")


if __name__ == "__main__":
    main()
