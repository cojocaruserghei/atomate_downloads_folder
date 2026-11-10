# Download Monitor

Download Monitor is a small, safe Python application that uses the `watchdog` library to watch a Downloads folder and move completed files into configurable category folders.

## Features

- Works with a Downloads folder located anywhere on the computer.
- JSON settings for destinations, extensions, polling interval, and completion checks.
- Waits for a file to stop changing before moving it.
- Ignores temporary download files such as `.crdownload` and `.part`.
- Never overwrites a file; collisions become `name (1).ext`, `name (2).ext`, and so on.
- Unknown extensions go to the `other` destination.
- Usable as a package, command-line application, or importable library.

## Quick start

Requires Python 3.11 or newer.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item config.example.json settings.json
# Edit settings.json and set your download_folder and destinations.
download-monitor --config settings.json --once --verbose
download-monitor --config settings.json --verbose
```

The first command performs one scan. The second keeps monitoring with watchdog filesystem events until you press `Ctrl+C`. Destination paths in the example are relative to the settings file; absolute Windows paths are also supported.

## Configuration

`download_folder` is the folder to watch. Each key in `destinations` is a category, and each category in `extensions` contains the suffixes assigned to it. Extensions may be written with or without a leading dot and are case-insensitive.

`stability_checks` defaults to `2`: a file must have the same size across two scans before it is moved. Increase it for slow or unreliable downloads. `poll_interval_seconds` defaults to `2`.

## Development

```powershell
pip install -e .
pip install pytest
pytest
```

The project uses a `src/` layout, type-oriented dataclasses, a narrow service boundary between monitoring and organizing, and filesystem tests using temporary directories.

## Project layout

```text
src/download_monitor/
  cli.py          # command-line entry point
  config.py       # JSON loading and validation
  monitor.py      # polling and stability tracking
  organizer.py    # safe classification and moving
tests/            # behavior-focused unit tests
config.example.json
pyproject.toml
```

## License

MIT. See [LICENSE](LICENSE).
