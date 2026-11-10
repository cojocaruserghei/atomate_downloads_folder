"""Allow ``python -m download_monitor`` to start the application."""

from .cli import main

raise SystemExit(main())
