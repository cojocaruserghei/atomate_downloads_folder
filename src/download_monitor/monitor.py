"""Polling monitor for completed downloads."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from threading import Event

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config import Settings
from .organizer import FileOrganizer, MoveResult

LOGGER = logging.getLogger(__name__)


class DownloadEventHandler(FileSystemEventHandler):
    """Forward file creation and modification events to a monitor."""

    def __init__(self, monitor: DownloadMonitor) -> None:
        super().__init__()
        self.monitor = monitor

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self.monitor.handle_path(event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self.monitor.handle_path(event.src_path)


class DownloadMonitor:
    """Watch a folder with watchdog and organize completed files."""

    def __init__(self, settings: Settings, organizer: FileOrganizer | None = None, stability_checks: int | None = None) -> None:
        self.settings = settings
        self.organizer = organizer or FileOrganizer(settings)
        self.stability_checks = stability_checks or settings.stability_checks
        self._sizes: dict[Path, tuple[int, int]] = {}

    def scan_once(self) -> list[MoveResult]:
        """Process the current files once; useful for one-shot runs and tests."""
        folder = self.settings.download_folder
        folder.mkdir(parents=True, exist_ok=True)
        results: list[MoveResult] = []
        for path in folder.iterdir():
            if not path.is_file():
                continue
            result = self.handle_path(path)
            if result:
                results.append(result)
        return results

    def handle_path(self, file_path: str | Path) -> MoveResult | None:
        """Process one event path once it has remained the same size."""
        path = Path(file_path)
        if not path.is_file():
            return None
        try:
            size = path.stat().st_size
        except OSError:
            return None
        previous_size, stable_count = self._sizes.get(path, (-1, 0))
        stable_count = stable_count + 1 if previous_size == size else 1
        self._sizes[path] = (size, stable_count)
        if stable_count < self.stability_checks:
            return None
        try:
            result = self.organizer.organize(path)
        except OSError as exc:
            LOGGER.warning("Could not organize %s: %s", path, exc)
            return None
        self._sizes.pop(path, None)
        return result

    def run(self, stop_requested: Callable[[], bool] | None = None) -> None:
        """Run the watchdog observer until interrupted or stopped."""
        self.settings.download_folder.mkdir(parents=True, exist_ok=True)
        stop_event = Event()
        observer = Observer()
        observer.schedule(DownloadEventHandler(self), str(self.settings.download_folder), recursive=False)
        observer.start()
        LOGGER.info("Monitoring %s with watchdog", self.settings.download_folder)
        try:
            while not (stop_requested and stop_requested()):
                stop_event.wait(timeout=0.5)
        finally:
            observer.stop()
            observer.join()
