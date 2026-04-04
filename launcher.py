"""PyInstaller entry point to launch the Streamlit UI as a desktop app."""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import cli as stcli


def _app_path() -> Path:
    """Resolve the packaged location of app.py for frozen and source runs."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app.py"
    return Path(__file__).resolve().parent / "app.py"


def main() -> int:
    app_file = _app_path()
    if not app_file.exists():
        print(f"Could not find app file: {app_file}", file=sys.stderr)
        return 1

    # Ensure packaged runs are not affected by a user's global Streamlit
    # development mode, which conflicts with explicit server.port.
    sys.argv = [
        "streamlit",
        "run",
        str(app_file),
        "--global.developmentMode=false",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        "8501",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]
    return stcli.main()


if __name__ == "__main__":
    raise SystemExit(main())
