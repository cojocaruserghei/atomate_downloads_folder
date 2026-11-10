from pathlib import Path

from download_monitor.config import Settings
from download_monitor.organizer import FileOrganizer


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        download_folder=tmp_path / "Downloads",
        destinations={
            "documents": tmp_path / "Documents",
            "other": tmp_path / "Other",
        },
        extensions={"documents": frozenset({".pdf", ".txt"})},
    )


def test_organize_moves_file_to_matching_destination(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    source = settings.download_folder
    source.mkdir()
    file_path = source / "report.pdf"
    file_path.write_text("report", encoding="utf-8")

    result = FileOrganizer(settings).organize(file_path)

    assert result.destination == tmp_path / "Documents" / "report.pdf"
    assert not file_path.exists()
    assert result.destination.read_text(encoding="utf-8") == "report"


def test_organize_renames_when_destination_exists(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    settings.download_folder.mkdir()
    destination = tmp_path / "Documents"
    destination.mkdir()
    (destination / "report.pdf").write_text("old", encoding="utf-8")
    file_path = settings.download_folder / "report.pdf"
    file_path.write_text("new", encoding="utf-8")

    result = FileOrganizer(settings).organize(file_path)

    assert result.destination.name == "report (1).pdf"
    assert result.destination.read_text(encoding="utf-8") == "new"


def test_organize_ignores_directories_and_temporary_files(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    settings.download_folder.mkdir()
    directory = settings.download_folder / "folder.pdf"
    directory.mkdir()
    temporary = settings.download_folder / "partial.pdf.crdownload"
    temporary.write_text("in progress", encoding="utf-8")

    organizer = FileOrganizer(settings)

    assert organizer.organize(directory) is None
    assert organizer.organize(temporary) is None
