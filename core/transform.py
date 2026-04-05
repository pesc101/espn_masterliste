"""
Data transformation helpers (no Streamlit dependency).
"""

from __future__ import annotations

import pandas as pd

from .config import COL, COLS_IPNA, COLS_NEUE


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


def _norm_membership_key(value: object) -> str:
    """Return a case-insensitive, whitespace-normalised key for membership labels."""
    return " ".join(str(value).lower().split()) if pd.notna(value) else ""


def resolve_membership_from_pdf(
    item: object,
    amount: object,
    fee_lookup: dict,
    espn_ipna_col: str,
) -> str:
    """Resolve membership label from the PDF 'Membership' column when possible.

    Matching strategy:
    1) Parse from order item and map to an exact/normalised PDF membership label.
    2) Fallback to amount matching against the PDF ESPN&IPNA column.
    3) Final fallback is the parsed label from the order item.
    """

    parsed = parse_membership(item)
    if not fee_lookup:
        return parsed

    by_norm = {_norm_membership_key(k): str(k) for k in fee_lookup.keys()}
    parsed_norm = _norm_membership_key(parsed)
    if parsed_norm in by_norm:
        return by_norm[parsed_norm]

    def _to_float(val: object) -> float | None:
        try:
            return float(str(val).replace("€", "").replace(",", ".").strip())
        except (ValueError, TypeError):
            return None

    amount_num = _to_float(amount)
    if amount_num is None:
        return parsed

    amount_matches: list[str] = []
    for membership, values in fee_lookup.items():
        fee_num = _to_float(values.get(espn_ipna_col, ""))
        if fee_num is None:
            continue
        if abs(fee_num - amount_num) < 1e-9:
            amount_matches.append(str(membership))

    if len(amount_matches) == 1:
        return amount_matches[0]
    if len(amount_matches) > 1 and parsed_norm in {
        _norm_membership_key(m): m for m in amount_matches
    }:
        return by_norm.get(parsed_norm, parsed)

    return parsed


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

    # Pre-compute a normalised (lower-case, collapsed whitespace) → original key
    # mapping so that _match_pdf_label avoids re-normalising every fee_lookup key
    # on each call.
    _norm_to_pdf_label: dict[str, str] = {
        " ".join(str(k).lower().split()): k for k in fee_lookup
    }

    def _match_pdf_label(parsed: str) -> str:
        """Return the fee_lookup key that matches *parsed* case-insensitively.

        The ``Membership`` column in the output should show the exact label from
        the PDF's "Membership" column.  ``parse_membership`` may produce a
        normalised string that differs only in case or whitespace from the
        PDF label, so a case-insensitive, whitespace-normalised lookup is used
        as a fallback.
        Falls back to *parsed* unchanged when no match is found.
        """
        if parsed in fee_lookup:
            return parsed
        parsed_norm = " ".join(parsed.lower().split())
        return _norm_to_pdf_label.get(parsed_norm, parsed)

    def get_ipna_amount(membership: str) -> str:
        raw = fee_lookup.get(membership, {}).get(ipna_amt_col, "0 €")
        return fmt_amount(raw)

    def _norm_text(value: object) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _typed_addr_value(row: pd.Series, slot: str, part: str) -> str:
        if part == "street" and slot == "addr1":
            street = _norm_text(row.get(COL["addr1_street"], ""))
            street2 = _norm_text(row.get(COL.get("addr1_street2", ""), ""))
            return ", ".join([x for x in [street, street2] if x])
        key = f"{slot}_{part}"
        col_name = COL.get(key)
        if not col_name:
            return ""
        return _norm_text(row.get(col_name, ""))

    def _resolve_address_part(row: pd.Series, part: str) -> str:
        membership = _norm_text(row.get("Membership", "")).lower()
        prefer_shipping = "print journal" in membership

        shipping_vals: list[str] = []
        billing_vals: list[str] = []
        untyped_vals: list[str] = []

        for slot in ("addr1", "addr2"):
            type_col = COL.get(f"{slot}_type")
            addr_type = _norm_text(row.get(type_col, "")).lower() if type_col else ""
            value = _typed_addr_value(row, slot, part)
            if not value:
                continue
            if "shipping" in addr_type:
                shipping_vals.append(value)
            elif "billing" in addr_type:
                billing_vals.append(value)
            elif addr_type == "":
                untyped_vals.append(value)

        ordered_candidates = (
            shipping_vals + billing_vals + untyped_vals
            if prefer_shipping
            else billing_vals + shipping_vals + untyped_vals
        )
        if ordered_candidates:
            return ordered_candidates[0]

        billing_key = {
            "street": "billing_address",
            "city": "billing_city",
            "zip": "billing_zip",
            "country": "billing_country",
            "state": "billing_state",
        }[part]
        return _norm_text(row.get(COL[billing_key], ""))

    address = merged.apply(lambda r: _resolve_address_part(r, "street"), axis=1)
    city = merged.apply(lambda r: _resolve_address_part(r, "city"), axis=1)
    zipcode = merged.apply(lambda r: _resolve_address_part(r, "zip"), axis=1)
    country = merged.apply(lambda r: _resolve_address_part(r, "country"), axis=1)
    state = merged.apply(lambda r: _resolve_address_part(r, "state"), axis=1)

    company = get_col(merged, COL["company"]).where(
        get_col(merged, COL["company"]) != "", get_col(merged, COL["billing_company"])
    )

    full = pd.DataFrame(
        {
            "Membership Number #": get_col(merged, COL["order_id"]),
            "Titel": get_col(merged, COL["title"]),
            "First Name": get_col(merged, COL["first_name"]),
            "Last Name": get_col(merged, COL["last_name"]),
            "Email": get_col(merged, COL["email"]),
            "Phone": get_col(merged, COL["phone"]),
            "Birthdate": get_col(merged, COL["birthdate"]),
            "Address": address,
            "City": city,
            "Zipcode": zipcode,
            "Country": country,
            "State": state,
            "Company": company,
            "Member since": get_col(merged, COL["date_created"]),
            "ESPN&IPNA amount": get_col(merged, COL["price"]).apply(fmt_amount),
            "IPNA amount": merged["Membership"].apply(
                lambda m: get_ipna_amount(_match_pdf_label(m))
            ),
            "Membership": merged["Membership"].apply(_match_pdf_label),
            "Gender": get_col(merged, COL["gender"]),
            "Note": "",
        }
    )

    return full


def slice_outputs(
    full: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Slice *full* into the two remaining output schemas.

    Returns
    -------
    ipna_out, neue_out : pd.DataFrame
    """
    ipna_only = full[full["Membership"].str.contains("ESPN&IPNA", na=False)]
    neue_out = select_columns(full, COLS_NEUE)
    return (
        select_columns(ipna_only, COLS_IPNA),
        neue_out,
    )
