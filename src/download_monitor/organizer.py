"""Safe file-moving behavior."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from shutil import move

from .config import Settings

LOGGER = logging.getLogger(__name__)
TEMPORARY_SUFFIXES = (".crdownload", ".part", ".partial", ".tmp")


@dataclass(frozen=True)
class MoveResult:
    source: Path
    destination: Path
    category: str


class FileOrganizer:
    """Organize completed files without overwriting existing files."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def organize(self, file_path: str | Path) -> MoveResult | None:
        source = Path(file_path)
        if not source.is_file() or self._is_temporary(source):
            return None
        destination_dir = self.settings.destination_for(source)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = self._available_destination(destination_dir / source.name)
        move(str(source), str(destination))
        category = next(
            (category for category, suffixes in self.settings.extensions.items() if source.suffix.lower() in suffixes),
            "other",
        )
        LOGGER.info("Moved %s -> %s", source, destination)
        return MoveResult(source, destination, category)

    @staticmethod
    def _is_temporary(path: Path) -> bool:
        return path.name.startswith("~$") or path.suffix.lower() in TEMPORARY_SUFFIXES

    @staticmethod
    def _available_destination(candidate: Path) -> Path:
        if not candidate.exists():
            return candidate
        stem, suffix = candidate.stem, candidate.suffix
        counter = 1
        while True:
            next_candidate = candidate.with_name(f"{stem} ({counter}){suffix}")
            if not next_candidate.exists():
                return next_candidate
            counter += 1
