"""wtcmddo: a lightweight command explainer with guardrails."""

from __future__ import annotations

import argparse
import subprocess

from . import tui
from .config import get_config
from .explainer import (
    ExplainerError,
    NotACommandError,
    explain_command,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="wtcmddo",
        description="Explain a shell command, assess its risk, and optionally run it.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="The shell command to explain. Put options after a '--' separator if needed.",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run interactive setup wizard.",
    )
    parser.add_argument(
        "--model",
        help="Model to use (overrides config/model).",
    )
    parser.add_argument(
        "--base-url",
        help="API base URL (overrides config/base-url).",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip the confirmation prompt and execute immediately.",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Only explain; do not ask to execute.",
    )
    return parser.parse_args(argv)


def _execute_command(command: str) -> int:
    tui.echo_command(command)
    try:
        result = subprocess.run(command, shell=True)
        return result.returncode
    except FileNotFoundError:
        tui.display_error("command not found.")
        return 127


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.setup:
        tui.run_setup()
        return 0

    command = " ".join(args.command)
    if not command:
        tui.display_error("No command provided.")
        return 1

    config = get_config()

    try:
        with tui.analyzing(command):
            result = explain_command(
                command,
                model=args.model or config["model"],
                base_url=args.base_url or config["base_url"],
            )
    except NotACommandError as exc:
        tui.display_error(str(exc))
        return 2
    except ExplainerError as exc:
        tui.display_error(str(exc))
        return 1

    tui.display_explanation(command, result)

    if args.dry_run:
        return 0

    if args.yes or tui.confirm_execution():
        return _execute_command(command)

    tui.display_aborted()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
