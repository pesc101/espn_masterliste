"""
Streamlit app – Masterliste Updater
====================================
Upload the two source files (Bestellungen, Kontakte) and the PDF fee schedule,
preview the derived new-members table, then download the three masterlists as
semicolon-separated CSVs.

Column schemas are fixed and match the reference files:
  • IPNA Masterliste         – no Membership Number #, includes IPNA amount
  • Masterliste neue Mitgl.  – includes Membership Number #, no IPNA amount
  • Masterliste Vollständig  – same structure as neue Mitglieder
"""

from __future__ import annotations

import io

import pandas as pd
import pdfplumber
import streamlit as st

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Masterliste Updater",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Masterliste Updater")
st.markdown(
    "Upload the export files and the PDF fee schedule, then download the "
    "generated masterlists."
)

# ── Fixed output column schemas ────────────────────────────────────────────────
COLS_IPNA: list[str] = [
    "Titel",
    "First Name",
    "Last Name",
    "Email",
    "Phone",
    "Birthdate",
    "Address",
    "City",
    "Zipcode",
    "Country",
    "State",
    "Company",
    "Member since",
    "ESPN&IPNA amount",
    "IPNA amount",
    "Membership",
    "Gender",
    "Note",
]

COLS_NEUE: list[str] = [
    "Membership Number #",
    "Titel",
    "First Name",
    "Last Name",
    "Email",
    "Phone",
    "Birthdate",
    "Address",
    "City",
    "Zipcode",
    "Country",
    "State",
    "Company",
    "Member since",
    "ESPN&IPNA amount",
    "Membership",
    "Gender",
    "Note",
]

# Vollständig has the same structure as Neue Mitglieder
COLS_VOLL: list[str] = COLS_NEUE

# ── Column-name map ────────────────────────────────────────────────────────────
COL: dict[str, str] = {
    # Orders export
    "order_id": "Order number",
    "item": "Item",
    "price": "Price",
    "email": "Contact email",
    "date_created": "Date created",
    "billing_address": "Billing address",
    "billing_city": "Billing city",
    "billing_zip": "Billing zip/postal code",
    "billing_country": "Billing country",
    "billing_state": "Billing state",
    "billing_company": "Billing company name",
    # Contacts export
    "contact_email": "Email 1",
    "title": "Titel",
    "first_name": "First Name",
    "last_name": "Last Name",
    "phone": "Phone 1",
    "birthdate": "Birthdate",
    "gender": "Gender",
    # Contacts – primary address (Address 1)
    "addr1_street": "Address 1 - Street",
    "addr1_city": "Address 1 - City",
    "addr1_state": "Address 1 - State/Region",
    "addr1_zip": "Address 1 - Zip",
    "addr1_country": "Address 1 - Country",
    # Contacts – extra fields
    "company": "Company",
    "labels": "Labels",
    "language": "Language",
}

ENCODING_FALLBACKS = ["utf-8", "windows-1252", "windows-1250", "latin-1", "ascii"]


# ── Helpers ────────────────────────────────────────────────────────────────────


def load_csv_bytes(data: bytes, label: str, sep: str = ",") -> pd.DataFrame:
    last_err: Exception | None = None
    for enc in ENCODING_FALLBACKS:
        try:
            return pd.read_csv(io.BytesIO(data), sep=sep, encoding=enc)
        except (UnicodeDecodeError, LookupError) as exc:
            last_err = exc
    raise ValueError(f"Could not decode '{label}': {last_err}")


def get_col(df: pd.DataFrame, col: str, default: str = "") -> pd.Series:
    if col in df.columns:
        return df[col]
    return pd.Series(default, index=df.index, dtype=str)


def select_columns(source: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Return a DataFrame with exactly *cols*, filling any missing ones with ''."""
    result = pd.DataFrame(index=source.index)
    for c in cols:
        result[c] = source[c] if c in source.columns else ""
    return result.reset_index(drop=True)


def fmt_amount(val: object) -> str:
    try:
        cleaned = str(val).replace("€", "").strip().replace(",", ".")
        return f"{float(cleaned):.2f} €".replace(".", ",")
    except (ValueError, TypeError):
        return str(val)


def parse_membership(item: object) -> str:
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


def find_col(
    df: pd.DataFrame, *keywords: str, exclude: tuple[str, ...] = ()
) -> str | None:
    for col in df.columns:
        cl = col.lower()
        if all(k.lower() in cl for k in keywords) and not any(
            e.lower() in cl for e in exclude
        ):
            return col
    return None


def parse_pdf_fees(pdf_bytes: bytes) -> tuple[dict, str, str, str]:
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
        (i for i, r in enumerate(all_rows) if any(c and str(c).strip() for c in r)), 0
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


def df_to_csv_bytes(df: pd.DataFrame, encoding: str = "utf-8") -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, sep=";", index=False, encoding=encoding)
    return buf.getvalue()


# ── Sidebar: file uploads ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("Upload files")

    bestellungen_f = st.file_uploader("Bestellungen CSV", type=["csv"])
    kontakte_f = st.file_uploader("Kontakte CSV", type=["csv"])
    st.write("---")
    pdf_f = st.file_uploader("Beiträge PDF (fee schedule)", type=["pdf"])

    run_btn = st.button(
        "▶ Run",
        type="primary",
        disabled=not all([bestellungen_f, kontakte_f, pdf_f]),
    )

# ── Main area ──────────────────────────────────────────────────────────────────
if not all([bestellungen_f, kontakte_f, pdf_f]):
    st.info("Upload all three files in the sidebar, then click **▶ Run**.")
    st.stop()

if not run_btn and "results" not in st.session_state:
    st.info("Files ready. Click **▶ Run** in the sidebar to proceed.")
    st.stop()

if run_btn:
    with st.spinner("Processing…"):
        try:
            bestellungen = load_csv_bytes(bestellungen_f.read(), "Bestellungen")
            kontakte = load_csv_bytes(kontakte_f.read(), "Kontakte")
            fee_lookup, mem_col, espn_ipna_col, ipna_amt_col = parse_pdf_fees(
                pdf_f.read()
            )
        except Exception as exc:
            st.error(f"Error loading files: {exc}")
            st.stop()

        # Build new_members
        email_l, email_r = COL["email"], COL["contact_email"]
        if email_l not in bestellungen.columns:
            st.error(f"Column '{email_l}' not found in Orders.")
            st.stop()
        if email_r not in kontakte.columns:
            st.error(f"Column '{email_r}' not found in Contacts.")
            st.stop()

        merged = bestellungen.merge(
            kontakte, left_on=email_l, right_on=email_r, how="left"
        )
        merged["Membership"] = merged[COL["item"]].apply(parse_membership)

        def get_ipna_amount(membership: str) -> str:
            raw = fee_lookup.get(membership, {}).get(ipna_amt_col, "0 €")
            return fmt_amount(raw)

        def _coalesce(primary_key: str, fallback_key: str) -> pd.Series:
            primary = get_col(merged, COL[primary_key])
            if primary.eq("").all():
                return get_col(merged, COL[fallback_key])
            return primary.where(primary != "", get_col(merged, COL[fallback_key]))

        new_members = pd.DataFrame(
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

        # Slice to each masterliste schema
        ipna_out = select_columns(new_members, COLS_IPNA)
        neue_out = select_columns(new_members, COLS_NEUE)
        voll_out = select_columns(new_members, COLS_VOLL)

        st.session_state["results"] = {
            "new_members": new_members,
            "ipna_out": ipna_out,
            "neue_out": neue_out,
            "voll_out": voll_out,
            "fee_cols": (mem_col, espn_ipna_col, ipna_amt_col),
        }

    st.success("Done!")

# ── Display results ────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.stop()

res = st.session_state["results"]

# Summary
st.subheader("Summary")
st.metric("New members found", len(res["new_members"]))

st.write("---")

# New members preview
st.subheader("New members")
st.dataframe(res["new_members"], width="stretch")

st.write("---")

# Per-masterliste tabs with preview + download
tab1, tab2, tab3 = st.tabs(
    [
        "IPNA Masterliste",
        "Masterliste neue Mitglieder",
        "Masterliste Vollständig",
    ]
)

_downloads = [
    (tab1, "ipna_out", "IPNA Masterliste.csv", "windows-1252"),
    (tab2, "neue_out", "Masterliste neue Mitglieder.csv", "windows-1250"),
    (tab3, "voll_out", "Masterliste_full.csv", "windows-1252"),
]

for tab, key, filename, enc in _downloads:
    df = res[key]
    with tab:
        st.caption(f"{len(df)} row(s)")
        st.data_editor(df, width="stretch", num_rows="dynamic", key=f"editor_{key}")
        st.download_button(
            label=f"⬇ Download {filename}",
            data=df_to_csv_bytes(df, encoding=enc),
            file_name=filename,
            mime="text/csv",
            key=f"dl_{key}",
        )
