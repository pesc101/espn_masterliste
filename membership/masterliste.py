"""
Masterliste update helpers:
  - align_columns  – restrict new_members to the target list's column set
  - dedup_append   – append new rows, skip existing members by e-mail / order-id
  - update_list    – align + dedup + save in one call
"""

from __future__ import annotations

import pandas as pd

from .io import save_csv


def align_columns(
    source_df: pd.DataFrame,
    target_cols: list[str],
    label: str = "",
) -> pd.DataFrame:
    """
    Return *source_df* restricted to columns that appear in *target_cols*.
    Warns about any target columns that are missing from source_df.
    """
    present = [c for c in target_cols if c in source_df.columns]
    missing = [c for c in target_cols if c not in source_df.columns]
    if missing:
        print(f"  ⚠  {label}: columns missing from new_members – skipping: {missing}")
    return source_df[present].copy()


def dedup_append(
    existing: pd.DataFrame,
    new_rows: pd.DataFrame,
    label: str = "",
) -> pd.DataFrame:
    """
    Append *new_rows* to *existing*, skipping any row whose dedup key already appears.

    Dedup key priority: 'Email' → 'Membership Number #' → full-row equality.
    Rows with a null/empty key are never treated as duplicates (always kept).
    Existing rows always win (keep='first').
    """
    dedup_key: str | None = None
    for key in ("Email", "Membership Number #"):
        if key in existing.columns and key in new_rows.columns:
            dedup_key = key
            break

    if dedup_key is None:
        print(f"  ⚠  {label}: no dedup key found, appending without dedup")
        return pd.concat([existing, new_rows], ignore_index=True)

    combined = pd.concat([existing, new_rows], ignore_index=True)

    # Only deduplicate rows that carry a non-null, non-empty key value
    has_key = combined[dedup_key].notna() & (
        combined[dedup_key].astype(str).str.strip() != ""
    )
    deduped = combined[has_key].drop_duplicates(subset=[dedup_key], keep="first")
    no_key = combined[~has_key]
    result = pd.concat([deduped, no_key]).sort_index().reset_index(drop=True)

    skipped = len(combined) - len(result)
    if skipped:
        print(
            f"  ℹ  {label}: {skipped} duplicate(s) skipped (matched on '{dedup_key}')"
        )
    return result


def update_list(
    existing: pd.DataFrame,
    new_members: pd.DataFrame,
    save_path: str,
    encoding: str,
    label: str,
) -> pd.DataFrame:
    """
    Full update pipeline for one masterliste:
      1. Align new_members columns to the existing list's schema
      2. Dedup-append (skip already-present members)
      3. Save to CSV
      4. Print a summary line

    Returns the updated DataFrame.
    """
    aligned = align_columns(new_members, existing.columns.tolist(), label=label)
    updated = dedup_append(existing, aligned, label=label)
    save_csv(updated, save_path, encoding=encoding)
    print(f"  {label}: {len(existing)} → {len(updated)} rows")
    return updated
