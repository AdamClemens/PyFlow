"""Entry point for `python -m pyflow`.

With no arguments: prints version and help (backlog C1a) -- unchanged
from Stage 0's placeholder behaviour, still what
`tests/integration/test_cli.py` checks.

`pyflow run`: the real bootstrap (TASK-010, backlog D4) -- load
configuration, initialise logging, open the rendering window, run the
loop, exit cleanly. Kept as a subcommand rather than the bare-invocation
default so the existing no-args contract doesn't change underneath it.

`pyflow generate-config` (TASK-039): prints a valid `PyFlowConfig` YAML
scaffold to stdout, or writes it to `--output PATH` if given -- so a
config author starts from something `load_config` already accepts
rather than hand-typing section and field names from memory.

`pyflow run --demos [NAME_OR_NUMBER]` (TASK-043): a shortcut for
`--config examples/golden-demos/<name>.yaml`, resolved by
`pyflow.configuration.golden_demos.resolve_golden_demo` against its own
curated registry. Bare (no value) prints the available demos and exits
without running anything -- `format_golden_demos_listing()`, not
`bootstrap()`. Mutually exclusive with `--config` (an `argparse` mutually
exclusive group, so passing both is rejected by `argparse` itself, not by
bespoke code here); an unresolvable name or out-of-range number is
rejected via `run_parser.error(...)`, the same rejection path
`--backend`'s `choices=` already uses for an invalid backend.

The top-level parser's own `description`/`epilog` (below) is the CLI's
self-description, printed both by bare invocation and by `--help`.
**It must be kept current with what the CLI can actually do** -- see
`src/pyflow/CLAUDE.md`'s dated rule, added 2026-08-28 after this text
spent well past Stage 0 still claiming "no simulation functionality
yet" and never mentioning `--config` or how to run a golden demo at
all (argparse does not surface a subcommand's own flags at the
top level, so `run_parser`'s `--config` help text alone was never
enough). `description` is phrased by capability, not by roadmap stage
number, so it does not need editing every stage exit.
"""

import argparse
from pathlib import Path
from typing import cast, get_args

from pyflow import __version__
from pyflow.bootstrap import bootstrap
from pyflow.configuration.generator import generate_config_yaml
from pyflow.configuration.golden_demos import (
    UnknownGoldenDemoError,
    format_golden_demos_listing,
    resolve_golden_demo,
)
from pyflow.configuration.schema import RenderBackend

# Sentinel for `--demos` given with no value ("list the demos"),
# distinguishable from both "not given at all" (`None`, the default) and
# any real name/number a user could type -- `argparse`'s own `const`
# mechanism for an optional-value option (`nargs="?"`).
_LIST_DEMOS = object()


def main(argv: list[str] | None = None) -> None:
    """`argv`, if given, is parsed instead of `sys.argv[1:]` -- the same
    convention `argparse.ArgumentParser.parse_args` itself uses. Exists
    so `tests/unit/test_main.py` can call this in-process: coverage.py
    can't see into the subprocess `tests/integration/test_cli.py` and
    `test_bootstrap.py` deliberately use to test the real packaged entry
    point, so without this, `__main__.py` would show 0% covered despite
    genuinely being exercised by those tests. Behaviour is identical
    either way -- `argv=None` still reads `sys.argv`.
    """
    parser = argparse.ArgumentParser(
        prog="pyflow",
        description=(
            "PyFlow: a modular, field-centric computational fluid dynamics\n"
            "engine. Configure a mesh, boundary conditions, and numerical\n"
            "scheme in YAML, and PyFlow will assemble, run, and visualise\n"
            "the simulation."
        ),
        epilog=(
            "examples:\n"
            "  pyflow run\n"
            "      Run with the built-in default configuration.\n"
            "  pyflow run --config path/to/config.yaml\n"
            "      Run with your own configuration file.\n"
            "  pyflow run --config examples/golden-demos/<name>.yaml\n"
            "      Run one of the golden demos shipped under "
            "examples/golden-demos/\n"
            "      (see docs/implementation/golden-demos.md for what each "
            "one shows).\n"
            "  pyflow run --demos lid_driven_cavity\n"
            "      Shortcut for the above -- run a golden demo by its "
            "curated name or number.\n"
            "  pyflow run --demos\n"
            "      List the available demos and their numbers.\n"
            "  pyflow generate-config --output config.yaml\n"
            "      Write a valid starting configuration file, ready to "
            "edit.\n"
            "\n"
            "Run 'pyflow <command> --help' for a command's own options -- "
            "e.g. 'pyflow run --help'\n"
            "for --config, --demos, --max-frames, and --backend."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Bootstrap the engine: load configuration, initialise logging, "
        "open the rendering window, and run until it's closed.",
        epilog=(
            "examples:\n"
            "  pyflow run --config examples/golden-demos/<name>.yaml "
            "--backend offscreen --max-frames 100\n"
            "  pyflow run --demos lid_driven_cavity --backend offscreen "
            "--max-frames 100\n"
            "  pyflow run --demos\n"
            "      List the available demos (name is stable; number is a "
            "convenience index only).\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    config_or_demo = run_parser.add_mutually_exclusive_group()
    config_or_demo.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a YAML configuration file (default: built-in defaults).",
    )
    config_or_demo.add_argument(
        "--demos",
        nargs="?",
        const=_LIST_DEMOS,
        default=None,
        metavar="NAME_OR_NUMBER",
        help="Run a bundled golden demo by its curated name or 1-indexed "
        "number, instead of --config. With no value, list the available "
        "demos and exit.",
    )
    run_parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Exit automatically after this many rendered frames, instead of "
        "waiting for the window to be closed. For automated/headless runs.",
    )
    run_parser.add_argument(
        "--backend",
        choices=get_args(RenderBackend),
        default=None,
        help="Override the configured rendering.backend (e.g. force "
        "'offscreen' for a headless run of an interactive config).",
    )

    generate_config_parser = subparsers.add_parser(
        "generate-config",
        help="Print a valid PyFlowConfig YAML scaffold (the schema's own "
        "defaults) to stdout, or write it to --output.",
    )
    generate_config_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the generated YAML to this path instead of stdout.",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        if args.demos is _LIST_DEMOS:
            print(format_golden_demos_listing())
            return

        config_path = args.config
        if args.demos is not None:
            try:
                config_path = resolve_golden_demo(args.demos)
            except UnknownGoldenDemoError as exc:
                run_parser.error(str(exc))

        # argparse's `choices` guarantees this is a valid RenderBackend
        # at runtime; mypy can't see that from `choices=` alone, hence
        # the cast rather than a broader `str | None` on bootstrap()'s
        # own signature (which would let an *invalid* string through
        # from any other caller).
        bootstrap(
            config_path,
            max_frames=args.max_frames,
            backend=cast("RenderBackend | None", args.backend),
        )
        return

    if args.command == "generate-config":
        yaml_text = generate_config_yaml()
        if args.output is None:
            print(yaml_text, end="")
        else:
            args.output.write_text(yaml_text, encoding="utf-8")
        return

    print(f"pyflow {__version__}")
    parser.print_help()


if __name__ == "__main__":
    main()
