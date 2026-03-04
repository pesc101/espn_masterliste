"""PDF fee-schedule parser."""

from __future__ import annotations

import pdfplumber
import pandas as pd


def _find_col(
    df: pd.DataFrame, *keywords: str, exclude: tuple[str, ...] = ()
) -> str | None:
    """Return the first column whose name contains all *keywords* (case-insensitive)."""
    for col in df.columns:
        cl = col.lower()
        if all(k.lower() in cl for k in keywords) and not any(
            e.lower() in cl for e in exclude
        ):
            return col
    return None


def parse_fee_schedule(pdf_path: str) -> tuple[dict, str]:
    """
    Extract the membership fee table from a PDF and return:
        (fee_lookup, ipna_amt_col)

    fee_lookup  – dict[membership_label → {"espn_ipna_col": "...", ipna_amt_col: "..."}]
    ipna_amt_col – the detected column name for the IPNA-only amount

    The PDF is expected to contain at least one table whose header row has columns
    that include substrings matching 'membership', 'espn'/'ipna', and 'ipna'.
    """
    with pdfplumber.open(pdf_path) as pdf:
        all_rows = [
            row
            for page in pdf.pages
            for table in page.extract_tables()
            for row in table
        ]

    if not all_rows:
        raise ValueError(
            f"No tables found in '{pdf_path}' – check the file path and format."
        )

    # Detect header row: first row with at least one non-empty cell
    header_idx = next(
        (i for i, r in enumerate(all_rows) if any(c and str(c).strip() for c in r)),
        0,
    )
    raw_header = [
        str(c).strip() if c else f"col_{i}" for i, c in enumerate(all_rows[header_idx])
    ]
    fee_df = pd.DataFrame(all_rows[header_idx + 1 :], columns=raw_header)
    fee_df = fee_df[fee_df.iloc[:, 0].notna() & (fee_df.iloc[:, 0].str.strip() != "")]

    mem_col = _find_col(fee_df, "membership") or fee_df.columns[0]
    espn_ipna_col = (
        _find_col(fee_df, "espn", "ipna")
        or _find_col(fee_df, "espn")
        or fee_df.columns[1]
    )
    ipna_amt_col = _find_col(fee_df, "ipna", exclude=("espn",)) or fee_df.columns[2]

    fee_df = fee_df.drop_duplicates(subset=mem_col, keep="first")
    fee_lookup = fee_df.set_index(mem_col)[[espn_ipna_col, ipna_amt_col]].to_dict(
        "index"
    )

    print(
        f"PDF columns detected: membership='{mem_col}', "
        f"espn_ipna='{espn_ipna_col}', ipna='{ipna_amt_col}'"
    )
    print("Fee schedule loaded:", list(fee_lookup.keys()))

    return fee_lookup, ipna_amt_col
