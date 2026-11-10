"""Configuration loading and validation for Download Monitor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXTENSIONS: dict[str, frozenset[str]] = {
    "images": frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".heic"}),
    "documents": frozenset({".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"}),
    "spreadsheets": frozenset({".xls", ".xlsx", ".csv", ".ods"}),
    "archives": frozenset({".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}),
    "audio": frozenset({".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}),
    "video": frozenset({".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"}),
    "applications": frozenset({".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"}),
}


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings with absolute paths."""

    download_folder: Path
    destinations: dict[str, Path]
    extensions: dict[str, frozenset[str]]
    poll_interval_seconds: float = 2.0
    stability_checks: int = 2

    def destination_for(self, filename: str | Path) -> Path:
        suffix = Path(filename).suffix.lower()
        for category, extensions in self.extensions.items():
            if suffix in extensions:
                return self.destinations.get(category, self.destinations["other"])
        return self.destinations["other"]


def load_settings(path: str | Path) -> Settings:
    """Load and validate a JSON settings file."""
    config_path = Path(path).expanduser().resolve()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Settings file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in settings file: {exc}") from exc
    if not isinstance(raw.get("download_folder"), str) or not raw["download_folder"].strip():
        raise ValueError("Settings must define a non-empty 'download_folder'.")
    base = config_path.parent

    def resolve(value: str) -> Path:
        candidate = Path(value).expanduser()
        return (candidate if candidate.is_absolute() else base / candidate).resolve()

    destinations_raw = raw.get("destinations", {})
    if not isinstance(destinations_raw, dict):
        raise ValueError("'destinations' must be an object mapping categories to folders.")  # noqa: TRY004
    destinations = {str(category): resolve(folder) for category, folder in destinations_raw.items()}
    destinations.setdefault("other", base / "Other")
    extensions_raw = raw.get("extensions", {})
    if not isinstance(extensions_raw, dict):
        raise ValueError("'extensions' must be an object mapping categories to suffix lists.")  # noqa: TRY004
    extensions = {
        str(category): frozenset(
            suffix.lower() if str(suffix).startswith(".") else f".{str(suffix).lower()}"
            for suffix in suffixes
        )
        for category, suffixes in extensions_raw.items()
    }
    if not extensions:
        extensions = DEFAULT_EXTENSIONS
    interval = float(raw.get("poll_interval_seconds", 2.0))
    checks = int(raw.get("stability_checks", 2))
    if interval <= 0 or checks < 1:
        raise ValueError("'poll_interval_seconds' must be positive and 'stability_checks' at least 1.")
    return Settings(resolve(raw["download_folder"]), destinations, extensions, interval, checks)
