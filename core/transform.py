"""
Data transformation helpers (no Streamlit dependency).
"""

from __future__ import annotations

import pandas as pd

from .config import COL, COLS_IPNA, COLS_NEUE, COLS_VOLL


# ── Low-level utilities ────────────────────────────────────────────────────────


def fmt_amount(val: object) -> str:
    """Format a numeric-ish value as a German-style currency string, e.g. ``52,00 €``."""
    try:
        cleaned = str(val).replace("€", "").strip().replace(",", ".")
        return f"{float(cleaned):.2f} €".replace(".", ",")
    except (ValueError, TypeError):
        return str(val)


def get_col(df: pd.DataFrame, col: str, default: str = "") -> pd.Series:
    """Return column *col* from *df*, or a series filled with *default* if absent."""
    if col in df.columns:
        return df[col]
    return pd.Series(default, index=df.index, dtype=str)


def select_columns(source: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Return a DataFrame with exactly *cols* in order, filling missing ones with ''."""
    result = pd.DataFrame(index=source.index)
    for c in cols:
        result[c] = source[c] if c in source.columns else ""
    return result.reset_index(drop=True)


def parse_membership(item: object) -> str:
    """Derive a normalised membership label from a free-text order-item string."""
    a = str(item).lower() if pd.notna(item) else ""
    base = (
        "ESPN&IPNA"
        if ("espn" in a and "ipna" in a)
        else ("ESPN" if "espn" in a else "IPNA")
    )
    lmi = "lower-middle income -" if "lower" in a else ""
    jrn = (
        "online&print journal"
        if "print" in a
        else ("online journal" if "online" in a else "")
    )
    return " ".join(filter(None, [base, lmi, jrn]))


# ── High-level builder ─────────────────────────────────────────────────────────


def build_new_members(
    merged: pd.DataFrame,
    fee_lookup: dict,
    ipna_amt_col: str,
) -> pd.DataFrame:
    """Build the full new-members table from the merged orders+contacts DataFrame.

    Parameters
    ----------
    merged:
        Result of merging the orders export with the contacts export, with a
        ``Membership`` column already attached.
    fee_lookup:
        Fee table keyed by membership type, as returned by ``parse_pdf_fees``.
    ipna_amt_col:
        Name of the IPNA-amount column inside *fee_lookup* entries.

    Returns
    -------
    pd.DataFrame
        One row per new member with all columns needed by every output schema.
    """

    def get_ipna_amount(membership: str) -> str:
        raw = fee_lookup.get(membership, {}).get(ipna_amt_col, "0 €")
        return fmt_amount(raw)

    def _coalesce(primary_key: str, fallback_key: str) -> pd.Series:
        primary = get_col(merged, COL[primary_key])
        if primary.eq("").all():
            return get_col(merged, COL[fallback_key])
        return primary.where(primary != "", get_col(merged, COL[fallback_key]))

    full = pd.DataFrame(
        {
            "Membership Number #": get_col(merged, COL["order_id"]),
            "Titel": get_col(merged, COL["title"]),
            "First Name": get_col(merged, COL["first_name"]),
            "Last Name": get_col(merged, COL["last_name"]),
            "Email": get_col(merged, COL["email"]),
            "Phone": get_col(merged, COL["phone"]),
            "Birthdate": get_col(merged, COL["birthdate"]),
            "Address": _coalesce("addr1_street", "billing_address"),
            "City": _coalesce("addr1_city", "billing_city"),
            "Zipcode": _coalesce("addr1_zip", "billing_zip"),
            "Country": _coalesce("addr1_country", "billing_country"),
            "State": _coalesce("addr1_state", "billing_state"),
            "Company": _coalesce("company", "billing_company"),
            "Member since": get_col(merged, COL["date_created"]),
            "ESPN&IPNA amount": get_col(merged, COL["price"]).apply(fmt_amount),
            "IPNA amount": merged["Membership"].apply(get_ipna_amount),
            "Membership": merged["Membership"],
            "Gender": get_col(merged, COL["gender"]),
            "Language": get_col(merged, COL["language"]),
            "Labels": get_col(merged, COL["labels"]),
            "Note": "",
        }
    )

    return full


def slice_outputs(
    full: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Slice *full* into the three masterliste schemas.

    Returns
    -------
    ipna_out, neue_out, voll_out : pd.DataFrame
    """
    return (
        select_columns(full, COLS_IPNA),
        select_columns(full, COLS_NEUE),
        select_columns(full, COLS_VOLL),
    )
