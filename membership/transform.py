"""
Data-transformation helpers:
  - parse_membership  – normalise article string → membership label
  - fmt_amount        – normalise numeric/string amounts to "X,XX €"
  - build_new_members – assemble the unified new-member DataFrame
"""

from __future__ import annotations

import pandas as pd

from .config import COL
from .io import get_col


def parse_membership(item) -> str:
    """
    Map an order article string to a normalised membership label.

    Examples
    --------
    "ESPN&IPNA lower-middle income - online journal" → "ESPN&IPNA lower-middle income - online journal"
    "ESPN Mitgliedschaft"                             → "ESPN"
    """
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


def fmt_amount(val) -> str:
    """
    Normalise a monetary value to the canonical "X,XX €" format.

    Accepts floats, plain integers, "152.00", "152,00", "152 €", "152,00 €", etc.
    Returns the original string unchanged if it cannot be parsed.
    """
    try:
        cleaned = str(val).replace("€", "").strip().replace(",", ".")
        return f"{float(cleaned):.2f} €".replace(".", ",")
    except (ValueError, TypeError):
        return str(val)


def build_new_members(
    merged: pd.DataFrame,
    fee_lookup: dict,
    ipna_amt_col: str,
) -> pd.DataFrame:
    """
    Assemble the *new_members* DataFrame from the merged orders+contacts table.

    Parameters
    ----------
    merged       : result of merging Bestellungen with Kontakte on e-mail
    fee_lookup   : {membership_label → {ipna_amt_col: raw_amount, ...}}
    ipna_amt_col : the column key inside fee_lookup for the IPNA-only amount
    """

    def get_ipna_amount(membership: str) -> str:
        raw = fee_lookup.get(membership, {}).get(ipna_amt_col, "0 €")
        return fmt_amount(raw)

    def _coalesce(primary_key: str, fallback_key: str) -> pd.Series:
        """Return the contacts column when available, fall back to the orders column."""
        primary = get_col(merged, COL[primary_key])
        if primary.eq("").all():
            return get_col(merged, COL[fallback_key])
        return primary.where(primary != "", get_col(merged, COL[fallback_key]))

    return pd.DataFrame(
        {
            "Membership Number #": get_col(merged, COL["order_id"]),
            "Titel": get_col(merged, COL["title"]),
            "First Name": get_col(merged, COL["first_name"]),
            "Last Name": get_col(merged, COL["last_name"]),
            "Email": get_col(merged, COL["email"]),
            "Phone": get_col(merged, COL["phone"]),
            "Birthdate": get_col(merged, COL["birthdate"]),
            # Prefer contacts Address 1; fall back to billing address from orders
            "Address": _coalesce("addr1_street", "billing_address"),
            "City": _coalesce("addr1_city", "billing_city"),
            "Zipcode": _coalesce("addr1_zip", "billing_zip"),
            "Country": _coalesce("addr1_country", "billing_country"),
            "State": _coalesce("addr1_state", "billing_state"),
            # Prefer contacts Company; fall back to billing company from orders
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
