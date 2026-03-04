"""
CSV / file I/O helpers (no Streamlit dependency).
"""

from __future__ import annotations

import io

import pandas as pd

from .config import ENCODING_FALLBACKS


def load_csv_bytes(data: bytes, label: str, sep: str = ",") -> pd.DataFrame:
    """Try each encoding in ENCODING_FALLBACKS and return the first that succeeds."""
    last_err: Exception | None = None
    for enc in ENCODING_FALLBACKS:
        try:
            return pd.read_csv(io.BytesIO(data), sep=sep, encoding=enc)
        except (UnicodeDecodeError, LookupError) as exc:
            last_err = exc
    raise ValueError(f"Could not decode '{label}': {last_err}")


def df_to_csv_bytes(df: pd.DataFrame, encoding: str = "utf-8") -> bytes:
    """Serialise *df* to a semicolon-delimited CSV and return the raw bytes."""
    buf = io.BytesIO()
    df.to_csv(buf, sep=";", index=False, encoding=encoding)
    return buf.getvalue()
