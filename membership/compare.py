"""
Format-comparison utility.
Checks that newly appended rows match the schema and value patterns of the original.
"""

from __future__ import annotations

import pandas as pd


def _sample_pattern(series: pd.Series) -> str:
    """Classify the predominant value pattern of a Series."""
    s = series.dropna().astype(str).str.strip()
    s = s[s != ""]
    if s.empty:
        return "(empty)"
    if s.str.match(r"^\d{1,3}(,\d{3})*(\.\d+)? €$").mean() > 0.5:
        return "euro-amount"
    if s.str.match(r"^\d{4}-\d{2}-\d{2}").mean() > 0.5:
        return "date (YYYY-MM-DD)"
    if s.str.match(r"^\d+$").mean() > 0.7:
        return "numeric string"
    return "free text"


def compare_format(
    original: pd.DataFrame,
    appended: pd.DataFrame,
    label: str,
) -> None:
    """
    Print a schema and value-pattern comparison between the *original* DataFrame
    and the rows that were appended to it.

    Parameters
    ----------
    original : the DataFrame as it was *before* appending new members
    appended : the DataFrame *after* appending (original + new rows)
    label    : display name shown in the report header
    """
    orig_cols = original.columns.tolist()
    new_rows = appended.iloc[len(original) :]

    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    missing_in_new = [c for c in orig_cols if c not in appended.columns]
    extra_in_new = [c for c in appended.columns if c not in orig_cols]
    print(f"  Columns missing : {missing_in_new or '—'}")
    print(f"  Extra columns   : {extra_in_new or '—'}")
    print(f"  Column order OK : {appended.columns.tolist() == orig_cols}")

    header = (
        f"\n  {'Column':<30} {'orig dtype':<12} {'new dtype':<12} "
        f"{'orig pattern':<22} {'new pattern'}"
    )
    print(header)
    print(f"  {'-' * 100}")

    for col in orig_cols:
        if col not in appended.columns:
            continue
        orig_pat = _sample_pattern(original[col])
        new_pat = (
            _sample_pattern(new_rows[col]) if not new_rows.empty else "(no new rows)"
        )
        dtype_ok = original[col].dtype == appended[col].dtype
        pat_ok = orig_pat == new_pat
        flag = "" if (dtype_ok and pat_ok) else "  ← CHECK"
        print(
            f"  {col:<30} {str(original[col].dtype):<12} "
            f"{str(appended[col].dtype):<12} {orig_pat:<22} {new_pat}{flag}"
        )

    if not new_rows.empty:
        print(
            f"\n  Sample of appended rows ({min(3, len(new_rows))} of {len(new_rows)}):"
        )
        print(new_rows.head(3).to_string())
    else:
        print("\n  ⚠  No new rows were appended.")
