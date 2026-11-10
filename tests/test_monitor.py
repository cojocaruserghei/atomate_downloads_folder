from pathlib import Path

from watchdog.events import FileCreatedEvent, FileModifiedEvent

from download_monitor.config import Settings
from download_monitor.monitor import DownloadEventHandler, DownloadMonitor
from download_monitor.organizer import FileOrganizer


def test_scan_organizes_only_stable_files(tmp_path: Path) -> None:
    settings = Settings(
        download_folder=tmp_path / "Downloads",
        destinations={"other": tmp_path / "Other"},
        extensions={},
    )
    settings.download_folder.mkdir()
    pending = settings.download_folder / "pending.zip"
    pending.write_bytes(b"pending")
    organizer = FileOrganizer(settings)
    monitor = DownloadMonitor(settings, organizer=organizer, stability_checks=2)

    first = monitor.scan_once()
    second = monitor.scan_once()

    assert first == []
    assert len(second) == 1
    assert second[0].destination == tmp_path / "Other" / "pending.zip"


def test_watchdog_events_organize_a_file_after_it_is_stable(tmp_path: Path) -> None:
    settings = Settings(
        download_folder=tmp_path / "Downloads",
        destinations={"other": tmp_path / "Other"},
        extensions={},
    )
    settings.download_folder.mkdir()
    file_path = settings.download_folder / "new.zip"
    file_path.write_bytes(b"download")
    monitor = DownloadMonitor(settings, stability_checks=2)
    handler = DownloadEventHandler(monitor)

    handler.on_created(FileCreatedEvent(str(file_path)))
    assert file_path.exists()

    handler.on_modified(FileModifiedEvent(str(file_path)))
    assert (tmp_path / "Other" / "new.zip").exists()
