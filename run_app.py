"""
Launcher for the Masterliste Updater Streamlit app.
This file is used as the PyInstaller entry point.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    # When frozen by PyInstaller, files are extracted to sys._MEIPASS
    if getattr(sys, "frozen", False):
        app_path = os.path.join(sys._MEIPASS, "app.py")  # type: ignore[attr-defined]
    else:
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
