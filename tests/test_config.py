import json
from pathlib import Path

import pytest

from download_monitor.config import Settings, load_settings


def test_load_settings_resolves_relative_paths_from_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text(
        json.dumps(
            {
                "download_folder": "Downloads",
                "destinations": {"documents": "Sorted/Documents"},
                "extensions": {"documents": [".pdf", "docx"]},
            }
        ),
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.download_folder == tmp_path / "Downloads"
    assert settings.destination_for("document.pdf") == tmp_path / "Sorted" / "Documents"
    assert settings.extensions["documents"] == frozenset({".pdf", ".docx"})


def test_load_settings_rejects_missing_download_folder(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text(json.dumps({"destinations": {}}), encoding="utf-8")

    with pytest.raises(ValueError, match="download_folder"):
        load_settings(config_path)


def test_destination_for_unknown_extension_uses_other(tmp_path: Path) -> None:
    settings = Settings(
        download_folder=tmp_path,
        destinations={"other": tmp_path / "Other"},
        extensions={"documents": frozenset({".pdf"})},
    )

    assert settings.destination_for("archive.xyz") == tmp_path / "Other"
