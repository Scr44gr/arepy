"""Command-line interface for the Arepy builder."""

import argparse
import sys
from pathlib import Path
from collections.abc import Sequence

from .config import BuildConfig
from .core import Builder
from .errors import BuilderError
from .models import BuildTarget


def create_parser(prog: str = "arepy") -> argparse.ArgumentParser:
    """Create the public Arepy command-line parser."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description="Build and export Arepy games.",
    )
    parser.add_argument(
        "--export",
        dest="export_targets",
        nargs="+",
        choices=[target.value for target in BuildTarget],
        metavar="TARGET",
        help="Export to one or more platforms.",
    )
    parser.add_argument(
        "legacy_targets",
        nargs="*",
        choices=[target.value for target in BuildTarget],
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--config",
        default="arepy.build.toml",
        help="Path to the build TOML file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the public Arepy CLI."""

    program_name = Path(sys.argv[0]).stem if argv is None else "arepy"
    if program_name == "__main__":
        program_name = "arepy"
    parser = create_parser(program_name)
    args = parser.parse_args(argv)
    targets = _unique_targets([*(args.export_targets or ()), *args.legacy_targets])
    if not targets:
        parser.error("the following argument is required: --export TARGET")

    try:
        config = BuildConfig.from_file(Path(args.config))
        artifacts = Builder().build(config, targets)
    except (BuilderError, OSError, ValueError) as error:
        print(f"{parser.prog}: {error}", file=sys.stderr)
        return 1

    for artifact in artifacts:
        print(f"{artifact.target.value}: {artifact.output_path}")
        print(f"manifest: {artifact.manifest_path}")
    return 0


def _unique_targets(targets: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(targets))


if __name__ == "__main__":
    raise SystemExit(main())
