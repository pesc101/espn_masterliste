"""I/O helpers: loading CSVs with encoding fallback and saving results."""

from __future__ import annotations

import pandas as pd

from .config import ENCODING_FALLBACKS


def load_csv(
    path: str, encoding: str = "utf-8", sep: str = ",", **kwargs
) -> pd.DataFrame:
    """
    Load a CSV file.

    *sep* defaults to ',' for the new English-language Orders/Contacts exports.
    Pass sep=';' explicitly for the semicolon-separated Masterliste files.
    Tries *encoding* first, then every entry in ENCODING_FALLBACKS.
    Raises ValueError if all encodings fail.
    """
    encodings = list(dict.fromkeys([encoding] + ENCODING_FALLBACKS))
    last_err: Exception | None = None
    for enc in encodings:
        try:
            return pd.read_csv(path, sep=sep, encoding=enc, **kwargs)
        except (UnicodeDecodeError, LookupError) as e:
            last_err = e
    raise ValueError(f"Could not read '{path}' with encodings {encodings}: {last_err}")


def save_csv(df: pd.DataFrame, path: str, encoding: str = "utf-8") -> None:
    """Save a DataFrame as semicolon-separated CSV."""
    df.to_csv(path, sep=";", index=False, encoding=encoding)
    print(f"  ✓  Saved → {path}")


def get_col(df: pd.DataFrame, col: str, default: str = "") -> pd.Series:
    """
    Return df[col] if the column exists.
    Otherwise return an empty Series and print a warning.
    """
    if col in df.columns:
        return df[col]
    print(f"  ⚠  Column '{col}' not found – filling with {default!r}")
    return pd.Series(default, index=df.index, dtype=str)
