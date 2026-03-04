"""
Streamlit app – Masterliste Updater
====================================
Upload the five source files (Bestellungen, Kontakte, 3× Masterlisten) and the
PDF fee schedule, preview the derived new-members table, then download the
three updated masterlists as semicolon-separated CSVs.
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
    "updated masterlists."
)

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


def align_columns(source: pd.DataFrame, target_cols: list[str]) -> pd.DataFrame:
    present = [c for c in target_cols if c in source.columns]
    return source[present].copy()


def dedup_append(
    existing: pd.DataFrame, new_rows: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    for key in ("Email", "Membership Number #"):
        if key in existing.columns and key in new_rows.columns:
            break
    else:
        return pd.concat([existing, new_rows], ignore_index=True), len(new_rows)

    combined = pd.concat([existing, new_rows], ignore_index=True)
    has_key = combined[key].notna() & (combined[key].astype(str).str.strip() != "")
    deduped = combined[has_key].drop_duplicates(subset=[key], keep="first")
    no_key = combined[~has_key]
    result = pd.concat([deduped, no_key]).sort_index().reset_index(drop=True)
    added = len(result) - len(existing)
    return result, added


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
    ipna_f = st.file_uploader("IPNA Masterliste CSV", type=["csv"])
    neue_f = st.file_uploader("Masterliste neue Mitglieder CSV", type=["csv"])
    voll_f = st.file_uploader("Masterliste Vollständig CSV", type=["csv"])
    st.write("---")
    pdf_f = st.file_uploader("Beiträge PDF (fee schedule)", type=["pdf"])

    run_btn = st.button(
        "▶ Run update",
        type="primary",
        disabled=not all([bestellungen_f, kontakte_f, ipna_f, neue_f, voll_f, pdf_f]),
    )

# ── Main area ──────────────────────────────────────────────────────────────────
if not all([bestellungen_f, kontakte_f, ipna_f, neue_f, voll_f, pdf_f]):
    st.info("Upload all six files in the sidebar, then click **▶ Run update**.")
    st.stop()

if not run_btn and "results" not in st.session_state:
    st.info("Files ready. Click **▶ Run update** in the sidebar to proceed.")
    st.stop()

if run_btn:
    with st.spinner("Processing…"):
        try:
            bestellungen = load_csv_bytes(bestellungen_f.read(), "Bestellungen")
            kontakte = load_csv_bytes(kontakte_f.read(), "Kontakte")
            ipna_ml = load_csv_bytes(ipna_f.read(), "IPNA Masterliste", sep=";")
            neue_ml = load_csv_bytes(
                neue_f.read(), "Masterliste neue Mitglieder", sep=";"
            )
            voll_ml = load_csv_bytes(voll_f.read(), "Masterliste_full", sep=";")
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

        updated_ipna, added_ipna = dedup_append(
            ipna_ml, align_columns(new_members, ipna_ml.columns.tolist())
        )
        updated_neue, added_neue = dedup_append(
            neue_ml, align_columns(new_members, neue_ml.columns.tolist())
        )
        updated_voll, added_voll = dedup_append(
            voll_ml, align_columns(new_members, voll_ml.columns.tolist())
        )

        st.session_state["results"] = {
            "new_members": new_members,
            "updated_ipna": updated_ipna,
            "updated_neue": updated_neue,
            "updated_voll": updated_voll,
            "added_ipna": added_ipna,
            "added_neue": added_neue,
            "added_voll": added_voll,
            "orig_ipna_len": len(ipna_ml),
            "orig_neue_len": len(neue_ml),
            "orig_voll_len": len(voll_ml),
            "fee_cols": (mem_col, espn_ipna_col, ipna_amt_col),
        }

    st.success("Done!")

# ── Display results ────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.stop()

res = st.session_state["results"]

# Summary metrics
st.subheader("Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("New members found", len(res["new_members"]))
c2.metric("Added to IPNA Masterliste", res["added_ipna"])
c3.metric("Added to Neue Mitglieder", res["added_neue"])
c4.metric("Added to Vollständig", res["added_voll"])

st.write("---")

# New members preview
st.subheader("New members")
st.dataframe(res["new_members"], use_container_width=True)

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
    (tab1, "updated_ipna", "IPNA Masterliste.csv", "windows-1252"),
    (tab2, "updated_neue", "Masterliste neue Mitglieder.csv", "windows-1250"),
    (tab3, "updated_voll", "Masterliste_full.csv", "windows-1252"),
]

for tab, key, filename, enc in _downloads:
    df = res[key]
    with tab:
        orig_len = res[f"orig_{key.split('_')[1]}_len"]
        st.caption(f"{orig_len} → {len(df)} rows")
        st.dataframe(
            df.tail(max(10, res[f"added_{key.split('_')[1]}"] + 2)),
            use_container_width=True,
        )
        st.download_button(
            label=f"⬇ Download {filename}",
            data=df_to_csv_bytes(df, encoding=enc),
            file_name=filename,
            mime="text/csv",
            key=f"dl_{key}",
        )
