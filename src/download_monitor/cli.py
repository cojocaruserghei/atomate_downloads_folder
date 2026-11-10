"""Command-line interface for Download Monitor."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import load_settings
from .monitor import DownloadMonitor

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Organize downloaded files by type.")
    parser.add_argument("-c", "--config", type=Path, default=Path("settings.json"), help="JSON settings file")
    parser.add_argument("--once", action="store_true", help="scan once and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable informational logging")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s")
    try:
        settings = load_settings(args.config)
    except ValueError as exc:
        LOGGER.error("%s", exc)
        return 2
    monitor = DownloadMonitor(settings)
    try:
        if args.once:
            monitor.scan_once()
        else:
            monitor.run()
    except KeyboardInterrupt:
        LOGGER.info("Stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
