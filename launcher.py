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

    sys.argv = ["streamlit", "run", str(app_file)]
    return stcli.main()


if __name__ == "__main__":
    raise SystemExit(main())
