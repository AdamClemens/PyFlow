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

`pyflow record --config <file> --max-frames N [--output-dir DIR]
[--checkpoint-interval N]` (TASK-045, Stage 8, Recording & Playback): a
new subcommand, not a flag on `run` -- it produces checkpoint files, not
pixels, the same "new capability, own inputs/outputs" shape
`generate-config` already set, unlike `--demos`, which is only an
alternate way to say what `run` already does. `--config`/`--max-frames`
are `required=True` here, unlike `run`'s own optional versions: a
headless record run with no config just re-records the built-in
defaults pointlessly, and an unbounded one has no natural stopping
point, neither of which `run`'s own interactive default has to worry
about. Dispatches to `pyflow.recording.record`, which never imports
`rendering` at all -- see that module's own docstring for why this is a
separate entry point rather than a `bootstrap()` keyword argument.

`pyflow resume --checkpoint <file> --max-frames N [--output-dir DIR]
[--checkpoint-interval N]` (TASK-045, added the same day as `record`
once a user asked how a second run would ingest `record`'s own output):
continues a headless recording from an existing checkpoint rather than
from frame 0 -- still no rendering window, still writing further
checkpoint files, not the dense per-frame replay TASK-046/047 still
owns. **Deliberately no `--config` flag at all** -- a checkpoint carries
its own, validated exactly as strictly as a config file
(`pyflow.checkpoint.read_checkpoint`), so naming one here would only
invite a mismatch between "the config this run resumes under" and
"the config a user happened to pass." `--checkpoint`/`--max-frames` are
`required=True`, the same reasoning `record`'s own required flags use;
`--max-frames` must additionally be past the checkpoint's own frame
count (`pyflow.recording.NothingToResumeError` otherwise). Dispatches to
`pyflow.recording.resume`, which shares its checkpoint-writing policy
with `record` (`recording.py`'s own `_advance_and_checkpoint`) so a
`record` to frame 6 followed by a `resume` to frame 12 writes the same
files an uninterrupted `record` to frame 12 would have.

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
from pyflow.recording import record, resume

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
            "  pyflow record --config path/to/config.yaml --max-frames 1000\n"
            "      Headlessly step a simulation forward, writing periodic "
            "checkpoints\n"
            "      to disk -- no rendering window at all.\n"
            "  pyflow resume --checkpoint checkpoints/checkpoint_00000100.pt "
            "--max-frames 500\n"
            "      Continue a headless recording from an existing "
            "checkpoint -- no --config,\n"
            "      the checkpoint carries its own.\n"
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

    record_parser = subparsers.add_parser(
        "record",
        help="Headlessly step a simulation forward and write periodic "
        "checkpoints to disk, with no rendering window at all.",
        epilog=(
            "examples:\n"
            "  pyflow record --config examples/golden-demos/heat_diffusion.yaml "
            "--max-frames 1000\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    record_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a YAML configuration file.",
    )
    record_parser.add_argument(
        "--max-frames",
        type=int,
        required=True,
        help="Step this many timesteps forward, then stop.",
    )
    record_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Where to write checkpoint files (default: config.recording.output_dir).",
    )
    record_parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=None,
        help="Frames between checkpoints (default: config.recording.checkpoint_interval).",
    )

    resume_parser = subparsers.add_parser(
        "resume",
        help="Read a checkpoint written by `record` (or a previous "
        "`resume`), and continue stepping headlessly from its own frame, "
        "writing further checkpoints. No --config -- the checkpoint "
        "carries its own.",
        epilog=(
            "examples:\n"
            "  pyflow resume --checkpoint checkpoints/checkpoint_00000100.pt "
            "--max-frames 500\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    resume_parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to a checkpoint file written by `pyflow record` or `pyflow resume`.",
    )
    resume_parser.add_argument(
        "--max-frames",
        type=int,
        required=True,
        help="Step forward to this frame, then stop. Must be greater than "
        "the checkpoint's own frame count.",
    )
    resume_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Where to write further checkpoint files (default: the checkpoint's own directory).",
    )
    resume_parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=None,
        help="Frames between checkpoints (default: the checkpoint's own "
        "embedded config.recording.checkpoint_interval).",
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

    if args.command == "record":
        result = record(
            args.config,
            max_frames=args.max_frames,
            output_dir=args.output_dir,
            checkpoint_interval=args.checkpoint_interval,
        )
        print(f"wrote {len(result.checkpoint_frames)} checkpoint(s) to {result.output_dir}")
        return

    if args.command == "resume":
        result = resume(
            args.checkpoint,
            max_frames=args.max_frames,
            output_dir=args.output_dir,
            checkpoint_interval=args.checkpoint_interval,
        )
        print(f"wrote {len(result.checkpoint_frames)} checkpoint(s) to {result.output_dir}")
        return

    print(f"pyflow {__version__}")
    parser.print_help()


if __name__ == "__main__":
    main()
