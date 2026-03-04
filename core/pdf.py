"""
PDF fee-schedule parser (no Streamlit dependency).
"""

from __future__ import annotations

import io

import pandas as pd
import pdfplumber


def find_col(
    df: pd.DataFrame, *keywords: str, exclude: tuple[str, ...] = ()
) -> str | None:
    """Return the first column whose lowercased name contains all *keywords*
    and none of the *exclude* terms. Returns None if no match is found."""
    for col in df.columns:
        cl = col.lower()
        if all(k.lower() in cl for k in keywords) and not any(
            e.lower() in cl for e in exclude
        ):
            return col
    return None


def parse_pdf_fees(pdf_bytes: bytes) -> tuple[dict, str, str, str]:
    """Extract the fee lookup table from the PDF.

    Returns
    -------
    fee_lookup : dict
        ``{membership_type: {espn_ipna_col: value, ipna_amt_col: value}}``
    mem_col : str
        Name of the membership-type column in the PDF table.
    espn_ipna_col : str
        Name of the ESPN+IPNA combined-fee column.
    ipna_amt_col : str
        Name of the IPNA-only fee column.
    """
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        all_rows = [
            row
            for page in pdf.pages
            for table in page.extract_tables()
            for row in table
        ]

    if not all_rows:
        raise ValueError("No tables found in the PDF.")

    header_idx = next(
        (i for i, r in enumerate(all_rows) if any(c and str(c).strip() for c in r)),
        0,
    )
    raw_header = [
        str(c).strip() if c else f"col_{i}" for i, c in enumerate(all_rows[header_idx])
    ]

    fee_df = pd.DataFrame(all_rows[header_idx + 1 :], columns=raw_header)
    fee_df = fee_df[fee_df.iloc[:, 0].notna() & (fee_df.iloc[:, 0].str.strip() != "")]

    mem_col = find_col(fee_df, "membership") or fee_df.columns[0]
    espn_ipna_col = (
        find_col(fee_df, "espn", "ipna")
        or find_col(fee_df, "espn")
        or fee_df.columns[1]
    )
    ipna_amt_col = find_col(fee_df, "ipna", exclude=("espn",)) or fee_df.columns[2]

    fee_df = fee_df.drop_duplicates(subset=mem_col, keep="first")
    fee_lookup = fee_df.set_index(mem_col)[[espn_ipna_col, ipna_amt_col]].to_dict(
        "index"
    )

    return fee_lookup, mem_col, espn_ipna_col, ipna_amt_col
