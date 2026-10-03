"""Command-line entry point: ``thot {transcribe,live,gui}``."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from thot import __version__
from thot.cli import live, transcribe
from thot.cli.console import setup_logging


def _run_gui(args: argparse.Namespace) -> int:
    from thot.gui.app import main as gui_main

    return gui_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thot", description="THOT — offline speech-to-text.")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug output")
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    transcribe.register(subparsers)
    live.register(subparsers)
    subparsers.add_parser("gui", help="open the desktop interface").set_defaults(func=_run_gui)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print(file=sys.stderr)
        return 130
